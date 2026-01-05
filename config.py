from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # Project Info
    PROJECT_NAME: str = "EDGAR AlphaOps"
    VERSION: str = "0.1.0"
    
    # SEC Config
    SEC_USER_AGENT: str = "EDGAR-AlphaOps-Research/0.1 (contact@example.com)"
    
    # Data Storage
    DATA_DIR: str = "./data"
    
    # MotherDuck (SQL Cloud)
    MOTHERDUCK_TOKEN: Optional[str] = None
    
    # Vector Integration
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: Optional[str] = None
    
    # LLM
    OPENAI_BASE_URL: str = "http://localhost:8080/v1"
    OPENAI_API_KEY: str = "EMPTY"
    MODEL_NAME: str = "mlx-community/Llama-3.2-3B-Instruct-4bit"
    
    # Database (Postgres)
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "edgar_ops"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    
    # Object Storage (MinIO)
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_RAW: str = "sec-raw"
    MINIO_BUCKET_ARTIFACTS: str = "artifacts"
    
    # Queue/Cache (Valkey/Redis)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    
    # Observability (Phoenix / Otel)
    PHOENIX_COLLECTOR_ENDPOINT: str = "http://localhost:4317"
    PHOENIX_PROJECT_NAME: str = "edgar-alphaops"

    # Langfuse
    LANGFUSE_PUBLIC_KEY: Optional[str] = None
    LANGFUSE_SECRET_KEY: Optional[str] = None
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

@lru_cache
def get_settings() -> Settings:
    return Settings()
