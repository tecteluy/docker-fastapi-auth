import logging
import logging.handlers
import os
from pathlib import Path
from .config import settings

def setup_logging():
    """
    Configure logging for the FastAPI application.
    """
    # Create logs directory if it doesn't exist
    logs_dir = Path("/app/logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Set the root logger level
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Console handler for general logs
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(settings.log_format)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    
    # File handler for application logs with rotation
    app_log_file = logs_dir / "app.log"
    file_handler = logging.handlers.RotatingFileHandler(
        app_log_file,
        maxBytes=settings.log_file_max_bytes,
        backupCount=settings.log_file_backup_count,
        encoding='utf-8'
    )
    file_formatter = logging.Formatter(settings.log_format)
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    root_logger.addHandler(file_handler)
    
    # Error log file handler
    error_log_file = logs_dir / "error.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=settings.log_file_max_bytes,
        backupCount=settings.log_file_backup_count,
        encoding='utf-8'
    )
    error_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    )
    error_handler.setFormatter(error_formatter)
    error_handler.setLevel(logging.ERROR)
    root_logger.addHandler(error_handler)
    
    # OAuth service logger
    oauth_logger = logging.getLogger("fastapi.oauth")
    oauth_file = logs_dir / "oauth.log"
    oauth_handler = logging.handlers.RotatingFileHandler(
        oauth_file,
        maxBytes=settings.log_file_max_bytes,
        backupCount=settings.log_file_backup_count,
        encoding='utf-8'
    )
    oauth_handler.setFormatter(file_formatter)
    oauth_logger.addHandler(oauth_handler)
    oauth_logger.setLevel(logging.INFO)
    
    # Authentication service logger
    auth_logger = logging.getLogger("fastapi.auth")
    auth_file = logs_dir / "auth.log"
    auth_handler = logging.handlers.RotatingFileHandler(
        auth_file,
        maxBytes=settings.log_file_max_bytes,
        backupCount=settings.log_file_backup_count,
        encoding='utf-8'
    )
    auth_handler.setFormatter(file_formatter)
    auth_logger.addHandler(auth_handler)
    auth_logger.setLevel(logging.INFO)
    
    # Database logger
    db_logger = logging.getLogger("fastapi.database")
    db_file = logs_dir / "database.log"
    db_handler = logging.handlers.RotatingFileHandler(
        db_file,
        maxBytes=settings.log_file_max_bytes,
        backupCount=settings.log_file_backup_count,
        encoding='utf-8'
    )
    db_handler.setFormatter(file_formatter)
    db_logger.addHandler(db_handler)
    db_logger.setLevel(logging.INFO)
    
    # Suppress overly verbose third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    # Log startup message
    logger = logging.getLogger("fastapi.startup")
    logger.info("Logging system initialized")
    logger.info(f"Log level: {settings.log_level}")
    logger.info(f"Request logging enabled: {settings.enable_request_logging}")
    logger.info(f"Logs directory: {logs_dir}")
    
    return root_logger
