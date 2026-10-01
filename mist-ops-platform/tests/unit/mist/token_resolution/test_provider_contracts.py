"""Preserve provider values, cache scope, and exception policies."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING
from unittest.mock import PropertyMock, call, patch

import hvac
import pytest
import requests
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import ResponseError as RedisResponseError

from src.shared.mist.session import MistSessionFactory

if TYPE_CHECKING:
    from tests.unit.mist.token_resolution.conftest import TokenContext


class TestAcceptedTokens:
    """Keep each accepted string unchanged."""

    @pytest.mark.parametrize("source", ["cache", "vault", "configured"])
    @pytest.mark.parametrize(
        "candidate",
        [
            pytest.param("x", id="short"),
            pytest.param("0", id="zero-text"),
            pytest.param("None", id="none-text"),
            pytest.param("null", id="null-text"),
            pytest.param("changeme", id="placeholder-text"),
            pytest.param(" \topaque-value\r\n", id="surrounding-whitespace"),
            pytest.param("opaque:/+=_-'\".", id="punctuation"),
            pytest.param("opaque-\u00e9-\u6771", id="unicode"),
            pytest.param("\u200b", id="non-whitespace-format-character"),
            pytest.param("x" * 100_001, id="oversized"),
        ],
    )
    def test_opaque_tokens(self, context: TokenContext, source: str, candidate: str) -> None:
        if source == "cache":
            context.cache.get.return_value = candidate
        elif source == "vault":
            context.vault.return_value = {"data": {"data": {"api_token": candidate}}}
        else:
            context.settings.mist_api_token = candidate

        result = context.factory.create_session("org-one")

        assert result is context.sdk.return_value
        context.sdk.assert_called_once_with(host="api.eu.mist.com", apitoken=candidate)
        cache_key = "mist_token:org-one"
        expected_write = [call(cache_key, 300, candidate)] if source == "vault" else []
        assert context.cache.setex.call_args_list == expected_write

    @pytest.mark.parametrize(
        ("candidate", "expected"),
        [
            pytest.param(b"cache-opaque", "cache-opaque", id="ascii-bytes"),
            pytest.param(b" \tcache-opaque\r\n", " \tcache-opaque\r\n", id="untrimmed-bytes"),
            pytest.param("opaque-\u00e9-\u6771".encode(), "opaque-\u00e9-\u6771", id="unicode"),
        ],
    )
    def test_cache_bytes(self, context: TokenContext, candidate: bytes, expected: str) -> None:
        context.cache.get.return_value = candidate

        resolved = context.factory._resolve_token("org-one")

        assert resolved == expected
        context.vault.assert_not_called()
        context.cache.setex.assert_not_called()
        assert context.sdk.call_count == 0

    @pytest.mark.parametrize("org_id", ["org-one", "org-two"])
    def test_vault_cache_key_ttl_scope(self, context: TokenContext, org_id: str) -> None:
        context.vault.return_value = {"data": {"data": {"api_token": " \tvault-opaque\r\n"}}}

        resolved = context.factory._resolve_token(org_id)

        assert resolved == " \tvault-opaque\r\n"
        context.cache.get.assert_called_once_with(f"mist_token:{org_id}")
        context.vault.assert_called_once_with(
            path=f"secret/data/mist/tokens/{org_id}",
            raise_on_deleted_version=True,
        )
        context.cache.setex.assert_called_once_with(
            f"mist_token:{org_id}",
            300,
            " \tvault-opaque\r\n",
        )

    def test_healthy_cache_bypasses_later_sources(self, context: TokenContext) -> None:
        context.cache.get.return_value = "cache-opaque"
        context.vault.side_effect = AssertionError("A cache hit must not read Vault")
        configured = PropertyMock(side_effect=AssertionError("Do not read the fallback setting"))

        with patch.object(type(context.settings), "mist_api_token", configured, create=True):
            resolved = context.factory._resolve_token("org-one")

        assert resolved == "cache-opaque"
        configured.assert_not_called()
        context.vault.assert_not_called()
        context.cache.setex.assert_not_called()

    def test_healthy_vault_bypasses_configured_env(self, context: TokenContext) -> None:
        context.vault.return_value = {"data": {"data": {"api_token": "vault-opaque"}}}
        configured = PropertyMock(side_effect=AssertionError("Vault must not read the setting"))

        with patch.object(type(context.settings), "mist_api_token", configured, create=True):
            resolved = context.factory._resolve_token("org-one")

        assert resolved == "vault-opaque"
        configured.assert_not_called()
        context.cache.setex.assert_called_once_with("mist_token:org-one", 300, "vault-opaque")


class TestProviderFailures:
    """Preserve provider exceptions. Keep the failure policy for Vault."""

    @pytest.mark.parametrize(
        "failure",
        [
            pytest.param(RedisConnectionError("controlled cache connection"), id="connection"),
            pytest.param(RedisResponseError("controlled cache response"), id="response"),
            pytest.param(requests.exceptions.Timeout("controlled cache timeout"), id="timeout"),
        ],
    )
    def test_cache_read_error(self, context: TokenContext, failure: Exception) -> None:
        context.cache.get.side_effect = failure
        context.settings.mist_api_token = "env-opaque"

        with pytest.raises(type(failure)) as raised:
            MistSessionFactory.create_session(context.factory, "org-one")

        assert raised.value is failure
        assert context.sdk.call_count == 0
        context.cache.setex.assert_not_called()
        context.vault.assert_not_called()

    def test_invalid_cache_bytes_keep_decode_failure(self, context: TokenContext) -> None:
        context.cache.get.return_value = b"\xff"
        context.settings.mist_api_token = "env-opaque"

        with pytest.raises(UnicodeDecodeError) as raised:
            context.factory.create_session("org-one")

        assert raised.value.object == b"\xff"
        assert raised.value.encoding == "utf-8"
        assert context.sdk.call_count == 0
        context.cache.setex.assert_not_called()
        context.vault.assert_not_called()

    @pytest.mark.parametrize(
        "failure",
        [
            pytest.param(RedisConnectionError("controlled cache write"), id="connection"),
            pytest.param(RedisResponseError("controlled cache write"), id="response"),
            pytest.param(requests.exceptions.Timeout("controlled cache write"), id="timeout"),
        ],
    )
    def test_cache_write_error(self, context: TokenContext, failure: Exception) -> None:
        context.vault.return_value = {"data": {"data": {"api_token": "vault-opaque"}}}
        context.cache.setex.side_effect = failure
        context.settings.mist_api_token = "env-opaque"

        with pytest.raises(type(failure)) as raised:
            MistSessionFactory.create_session(context.factory, "org-one")

        assert raised.value is failure
        context.cache.setex.assert_called_once_with("mist_token:org-one", 300, "vault-opaque")
        assert context.sdk.call_count == 0

    @pytest.mark.parametrize(
        ("status_code", "failure"),
        [
            pytest.param(403, hvac.exceptions.Forbidden("HTTP 403"), id="http-4xx"),
            pytest.param(500, hvac.exceptions.InternalServerError("HTTP 500"), id="http-5xx"),
            pytest.param(None, requests.exceptions.Timeout("Vault timeout fixture"), id="timeout"),
            pytest.param(
                None,
                requests.exceptions.ConnectionError("Vault connection fixture"),
                id="connection",
            ),
            pytest.param(None, json.JSONDecodeError("Vault JSON", "", 0), id="malformed-json"),
            pytest.param(None, TypeError("Vault type fixture"), id="type"),
        ],
    )
    def test_vault_error_fallback(
        self,
        context: TokenContext,
        status_code: int | None,
        failure: Exception,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        reader = context.vault
        reader.side_effect = failure
        context.settings.mist_api_token = "env-opaque"

        with caplog.at_level(logging.DEBUG, logger="src.shared.mist.session"):
            result = MistSessionFactory.create_session(context.factory, "org-one")

        assert reader.side_effect is failure
        assert result is context.sdk.return_value
        context.sdk.assert_called_once_with(host="api.eu.mist.com", apitoken="env-opaque")
        expected = "Vault lookup failed for org org-one after " + type(failure).__name__
        assert expected in caplog.text
        if status_code is not None:
            assert str(failure) == f"HTTP {status_code}, on None None"
        assert context.cache.setex.call_count == 0

    @pytest.mark.parametrize(
        "reply",
        [
            pytest.param(None, id="empty-body"),
            pytest.param({}, id="missing-data"),
            pytest.param({"data": {}}, id="missing-nested-data"),
            pytest.param({"data": {"data": None}}, id="invalid-nested-data"),
        ],
    )
    def test_vault_reply_fallback(self, context: TokenContext, reply: object) -> None:
        context.vault.return_value = reply
        context.settings.mist_api_token = "env-opaque"

        result = MistSessionFactory.create_session(context.factory, "org-one")

        assert result is context.sdk.return_value
        context.sdk.assert_called_once_with(host="api.eu.mist.com", apitoken="env-opaque")
        assert context.cache.setex.call_count == 0


class TestConfiguredFallback:
    """Read the configured setting. Do not read the global environment."""

    def test_env_only(self, context: TokenContext, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MIST_API_TOKEN", "GLOBAL_SECRET_MARKER")
        monkeypatch.setenv("MIST_APITOKEN", "GLOBAL_SECRET_MARKER")

        with pytest.raises(RuntimeError, match=r"^No Mist API token for org org-one$"):
            context.factory.create_session("org-one")

        assert context.sdk.call_count == 0
        assert context.cache.setex.call_count == 0

    def test_missing_clients_keep_configured_fallback(self, context: TokenContext) -> None:
        context.factory._redis = None
        context.factory._vault = None
        context.settings.mist_api_token = "env-opaque"

        resolved = context.factory._resolve_token("org-one")

        assert resolved == "env-opaque"
        assert context.cache.mock_calls == []
        assert context.vault.mock_calls == []

    def test_vault_without_cache(self, context: TokenContext) -> None:
        context.factory._redis = None
        context.vault.return_value = {"data": {"data": {"api_token": "vault-opaque"}}}

        resolved = context.factory._resolve_token("org-one")

        assert resolved == "vault-opaque"
        assert context.cache.mock_calls == []
        assert context.sdk.call_count == 0
