"""Unit tests for the admin token hygiene Mist client."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import mistapi
import pytest

from src.mist.intelligence.reports.admin_token_hygiene.client import AdminTokenHygieneClient


@dataclass
class FakeResponse:
    """Small SDK response double."""

    data: Any
    status_code: int = 200
    next: str | None = None


class FakePagedSession:
    """Return one planned later page and record the requested link."""

    def __init__(self, later_page: FakeResponse) -> None:
        """Store the page that follows the endpoint response."""
        self._later_page = later_page  # WHY: the fake must return the exact planned second page.
        self.links: list[str] = []  # WHY: the assertion must prove that pagination used this session.

    def mist_get(self, uri: str) -> FakeResponse:
        """Return the planned page for one SDK pagination request."""
        self.links.append(uri)  # WHY: record the SDK request before returning its response.
        return self._later_page  # WHY: complete the two-page response without network access.


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


def test_client_uses_active_session_for_paginated_admins(monkeypatch: Any) -> None:
    """The admin read must traverse a later page through the active session."""
    second_page = FakeResponse([{"email": "b"}])  # WHY: the second page proves pagination did not stop early.
    session = FakePagedSession(second_page)  # WHY: the client must pass this object to the real SDK paginator.
    first_page = FakeResponse([{"email": "a"}], next="/admins?page=2")  # WHY: a next link triggers get_next.
    monkeypatch.setattr(  # WHY: keep the endpoint deterministic while the real paginator runs.
        mistapi.api.v1.orgs.admins,
        "listOrgAdmins",
        lambda active_session, org_id: first_page,
    )
    client = AdminTokenHygieneClient(session, "org-1")  # WHY: bind the session that owns the later-page fetch.

    assert client.list_admins() == [{"email": "a"}, {"email": "b"}]  # WHY: prove both pages reached the caller.
    assert session.links == ["/admins?page=2"]  # WHY: prove self._apisession traversed the next link.


def test_client_reads_settings(monkeypatch: Any) -> None:
    """The client must return the settings object from the SDK response."""
    monkeypatch.setattr(
        mistapi.api.v1.orgs.setting, "getOrgSettings", lambda session, org_id: FakeResponse({"password_policy": {}})
    )
    client = AdminTokenHygieneClient(object(), "org-1")
    assert client.get_settings() == {"password_policy": {}}


def test_client_raises_on_admin_4xx_response(monkeypatch: Any) -> None:
    """The client must fail closed when the admin list returns a 4xx status."""
    monkeypatch.setattr(mistapi, "get_all", lambda response, mist_session: response.data)
    monkeypatch.setattr(mistapi.api.v1.orgs.admins, "listOrgAdmins", lambda session, org_id: FakeResponse([], 403))
    client = AdminTokenHygieneClient(object(), "org-1")
    with pytest.raises(RuntimeError, match="listOrgAdmins failed with HTTP 403"):
        client.list_admins()


def test_client_raises_on_token_5xx_response(monkeypatch: Any) -> None:
    """The client must fail closed when the token list returns a 5xx status."""
    monkeypatch.setattr(mistapi, "get_all", lambda response, mist_session: response.data)
    monkeypatch.setattr(
        mistapi.api.v1.orgs.apitokens, "listOrgApiTokens", lambda session, org_id: FakeResponse([], 503)
    )
    client = AdminTokenHygieneClient(object(), "org-1")
    with pytest.raises(RuntimeError, match="listOrgApiTokens failed with HTTP 503"):
        client.list_tokens()


def test_client_returns_empty_settings_on_4xx_response(monkeypatch: Any) -> None:
    """The client must keep report generation possible when settings return a 4xx status."""
    monkeypatch.setattr(
        mistapi.api.v1.orgs.setting, "getOrgSettings", lambda session, org_id: FakeResponse({"error": "denied"}, 404)
    )
    client = AdminTokenHygieneClient(object(), "org-1")
    assert client.get_settings() == {}


def test_client_returns_empty_settings_on_5xx_response(monkeypatch: Any) -> None:
    """The client must keep report generation possible when settings return a 5xx status."""
    monkeypatch.setattr(
        mistapi.api.v1.orgs.setting, "getOrgSettings", lambda session, org_id: FakeResponse({"error": "down"}, 500)
    )
    client = AdminTokenHygieneClient(object(), "org-1")
    assert client.get_settings() == {}
