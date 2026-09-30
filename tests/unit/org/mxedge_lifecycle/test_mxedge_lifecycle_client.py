"""Unit tests for the Mist Edge lifecycle SDK client."""

from __future__ import annotations  # WHY: match package type syntax.

import logging  # WHY: caplog validates secret redaction.
from typing import Any  # WHY: fake response stores dynamic JSON.

import mistapi  # WHY: monkeypatch SDK methods used by the client.
import pytest  # WHY: failure-mode tests assert raised client errors.

from src.org.mxedge_lifecycle.client import (  # WHY: system under test and error contract.
    MxEdgeLifecycleApiError,
    MxEdgeLifecycleClient,
)


class FakeResponse:
    """Small response wrapper that matches `mistapi` response shape."""

    def __init__(self, data: Any, status_code: int = 200) -> None:
        """Store fake response data and HTTP status."""
        self.data = data  # WHY: client reads the `.data` attribute.
        self.status_code = status_code  # WHY: client checks HTTP failure modes before normalization.


def test_mxedge_lifecycle_client_claim_does_not_log_claim_code(monkeypatch: Any, caplog: Any) -> None:
    """The claim code must not appear in client logs."""
    secret = "135-546-673"  # WHY: secret value must stay out of log text.

    def fake_claim(session: object, org_id: str, body: dict[str, Any]) -> FakeResponse:
        """Return a successful fake claim response."""
        assert body == {"code": secret}  # WHY: client must still send the code to Mist.
        return FakeResponse({"status": "ok"})  # WHY: successful response shape.

    monkeypatch.setattr(mistapi.api.v1.orgs.mxedges, "claimOrgMxEdge", fake_claim)  # WHY: block network calls.
    caplog.set_level(logging.DEBUG)  # WHY: inspect info and debug logs.
    result = MxEdgeLifecycleClient(object(), "org-1").claim({"code": secret})  # WHY: run the client path.
    assert result == {"status": "ok"}  # WHY: response normalization keeps data.
    assert secret not in caplog.text  # WHY: acceptance criterion forbids claim code in logs.


def test_mxedge_lifecycle_client_methods_call_expected_sdk_functions(monkeypatch: Any) -> None:
    """Client methods must call the SDK function for each operation."""
    calls: list[str] = []  # WHY: record SDK paths without network.

    def fake_response(name: str) -> FakeResponse:
        """Return a fake response and record the call name."""
        calls.append(name)  # WHY: prove the expected SDK function ran.
        return FakeResponse({"status": name})  # WHY: client normalizes this dict.

    monkeypatch.setattr(mistapi.api.v1.orgs.mxedges, "assignOrgMxEdgeToSite", lambda *args: fake_response("assign"))
    monkeypatch.setattr(
        mistapi.api.v1.orgs.mxedges, "unassignOrgMxEdgeFromSite", lambda *args: fake_response("unassign")
    )
    monkeypatch.setattr(mistapi.api.v1.orgs.mxedges, "bounceOrgMxEdgeDataPorts", lambda *args: fake_response("bounce"))
    monkeypatch.setattr(mistapi.api.v1.orgs.mxedges, "upgradeOrgMxEdges", lambda *args: fake_response("upgrade"))
    monkeypatch.setattr(mistapi.api.v1.orgs.mxedges, "getOrgMxEdgeUpgrade", lambda *args: fake_response("get"))
    client = MxEdgeLifecycleClient(object(), "org-1")  # WHY: fake session avoids network.
    assert client.assign({"mxedge_ids": ["mx-1"], "site_id": "site-1"})["status"] == "assign"
    assert client.unassign({"mxedge_ids": ["mx-1"]})["status"] == "unassign"
    assert client.bounce("mx-1", {"ports": ["0"]})["status"] == "bounce"
    assert client.upgrade({"mxedge_ids": ["mx-1"]})["status"] == "upgrade"
    assert client.get_upgrade("upgrade-1")["status"] == "get"
    assert calls == ["assign", "unassign", "bounce", "upgrade", "get"]  # WHY: all operation SDK paths ran.


