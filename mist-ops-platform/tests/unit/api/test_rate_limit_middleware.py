"""Regression tests for the per-org API rate limiter (issues #2049 and #2050).

The old middleware counted a request before authentication ran. A caller
without a token could burn the budget of any organization. The limiter now
runs as a dependency after the membership check. These tests hold that order
in place and keep the fail-open behavior on a Redis outage. Real Lua tests
cover atomic expiry without a live Redis service.
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fakeredis import FakeServer
from fakeredis.aioredis import FakeRedis
from fastapi import HTTPException
from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import ResponseError
from redis.exceptions import TimeoutError as RedisTimeoutError

from src.api.middleware import rate_limit
from src.api.middleware.rate_limit import (
    DEFAULT_REQUEST_LIMIT,
    DEFAULT_WINDOW_SECONDS,
    OrgRateLimiter,
)
from src.shared.redis_timeouts import redis_timeout_kwargs

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator

ORG_IN_SCOPE = "11111111-1111-1111-1111-111111111111"  # Organization the caller owns
ORG_OUT_OF_SCOPE = "22222222-2222-2222-2222-222222222222"  # Organization the caller must not read
HTTP_OK = 200  # Names the success status, because a bare number is a magic value
HTTP_UNAUTHORIZED = 401  # Names the status that a missing credential returns
HTTP_FORBIDDEN = 403  # Names the status that a scope refusal returns
HTTP_TOO_MANY_REQUESTS = 429  # Names the status that the rate limiter returns
RATE_LIMIT_KEY = f"api_ratelimit:{ORG_IN_SCOPE}"
EXPECTED_SCRIPT_CALLS = 2


@pytest.fixture
def redis_clock() -> Iterator[MagicMock]:
    """Control only the fake server clock, not the application clock."""
    with patch("fakeredis._basefakesocket.time", wraps=time) as clock:
        clock.time.return_value = 1_800_000_000.0
        yield clock.time


@pytest.fixture
def redis_server(redis_clock: MagicMock) -> FakeServer:
    """Build an isolated server under the controlled clock."""
    return FakeServer()


@pytest.fixture
async def redis_client(redis_server: FakeServer) -> AsyncIterator[FakeRedis]:
    """Execute Redis commands and Lua without a network connection."""
    client = FakeRedis(server=redis_server, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose(close_connection_pool=True)
        assert not client.connection_pool._in_use_connections
        available = client.connection_pool._available_connections  # Inspect idle connections.
        assert not any(connection.is_connected for connection in available)


@pytest.fixture
def limiter(redis_client: FakeRedis) -> OrgRateLimiter:
    """Use the in-process Redis client for every limiter request."""
    instance = OrgRateLimiter(redis_url="redis://localhost")
    instance._redis = redis_client
    return instance


@pytest.fixture
def mock_redis() -> MagicMock:
    """Provide a synchronous registration method and an async script."""
    client = MagicMock(spec=Redis)
    client.register_script.return_value = AsyncMock(return_value=1)
    return client


@pytest.fixture
def mock_limiter(mock_redis: MagicMock) -> OrgRateLimiter:
    """Use a controlled client for command failure tests."""
    instance = OrgRateLimiter(redis_url="redis://localhost")
    instance._redis = mock_redis
    return instance


@pytest.fixture
def pending_redis_failure() -> tuple[AsyncMock, asyncio.Event, asyncio.Event]:
    """Hold one Redis error until the test permits its completion."""
    started, release = asyncio.Event(), asyncio.Event()

    async def delayed_failure(**_kwargs: object) -> int:
        started.set()
        await release.wait()
        raise RedisConnectionError("late failure")

    return AsyncMock(side_effect=delayed_failure), started, release


class _RecordingLimiter:
    """Stand-in limiter that records which organizations it counted."""

    def __init__(self, over_limit: bool = False) -> None:
        self.checked_orgs: list[str] = []  # Every org the dependency counted
        self._over_limit = over_limit  # When True, the check raises 429

    async def check(self, org_id: object) -> None:
        self.checked_orgs.append(str(org_id))  # Record the count, so a test can read it
        if self._over_limit:
            raise HTTPException(  # Mirror the real limiter's refusal
                status_code=HTTP_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Try again later.",
            )


def _build_probe_app(
    org_ids: list[str],
    limiter: _RecordingLimiter,
    authenticated: bool = True,
):
    """Return a small app whose single route uses the scope dependency."""
    fastapi = pytest.importorskip("fastapi")  # Skip when the web framework is absent
    pytest.importorskip("httpx2")  # The test client needs the httpx2 package
    pytest.importorskip("sqlalchemy")  # deps.py imports sqlalchemy at module load

    from src.api.deps import get_authenticated_user, get_scoped_org_id
    from src.api.middleware.auth import CurrentUser

    app = fastapi.FastAPI()  # Minimal app, so the test needs no database
    org_dependency = fastapi.Depends(get_scoped_org_id)  # Reuse the dependency in the probe.

    @app.get("/probe")  # One route is enough to exercise the dependency
    async def probe(org_id: Any = org_dependency) -> dict:  # Count only a verified organization.
        """Return the organization the dependency approved."""
        return {"org_id": str(org_id)}  # Echo the value, so a pass is visible

    if authenticated:  # Only a verified caller skips the live Mist lookup

        async def fake_user() -> CurrentUser:
            """Return a caller whose scope the test controls."""
            return CurrentUser(
                token="test-token",
                email="tester@example.com",
                org_ids=org_ids,
                is_msp=False,
                msp_org_ids=[],  # The caller owns no extra organization
            )

        app.dependency_overrides[get_authenticated_user] = fake_user  # Skip the live Mist lookup
    return app


def _get(app, org_id: str):
    """Send one probe request and return the response."""
    from fastapi.testclient import TestClient  # Imported late, so the skip above applies

    with TestClient(app) as client:  # Context manager runs the app lifespan
        return client.get("/probe", params={"org_id": org_id})


# -- Limiter unit behavior ----------------------------------------------


@pytest.mark.parametrize("error_type", [RedisConnectionError, RedisTimeoutError, ResponseError])
async def test_runtime_redis_failure_fails_open_and_clears_client(
    mock_limiter: OrgRateLimiter,
    mock_redis: MagicMock,
    error_type: type[Exception],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A command outage must not turn an API request into an HTTP 500."""
    mock_redis.register_script.return_value.side_effect = error_type("command failed")

    assert await mock_limiter.is_over_limit(ORG_IN_SCOPE) is False
    assert mock_limiter._redis is None
    assert mock_limiter._atomic_incr is None
    assert "Rate limit Redis command failed" in caplog.text


