# Validation Coverage Matrix

| Requirement | Implementation Path | Verification Command | Expected Artifact |
|-------------|---------------------|----------------------|-------------------|
| Docker Stack | `docker-compose.yml` | `make up` | Running Containers (Qdrant, Phoenix) |
| Makefile Targets | `Makefile` | `make help` | List of targets (ingest, test, demo) |
| SEC Compliance | `pipelines/sec/client.py` | `grep "User-Agent" pipelines/sec/client.py` | Code with rate limiter |
| SEC RSS Ingestion | `pipelines/sec/rss.py` | `make test` | Logic verified by `test_rss_cycle` |
| XBRL Ingestion | `pipelines/xbrl/facts.py` | `make demo` (Step 3) | `xbrl_facts` table populated |
| XBRL Normalization | `pipelines/xbrl/quality_gates.py` | `check_data.py` | `frame` column populated (verified 79%) |
| Market Data Ingestion | `pipelines/market/client.py` | `make demo` (Step 1) | `prices` table matches YFinance history |
| Daily Returns | `pipelines/market/client.py`(pandas) | Queries to `prices` table | `daily_return` and `volatility_30d` columns |
| Vector Indexing | `apps/cli.py` (ingest-rag) | `make build_index` | Qdrant collection `sec_filings` populated |
| RAG Citations | `agents/tools.py` | `verify_rag_citations.py` | `[Source: AAPL 10-K 2023-11-03]` confirmed |
| DS: Risk Model | `ds/risk_model/engine.py` | `make compute_risk` | Table `risk_metrics` (VaR, Regime) populated |
| GraphRAG | `rag/graphrag/` | `make build_graph` | Table `graph_entities` populated |
| Agent Router | `agents/graph.py` | `make serve_llm` + `run_ui` | System Prompt guides tool selection (SQL/Graph) |
| DS: Event Study | `ds/event_study/engine.py` | `make compute_ds` | Table `event_studies` populated with CAR |
| RAG: Citations | `agents/tools.py` | `make demo` | Response with `[Source: ...]` |
| Observability | `observability/setup.py` | `http://localhost:6006` | Traces in Phoenix |
