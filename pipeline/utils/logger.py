"""
pipeline/utils/logger.py
Centralized logger setup for the ETL pipeline.
"""

import logging
import sys
from pipeline.utils.config import config

def get_logger(name: str) -> logging.Logger:
    """Create and return a configured logger instance."""
    logger = logging.getLogger(name)
    
    # Prevent duplicate handlers if get_logger is called multiple times
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    config.log_dir.mkdir(parents=True, exist_ok=True)
    log_file = config.log_dir / f"pipeline_{config.pipeline_date}.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
