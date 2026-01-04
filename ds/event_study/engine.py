import pandas as pd
import numpy as np
from typing import Optional, Tuple, List
import logging
from datetime import timedelta
from lakehouse.db import Database
import uuid

class EventStudyEngine:
    def __init__(self, benchmark_ticker: str = "SPY"):
        self.db = Database()
        self.benchmark_ticker = benchmark_ticker

    def run_study(self, ticker: str, events: List[dict] = None) -> None:
        """
        Run event study for a list of events. 
        If events is None, fetch 10-K/10-Q filings from DB for this ticker.
        """
        if not events:
            events = self._fetch_filing_events(ticker)
            
        if not events:
            logging.warning(f"No events found for {ticker}")
            return
            
        # Fetch Market Data (Benchmark)
        spy_df = self._fetch_prices(self.benchmark_ticker)
        if spy_df.empty:
            logging.error(f"Benchmark {self.benchmark_ticker} data missing.")
            return
            
        # Fetch Ticker Data
        stock_df = self._fetch_prices(ticker)
        if stock_df.empty:
            logging.error(f"Ticker {ticker} data missing.")
            return
            
        # Merge for alignment
        # We need daily returns.
        data = pd.merge(
            stock_df[["date", "daily_return"]], 
            spy_df[["date", "daily_return"]], 
            on="date", 
            suffixes=("_stock", "_mkt"),
            how="inner"
        ).dropna()
        
        results = []
        for event in events:
            # Event: {date, type, accession, ...}
            # Ensure proper timestamp for comparison with DataFrame datetime64
            event_date = pd.to_datetime(event["date"])
            
            # Windows
            # Est Window: [-120, -10] (Trading days relative to event)
            # Car Window: [-2, +2]
            
            # Find index of event date
            try:
                # Find exact or closest preceding date if holiday?
                # Using searchsorted or simple filtering
                # data is strictly daily trading days.
                
                # Get location of closest date <= event_date
                loc_idx = data[data["date"] <= event_date].index.max()
                
                if pd.isna(loc_idx):
                    logging.debug(f"Event date {event_date} out of range (too early).")
                    continue
                    
                # Indices for windows (assuming row index is time sorted? data should be sorted)
                data = data.sort_values("date").reset_index(drop=True)
                
                # Re-find index after reset
                # Using searchsorted for speed if needed, but pandas filtering is safer for business logic legibility
                
                # Let's simple filter:
                # estimation: date < event_date - 10 days... tricky with weekends.
                # Better to use integer iloc offsets.
                
                event_row_idx = data[data["date"] <= event_date].index[-1]
                
                # Verify the date is close enough (e.g. within 5 days, else event might be way off)
                actual_date = data.loc[event_row_idx, "date"]
                if (event_date - actual_date).days > 5:
                    logging.warning(f"No market data near event {event_date} (closest {actual_date})")
                    continue
                
                # Define Integers
                # CAR [-2, +2]
                car_start_idx = event_row_idx - 2
                car_end_idx = event_row_idx + 2
                
                # Est [-120, -10]
                est_start_idx = event_row_idx - 120
                est_end_idx = event_row_idx - 10
                
                if est_start_idx < 0:
                    logging.debug("Not enough history for estimation.")
                    continue
                    
                # Slices
                est_data = data.iloc[est_start_idx:est_end_idx+1]
                car_data = data.iloc[car_start_idx:car_end_idx+1]
                
                if len(est_data) < 60: # Minimum observations
                    continue
                    
                # Regression (OLS)
                # R_i = alpha + beta * R_m
                x = est_data["daily_return_mkt"].values
                y = est_data["daily_return_stock"].values
                
                # Simple linear regression (numpy polyfit deg=1)
                # slope (beta), intercept (alpha)
                beta, alpha = np.polyfit(x, y, 1)
                
                # Correlation / R2
                # corr_matrix = np.corrcoef(x, y)
                # corr = corr_matrix[0, 1]
                # r_sq = corr ** 2
                
                # Calculate Abnormal Returns in Event Window
                car_data = car_data.copy()
                car_data["expected_return"] = alpha + beta * car_data["daily_return_mkt"]
                car_data["abnormal_return"] = car_data["daily_return_stock"] - car_data["expected_return"]
                
                car_val = car_data["abnormal_return"].sum()
                
                # Save Result
                res_dict = {
                    "study_id": str(uuid.uuid4()),
                    "cik": event.get("cik", ""),
                    "ticker": ticker,
                    "event_date": event_date,
                    "event_type": event.get("type", "Unknown"),
                    "estimation_window_start": est_data["date"].min(),
                    "estimation_window_end": est_data["date"].max(),
                    "alpha": alpha,
                    "beta": beta,
                    "r_squared": 0.0, # TODO simple
                    "car_window": "-2,2",
                    "car_value": car_val,
                    "t_stat": 0.0 # TODO simple standard error
                }
                results.append(res_dict)
                
            except Exception as e:
                logging.warning(f"Calculation failed for {event_date}: {e}")
                continue
        
        if results:
            self._save_results(pd.DataFrame(results))
            logging.info(f"Saved {len(results)} event studies for {ticker}")

    def _fetch_prices(self, ticker: str) -> pd.DataFrame:
        conn = self.db.get_connection()
        try:
            # Need daily_return column. If created in Sprint 3.
            query = f"SELECT date, daily_return FROM prices WHERE ticker = '{ticker}' AND daily_return IS NOT NULL ORDER BY date"
            return conn.execute(query).fetchdf()
        finally:
            conn.close()

    def _fetch_filing_events(self, ticker: str) -> List[dict]:
        conn = self.db.get_connection()
        try:
            query = f"SELECT cik, filing_date, form_type, accession_number FROM filings WHERE ticker = '{ticker}' AND form_type IN ('10-K', '10-Q')"
            df = conn.execute(query).fetchdf()
            if df.empty:
                return []
            
            events = []
            for _, row in df.iterrows():
                events.append({
                    "cik": row["cik"],
                    "date": row["filing_date"],
                    "type": row["form_type"],
                    "accession": row["accession_number"]
                })
            return events
        finally:
            conn.close()

    def _save_results(self, df: pd.DataFrame) -> None:
        conn = self.db.get_connection()
        try:
            conn.register("df_events", df)
            conn.execute("""
                INSERT INTO event_studies (study_id, cik, ticker, event_date, event_type, estimation_window_start, estimation_window_end, alpha, beta, r_squared, car_window, car_value, t_stat)
                SELECT study_id, cik, ticker, event_date, event_type, estimation_window_start, estimation_window_end, alpha, beta, r_squared, car_window, car_value, t_stat FROM df_events
            """)
        finally:
            conn.close()
