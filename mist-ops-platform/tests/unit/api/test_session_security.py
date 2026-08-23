"""Tests for the opaque session cookie and the off-loop Mist verification.

These tests cover issue #1859 and issue #1858. Issue #1859 asks for an opaque
session cookie, a server-side token, a Secure attribute, and a logout that
deletes the record. Issue #1858 asks for a verification that does not block the
event loop, and for a cache that stops the repeat upstream call.
"""

from __future__ import annotations

import asyncio
import threading
import time
from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import Depends, FastAPI

from src.api.deps import get_db_session
from src.api.middleware.auth import CurrentUser, get_current_user
from src.api.routes.health import auth_router
from src.shared.config.settings import get_settings
from src.shared.services.auth import AuthService, MistApiUnavailableError, MistPrivileges
from src.shared.services.session_store import SessionStore

TEST_TOKEN = "raw-mist-token-value-that-must-never-reach-the-client"
HTTP_OK = 200  # Names the success status, because a bare number is a magic value.
HTTP_UNAUTHORIZED = 401  # Names the status that a missing or bad credential returns.
HTTP_SERVICE_UNAVAILABLE = 503  # Names the status that an unreachable Mist API returns.
MIN_SESSION_ID_LENGTH = 32  # A shorter identifier would be easier to guess.
MAX_CONCURRENT_SECONDS = 0.45  # Two 0.25 second lookups must overlap, not run one after the other.
TEST_PRIVILEGES = MistPrivileges(
    email="operator@example.com",
    name="Test Operator",
    is_msp=False,
    org_ids=[],
    site_ids=[],
)


def _fake_db_session() -> Any:
    """Return a stub database session that records no rows."""
    session = AsyncMock()
    session.flush = AsyncMock()
    return session


def _build_app(store: SessionStore) -> FastAPI:
    """Return an application that mounts the auth routes and one guarded route."""
    app = FastAPI()
    app.include_router(auth_router, prefix="/api/v1")
    app.state.engine = object()
    app.state.session_store = store

    @app.get("/api/v1/protected")
    async def protected(user: CurrentUser = Depends(get_current_user)) -> dict[str, str]:
        return {"email": user.email}

    async def _override_db() -> Any:
        yield _fake_db_session()

    app.dependency_overrides[get_db_session] = _override_db
    return app


def _client(app: FastAPI) -> httpx.AsyncClient:
    """Return an async client bound to *app*."""
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")


@pytest.fixture
def store() -> SessionStore:
    """Return a store that keeps its records in the process, not in Redis."""
    return SessionStore(redis_client=None)


@pytest.fixture
def app(store: SessionStore) -> FastAPI:
    """Return the test application."""
    return _build_app(store)


@pytest.fixture(autouse=True)
def _reset_settings_cache() -> Any:
    """Clear the cached settings so an environment change takes effect."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


class TestOpaqueSessionCookie:
    """Cover the cookie contract of issue #1859."""

    async def test_cookie_value_differs_from_the_posted_token(
        self,
        app: FastAPI,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(AuthService, "validate_token", lambda self, token: TEST_PRIVILEGES)
        async with _client(app) as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={"method": "token", "token": TEST_TOKEN},
            )
        assert response.status_code == HTTP_OK
        cookie = response.cookies["mist_session"]
        assert cookie != TEST_TOKEN
        assert TEST_TOKEN not in response.headers["set-cookie"]

    async def test_cookie_carries_the_secure_attribute_by_default(
        self,
        app: FastAPI,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv("SESSION_COOKIE_SECURE", raising=False)
        monkeypatch.setattr(AuthService, "validate_token", lambda self, token: TEST_PRIVILEGES)
        async with _client(app) as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={"method": "token", "token": TEST_TOKEN},
            )
        assert "Secure" in response.headers["set-cookie"]
        assert "HttpOnly" in response.headers["set-cookie"]

    async def test_a_documented_setting_disables_the_secure_attribute(
        self,
        app: FastAPI,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("SESSION_COOKIE_SECURE", "false")
        monkeypatch.setattr(AuthService, "validate_token", lambda self, token: TEST_PRIVILEGES)
        async with _client(app) as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={"method": "token", "token": TEST_TOKEN},
            )
        assert "Secure" not in response.headers["set-cookie"]

    async def test_the_server_keeps_the_token_under_the_session_identifier(
        self,
        app: FastAPI,
        store: SessionStore,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(AuthService, "validate_token", lambda self, token: TEST_PRIVILEGES)
        async with _client(app) as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={"method": "token", "token": TEST_TOKEN},
            )
        record = store.resolve(response.cookies["mist_session"])
        assert record is not None
        assert record.token == TEST_TOKEN


class TestSessionRevocation:
    """Cover the logout contract of issue #1859."""

    async def test_a_deleted_session_identifier_returns_401(
        self,
        app: FastAPI,
        store: SessionStore,
    ) -> None:
        session_id = store.create(TEST_TOKEN)
        store.delete(session_id)
        async with _client(app) as client:
            response = await client.get(
                "/api/v1/protected",
                cookies={"mist_session": session_id},
            )
        assert response.status_code == HTTP_UNAUTHORIZED

    async def test_an_unknown_session_identifier_returns_401(self, app: FastAPI) -> None:
        async with _client(app) as client:
            response = await client.get(
                "/api/v1/protected",
                cookies={"mist_session": "never-issued"},
            )
        assert response.status_code == HTTP_UNAUTHORIZED

    async def test_logout_deletes_the_server_side_record(
        self,
        app: FastAPI,
        store: SessionStore,
    ) -> None:
        session_id = store.create(TEST_TOKEN)
        async with _client(app) as client:
            response = await client.delete(
                "/api/v1/auth/session",
                cookies={"mist_session": session_id},
            )
        assert response.status_code == HTTP_OK
        assert store.resolve(session_id) is None


