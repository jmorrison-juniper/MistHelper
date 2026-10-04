"""Tests for the WebSocket picker service.

Why:
    Issue #3551 needs picker rows that come from Mist data, with no network
    call in the tests.
"""

from __future__ import annotations  # Keep annotations lazy for the test imports.

from types import SimpleNamespace  # Build small SDK answers for the picker tests.
from typing import Any  # Type fake SDK arguments without importing SDK types.

import mistapi  # Patch the installed SDK seams that the picker calls.

from src.mist.realtime.websocket_streams.intake.pickers.service import StreamPickerService  # The class under test.

SITE_ID = "11111111-2222-3333-4444-555555555555"  # One stable site identifier.
MAP_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"  # One stable map identifier.
ORG_ID = "99999999-8888-7777-6666-555555555555"  # One stable organization identifier.


def test_devices_include_family_and_cache(monkeypatch: Any) -> None:
    """The device picker classifies devices and reuses the short cache."""
    calls: list[str] = []  # Count SDK calls to prove that the cache is used.

    def list_devices(_session: object, **kwargs: object) -> SimpleNamespace:
        """Return one row of each device family."""
        calls.append(str(kwargs.get("type")))  # The picker must request every device type.
        rows = [
            {"id": "ap1", "name": "AP One", "type": "ap", "model": "AP45", "mac": "aabbcc000001"},
            {"id": "sw1", "name": "Switch One", "type": "switch", "model": "EX4100", "mac": "aabbcc000002"},
            {"id": "gw1", "name": "Gateway One", "type": "gateway", "model": "SRX320", "mac": "aabbcc000003"},
            {"id": "gw2", "name": "Router One", "type": "gateway", "model": "SSR120", "mac": "aabbcc000004"},
            {"id": "cam1", "name": "Camera One", "type": "camera", "model": "CAM", "mac": "aabbcc000005"},
        ]  # The five family branches.
        return SimpleNamespace(data=rows)  # Match the Mist SDK answer shape.

    monkeypatch.setattr(mistapi.api.v1.sites.devices, "listSiteDevices", list_devices)  # Replace the SDK read.
    service = StreamPickerService(object(), ORG_ID)  # Build the picker with a fake session.
    payload = service.devices(SITE_ID)  # Read the device picker once.
    second = service.describe_device(SITE_ID, "sw1")  # Read from the cache for a start check.
    families = {row["id"]: row["family"] for row in payload["rows"]}  # Index rows by identifier.
    assert calls == ["all"]  # The second read did not reach the SDK.
    assert families == {"ap1": "ap", "sw1": "ex", "gw1": "srx", "gw2": "ssr", "cam1": None}  # Families.
    assert second is not None and second.name == "Switch One" and second.family == "ex"  # Facts match the row.


def test_devices_empty_payload_has_reason(monkeypatch: Any) -> None:
    """An empty device list carries a plain reason."""

    def list_devices(_session: object, **_kwargs: object) -> SimpleNamespace:
        """Return no devices from the fake SDK."""
        return SimpleNamespace(data=[])  # The empty Mist answer.

    monkeypatch.setattr(mistapi.api.v1.sites.devices, "listSiteDevices", list_devices)  # Replace the SDK read.
    payload = StreamPickerService(object(), ORG_ID).devices(SITE_ID)  # Read the picker.
    assert payload["rows"] == []  # No rows came back.
    assert payload["total_count"] == 0  # The count matches the rows.
    assert payload["reason"] == "The site has no devices that the portal can list."  # Operator text exists.


def test_site_pickers_use_expected_sdk_functions(monkeypatch: Any) -> None:
    """The map, asset, and SDK client pickers call the expected SDK seams."""

    def list_maps(_session: object, site_id: str) -> SimpleNamespace:
        """Return one map row."""
        assert site_id == SITE_ID  # The picker forwards the site identifier.
        return SimpleNamespace(data=[{"id": MAP_ID, "name": "Floor 1", "type": "image"}])  # One map.

    def list_assets(_session: object, site_id: str) -> SimpleNamespace:
        """Return one asset row."""
        assert site_id == SITE_ID  # The picker forwards the site identifier.
        return SimpleNamespace(data=[{"id": "asset1", "name": "Badge 1", "status": "seen"}])  # One asset.

    def list_clients(_session: object, site_id: str, map_id: str) -> SimpleNamespace:
        """Return one SDK client row."""
        assert (site_id, map_id) == (SITE_ID, MAP_ID)  # The picker forwards both identifiers.
        return SimpleNamespace(data=[{"id": "client1", "hostname": "Phone 1", "mac": "aabbccddeeff"}])  # One client.

    monkeypatch.setattr(mistapi.api.v1.sites.maps, "listSiteMaps", list_maps)  # Replace map read.
    monkeypatch.setattr(mistapi.api.v1.sites.assets, "listSiteAssets", list_assets)  # Replace asset read.
    monkeypatch.setattr(mistapi.api.v1.sites.stats, "getSiteSdkStatsByMap", list_clients)  # Replace client read.
    service = StreamPickerService(object(), ORG_ID)  # Build the picker with a fake session.
    assert service.maps(SITE_ID)["rows"][0]["label"] == "Floor 1"  # Map label comes from name.
    assert service.assets(SITE_ID)["rows"][0]["label"] == "Badge 1"  # Asset label comes from name.
    assert service.sdkclients(SITE_ID, MAP_ID)["rows"][0]["label"] == "Phone 1"  # Client label comes from host.


def test_mxedges_read_site_or_org_scope(monkeypatch: Any) -> None:
    """The Mist Edge picker reads the site scope when present, else the organization."""
    calls: list[str] = []  # Record which scope the picker used.

    def list_site(_session: object, site_id: str) -> SimpleNamespace:
        """Return one site Mist Edge row."""
        calls.append("site:" + site_id)  # Record the selected scope.
        return SimpleNamespace(data=[{"id": "mx1", "name": "Edge Site", "model": "ME"}])  # One site edge.

    def list_org(_session: object, org_id: str) -> SimpleNamespace:
        """Return one organization Mist Edge row."""
        calls.append("org:" + org_id)  # Record the selected scope.
        return SimpleNamespace(data=[{"id": "mx2", "name": "Edge Org", "model": "ME"}])  # One org edge.

    monkeypatch.setattr(mistapi.api.v1.sites.mxedges, "listSiteMxEdges", list_site)  # Replace site read.
    monkeypatch.setattr(mistapi.api.v1.orgs.mxedges, "listOrgMxEdges", list_org)  # Replace org read.
    service = StreamPickerService(object(), ORG_ID)  # Build the picker with a fake session.
    assert service.mxedges(SITE_ID)["rows"][0]["id"] == "mx1"  # Site scope uses the site function.
    assert service.mxedges(None)["rows"][0]["id"] == "mx2"  # Org scope uses the org function.
    assert calls == ["site:" + SITE_ID, "org:" + ORG_ID]  # The picker chose both scopes correctly.


def test_picker_failure_returns_reason(monkeypatch: Any) -> None:
    """A picker failure returns an empty list with a reason."""

    def list_maps(_session: object, _site_id: str) -> SimpleNamespace:
        """Raise like a failed SDK request."""
        raise RuntimeError("cloud refused the read")  # The picker must catch this failure.

    monkeypatch.setattr(mistapi.api.v1.sites.maps, "listSiteMaps", list_maps)  # Replace the map read.
    payload = StreamPickerService(object(), ORG_ID).maps(SITE_ID)  # Read the picker.
    assert payload["rows"] == []  # No row leaves a failed picker.
    assert payload["reason"] == "The portal could not list this data from Mist."  # The reason is plain.
