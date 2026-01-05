
import pytest
import time
import concurrent.futures
from pipelines.sec.client import SecClient, GlobalRateLimiter
from pipelines.storage import MinIOClient
from config import get_settings

settings = get_settings()

def test_user_agent_enforcement(monkeypatch):
    monkeypatch.setattr(settings, "SEC_USER_AGENT", "AlphaOps/Test (test@alphaops.ai)")
    client = SecClient()
    assert "User-Agent" in client.headers
    assert client.headers["User-Agent"] == "AlphaOps/Test (test@alphaops.ai)"

def test_deterministic_storage_path():
    storage = MinIOClient()
    cik = "0000320193"
    acc = "0000320193-23-000106"
    expected = f"raw/{cik}/{acc}.txt"
    assert storage.get_storage_path(cik, acc, "txt") == expected
    assert storage.get_storage_path(cik, acc, "html") == f"raw/{cik}/{acc}.html"

@pytest.mark.slow
def test_global_rate_limiter():
    """
    Spawns 20 threads trying to acquire tokens.
    Should take at least ~2 seconds total if rate is 10/s.
    """
    limiter = GlobalRateLimiter(rate=10)
    
    def task(i):
        limiter.acquire()
        return time.time()

    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(task, i) for i in range(25)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    duration = time.time() - start_time
    print(f"\nTime taken for 25 requests: {duration:.2f}s")
    
    # 25 requests at 10/s should take at least 2.4s ideally (0-10: 1s, 11-20: 1s, 21-25: 0.5s)
    # Allowing some jitter/latency, but it shouldn't be instant (<0.5s)
    assert duration > 1.5, "Rate limiter was too fast! Leaking tokens?"

