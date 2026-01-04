from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # Project Info
    PROJECT_NAME: str = "EDGAR AlphaOps"
    VERSION: str = "0.1.0"
    
    # SEC Config
    SEC_USER_AGENT: str = "EDGAR-AlphaOps-Research/0.1 (contact@example.com)"
    
    # Paths
    DATA_DIR: str = "./data"
    
    # Vector Integration
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    
    # Observability
    PHOENIX_COLLECTOR_ENDPOINT: str = "http://localhost:4317"

    # LLM
    OPENAI_BASE_URL: str = "http://localhost:8080/v1"
    OPENAI_API_KEY: str = "EMPTY"
    MODEL_NAME: str = "mlx-community/Llama-3.2-3B-Instruct-4bit"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

@lru_cache
def get_settings() -> Settings:
    return Settings()
