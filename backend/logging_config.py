"""
Logging Configuration for LegalSaathi
"""
import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import json

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

# Monitoring metrics
class LogMetrics:
    """Track logging metrics"""
    def __init__(self):
        self.total_logs = 0
        self.debug_logs = 0
        self.info_logs = 0
        self.warning_logs = 0
        self.error_logs = 0
        self.critical_logs = 0
        self.start_time = datetime.now()
    
    def increment(self, level: str):
        """Increment log count for level"""
        self.total_logs += 1
        if level == "DEBUG":
            self.debug_logs += 1
        elif level == "INFO":
            self.info_logs += 1
        elif level == "WARNING":
            self.warning_logs += 1
        elif level == "ERROR":
            self.error_logs += 1
        elif level == "CRITICAL":
            self.critical_logs += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get logging statistics"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        return {
            "total_logs": self.total_logs,
            "debug_logs": self.debug_logs,
            "info_logs": self.info_logs,
            "warning_logs": self.warning_logs,
            "error_logs": self.error_logs,
            "critical_logs": self.critical_logs,
            "start_time": self.start_time.isoformat(),
            "uptime_seconds": uptime
        }

# Global metrics instance
log_metrics = LogMetrics()

# Custom handler to track metrics
class MetricsHandler(logging.Handler):
    """Handler that tracks logging metrics"""
    def emit(self, record: logging.LogRecord):
        log_metrics.increment(record.levelname)

# Add metrics handler
metrics_handler = MetricsHandler()
logger.addHandler(metrics_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    child_logger = logging.getLogger(f"legalsaathi.{name}")
    # Add metrics handler to child logger too
    if not any(isinstance(h, MetricsHandler) for h in child_logger.handlers):
        child_logger.addHandler(metrics_handler)
    return child_logger


def get_log_stats() -> Dict[str, Any]:
    """Get logging statistics"""
    return log_metrics.get_stats()



# Module-level logger for this file
__logger = get_logger("logging")

if __name__ == "__main__":
    __logger.info("Logging configuration loaded")
    __logger.debug("This is a debug message")
    __logger.info("This is an info message")
    __logger.warning("This is a warning message")
    __logger.error("This is an error message")
