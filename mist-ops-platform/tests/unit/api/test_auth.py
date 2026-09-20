"""Unit tests for auth middleware scope enforcement (T107)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.shared.services import auth as auth_module
from src.shared.services.auth import AuthService, MistApiUnavailableError, MistPrivileges

STATUS_UNAUTHORIZED = 401  # Name the HTTP 4xx token rejection used by auth tests.
STATUS_UNAVAILABLE = 503  # Name the HTTP 5xx service failure used by auth tests.


class _FakeRedisClient:
    """Return one prepared value to tests that exercise the real cache reader."""

    def __init__(self, raw_value: bytes) -> None:
        self.raw_value = raw_value  # Preserve the exact Redis bytes for this test case.
        self.key_read = ""  # Record the key so the test proves the cache path ran.

    def get(self, key: str) -> bytes:
        self.key_read = key  # Capture the digest key without exposing the token.
        return self.raw_value  # Return the prepared bytes to exercise parsing.


class _SchemaDriftPrivileges:
    """Require one new field to simulate a later MistPrivileges schema."""

    def __init__(self, email: str, required_scope: str) -> None:
        self.email = email  # Keep the old field so the missing new field causes TypeError.
        self.required_scope = required_scope  # Require the future field for schema drift.


class TestMistPrivileges:
    """Verify MistPrivileges data class."""

    def test_has_org_access_true(self) -> None:
        privs = MistPrivileges(
            name="test-user",
            email="u@example.com",
            org_ids=["org-aaa", "org-bbb"],
            site_ids=["site-111"],
        )
        assert privs.has_org_access("org-aaa") is True

    def test_has_org_access_false(self) -> None:
        privs = MistPrivileges(
            name="test-user",
            email="u@example.com",
            org_ids=["org-aaa"],
            site_ids=[],
        )
        assert privs.has_org_access("org-zzz") is False

    def test_empty_privileges(self) -> None:
        privs = MistPrivileges(
            name="nobody",
            email="",
            org_ids=[],
            site_ids=[],
        )
        assert privs.has_org_access("any") is False


class TestAuthService:
    """Verify AuthService token validation and caching."""

    def setup_method(self) -> None:
        self.mock_redis = MagicMock()
        self.svc = AuthService(redis_client=self.mock_redis)

    @patch.object(AuthService, "_fetch_self")
    @patch.object(AuthService, "_read_cache", return_value=None)
    def test_validate_token_calls_fetch_on_cache_miss(
        self,
        mock_cache: MagicMock,
        mock_fetch: MagicMock,
    ) -> None:
        mock_privs = MistPrivileges(
            name="user",
            email="u@e.com",
            org_ids=["org-1"],
            site_ids=[],
        )
        mock_fetch.return_value = mock_privs

        result = self.svc.validate_token("tok-abc")

        mock_fetch.assert_called_once_with("tok-abc")
        assert result.name == "user"

    @patch.object(AuthService, "_read_cache")
    def test_validate_token_returns_cached(
        self,
        mock_cache: MagicMock,
    ) -> None:
        cached_privs = MistPrivileges(
            name="cached",
            email="c@e.com",
            org_ids=["org-cached"],
            site_ids=[],
        )
        mock_cache.return_value = cached_privs

        result = self.svc.validate_token("tok-cached")

        assert result.name == "cached"

    @patch.object(AuthService, "_fetch_self")
    @patch.object(AuthService, "_read_cache", return_value=None)
    @patch.object(AuthService, "_write_cache")
    def test_validate_token_writes_cache(
        self,
        mock_write: MagicMock,
        mock_read: MagicMock,
        mock_fetch: MagicMock,
    ) -> None:
        privs = MistPrivileges(
            name="new",
            email="n@e.com",
            org_ids=[],
            site_ids=[],
        )
        mock_fetch.return_value = privs

        self.svc.validate_token("tok-new")

        mock_write.assert_called_once()

    def test_read_cache_returns_none_and_logs_truncated_value(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        redis_client = _FakeRedisClient(b'{"email": "a@b.c"')  # Simulate a truncated Redis value.
        service = AuthService(redis_client=redis_client)  # Use a fake client for the real reader.

        with caplog.at_level("WARNING", logger=auth_module.__name__):  # Capture the warning.
            result = service._read_cache("tok-truncated")  # Exercise the sign-in cache path.

        assert result is None  # The cache reader must take the same path as a cache miss.
        assert "Discarding an unreadable privilege cache entry" in caplog.text  # Prove the log.
        assert "Expecting ',' delimiter" in caplog.text  # Prove the log keeps the parse cause.
        expected_key = auth_module.privilege_cache_key("tok-truncated")  # Build the expected key.
        assert redis_client.key_read == expected_key  # Prove the real key path.

    def test_read_cache_returns_none_and_logs_empty_body(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        redis_client = _FakeRedisClient(b"")  # Simulate a zero-byte Redis value.
        service = AuthService(redis_client=redis_client)  # Use a fake client for the real reader.

        with caplog.at_level("WARNING", logger=auth_module.__name__):  # Capture the warning.
            result = service._read_cache("tok-empty")  # Exercise the empty-body cache path.

        assert result is None  # The cache reader must take the same path as a cache miss.
        assert caplog.text == ""  # The product treats an empty body as an ordinary cache miss.
        expected_key = auth_module.privilege_cache_key("tok-empty")  # Build the expected key.
        assert redis_client.key_read == expected_key  # Prove the real key path.

    def test_read_cache_returns_none_and_logs_malformed_json(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        redis_client = _FakeRedisClient(b"{not valid JSONDecodeError")  # Simulate damaged Redis JSON.
        service = AuthService(redis_client=redis_client)  # Use a fake client for the real reader.

        with caplog.at_level("WARNING", logger=auth_module.__name__):  # Capture the warning.
            result = service._read_cache("tok-malformed")  # Exercise the malformed cache path.

        assert result is None  # The cache reader must take the same path as a cache miss.
        assert "Discarding an unreadable privilege cache entry" in caplog.text  # Prove the log.
        assert "Expecting property name enclosed in double quotes" in caplog.text  # Prove parse cause.
        expected_key = auth_module.privilege_cache_key("tok-malformed")  # Build the expected key.
        assert redis_client.key_read == expected_key  # Prove the real key path.

    def test_read_cache_returns_none_and_logs_schema_drift(
        self,
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        redis_client = _FakeRedisClient(b'{"email": "a@b.c"}')  # Simulate an old cache schema.
        service = AuthService(redis_client=redis_client)  # Use a fake client for the real reader.
        monkeypatch.setattr(auth_module, "MistPrivileges", _SchemaDriftPrivileges)  # Add drift.

        with caplog.at_level("WARNING", logger=auth_module.__name__):  # Capture the warning.
            result = service._read_cache("tok-schema-drift")  # Exercise schema drift.

        assert result is None  # The cache reader must take the same path as a cache miss.
        assert "Discarding an unreadable privilege cache entry" in caplog.text  # Prove the log.
        assert "required_scope" in caplog.text  # Prove the log keeps the schema drift cause.
        expected_key = auth_module.privilege_cache_key("tok-schema-drift")  # Build the key.
        assert redis_client.key_read == expected_key  # Prove the real key path.

    def test_read_cache_returns_privileges_for_valid_value(self) -> None:
        raw_value = (  # Keep the valid cache payload close to the assertion.
            b'{"email": "a@b.c", "name": "Agent", "is_msp": false, '
            b'"org_ids": ["org-1"], "site_ids": ["site-1"], "org_names": {"org-1": "Org"}}'
        )
        redis_client = _FakeRedisClient(raw_value)  # Match the _write_cache shape.
        service = AuthService(redis_client=redis_client)  # Use a fake client for the real reader.

        result = service._read_cache("tok-valid")  # Exercise the happy path.

        assert isinstance(result, MistPrivileges)  # Prove the guard keeps valid entries.
        assert result.email == "a@b.c"  # Prove the cached identity survives the trip.
        assert result.org_ids == ["org-1"]  # Prove the cached org scope survives the round trip.
        expected_key = auth_module.privilege_cache_key("tok-valid")  # Build the expected key.
        assert redis_client.key_read == expected_key  # Prove the real key path.

    @patch("src.shared.services.auth.mistapi.APISession")
    @patch("src.shared.services.auth.MistEndpointService")
    def test_fetch_self_returns_empty_privileges_on_401(
        self,
        mock_service_cls: MagicMock,
        mock_session_cls: MagicMock,
    ) -> None:
        mock_service = mock_service_cls.return_value  # Use the _fetch_self service double.
        mock_service.list_all_entities.return_value = MagicMock(  # Return a Mist client error.
            success=False,  # Prove the failure branch executes.
            status_code=STATUS_UNAUTHORIZED,  # Exercise the HTTP 4xx token path.
            data={"detail": "Unauthorized"},  # Keep the Mist body visible.
        )

        result = self.svc._fetch_self("tok-bad")  # Validate the token upstream.

        assert result == MistPrivileges()  # The caller maps empty privileges to 401.
        mock_session_cls.assert_called_once_with(  # Verify the token path.
            host="api.mist.com",
            apitoken="tok-bad",
        )
        mock_service.list_all_entities.assert_called_once_with(  # Verify the /self endpoint.
            "self_identity",
            {},
        )

    @patch("src.shared.services.auth.mistapi.APISession")
    @patch("src.shared.services.auth.MistEndpointService")
    def test_fetch_self_raises_unavailable_on_503(
        self,
        mock_service_cls: MagicMock,
        mock_session_cls: MagicMock,
    ) -> None:
        mock_service = mock_service_cls.return_value  # Use the _fetch_self service double.
        mock_service.list_all_entities.return_value = MagicMock(  # Return a Mist server error.
            success=False,  # Prove the HTTP failure branch executes.
            status_code=STATUS_UNAVAILABLE,  # Exercise the HTTP 5xx failure path.
            data={"detail": "Service unavailable"},  # Keep the body distinct.
        )

        with pytest.raises(MistApiUnavailableError, match="status 503"):  # Assert the signal.
            self.svc._fetch_self("tok-server-error")  # Call the uncached seam.

        mock_session_cls.assert_called_once_with(  # Verify the token path.
            host="api.mist.com",
            apitoken="tok-server-error",
        )
        mock_service.list_all_entities.assert_called_once_with(  # Verify the /self endpoint.
            "self_identity",
            {},
        )

    @patch("src.shared.services.auth.mistapi.APISession")
    @patch("src.shared.services.auth.MistEndpointService")
    def test_fetch_self_direct_service_reports_503(
        self,
        mock_service_cls: MagicMock,
        mock_session_cls: MagicMock,
    ) -> None:
        status_code = 503  # Prove the HTTP 5xx status family with a status-named value.
        service = AuthService(redis_client=MagicMock())  # Call source directly, not through setup state.
        mock_service = mock_service_cls.return_value  # Use the _fetch_self service double.
        mock_service.list_all_entities.return_value = MagicMock(  # Return a Mist server error.
            success=False,  # Prove the HTTP failure branch executes.
            status_code=status_code,  # Exercise the HTTP 5xx failure path.
            data={"detail": "Service unavailable"},  # Keep the body distinct.
        )

        with pytest.raises(MistApiUnavailableError, match="status 503"):  # Assert the observable signal.
            service._fetch_self("tok-server-error")  # Call the uncached seam directly.

        mock_session_cls.assert_called_once_with(host="api.mist.com", apitoken="tok-server-error")
