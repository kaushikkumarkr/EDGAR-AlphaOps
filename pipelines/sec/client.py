import httpx
import time
from tenacity import retry, stop_after_attempt, wait_exponential
from config import get_settings
import logging
from typing import Optional, Dict, Any

# Global Rate Limiter
# Simple token bucket or just strict sleep. 
# SEC limit is 10 requests per second.
# We will enforce 0.1s sleep between requests minimum to be safe + simplistic.

class RateLimiter:
    def __init__(self, requests_per_second: int = 10):
        self.interval = 1.0 / requests_per_second
        self.last_request_time = 0.0

    def wait(self) -> None:
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < self.interval:
            time.sleep(self.interval - elapsed)
        self.last_request_time = time.time()

global_limiter = RateLimiter(requests_per_second=10)

class SecClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        if "example.com" in self.settings.SEC_USER_AGENT:
             logging.warning("⚠️  Using default SEC User-Agent. Please update .env with your actual email for compliance!")
        
        self.headers = {
            "User-Agent": self.settings.SEC_USER_AGENT,
            "Accept-Encoding": "gzip, deflate",
        }
        self.client = httpx.Client(headers=self.headers, timeout=30.0, follow_redirects=True)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _get(self, url: str) -> httpx.Response:
        """
        Internal GET with rate limiting and retries.
        """
        global_limiter.wait()
        response = self.client.get(url)
        response.raise_for_status()
        return response

    def get_filing_html(self, url: str) -> str:
        """
        Download filing text/html.
        """
        # SEC URLs often are http but redirect to https.
        # Ensure url is using https
        if url.startswith("http://"):
            url = url.replace("http://", "https://", 1)
            
        logging.info(f"Downloading filing: {url}")
        resp = self._get(url)
        return resp.text

    def get_rss_feed(self, count: int = 100) -> bytes:
        """
        Fetch the RSS feed.
        """
        url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=&company=&dateb=&owner=include&start=0&count={count}&output=atom"
        logging.info("Polling SEC RSS feed...")
        resp = self._get(url)
        return resp.content
