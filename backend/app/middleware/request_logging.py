"""
Request logging and correlation ID middleware.
"""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

logger = get_logger("request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs every request with timing, status code, and correlation ID."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
        request.state.request_id = request_id

        start_time = time.time()

        logger.info(
            "REQ  %s %s %s | id=%s",
            request.method,
            request.url.path,
            str(request.query_params) if request.query_params else "",
            request_id,
        )

        response = await call_next(request)

        duration_ms = (time.time() - start_time) * 1000

        logger.info(
            "RESP %s %s | %d | %.2fms | id=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            request_id,
        )

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"
        return response
