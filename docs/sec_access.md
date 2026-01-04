# SEC Fair Access Compliance

This document outlines how **EDGAR AlphaOps** adheres to the SEC's [Fair Access Policy](https://www.sec.gov/os/accessing-edgar-data).

## 1. User-Agent Declaration
All requests to `sec.gov` include a `User-Agent` header in the specified format:
`User-Agent: Sample Company Name AdminContact@<sample company domain>.com`

**Implementation**:
- Configured via `SEC_USER_AGENT` in `.env`.
- Enforced in `pipelines/sec/client.py`.
- Application logs a warning if the default placeholder is detected.

## 2. Rate Limiting
The SEC limits traffic to **10 requests per second**.

**Implementation**:
- A global `RateLimiter` class in `pipelines/sec/client.py` enforces a minimum interval of **0.1 seconds** between requests.
- This is a hard client-side limit that blocks formatting requests until the token bucket allows.

## 3. Excessive Load Prevention (Backoff)
In case of server errors (5xx) or rate limit hits (429), the system employs exponential backoff.

**Implementation**:
- Uses the `tenacity` library.
- Strategy: `wait_exponential(multiplier=1, min=2, max=10)`.
- Stops after 3 failed attempts to prevent hammering.

## 4. Efficient Data Usage
- **Caching**: We assume local file storage (`data/filings`) acts as a cache. We never re-download an Accession Number if it exists locally.
- **gzip Compression**: The `Accept-Encoding: gzip, deflate` header is sent to reduce bandwidth.
