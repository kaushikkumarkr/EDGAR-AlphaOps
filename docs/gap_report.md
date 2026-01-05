# Gap Report & Migration Plan

## Current State Audit
- **Infrastructure**: `docker-compose.yml` services (Postgres, MinIO, Valkey, Qdrant, Phoenix) are present.
- **Dependencies**: `pyproject.toml` covers most requirements (FastAPI, DuckDB, Qdrant, etc.).
- **Structure**: Repo structure (`apps`, `pipelines`, `ds`, `rag`) matches expectations.
- **Legacy**: mix of `apps.cli` and some root scripts (`verify_*.py`).

## Gaps Identified

### 1. Ingestion Reliability
- **Rate Limiting**: Global rate limiter logic exists in `pipelines/sec/client.py` (checked previously) but need to verify it's shared via Redis across workers.
- **Reconciliation**: `pipelines/reconcile.py` exists, but need to ensure it runs nightly via Celery Beat.

### 2. Storage & Replay
- **MinIO**: Paths need to be deterministic (`raw/{cik}/{ex}/{acc}.txt`).
- **DuckDB**: Need to confirm `lakehouse` paradigm is used (Parquet files in MinIO, queried via DuckDB).

### 3. Citations
- **Strict Parsing**: Requirement for `start_offset/end_offset` in citations. Existing `rag` pipeline needs strict verification.

### 4. Advanced DS
- **Event Study**: Logic exists in `pipelines/analytics`, but needs to be robust (placebo tests).
- **Risk Score**: Needs calibration logic.

### 5. Observability
- **Loki**: Missing from `docker-compose.yml`.
- **Instrumentation**: Need to ensure OpenTelemetry SDK is initialized in API and Worker.

### 6. LLM Serving
- **vLLM**: Requirement for Prod. Currently utilizing `mlx_lm` for Mac Dev. Need to add `vllm-server` to compose (commented out or profile).

## Migration Plan (Sprint 0)
1.  **Refactor**: detailed cleaning of `docker-compose.yml` to matching standard.
2.  **Makefile**: Align targets exactly with "Deliverable Commands".
3.  **Config**: Ensure `.env` is robust.
4.  **Logging**: Standardize JSON structured logging for Loki.
