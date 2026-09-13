"""Unit tests for auth middleware scope enforcement (T107)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.shared.services.auth import AuthService, MistPrivileges


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
