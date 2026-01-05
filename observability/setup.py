from openinference.instrumentation.langchain import LangChainInstrumentor
from phoenix.otel import register
from config import get_settings
import logging

def setup_observability() -> None:
    """
    Initialize Phoenix tracing and OTEL instrumentation.
    """
    settings = get_settings()
    try:
        # Register the Phoenix OTEL collector
        register(
            endpoint=settings.PHOENIX_COLLECTOR_ENDPOINT,
            project_name=settings.PROJECT_NAME
        )
        
        # Auto-instrument LangChain
        LangChainInstrumentor().instrument()
        
        logging.getLogger(__name__).info(f"Observability initialized. Collector: {settings.PHOENIX_COLLECTOR_ENDPOINT}")
    except Exception as e:
        logging.getLogger(__name__).warning(f"Failed to initialize observability: {e}")
