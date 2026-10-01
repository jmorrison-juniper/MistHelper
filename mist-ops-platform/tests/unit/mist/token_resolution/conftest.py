"""Controlled providers for MistSessionFactory."""

from __future__ import annotations

import socket
from dataclasses import dataclass
from unittest.mock import MagicMock, create_autospec

import hvac
import mistapi
import pytest
from redis import Redis

from src.shared.config.settings import AppSettings
from src.shared.mist.session import MistSessionFactory


@dataclass
class TokenContext:
    """Store the factory and mocks for the providers."""

    factory: MistSessionFactory
    settings: MagicMock
    cache: MagicMock
    vault: MagicMock
    sdk: MagicMock


@pytest.fixture(autouse=True)
def reject_live_transports(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail if a required token test attempts a live connection."""
    blocked = MagicMock(side_effect=AssertionError("Live token-test transport is forbidden"))
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)


@pytest.fixture
def context(monkeypatch: pytest.MonkeyPatch) -> TokenContext:
    """Import the real factory and replace only its external providers."""
    settings = MagicMock(spec=AppSettings)
    settings.mist_api_host = "api.eu.mist.com"
    settings.mist_api_token = None
    cache = MagicMock(spec=Redis)
    cache.get.return_value = None
    vault = MagicMock(spec=hvac.Client)
    vault.secrets.kv.v2.read_secret_version.return_value = {"data": {"data": {}}}
    sdk = create_autospec(mistapi.APISession)
    monkeypatch.setattr(mistapi, "APISession", sdk)
    monkeypatch.setattr(MistSessionFactory, "_build_vault_client", MagicMock(return_value=vault))
    monkeypatch.setattr(
        MistSessionFactory,
        "_build_redis_client",
        MagicMock(side_effect=AssertionError("The injected cache must bypass Redis construction")),
    )
    factory = MistSessionFactory(settings=settings, redis=cache)
    return TokenContext(factory, settings, cache, vault.secrets.kv.v2.read_secret_version, sdk)
