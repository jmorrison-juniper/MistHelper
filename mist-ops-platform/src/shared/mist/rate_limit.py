"""Per-org Redis sliding-window rate limiter for Mist API calls (R-06).

Each organization has its own rate-limit bucket in Redis, ensuring one
busy org cannot starve others.  The default budget is 5 000 requests
per 60-minute window.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from redis.asyncio import Redis

logger = logging.getLogger(__name__)

DEFAULT_LIMIT = 5_000
DEFAULT_WINDOW_SECONDS = 3_600


class OrgRateLimiter:
    """Distributed sliding-window rate limiter backed by Redis."""

    def __init__(
        self,
        redis: Redis,
        org_id: str,
        limit: int = DEFAULT_LIMIT,
        window: int = DEFAULT_WINDOW_SECONDS,
    ) -> None:
        self._redis = redis
        self._key = f"ratelimit:{org_id}"
        self._limit = limit
        self._window = window

    async def acquire(self) -> float:
        """Acquire a request slot; return seconds to wait (0 if immediate)."""
        current = await self._redis.incr(self._key)
        if current == 1:
            await self._redis.expire(self._key, self._window)

        if current <= self._limit:
            return 0.0

        ttl = await self._redis.ttl(self._key)
        delay = max(float(ttl), 1.0)
        logger.warning(
            "Rate limit reached for %s (%d/%d). Retry in %.0fs.",
            self._key,
            current,
            self._limit,
            delay,
        )
        return delay

    async def wait_and_acquire(self) -> None:
        """Block until a request slot is available."""
        delay = await self.acquire()
        if delay > 0:
            await asyncio.sleep(delay)

    async def remaining(self) -> int:
        """Return how many requests remain in the current window."""
        current = await self._redis.get(self._key)
        used = int(current) if current else 0
        return max(self._limit - used, 0)

    async def reset(self) -> None:
        """Force-reset the rate-limit counter (admin only)."""
        await self._redis.delete(self._key)
