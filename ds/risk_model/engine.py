import pandas as pd
import numpy as np
from typing import Optional, Dict
import logging
import uuid
from lakehouse.db import Database

class RiskEngine:
    def __init__(self):
        self.db = Database()

    def run_risk_analysis(self, ticker: str) -> None:
        """
        Compute daily VaR and determine volatility regime for the latest available date.
        """
        logging.info(f"Running risk analysis for {ticker}...")
        
        # 1. Fetch History (1 year for VaR)
        prices_df = self._fetch_prices(ticker, lookback_days=365)
        if prices_df.empty or len(prices_df) < 50:
            logging.warning(f"Not enough history for {ticker} risk analysis.")
            return

        # 2. Fetch VIX for Regime (latest available)
        vix_df = self._fetch_prices("^VIX", lookback_days=5)
        current_vix = vix_df["close"].iloc[-1] if not vix_df.empty else None
        
        # Latest date
        latest_date = prices_df["date"].max()
        
        # 3. Compute Metrics
        
        # Volatility Regime
        regime = "Normal"
        if current_vix:
            if current_vix < 12:
                regime = "Low"
            elif current_vix > 30:
                regime = "Crisis"
            elif current_vix > 20:
                regime = "High"
        else:
            # Fallback to realized vol
            recent_vol = prices_df["volatility_30d"].iloc[-1] if "volatility_30d" in prices_df else 0
            # Annualized 30d vol. If > 0.4 (40%) -> High?
            if recent_vol > 0.4:
                regime = "High"
            elif recent_vol > 0.6:
                regime = "Crisis"
            elif recent_vol < 0.1:
                regime = "Low"

        # VaR (Historical Simulation)
        # Using returns distribution of last 252 days
        returns = prices_df["daily_return"].dropna()
        if len(returns) > 0:
            var_95 = np.percentile(returns, 5) # 5th percentile (negative number)
            var_99 = np.percentile(returns, 1) # 1st percentile
            
            # Parametric VaR (Normal Distribution assumption) -> maybe too simple?
            # Historical is robust for fat tails.
            
            # CVaR (Expected Shortfall) - mean of returns <= var_95
            cvar_95 = returns[returns <= var_95].mean()
        else:
            var_95, var_99, cvar_95 = 0, 0, 0
            
        # 4. Save
        result = {
            "metric_id": str(uuid.uuid4()),
            "ticker": ticker,
            "asof_date": latest_date,
            "volatility_30d": prices_df["volatility_30d"].iloc[-1] if "volatility_30d" in prices_df else None,
            "volatility_regime": regime,
            "var_95": var_95,
            "var_99": var_99,
            "cvar_95": cvar_95
        }
        
        self._save_metrics(result)
        logging.info(f"Risk metrics saved for {ticker} (Regime: {regime}, VaR95: {var_95:.2%})")

    def _fetch_prices(self, ticker: str, lookback_days: int) -> pd.DataFrame:
        conn = self.db.get_connection()
        try:
            # DuckDB interval
            query = f"""
                SELECT date, close, daily_return, volatility_30d 
                FROM prices 
                WHERE ticker = '{ticker}' 
                AND date >= (SELECT MAX(date) - INTERVAL {lookback_days} DAY FROM prices WHERE ticker='{ticker}')
                ORDER BY date
            """
            return conn.execute(query).fetchdf()
        finally:
            conn.close()

    def _save_metrics(self, data: Dict) -> None:
        conn = self.db.get_connection()
        try:
            # Upsert
            cols = ["metric_id", "ticker", "asof_date", "volatility_30d", "volatility_regime", "var_95", "var_99", "cvar_95"]
            placeholders = ", ".join(["?"] * len(cols))
            
            # We treat (ticker, asof_date) as unique logic, but ID is PK.
            # Ideally delete existing for this date first?
            # Or use sql insert.
            
            # Warning: sqlite/duckdb can be picky about types. UUID is string.
            val_tuple = tuple([data[c] for c in cols])
            
            conn.execute(f"DELETE FROM risk_metrics WHERE ticker=? AND asof_date=?", [data["ticker"], data["asof_date"]])
            
            conn.execute(f"""
                INSERT INTO risk_metrics ({', '.join(cols)}, created_at)
                VALUES ({placeholders}, current_timestamp)
            """, val_tuple)
            
        finally:
            conn.close()
