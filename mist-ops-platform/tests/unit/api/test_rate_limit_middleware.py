"""Regression tests for the per-org API rate limiter (issue #2049).

The old middleware counted a request before authentication ran. A caller
without a token could burn the budget of any organization. The limiter now
runs as a dependency after the membership check. These tests hold that order
in place and keep the fail-open behavior on a Redis outage.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from redis.exceptions import ConnectionError as RedisConnectionError

from src.api.middleware.rate_limit import (
    DEFAULT_REQUEST_LIMIT,
    DEFAULT_WINDOW_SECONDS,
    OrgRateLimiter,
)

ORG_IN_SCOPE = "11111111-1111-1111-1111-111111111111"  # Organization the caller owns
ORG_OUT_OF_SCOPE = "22222222-2222-2222-2222-222222222222"  # Organization the caller must not read
HTTP_OK = 200  # Names the success status, because a bare number is a magic value
HTTP_UNAUTHORIZED = 401  # Names the status that a missing credential returns
HTTP_FORBIDDEN = 403  # Names the status that a scope refusal returns
HTTP_TOO_MANY_REQUESTS = 429  # Names the status that the rate limiter returns


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
    from uuid import UUID  # Match the type the real routes declare

    from src.api.deps import get_authenticated_user, get_scoped_org_id
    from src.api.middleware.auth import CurrentUser

    app = fastapi.FastAPI()  # Minimal app, so the test needs no database

    @app.get("/probe")  # One route is enough to exercise the dependency
    async def probe(org_id: UUID = fastapi.Depends(get_scoped_org_id)) -> dict:
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


async def test_runtime_redis_failure_fails_open_and_clears_client() -> None:
    """A command outage must not turn an API request into an HTTP 500."""
    limiter = OrgRateLimiter(redis_url="redis://localhost")  # Build the limiter under test
    redis = AsyncMock()  # Fake client, so no real Redis is needed
    redis.incr.side_effect = RedisConnectionError("connection lost")  # Simulate the outage
    limiter._redis = redis  # Inject the failing client

    over_limit = await limiter.is_over_limit("org-1")  # Run the check through the outage

    assert over_limit is False  # The fail-open rule lets the request through
    assert limiter._redis is None  # The dead client is dropped for a clean retry


async def test_expiry_failure_fails_open_and_clears_client() -> None:
    """An expiry command outage must use the same safe recovery path."""
    limiter = OrgRateLimiter(redis_url="redis://localhost")  # Build the limiter under test
    redis = AsyncMock()  # Fake client, so no real Redis is needed
    redis.incr.return_value = 1  # The first request in the window
    redis.expire.side_effect = RedisConnectionError("connection lost")  # Fail the expiry
    limiter._redis = redis  # Inject the failing client

    over_limit = await limiter.is_over_limit("org-1")  # Run the check through the outage

    assert over_limit is False  # The fail-open rule lets the request through
    assert limiter._redis is None  # The dead client is dropped for a clean retry


async def test_first_request_sets_the_window_expiry() -> None:
    """The first count of a window must arm the expiry timer."""
    limiter = OrgRateLimiter(redis_url="redis://localhost")  # Build the limiter under test
    redis = AsyncMock()  # Fake client, so the test reads the calls
    redis.incr.return_value = 1  # The first request in the window
    limiter._redis = redis  # Inject the fake client

    over_limit = await limiter.is_over_limit("org-1")  # Run the check

    assert over_limit is False  # One request is far under the budget
    redis.incr.assert_awaited_once_with("api_ratelimit:org-1")  # The key names the org
    redis.expire.assert_awaited_once_with("api_ratelimit:org-1", DEFAULT_WINDOW_SECONDS)


async def test_request_over_budget_is_rejected() -> None:
    """A count past the budget must raise 429 through the check method."""
    limiter = OrgRateLimiter(redis_url="redis://localhost")  # Build the limiter under test
    redis = AsyncMock()  # Fake client, so the test reads the calls
    redis.incr.return_value = DEFAULT_REQUEST_LIMIT + 1  # One request past the budget
    limiter._redis = redis  # Inject the fake client

    with pytest.raises(HTTPException) as exc_info:  # The check must refuse the request
        await limiter.check("org-1")

    assert exc_info.value.status_code == HTTP_TOO_MANY_REQUESTS  # The status names the cause
    redis.expire.assert_not_awaited()  # A later request must not re-arm the window


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
