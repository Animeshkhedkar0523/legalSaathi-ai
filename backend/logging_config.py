"""
Logging Configuration for LegalSaathi
"""
import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path

# Create logs directory
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Log file path
log_file = logs_dir / f"legalsaathi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Create logger
logger = logging.getLogger("legalsaathi")
logger.setLevel(logging.DEBUG)

# File handler (all logs)
file_handler = logging.handlers.RotatingFileHandler(
    log_file,
    maxBytes=10_000_000,  # 10MB
    backupCount=10
)
file_handler.setLevel(logging.DEBUG)

# Console handler (INFO and above)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers
logger.addHandler(file_handler)
logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(f"legalsaathi.{name}")


# Module-level logger for this file
__logger = get_logger("logging")

if __name__ == "__main__":
    __logger.info("Logging configuration loaded")
    __logger.debug("This is a debug message")
    __logger.info("This is an info message")
    __logger.warning("This is a warning message")
    __logger.error("This is an error message")
