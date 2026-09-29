"""Tests for the client fingerprint census API client."""

from __future__ import annotations  # WHY: keep test annotations consistent.

from typing import Any  # WHY: pytest monkeypatch fakes receive SDK-shaped values.

from pytest import MonkeyPatch  # WHY: replace SDK functions without network calls.

from src.reports.client_fingerprint_census import client as client_module
from src.reports.client_fingerprint_census.client import ClientFingerprintCensusClient


def test_count_uses_sdk_site_alias_and_pages_response(monkeypatch: MonkeyPatch) -> None:
    """Assert that the client calls the SDK site alias with expected arguments."""
    calls: dict[str, Any] = {}  # WHY: capture fake SDK arguments for assertions.
    fake_response = object()  # WHY: stand in for a mistapi APIResponse.
    fake_session = object()  # WHY: stand in for the authenticated Mist session.

    def fake_count(*args: Any, **kwargs: Any) -> object:
        calls["count_args"] = args  # WHY: verify positional SDK arguments.
        calls["count_kwargs"] = kwargs  # WHY: verify query parameters.
        return fake_response  # WHY: feed the paging helper.

    def fake_get_all(*args: Any, **kwargs: Any) -> list[dict[str, object]]:
        calls["get_all_args"] = args  # WHY: verify no positional paging arguments are required.
        calls["get_all_kwargs"] = kwargs  # WHY: verify response and session handoff.
        return [{"property": "Apple", "count": 7}]  # WHY: return one raw count row.

    monkeypatch.setattr(client_module.insights, "countSiteClientFingerprints", fake_count)  # WHY: no network call.
    monkeypatch.setattr(client_module.mistapi, "get_all", fake_get_all)  # WHY: no SDK pagination.
    rows = ClientFingerprintCensusClient(fake_session).count("site-1", "family")  # WHY: exercise client.

    assert calls["count_args"] == (fake_session, "site-1")  # WHY: SDK takes session and site identifier.
    assert calls["count_kwargs"] == {"distinct": "family", "limit": 100}  # WHY: count query contract.
    assert calls["get_all_kwargs"] == {"response": fake_response, "mist_session": fake_session}  # WHY: pages.
    assert rows == [{"property": "Apple", "count": 7}]  # WHY: client returns raw rows for model parsing.
