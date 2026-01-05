from fastapi import FastAPI
from config import get_settings

from observability.logging import setup_logging

# Setup Observability
setup_logging()

settings = get_settings()
app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

@app.get("/health")
def health_check():
    return {
        "status": "ok", 
        "version": settings.VERSION,
        "services": {
            "postgres": "unknown", # To be implemented
            "redis": "unknown",    # To be implemented
            "minio": "unknown"     # To be implemented
        }
    }

@app.get("/")
def root():
    return {"message": "Welcome to EDGAR AlphaOps v2 API"}

# Include Routers
from apps.api.routers import rag, analytics
app.include_router(rag.router, prefix="/api/v1", tags=["RAG"])
app.include_router(analytics.router, prefix="/api/v1", tags=["Analytics"])
