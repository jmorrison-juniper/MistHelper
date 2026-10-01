"""Tests for the client fingerprint census API client."""

from __future__ import annotations  # WHY: keep test annotations consistent.

from types import SimpleNamespace  # WHY: create SDK-like responses with status codes.
from typing import Any  # WHY: pytest monkeypatch fakes receive SDK-shaped values.

import pytest  # WHY: assert HTTP failure behavior.
from pytest import MonkeyPatch  # WHY: replace SDK functions without network calls.

from src.reports.client_fingerprint_census import client as client_module
from src.reports.client_fingerprint_census.client import ClientFingerprintCensusClient


def test_count_uses_org_path_with_site_filter_and_pages_response(monkeypatch: MonkeyPatch) -> None:
    """Assert that the client calls the live org path with the selected site."""
    calls: dict[str, Any] = {}  # WHY: capture fake SDK arguments for assertions.
    fake_response = SimpleNamespace(status_code=200)  # WHY: stand in for a successful mistapi APIResponse.
    fake_session = SimpleNamespace()  # WHY: stand in for the authenticated Mist session.

    def fake_mist_get(path: str, query: dict[str, str]) -> object:
        calls["path"] = path  # WHY: verify the live org path.
        calls["query"] = query  # WHY: verify the site filter is sent.
        return fake_response  # WHY: feed the paging helper.

    def fake_get_all(*args: Any, **kwargs: Any) -> list[dict[str, object]]:
        calls["get_all_args"] = args  # WHY: verify no positional paging arguments are required.
        calls["get_all_kwargs"] = kwargs  # WHY: verify response and session handoff.
        return [{"family": "Phone/Tablet/Wearable", "count": 6}]  # WHY: mirror the live org payload shape.

    fake_session.mist_get = fake_mist_get  # WHY: no network call.
    monkeypatch.setattr(client_module.mistapi, "get_all", fake_get_all)  # WHY: no SDK pagination.
    rows = ClientFingerprintCensusClient(fake_session, "org-1").count("site-1", "family")  # WHY: exercise client.

    assert calls["path"] == "/api/v1/orgs/org-1/insights/fingerprints/count"  # WHY: live path must be first.
    assert calls["query"] == {"distinct": "family", "site_id": "site-1", "limit": "100"}  # WHY: query contract.
    assert calls["get_all_kwargs"] == {"response": fake_response, "mist_session": fake_session}  # WHY: pages.
    assert rows == [{"family": "Phone/Tablet/Wearable", "count": 6}]  # WHY: client preserves raw rows.


def test_count_falls_back_to_site_path_when_org_path_returns_404(monkeypatch: MonkeyPatch) -> None:
    """Assert that a missing org path falls back to the documented site path."""
    calls: dict[str, Any] = {}  # WHY: capture fake SDK arguments for assertions.
    org_response = SimpleNamespace(status_code=404)  # WHY: simulate the documented divergence case.
    site_response = SimpleNamespace(status_code=200)  # WHY: simulate a successful fallback.
    fake_session = SimpleNamespace()  # WHY: stand in for the authenticated Mist session.

    def fake_mist_get(path: str, query: dict[str, str]) -> object:
        calls["org_path"] = path  # WHY: verify the org path is tried first.
        calls["org_query"] = query  # WHY: verify the selected site remains in the filter.
        return org_response  # WHY: force the fallback branch.

    def fake_count(*args: Any, **kwargs: Any) -> object:
        calls["site_args"] = args  # WHY: verify the documented SDK path.
        calls["site_kwargs"] = kwargs  # WHY: verify the distinct query.
        return site_response  # WHY: feed the paging helper after fallback.

    def fake_get_all(*args: Any, **kwargs: Any) -> list[dict[str, object]]:
        calls["get_all_args"] = args  # WHY: verify no positional paging arguments are required.
        calls["get_all_kwargs"] = kwargs  # WHY: verify response and session handoff.
        return [{"property": "Apple", "count": 7}]  # WHY: fallback path can keep the documented payload shape.

    fake_session.mist_get = fake_mist_get  # WHY: no network call.
    monkeypatch.setattr(client_module.insights, "countSiteClientFingerprints", fake_count)  # WHY: no network call.
    monkeypatch.setattr(client_module.mistapi, "get_all", fake_get_all)  # WHY: no SDK pagination.
    rows = ClientFingerprintCensusClient(fake_session, "org-1").count("site-1", "family")  # WHY: exercise client.

    assert calls["org_path"] == "/api/v1/orgs/org-1/insights/fingerprints/count"  # WHY: org path comes first.
    assert calls["site_args"] == (fake_session, "site-1")  # WHY: fallback uses the selected site.
    assert calls["site_kwargs"] == {"distinct": "family", "limit": 100}  # WHY: keep previous SDK query.
    assert calls["get_all_kwargs"] == {"response": site_response, "mist_session": fake_session}  # WHY: pages.
    assert rows == [{"property": "Apple", "count": 7}]  # WHY: client returns fallback rows unchanged.


