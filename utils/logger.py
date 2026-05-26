import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "framework.log"

# Make sure logs directory exists
LOG_DIR.mkdir(exist_ok=True)

def setup_logger(name: str = "openweather_fw", log_level: int = logging.DEBUG) -> logging.Logger:
    """Sets up a robust, rotation-based logger with file and console handlers."""
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(log_level)
    
    # Formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)8s] %(message)s (%(filename)s:%(lineno)d)",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler with rotation (10 MB per file, max 5 backups)
    file_handler = RotatingFileHandler(
        filename=LOG_FILE,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

# Primary logger instance
logger = setup_logger()
