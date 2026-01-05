FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY pyproject.toml .
# Create a dummy README so pip install -e . works if referenced, 
# or just install deps directly. 
# We'll stick to installing requirements generated from toml or just pip install .
RUN pip install --upgrade pip
RUN pip install -e .[dev]

# Install specific prod deps that might not be in pyproject.toml yet
RUN pip install "fastapi>=0.109.0" "uvicorn>=0.27.0" "celery[redis]>=5.3.0" \
    "minio>=7.2.0" "sqlalchemy>=2.0.0" "psycopg2-binary>=2.9.0" \
    "boto3>=1.34.0" "requests>=2.31.0" "redis>=5.0.0" \
    "beautifulsoup4>=4.12.0" "lxml>=5.1.0" "duckdb>=0.9.2" \
    "langchain-text-splitters>=0.2.0" "sentence-transformers>=2.2.2" "qdrant-client>=1.7.0"

COPY . .

# Default command (overridden in compose)
CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
