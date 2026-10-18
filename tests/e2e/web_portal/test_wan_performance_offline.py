"""Verify the WAN Performance pages with isolated synthetic fixtures."""

import logging
import re
import threading
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path

import pytest
from flask.testing import FlaskClient
from playwright.sync_api import Page, expect
from werkzeug.serving import make_server

from src.interfaces.portals.wan_performance.presentation.offline_preview import OfflinePreviewFactory

logger = logging.getLogger(__name__)  # Keep route test records on the module logger.
SITE_ID = "11111111-1111-1111-1111-111111111111"
GATEWAY_ID = "aabbccddeeff"


@pytest.fixture
def preview_client(
    client: FlaskClient,
) -> FlaskClient:
    """Return the portal client for its labeled offline preview."""
    return client


@pytest.fixture
def wan_browser_portal(client: FlaskClient) -> Iterator[str]:
    """Serve the existing test portal without a Mist session or another service."""
    server = make_server("127.0.0.1", 0, client.application, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    logger.info("Starting the offline WAN browser server on port %d", server.server_port)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        logger.info("Stopping the offline WAN browser server on port %d", server.server_port)
        server.shutdown()
        thread.join(timeout=10)
        server.server_close()
        if thread.is_alive():
            raise RuntimeError("The offline WAN browser server did not stop.")
        logger.debug("The offline WAN browser server stopped")


def _assert_preview_layout(page: Page, view: str) -> None:
    """Check that each synthetic route keeps its screenshot page structure."""
    selectors = {
        "wan-overview": ("wan-overview-kpis", "wan-overview-tables", "wan-overview-charts"),
        "wan-gateway": ("wan-gateway-kpis", "wan-gateway-tables", "wan-gateway-charts"),
        "wan-port": (
            "wan-port-kpis",
            "wan-port-gauges",
            "wan-port-current-statistics",
            "wan-port-configuration",
            "wan-port-charts",
            "wan-port-packet-statistics",
            "wan-port-error-counters",
        ),
        "wan-peer": (
            "wan-peer-kpis",
            "wan-peer-gauges",
            "wan-peer-charts",
            "wan-peer-details",
            "wan-peer-statistics",
        ),
    }
    expect(page.get_by_test_id(view)).to_be_visible()
    expect(page.get_by_test_id("wan-data-state")).to_contain_text("Synthetic offline preview")
    for selector in selectors[view]:
        expect(page.get_by_test_id(selector)).to_be_visible()


def _assert_detail_metrics(page: Page, detail: str) -> None:
    """Check screenshot fixture values on the selected detail page."""
    expected = (
        {"wan-port-kpis": "125.0", "wan-port-gauges": "12.5", "wan-calendar-summaries": "1 of 744"}
        if detail == "port"
        else {"wan-peer-kpis": "33.3", "wan-peer-gauges": "0.25"}
    )
    for selector, value in expected.items():
        expect(page.get_by_test_id(selector)).to_contain_text(value)


@pytest.mark.parametrize(("detail", "selector"), [("port", "wan-port"), ("peer", "wan-peer")])
def test_browser_follows_live_and_synthetic_wan_journeys(
    page: Page, wan_browser_portal: str, detail: str, selector: str, pytestconfig: pytest.Config
) -> None:
    """Follow real portal links through each synthetic detail view and back."""
    logger.info("Starting the offline WAN browser journey for %s", detail)
    page.set_default_timeout(15_000)
    page.set_viewport_size({"width": 1440, "height": 1100})
    response = page.goto(f"{wan_browser_portal}/", wait_until="domcontentloaded", timeout=15_000)
    if response is None:
        raise AssertionError("The portal dashboard returned no browser response.")
    assert response.status == 200, f"The portal dashboard returned HTTP {response.status}."
    page.get_by_test_id("nav-wan-performance").click()
    expect(page.get_by_test_id("wan-live-overview")).to_be_visible()
    page.get_by_test_id("wan-offline-link").click()
    evidence = Path(pytestconfig.rootpath) / "test-artifacts" / "wan-performance"
    evidence.mkdir(parents=True, exist_ok=True)
    for link, view in (("wan-gateway-link", "wan-overview"), (f"wan-{detail}-link", "wan-gateway")):
        _assert_preview_layout(page, view)
        page.screenshot(path=str(evidence / f"{view}-comparison.png"), full_page=True)
        page.get_by_test_id(link).click()
    expect(page.get_by_test_id(selector)).to_be_visible()
    expect(page.get_by_test_id("wan-data-state")).to_contain_text("Live data is not connected")
    _assert_detail_metrics(page, detail)
    chart_grid = page.get_by_test_id(f"wan-{detail}-charts")
    expect(chart_grid).to_have_class(re.compile("wan-chart-grid--single"))
    chart_panel = chart_grid.locator(".wan-chart-panel")
    chart_bounds = chart_panel.bounding_box()
    assert (
        chart_bounds is not None and chart_bounds["width"] > 1_000
    ), "The single detail chart did not use the source page width."
    page.screenshot(path=str(evidence / f"{detail}-comparison.png"), full_page=True)
    page.get_by_test_id("wan-back-link").click()
    expect(page.get_by_test_id("wan-gateway")).to_be_visible()
    page.get_by_test_id("wan-back-link").click()
    expect(page.get_by_test_id("wan-overview")).to_be_visible()
    page.screenshot(path=str(evidence / f"{detail}-journey.png"), full_page=True)
    logger.debug("The offline WAN browser journey for %s returned to the overview", detail)


def test_portal_navigation_opens_live_wan_snapshots(client: FlaskClient) -> None:
    """Open live snapshots first and keep the synthetic preview separate."""
    logger.info("Loading the existing portal dashboard to inspect navigation")
    response = client.get("/")
    page = response.get_data(as_text=True)
    assert response.status_code == 200, f"The portal dashboard returned {response.status_code}."
    assert 'data-testid="nav-wan-performance"' in page, "The portal navigation omitted WAN Performance."
    assert 'href="/wan-performance/live/"' in page, "The portal navigation does not open live snapshots."
    assert ">WAN Performance</a>" in page, "The navigation does not identify the live portal."
    logger.debug("The portal navigation exposed live WAN snapshots")


@pytest.mark.parametrize(
    ("path", "selector"),
    [
        ("/wan-performance/", "wan-overview"),
        (f"/wan-performance/gateway/{GATEWAY_ID}?site_id={SITE_ID}", "wan-gateway"),
        (
            f"/wan-performance/port/{SITE_ID}/ge-0%2F0%2F1?gateway_id={GATEWAY_ID}",
            "wan-port",
        ),
        (
            f"/wan-performance/vpn/{SITE_ID}/11%3A22%3A33%3A44%3A55%3A66",
            "wan-peer",
        ),
    ],
)
def test_each_page_renders_an_explicit_synthetic_state(
    preview_client: FlaskClient,
    path: str,
    selector: str,
) -> None:
    """Keep all four journeys visibly separate from live measurements."""
    logger.info("Requesting the synthetic WAN page at %s", path)
    response = preview_client.get(path)
    page = response.get_data(as_text=True)
    assert response.status_code == 200, f"The synthetic page returned {response.status_code}."
    assert f'data-testid="{selector}"' in page, f"The page did not render selector {selector!r}."
    assert 'data-testid="wan-data-state"' in page, "The page did not render its data-state selector."
    assert "Synthetic offline preview" in page, "The page did not identify its synthetic data."
    logger.debug("The synthetic WAN page returned %d", response.status_code)


def test_overview_shows_verified_fixture_values_and_marks_unknown_metrics(
    preview_client: FlaskClient,
) -> None:
    """Show available fixture metrics without inventing congestion or availability."""
    logger.info("Checking the synthetic WAN overview metrics")
    response = preview_client.get("/wan-performance/")
    page = response.get_data(as_text=True)
    assert 'data-testid="wan-overview-kpis"' in page, "The overview omitted its KPI cards."
    assert "12.5" in page, "The overview omitted the screenshot fixture utilization value."
    assert 'data-testid="wan-unknown-metrics"' in page, "The overview omitted its unknown-metric note."
    assert "Not established in offline data" in page, "The overview presented an unverified metric as known."
    assert (
        f'href="/wan-performance/gateway/{GATEWAY_ID}?site_id={SITE_ID}"' in page
    ), "The overview omitted the gateway detail link."
    logger.debug("The synthetic WAN overview exposed only verified fixture values")


def test_detail_pages_link_across_the_gateway_port_peer_journeys(
    preview_client: FlaskClient,
) -> None:
    """Keep gateway, port, peer, and overview navigation connected."""
    logger.info("Checking the offline WAN detail navigation")
    gateway_response = preview_client.get(f"/wan-performance/gateway/{GATEWAY_ID}?site_id={SITE_ID}")
    gateway_page = gateway_response.get_data(as_text=True)
    assert 'data-testid="wan-port-link"' in gateway_page, "The gateway page omitted its port link."
    assert 'data-testid="wan-peer-link"' in gateway_page, "The gateway page omitted its peer link."
    assert 'data-testid="wan-back-link"' in gateway_page, "The gateway page omitted its overview link."
    port_response = preview_client.get(f"/wan-performance/port/{SITE_ID}/ge-0%2F0%2F1?gateway_id={GATEWAY_ID}")
    assert 'data-testid="wan-back-link"' in port_response.get_data(
        as_text=True
    ), "The port page omitted its gateway link."
    peer_response = preview_client.get(f"/wan-performance/vpn/{SITE_ID}/11%3A22%3A33%3A44%3A55%3A66")
    assert 'data-testid="wan-back-link"' in peer_response.get_data(
        as_text=True
    ), "The peer page omitted its gateway link."
    logger.debug("Gateway, port, peer, and overview navigation is connected")


def test_port_route_preserves_an_encoded_slash_and_bandwidth_units(
    preview_client: FlaskClient,
) -> None:
    """Resolve an encoded interface name without changing its source value."""
    logger.info("Requesting the synthetic WAN port with encoded separators")
    response = preview_client.get(f"/wan-performance/port/{SITE_ID}/ge-0%2F0%2F1?gateway_id={GATEWAY_ID}")
    page = response.get_data(as_text=True)
    assert response.status_code == 200, f"The encoded port route returned {response.status_code}."
    assert "ge-0/0/1" in page, "The port page changed the interface name."
    assert "RX (Mbps)" in page, "The port page omitted receive bandwidth."
    assert "125.0" in page, "The port page omitted its synthetic receive value."
    assert "megabits per second" in page, "The port page omitted the bandwidth unit."
    logger.debug("The encoded WAN port route returned %d", response.status_code)


def test_port_calendar_summaries_report_observations_and_missing_hours(
    preview_client: FlaskClient,
) -> None:
    """Show synthetic summaries without claiming complete elapsed-time coverage."""
    response = preview_client.get(f"/wan-performance/port/{SITE_ID}/ge-0%2F0%2F1?gateway_id={GATEWAY_ID}")
    page = response.get_data(as_text=True)
    assert response.status_code == 200, "The synthetic calendar view failed."
    assert 'data-testid="wan-calendar-summaries"' in page, "The port omitted calendar summaries."
    assert "1 of 24" in page, "The daily view did not expose missing hours."
    assert "1 of 168" in page, "The weekly view did not expose missing hours."
    assert "1 of 744" in page, "The monthly view did not expose missing hours."
    assert "rolling_3h" in page and "1 of 3" in page, "The 3-hour view omitted its observed sample count."
    assert "rolling_12h" in page and "1 of 12" in page, "The 12-hour view omitted its observed sample count."
    assert "rolling_24h" in page and "1 of 24" in page, "The 24-hour view omitted its observed sample count."
    assert "end at the latest retained observation" in page, "The rolling window anchor was not disclosed."
    assert "equal weight" in page, "The calendar view did not disclose source weighting."
    assert "not duration coverage" in page, "The calendar view mislabeled observation coverage."


def test_port_calendar_view_handles_missing_synthetic_records(
    client: FlaskClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Keep an empty preview explicit instead of presenting zero-valued summaries."""
    dashboard = replace(OfflinePreviewFactory.build(), measurements=())
    monkeypatch.setattr(OfflinePreviewFactory, "build", staticmethod(lambda: dashboard))
    response = client.get(f"/wan-performance/port/{SITE_ID}/ge-0%2F0%2F1?gateway_id={GATEWAY_ID}")
    page = response.get_data(as_text=True)
    assert response.status_code == 200, "The port view failed when synthetic measurements were absent."
    assert "No synthetic circuit history is available." in page, "The view omitted its missing history state."
    assert "1 of 24" not in page, "The view invented an observed hour."


def test_peer_route_shows_each_quality_metric_and_tunnel_identity(
    preview_client: FlaskClient,
) -> None:
    """Keep the synthetic peer values and explicit tunnel identity visible."""
    logger.info("Checking the synthetic VPN peer metrics")
    response = preview_client.get(f"/wan-performance/vpn/{SITE_ID}/11%3A22%3A33%3A44%3A55%3A66")
    page = response.get_data(as_text=True)
    assert "11:22:33:44:55:66" in page, "The peer page changed the MAC address."
    assert "packet loss" in page.lower(), "The peer page omitted packet loss."
    assert "latency" in page.lower(), "The peer page omitted latency."
    assert "jitter" in page.lower(), "The peer page omitted jitter."
    assert "synthetic-tunnel-4200" in page, "The peer page omitted explicit tunnel identity."
    logger.debug("The synthetic VPN peer page exposed all fixture quality metrics")


@pytest.mark.parametrize(
    ("path", "expected_status"),
    [
        (f"/wan-performance/gateway/%21invalid?site_id={SITE_ID}", 400),
        (f"/wan-performance/gateway/unknown-gateway?site_id={SITE_ID}", 404),
        ("/wan-performance/gateway/aabbccddeeff?site_id=22222222-2222-2222-2222-222222222222", 404),
    ],
)
def test_gateway_routes_reject_invalid_or_unmatched_identities(
    preview_client: FlaskClient,
    path: str,
    expected_status: int,
) -> None:
    """Reject malformed gateway IDs and valid IDs outside the fixture."""
    logger.info("Checking gateway route rejection at %s", path)
    response = preview_client.get(path)
    assert (
        response.status_code == expected_status
    ), f"The gateway route returned {response.status_code}, not {expected_status}."
    logger.debug("The gateway route rejected the identity with %d", response.status_code)


def test_routes_keep_the_existing_portal_allowlist(preview_client: FlaskClient) -> None:
    """Apply the existing portal address check to the WAN blueprint."""
    logger.info("Checking WAN page access from a public address")
    response = preview_client.get(
        "/wan-performance/",
        environ_base={"REMOTE_ADDR": "203.0.113.10"},
    )
    assert response.status_code == 403, "A public address reached the WAN portal route."
    logger.debug("The public address received %d", response.status_code)


def test_offline_preview_is_available_without_a_live_provider(
    client: FlaskClient,
) -> None:
    """Serve labeled synthetic values without a live data provider."""
    logger.info("Requesting the WAN preview without a live data provider")
    response = client.get("/wan-performance/")
    page = response.get_data(as_text=True)
    assert response.status_code == 200, f"The offline preview returned {response.status_code}."
    assert "Synthetic offline preview" in page, "The preview did not identify its synthetic values."
    assert "Live data is not connected" in page, "The preview did not distinguish live data."
    logger.debug("The WAN preview returned synthetic values with status %d", response.status_code)


def test_offline_preview_is_labeled_when_test_mode_is_disabled(
    preview_client: FlaskClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Keep synthetic preview values separate from live data outside test mode."""
    logger.info("Disabling test mode while the offline preview remains available")
    monkeypatch.setitem(preview_client.application.config, "TESTING", False)
    response = preview_client.get("/wan-performance/")
    page = response.get_data(as_text=True)
    assert response.status_code == 200, "The offline preview is unavailable outside test mode."
    assert "Synthetic offline preview" in page, "The page did not label synthetic values."
    assert "Live data is not connected" in page, "The page did not distinguish live data."
    logger.debug("The offline preview returned %d outside test mode", response.status_code)


def test_preview_rejects_a_factory_with_an_unknown_shape(
    client: FlaskClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reject a preview factory result that does not match the offline contract."""
    logger.info("Installing a preview factory with an unsupported return value")
    monkeypatch.setattr(OfflinePreviewFactory, "build", staticmethod(lambda: object()))
    response = client.get("/wan-performance/")
    assert response.status_code == 500, "The route accepted an unsupported provider result."
    assert (
        "invalid shape" in response.get_data(as_text=True).lower()
    ), "The route did not report the unsupported provider shape."
    logger.debug("The unsupported preview factory returned %d", response.status_code)


def test_preview_rejects_any_live_record_from_the_preview_factory(
    client: FlaskClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Keep a live measurement out of the synthetic preview."""
    logger.info("Building a preview result with one live measurement")
    dashboard = OfflinePreviewFactory.build()
    live_measurement = replace(dashboard.measurements[0], provenance="live")
    mixed_dashboard = replace(
        dashboard,
        measurements=(live_measurement, *dashboard.measurements[1:]),
    )
    monkeypatch.setattr(OfflinePreviewFactory, "build", staticmethod(lambda: mixed_dashboard))
    response = client.get("/wan-performance/")
    assert response.status_code == 500, "The preview displayed a live measurement."
    assert (
        "must be synthetic" in response.get_data(as_text=True).lower()
    ), "The preview did not report its provenance violation."
    logger.debug("The mixed-provenance provider returned %d", response.status_code)


def test_port_route_rejects_path_traversal_and_unmatched_ports(
    preview_client: FlaskClient,
) -> None:
    """Reject traversal syntax and valid port names outside the fixture."""
    logger.info("Checking invalid and unmatched WAN port values")
    traversal = preview_client.get(f"/wan-performance/port/{SITE_ID}/ge-0/%2E%2E/1?gateway_id={GATEWAY_ID}")
    unmatched = preview_client.get(f"/wan-performance/port/{SITE_ID}/ge-0/0/2?gateway_id={GATEWAY_ID}")
    assert traversal.status_code == 400, "The WAN port route accepted a traversal component."
    assert unmatched.status_code == 404, "The WAN port route returned a fixture for another port."
    logger.debug("The WAN port route rejected traversal and unmatched values")


@pytest.mark.parametrize(
    ("site_id", "peer_mac", "expected_status"),
    [
        (SITE_ID, "not-a-peer", 400),
        ("22222222-2222-2222-2222-222222222222", "11:22:33:44:55:66", 404),
        (SITE_ID, "00:00:00:00:00:01", 404),
    ],
)
def test_peer_route_rejects_invalid_or_unmatched_identity(
    preview_client: FlaskClient,
    site_id: str,
    peer_mac: str,
    expected_status: int,
) -> None:
    """Reject malformed peer values and identities outside the fixture."""
    logger.info("Checking a VPN peer route for site %s", site_id)
    response = preview_client.get(f"/wan-performance/vpn/{site_id}/{peer_mac}")
    assert (
        response.status_code == expected_status
    ), f"The peer route returned {response.status_code}, not {expected_status}."
    logger.debug("The peer route returned %d for the requested identity", response.status_code)