def test_mxedge_lifecycle_client_raises_for_http_4xx(monkeypatch: Any) -> None:
    """A 4xx response must raise an API error with the status code."""

    def fake_assign(session: object, org_id: str, body: dict[str, Any]) -> FakeResponse:
        """Return a fake authorization failure."""
        return FakeResponse({"message": "forbidden"}, status_code=403)  # WHY: simulate a Mist client error.

    monkeypatch.setattr(mistapi.api.v1.orgs.mxedges, "assignOrgMxEdgeToSite", fake_assign)  # WHY: block network.
    client = MxEdgeLifecycleClient(object(), "org-1")  # WHY: fake session avoids network.
    with pytest.raises(MxEdgeLifecycleApiError) as error_info:  # WHY: 4xx must not look successful.
        client.assign({"mxedge_ids": ["mx-1"], "site_id": "site-1"})  # WHY: exercise API client path.
    assert error_info.value.status_code == 403  # WHY: caller can identify client-side HTTP failure.
    assert "forbidden" in str(error_info.value)  # WHY: safe API message reaches the operator.


def test_mxedge_lifecycle_client_raises_for_http_5xx(monkeypatch: Any) -> None:
    """A 5xx response must raise an API error with the status code."""

    def fake_list_upgrades(session: object, org_id: str) -> FakeResponse:
        """Return a fake service failure."""
        return FakeResponse({"error": "service unavailable"}, status_code=503)  # WHY: simulate a Mist server error.

    monkeypatch.setattr(mistapi.api.v1.orgs.mxedges, "listOrgMxEdgeUpgrades", fake_list_upgrades)  # WHY: no network.
    client = MxEdgeLifecycleClient(object(), "org-1")  # WHY: fake session avoids network.
    with pytest.raises(MxEdgeLifecycleApiError) as error_info:  # WHY: 5xx must not return an empty list.
        client.list_upgrades()  # WHY: exercise list response path.
    assert error_info.value.status_code == 503  # WHY: caller can identify server-side HTTP failure.
    assert "service unavailable" in str(error_info.value)  # WHY: safe API message reaches the operator.


def test_mxedge_lifecycle_client_list_upgrades_accepts_results_wrapper(monkeypatch: Any) -> None:
    """The list client must read a wrapped `results` list."""

    def fake_list_upgrades(session: object, org_id: str) -> FakeResponse:
        """Return a wrapped list response."""
        return FakeResponse({"results": [{"id": "upgrade-1"}, "ignored"]})  # WHY: mixed rows test filtering.

    monkeypatch.setattr(mistapi.api.v1.orgs.mxedges, "listOrgMxEdgeUpgrades", fake_list_upgrades)
    rows = MxEdgeLifecycleClient(object(), "org-1").list_upgrades()  # WHY: exercise `_rows` wrapper path.
    assert rows == [{"id": "upgrade-1"}]  # WHY: only dictionary rows are kept.


def test_mxedge_lifecycle_client_preserves_non_dict_response(monkeypatch: Any) -> None:
    """The client must preserve accepted non-dictionary response data."""

    def fake_bounce(session: object, org_id: str, mxedge_id: str, body: dict[str, Any]) -> FakeResponse:
        """Return a non-dictionary accepted response."""
        return FakeResponse(["accepted"])  # WHY: exercise `_data` fallback path.

    monkeypatch.setattr(mistapi.api.v1.orgs.mxedges, "bounceOrgMxEdgeDataPorts", fake_bounce)
    result = MxEdgeLifecycleClient(object(), "org-1").bounce("mx-1", {"ports": ["0"]})
    assert result == {"data": ["accepted"]}  # WHY: non-dict data stays available to callers.


def test_mxedge_lifecycle_client_status_field_http_error() -> None:
    """The HTTP error checker must also read the `status` field."""
    response = type("Response", (), {"status": 500, "data": "failed"})()  # WHY: SDK variants can use status.
    with pytest.raises(MxEdgeLifecycleApiError) as error_info:
        MxEdgeLifecycleClient._data(response)  # WHY: exercise the status-field failure path.
    assert error_info.value.status_code == 500  # WHY: status field becomes the API error code.
