"""Tests that the token refresh route renews a real session and refuses an anonymous caller.

The route used to answer any caller with ``secrets.token_urlsafe(32)``. That
value looked like a session identifier, but the session store never issued it.
Three faults followed. An anonymous caller received a credential-shaped string.
A client that followed the refresh contract replaced a working identifier with
an unknown one. The real record never gained a longer lifetime.

The static guard in ``test_write_route_authentication.py`` did not catch this,
because the allowlist entry stated a cookie check that the code never made.
These tests hold the corrected behavior in place.
"""

from __future__ import annotations

import pathlib  # Locate the sub-project root, so "src" resolves during a direct run
import sys  # Extend the import path before the first "src" import

import pytest  # Test framework and skip helper

PLATFORM_ROOT = pathlib.Path(__file__).resolve().parents[3]  # Sub-project root directory

if str(PLATFORM_ROOT) not in sys.path:  # Only extend the path one time
    sys.path.insert(0, str(PLATFORM_ROOT))  # Make "src.shared" and "src.api" importable

from src.shared.services.session_store import (  # noqa: E402
    SESSION_TTL_SECONDS,
    SessionStore,
)

HTTP_UNAUTHORIZED = 401  # Status code that a refresh with no session must get
HTTP_OK = 200  # Status code that a refresh with a valid session must get


# -- The store refuses to mint a session -------------------------------


def test_renew_refuses_an_empty_identifier() -> None:
    """An empty cookie value addresses no record, so the renewal reports None."""
    store = SessionStore()  # A None client selects the process-local fallback map.
    assert store.renew("") is None  # An empty value must never gain a lifetime.


def test_renew_refuses_an_unknown_identifier() -> None:
    """An identifier that the store never issued must not gain a lifetime.

    This is the defect the route carried. A random string used to reach the
    caller as a session identifier. The store must refuse it.
    """
    store = SessionStore()  # Use the fallback map, so the test needs no Redis.
    unknown = "this-identifier-was-never-issued"  # A value that the store did not create.
    assert store.renew(unknown) is None  # The store must not create a record on a renewal.


def test_renew_extends_a_real_record_and_keeps_its_identifier() -> None:
    """A renewal returns the true lifetime and leaves the identifier unchanged."""
    store = SessionStore()  # Use the fallback map, so the test needs no Redis.
    session_id = store.create("mist-token-value")  # Create the record the login route would write.

    lifetime = store.renew(session_id)  # Renew the record that the cookie addresses.

    assert lifetime == SESSION_TTL_SECONDS  # The route reports the real lifetime, not 3600.
    record = store.resolve(session_id)  # Read the record back under the same identifier.
    assert record is not None  # The renewal must keep the record reachable.
    assert record.token == "mist-token-value"  # The renewal must not disturb the credential.


def test_renew_does_not_create_a_record_for_the_identifier_it_refused() -> None:
    """A refused renewal leaves no record behind, so a retry stays refused."""
    store = SessionStore()  # Use the fallback map, so the test needs no Redis.
    unknown = "a-second-identifier-the-store-never-issued"  # A value the store did not create.

    store.renew(unknown)  # Attempt the renewal that the store must refuse.

    assert store.resolve(unknown) is None  # No record may exist after the refusal.


# -- The route refuses an anonymous caller ------------------------------


def _build_client() -> object:
    """Return a test client for the auth router, or skip when FastAPI is absent."""
    fastapi = pytest.importorskip("fastapi")  # Skip when the web framework is not installed.
    testclient = pytest.importorskip("fastapi.testclient")  # The client needs httpx as well.

    from src.api.routes.health import auth_router  # Import here, so a missing dependency skips.

    app = fastapi.FastAPI()  # A bare application isolates the route from the real middleware.
    app.include_router(auth_router)  # Mount the router that holds POST /auth/token.
    app.state.session_store = SessionStore()  # Give the route the fallback store to read.
    return testclient.TestClient(app)  # The client drives a real request through the route.


def test_an_anonymous_refresh_is_refused() -> None:
    """A refresh with no session cookie must answer 401, never 200 with a value."""
    client = _build_client()  # Build the client, or skip when a dependency is missing.

    response = client.post("/auth/token")  # Send the refresh with no cookie at all.

    assert response.status_code == HTTP_UNAUTHORIZED  # An anonymous caller gains no session.
    assert "session_id" not in response.text  # The body must carry no credential-shaped value.


def test_a_refresh_with_an_unknown_cookie_is_refused() -> None:
    """A cookie that names no record must answer 401, so a guess gains nothing."""
    client = _build_client()  # Build the client, or skip when a dependency is missing.
    client.cookies.set("mist_session", "an-identifier-the-store-never-issued")  # Guess a value.

    response = client.post("/auth/token")  # Send the refresh with the guessed cookie.

    assert response.status_code == HTTP_UNAUTHORIZED  # A guessed identifier must not refresh.


def test_a_refresh_with_a_valid_cookie_returns_the_stored_identifier() -> None:
    """A valid session receives its own identifier back, and the true lifetime."""
    client = _build_client()  # Build the client, or skip when a dependency is missing.
    store = client.app.state.session_store  # Reuse the store the route reads.
    session_id = store.create("mist-token-value")  # Create the record the login route would write.
    client.cookies.set("mist_session", session_id)  # Present the cookie that the browser holds.

    response = client.post("/auth/token")  # Send the refresh with the valid cookie.

    assert response.status_code == HTTP_OK  # A valid session refreshes without an error.
    body = response.json()["data"]  # The route wraps the payload in a response envelope.
    assert body["session_id"] == session_id  # The route returns the identifier the store knows.
    assert body["expires_in"] == SESSION_TTL_SECONDS  # The route reports the real lifetime.
