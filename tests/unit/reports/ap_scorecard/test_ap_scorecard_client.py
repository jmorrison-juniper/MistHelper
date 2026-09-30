"""Tests for the AP scorecard Mist API client."""

from __future__ import annotations

from collections.abc import Mapping
from types import SimpleNamespace

import pytest

from src.reports.ap_scorecard import client


def test_ap_scorecard_client_calls_ap_stats_with_required_parameters(monkeypatch: pytest.MonkeyPatch) -> None:
    """The client requests AP stats with the required type and limit."""
    calls: list[dict[str, object]] = []
    session = object()

    def fake_list_org_devices_stats(session: object, org_id: str, **kwargs: object) -> object:
        calls.append({"session": session, "org_id": org_id, **kwargs})
        return SimpleNamespace(status_code=200)

    monkeypatch.setattr(client.mistapi.api.v1.orgs.stats, "listOrgDevicesStats", fake_list_org_devices_stats)
    monkeypatch.setattr(client.mistapi, "get_all", lambda response, mist_session: [{"mac": "aabb"}])
    result = client.ApScorecardClient(session, "org-1").list_ap_stats()
    assert result == [{"mac": "aabb"}]
    assert calls == [{"session": session, "org_id": "org-1", "type": "ap", "limit": 1000}]


def test_ap_scorecard_client_uses_mistapi_get_all(monkeypatch: pytest.MonkeyPatch) -> None:
    """The client uses the shared mistapi pagination seam."""
    session = object()
    response = SimpleNamespace(status_code=200)
    observed: dict[str, object] = {}

    def fake_get_all(*, response: object, mist_session: object) -> list[Mapping[str, object]]:
        observed["response"] = response
        observed["mist_session"] = mist_session
        return [{"mac": "aabb"}]

    monkeypatch.setattr(client.mistapi.api.v1.orgs.stats, "listOrgDevicesStats", lambda *args, **kwargs: response)
    monkeypatch.setattr(client.mistapi, "get_all", fake_get_all)
    result = client.ApScorecardClient(session, "org-1").list_ap_stats()
    assert result == [{"mac": "aabb"}]
    assert observed == {"response": response, "mist_session": session}


@pytest.mark.parametrize("status_code", [400, 500])
def test_ap_scorecard_client_rejects_http_failures(
    monkeypatch: pytest.MonkeyPatch,
    status_code: int,
) -> None:
    """The client raises on HTTP failures instead of returning empty success."""
    monkeypatch.setattr(
        client.mistapi.api.v1.orgs.stats,
        "listOrgDevicesStats",
        lambda *args, **kwargs: SimpleNamespace(status_code=status_code),
    )
    with pytest.raises(RuntimeError, match=f"HTTP status {status_code}"):
        client.ApScorecardClient(object(), "org-1").list_ap_stats()