class TestVerificationCache:
    """Cover the cache contract of issue #1858."""

    async def test_a_second_request_makes_no_second_upstream_call(
        self,
        app: FastAPI,
        store: SessionStore,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        calls: list[str] = []

        def _counted(self: AuthService, token: str) -> MistPrivileges:
            calls.append(token)
            return TEST_PRIVILEGES

        monkeypatch.setattr(AuthService, "validate_token", _counted)
        session_id = store.create(TEST_TOKEN)
        async with _client(app) as client:
            first = await client.get("/api/v1/protected", cookies={"mist_session": session_id})
            second = await client.get("/api/v1/protected", cookies={"mist_session": session_id})
        assert first.status_code == HTTP_OK
        assert second.status_code == HTTP_OK
        assert len(calls) == 1

    async def test_the_login_result_primes_the_session_cache(
        self,
        app: FastAPI,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        calls: list[str] = []

        def _counted(self: AuthService, token: str) -> MistPrivileges:
            calls.append(token)
            return TEST_PRIVILEGES

        monkeypatch.setattr(AuthService, "validate_token", _counted)
        async with _client(app) as client:
            login = await client.post(
                "/api/v1/auth/login",
                json={"method": "token", "token": TEST_TOKEN},
            )
            await client.get(
                "/api/v1/protected",
                cookies={"mist_session": login.cookies["mist_session"]},
            )
        assert len(calls) == 1

    def test_the_cache_key_is_a_stable_digest(self) -> None:
        from src.shared.services.auth import privilege_cache_key

        first = privilege_cache_key(TEST_TOKEN)
        assert first == privilege_cache_key(TEST_TOKEN)
        assert TEST_TOKEN not in first
        assert first != privilege_cache_key("a-different-token")


class TestEventLoopIsFree:
    """Cover the blocking call contract of issue #1858."""

    async def test_the_mist_lookup_runs_off_the_event_loop(
        self,
        app: FastAPI,
        store: SessionStore,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        seen: list[int] = []

        def _record_thread(self: AuthService, token: str) -> MistPrivileges:
            seen.append(threading.get_ident())
            return TEST_PRIVILEGES

        monkeypatch.setattr(AuthService, "validate_token", _record_thread)
        session_id = store.create(TEST_TOKEN)
        async with _client(app) as client:
            response = await client.get(
                "/api/v1/protected",
                cookies={"mist_session": session_id},
            )
        assert response.status_code == HTTP_OK
        assert seen and seen[0] != threading.get_ident()

    async def test_two_concurrent_requests_do_not_serialize(
        self,
        app: FastAPI,
        store: SessionStore,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def _slow(self: AuthService, token: str) -> MistPrivileges:
            time.sleep(0.25)
            return TEST_PRIVILEGES

        monkeypatch.setattr(AuthService, "validate_token", _slow)
        first_id = store.create(TEST_TOKEN)
        second_id = store.create(TEST_TOKEN)
        start = time.perf_counter()
        async with _client(app) as client:
            await asyncio.gather(
                client.get("/api/v1/protected", cookies={"mist_session": first_id}),
                client.get("/api/v1/protected", cookies={"mist_session": second_id}),
            )
        assert (time.perf_counter() - start) < MAX_CONCURRENT_SECONDS


class TestUpstreamFailureSeparation:
    """Cover the 503 against 401 contract of issue #1858."""

    async def test_an_unreachable_mist_api_returns_503(
        self,
        app: FastAPI,
        store: SessionStore,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def _unreachable(self: AuthService, token: str) -> MistPrivileges:
            raise MistApiUnavailableError("connection refused")

        monkeypatch.setattr(AuthService, "validate_token", _unreachable)
        session_id = store.create(TEST_TOKEN)
        async with _client(app) as client:
            response = await client.get(
                "/api/v1/protected",
                cookies={"mist_session": session_id},
            )
        assert response.status_code == HTTP_SERVICE_UNAVAILABLE

    async def test_a_rejected_token_returns_401(
        self,
        app: FastAPI,
        store: SessionStore,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(AuthService, "validate_token", lambda self, token: MistPrivileges())
        session_id = store.create(TEST_TOKEN)
        async with _client(app) as client:
            response = await client.get(
                "/api/v1/protected",
                cookies={"mist_session": session_id},
            )
        assert response.status_code == HTTP_UNAUTHORIZED


class TestSessionStoreBehavior:
    """Cover the store itself, without an application."""

    def test_a_new_identifier_is_opaque(self, store: SessionStore) -> None:
        session_id = store.create(TEST_TOKEN)
        assert session_id != TEST_TOKEN
        assert len(session_id) >= MIN_SESSION_ID_LENGTH

    def test_delete_reports_whether_a_record_existed(self, store: SessionStore) -> None:
        session_id = store.create(TEST_TOKEN)
        assert store.delete(session_id) is True
        assert store.delete(session_id) is False

    def test_a_stale_result_forces_a_new_lookup(self, store: SessionStore) -> None:
        session_id = store.create(TEST_TOKEN, {"email": "a@b.com"})
        record = store.resolve(session_id)
        assert record is not None
        assert record.privileges_are_fresh() is True
        assert record.privileges_are_fresh(now=record.verified_at + 400) is False
