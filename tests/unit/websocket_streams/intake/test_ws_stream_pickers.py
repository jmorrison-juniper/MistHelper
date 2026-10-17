"""Tests for the WebSocket picker service.

Why:
    Issue #3551 needs picker rows that come from Mist data, with no network
    call in the tests.
"""

from __future__ import annotations  # Keep annotations lazy for the test imports.

from types import SimpleNamespace  # Build small SDK answers for the picker tests.
from typing import Any  # Type fake SDK arguments without importing SDK types.

import mistapi  # Patch the installed SDK seams that the picker calls.
import pytest  # Verify that failed discovery does not look like an empty list.

import src.foundation.runtime.config.runtime_settings as runtime_settings  # Use the live page-limit setting.
from src.mist.realtime.websocket_streams.intake.fields.error import StreamRequestError  # Check picker refusals.
from src.mist.realtime.websocket_streams.intake.pickers.service import StreamPickerService  # The class under test.

SITE_ID = "11111111-2222-3333-4444-555555555555"  # One stable site identifier.
MAP_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"  # One stable map identifier.
ORG_ID = "99999999-8888-7777-6666-555555555555"  # One stable organization identifier.


def test_devices_include_family_and_cache(monkeypatch: Any) -> None:
    """The device picker classifies devices and reuses the short cache."""
    calls: list[dict[str, object]] = []  # Record SDK arguments and prove that the cache is used.
    session = object()  # Keep the authenticated session identity for the cursor request.
    monkeypatch.setattr(runtime_settings, "DEFAULT_API_PAGE_LIMIT", 250)  # Prove the configured limit is dynamic.
    rows = [
        {"id": "ap1", "name": "AP One", "type": "ap", "model": "AP45", "mac": "aabbcc000001"},
        {"id": "sw1", "name": "Switch One", "type": "switch", "model": "EX4100", "mac": "aabbcc000002"},
        {"id": "gw1", "name": "Gateway One", "type": "gateway", "model": "SRX320", "mac": "aabbcc000003"},
        {"id": "gw2", "name": "Router One", "type": "gateway", "model": "SSR120", "mac": "aabbcc000004"},
        {"id": "cam1", "name": "Camera One", "type": "camera", "model": "CAM", "mac": "aabbcc000005"},
    ]  # Keep target facts stable across both pages.

    def list_devices(_session: object, **kwargs: object) -> SimpleNamespace:
        """Return one row of each device family."""
        calls.append(dict(kwargs))  # The picker must request every device type at the configured limit.
        return SimpleNamespace(status_code=200, data=rows[:2], next="/devices?page=2")  # Return the first page.

    monkeypatch.setattr(mistapi.api.v1.sites.devices, "listSiteDevices", list_devices)  # Replace the SDK read.
    second_page = SimpleNamespace(status_code=200, data=rows[2:], next=None)  # Keep later-page rows intact.
    client_second = SimpleNamespace(
        status_code=200,
        data={
            "results": [
                {"site_id": SITE_ID, "mac": "aabbccdde002", "hostname": "Client Two", "device_mac": ["aabbcc000002"]}
            ]
        },
        next=None,
    )  # Keep the later wired-client page scoped to the selected switch.
    pages = {"/devices?page=2": second_page, "/clients?page=2": client_second}  # Bind each SDK cursor to one page.
    next_calls: list[str] = []  # Prove that every later page uses the configured session.

    def get_next(mist_session: object, response: object) -> SimpleNamespace:
        """Return one page for the server-provided cursor."""
        assert mist_session is session  # The reader must reuse the authenticated session.
        cursor = str(getattr(response, "next", ""))  # Read only the SDK cursor.
        next_calls.append(cursor)  # Record the cursor without logging it.
        return pages[cursor]  # Return the complete offline page.

    def search_clients(
        _session: object, site_id: str, device_mac: str | None = None, limit: int | None = None
    ) -> SimpleNamespace:
        """Return the first verified wired-client page."""
        assert (site_id, device_mac, limit) == (SITE_ID, "aabbcc000002", 250)  # Check scope and page size.
        client = {
            "site_id": SITE_ID,
            "mac": "aabbccdde001",
            "hostname": "Client One",
            "device_mac": ["aabbcc000002"],
        }  # Prove the switch association.
        return SimpleNamespace(
            status_code=200, data={"results": [client], "next": "/clients?page=2"}, next="/clients?page=2"
        )  # Return one result page and its cursor.

    monkeypatch.setattr(mistapi, "get_next", get_next)  # Follow authenticated SDK cursors.
    monkeypatch.setattr(
        mistapi.api.v1.sites.wired_clients, "searchSiteWiredClients", search_clients
    )  # Replace the selected-switch lookup.
    service = StreamPickerService(session, ORG_ID)  # Build the picker with a fake authenticated session.
    payload = service.devices(SITE_ID)  # Read the device picker once.
    second = service.describe_device(SITE_ID, "sw1")  # Read from the cache for a start check.
    families = {row["id"]: row["family"] for row in payload["rows"]}  # Index rows by identifier.
    assert calls == [{"site_id": SITE_ID, "type": "all", "limit": 250}]  # Verify every required SDK argument.
    assert families == {"ap1": "ap", "sw1": "ex", "gw1": "srx", "gw2": "ssr", "cam1": None}  # Families.
    assert second is not None and second.name == "Switch One" and second.family == "ex"  # Facts match the row.
    clients = service.clients(SITE_ID, "sw1")  # Read client suggestions through both pages.
    assert {row["id"] for row in clients["rows"]} == {"aabbccdde001", "aabbccdde002"}  # Preserve both clients.
    assert next_calls == ["/devices?page=2", "/clients?page=2"]  # Keep cursor order and authenticated use.


