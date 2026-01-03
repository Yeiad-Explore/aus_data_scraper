"""Structured logging configuration using structlog."""

import logging
import sys
from pathlib import Path

import structlog


def setup_logging(log_file: Path | None = None, console_level: str = "INFO") -> None:
    """Configure structured logging with JSON format.

    Args:
        log_file: Optional path to log file. If None, only console logging is enabled.
        console_level: Logging level for console output (default: INFO)
    """
    # Create log directory if file logging is enabled
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, console_level.upper()),
        stream=sys.stdout,
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer() if not log_file else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        logging.root.addHandler(file_handler)
