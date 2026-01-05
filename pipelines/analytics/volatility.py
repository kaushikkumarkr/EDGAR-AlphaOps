
import numpy as np
import pandas as pd
import logging
from pipelines.storage import MinIOClient
from pipelines.market.stooq import StooqClient
from io import BytesIO

logger = logging.getLogger(__name__)

class RiskEngine:
    def __init__(self):
        self.storage = MinIOClient()
        self.stooq = StooqClient()

    def _get_price_series(self, ticker: str) -> pd.DataFrame:
        clean_ticker = ticker.lower().strip()
        key = f"market/{clean_ticker}.csv"
        try:
            data = self.storage.get_object(key)
            df = pd.read_csv(BytesIO(data))
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
            df.sort_index(inplace=True)
            # Calculate Log Returns
            df['Return'] = np.log(df['Close'] / df['Close'].shift(1))
            return df
        except Exception:
            return pd.DataFrame()

    def calculate_volatility(self, ticker: str, window: int = 252) -> dict:
        """
        Calculates Annualized Volatility and EWMA Volatility.
        """
        df = self._get_price_series(ticker)
        if df.empty or len(df) < 30:
            return {"error": "Insufficient Data"}
            
        returns = df['Return'].dropna()
        
        # 1. Annualized Std Dev (Rolling window, but we take latest)
        recent_vol = returns.tail(30).std() * np.sqrt(252)
        
        # 2. EWMA (Span=30 days roughly lambda=0.94)
        ewma_vol = returns.ewm(span=30).std().iloc[-1] * np.sqrt(252)
        
        # 3. VaR 95% (Parametric via EWMA)
        # Z-score for 95% is 1.645
        var_95 = 1.645 * ewma_vol
        
        # 4. Risk Score (0-100)
        # Baseline: 20% vol is normal (Score 20). 100% vol is Score 100.
        # Cap at 100.
        risk_score = min(100, ewma_vol * 100)
        
        return {
            "ticker": ticker,
            "volatility_annual": float(recent_vol),
            "volatility_ewma": float(ewma_vol),
            "var_95": float(var_95),
            "risk_score": float(risk_score)
        }