async def test_registration_failure_fails_open_and_clears_client(
    mock_limiter: OrgRateLimiter, mock_redis: MagicMock
) -> None:
    """Script registration must use the same Redis recovery path."""
    mock_redis.register_script.side_effect = RedisConnectionError("registration failed")

    assert await mock_limiter.is_over_limit(ORG_IN_SCOPE) is False
    assert mock_limiter._redis is None
    assert mock_limiter._atomic_incr is None


async def test_reuses_script(mock_limiter: OrgRateLimiter, mock_redis: MagicMock) -> None:
    """Requests must reuse one script bound to the current client."""
    for _ in range(EXPECTED_SCRIPT_CALLS):
        assert await mock_limiter.is_over_limit(ORG_IN_SCOPE) is False

    mock_redis.register_script.assert_called_once_with(rate_limit.ATOMIC_INCR_SCRIPT)
    script = mock_redis.register_script.return_value
    assert script.await_count == EXPECTED_SCRIPT_CALLS
    expected_args = [DEFAULT_WINDOW_SECONDS]  # Match the fixed window script input.
    script.assert_awaited_with(keys=[RATE_LIMIT_KEY], args=expected_args, client=mock_redis)
    mock_redis.incr.assert_not_called()
    mock_redis.expire.assert_not_called()


async def test_disabled_limiter_does_not_create_a_client() -> None:
    """An empty Redis URL keeps the configured rate limiter disabled."""
    with patch("redis.asyncio.Redis.from_url") as factory:
        assert await OrgRateLimiter().is_over_limit(ORG_IN_SCOPE) is False
    factory.assert_not_called()


async def test_client_creation_failure_fails_open(caplog: pytest.LogCaptureFixture) -> None:
    """A Redis connection error must produce a warning and permit the request."""
    instance = OrgRateLimiter(redis_url="redis://localhost")
    with patch("redis.asyncio.Redis.from_url", side_effect=RedisConnectionError("unavailable")):
        assert await instance.is_over_limit(ORG_IN_SCOPE) is False
    assert instance._redis is None
    assert "The API permits this request" in caplog.text