def test_devices_empty_payload_has_reason(monkeypatch: Any) -> None:
    """An empty device list carries a plain reason."""
    calls = 0  # Prove that complete empty lists use the short device cache.

    def list_devices(_session: object, **_kwargs: object) -> SimpleNamespace:
        """Return no devices from the fake SDK."""
        nonlocal calls  # Keep the fake call count local to this test.
        calls += 1  # Count the authenticated page request.
        return SimpleNamespace(status_code=200, data=[], next=None)  # The complete empty Mist answer.

    monkeypatch.setattr(mistapi.api.v1.sites.devices, "listSiteDevices", list_devices)  # Replace the SDK read.
    service = StreamPickerService(object(), ORG_ID)  # Build the picker with a fake session.
    payload = service.devices(SITE_ID)  # Read the picker.
    service.devices(SITE_ID)  # Read the complete empty cache entry again.
    assert payload["rows"] == []  # No rows came back.
    assert payload["total_count"] == 0  # The count matches the rows.
    assert payload["reason"] == "The site has no devices that the portal can list."  # Operator text exists.
    assert calls == 1  # A complete empty list is cached rather than fetched again.


def test_site_pickers_use_expected_sdk_functions(monkeypatch: Any) -> None:
    """The map, asset, and SDK client pickers call the expected SDK seams."""

    session = object()  # Keep the same authenticated session for later pages.
    pages = {
        "/maps?page=2": SimpleNamespace(status_code=200, data=[{"id": "map2", "name": "Floor 2"}], next=None),
        "/assets?page=2": SimpleNamespace(status_code=200, data=[{"id": "asset2", "name": "Badge 2"}], next=None),
        "/clients?page=2": SimpleNamespace(
            status_code=200, data={"sdkclients": [{"id": "client2", "hostname": "Phone 2"}]}, next=None
        ),
    }  # Preserve distinct natural identities for each resource page.

    def get_next(mist_session: object, response: object) -> SimpleNamespace:
        """Return the page registered for one SDK cursor."""
        assert mist_session is session  # Later pages must use the same authenticated session.
        return pages[str(getattr(response, "next", ""))]  # Resolve only the server-provided cursor.

    def list_maps(_session: object, site_id: str, limit: int | None = None) -> SimpleNamespace:
        """Return one map row."""
        assert site_id == SITE_ID  # The picker forwards the site identifier.
        assert limit == runtime_settings.DEFAULT_API_PAGE_LIMIT  # The map request uses the configured limit.
        return SimpleNamespace(
            status_code=200, data=[{"id": MAP_ID, "name": "Floor 1", "type": "image"}], next="/maps?page=2"
        )  # Return the first map page.

    def list_assets(_session: object, site_id: str, limit: int | None = None) -> SimpleNamespace:
        """Return one asset row."""
        assert site_id == SITE_ID  # The picker forwards the site identifier.
        assert limit == runtime_settings.DEFAULT_API_PAGE_LIMIT  # The asset request uses the configured limit.
        return SimpleNamespace(
            status_code=200, data=[{"id": "asset1", "name": "Badge 1", "status": "seen"}], next="/assets?page=2"
        )  # Return the first asset page.

    def list_clients(_session: object, site_id: str, map_id: str) -> SimpleNamespace:
        """Return one SDK client row."""
        assert (site_id, map_id) == (SITE_ID, MAP_ID)  # The picker forwards both identifiers.
        return SimpleNamespace(
            status_code=200,
            data={"sdkclients": [{"id": "client1", "hostname": "Phone 1", "mac": "aabbccddeeff"}]},
            next="/clients?page=2",
        )  # Return the first SDK client page.

    monkeypatch.setattr(mistapi.api.v1.sites.maps, "listSiteMaps", list_maps)  # Replace map read.
    monkeypatch.setattr(mistapi.api.v1.sites.assets, "listSiteAssets", list_assets)  # Replace asset read.
    monkeypatch.setattr(mistapi.api.v1.sites.stats, "getSiteSdkStatsByMap", list_clients)  # Replace client read.
    monkeypatch.setattr(mistapi, "get_next", get_next)  # Follow all resource cursors through the SDK.
    service = StreamPickerService(session, ORG_ID)  # Build the picker with a fake authenticated session.
    assert [row["label"] for row in service.maps(SITE_ID)["rows"]] == ["Floor 1", "Floor 2"]  # Read both maps.
    assert [row["label"] for row in service.assets(SITE_ID)["rows"]] == ["Badge 1", "Badge 2"]  # Read both assets.
    assert [row["label"] for row in service.sdkclients(SITE_ID, MAP_ID)["rows"]] == [
        "Phone 1",
        "Phone 2",
    ]  # Read both SDK client pages.


