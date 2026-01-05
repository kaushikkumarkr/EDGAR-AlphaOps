import yfinance as yf
import pandas as pd
import logging
from lakehouse.db import Database
import time

class MarketDataFetcher:
    def __init__(self) -> None:
        self.db = Database()

    def fetch_prices(self, tickers: list[str]) -> None:
        """
        Download history for tickers and save to DuckDB.
        """
        if not tickers:
            return

        logging.info(f"Fetching market data for {len(tickers)} tickers: {tickers}")
        
        try:
            # yfinance can download multiple tickers
            # data = yf.download(tickers, period="max", group_by="ticker", auto_adjust=False)
            # data structure varies if 1 vs multiple tickers.
            # safer to loop for robustness in this MVP, or handle multi-index.
            
            for t in tickers:
                self._fetch_one(t)
                time.sleep(0.5) # Politeness
                
        except Exception as e:
            logging.error(f"Error fetching market data: {e}")

    def _fetch_one(self, ticker: str) -> None:
        logging.info(f"Downloading {ticker}...")
        try:
            # period="max" or "10y"
            df = yf.download(ticker, period="10y", auto_adjust=False, progress=False)
            
            if df.empty:
                logging.warning(f"No price data for {ticker}")
                return

            # Ensure single level columns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            df = df.reset_index()
            logging.info(f"Columns: {df.columns.tolist()}")

            # Rename for DB
            # Ensure "Adj Close" exists, else use Close
            if "Adj Close" not in df.columns:
                df["Adj Close"] = df["Close"]
            
            df = df.rename(columns={
                "Date": "date",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Adj Close": "adjusted_close",
                "Volume": "volume"
            })
            
            df["ticker"] = ticker
            
            # Select schema columns explicitly to ensure order/existence
            # Compute Returns & Volatility
            df = df.sort_values("date")
            df["daily_return"] = df["adjusted_close"].pct_change()
            # Annualized Volatility (30-day rolling std dev * sqrt(252))
            df["volatility_30d"] = df["daily_return"].rolling(window=30).std() * (252 ** 0.5)

            final_df = df[["ticker", "date", "open", "high", "low", "close", "volume", "adjusted_close", "daily_return", "volatility_30d"]].copy()
            
            self._save_prices(final_df)
            
        except Exception as e:
            logging.error(f"Failed to fetch {ticker}: {e}")

    def _save_prices(self, df: pd.DataFrame) -> None:
        conn = self.db.get_connection()
        try:
            conn.register("df_prices", df)
            # Insert or Replace
            conn.execute("""
                INSERT INTO prices (ticker, date, open, high, low, close, volume, adjusted_close, daily_return, volatility_30d)
                SELECT ticker, date, open, high, low, close, volume, adjusted_close, daily_return, volatility_30d FROM df_prices
                ON CONFLICT (ticker, date) DO UPDATE SET
                    close = EXCLUDED.close,
                    adjusted_close = EXCLUDED.adjusted_close,
                    volume = EXCLUDED.volume,
                    open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    daily_return = EXCLUDED.daily_return,
                    volatility_30d = EXCLUDED.volatility_30d
            """)
            logging.info(f"Saved {len(df)} rows for {df['ticker'].iloc[0]}")
        finally:
            conn.close()
