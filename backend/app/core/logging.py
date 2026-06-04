"""
Structured logging configuration.
"""

import logging
import sys
from datetime import datetime
from typing import Any, Dict

from fastapi import Request

# Configure root logger
def setup_logging() -> None:
    """Configure structured JSON-like logging for the application."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers = [handler]

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)


class RequestLogFormatter:
    """Format request/response logs with structured fields."""

    @staticmethod
    def format_request(request: Request) -> Dict[str, Any]:
        return {
            "method": request.method,
            "path": request.url.path,
            "query": str(request.query_params),
            "client": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }
