"""Unit tests for the Mist Edge lifecycle SDK client."""

from __future__ import annotations  # WHY: match package type syntax.

import logging  # WHY: caplog validates secret redaction.
from typing import Any  # WHY: fake response stores dynamic JSON.

import mistapi  # WHY: monkeypatch SDK methods used by the client.

from src.org.mxedge_lifecycle.client import MxEdgeLifecycleClient  # WHY: system under test.


class FakeResponse:
    """Small response wrapper that matches `mistapi` response shape."""

    def __init__(self, data: Any) -> None:
        """Store fake response data."""
        self.data = data  # WHY: client reads the `.data` attribute.


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
