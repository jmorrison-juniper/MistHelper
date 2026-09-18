"""Unit tests for auth middleware scope enforcement (T107)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.shared.services.auth import AuthService, MistApiUnavailableError, MistPrivileges

STATUS_UNAUTHORIZED = 401  # Name the HTTP 4xx token rejection used by auth tests.
STATUS_UNAVAILABLE = 503  # Name the HTTP 5xx service failure used by auth tests.


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


def test_observable_failure_mode_contracts() -> None:
    """Failure-mode contracts stay explicit for this test module."""
    from tests.support import failure_mode_observations as failure_modes  # Import shared contracts.

    failure_modes.assert_mistapi_empty_result_observation("JSONDecodeError")  # Bad JSON gives empty data.
    failure_modes.assert_mistapi_empty_result_observation(b"")  # Empty body gives empty data.
