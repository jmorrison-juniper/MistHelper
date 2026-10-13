"""Verify the WAN Performance pages with isolated synthetic fixtures."""

import logging
from dataclasses import replace

import pytest
from flask import Flask
from flask.testing import FlaskClient

from tests.fixtures.wan_performance.offline_dashboard import OfflineDashboardFactory

logger = logging.getLogger(__name__)  # Keep route test records on the module logger.
SITE_ID = "11111111-1111-1111-1111-111111111111"
GATEWAY_ID = "aabbccddeeff"


@pytest.fixture
def preview_client(
    client: FlaskClient,
    flask_app: Flask,
    monkeypatch: pytest.MonkeyPatch,
) -> FlaskClient:
    """Inject the offline fixture without starting a service client."""
    logger.info("Installing the synthetic WAN provider for one portal test")
    monkeypatch.setitem(flask_app.config, "WAN_PERFORMANCE_PREVIEW_FACTORY", OfflineDashboardFactory.build)
    logger.debug("Installed the isolated synthetic WAN provider")
    return client


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
    assert 'data-testid="wan-utilization"' in page, "The overview omitted utilization."
    assert "42.5" in page, "The overview omitted the fixture utilization value."
    assert 'data-testid="wan-congestion"' in page, "The overview omitted its congestion state."
    assert 'data-testid="wan-availability"' in page, "The overview omitted its availability state."
    assert "Not established in offline data" in page, "The overview presented an unverified metric as known."
    assert (
        f'href="/wan-performance/gateway/{GATEWAY_ID}?site_id={SITE_ID}"' in page
    ), "The overview omitted the gateway detail link."
    logger.debug("The synthetic WAN overview exposed only verified fixture values")


def test_port_route_preserves_an_encoded_slash_and_bandwidth_units(
    preview_client: FlaskClient,
) -> None:
    """Resolve an encoded interface name without changing its source value."""
    logger.info("Requesting the synthetic WAN port with encoded separators")
    response = preview_client.get(f"/wan-performance/port/{SITE_ID}/ge-0%2F0%2F1?gateway_id={GATEWAY_ID}")
    page = response.get_data(as_text=True)
    assert response.status_code == 200, f"The encoded port route returned {response.status_code}."
    assert "ge-0/0/1" in page, "The port page changed the interface name."
    assert "Receive bandwidth" in page, "The port page omitted receive bandwidth."
    assert "80.0" in page, "The port page omitted its synthetic receive value."
    assert "megabits per second" in page, "The port page omitted the bandwidth unit."
    logger.debug("The encoded WAN port route returned %d", response.status_code)


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


def test_missing_provider_returns_unavailable_instead_of_live_fallback(
    client: FlaskClient,
) -> None:
    """Do not make an API call or return synthetic data without an explicit provider."""
    logger.info("Requesting WAN Performance without an installed data provider")
    response = client.get("/wan-performance/")
    assert response.status_code == 503, f"The unavailable route returned {response.status_code}."
    assert (
        "data provider" in response.get_data(as_text=True).lower()
    ), "The unavailable response did not name the missing provider."
    logger.debug("The WAN route reported unavailable data with %d", response.status_code)


def test_synthetic_provider_stays_disabled_outside_test_mode(
    preview_client: FlaskClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prevent a configured test fixture from serving a live portal request."""
    logger.info("Disabling test mode while the synthetic provider remains configured")
    monkeypatch.setitem(preview_client.application.config, "TESTING", False)
    response = preview_client.get("/wan-performance/")
    assert response.status_code == 503, "The live portal served a synthetic test fixture."
    assert (
        "data provider" in response.get_data(as_text=True).lower()
    ), "The live portal did not report its unavailable provider."
    logger.debug("The live-mode request returned %d", response.status_code)


def test_preview_rejects_a_provider_with_an_unknown_shape(
    client: FlaskClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reject an injected provider that does not match the offline contract."""
    logger.info("Installing a provider with an unsupported return value")
    monkeypatch.setitem(client.application.config, "WAN_PERFORMANCE_PREVIEW_FACTORY", lambda: object())
    response = client.get("/wan-performance/")
    assert response.status_code == 500, "The route accepted an unsupported provider result."
    assert (
        "invalid shape" in response.get_data(as_text=True).lower()
    ), "The route did not report the unsupported provider shape."
    logger.debug("The unsupported provider returned %d", response.status_code)


def test_preview_rejects_any_live_record_from_the_fixture_provider(
    client: FlaskClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Keep a live measurement out of the synthetic preview."""
    logger.info("Building a provider result with one live measurement")
    dashboard = OfflineDashboardFactory.build()
    live_measurement = replace(dashboard.measurements[0], provenance="live")
    mixed_dashboard = replace(
        dashboard,
        measurements=(live_measurement, *dashboard.measurements[1:]),
    )
    monkeypatch.setitem(
        client.application.config,
        "WAN_PERFORMANCE_PREVIEW_FACTORY",
        lambda: mixed_dashboard,
    )
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
