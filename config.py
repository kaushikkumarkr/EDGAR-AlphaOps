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
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

@lru_cache
def get_settings() -> Settings:
    return Settings()
