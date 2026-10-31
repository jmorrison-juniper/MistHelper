"""Count SDK instances and verify secret-free diagnostics."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import hvac
import pytest

from src.shared.mist import session as session_module
from src.shared.mist.rate_limit import OrgRateLimiter
from src.shared.mist.session import MistSessionFactory

if TYPE_CHECKING:
    from tests.unit.mist.token_resolution.conftest import TokenContext


class TestSessionBoundary:
    """Exercise the real session method, not an extracted method or factory double."""

    def test_factory_import_uses_this_backend(self, context: TokenContext) -> None:
        backend = Path(__file__).resolve().parents[4]
        expected = backend / "src" / "shared" / "mist" / "session.py"

        assert Path(session_module.__file__).resolve() == expected
        assert type(context.factory) is MistSessionFactory
        assert context.factory._settings is context.settings
        assert context.factory._redis is context.cache
        vault_client = context.factory._vault
        assert isinstance(vault_client, hvac.Client)
        assert vault_client.secrets.kv.v2.read_secret_version is context.vault
        assert context.sdk.call_count == 0

    @pytest.mark.parametrize(
        "failure",
        [
            pytest.param(ValueError("controlled SDK argument"), id="argument"),
            pytest.param(RuntimeError("controlled SDK failure"), id="runtime"),
            pytest.param(TimeoutError("controlled SDK timeout"), id="timeout"),
            pytest.param(RuntimeError("HTTP 403"), id="http-4xx"),
            pytest.param(RuntimeError("HTTP 500"), id="http-5xx"),
        ],
    )
    def test_sdk_error_identity(self, context: TokenContext, failure: Exception) -> None:
        context.cache.get.return_value = "cache-opaque"
        context.sdk.side_effect = failure

        with pytest.raises(type(failure)) as raised:
            MistSessionFactory.create_session(context.factory, "org-one")

        assert raised.value is failure
        context.sdk.assert_called_once_with(host="api.eu.mist.com", apitoken="cache-opaque")
        context.vault.assert_not_called()
        context.cache.setex.assert_not_called()

    def test_constructor_arguments(self, context: TokenContext) -> None:
        context.settings.mist_api_host = "api.gc1.mist.com"
        context.settings.mist_api_token = " \tenv-opaque\r\n"

        result = context.factory.create_session("org-two")

        assert result is context.sdk.return_value
        context.sdk.assert_called_once_with(host="api.gc1.mist.com", apitoken=" \tenv-opaque\r\n")
        context.cache.setex.assert_not_called()
        context.cache.get.assert_called_once_with("mist_token:org-two")


class TestProductDiagnostics:
    """Record source decisions. Do not include credential values."""

    secret_markers = (
        "CACHE_SECRET_MARKER",
        "VAULT_SECRET_MARKER",
        "ENV_SECRET_MARKER",
        "BODY_SECRET_MARKER",
        "HEADER_SECRET_MARKER",
    )

    def test_failure_log(self, context: TokenContext, caplog: pytest.LogCaptureFixture) -> None:
        context.cache.get.return_value = "\u2003"
        context.vault.return_value = {"data": {"data": {"api_token": "\u00a0"}}}
        context.settings.mist_api_token = "\u202f"

        with (
            caplog.at_level(logging.WARNING, logger="src.shared.mist.session"),
            pytest.raises(RuntimeError, match=r"^No Mist API token for org org-one$") as raised,
        ):
            context.factory.create_session("org-one")

        assert str(raised.value) == "No Mist API token for org org-one"
        assert "api_token" in caplog.text
        assert "mist_api_token" in caplog.text
        assert "checked=3" in caplog.text
        assert any(record.levelno == logging.ERROR for record in caplog.records)
        assert all(record.getMessage().isascii() for record in caplog.records)
        assert context.sdk.call_count == 0
        assert context.cache.setex.call_count == 0

    def test_redaction(self, context: TokenContext, caplog: pytest.LogCaptureFixture) -> None:
        context.cache.get.return_value = {"api_token": "CACHE_SECRET_MARKER"}
        reply = {
            "api_token": ["VAULT_SECRET_MARKER"],
            "body": "BODY_SECRET_MARKER",
            "headers": {"Authorization": "HEADER_SECRET_MARKER"},
        }
        context.vault.return_value = {"data": {"data": reply}}
        context.settings.mist_api_token = {"api_token": "ENV_SECRET_MARKER"}

        with (
            caplog.at_level(logging.DEBUG, logger="src.shared.mist.session"),
            pytest.raises(RuntimeError, match=r"^No Mist API token for org org-one$") as raised,
        ):
            context.factory.create_session("org-one")

        diagnostics = caplog.text + str(raised.value)
        for marker in self.secret_markers:
            assert marker not in diagnostics
        assert "cache" in diagnostics.lower()
        assert "vault" in diagnostics.lower()
        assert "checked=3" in diagnostics
        assert context.sdk.call_count == 0
        assert context.cache.setex.call_count == 0

    def test_fallback_log(self, context: TokenContext, caplog: pytest.LogCaptureFixture) -> None:
        context.cache.get.return_value = ["CACHE_SECRET_MARKER"]
        context.vault.return_value = {"data": {"data": {"api_token": b"VAULT_SECRET_MARKER"}}}
        context.settings.mist_api_token = "ENV_SECRET_MARKER"

        with caplog.at_level(logging.WARNING, logger="src.shared.mist.session"):
            result = context.factory.create_session("org-one")

        assert result is context.sdk.return_value
        context.sdk.assert_called_once_with(host="api.eu.mist.com", apitoken="ENV_SECRET_MARKER")
        assert "cache" in caplog.text.lower()
        assert "vault" in caplog.text.lower()
        assert "checked=1" in caplog.text
        assert "checked=2" in caplog.text
        assert "SECRET_MARKER" not in caplog.text
        assert context.cache.setex.call_count == 0

    def test_no_candidate_inspection(self, context: TokenContext) -> None:
        truthiness = MagicMock(side_effect=AssertionError("Do not evaluate non-string truthiness"))
        formatting = MagicMock(side_effect=AssertionError("Do not format a rejected credential"))
        candidate = MagicMock(__bool__=truthiness, __str__=formatting)
        context.cache.get.return_value = candidate
        context.vault.return_value = {"data": {"data": {"api_token": candidate}}}
        context.settings.mist_api_token = candidate

        with pytest.raises(RuntimeError, match=r"^No Mist API token for org org-one$"):
            context.factory.create_session("org-one")

        truthiness.assert_not_called()
        formatting.assert_not_called()
        assert context.sdk.call_count == 0
        assert context.cache.setex.call_count == 0


class TestRateLimiterPreservation:
    """Token rejection must not change the separate rate-limit boundary."""

    async def test_injected_async_client_keeps_org_bucket(self, context: TokenContext) -> None:
        rate_client = AsyncMock()
        rate_client.incr.return_value = 1
        context.factory._rate_redis = rate_client

        limiter = context.factory.create_rate_limiter("org-two")

        assert isinstance(limiter, OrgRateLimiter)
        assert limiter._redis is rate_client
        assert limiter._key == "ratelimit:org-two"
        assert await limiter.acquire() == 0.0
        rate_client.incr.assert_awaited_once_with("ratelimit:org-two")
        rate_client.expire.assert_awaited_once_with("ratelimit:org-two", 3_600)
        assert context.cache.mock_calls == []
        assert context.vault.mock_calls == []
        assert context.sdk.call_count == 0

    def test_disabled_limiter_keeps_visible_current_policy(
        self,
        context: TokenContext,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        provider = MagicMock(return_value=None)
        monkeypatch.setattr(context.factory, "_get_async_redis_client", provider)

        with caplog.at_level(logging.WARNING, logger="src.shared.mist.session"):
            limiter = context.factory.create_rate_limiter("org-two")

        assert limiter is None
        provider.assert_called_once_with()
        assert "Rate limiter disabled for org org-two: no async Redis client" in caplog.text
        assert context.sdk.call_count == 0
