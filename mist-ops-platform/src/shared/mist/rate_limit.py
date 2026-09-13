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
# WHY: bound the wait so a caller never blocks forever. Issue #1886.
DEFAULT_MAX_WAIT_SECONDS = 60.0


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

    async def wait_and_acquire(
        self,
        max_wait_seconds: float = DEFAULT_MAX_WAIT_SECONDS,
    ) -> None:
        """Block until a request slot is free, within a bounded wait.

        Loops on ``acquire`` after each sleep so the caller only
        proceeds once it truly holds a slot, instead of assuming
        one sleep is enough. Fixes issue #1886.

        Raises:
            TimeoutError: The bound passed and no slot became free.
        """
        # WHY: log before the wait starts.
        logger.info("Waiting for a rate-limit slot on %s", self._key)
        waited = 0.0  # WHY: track the total requested wait against the bound.
        while True:
            delay = await self.acquire()  # WHY: re-check the budget on every pass, not just once.
            if delay <= 0:
                logger.debug(
                    "Rate-limit slot acquired for %s after %.1fs",
                    self._key,
                    waited,
                )  # WHY: confirm success with a result summary after the wait.
                return  # WHY: a slot is free, so the caller may proceed now.
            if waited + delay > max_wait_seconds:
                # WHY: name the bound that was hit for the caller.
                msg = f"Rate limit wait for {self._key} exceeded the {max_wait_seconds:.0f}s bound"
                raise TimeoutError(msg)  # WHY: give up instead of blocking forever.
            await asyncio.sleep(delay)  # WHY: wait the time Mist told us to wait, then re-check.
            waited += delay  # WHY: add this sleep to the running total against the bound.

    async def remaining(self) -> int:
        """Return how many requests remain in the current window."""
        current = await self._redis.get(self._key)
        used = int(current) if current else 0
        return max(self._limit - used, 0)

    async def reset(self) -> None:
        """Force-reset the rate-limit counter (admin only)."""
        await self._redis.delete(self._key)
