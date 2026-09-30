"""Unit tests for the admin token hygiene Mist client."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import mistapi

from src.reports.admin_token_hygiene.client import AdminTokenHygieneClient


@dataclass
class FakeResponse:
    """Small SDK response double."""

    data: Any
    status_code: int = 200


def test_client_reads_admins_without_logging_payload(monkeypatch: Any) -> None:
    """The client must return admin rows from the SDK response."""
    monkeypatch.setattr(mistapi, "get_all", lambda response, mist_session: response.data)
    monkeypatch.setattr(
        mistapi.api.v1.orgs.admins, "listOrgAdmins", lambda session, org_id: FakeResponse([{"email": "a"}])
    )
    client = AdminTokenHygieneClient(object(), "org-1")
    assert client.list_admins() == [{"email": "a"}]


def test_client_reads_tokens_without_filtering_metadata(monkeypatch: Any) -> None:
    """The model owns token redaction, so the client returns token metadata."""
    monkeypatch.setattr(mistapi, "get_all", lambda response, mist_session: response.data)
    monkeypatch.setattr(
        mistapi.api.v1.orgs.apitokens, "listOrgApiTokens", lambda session, org_id: FakeResponse([{"id": "t"}])
    )
    client = AdminTokenHygieneClient(object(), "org-1")
    assert client.list_tokens() == [{"id": "t"}]


def test_client_reads_settings(monkeypatch: Any) -> None:
    """The client must return the settings object from the SDK response."""
    monkeypatch.setattr(
        mistapi.api.v1.orgs.setting, "getOrgSettings", lambda session, org_id: FakeResponse({"password_policy": {}})
    )
    client = AdminTokenHygieneClient(object(), "org-1")
    assert client.get_settings() == {"password_policy": {}}
