"""
Logging configuration for the Assort Health Voice Agent.
"""
import logging

def setup_logger():
    """
    Configure logging for the application.
    """
    # Configure logging - set to minimal logging
    logging.basicConfig(level=logging.ERROR)
    
    # Configure specific loggers
    for logger_name in ["livekit", "livekit.agents", "httpx", "httpcore", "asyncio"]:
        logging.getLogger(logger_name).setLevel(logging.ERROR)
    
    # Create application logger
    app_logger = logging.getLogger("assort_health")
    app_logger.setLevel(logging.INFO)
    
    # Set patient_db logs to WARNING to reduce initialization messages
    logging.getLogger("patient_db").setLevel(logging.WARNING)
    
    return app_logger

# Create a logger instance
logger = setup_logger()
