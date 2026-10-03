"""Unit tests for the PSK hygiene Mist client."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from src.mist.intelligence.reports.psk_hygiene import client as client_module
from src.mist.intelligence.reports.psk_hygiene.client import DEFAULT_LIMIT


class _FakeResponse:
    """Represent an SDK response with an HTTP status code."""

    def __init__(self, status_code: int) -> None:
        """Store the fake HTTP status code."""
        self.status_code = status_code  # Let client tests exercise status-specific behavior.


def test_client_fetches_paginated_psks(monkeypatch: Any) -> None:
    """The client fetches all PSK pages through mistapi.get_all."""
    calls: list[str] = []  # Record endpoint and pagination calls.
    response = object()  # Represent the first SDK response.
    monkeypatch.setattr(
        client_module.mistapi.api.v1.orgs.psks,
        "listOrgPsks",
        lambda session, org_id, limit: calls.append(f"psks:{org_id}:{limit}") or response,
    )  # Replace the SDK PSK endpoint with a fake.
    monkeypatch.setattr(
        client_module.mistapi,
        "get_all",
        lambda response, mist_session: calls.append("get_all") or [{"name": "key"}],
    )  # Replace pagination with a deterministic fake.
    client = client_module.PskHygieneClient(SimpleNamespace(), "org-1")  # Build the read-only client.
    assert client.fetch_psks() == [{"name": "key"}]  # The client should return normalized records.
    assert calls == [f"psks:org-1:{DEFAULT_LIMIT}", "get_all"]  # The endpoint must run before pagination.


def test_client_fetches_paginated_wlans(monkeypatch: Any) -> None:
    """The client fetches all WLAN pages through mistapi.get_all."""
    calls: list[str] = []  # Record endpoint and pagination calls.
    response = object()  # Represent the first SDK response.
    monkeypatch.setattr(
        client_module.mistapi.api.v1.orgs.wlans,
        "listOrgWlans",
        lambda session, org_id, limit: calls.append(f"wlans:{org_id}:{limit}") or response,
    )  # Replace the SDK WLAN endpoint with a fake.
    monkeypatch.setattr(
        client_module.mistapi,
        "get_all",
        lambda response, mist_session: calls.append("get_all") or [{"ssid": "Facility"}],
    )  # Replace pagination with a deterministic fake.
    client = client_module.PskHygieneClient(SimpleNamespace(), "org-1")  # Build the read-only client.
    assert client.fetch_wlans() == [{"ssid": "Facility"}]  # The client should return normalized records.
    assert calls == [f"wlans:org-1:{DEFAULT_LIMIT}", "get_all"]  # The endpoint must run before pagination.


def test_client_fetches_paginated_templates(monkeypatch: Any) -> None:
    """The client fetches all template pages through mistapi.get_all."""
    calls: list[str] = []  # Record endpoint and pagination calls.
    response = object()  # Represent the first SDK response.
    monkeypatch.setattr(
        client_module.mistapi.api.v1.orgs.templates,
        "listOrgTemplates",
        lambda session, org_id, limit: calls.append(f"templates:{org_id}:{limit}") or response,
    )  # Replace the SDK template endpoint with a fake.
    monkeypatch.setattr(
        client_module.mistapi,
        "get_all",
        lambda response, mist_session: calls.append("get_all") or [{"name": "Template"}],
    )  # Replace pagination with a deterministic fake.
    client = client_module.PskHygieneClient(SimpleNamespace(), "org-1")  # Build the read-only client.
    assert client.fetch_templates() == [{"name": "Template"}]  # The client should return normalized records.
    assert calls == [f"templates:org-1:{DEFAULT_LIMIT}", "get_all"]  # The endpoint must run before pagination.


def test_client_raises_on_4xx_response_without_pagination(monkeypatch: Any) -> None:
    """The client fails explicitly when Mist returns an HTTP 4xx response."""
    response = _FakeResponse(404)  # Simulate a client-side Mist API failure.
    monkeypatch.setattr(
        client_module.mistapi.api.v1.orgs.psks,
        "listOrgPsks",
        lambda session, org_id, limit: response,
    )  # Return the failing response from the PSK endpoint.
    monkeypatch.setattr(
        client_module.mistapi,
        "get_all",
        lambda response, mist_session: pytest.fail("pagination must not run after HTTP 404"),
    )  # Prove pagination is skipped after the failure.
    client = client_module.PskHygieneClient(SimpleNamespace(), "org-1")  # Build the read-only client.
    with pytest.raises(RuntimeError, match="HTTP 404.*organization PSKs"):  # Assert the exact failure behavior.
        client.fetch_psks()  # Fetching PSKs must raise on the HTTP 404 response.


def test_client_raises_on_5xx_response_without_pagination(monkeypatch: Any) -> None:
    """The client fails explicitly when Mist returns an HTTP 5xx response."""
    response = _FakeResponse(503)  # Simulate a server-side Mist API failure.
    monkeypatch.setattr(
        client_module.mistapi.api.v1.orgs.wlans,
        "listOrgWlans",
        lambda session, org_id, limit: response,
    )  # Return the failing response from the WLAN endpoint.
    monkeypatch.setattr(
        client_module.mistapi,
        "get_all",
        lambda response, mist_session: pytest.fail("pagination must not run after HTTP 503"),
    )  # Prove pagination is skipped after the failure.
    client = client_module.PskHygieneClient(SimpleNamespace(), "org-1")  # Build the read-only client.
    with pytest.raises(RuntimeError, match="HTTP 503.*organization WLANs"):  # Assert the exact failure behavior.
        client.fetch_wlans()  # Fetching WLANs must raise on the HTTP 503 response.
