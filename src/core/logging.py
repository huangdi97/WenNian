"""Structured logging setup with console and rotating file handlers.

Provides color-coded console output and daily-rotating file logs
with the format: [timestamp][module][LEVEL] message.
"""

import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import AppConfig


COLORS = {
    "DEBUG": "\033[36m",
    "INFO": "\033[32m",
    "WARNING": "\033[33m",
    "ERROR": "\033[31m",
    "CRITICAL": "\033[35m",
}
RESET = "\033[0m"


class _ColorFormatter(logging.Formatter):
    """Formatter that applies ANSI color codes based on log level."""

    def format(self, record: logging.LogRecord) -> str:
        color = COLORS.get(record.levelname, "")
        if color:
            record.levelname = f"{color}{record.levelname}{RESET}"
            record.name = f"{color}{record.name}{RESET}"
        return super().format(record)


def setup_logging(config: "AppConfig") -> None:
    """Configure the root logger with console and file handlers.

    Args:
        config: Application configuration instance.

    Logs are written to stderr (console) and to logs/wennian.log
    with daily rotation and 30-day retention.
    """
    log_level_name = config.get("logging.level", "INFO")
    log_level = getattr(logging, log_level_name.upper(), logging.INFO)
    log_dir = Path(config.get("logging.dir", "logs"))
    log_dir.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(log_level)

    fmt = "[%(asctime)s][%(name)s][%(levelname)s] %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    # Console handler
    console = logging.StreamHandler(sys.stderr)
    console.setLevel(log_level)
    console.setFormatter(_ColorFormatter(fmt, datefmt=datefmt))
    root.addHandler(console)

    # File handler with daily rotation
    log_file = log_dir / "wennian.log"
    file_handler = TimedRotatingFileHandler(
        str(log_file), when="midnight", interval=1, backupCount=30, encoding="utf-8"
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(fmt, datefmt=datefmt))
    root.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Retrieve a logger instance for the given module name.

    Args:
        name: Typically __name__ of the calling module.

    Returns:
        A configured logger instance.
    """
    return logging.getLogger(name)
