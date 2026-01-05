# Sprint Plan: EDGAR AlphaOps Upgrade

## Sprint 0: Foundation & Scaffolding
**Goal**: Production-ready local environment (Containerized Stack + CI/CD Skeleton).
- [ ] Fix `docker-compose.yml`: Add Loki, verify network, ensured vLLM placeholder.
- [ ] Fix `Makefile`: Implement all required targets (stubs where needed).
- [ ] CI Skeleton: GitHub Actions for lint/test.
- [ ] Logging: JSON logs enabled for Loki.
- **DoD**: `make up` starts all services. `make test` runs.

## Sprint 1: SEC Compliance & Ingestion
**Goal**: Reliable, rate-limited ingestion pipeline.
- [ ] Global Redis Rate Limiter (10req/s).
- [ ] User-Agent Enforcer.
- [ ] MinIO Raw Storage (Deterministic Paths).
- [ ] RSS Watcher (Poller Task).
- **DoD**: `make ingest_recent` runs without error, adhering to rate limits.

## Sprint 2: Storage, Reconcile & XBRL
**Goal**: Durability and Structured Data.
- [ ] Postgres Metadata Models (Filing, State).
- [ ] Nightly Reconcile Task (Index vs DB).
- [ ] XBRL Parsing (Facts -> DuckDB).
- **DoD**: `make reconcile_index` works. XBRL data available in SQL.

## Sprint 3: Market Data & Feature Store
**Goal**: Analytical Marts.
- [ ] Stooq Ingestion (Daily OHLC).
- [ ] DuckDB Feature Store (Point-in-Time Joins).
- [ ] Returns Calculation.
- **DoD**: `make compute_ds` produces parquet files in MinIO.

## Sprint 4: RAG Foundation (Strict Citations)
**Goal**: Grounded Retrieval.
- [ ] Chunker with Offsets.
- [ ] Embedding Pipeline (Sentence Transformers).
- [ ] Qdrant Indexing with Metadata.
- [ ] `/ask` Endpoint with Citations.
- **DoD**: `make build_index` works. Query returns explicit source citations.

## Sprint 5: Event Study Engine
**Goal**: Alpha Signal Generation.
- [ ] Market Model Regression (Alpha/Beta).
- [ ] CAR Calculation ([-2,+2]).
- [ ] Robustness Checks.
- **DoD**: Event study artifacts generated for demo tickers.

## Sprint 6: Risk & Volatility
**Goal**: Advanced Risk Modeling.
- [ ] Volatility Regime Detection (GARCH/Rolling).
- [ ] Risk Score Calibration.
- **DoD**: Risk metrics available via API.

## Sprint 7: GraphRAG & Router
**Goal**: Multi-hop Reasoning.
- [ ] Entity Extraction.
- [ ] Graph Construction (NetworkX/Neo4j lite?).
- [ ] Router Agent (Vector vs Graph).
- **DoD**: Complex multi-hop queries answered.

## Sprint 8: Observability & Eval Gating
**Goal**: Production Trust.
- [ ] RAGAS Eval Suite.
- [ ] Phoenix Tracing (End-to-End).
- [ ] Grafana Dashboards.
- **DoD**: `make eval` generates report. Dashboards show metrics.
