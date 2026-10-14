"""Exercise the live WAN portal using isolated stores and mocked Mist responses."""

import re
import threading
from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest
from playwright.sync_api import Page, expect
from werkzeug.serving import make_server

from src.interfaces.portals.wan_performance.collection.live_service import LiveService


@pytest.fixture
def live_service(client):
    """Inject public boundaries without creating any network connection."""
    snapshot = {
        "org_id": "org-one",
        "provenance": "live",
        "collected_at_utc": "2024-01-01T12:34:00+00:00",
        "ports": [
            {
                "org_id": "org-one",
                "site_id": "site-one",
                "mac": "aabbccddeeff",
                "port_id": "ge-0/0/0",
                "rx_bps": 40,
                "tx_bps": 80,
            }
        ],
        "peers": [
            {
                "org_id": "org-one",
                "site_id": "site-one",
                "mac": "aabbccddeeff",
                "port_id": "ge-0/0/0",
                "peer_mac": "11:22:33:44:55:66",
                "peer_site_id": "site-two",
                "peer_port_id": "ge-0/0/1",
                "type": "ipsec",
                "loss": 0,
                "latency": 10,
                "jitter": 2,
            }
        ],
        "partial": False,
    }
    store = MagicMock()
    store.cached.return_value = snapshot
    history = MagicMock()
    history.read.return_value = ()
    service = LiveService(MagicMock(), "org-one", store, history)
    old_org = client.application.config.get("ORG_ID")
    client.application.config["WAN_LIVE_SERVICE"] = service
    client.application.config["ORG_ID"] = "org-one"
    try:
        yield service
    finally:
        client.application.config.pop("WAN_LIVE_SERVICE", None)
        client.application.config["ORG_ID"] = old_org


@pytest.mark.parametrize(
    ("path", "selector"),
    [
        ("/wan-performance/live/", "wan-live-overview"),
        ("/wan-performance/live/gateway/aabbccddeeff?site_id=site-one", "wan-live-gateway"),
        ("/wan-performance/live/port/site-one/ge-0/0/0?gateway_id=aabbccddeeff", "wan-live-port"),
        ("/wan-performance/live/vpn/site-one/11:22:33:44:55:66", "wan-live-peer"),
    ],
)
def test_all_live_journeys_read_cache_without_live_calls(client, live_service, path, selector):
    """Serve all four protected journeys with explicit snapshot and stale labels."""
    response = client.get(path)
    text = response.get_data(as_text=True)
    assert response.status_code == 200
    assert f'data-testid="{selector}"' in text
    assert "Live snapshot" in text
    assert "stale" in text.lower()
    assert "full-hour" in text
    live_service.store.acquire.assert_not_called()
    live_service.session.assert_not_called()


def test_unknown_gateway_returns_not_found(client, live_service):
    """Reject arbitrary gateway and site combinations outside the cached org."""
    response = client.get("/wan-performance/live/gateway/unknown?site_id=site-one")
    assert response.status_code == 404


def test_second_gateway_refresh_keeps_selected_site_and_gateway(client, live_service):
    """The gateway journey can refresh another cached gateway rather than the first discovered device."""
    from src.interfaces.portals.wan_performance.domain.identity import GatewayIdentity, SiteIdentity

    snapshot = live_service.store.cached.return_value
    snapshot["ports"].append({**snapshot["ports"][0], "site_id": "site-two", "mac": "112233445566"})
    page = client.get("/wan-performance/live/gateway/112233445566?site_id=site-two").get_data(as_text=True)
    assert 'name="gateway_id" value="112233445566"' in page
    assert 'name="site_id" value="site-two"' in page
    token = re.findall(r'name="csrf_token" value="([^"]+)"', page)[0]
    with patch.object(live_service, "refresh", return_value=snapshot) as refresh:
        response = client.post(
            "/wan-performance/live/refresh",
            data={"csrf_token": token, "gateway_id": "112233445566", "site_id": "site-two"},
        )
    assert response.status_code == 302
    assert response.headers["Location"] == "/wan-performance/live/gateway/112233445566?site_id=site-two"
    refresh.assert_called_once_with(GatewayIdentity(SiteIdentity("org-one", "site-two"), "112233445566"))


def test_overview_can_select_a_gateway_outside_the_cached_port_page(client, live_service):
    """Use exact organization-scoped discovery for a known gateway that the capped cache does not contain."""
    from src.interfaces.portals.wan_performance.domain.identity import GatewayIdentity, SiteIdentity

    page = client.get("/wan-performance/live/").get_data(as_text=True)
    assert 'data-testid="wan-live-gateway-site"' in page
    assert 'data-testid="wan-live-gateway-mac"' in page
    token = re.findall(r'name="csrf_token" value="([^"]+)"', page)[0]
    with patch.object(live_service, "refresh", return_value={}) as refresh:
        response = client.post(
            "/wan-performance/live/refresh",
            data={"csrf_token": token, "site_id": "site-two", "gateway_id": "112233445566"},
        )
    assert response.status_code == 302
    refresh.assert_called_once_with(GatewayIdentity(SiteIdentity("org-one", "site-two"), "112233445566"))


def test_blank_gateway_selection_preserves_organization_refresh(client, live_service):
    """An untouched optional selector must not turn the normal refresh into invalid input."""
    page = client.get("/wan-performance/live/").get_data(as_text=True)
    token = re.findall(r'name="csrf_token" value="([^"]+)"', page)[0]
    with patch.object(live_service, "refresh", return_value={}) as refresh:
        response = client.post(
            "/wan-performance/live/refresh", data={"csrf_token": token, "site_id": "", "gateway_id": ""}
        )
    assert response.status_code == 302
    assert response.headers["Location"] == "/wan-performance/live/"
    refresh.assert_called_once_with(None)


def test_point_in_time_utilization_is_visible_without_duration_claims(client, live_service):
    """Show both directional percentages while keeping historical duration unknown."""
    live_service.store.cached.return_value["ports"][0].update(speed=100, rx_bps=70000000, tx_bps=80000000)
    page = client.get("/wan-performance/live/port/site-one/ge-0/0/0?gateway_id=aabbccddeeff")
    text = page.get_data(as_text=True)
    assert page.status_code == 200
    assert "rx_utilization_percent: 70.0 %" in text
    assert "tx_utilization_percent: 80.0 %" in text
    assert "point-in-time" in text
    assert "Snapshot rates do not establish duration" in text


def test_peer_current_state_and_uptime_are_distinct_from_availability(client, live_service):
    """Display verified current peer metadata without treating it as historical duration."""
    live_service.store.cached.return_value["peers"][0].update(up=True, is_active=False, uptime=0, last_seen=1704112440)
    page = client.get("/wan-performance/live/vpn/site-one/11:22:33:44:55:66")
    text = page.get_data(as_text=True)
    assert page.status_code == 200
    assert 'data-testid="wan-live-current-state"' in text
    assert "Current link state: Up" in text
    assert "Redundant path: Standby" in text
    assert "Gateway-reported uptime (s): 0" in text
    assert "Last observed (UTC): 2024-01-01T12:34:00+00:00" in text
    assert "Current status does not establish historical availability" in text


def test_missing_session_is_explicit_unavailable(client):
    """Do not create another API session or show synthetic values as live."""
    client.application.config["APISESSION"] = None
    response = client.get("/wan-performance/live/")
    assert response.status_code == 200
    assert "no configured Mist session" in response.get_data(as_text=True)


@pytest.mark.parametrize("unavailable", ["transport", "configuration"])
def test_portal_startup_with_hidden_transport_refuses_refresh(monkeypatch, caplog, unavailable):
    """Keep the portal available while refusing requests without shared admission."""
    from types import SimpleNamespace

    from requests import Session

    from src.foundation.persistence.db import DatabaseConfig
    from web_portal.app import WebPortalApp

    monkeypatch.setenv("WAN_SHARED_ADMISSION", "true")
    session = SimpleNamespace()
    if unavailable == "configuration":
        session._session = Session()
        monkeypatch.setattr(
            DatabaseConfig,
            "from_env",
            MagicMock(side_effect=ValueError("Missing required environment variable: ARANGO_USERNAME")),
        )
    app = WebPortalApp.create_app(session, {}, "org-one")
    try:
        client = app.test_client()
        page = client.get("/wan-performance/live/")
        assert page.status_code == 200
        assert "Live data is unavailable" in page.get_data(as_text=True)
        token = re.findall(r'name="csrf_token" value="([^"]+)"', page.get_data(as_text=True))[0]
        response = client.post("/wan-performance/live/refresh", data={"csrf_token": token})
        assert response.status_code == 503
        assert "WAN refresh failed" in response.get_data(as_text=True)
        assert "Configure shared Redis admission" in caplog.text
        assert client.get("/wan-performance/").status_code == 200
        assert ("SDK session transport" if unavailable == "transport" else "ARANGO_USERNAME") in caplog.text
        assert app.config["APISESSION"] is session
    finally:
        WebPortalApp.shutdown_app(app)
        if unavailable == "configuration":
            session._session.close()


def test_cache_outage_keeps_page_readable(client, live_service):
    """Show an explicit unavailable state without starting uncoordinated refresh."""
    live_service.store.cached.side_effect = ConnectionError("cache unavailable")
    response = client.get("/wan-performance/live/")
    assert response.status_code == 200
    assert "unavailable" in response.get_data(as_text=True)
    live_service.store.acquire.assert_not_called()


def test_operator_refresh_failure_is_explicit(client, live_service):
    """Report lease failures and preserve the cached state."""
    live_service.store.acquire.side_effect = ConnectionError("cooldown")
    page = client.get("/wan-performance/live/").get_data(as_text=True)
    token = re.findall(r'name="csrf_token" value="([^"]+)"', page)[0]
    response = client.post("/wan-performance/live/refresh", data={"csrf_token": token})
    assert response.status_code == 503
    assert "cooldown" in response.get_data(as_text=True)