async def test_configuration_errors_do_not_silently_disable_rate_limiting() -> None:
    """An invalid URL is a configuration defect, not a Redis outage."""
    with pytest.raises(ValueError, match="Redis URL"):
        await OrgRateLimiter(redis_url="https://invalid").is_over_limit(ORG_IN_SCOPE)


async def test_programming_errors_do_not_silently_disable_rate_limiting(
    mock_limiter: OrgRateLimiter, mock_redis: MagicMock
) -> None:
    """Only Redis errors can use the documented fail-open behavior."""
    mock_redis.register_script.return_value.side_effect = TypeError("invalid script result")
    with pytest.raises(TypeError, match="invalid script result"):
        await mock_limiter.is_over_limit(ORG_IN_SCOPE)
    assert mock_limiter._redis is mock_redis


# -- Real Redis Lua behavior --------------------------------------------


async def test_real_lua_sets_expiry(limiter: OrgRateLimiter, redis_client: FakeRedis) -> None:
    """The first count and its expiry must not use separate client commands."""
    with (
        patch.object(redis_client, "incr", side_effect=AssertionError("INCR must run in Lua")),
        patch.object(redis_client, "expire", side_effect=AssertionError("EXPIRE must run in Lua")),
    ):
        assert await limiter.is_over_limit(ORG_IN_SCOPE) is False

    assert await redis_client.get(RATE_LIMIT_KEY) == "1"
    assert await redis_client.ttl(RATE_LIMIT_KEY) == DEFAULT_WINDOW_SECONDS


@pytest.mark.parametrize("existing_count", [1, DEFAULT_REQUEST_LIMIT + 1])
async def test_repairs_a_bucket_without_expiry(
    limiter: OrgRateLimiter, redis_client: FakeRedis, existing_count: int
) -> None:
    """A counter left by the old crash window must not stay permanent."""
    await redis_client.set(RATE_LIMIT_KEY, existing_count)
    assert await redis_client.ttl(RATE_LIMIT_KEY) == -1

    assert await limiter.is_over_limit(ORG_IN_SCOPE) is (existing_count >= DEFAULT_REQUEST_LIMIT)
    assert await redis_client.get(RATE_LIMIT_KEY) == str(existing_count + 1)
    assert await redis_client.ttl(RATE_LIMIT_KEY) == DEFAULT_WINDOW_SECONDS


@pytest.mark.parametrize("existing_count", [0, DEFAULT_REQUEST_LIMIT])
async def test_later_requests_preserve_the_existing_expiry(
    limiter: OrgRateLimiter, redis_client: FakeRedis, existing_count: int
) -> None:
    """A valid window must keep its original expiry, including a zero counter."""
    remaining_seconds = DEFAULT_WINDOW_SECONDS // 2
    await redis_client.set(RATE_LIMIT_KEY, existing_count, ex=remaining_seconds)

    assert await limiter.is_over_limit(ORG_IN_SCOPE) is (existing_count >= DEFAULT_REQUEST_LIMIT)
    assert await redis_client.ttl(RATE_LIMIT_KEY) == remaining_seconds


async def test_request_at_budget_is_allowed_and_next_request_is_rejected(
    limiter: OrgRateLimiter, redis_client: FakeRedis
) -> None:
    """The exact budget is valid. The next request must receive HTTP 429."""
    await redis_client.set(RATE_LIMIT_KEY, DEFAULT_REQUEST_LIMIT - 1, ex=DEFAULT_WINDOW_SECONDS)
    await limiter.check(ORG_IN_SCOPE)

    with pytest.raises(HTTPException) as exc_info:
        await limiter.check(ORG_IN_SCOPE)

    assert exc_info.value.status_code == HTTP_TOO_MANY_REQUESTS
    assert await redis_client.get(RATE_LIMIT_KEY) == str(DEFAULT_REQUEST_LIMIT + 1)
    assert await redis_client.ttl(RATE_LIMIT_KEY) == DEFAULT_WINDOW_SECONDS


