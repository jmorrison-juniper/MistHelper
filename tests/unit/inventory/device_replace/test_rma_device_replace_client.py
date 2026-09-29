"""Unit tests for the RMA device replacement client."""

from __future__ import annotations  # WHY: keep annotations consistent with source modules.

from dataclasses import dataclass  # WHY: fake responses need simple data and status fields.
from typing import Any  # WHY: fake SDK calls store arbitrary body payloads.

import mistapi  # WHY: monkeypatch the same SDK functions that the client calls.

from src.inventory.device_replace.client import DeviceReplaceClient  # WHY: test the API seam.
from src.inventory.device_replace.models import InventoryDevice, ReplaceRequest  # WHY: build typed inputs.


@dataclass(slots=True)
class FakeResponse:
    """Small fake for a mistapi response."""

    data: Any  # WHY: the client reads response data dynamically.
    status_code: int = 200  # WHY: replacement returns a status summary.


def test_list_inventory_normalizes_rows(monkeypatch: Any) -> None:
    """Inventory reads return normalized devices."""
    response = FakeResponse([{"id": "one", "mac": "AA:BB", "type": "ap"}])  # WHY: fake first page.
    monkeypatch.setattr(mistapi.api.v1.orgs.inventory, "getOrgInventory", lambda *args, **kwargs: response)  # WHY.
    monkeypatch.setattr(mistapi, "get_all", lambda response, mist_session: response.data)  # WHY: avoid paging.
    devices = DeviceReplaceClient(object(), "org-1").list_inventory()  # WHY: exercise client normalization.
    assert devices[0].mac == "aabb"  # WHY: MAC normalization is required for selectors and request body.


def test_replace_device_sends_request_body(monkeypatch: Any) -> None:
    """Replacement sends the OpenAPI body to the SDK."""
    sent: dict[str, Any] = {}  # WHY: capture call arguments for assertions.

    def fake_replace(session: Any, org_id: str, body: dict[str, object]) -> FakeResponse:
        sent.update({"session": session, "org_id": org_id, "body": body})  # WHY: record SDK arguments.
        return FakeResponse({"message": "ok"})  # WHY: client returns response data.

    monkeypatch.setattr(mistapi.api.v1.orgs.inventory, "replaceOrgDevices", fake_replace)  # WHY: no network call.
    request = ReplaceRequest(site_id="site", mac="old", inventory_mac="new")  # WHY: typed request input.
    result = DeviceReplaceClient("session", "org-1").replace_device(request)  # WHY: exercise send path.
    assert sent["body"] == {"site_id": "site", "mac": "old", "inventory_mac": "new", "discard": []}
    assert result == {"message": "ok"}


def test_get_old_configuration_reads_site_device(monkeypatch: Any) -> None:
    """Backup reads call the site device SDK function."""
    sent: dict[str, Any] = {}  # WHY: capture site and device IDs.

    def fake_get(session: Any, site_id: str, device_id: str) -> FakeResponse:
        sent.update({"site_id": site_id, "device_id": device_id})  # WHY: record SDK arguments.
        return FakeResponse({"name": "old"})  # WHY: fake device configuration.

    monkeypatch.setattr(mistapi.api.v1.sites.devices, "getSiteDevice", fake_get)  # WHY: no network call.
    old_device = InventoryDevice.from_row({"id": "dev", "mac": "aa", "site_id": "site", "type": "ap"})  # WHY.
    data = DeviceReplaceClient("session", "org-1").get_old_configuration(old_device)  # WHY: exercise read path.
    assert sent == {"site_id": "site", "device_id": "dev"}
    assert data == {"name": "old"}
