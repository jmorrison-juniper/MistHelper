"""Prove required token rejection through the imported session factory."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import call

import pytest

if TYPE_CHECKING:
    from tests.unit.mist.token_resolution.conftest import TokenContext


class TestOriginalFailures:
    """These three cases must fail against the unchanged original source."""

    def test_blank_cache_uses_vault(self, context: TokenContext) -> None:
        context.cache.get.return_value = "   "
        context.vault.return_value = {"data": {"data": {"api_token": "vault-opaque"}}}
        context.settings.mist_api_token = "env-opaque"

        result = context.factory.create_session("org-one")

        context.sdk.assert_called_once_with(host="api.eu.mist.com", apitoken="vault-opaque")
        assert result is context.sdk.return_value
        context.vault.assert_called_once_with(
            path="secret/data/mist/tokens/org-one",
            raise_on_deleted_version=True,
        )
        context.cache.setex.assert_called_once_with("mist_token:org-one", 300, "vault-opaque")

    def test_blank_vault_uses_env(self, context: TokenContext) -> None:
        context.vault.return_value = {"data": {"data": {"api_token": "\t "}}}
        context.settings.mist_api_token = "env-opaque"

        result = context.factory.create_session("org-one")

        context.sdk.assert_called_once_with(host="api.eu.mist.com", apitoken="env-opaque")
        assert result is context.sdk.return_value
        context.cache.get.assert_called_once_with("mist_token:org-one")
        context.vault.assert_called_once_with(
            path="secret/data/mist/tokens/org-one",
            raise_on_deleted_version=True,
        )
        context.cache.setex.assert_not_called()

    def test_all_blank_stops_sdk(self, context: TokenContext) -> None:
        context.cache.get.return_value = " "
        context.vault.return_value = {"data": {"data": {"api_token": "\t "}}}
        context.settings.mist_api_token = "\n "

        with pytest.raises(RuntimeError, match=r"^No Mist API token for org org-one$"):
            context.factory.create_session("org-one")

        assert context.sdk.call_count == 0
        assert context.cache.setex.call_count == 0


class TestProviderFallbacks:
    """An unusable provider value must not block the next provider."""

    @pytest.mark.parametrize(
        "candidate",
        [
            pytest.param(None, id="none"),
            pytest.param("", id="empty"),
            pytest.param(" \t\r\n", id="ascii-whitespace"),
            pytest.param("\u00a0\u2003\u202f", id="unicode-whitespace"),
            pytest.param(b"", id="empty-cache-bytes"),
            pytest.param(b" \t\r\n", id="blank-cache-bytes"),
            pytest.param("\u00a0\u2003".encode(), id="unicode-cache-bytes"),
            pytest.param(bytearray(b"CACHE_SECRET_MARKER"), id="unsupported-bytearray"),
            pytest.param(0, id="zero"),
            pytest.param(7, id="integer"),
            pytest.param(False, id="false"),
            pytest.param(True, id="true"),
            pytest.param([], id="empty-list"),
            pytest.param(["CACHE_SECRET_MARKER"], id="list"),
            pytest.param({}, id="empty-dict"),
            pytest.param({"api_token": "CACHE_SECRET_MARKER"}, id="dict"),
            pytest.param(object(), id="object"),
        ],
    )
    def test_unusable_cache_uses_vault(self, context: TokenContext, candidate: object) -> None:
        context.cache.get.return_value = candidate
        context.vault.return_value = {"data": {"data": {"api_token": "vault-opaque"}}}
        context.settings.mist_api_token = "env-opaque"

        resolved = context.factory._resolve_token("org-one")

        assert resolved == "vault-opaque"
        assert context.cache.get.call_args_list == [call("mist_token:org-one")]
        context.cache.setex.assert_called_once_with("mist_token:org-one", 300, "vault-opaque")
        context.vault.assert_called_once_with(
            path="secret/data/mist/tokens/org-one",
            raise_on_deleted_version=True,
        )
        assert context.sdk.call_count == 0

    @pytest.mark.parametrize(
        "candidate",
        [
            pytest.param(None, id="none"),
            pytest.param("", id="empty"),
            pytest.param(" \t\r\n", id="ascii-whitespace"),
            pytest.param("\u00a0\u2003\u202f", id="unicode-whitespace"),
            pytest.param(b"VAULT_SECRET_MARKER", id="unsupported-bytes"),
            pytest.param(bytearray(b"VAULT_SECRET_MARKER"), id="unsupported-bytearray"),
            pytest.param(0, id="zero"),
            pytest.param(7, id="integer"),
            pytest.param(False, id="false"),
            pytest.param(True, id="true"),
            pytest.param([], id="empty-list"),
            pytest.param(["VAULT_SECRET_MARKER"], id="list"),
            pytest.param({}, id="empty-dict"),
            pytest.param({"api_token": "VAULT_SECRET_MARKER"}, id="dict"),
            pytest.param(object(), id="object"),
        ],
    )
    def test_unusable_vault_uses_env(self, context: TokenContext, candidate: object) -> None:
        context.vault.return_value = {"data": {"data": {"api_token": candidate}}}
        context.settings.mist_api_token = "env-opaque"

        result = context.factory.create_session("org-one")

        assert result is context.sdk.return_value
        context.sdk.assert_called_once_with(host="api.eu.mist.com", apitoken="env-opaque")
        context.vault.assert_called_once_with(
            path="secret/data/mist/tokens/org-one",
            raise_on_deleted_version=True,
        )
        assert context.cache.setex.call_count == 0


class TestRequiredCredentials:
    """No unusable value can produce a session or a cache write."""

    @pytest.mark.parametrize(
        "candidates",
        [
            pytest.param((None, None, None), id="all-none"),
            pytest.param(("", "", ""), id="all-empty"),
            pytest.param((" \t", "\n ", "\r\n"), id="all-ascii-whitespace"),
            pytest.param(("\u00a0", "\u2003", "\u202f"), id="all-unicode-whitespace"),
            pytest.param((b"", b"", b""), id="all-empty-bytes"),
            pytest.param((b" \t", b" \t", b" \t"), id="all-blank-bytes"),
            pytest.param((0, 0, 0), id="all-zero"),
            pytest.param((7, 7, 7), id="all-integer"),
            pytest.param((False, False, False), id="all-false"),
            pytest.param((True, True, True), id="all-true"),
            pytest.param(([], [], []), id="all-empty-list"),
            pytest.param(({}, {}, {}), id="all-empty-dict"),
            pytest.param(({"api_token": "cache-marker"}, ["vault-marker"], 7), id="mixed"),
        ],
    )
    def test_all_unusable_sources_stop_sdk(
        self, context: TokenContext, candidates: tuple[object, object, object]
    ) -> None:
        cached, vaulted, configured = candidates
        context.cache.get.return_value = cached
        context.vault.return_value = {"data": {"data": {"api_token": vaulted}}}
        context.settings.mist_api_token = configured

        with pytest.raises(RuntimeError, match=r"^No Mist API token for org org-one$") as failure:
            context.factory.create_session("org-one")

        assert str(failure.value) == "No Mist API token for org org-one"
        assert context.sdk.call_count == 0
        assert context.cache.setex.call_count == 0
        context.cache.get.assert_called_once_with("mist_token:org-one")
        context.vault.assert_called_once_with(
            path="secret/data/mist/tokens/org-one",
            raise_on_deleted_version=True,
        )

    @pytest.mark.parametrize(
        "candidate",
        [
            pytest.param(None, id="none"),
            pytest.param("", id="empty"),
            pytest.param(" \t\r\n", id="ascii-whitespace"),
            pytest.param("\u00a0\u2003\u202f", id="unicode-whitespace"),
            pytest.param(b"ENV_SECRET_MARKER", id="unsupported-bytes"),
            pytest.param(bytearray(b"ENV_SECRET_MARKER"), id="unsupported-bytearray"),
            pytest.param(0, id="zero"),
            pytest.param(7, id="integer"),
            pytest.param(False, id="false"),
            pytest.param(True, id="true"),
            pytest.param([], id="empty-list"),
            pytest.param(["ENV_SECRET_MARKER"], id="list"),
            pytest.param({}, id="empty-dict"),
            pytest.param({"api_token": "ENV_SECRET_MARKER"}, id="dict"),
            pytest.param(object(), id="object"),
        ],
    )
    def test_unusable_env_stops_sdk(self, context: TokenContext, candidate: object) -> None:
        context.settings.mist_api_token = candidate

        with pytest.raises(RuntimeError, match=r"^No Mist API token for org org-one$"):
            context.factory.create_session("org-one")

        assert context.sdk.call_count == 0
        assert context.cache.setex.call_count == 0

    def test_absent_provider_clients_stop_sdk(self, context: TokenContext) -> None:
        context.factory._redis = None
        context.factory._vault = None

        with pytest.raises(RuntimeError, match=r"^No Mist API token for org org-one$"):
            context.factory.create_session("org-one")

        assert context.sdk.call_count == 0
        assert context.cache.mock_calls == []
        assert context.vault.mock_calls == []