async def test_expired_window_starts_a_new_budget(
    limiter: OrgRateLimiter, redis_client: FakeRedis, redis_clock: MagicMock
) -> None:
    """An exhausted window must reset instead of extending with each rejection."""
    await redis_client.set(RATE_LIMIT_KEY, DEFAULT_REQUEST_LIMIT, ex=DEFAULT_WINDOW_SECONDS)
    redis_clock.return_value += DEFAULT_WINDOW_SECONDS - 0.001
    assert await limiter.is_over_limit(ORG_IN_SCOPE) is True
    assert await redis_client.pttl(RATE_LIMIT_KEY) <= 1

    redis_clock.return_value += 0.002  # Cross the expiry boundary without a real sleep.
    assert await limiter.is_over_limit(ORG_IN_SCOPE) is False
    assert await redis_client.get(RATE_LIMIT_KEY) == "1"
    assert await redis_client.ttl(RATE_LIMIT_KEY) == DEFAULT_WINDOW_SECONDS


async def test_org_budgets_independent(limiter: OrgRateLimiter, redis_client: FakeRedis) -> None:
    """An exhausted organization must not consume another organization's budget."""
    await redis_client.set(RATE_LIMIT_KEY, DEFAULT_REQUEST_LIMIT, ex=DEFAULT_WINDOW_SECONDS)

    assert await limiter.is_over_limit(ORG_IN_SCOPE) is True
    assert await limiter.is_over_limit(ORG_OUT_OF_SCOPE) is False
    assert await redis_client.get(f"api_ratelimit:{ORG_OUT_OF_SCOPE}") == "1"


async def test_concurrent_clients_share_one_atomic_budget(
    limiter: OrgRateLimiter, redis_client: FakeRedis, redis_server: FakeServer
) -> None:
    """Concurrent clients must count every request exactly once in one shared window."""
    excess_requests = 7
    total = DEFAULT_REQUEST_LIMIT + excess_requests  # Include requests past the budget.
    peer_client = FakeRedis(server=redis_server, decode_responses=True)
    try:
        peer = OrgRateLimiter(redis_url="redis://localhost")
        peer._redis = peer_client
        clients = (limiter, peer)
        results = await asyncio.gather(  # Run all checks against one server.
            *(clients[index % len(clients)].is_over_limit(ORG_IN_SCOPE) for index in range(total))
        )
    finally:
        await peer_client.aclose(close_connection_pool=True)

    assert sum(results) == excess_requests
    assert await redis_client.get(RATE_LIMIT_KEY) == str(total)
    assert await redis_client.ttl(RATE_LIMIT_KEY) == DEFAULT_WINDOW_SECONDS


async def test_script_cache_eviction_reloads_without_losing_counts(
    limiter: OrgRateLimiter, redis_client: FakeRedis
) -> None:
    """The registered handle must reload a script that the server no longer stores."""
    assert await limiter.is_over_limit(ORG_IN_SCOPE) is False
    script = limiter._atomic_incr
    await redis_client.script_flush()

    assert await limiter.is_over_limit(ORG_IN_SCOPE) is False
    assert limiter._atomic_incr is script
    assert await redis_client.get(RATE_LIMIT_KEY) == "2"
    assert await redis_client.ttl(RATE_LIMIT_KEY) == DEFAULT_WINDOW_SECONDS


async def test_lost_reply_keeps_expiry(limiter: OrgRateLimiter, redis_client: FakeRedis) -> None:
    """A lost reply must not leave the server counter without an expiry."""
    await redis_client.script_load(rate_limit.ATOMIC_INCR_SCRIPT)
    evalsha = redis_client.evalsha

    async def lost_reply(sha: str, number_of_keys: int, *arguments: str | int) -> None:
        await evalsha(sha, number_of_keys, *arguments)
        raise RedisConnectionError("reply lost after execution")

    with patch.object(redis_client, "evalsha", side_effect=lost_reply):
        assert await limiter.is_over_limit(ORG_IN_SCOPE) is False

    assert limiter._redis is None
    assert limiter._atomic_incr is None
    assert await redis_client.get(RATE_LIMIT_KEY) == "1"
    assert await redis_client.ttl(RATE_LIMIT_KEY) == DEFAULT_WINDOW_SECONDS


async def test_outage_recovers_with_a_new_script_handle(
    limiter: OrgRateLimiter, redis_client: FakeRedis, redis_server: FakeServer
) -> None:
    """A recovered client must register a new handle and retain the active budget."""
    assert await limiter.is_over_limit(ORG_IN_SCOPE) is False
    original_script = limiter._atomic_incr
    redis_server.connected = False
    assert await limiter.is_over_limit(ORG_IN_SCOPE) is False
    assert limiter._redis is None
    assert limiter._atomic_incr is None

    redis_server.connected = True
    with patch("redis.asyncio.Redis.from_url", return_value=redis_client) as factory:
        assert await limiter.is_over_limit(ORG_IN_SCOPE) is False
    factory.assert_called_once_with(
        "redis://localhost",
        single_connection_client=False,
        auto_close_connection_pool=None,
        **redis_timeout_kwargs(),
    )
    assert limiter._atomic_incr is not original_script
    assert await redis_client.get(RATE_LIMIT_KEY) == "2"


