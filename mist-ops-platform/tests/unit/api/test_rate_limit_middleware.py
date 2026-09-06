"""Regression tests for the per-org API rate-limit middleware (T022).

Covers the atomic INCR+EXPIRE fix for issue #2050: a crash between the
counter increment and the TTL set must not be possible, and a Redis outage
must still fail open.
"""

from unittest.mock import AsyncMock, MagicMock

from redis.exceptions import ConnectionError as RedisConnectionError

from src.api.middleware.rate_limit import (
    ATOMIC_INCR_SCRIPT,
    DEFAULT_WINDOW_SECONDS,
    RateLimitMiddleware,
)

EXPECTED_SCRIPT_CALLS = 2  # Two requests share one registered script handle.


def _middleware_with_mock_redis() -> tuple[RateLimitMiddleware, AsyncMock]:
    """Build a middleware whose Redis client is a mock."""
    middleware = RateLimitMiddleware(app=None, redis_url="redis://localhost")
    fake_redis = AsyncMock()
    middleware._redis = fake_redis
    return middleware, fake_redis


def test_atomic_script_uses_single_incr_and_expire() -> None:
    """The counter and the TTL must be set in one atomic Redis call."""
    assert "INCR" in ATOMIC_INCR_SCRIPT
    assert "EXPIRE" in ATOMIC_INCR_SCRIPT
    assert "if count == 1" in ATOMIC_INCR_SCRIPT


async def test_counter_and_ttl_are_set_atomically() -> None:
    """A single script call sets the counter and the TTL together."""
    middleware, fake_redis = _middleware_with_mock_redis()
    fake_script = AsyncMock(return_value=1)
    fake_redis.register_script = MagicMock(return_value=fake_script)

    over = await middleware._is_over_limit("org-1")

    assert over is False
    fake_redis.register_script.assert_called_once_with(ATOMIC_INCR_SCRIPT)
    fake_script.assert_awaited_once_with(
        keys=["api_ratelimit:org-1"],
        args=[DEFAULT_WINDOW_SECONDS],
    )
    fake_redis.incr.assert_not_awaited()
    fake_redis.expire.assert_not_awaited()


async def test_script_is_registered_once() -> None:
    """The script is registered once and reused across requests."""
    middleware, fake_redis = _middleware_with_mock_redis()
    fake_script = AsyncMock(return_value=1)
    fake_redis.register_script = MagicMock(return_value=fake_script)

    await middleware._is_over_limit("org-1")
    await middleware._is_over_limit("org-1")

    assert fake_redis.register_script.call_count == 1
    assert fake_script.await_count == EXPECTED_SCRIPT_CALLS


async def test_runtime_redis_failure_fails_open_and_clears_client() -> None:
    """A Redis outage must not block the API and must force a reconnect."""
    middleware, fake_redis = _middleware_with_mock_redis()
    fake_script = AsyncMock(side_effect=RedisConnectionError("connection lost"))
    fake_redis.register_script = MagicMock(return_value=fake_script)

    over = await middleware._is_over_limit("org-1")

    assert over is False
    assert middleware._redis is None
    assert middleware._atomic_incr is None


async def test_script_failure_fails_open_and_clears_client() -> None:
    """A failed script call must fail open and clear both handles."""
    middleware, fake_redis = _middleware_with_mock_redis()
    fake_script = AsyncMock(side_effect=RedisConnectionError("script failed"))
    fake_redis.register_script = MagicMock(return_value=fake_script)

    over = await middleware._is_over_limit("org-1")

    assert over is False
    assert middleware._redis is None
    assert middleware._atomic_incr is None
