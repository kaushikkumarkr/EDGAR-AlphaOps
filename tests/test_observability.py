from observability.logging import setup_logging
from observability.setup import setup_observability
import logging

def test_logging_setup():
    setup_logging()
    logger = logging.getLogger("test_logger")
    # Just verify it doesn't crash; asserting output in stdout is harder here without capsys
    logger.info("Test log message")

def test_observability_setup():
    # Should not crash even if collector is offline (it logs warning)
    setup_observability()
