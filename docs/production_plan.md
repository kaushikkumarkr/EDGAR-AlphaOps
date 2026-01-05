# EDGAR AlphaOps v2 - Zero-Cost Production Deployment Plan

This guide outlines how to deploy EDGAR AlphaOps to a live production environment using exclusively **free tier** and **open-source** resources.

## 🏗 The "Zero-Cost" Stack

| Component | Local Dev (Current) | Production (Free Tier) | Why? |
| :--- | :--- | :--- | :--- |
| **Compute (App)** | Docker Compose (Local) | **Hugging Face Spaces** (Docker) | Generous free tier (2vCPU, 16GB RAM), keeps app alive. |
| **Compute (Jobs)** | Local Cron / Makefile | **GitHub Actions** (Scheduled) | Free 2000 min/month is enough for daily ingestion. |
| **LLM Inference** | MLX (Mac Silicon) | **Groq API** (Llama 3) | Currently free, extremely fast (tokens/sec), OpenAI-compatible. |
| **SQL Lake** | DuckDB (Local Files) | **MotherDuck** | Managed DuckDB. Shared-tier is free (10GB storage). |
| **Vector DB** | Qdrant (Local Container) | **Qdrant Cloud** | Free tier includes 1GB cluster (enough for ~1M vectors). |
| **Observability** | Phoenix (Local) | **LangFuse Cloud** | Free hobby tier (50k traces/mo). Excellent LangGraph integration. |

---

## 📅 Deployment Steps

### Phase 1: External Services Setup (One-time)

1.  **Qdrant Cloud**:
    -   Sign up at [cloud.qdrant.io](https://cloud.qdrant.io/).
    -   Create a **Free Tier Cluster**.
    -   Get `QDRANT_HOST` (URL) and `QDRANT_API_KEY`.
2.  **MotherDuck**:
    -   Sign up at [motherduck.com](https://motherduck.com/).
    -   Get Service Token (`motherduck_token`).
    -   *Migration*: Update `lakehouse/db.py` to connect to `md:my_db?motherduck_token=...` instead of local file.
3.  **Groq**:
    -   Sign up at [console.groq.com](https://console.groq.com/).
    -   Get API Key.
4.  **LangFuse** (Optional but recommended):
    -   Sign up at [langfuse.com](https://langfuse.com/).
    -   Get Keys.

### Phase 2: Configuration Update

Update your `.env` (or secrets manager) to switch providers:

```bash
# .env (Production)

# 1. LLM (Switch from MLX to Groq)
OPENAI_BASE_URL="https://api.groq.com/openai/v1"
OPENAI_API_KEY="gsk_..."
MODEL_NAME="llama3-70b-8192"

# 2. Databases
# SQL
DUCKDB_PATH="md:edgar_alphaops"
MOTHERDUCK_TOKEN="<token>"
# Vector
QDRANT_HOST="https://<cluster>.qdrant.tech"
QDRANT_API_KEY="<key>"

# 3. Observability
LANGFUSE_PUBLIC_KEY="pk-..."
LANGFUSE_SECRET_KEY="sk-..."
```

### Phase 3: Application Deployment (Hugging Face Spaces)

Hugging Face Spaces supports Dockerfiles directly.

1.  **Create Space**:
    -   Go to HF Spaces -> Create New.
    -   SDK: **Docker**.
    -   Hardware: **Free CPU Basic**.
2.  **Dockerfile**:
    -   Use the existing project structure.
    -   Ensure `CMD` runs the Streamlit app: `CMD ["streamlit", "run", "apps/streamlit_app.py", "--server.port", "7860"]`.
3.  **Secrets**:
    -   Add all `.env` variables as **Repository Secrets** in the HF Space settings.
4.  **Push**:
    -   `git remote add space https://huggingface.co/spaces/<your-username>/edgar-alphaops`
    -   `git push space main`

### Phase 4: Ingestion Automation (GitHub Actions)

Don't run heavy ingestion on the HF Space (it restarts). Use GitHub Actions for daily updates.

Create `.github/workflows/daily_ingest.yml`:

```yaml
name: Daily Ingestion
on:
  schedule:
    - cron: '0 8 * * 1-5' # 8 AM Mon-Fri (Pre-market)
  workflow_dispatch:

jobs:
  ingest:
    runs-on: ubuntu-latest
    env:
      SEC_USER_AGENT: ${{ secrets.SEC_USER_AGENT }}
      MOTHERDUCK_TOKEN: ${{ secrets.MOTHERDUCK_TOKEN }}
      QDRANT_HOST: ${{ secrets.QDRANT_HOST }}
      QDRANT_API_KEY: ${{ secrets.QDRANT_API_KEY }}
      OPENAI_API_KEY: ${{ secrets.GROQ_API_KEY }}
      OPENAI_BASE_URL: "https://api.groq.com/openai/v1"
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      # Daily Ingest for watchlist
      - run: python -m apps.cli ingest-market --tickers AAPL,MSFT,NVDA
      - run: python -m apps.cli ingest-rag --tickers AAPL,MSFT,NVDA
      - run: python -m apps.cli compute-ds --tickers AAPL,MSFT,NVDA
```

## 🔄 Workflow Summary

1.  **08:00 AM**: GitHub Action wakes up -> Ingests new Prices/Docs -> Pushes data to **MotherDuck** & **Qdrant Cloud**.
2.  **User**: Visits Hugging Face Space URL.
3.  **HF Space**:
    -   Streamlit App loads (stateless container).
    -   Connects to MotherDuck (SQL) & Qdrant (Vector) to read *persisted* data.
    -   User Query -> **Groq API** (Llama 3) -> Answer.

## 🚀 Impact

-   **Zero Cost**: All selected tiers have generous free limits.
-   **No Hardware Dependency**: Removes reliance on Mac Silicon.
-   **Persistent State**: MotherDuck/Qdrant act as the persistent brain independent of app restarts.
