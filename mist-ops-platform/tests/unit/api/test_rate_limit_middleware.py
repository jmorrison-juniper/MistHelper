"""Regression tests for runtime Redis failures in API rate limiting."""

from unittest.mock import AsyncMock

from redis.exceptions import ConnectionError as RedisConnectionError

from src.api.middleware.rate_limit import RateLimitMiddleware


async def test_runtime_redis_failure_fails_open_and_clears_client() -> None:
    """A command outage must not turn an API request into an HTTP 500."""
    middleware = RateLimitMiddleware(app=None, redis_url="redis://localhost")
    redis = AsyncMock()
    redis.incr.side_effect = RedisConnectionError("connection lost")
    middleware._redis = redis

    over_limit = await middleware._is_over_limit("org-1")

    assert over_limit is False
    assert middleware._redis is None


async def test_expiry_failure_fails_open_and_clears_client() -> None:
    """An expiry command outage must use the same safe recovery path."""
    middleware = RateLimitMiddleware(app=None, redis_url="redis://localhost")
    redis = AsyncMock()
    redis.incr.return_value = 1
    redis.expire.side_effect = RedisConnectionError("connection lost")
    middleware._redis = redis

    over_limit = await middleware._is_over_limit("org-1")

    assert over_limit is False
    assert middleware._redis is None