@pytest.fixture
def live_browser_url(client, live_service) -> Iterator[str]:
    """Serve mocked live journeys within the existing test portal process."""
    server = make_server("127.0.0.1", 0, client.application, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join(timeout=10)
        server.server_close()
        if thread.is_alive():
            raise RuntimeError("The WAN live browser test server did not stop.")


@pytest.mark.parametrize("detail", ["port", "peer"])
def test_browser_live_journeys(page: Page, live_browser_url: str, detail: str):
    """Follow real overview, gateway, and detail links using mocked cached data."""
    response = page.goto(f"{live_browser_url}/wan-performance/live/")
    assert response is not None and response.status == 200
    expect(page.get_by_test_id("wan-live-overview")).to_be_visible()
    page.get_by_test_id("wan-live-gateway-link").first.click()
    expect(page.get_by_test_id("wan-live-gateway")).to_be_visible()
    page.get_by_test_id(f"wan-live-{detail}-link").first.click()
    expect(page.get_by_test_id(f"wan-live-{detail}")).to_be_visible()
    expect(page.get_by_test_id("wan-live-history")).to_contain_text("not full-hour averages")
    page.get_by_test_id("wan-live-back-link").click()
    expect(page.get_by_test_id("wan-live-overview")).to_be_visible()


def test_browser_scoped_gateway_selector(page: Page, live_browser_url: str, live_service):
    """Submit the real CSRF-protected form and retain its exact selected gateway journey."""
    from src.interfaces.portals.wan_performance.domain.identity import GatewayIdentity, SiteIdentity

    page.goto(f"{live_browser_url}/wan-performance/live/")
    page.get_by_test_id("wan-live-gateway-site").fill("site-one")
    page.get_by_test_id("wan-live-gateway-mac").fill("aabbccddeeff")
    with patch.object(live_service, "refresh", return_value={}) as refresh:
        page.get_by_test_id("wan-live-refresh").click()
        expect(page.get_by_test_id("wan-live-gateway")).to_be_visible()
    refresh.assert_called_once_with(GatewayIdentity(SiteIdentity("org-one", "site-one"), "aabbccddeeff"))


def test_refresh_requires_csrf(client, live_service):
    """Keep the existing portal's write protection active for live refresh."""
    response = client.post("/wan-performance/live/refresh")
    assert response.status_code == 400
    live_service.store.acquire.assert_not_called()


def test_history_outage_is_distinct_from_empty_history(client, live_service):
    """Do not label a storage failure as a successful empty query."""
    live_service.history.read.side_effect = ConnectionError("database unavailable")
    response = client.get("/wan-performance/live/port/site-one/ge-0/0/0?gateway_id=aabbccddeeff")
    assert response.status_code == 200
    assert "History is unavailable" in response.get_data(as_text=True)


def test_missing_history_keeps_cached_view_and_refuses_refresh(client, live_service):
    """Keep cached observations readable without claiming a successful durable write."""
    live_service.history = None
    response = client.get("/wan-performance/live/port/site-one/ge-0/0/0?gateway_id=aabbccddeeff")
    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert "History is unavailable" in text
    assert "rx_bps" in text
    token = re.findall(r'name="csrf_token" value="([^"]+)"', text)[0]
    response = client.post("/wan-performance/live/refresh", data={"csrf_token": token})
    assert response.status_code == 503
    live_service.store.acquire.assert_not_called()


def test_gateway_insights_render_as_gateway_measurements(client, live_service):
    """Keep gateway insight samples separate from invented WAN port identities."""
    snapshot = live_service.store.cached.return_value
    snapshot["insights"] = {
        "gateway": {
            "org_id": "org-one",
            "site_id": "site-one",
            "mac": "aabbccddeeff",
            "id": "00000000-0000-0000-0000-000000000001",
        },
        "samples": [
            {"metric": name, "value": value, "unit": "bit/s", "hour_start_utc": "2024-01-01T11:00:00+00:00"}
            for name, value in [("rx_bps", "0"), ("tx_bps", "10")]
        ],
    }
    response = client.get("/wan-performance/live/gateway/aabbccddeeff?site_id=site-one")
    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert 'data-testid="wan-live-gateway-insights"' in text
    assert "Gateway insight hour" in text
    assert "rx_bps: 0.0 bit/s" in text
    assert live_service.history.read.call_args.args[0].gateway_id == "aabbccddeeff"


def test_foreign_org_service_is_rejected(client, live_service):
    """Prevent an injected or stale provider from crossing the selected org boundary."""
    client.application.config["ORG_ID"] = "another-org"
    response = client.get("/wan-performance/live/")
    assert response.status_code == 200
    assert "unavailable" in response.get_data(as_text=True)
    live_service.store.cached.assert_not_called()


def test_persisted_observations_render_calendar_summaries(client, live_service):
    """Exercise actual domain summaries rather than an empty mock result."""
    from src.interfaces.portals.wan_performance.collection.snapshot_records import SnapshotRecords

    records = SnapshotRecords.build(live_service.store.cached.return_value)
    live_service.history.read.return_value = (records[0],)
    response = client.get("/wan-performance/live/port/site-one/ge-0/0/0?gateway_id=aabbccddeeff")
    assert response.status_code == 200
    assert "daily: 2024-01-01" in response.get_data(as_text=True)
    assert "mean 40.0" in response.get_data(as_text=True)