def test_mxedges_read_site_or_org_scope(monkeypatch: Any) -> None:
    """The Mist Edge picker reads the site scope when present, else the organization."""
    calls: list[str] = []  # Record which scope the picker used.
    session = object()  # Reuse the same authenticated session for organization pages.
    pages = {  # Keep each SDK cursor tied to its expected resource page.
        "/sites?page=2": SimpleNamespace(status_code=200, data=[{"id": "site2", "name": "Site Two"}], next=None),
        "/site-edges?page=2": SimpleNamespace(
            status_code=200, data=[{"id": "mx1b", "name": "Edge Site Two", "model": "ME"}], next=None
        ),
        "/org-edges?page=2": SimpleNamespace(
            status_code=200, data=[{"id": "mx2b", "name": "Edge Org Two", "model": "ME"}], next=None
        ),
    }

    def list_sites(_session: object, org_id: str, limit: int | None = None) -> SimpleNamespace:
        """Return the first organization site page."""
        calls.append("sites:" + org_id)  # Record the configured organization scope.
        assert (org_id, limit) == (ORG_ID, runtime_settings.DEFAULT_API_PAGE_LIMIT)  # Verify SDK scope and limit.
        return SimpleNamespace(
            status_code=200, data=[{"id": SITE_ID, "name": "Site One"}], next="/sites?page=2"
        )  # Return the first page and cursor.

    def list_site(_session: object, site_id: str, limit: int | None = None) -> SimpleNamespace:
        """Return one site Mist Edge row."""
        calls.append("site:" + site_id)  # Record the selected scope.
        assert limit == runtime_settings.DEFAULT_API_PAGE_LIMIT  # The site request uses the configured limit.
        return SimpleNamespace(
            status_code=200, data=[{"id": "mx1", "name": "Edge Site", "model": "ME"}], next="/site-edges?page=2"
        )  # Return the first site edge page.

    def list_org(_session: object, org_id: str, limit: int | None = None) -> SimpleNamespace:
        """Return one organization Mist Edge row."""
        calls.append("org:" + org_id)  # Record the selected scope.
        assert limit == runtime_settings.DEFAULT_API_PAGE_LIMIT  # The organization request uses the configured limit.
        return SimpleNamespace(
            status_code=200, data=[{"id": "mx2", "name": "Edge Org", "model": "ME"}], next="/org-edges?page=2"
        )  # Return the first organization edge page.

    def get_next(mist_session: object, response: object) -> SimpleNamespace:
        """Return the page registered for one SDK cursor."""
        assert mist_session is session  # The later page must use the authenticated session.
        return pages[str(getattr(response, "next", ""))]  # Resolve only the server-provided cursor.

    monkeypatch.setattr(mistapi.api.v1.orgs.sites, "listOrgSites", list_sites)  # Replace organization site discovery.
    monkeypatch.setattr(mistapi.api.v1.sites.mxedges, "listSiteMxEdges", list_site)  # Replace site read.
    monkeypatch.setattr(mistapi.api.v1.orgs.mxedges, "listOrgMxEdges", list_org)  # Replace org read.
    monkeypatch.setattr(mistapi, "get_next", get_next)  # Follow the organization site cursor through the SDK.
    service = StreamPickerService(session, ORG_ID)  # Build the picker with a fake authenticated session.
    sites = service.sites()  # Read every site in the configured organization.
    assert {row["id"] for row in service.mxedges(SITE_ID)["rows"]} == {"mx1", "mx1b"}  # Read both site edges.
    assert {row["id"] for row in service.mxedges(None)["rows"]} == {"mx2", "mx2b"}  # Read both organization edges.
    assert {row["id"] for row in sites["rows"]} == {SITE_ID, "site2"}  # Preserve both site natural keys.
    assert calls == ["sites:" + ORG_ID, "site:" + SITE_ID, "org:" + ORG_ID]  # Preserve all verified scopes.


