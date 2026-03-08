"""Structured logging middleware for request/response tracing (T021).

Logs every request with method, path, status, and duration using
structured key-value pairs (ASCII-only per Principle V).
"""

from __future__ import annotations

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("mist_ops.access")


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Log request metadata on every response."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Wrap the request lifecycle with timing + structured log."""
        start = time.monotonic()
        response = await call_next(request)
        elapsed_ms = (time.monotonic() - start) * 1_000

        logger.info(
            "method=%s path=%s status=%d duration_ms=%.1f",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response
