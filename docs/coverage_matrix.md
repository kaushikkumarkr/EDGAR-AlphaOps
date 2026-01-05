# Coverage Matrix

| Sprint | Component | Requirement | File(s) | Verification Command | Artifact |
|--------|-----------|-------------|---------|----------------------|----------|
| S0 | Foundation | Docker Compose | `docker-compose.yml` | `make up` | `docker ps` services up |
| S0 | Foundation | FastAPI Skeleton | `apps/api/main.py` | `curl localhost:8000/health` | `{"status":"ok"}` |
| S1 | Ingestion | Global Rate Limit | `pipelines/sec/client.py` | `pytest tests/test_rate_limit.py` | 10 req/s max |
| S1 | Ingestion | MinIO Storage | `pipelines/storage/minio.py` | `make ingest_recent` | Objects in MinIO |
| S4 | RAG | Citation Contract | `rag/citation.py` | `make demo` | JSON with offsets/hash |
| S5 | DS | Event Study | `ds/event_study.py` | `make compute_ds` | CAR plots/tables |
| S8 | Eval | RAGAS Gating | `eval/ragas/pipeline.py` | `make eval` | `artifacts/eval/report.json` |
