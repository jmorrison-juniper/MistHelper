"""Per-org API rate limiting backed by Redis (T022).

Re-uses the same sliding-window pattern as ``src/shared/mist/rate_limit.py``
but applies to inbound API requests on a per-org basis.

Issue #2049: the old ``BaseHTTPMiddleware`` read ``org_id`` from the raw
request and incremented the counter before authentication ran. Any caller
without a token could exhaust the budget of any organization. The check now
runs as a dependency after the membership check, so it reads the verified
organization only.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import HTTPException
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)

DEFAULT_REQUEST_LIMIT = 1_000
DEFAULT_WINDOW_SECONDS = 60


class OrgRateLimiter:
    """Enforce the per-org request budget on the API layer."""

    def __init__(self, redis_url: str = "") -> None:
        self._redis_url = redis_url  # Empty value turns rate limiting off
        self._redis = None  # Lazy client, so import cost stays out of startup

    async def check(self, org_id: Any) -> None:
        """Raise 429 when the verified organization exceeds its budget."""
        if await self.is_over_limit(org_id):  # Count only a caller that passed auth
            raise HTTPException(  # 429 names the cause for the caller
                status_code=429,
                detail="Rate limit exceeded. Try again later.",
            )

    async def is_over_limit(self, org_id: Any) -> bool:
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

    async def _get_redis(self) -> Any:
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


_limiter: OrgRateLimiter | None = None  # One shared limiter serves every request


def get_org_rate_limiter() -> OrgRateLimiter:
    """Return the shared limiter, built once from the configured Redis URL."""
    global _limiter  # A module holds one instance, so the routes share its client
    if _limiter is None:
        from src.shared.config.settings import get_settings

        _limiter = OrgRateLimiter(redis_url=get_settings().redis_url)  # Read the URL once
    return _limiter  # Hand the same instance to every dependency
