import time
import redis
import requests
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from config import get_settings
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


logger = logging.getLogger(__name__)
settings = get_settings()


class GlobalRateLimiter:
    """
    Redis-backed Token Bucket for Global Rate Limiting (10 req/sec strict).
    Uses a rolling window or per-second counter key.
    """
    def __init__(self, key="sec_global_limit", rate=10):
        self.redis = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
        self.key = key
        self.rate = rate

    def acquire(self):
        """
        Acquire a token. Blocks until available.
        Strict approach: 1 request per 0.1s bucket.
        """
        while True:
            try:
                # 1. Get current decisecond bucket (100ms)
                now = time.time()
                bucket = int(now * 10) 
                bucket_key = f"{self.key}:{bucket}"
                
                # 2. Increment
                current_count = self.redis.incr(bucket_key)
                
                # 3. Set expiry (1 sec is plenty for 0.1s bucket)
                if current_count == 1:
                    self.redis.expire(bucket_key, 1)
                
                # 4. Check limit (1 per 100ms = 10 per sec)
                if current_count <= 1:
                    return
                else:
                    # Sleep until next decisecond
                    next_bucket_time = (bucket + 1) / 10.0
                    sleep_time = next_bucket_time - time.time() + 0.01
                    if sleep_time > 0:
                        time.sleep(sleep_time)
            except redis.RedisError as e:
                logger.error(f"Redis error in RateLimiter: {e}")
                time.sleep(0.1)

class SecClient:
    def __init__(self):
        self.limiter = GlobalRateLimiter()
        self.headers = {"User-Agent": settings.SEC_USER_AGENT, "Accept-Encoding": "gzip, deflate"}
        if "example.com" in settings.SEC_USER_AGENT:
             logger.warning("Using default/example User-Agent! Please update SEC_USER_AGENT in .env")

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        reraise=True
    )
    def _get(self, url: str) -> requests.Response:
        self.limiter.acquire()
        response = requests.get(url, headers=self.headers, timeout=20)
        response.raise_for_status()
        return response

    def get(self, url: str) -> requests.Response:
        """Public wrapper for _get."""
        return self._get(url)

    def get_filing_html(self, url: str) -> str:
        """
        Download filing text/html.
        """
        if url.startswith("http://"):
            url = url.replace("http://", "https://", 1)
            
        logging.info(f"Downloading filing: {url}")
        resp = self._get(url)
        return resp.text

    def get_filing_bytes(self, url: str) -> bytes:
        """Download binary content."""
        if url.startswith("http://"):
            url = url.replace("http://", "https://", 1)
        logging.info(f"Downloading binary: {url}")
        resp = self._get(url)
        return resp.content

    def get_rss_feed(self, count: int = 100) -> bytes:
        """
        Fetch the SEC RSS feed (Atom).
        """
        url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=&company=&dateb=&owner=include&start=0&count={count}&output=atom"
        logging.info("Polling SEC RSS feed...")
        # RSS might not follow strict 10/s limits the same way as archives? 
        # But safely apply same limiter.
        resp = self._get(url)
        return resp.content

