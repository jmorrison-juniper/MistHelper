"""Per-org API rate limiting backed by Redis (T022).

The first verified request starts a fixed window. A Lua operation increments
the counter and sets an expiry when the key has none (issue #2050).

Issue #2049: the old ``BaseHTTPMiddleware`` read ``org_id`` from the raw
request and incremented the counter before authentication ran. Any caller
without a token could exhaust the budget of any organization. The check now
runs as a dependency after the membership check, so it reads the verified
organization only.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from fastapi import HTTPException
from redis.exceptions import RedisError

if TYPE_CHECKING:
    from redis.asyncio import Redis
    from redis.commands.core import AsyncScript

logger = logging.getLogger(__name__)

DEFAULT_REQUEST_LIMIT = 1_000
DEFAULT_WINDOW_SECONDS = 60

# Repair old counters without an expiry, but keep the deadline of a valid window.
ATOMIC_INCR_SCRIPT = """
local count = redis.call('INCR', KEYS[1])
if redis.call('TTL', KEYS[1]) == -1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return count
"""


class OrgRateLimiter:
    """Enforce the per-org request budget on the API layer."""

    def __init__(self, redis_url: str = "") -> None:
        self._redis_url = redis_url  # Empty value turns rate limiting off
        self._redis: Redis | None = None  # Lazy client, so import cost stays out of startup
        self._atomic_incr: AsyncScript | None = None

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
        if redis is None:
            return False  # fail-open when Redis unavailable

        try:
            current = await self._count_request(redis, org_id)
            return current > DEFAULT_REQUEST_LIMIT  # Reject only requests over the budget.
        except RedisError as error:
            # A late failure from an old client must not discard a replacement.
            if self._redis is redis:
                self._redis = None
                self._atomic_incr = None
            logger.warning(
                "Rate limit Redis command failed: %s. The API permits this request.",
                error,
            )
            return False  # Preserve the documented fail-open behavior during an outage.

    async def _count_request(self, redis: Redis, org_id: Any) -> int:
        """Increment the counter and ensure its expiry in one Redis operation."""
        key = f"api_ratelimit:{org_id}"
        logger.info("Checking the API rate limit for %s.", org_id)
        if self._atomic_incr is None:
            self._atomic_incr = redis.register_script(ATOMIC_INCR_SCRIPT)
        script_args = [DEFAULT_WINDOW_SECONDS]  # Give the script the fixed window length.
        result = await self._atomic_incr(keys=[key], args=script_args, client=redis)
        current = int(result)  # Convert the Redis response before the limit comparison.
        logger.debug("The API rate limit count for %s is %d.", org_id, current)
        return current

    async def _get_redis(self) -> Redis | None:
        """Create the async Redis client only when a request needs it."""
        if self._redis is not None:
            return self._redis
        if not self._redis_url:
            return None
        try:
            from redis.asyncio import Redis

            from src.shared.redis_timeouts import redis_timeout_kwargs

            logger.info("Rate limit Redis connect starts.")  # Announce the connect attempt.
            # WHY: a client with no socket limit holds this request forever on a silent host.
            self._redis = Redis.from_url(
                self._redis_url,
                single_connection_client=False,
                auto_close_connection_pool=None,
                **redis_timeout_kwargs(),
            )
            logger.debug("Rate limit Redis connect done.")  # Confirm the client exists.
            return self._redis
        except RedisError as error:
            logger.warning("Redis connection failed: %s. The API permits this request.", error)
            return None


_limiter: OrgRateLimiter | None = None  # One shared limiter serves every request


def get_org_rate_limiter() -> OrgRateLimiter:
    """Return the shared limiter, built once from the configured Redis URL."""
    global _limiter  # A module holds one instance, so the routes share its client
    if _limiter is None:
        from src.shared.config.settings import get_settings

        _limiter = OrgRateLimiter(redis_url=get_settings().redis_url)  # Read the URL once
    return _limiter  # Hand the same instance to every dependency
