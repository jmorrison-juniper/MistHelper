"""Offline regressions for the expiry clock in fakeredis (issue #3682).

The limiter tests supply the fixtures. These tests check clock isolation.
They execute Lua to test expiry. They need no API request or Redis service.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from .test_rate_limit_middleware import (
    DEFAULT_REQUEST_LIMIT,
    DEFAULT_WINDOW_SECONDS,
    ORG_IN_SCOPE,
    RATE_LIMIT_KEY,
)
from .test_rate_limit_middleware import limiter as limiter
from .test_rate_limit_middleware import redis_client as redis_client
from .test_rate_limit_middleware import redis_clock as redis_clock
from .test_rate_limit_middleware import redis_server as redis_server

if TYPE_CHECKING:
    from unittest.mock import MagicMock

    from fakeredis.aioredis import FakeRedis

    from .test_rate_limit_middleware import OrgRateLimiter

REAL_WALL_CLOCK = time.time
REAL_MONOTONIC_CLOCK = time.monotonic
MISSING_KEY_TTL = -2


def test_fake_clock_keeps_python_clocks_real(redis_clock: MagicMock) -> None:
    """Only the fake command clock can advance by the Redis window."""
    started = REAL_WALL_CLOCK()

    redis_clock.return_value += DEFAULT_WINDOW_SECONDS

    assert time.time is REAL_WALL_CLOCK
    assert time.monotonic is REAL_MONOTONIC_CLOCK
    assert started <= time.time() <= REAL_WALL_CLOCK()
    assert REAL_MONOTONIC_CLOCK() <= time.monotonic() <= REAL_MONOTONIC_CLOCK()


async def test_fake_clock_expires_and_renews_only_the_redis_window(
    limiter: OrgRateLimiter, redis_client: FakeRedis, redis_clock: MagicMock
) -> None:
    """Real Lua must renew an expired budget without advancing Python time."""
    await redis_client.set(RATE_LIMIT_KEY, DEFAULT_REQUEST_LIMIT, ex=DEFAULT_WINDOW_SECONDS)
    assert await limiter.is_over_limit(ORG_IN_SCOPE) is True
    assert await redis_client.ttl(RATE_LIMIT_KEY) == DEFAULT_WINDOW_SECONDS

    redis_clock.return_value += DEFAULT_WINDOW_SECONDS + 1

    assert await redis_client.get(RATE_LIMIT_KEY) is None
    assert await redis_client.ttl(RATE_LIMIT_KEY) == MISSING_KEY_TTL
    assert await limiter.is_over_limit(ORG_IN_SCOPE) is False
    assert await redis_client.get(RATE_LIMIT_KEY) == "1"
    assert await redis_client.ttl(RATE_LIMIT_KEY) == DEFAULT_WINDOW_SECONDS
    assert time.time is REAL_WALL_CLOCK
    assert time.monotonic is REAL_MONOTONIC_CLOCK