async def test_late_failure_keeps_the_replacement_client(
    mock_limiter: OrgRateLimiter,
    mock_redis: MagicMock,
    redis_client: FakeRedis,
    pending_redis_failure: tuple[AsyncMock, asyncio.Event, asyncio.Event],
) -> None:
    """An old request must not discard the handles that a newer request recovered."""
    script, started, release = pending_redis_failure
    mock_redis.register_script.return_value = script
    async with asyncio.TaskGroup() as tasks:
        pending = tasks.create_task(mock_limiter.is_over_limit(ORG_IN_SCOPE))
        await started.wait()
        script.side_effect = RedisConnectionError("first failure")
        assert await mock_limiter.is_over_limit(ORG_IN_SCOPE) is False
        with patch("redis.asyncio.Redis.from_url", return_value=redis_client):
            assert await mock_limiter.is_over_limit(ORG_IN_SCOPE) is False
        replacement_script = mock_limiter._atomic_incr
        release.set()

    assert pending.result() is False
    assert mock_limiter._redis is redis_client
    assert mock_limiter._atomic_incr is replacement_script


# -- Request-order regression (issue #2049) -------------------------------


def test_unauthenticated_caller_does_not_touch_the_org_counter() -> None:
    """A caller without a token gets 401 and counts toward no organization.

    The old middleware incremented the org counter before auth ran. This test
    fails the build if that order returns.
    """
    limiter = _RecordingLimiter()  # Record every org the dependency counts
    app = _build_probe_app([ORG_IN_SCOPE], limiter, authenticated=False)  # No token is sent
    with patch("src.api.deps.get_org_rate_limiter", return_value=limiter):  # Inject the recorder
        response = _get(app, ORG_IN_SCOPE)  # Send the request with no token

    assert response.status_code == HTTP_UNAUTHORIZED  # The auth dependency refuses the caller
    assert limiter.checked_orgs == []  # No organization lost budget to this call


def test_caller_outside_the_org_does_not_touch_the_counter() -> None:
    """A caller refused by the membership check counts toward no organization."""
    limiter = _RecordingLimiter()  # Record every org the dependency counts
    app = _build_probe_app([ORG_IN_SCOPE], limiter)  # The caller owns one organization
    with patch("src.api.deps.get_org_rate_limiter", return_value=limiter):  # Inject the recorder
        response = _get(app, ORG_OUT_OF_SCOPE)  # Request a different organization

    assert response.status_code == HTTP_FORBIDDEN  # The membership check refuses the caller
    assert limiter.checked_orgs == []  # The refused caller must not burn any budget


def test_verified_caller_counts_toward_the_org_budget() -> None:
    """A caller inside the organization counts toward that organization only."""
    limiter = _RecordingLimiter()  # Record every org the dependency counts
    app = _build_probe_app([ORG_IN_SCOPE], limiter)  # The caller owns one organization
    with patch("src.api.deps.get_org_rate_limiter", return_value=limiter):  # Inject the recorder
        response = _get(app, ORG_IN_SCOPE)  # Request the owned organization

    assert response.status_code == HTTP_OK  # The membership check passes
    assert limiter.checked_orgs == [ORG_IN_SCOPE]  # The verified org is the one counted


def test_over_budget_verified_caller_gets_429() -> None:
    """A verified caller past the budget gets 429, not the data."""
    limiter = _RecordingLimiter(over_limit=True)  # The check refuses the request
    app = _build_probe_app([ORG_IN_SCOPE], limiter)  # The caller owns one organization
    with patch("src.api.deps.get_org_rate_limiter", return_value=limiter):  # Inject the recorder
        response = _get(app, ORG_IN_SCOPE)  # Request the owned organization

    assert response.status_code == HTTP_TOO_MANY_REQUESTS  # The limiter refuses the caller
    assert limiter.checked_orgs == [ORG_IN_SCOPE]  # The refusal came from the count
