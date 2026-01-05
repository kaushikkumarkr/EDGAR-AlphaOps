# Project Assumptions & Constraints

## 1. Environment & Hardware
- **Production Target**: Single `n1-standard-8` (or equivalent) VM with Docker Compose.
- **Development**: Apple Silicon (M1/M2/M3).
  - *Assumption*: `MLX` is used for local LLM inference to save battery/latency.
  - *Constraint*: CI/CD pipeline must use CPU-compatible inference (e.g., `vLLM` CPU mode or mock) or have GPU runners.

## 2. Data Budget & Compliance
- **Budget**: $0.00. Strictly Free Tier or Open Source.
- **SEC Regulation**:
  - Global Rate Limit: 10 requests/second.
  - User-Agent: `EDGAR-AlphaOps-Research/1.0 (contact@example.com)`.
  - Data Source: Only `sec.gov` public endpoints. No `sec-api.io` (paid).

## 3. Security
- **Authentication**: Scope is "Internal Tool". No complex RBAC/SSO implemented in V1.
- **Secrets**: Managed via `.env` file (Docker) and GitHub Secrets (CI). No HashiCorp Vault.

## 4. Reliability
- **SLA**: Best effort.
- **Data Durability**:
  - Raw HTML/XML: MinIO (Reliable).
  - Metadata: Postgres (Reliable).
  - Derived/Cache: Redis/DuckDB (Ephemeral/Recomputable).

## 5. Model serving
- **Prod**: `vLLM` container serving OpenAI-compatible API.
- **Dev**: `mlx-lm` server serving OpenAI-compatible API.
- *Assumption*: Application logic is agnostic to the backend as long as it speaks OpenAI protocol.