def test_picker_failure_returns_reason(monkeypatch: Any) -> None:
    """A denied or incomplete page raises an error instead of returning an empty list."""

    def denied_maps(_session: object, site_id: str, **_kwargs: object) -> SimpleNamespace:
        """Return a denied initial page."""
        assert site_id == SITE_ID  # Keep the test inside the selected site.
        return SimpleNamespace(status_code=403, data={"error": "denied"})  # The picker must not hide access refusal.

    monkeypatch.setattr(mistapi.api.v1.sites.maps, "listSiteMaps", denied_maps)  # Replace the map read.
    with pytest.raises(StreamRequestError) as denied:  # Keep failed discovery separate from an empty result.
        StreamPickerService(object(), ORG_ID).maps(SITE_ID)  # Read the denied picker.
    assert denied.value.code == "picker_request_failed"  # Preserve the stable access error.

    def first_maps(_session: object, site_id: str, **_kwargs: object) -> SimpleNamespace:
        """Return a valid first page with a later cursor."""
        assert site_id == SITE_ID  # Keep the test inside the selected site.
        return SimpleNamespace(status_code=200, data=[], next="/maps?page=2")  # Require the later response.

    monkeypatch.setattr(mistapi.api.v1.sites.maps, "listSiteMaps", first_maps)  # Replace the initial map page.
    monkeypatch.setattr(
        mistapi, "get_next", lambda **_kwargs: SimpleNamespace(status_code=503, data=[])
    )  # Simulate a failed later page.
    with pytest.raises(StreamRequestError) as later:  # Do not accept a partial page set.
        StreamPickerService(object(), ORG_ID).maps(SITE_ID)  # Read both pages.
    assert later.value.code == "picker_service_failed"  # Preserve the later service failure.
