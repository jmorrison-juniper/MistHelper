"""Per-org API rate-limit middleware backed by Redis (T022).

Re-uses the same sliding-window pattern as ``src/shared/mist/rate_limit.py``
but applies to inbound API requests on a per-org basis.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from redis.exceptions import RedisError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

if TYPE_CHECKING:
    from starlette.requests import Request

logger = logging.getLogger(__name__)

DEFAULT_REQUEST_LIMIT = 1_000
DEFAULT_WINDOW_SECONDS = 60


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enforce per-org request rate limits on the API layer."""

    def __init__(self, app: Any, redis_url: str = "") -> None:
        super().__init__(app)
        self._redis_url = redis_url
        self._redis = None

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Check rate limit before forwarding the request."""
        org_id = self._extract_org_id(request)
        if org_id and await self._is_over_limit(org_id):
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
            )
        return await call_next(request)

    @staticmethod
    def _extract_org_id(request: Request) -> str | None:
        """Pull org_id from path params or query string."""
        org_id = request.path_params.get("org_id")
        if org_id:
            return str(org_id)
        return request.query_params.get("org_id")

    async def _is_over_limit(self, org_id: str) -> bool:
        """Return True when the org has exceeded its request budget."""
        redis = await self._get_redis()
        if not redis:
            return False  # fail-open when Redis unavailable

        key = f"api_ratelimit:{org_id}"
        try:
            current = await redis.incr(key)  # Increment the active window counter.
            if current == 1:
                await redis.expire(key, DEFAULT_WINDOW_SECONDS)  # Set the first-window expiry.
            return current > DEFAULT_REQUEST_LIMIT  # Reject only requests over the budget.
        except RedisError as error:
            self._redis = None  # Force a reconnect attempt after a runtime Redis outage.
            logger.warning(
                "Rate limit Redis command failed: %s. Rate limiting is disabled.",
                error,
            )
            return False  # Preserve the documented fail-open behavior during an outage.

    async def _get_redis(self):
        """Lazy-initialize async Redis connection."""
        if self._redis is not None:
            return self._redis
        if not self._redis_url:
            return None
        try:
            from redis.asyncio import from_url

            from src.shared.redis_timeouts import redis_timeout_kwargs

            logger.info("Rate limit Redis connect starts.")  # Announce the connect attempt.
            # WHY: a client with no socket limit holds this request forever on a silent host.
            self._redis = await from_url(self._redis_url, **redis_timeout_kwargs())
            logger.debug("Rate limit Redis connect done.")  # Confirm the client exists.
            return self._redis
        except Exception:
            logger.warning("Redis unavailable — rate limiting disabled")
            return None
