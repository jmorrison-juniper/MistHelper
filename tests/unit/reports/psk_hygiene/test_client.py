"""Unit tests for the PSK hygiene Mist client."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from src.reports.psk_hygiene import client as client_module


def test_client_fetches_paginated_psks(monkeypatch: Any) -> None:
    """The client fetches all PSK pages through mistapi.get_all."""
    calls: list[str] = []  # Record endpoint and pagination calls.
    response = object()  # Represent the first SDK response.
    monkeypatch.setattr(
        client_module.mistapi.api.v1.orgs.psks,
        "listOrgPsks",
        lambda session, org_id: calls.append(f"psks:{org_id}") or response,
    )  # Replace the SDK PSK endpoint with a fake.
    monkeypatch.setattr(
        client_module.mistapi,
        "get_all",
        lambda response, mist_session: calls.append("get_all") or [{"name": "key"}],
    )  # Replace pagination with a deterministic fake.
    client = client_module.PskHygieneClient(SimpleNamespace(), "org-1")  # Build the read-only client.
    assert client.fetch_psks() == [{"name": "key"}]  # The client should return normalized records.
    assert calls == ["psks:org-1", "get_all"]  # The endpoint must run before pagination.


def test_client_fetches_paginated_wlans(monkeypatch: Any) -> None:
    """The client fetches all WLAN pages through mistapi.get_all."""
    calls: list[str] = []  # Record endpoint and pagination calls.
    response = object()  # Represent the first SDK response.
    monkeypatch.setattr(
        client_module.mistapi.api.v1.orgs.wlans,
        "listOrgWlans",
        lambda session, org_id: calls.append(f"wlans:{org_id}") or response,
    )  # Replace the SDK WLAN endpoint with a fake.
    monkeypatch.setattr(
        client_module.mistapi,
        "get_all",
        lambda response, mist_session: calls.append("get_all") or [{"ssid": "Facility"}],
    )  # Replace pagination with a deterministic fake.
    client = client_module.PskHygieneClient(SimpleNamespace(), "org-1")  # Build the read-only client.
    assert client.fetch_wlans() == [{"ssid": "Facility"}]  # The client should return normalized records.
    assert calls == ["wlans:org-1", "get_all"]  # The endpoint must run before pagination.


def test_client_fetches_paginated_templates(monkeypatch: Any) -> None:
    """The client fetches all template pages through mistapi.get_all."""
    calls: list[str] = []  # Record endpoint and pagination calls.
    response = object()  # Represent the first SDK response.
    monkeypatch.setattr(
        client_module.mistapi.api.v1.orgs.templates,
        "listOrgTemplates",
        lambda session, org_id: calls.append(f"templates:{org_id}") or response,
    )  # Replace the SDK template endpoint with a fake.
    monkeypatch.setattr(
        client_module.mistapi,
        "get_all",
        lambda response, mist_session: calls.append("get_all") or [{"name": "Template"}],
    )  # Replace pagination with a deterministic fake.
    client = client_module.PskHygieneClient(SimpleNamespace(), "org-1")  # Build the read-only client.
    assert client.fetch_templates() == [{"name": "Template"}]  # The client should return normalized records.
    assert calls == ["templates:org-1", "get_all"]  # The endpoint must run before pagination.