@pytest.mark.parametrize("status_code", [400, 404])
def test_count_rejects_http_4xx_response(monkeypatch: MonkeyPatch, status_code: int) -> None:
    """Assert that client-side HTTP failures do not become empty reports."""
    fake_response = SimpleNamespace(status_code=status_code)  # WHY: simulate a 4xx cloud response.
    fake_session = SimpleNamespace()  # WHY: stand in for the authenticated Mist session.
    get_all_called = False  # WHY: pagination must not run after an HTTP failure.

    def fake_mist_get(*_args: Any, **_kwargs: Any) -> object:
        return fake_response  # WHY: client reads the org-path status from this fake response.

    def fake_count(*_args: Any, **_kwargs: Any) -> object:
        return fake_response  # WHY: client reads the status from this fake response.

    def fake_get_all(*_args: Any, **_kwargs: Any) -> list[dict[str, object]]:
        nonlocal get_all_called  # WHY: record whether pagination incorrectly ran.
        get_all_called = True  # WHY: a failure would make this value true.
        return [{"property": "bad", "count": 1}]  # WHY: this payload must never be trusted.

    fake_session.mist_get = fake_mist_get  # WHY: no network call.
    monkeypatch.setattr(client_module.insights, "countSiteClientFingerprints", fake_count)  # WHY: no network call.
    monkeypatch.setattr(client_module.mistapi, "get_all", fake_get_all)  # WHY: no SDK pagination.
    with pytest.raises(RuntimeError, match=f"HTTP {status_code}"):  # WHY: caller must see the HTTP failure.
        ClientFingerprintCensusClient(fake_session, "org-1").count("site-1", "family")  # WHY: exercise gate.
    assert get_all_called is False  # WHY: HTTP 4xx responses must not be paginated or exported.


@pytest.mark.parametrize("status_code", [500, 503])
def test_count_rejects_http_5xx_response(monkeypatch: MonkeyPatch, status_code: int) -> None:
    """Assert that server HTTP failures do not become empty reports."""
    fake_response = SimpleNamespace(status_code=status_code)  # WHY: simulate a 5xx cloud response.
    fake_session = SimpleNamespace()  # WHY: stand in for the authenticated Mist session.
    get_all_called = False  # WHY: pagination must not run after a server failure.

    def fake_mist_get(*_args: Any, **_kwargs: Any) -> object:
        return fake_response  # WHY: client reads the org-path status from this fake response.

    def fake_count(*_args: Any, **_kwargs: Any) -> object:
        return fake_response  # WHY: client reads the status from this fake response.

    def fake_get_all(*_args: Any, **_kwargs: Any) -> list[dict[str, object]]:
        nonlocal get_all_called  # WHY: record whether pagination incorrectly ran.
        get_all_called = True  # WHY: a failure would make this value true.
        return [{"property": "bad", "count": 1}]  # WHY: this payload must never be trusted.

    fake_session.mist_get = fake_mist_get  # WHY: no network call.
    monkeypatch.setattr(client_module.insights, "countSiteClientFingerprints", fake_count)  # WHY: no network call.
    monkeypatch.setattr(client_module.mistapi, "get_all", fake_get_all)  # WHY: no SDK pagination.
    with pytest.raises(RuntimeError, match=f"HTTP {status_code}"):  # WHY: caller must see the HTTP failure.
        ClientFingerprintCensusClient(fake_session, "org-1").count("site-1", "family")  # WHY: exercise gate.
    assert get_all_called is False  # WHY: HTTP 5xx responses must not be paginated or exported.
