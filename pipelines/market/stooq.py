
import requests
import logging
from pipelines.storage import MinIOClient
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class StooqClient:
    def __init__(self):
        self.storage = MinIOClient()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def download_daily_ohlc(self, ticker: str) -> bool:
        """
        Downloads daily OHLC data from Stooq as CSV and saves to MinIO.
        URL: https://stooq.com/q/d/l/?s={ticker}.us&i=d
        """
        clean_ticker = ticker.lower().strip()
        url = f"https://stooq.com/q/d/l/?s={clean_ticker}.us&i=d"
        logger.info(f"Fetching Stooq Data: {url}")
        
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            
            content = resp.content
            # Validation: Stooq returns "No data" in body if invalid ticker
            if b"No data" in content[:100] or len(content) < 50:
                logger.warning(f"No data found for {ticker} (Stooq returned empty/error text)")
                return False
                
            # Basic CSV validation (header check)
            if not content.startswith(b"Date,Open,High,Low,Close"):
                # Stooq sometimes changes headers or returns HTML error
                logger.warning(f"Invalid CSV format for {ticker}")
                return False
                
            # Save to MinIO
            key = f"market/{clean_ticker}.csv"
            self.storage.put_object(key, content)
            logger.info(f"Saved market data for {ticker}")
            return True
            
        except Exception as e:
            logger.error(f"Stooq Download Failed for {ticker}: {e}")
            raise


