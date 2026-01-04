# Project Assumptions

1. **Market Data Source**: The requirement is "Free market prices (Stooq)". I am using `yfinance` (Yahoo Finance) as the primary free source as it's more python-friendly and reliable for US equities. Stooq is acceptable but YF is the de-facto standard for free Python financial data.
2. **LLM**: Local execution via `MLX` (Apple Silicon) or `vLLM` (Linux/CUDA) is assumed. The system defaults to `localhost:8080/v1` (OpenAI compatible).
3. **Database**: DuckDB is used as the "Lakehouse" for structured data (Prices, XBRL, Features) due to its zero-dependency local nature.
4. **Vector DB**: Qdrant is selected over Chroma for its robust filtering and performance.
5. **Event Study**: We assume a simple "Market Model" using SPY or similar as the benchmark for computing Abnormal Returns.
