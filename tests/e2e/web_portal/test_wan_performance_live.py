"""Exercise the live WAN portal using isolated stores and mocked Mist responses."""

import re
import threading
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from playwright.sync_api import Locator, Page, expect
from werkzeug.serving import make_server

from src.interfaces.wan_performance.collection.live_service import LiveService


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


@pytest.fixture
def cached_gateway_statistics(live_service: LiveService) -> LiveService:
    """Add independently authored discovery fields without collecting or persisting them."""
    live_service.store.cached.return_value["insights"] = {
        "gateway": {
            "org_id": "org-one",
            "site_id": "site-one",
            "mac": "aabbccddeeff",
            "type": "gateway",
            "cpu_stat": {"usage": 0},
            "memory_stat": {"usage": 35.5},
            "uptime": 0,
            "last_seen": 0,
        },
        "samples": [],
    }
    return live_service


def test_cached_gateway_statistics_use_existing_scope_and_leave_csv_unchanged(client, cached_gateway_statistics):
    """Display documented metadata without adding it to observations or CSV history."""
    path = "/wan-performance/live/gateway/aabbccddeeff?site_id=site-one"
    text = client.get(path).get_data(as_text=True)
    assert 'data-testid="wan-gateway-statistics"' in text
    assert "35.5 %" in text and "0 seconds" in text
    assert "1970-01-01T00:00:00+00:00" in text
    exported = client.get(path + "&download=csv").get_data(as_text=True)
    assert "rx_bps" in exported and "Reported CPU usage" not in exported
    assert "35.5" not in exported
    cached_gateway_statistics.store.acquire.assert_not_called()
    cached_gateway_statistics.history.upsert.assert_not_called()
    cached_gateway_statistics.session.assert_not_called()


@pytest.mark.parametrize("field", ["org_id", "site_id", "mac", "type"])
def test_gateway_discovery_scope_failure_preserves_other_cached_records(client, cached_gateway_statistics, field):
    """Hide mismatched discovery metadata while retaining valid circuit observations."""
    cached_gateway_statistics.store.cached.return_value["insights"]["gateway"][field] = "foreign"
    text = client.get("/wan-performance/live/gateway/aabbccddeeff?site_id=site-one").get_data(as_text=True)
    assert "Unavailable: no matching cached gateway discovery." in text
    assert "35.5 %" not in text
    assert "rx_bps: 40 bit/s" in text
    cached_gateway_statistics.store.acquire.assert_not_called()


@pytest.mark.parametrize("viewport", [(1440, 1100), (1280, 800), (390, 844)])
def test_browser_cached_gateway_statistics_remain_read_only(
    page: Page, live_browser_url: str, cached_gateway_statistics: LiveService, viewport, wan_browser_artifacts: Path
) -> None:
    """Keep exact units and zero readable at all sizes without additional requests."""
    page.set_viewport_size({"width": viewport[0], "height": viewport[1]})
    page.goto(live_browser_url + "/wan-performance/live/gateway/aabbccddeeff?site_id=site-one")
    statistics = page.get_by_test_id("wan-gateway-statistics")
    expect(statistics).to_contain_text("Reported CPU usage")
    expect(statistics).to_contain_text("0 %")
    expect(statistics).to_contain_text("35.5 %")
    expect(statistics).to_contain_text("0 seconds")
    expect(statistics).to_contain_text("1970-01-01T00:00:00+00:00")
    expect(statistics).to_contain_text("not link availability")
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    assert cached_gateway_statistics.history.read.call_count == 1
    cached_gateway_statistics.history.upsert.assert_not_called()
    cached_gateway_statistics.store.acquire.assert_not_called()
    cached_gateway_statistics.session.assert_not_called()
    page.screenshot(path=str(wan_browser_artifacts / f"cached-gateway-statistics-{viewport[0]}.png"), full_page=True)


@pytest.fixture
def retained_history(live_service):
    """Return one independent retained observation inside each requested window."""
    from datetime import datetime, timedelta

    from src.interfaces.wan_performance.domain.measurement import (
        HourlyMeasurement,
        MeasurementIdentity,
        MetricMeasurement,
    )

    def read(identity: MeasurementIdentity, start: datetime, end: datetime) -> tuple[HourlyMeasurement, ...]:
        """Return synthetic values through the mocked live repository boundary."""
        hour = start.replace(minute=0, second=0, microsecond=0)
        if hour < start:
            hour += timedelta(hours=1)
        return (
            HourlyMeasurement(
                identity,
                hour,
                hour + timedelta(minutes=1),
                {
                    "rx_bps": MetricMeasurement(40, "bit/s"),
                    "loss": MetricMeasurement(None, "%", missing_reason="No fixture sample."),
                },
                "live",
            ),
        )

    live_service.history.read.side_effect = read
    return live_service.history


@pytest.mark.parametrize("path", ["/wan-performance/live/site/site-one", "/wan-performance/live/?site_id=site-one"])
def test_cached_site_selection_uses_exact_cached_org_membership(client, live_service, path):
    """Scope site views without claiming complete site inventory or reading all histories."""
    snapshot = live_service.store.cached.return_value
    snapshot["ports"].append({**snapshot["ports"][0], "site_id": "site-two", "mac": "112233445566"})
    snapshot["ports"].append({**snapshot["ports"][0], "site_id": "SITE-ONE", "mac": "112233445577"})
    response = client.get(path)
    text = response.get_data(as_text=True)
    assert response.status_code == 200
    assert 'data-testid="wan-live-site"' in text
    assert '<option value="site-one" selected>' in text
    assert '<option value="SITE-ONE">' in text
    assert 'data-testid="wan-live-gateway-link" href="/wan-performance/live/gateway/112233445566' not in text
    assert 'data-testid="wan-live-refresh"' not in text
    live_service.history.read.assert_not_called()
    live_service.store.acquire.assert_not_called()


def test_uncached_site_is_not_a_valid_history_selector(client, live_service):
    """Reject arbitrary site names before any history or API operation."""
    response = client.get("/wan-performance/live/site/unknown?window=6h")
    assert response.status_code == 404
    live_service.history.read.assert_not_called()
    live_service.store.acquire.assert_not_called()


@pytest.mark.parametrize("case", [("6h", 6), ("12h", 12), ("24h", 24), ("7d", 168)])
@pytest.mark.parametrize(
    "path",
    [
        "/wan-performance/live/gateway/aabbccddeeff?site_id=site-one",
        "/wan-performance/live/port/site-one/ge-0/0/0?gateway_id=aabbccddeeff",
        "/wan-performance/live/vpn/site-one/11:22:33:44:55:66",
    ],
)
def test_retained_window_reads_one_full_identity_without_new_aggregation(
    client, live_service, retained_history, case, path
):
    """Read one bounded UTC history and expose raw values, missing metrics, and missing buckets."""
    from datetime import timedelta

    key, hours = case
    separator = "&" if "?" in path else "?"
    response = client.get(path + separator + "window=" + key)
    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert 'data-testid="wan-retained-window"' in text
    assert f"1 retained hour buckets of {hours} expected" in text
    assert f"Missing retained buckets: {hours - 1}" in text
    assert "loss: Unknown: No fixture sample." in text
    assert "rx_bps: 40 bit/s" in text
    assert "Measurement completeness remains unknown" in text
    assert 'data-testid="wan-live-history"' not in text
    retained_history.read.assert_called_once()
    identity, start, end = retained_history.read.call_args.args
    gateway = identity if hasattr(identity, "site") else identity.gateway
    assert (gateway.site.org_id, gateway.site.site_id, gateway.gateway_id) == ("org-one", "site-one", "aabbccddeeff")
    assert end - start == timedelta(hours=hours)
    assert start.utcoffset() == end.utcoffset() == timedelta(0)
    assert (end.minute, end.second, end.microsecond) == (0, 0, 0)
    live_service.store.acquire.assert_not_called()
    retained_history.upsert.assert_not_called()
    retained_history.read_samples.assert_not_called()


@pytest.mark.parametrize("path", ["/wan-performance/live/", "/wan-performance/live/site/site-one"])
def test_retained_organization_and_site_aggregates_remain_unavailable(client, live_service, path):
    """Do not fan out across circuit identities or invent organization/site metrics."""
    response = client.get(path + "?window=7d")
    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert "Organization and site aggregate history is unavailable" in text
    assert 'data-testid="wan-retained-coverage"' not in text
    live_service.history.read.assert_not_called()
    live_service.store.acquire.assert_not_called()


@pytest.mark.parametrize("key", ["1h", "0h", "13months", "6H", "unknown"])
def test_invalid_retained_window_is_a_client_error(client, live_service, key):
    """Reject unsupported ranges before reading a cache or store."""
    response = client.get("/wan-performance/live/?window=" + key)
    assert response.status_code == 400
    live_service.store.cached.assert_not_called()
    live_service.history.read.assert_not_called()


@pytest.mark.parametrize("state", ["empty", "store-missing", "read-failed"])
def test_retained_window_distinguishes_empty_from_unavailable(client, live_service, state):
    """Never turn a failed history read into zero missing buckets or healthy metrics."""
    history = live_service.history
    if state == "store-missing":
        live_service.history = None
    elif state == "read-failed":
        history.read.side_effect = ConnectionError("Synthetic unavailable history.")
    response = client.get("/wan-performance/live/port/site-one/ge-0/0/0?gateway_id=aabbccddeeff&window=6h")
    text = response.get_data(as_text=True)
    assert response.status_code == 200
    if state == "empty":
        assert "Missing retained buckets: 6" in text
        assert "No retained observations exist in this window" in text
    else:
        assert 'data-testid="wan-retained-unavailable"' in text
        assert 'data-testid="wan-retained-coverage"' not in text
    live_service.store.acquire.assert_not_called()


def test_retained_window_does_not_change_cached_csv_scope(client, live_service):
    """Export only current cached rows without opening a retained history read."""
    response = client.get("/wan-performance/live/port/site-one/ge-0/0/0?gateway_id=aabbccddeeff&window=7d&download=csv")
    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert "2024-01-01T12:00:00+00:00" in response.get_data(as_text=True)
    live_service.history.read.assert_not_called()
    live_service.store.acquire.assert_not_called()


def test_retained_plot_renders_present_values_without_missing_value_zeros(client, live_service, retained_history):
    """Show an accessible discrete plot from the same exact scoped repository read."""
    response = client.get("/wan-performance/live/port/site-one/ge-0/0/0?gateway_id=aabbccddeeff&window=6h")
    text = response.get_data(as_text=True)
    assert response.status_code == 200
    assert 'aria-label="rx_bps: bit/s. Discrete retained hourly projections."' in text
    assert text.count('data-testid="wan-retained-point"') == 1
    assert 'data-value="40"' in text
    assert "Points do not identify source metric sample times" in text
    assert "No present metric values are available to plot" not in text
    retained_history.read.assert_called_once()
    retained_history.read_samples.assert_not_called()
    retained_history.upsert.assert_not_called()
    live_service.store.acquire.assert_not_called()


def test_cached_site_csv_cannot_include_other_cached_sites(client, live_service):
    """Preserve selected-site scope across the separate cached export."""
    import csv
    import io

    snapshot = live_service.store.cached.return_value
    snapshot["ports"].append({**snapshot["ports"][0], "site_id": "site-two", "mac": "112233445566"})
    response = client.get("/wan-performance/live/site/site-one?download=csv&window=12h")
    rows = list(csv.DictReader(io.StringIO(response.get_data(as_text=True))))
    assert response.status_code == 200
    assert {row["site_id"] for row in rows} == {"site-one"}
    assert {row["gateway_id"] for row in rows} == {"aabbccddeeff"}
    live_service.history.read.assert_not_called()
    live_service.store.acquire.assert_not_called()


def test_retained_peer_window_refuses_ambiguous_path_scope(client, live_service):
    """Keep distinct peer paths separate instead of reading an arbitrary history."""
    snapshot = live_service.store.cached.return_value
    snapshot["peers"].append({**snapshot["peers"][0], "peer_port_id": "ge-0/0/2"})
    response = client.get("/wan-performance/live/vpn/site-one/11:22:33:44:55:66?window=6h")
    assert response.status_code == 200
    assert "Select exactly one full detail identity" in response.get_data(as_text=True)
    live_service.history.read.assert_not_called()


@pytest.mark.parametrize("viewport", [(1440, 1100), (1280, 800), (390, 844)])
def test_browser_cached_site_and_retained_window_journey(page: Page, live_browser_url: str, retained_history, viewport):
    """Navigate cached sites and exact detail histories with a preserved UTC window."""
    page.set_viewport_size({"width": viewport[0], "height": viewport[1]})
    page.goto(live_browser_url + "/wan-performance/live/")
    page.get_by_test_id("wan-cached-site").select_option("site-one")
    page.get_by_test_id("wan-cached-site-open").click()
    expect(page.get_by_test_id("wan-live-site")).to_be_visible()
    page.get_by_test_id("wan-live-gateway-link").first.click()
    for key in ["6h", "12h", "24h", "7d"]:
        page.get_by_test_id("wan-retained-selection").select_option(key)
        page.get_by_test_id("wan-retained-apply").click()
        expect(page.get_by_test_id("wan-retained-records")).to_contain_text("rx_bps: 40 bit/s")
        expect(page.get_by_test_id("wan-retained-coverage")).to_contain_text("Measurement completeness remains unknown")
        expect(page.get_by_test_id("wan-retained-plot")).to_have_attribute(
            "aria-label", "rx_bps: bit/s. Discrete retained hourly projections."
        )
        expect(page.get_by_test_id("wan-retained-plot")).to_be_visible()
        expect(page.get_by_test_id("wan-retained-point")).to_have_count(1)
        expect(page.get_by_test_id("wan-retained-point")).to_have_attribute("data-value", "40")
        expect(page.get_by_test_id("wan-retained-plot").locator("polyline")).to_have_count(0)
    page.get_by_test_id("wan-live-port-link").first.click()
    expect(page.get_by_test_id("wan-live-port")).to_be_visible()
    expect(page.get_by_test_id("wan-retained-selection")).to_have_value("7d")
    page.get_by_test_id("wan-live-gateway-link").first.click()
    page.get_by_test_id("wan-live-peer-link").first.click()
    expect(page.get_by_test_id("wan-live-peer")).to_be_visible()
    expect(page.get_by_test_id("wan-retained-selection")).to_have_value("7d")
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), page.evaluate(
        "Array.from(document.querySelectorAll('dd'))"
        ".filter(element => element.scrollWidth > element.clientWidth).map(element => element.textContent)"
    )
    evidence_directory = Path(__file__).resolve().parents[3] / "test-artifacts" / "wan-performance"
    evidence_directory.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(evidence_directory / f"retained-{viewport[0]}.png"), full_page=True)
    reads = retained_history.read.call_count
    page.get_by_test_id("wan-live-back-link").click()
    expect(page.get_by_test_id("wan-retained-unavailable")).to_contain_text(
        "Organization and site aggregate history is unavailable"
    )
    assert retained_history.read.call_count == reads


class RetainedPlotJourney:
    """Keep distinct browser interaction assertions small and independently readable."""

    @staticmethod
    def inspect(chart: Locator) -> None:
        """Verify pointer and keyboard/touch selectors expose exact retained metadata."""
        chart.get_by_test_id("wan-retained-point").click()
        expect(chart.get_by_test_id("wan-retained-point-details")).to_contain_text("rx_bps: 40 bit/s")
        chart.get_by_test_id("wan-retained-point-selection").select_option("")
        chart.get_by_test_id("wan-retained-point-selection").select_option("0")
        expect(chart.get_by_test_id("wan-retained-point-details")).to_contain_text("rx_bps: 40 bit/s")

    @staticmethod
    def movement(page: Page, chart: Locator) -> None:
        """Verify keyboard zoom changes UTC bounds and reset restores them."""
        plot = chart.get_by_test_id("wan-retained-plot")
        initial = plot.locator("[data-window-start]").text_content()
        chart.get_by_test_id("wan-retained-zoom-in").focus()
        page.keyboard.press("Enter")
        expect(plot).to_have_attribute("data-plot-scale", "2")
        assert plot.locator("[data-window-start]").text_content() != initial
        chart.get_by_test_id("wan-retained-earlier").click()
        expect(plot).to_have_attribute("data-plot-offset", "0")
        expect(chart.get_by_test_id("wan-retained-earlier")).to_be_disabled()
        chart.get_by_test_id("wan-retained-later").click()
        expect(plot).to_have_attribute("data-plot-offset", "0.25")
        chart.get_by_test_id("wan-retained-reset").click()
        expect(plot).to_have_attribute("data-plot-scale", "1")
        assert plot.locator("[data-window-start]").text_content() == initial
        expect(chart.get_by_test_id("wan-retained-zoom-out")).to_be_disabled()

    @staticmethod
    def bounds(chart: Locator) -> None:
        """Verify both UTC boundaries, maximum zoom, and visible-point counts."""
        plot = chart.get_by_test_id("wan-retained-plot")
        for _ in range(3):
            chart.get_by_test_id("wan-retained-zoom-in").click()
        expect(plot).to_have_attribute("data-plot-scale", "8")
        expect(chart.get_by_test_id("wan-retained-zoom-in")).to_be_disabled()
        expect(chart.get_by_test_id("wan-retained-chart-status")).to_contain_text("0 of 1 retained points visible")
        for _ in range(7):
            chart.get_by_test_id("wan-retained-earlier").click()
        expect(plot).to_have_attribute("data-plot-offset", "0")
        expect(chart.get_by_test_id("wan-retained-earlier")).to_be_disabled()
        expect(chart.get_by_test_id("wan-retained-chart-status")).to_contain_text("1 of 1 retained points visible")
        for _ in range(14):
            chart.get_by_test_id("wan-retained-later").click()
        expect(plot).to_have_attribute("data-plot-offset", "0.875")
        expect(chart.get_by_test_id("wan-retained-later")).to_be_disabled()
        chart.get_by_test_id("wan-retained-reset").click()
        expect(chart.get_by_test_id("wan-retained-point")).to_have_attribute("data-value", "40")

    @staticmethod
    def download(page: Page, chart: Locator, directory: Path, width: int) -> None:
        """Save a real browser download and report rendering errors without a timeout."""
        browser_errors = []
        page.on("console", lambda message: browser_errors.append(message.text) if message.type == "error" else None)
        with page.expect_download() as downloaded:
            chart.get_by_test_id("wan-retained-png").click()
            expect(chart.get_by_test_id("wan-retained-chart-status")).to_contain_text(
                re.compile(r"PNG (download requested|could not be rendered)")
            )
            assert (
                "PNG download requested" in chart.get_by_test_id("wan-retained-chart-status").inner_text()
            ), browser_errors
        destination = directory / f"retained-controls-{width}.png"
        downloaded.value.save_as(destination)
        RetainedPlotJourney.verify_png(destination)
        expect(chart.get_by_test_id("wan-retained-point-details")).to_contain_text("UTC bucket")
        expect(chart.get_by_test_id("wan-retained-point-details")).to_contain_text("Collected")

    @staticmethod
    def verify_png(destination: Path) -> None:
        """Verify encoded image type and the bounded raster dimensions."""
        encoded = destination.read_bytes()
        assert encoded.startswith(b"\x89PNG\r\n\x1a\n")
        assert int.from_bytes(encoded[16:20], "big") == 1280
        assert int.from_bytes(encoded[20:24], "big") == 600


@pytest.mark.parametrize("viewport", [(1440, 1100), (1280, 800), (390, 844)])
def test_browser_retained_plot_controls_are_local_and_keyboard_accessible(
    page: Page, live_browser_url: str, retained_history, viewport, wan_browser_artifacts
):
    """Inspect, zoom, move, reset, and download without a second history request."""
    page.set_viewport_size({"width": viewport[0], "height": viewport[1]})
    page.goto(live_browser_url + "/wan-performance/live/port/site-one/ge-0/0/0?gateway_id=aabbccddeeff&window=6h")
    chart = page.get_by_test_id("wan-retained-chart")
    RetainedPlotJourney.inspect(chart)
    requests = []
    page.on("request", lambda request: requests.append(request.url) if "/wan-performance/" in request.url else None)
    RetainedPlotJourney.movement(page, chart)
    RetainedPlotJourney.bounds(chart)
    RetainedPlotJourney.download(page, chart, wan_browser_artifacts, viewport[0])
    expect(page.get_by_test_id("wan-retained-records")).to_contain_text("rx_bps: 40 bit/s")
    assert requests == []
    retained_history.read.assert_called_once()
    retained_history.read_samples.assert_not_called()
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    chart.screenshot(path=str(wan_browser_artifacts / f"retained-chart-{viewport[0]}.png"))


@pytest.fixture
def wan_browser_artifacts() -> Path:
    """Keep destination-only screenshots and PNG downloads in ignored test evidence."""
    directory = Path(__file__).resolve().parents[3] / "test-artifacts" / "wan-performance" / "destination-interactions"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


@pytest.fixture
def visibility_history(retained_history):
    """Keep two independent measured metrics beside an explicitly missing value."""
    from dataclasses import replace

    from src.interfaces.wan_performance.domain.measurement import MetricMeasurement

    previous = retained_history.read.side_effect

    def read(identity, start, end):
        """Use existing scoped synthetic hours with an additional measured zero."""
        records = previous(identity, start, end)
        return (replace(records[0], metrics={**records[0].metrics, "tx_bps": MetricMeasurement(0, "bit/s")}),)

    retained_history.read.side_effect = read
    return retained_history


class RetainedVisibilityJourney:
    """Verify display-only visibility without changing retained observations."""

    @staticmethod
    def track_labels(page: Page) -> None:
        """Record actual canvas labels while preserving the native image output."""
        page.evaluate(
            "() => { window.wanPaintLabels = []; const paint = CanvasRenderingContext2D.prototype.fillText;"
            "CanvasRenderingContext2D.prototype.fillText = function(...args) {"
            "window.wanPaintLabels.push(args[0]); return paint.apply(this, args); }; }"
        )

    @staticmethod
    def delay_image(page: Page) -> None:
        """Pause native SVG image loading so a visibility race is reproducible."""
        page.evaluate(
            "() => { const source = Object.getOwnPropertyDescriptor(HTMLImageElement.prototype, 'src');"
            "Object.defineProperty(HTMLImageElement.prototype, 'src', {...source, set(value) {"
            "window.wanImageSource = value; window.wanLoadImage = () => source.set.call(this, value); }}); }"
        )

    @staticmethod
    def snapshot_visible(page: Page) -> None:
        """Match the image's captured display state and annotation, not the current SVG."""
        assert (
            page.evaluate(
                "new DOMParser().parseFromString(decodeURIComponent(window.wanImageSource.split(',')[1]),"
                "'image/svg+xml').documentElement.getAttribute('data-points-visible')"
            )
            == "true"
        )
        assert page.evaluate("window.wanPaintLabels.slice(-1)[0]") == (
            "Exact collection times and missing reasons remain in the retained table."
        )

    @staticmethod
    def hide(page: Page, chart: Locator) -> None:
        """Preserve hidden points through keyboard activation, zoom, and reset."""
        toggle = chart.get_by_test_id("wan-retained-toggle-points")
        expect(toggle).to_have_attribute("aria-pressed", "true")
        toggle.focus()
        page.keyboard.press("Enter")
        expect(toggle).to_have_attribute("aria-pressed", "false")
        chart.get_by_test_id("wan-retained-zoom-in").click()
        chart.get_by_test_id("wan-retained-reset").click()
        expect(chart.get_by_test_id("wan-retained-point")).to_be_hidden()
        expect(toggle).to_have_attribute("aria-pressed", "false")
        expect(chart.get_by_test_id("wan-retained-chart-status")).to_contain_text("hidden by the operator")
        chart.get_by_test_id("wan-retained-point-selection").select_option("0")
        expect(chart.get_by_test_id("wan-retained-point-details")).to_contain_text("40 bit/s")

    @staticmethod
    def export(page: Page, chart: Locator, directory: Path, width: int) -> None:
        """Verify an actual hidden-plot PNG carries the explicit display state."""
        RetainedVisibilityJourney.track_labels(page)
        with page.expect_download() as downloaded:
            chart.get_by_test_id("wan-retained-png").click()
        destination = directory / f"retained-hidden-{width}.png"
        downloaded.value.save_as(destination)
        RetainedPlotJourney.verify_png(destination)
        assert "The operator hid plotted points. Exact values remain in the table." in page.evaluate(
            "window.wanPaintLabels"
        )
        expect(chart.get_by_test_id("wan-retained-visibility-status")).to_contain_text("hidden by the operator")


@pytest.mark.parametrize("viewport", [(1440, 1100), (1280, 800), (390, 844)])
def test_browser_retained_visibility_preserves_other_metrics(
    page: Page, live_browser_url: str, visibility_history, viewport, wan_browser_artifacts
):
    """Hide one metric locally while preserving zero, missing values, and scope."""
    page.set_viewport_size({"width": viewport[0], "height": viewport[1]})
    page.goto(live_browser_url + "/wan-performance/live/port/site-one/ge-0/0/0?gateway_id=aabbccddeeff&window=6h")
    charts = page.get_by_test_id("wan-retained-chart")
    expect(charts).to_have_count(2)
    table = page.get_by_test_id("wan-retained-records").inner_text()
    requests = []
    page.on("request", lambda request: requests.append(request.url))
    RetainedVisibilityJourney.hide(page, charts.first)
    expect(charts.last.get_by_test_id("wan-retained-point")).to_be_visible()
    expect(charts.last.get_by_test_id("wan-retained-point")).to_have_attribute("data-value", "0")
    RetainedVisibilityJourney.export(page, charts.first, wan_browser_artifacts, viewport[0])
    charts.first.screenshot(path=str(wan_browser_artifacts / f"retained-hidden-chart-{viewport[0]}.png"))
    charts.first.get_by_test_id("wan-retained-toggle-points").click()
    expect(charts.first.get_by_test_id("wan-retained-point")).to_be_visible()
    assert page.get_by_test_id("wan-retained-records").inner_text() == table
    assert "No fixture sample." in table
    assert requests == []
    assert visibility_history.read.call_count == 1
    visibility_history.read_samples.assert_not_called()
    visibility_history.upsert.assert_not_called()


def test_browser_retained_png_preserves_visibility_during_image_load(
    page: Page, live_browser_url: str, retained_history, wan_browser_artifacts
):
    """Keep PNG annotations consistent with its snapshot during another interaction."""
    page.goto(live_browser_url + "/wan-performance/live/port/site-one/ge-0/0/0?gateway_id=aabbccddeeff&window=6h")
    RetainedVisibilityJourney.track_labels(page)
    RetainedVisibilityJourney.delay_image(page)
    with page.expect_download() as downloaded:
        page.get_by_test_id("wan-retained-png").click()
        page.wait_for_function("typeof window.wanLoadImage === 'function'")
        page.get_by_test_id("wan-retained-toggle-points").click()
        page.evaluate("window.wanLoadImage()")
    destination = wan_browser_artifacts / "retained-pending-visibility.png"
    downloaded.value.save_as(destination)
    RetainedPlotJourney.verify_png(destination)
    RetainedVisibilityJourney.snapshot_visible(page)
    expect(page.get_by_test_id("wan-retained-visibility-status")).to_contain_text("hidden by the operator")
    assert retained_history.read.call_count == 1


@pytest.mark.browser_context_args(java_script_enabled=False)
def test_browser_retained_table_survives_without_javascript(page: Page, live_browser_url: str, retained_history):
    """Retain exact values and static points without browser interaction support."""
    page.goto(live_browser_url + "/wan-performance/live/port/site-one/ge-0/0/0?gateway_id=aabbccddeeff&window=6h")
    assert "rx_bps: 40 bit/s" in page.get_by_test_id("wan-retained-records").inner_text()
    expect(page.get_by_test_id("wan-retained-point")).to_be_visible()
    expect(page.get_by_test_id("wan-retained-zoom-in")).to_be_disabled()
    expect(page.get_by_test_id("wan-retained-png")).to_be_disabled()
    expect(page.get_by_test_id("wan-retained-toggle-points")).to_be_disabled()
    page.get_by_test_id("wan-retained-rectangle-controls").locator("summary").click()
    expect(page.get_by_test_id("wan-retained-rectangle-apply")).to_be_disabled()
    expect(page.get_by_test_id("wan-retained-chart-status")).to_contain_text("need JavaScript")
    retained_history.read.assert_called_once()


@pytest.fixture
def rectangle_history(live_service: LiveService) -> MagicMock:
    """Keep three exact hourly records, including zero and missing measurements."""
    from datetime import timedelta

    from src.interfaces.wan_performance.domain.measurement import HourlyMeasurement, MetricMeasurement

    def read(identity, start, end):
        """Return independent scoped observations without an aggregate or extra query."""
        return tuple(
            HourlyMeasurement(
                identity,
                start + timedelta(hours=index),
                start + timedelta(hours=index, minutes=1),
                {
                    "rx_bps": MetricMeasurement(value, "bit/s"),
                    "tx_bps": MetricMeasurement(10, "bit/s"),
                    "loss": MetricMeasurement(None, "%", missing_reason="No rectangle fixture sample."),
                },
                "live",
            )
            for index, value in enumerate((0, 40, 80))
        )

    live_service.history.read.side_effect = read
    return live_service.history


class RetainedRectangleJourney:
    """Verify actual rectangle interactions without changing retained observations."""

    @staticmethod
    def open(page: Page, base: str) -> Locator:
        """Open the existing scoped port view and the independent selection controls."""
        page.goto(base + "/wan-performance/live/port/site-one/ge-0/0/0?gateway_id=aabbccddeeff&window=6h")
        chart = page.get_by_test_id("wan-retained-chart").first
        expect(chart.get_by_test_id("wan-retained-rectangle-controls")).to_have_count(1)
        chart.get_by_test_id("wan-retained-rectangle-controls").locator("summary").click()
        return chart

    @staticmethod
    def keyboard(page: Page, chart: Locator, bounds: tuple[str, ...]) -> None:
        """Apply percentage bounds through keyboard-accessible controls."""
        for name, value in zip(("left", "right", "top", "bottom"), bounds, strict=True):
            chart.get_by_test_id(f"wan-retained-rectangle-{name}").fill(value)
        chart.get_by_test_id("wan-retained-rectangle-apply").focus()
        page.keyboard.press("Enter")

    @staticmethod
    def drag(page: Page, chart: Locator) -> None:
        """Reverse a real pointer drag across two existing retained point centers."""
        chart.get_by_test_id("wan-retained-rectangle-mode").click()
        plot = chart.get_by_test_id("wan-retained-plot")
        plot.scroll_into_view_if_needed()
        corners = plot.evaluate(
            "svg => [[25,100],[0,45]].map(([x,y])=>{"
            "const point=new DOMPoint(32+x*5.88,35+y*1.3).matrixTransform(svg.getScreenCTM());"
            "return [point.x,point.y];})"
        )
        page.mouse.move(*corners[0])
        page.mouse.down()
        try:
            page.mouse.move(*corners[1], steps=8)
        finally:
            page.mouse.up()

    @staticmethod
    def selected(chart: Locator) -> None:
        """Check exact zero, units, bucket, and collection metadata without aggregation."""
        rows = chart.get_by_test_id("wan-retained-rectangle-results").locator("li").all_text_contents()
        assert len(rows) == 2
        assert rows[0].startswith("rx_bps: 0 bit/s. UTC bucket")
        assert rows[1].startswith("rx_bps: 40 bit/s. UTC bucket")
        assert all("Collected" in row for row in rows)
        records = chart.locator("xpath=ancestor::details[@data-testid='wan-retained-window']").get_by_test_id(
            "wan-retained-records"
        )
        for index, row in enumerate(rows):
            cells = records.locator("tbody tr").nth(index).locator("td")
            assert cells.nth(0).inner_text() in row
            assert cells.nth(1).inner_text() in row
        assert chart.get_by_test_id("wan-retained-point").evaluate_all(
            "points=>points.map(point=>point.getAttribute('data-rectangle-selected'))"
        ) == ["true", "true", None]

    @staticmethod
    def unchanged(page: Page, history: MagicMock, table: str, requests: list[str]) -> None:
        """Keep all records, missing reasons, tenant scope, and read counts unchanged."""
        assert page.get_by_test_id("wan-retained-records").inner_text() == table
        assert "No rectangle fixture sample." in table
        assert "org-one" in page.get_by_test_id("wan-retained-window").inner_text()
        assert "ge-0/0/0" in page.get_by_test_id("wan-retained-window").inner_text()
        identity = history.read.call_args.args[0].to_dict()
        assert {key: identity[key] for key in ("org_id", "site_id", "gateway_id", "port_name")} == {
            "org_id": "org-one",
            "site_id": "site-one",
            "gateway_id": "aabbccddeeff",
            "port_name": "ge-0/0/0",
        }
        assert history.read.call_count == 1
        history.read_samples.assert_not_called()
        history.upsert.assert_not_called()
        assert requests == []


@pytest.mark.parametrize("viewport", [(1440, 1100), (1280, 800), (390, 844)])
def test_browser_retained_rectangle_is_local_and_accessible(
    page: Page, live_browser_url: str, rectangle_history: MagicMock, viewport, wan_browser_artifacts: Path
):
    """Select exact retained points by keyboard and pointer at each supported size."""
    page.set_viewport_size({"width": viewport[0], "height": viewport[1]})
    chart = RetainedRectangleJourney.open(page, live_browser_url)
    table = page.get_by_test_id("wan-retained-records").inner_text()
    requests = []
    page.on("request", lambda request: requests.append(request.url))
    RetainedRectangleJourney.keyboard(page, chart, ("0", "20", "45", "100"))
    RetainedRectangleJourney.selected(chart)
    expect(
        page.get_by_test_id("wan-retained-chart").last.get_by_test_id("wan-retained-rectangle-results")
    ).to_be_empty()
    chart.get_by_test_id("wan-retained-rectangle-clear").click()
    RetainedRectangleJourney.drag(page, chart)
    RetainedRectangleJourney.selected(chart)
    RetainedRectangleJourney.unchanged(page, rectangle_history, table, requests)
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    page.evaluate("window.scrollTo(0,0)")
    page.screenshot(path=str(wan_browser_artifacts / f"retained-rectangle-{viewport[0]}.png"), full_page=True)


@pytest.mark.parametrize("bounds", [("", "100", "0", "100"), ("80", "20", "0", "100"), ("0", "101", "0", "100")])
def test_browser_retained_rectangle_rejects_invalid_bounds(
    page: Page, live_browser_url: str, rectangle_history: MagicMock, bounds
):
    """Preserve an existing selection when empty, reversed, or excessive bounds fail."""
    chart = RetainedRectangleJourney.open(page, live_browser_url)
    RetainedRectangleJourney.keyboard(page, chart, ("0", "20", "45", "100"))
    RetainedRectangleJourney.keyboard(page, chart, bounds)
    expect(chart.get_by_test_id("wan-retained-rectangle-status")).to_contain_text("Invalid rectangle")
    RetainedRectangleJourney.selected(chart)
    assert rectangle_history.read.call_count == 1


def test_browser_retained_rectangle_clears_after_view_or_visibility_change(
    page: Page, live_browser_url: str, rectangle_history: MagicMock
):
    """Clear geometric selections while retaining all exact records and missing values."""
    chart = RetainedRectangleJourney.open(page, live_browser_url)
    for action in ("zoom-in", "toggle-points"):
        RetainedRectangleJourney.keyboard(page, chart, ("0", "100", "0", "100"))
        expect(chart.get_by_test_id("wan-retained-rectangle-results").locator("li")).not_to_have_count(0)
        chart.get_by_test_id(f"wan-retained-{action}").click()
        expect(chart.get_by_test_id("wan-retained-rectangle-results")).to_be_empty()
        if action == "zoom-in":
            chart.get_by_test_id("wan-retained-reset").click()
    RetainedRectangleJourney.keyboard(page, chart, ("0", "100", "0", "100"))
    expect(chart.get_by_test_id("wan-retained-rectangle-status")).to_contain_text("0 existing visible points selected")
    assert rectangle_history.read.call_count == 1


@pytest.mark.parametrize("cancellation", ["escape", "pointercancel"])
def test_browser_retained_rectangle_cancels_pointer_capture(
    page: Page, live_browser_url: str, rectangle_history: MagicMock, cancellation: str
):
    """Cancel a real gesture with Escape or a browser pointer-cancellation event."""
    chart = RetainedRectangleJourney.open(page, live_browser_url)
    chart.get_by_test_id("wan-retained-rectangle-mode").click()
    point = chart.get_by_test_id("wan-retained-point").nth(1)
    point.scroll_into_view_if_needed()
    bounds = point.bounding_box()
    page.mouse.move(bounds["x"] + bounds["width"] / 2, bounds["y"] + bounds["height"] / 2)
    page.mouse.down()
    try:
        if cancellation == "escape":
            page.keyboard.press("Escape")
        else:
            chart.get_by_test_id("wan-retained-plot").evaluate(
                "svg=>svg.dispatchEvent(new PointerEvent('pointercancel', {pointerId:svg.wanRectangleStart.pointerId}))"
            )
    finally:
        page.mouse.up()
    expect(chart.get_by_test_id("wan-retained-rectangle-results")).to_be_empty()
    expect(chart.get_by_test_id("wan-retained-rectangle-status")).to_contain_text("No rectangle")
    assert chart.get_by_test_id("wan-retained-plot").evaluate("svg=>svg.wanRectangleStart === undefined")
    assert rectangle_history.read.call_count == 1


def test_browser_retained_rectangle_rejects_plot_margin_start(
    page: Page, live_browser_url: str, rectangle_history: MagicMock
):
    """Reject a gesture outside the plotted area without selecting retained records."""
    chart = RetainedRectangleJourney.open(page, live_browser_url)
    chart.get_by_test_id("wan-retained-rectangle-mode").click()
    plot = chart.get_by_test_id("wan-retained-plot")
    plot.scroll_into_view_if_needed()
    positions = plot.evaluate(
        "svg=>[[10,100],[326,100]].map(([x,y])=>{"
        "const point=new DOMPoint(x,y).matrixTransform(svg.getScreenCTM());return [point.x,point.y];})"
    )
    page.mouse.move(*positions[0])
    page.mouse.down()
    try:
        assert plot.evaluate("svg=>svg.wanRectangleStart === undefined")
        page.mouse.move(*positions[1], steps=5)
    finally:
        page.mouse.up()
    expect(chart.get_by_test_id("wan-retained-rectangle-results")).to_be_empty()
    assert rectangle_history.read.call_count == 1


def test_browser_retained_png_failure_remains_explicit(page: Page, live_browser_url: str, retained_history):
    """Keep the original table available when the browser cannot encode a PNG."""
    page.goto(live_browser_url + "/wan-performance/live/port/site-one/ge-0/0/0?gateway_id=aabbccddeeff&window=6h")
    page.evaluate(
        "() => { HTMLCanvasElement.prototype.toBlob = callback => { window.wanEncodeComplete = callback; }; }"
    )
    page.get_by_test_id("wan-retained-png").click()
    expect(page.get_by_test_id("wan-retained-png")).to_be_disabled()
    page.get_by_test_id("wan-retained-zoom-in").click()
    expect(page.get_by_test_id("wan-retained-png")).to_be_disabled()
    page.wait_for_function("typeof window.wanEncodeComplete === 'function'")
    page.evaluate("() => window.wanEncodeComplete(null)")
    expect(page.get_by_test_id("wan-retained-chart-status")).to_contain_text("PNG could not be rendered")
    assert "rx_bps: 40 bit/s" in page.get_by_test_id("wan-retained-records").inner_text()
    expect(page.get_by_test_id("wan-retained-png")).to_be_enabled()
    retained_history.read.assert_called_once()


@pytest.fixture
def sle_api():
    """Return independent synthetic SDK results without opening any network connection."""
    namespace = "src.interfaces.wan_performance.presentation.inspection.sle"
    with (
        patch(f"{namespace}.listSiteSlesMetrics") as catalog,
        patch(f"{namespace}.listSiteSleImpactedGateways") as impacted,
    ):
        catalog.return_value = MagicMock(
            status_code=200, data={"supported": ["application_health", "disabled"], "enabled": ["application_health"]}
        )
        impacted.return_value = MagicMock(
            status_code=200,
            data={
                "gateways": [
                    {
                        "gateway_mac": "aabbccddeeff",
                        "name": "Synthetic gateway",
                        "gateway_model": "SRX",
                        "degraded": 0,
                        "total": 120,
                        "duration": None,
                    }
                ],
                "total_count": 2,
            },
        )
        yield catalog, impacted


def test_sle_get_is_cache_only_and_post_uses_supported_signature(client, live_service, sle_api):
    """Keep live requests explicit, tenant-scoped, admitted, and separate from retained history."""
    catalog, impacted = sle_api
    response = client.get("/wan-performance/live/sle")
    assert response.status_code == 200
    catalog.assert_not_called()
    live_service.store.acquire.assert_not_called()
    token = re.findall(r'name="csrf_token" value="([^"]+)"', response.get_data(as_text=True))[0]
    response = client.post(
        "/wan-performance/live/sle", data={"csrf_token": token, "site_id": "site-one", "metric": "application_health"}
    )
    assert response.status_code == 200
    assert "Partial page." in response.get_data(as_text=True)
    assert "source units unknown" in response.get_data(as_text=True)
    assert "Synthetic gateway" in response.get_data(as_text=True)
    catalog.assert_called_once_with(live_service.session, "site-one", "site", "site-one")
    impacted.assert_called_once_with(
        live_service.session, "site-one", "site", "site-one", "application_health", duration="1h"
    )
    live_service.store.acquire.assert_called_once_with("org-one")
    assert live_service.store.acquire.return_value.check.call_count == 2
    live_service.history.upsert.assert_not_called()


@pytest.mark.parametrize("phase", ["catalog", "gateways"])
@pytest.mark.parametrize("status", [403, 429, 500])
@pytest.mark.usefixtures("live_service")
def test_sle_reports_upstream_errors(client, sle_api, phase, status, caplog):
    """Preserve authorization, quota, and server failures instead of showing healthy empty data."""
    catalog, impacted = sle_api
    (catalog if phase == "catalog" else impacted).return_value.status_code = status
    page = client.get("/wan-performance/live/sle").get_data(as_text=True)
    token = re.findall(r'name="csrf_token" value="([^"]+)"', page)[0]
    response = client.post(
        "/wan-performance/live/sle", data={"csrf_token": token, "site_id": "site-one", "metric": "application_health"}
    )
    assert response.status_code == 503
    assert f"HTTP {status}" in caplog.text
    assert 'data-testid="wan-sle-results"' not in response.get_data(as_text=True)


@pytest.mark.parametrize(
    "site,metric", [("other-site", "application_health"), ("site-one", "disabled"), ("site-one", "unsupported")]
)
def test_sle_rejects_unscoped_or_disabled_inputs(client, live_service, sle_api, site, metric):
    """Do not query another site or invent supported metric identifiers."""
    catalog, impacted = sle_api
    page = client.get("/wan-performance/live/sle").get_data(as_text=True)
    token = re.findall(r'name="csrf_token" value="([^"]+)"', page)[0]
    response = client.post("/wan-performance/live/sle", data={"csrf_token": token, "site_id": site, "metric": metric})
    assert response.status_code == 503
    impacted.assert_not_called()
    if site == "other-site":
        catalog.assert_not_called()
        live_service.store.acquire.assert_not_called()


def test_sle_checks_ownership_again_before_impacted_query(client, live_service, sle_api, caplog):
    """A lost lease between requests prevents the second API operation."""
    _, impacted = sle_api
    live_service.store.acquire.return_value.check.side_effect = [
        None,
        ConnectionError("Ownership lost."),
    ]
    page = client.get("/wan-performance/live/sle").get_data(as_text=True)
    token = re.findall(r'name="csrf_token" value="([^"]+)"', page)[0]
    response = client.post(
        "/wan-performance/live/sle", data={"csrf_token": token, "site_id": "site-one", "metric": "application_health"}
    )
    assert response.status_code == 503
    assert "Ownership lost" in caplog.text
    impacted.assert_not_called()


def test_sle_catalog_only_and_csrf_protection(client, live_service, sle_api):
    """Read choices without an impacted query and reject unprotected submissions."""
    catalog, impacted = sle_api
    assert client.post("/wan-performance/live/sle", data={"site_id": "site-one"}).status_code == 400
    catalog.assert_not_called()
    page = client.get("/wan-performance/live/sle").get_data(as_text=True)
    token = re.findall(r'name="csrf_token" value="([^"]+)"', page)[0]
    response = client.post("/wan-performance/live/sle", data={"csrf_token": token, "site_id": "site-one"})
    assert response.status_code == 200
    assert "application_health" in response.get_data(as_text=True)
    assert 'data-testid="wan-sle-results"' not in response.get_data(as_text=True)
    impacted.assert_not_called()


def test_sle_uses_actual_refresh_lease_without_releasing_cooldown(client, live_service, sle_api):
    """Exercise the actual lease protocol rather than inventing a mock context manager."""
    from src.interfaces.wan_performance.integration.refresh_store import RefreshLease
    from src.interfaces.wan_performance.presentation.inspection.sle import SleReader

    redis_client = MagicMock()
    redis_client.get.return_value = "synthetic-owner"
    redis_client.ttl.return_value = 300
    live_service.store.acquire.return_value = RefreshLease(redis_client, "org-one", "synthetic-owner")

    result = SleReader.read(live_service, "site-one", "application_health")

    assert result.total == 2
    assert redis_client.get.call_count == 2
    redis_client.get.assert_called_with("misthelper:wan:v1:refresh:org-one")
    redis_client.delete.assert_not_called()


@pytest.mark.parametrize(
    "body",
    [
        {"gateways": "not-an-array"},
        {"gateways": [{}]},
        {"gateways": [{"gateway_mac": "aabbccddeeff", "duration": -1}]},
        {"gateways": [{"gateway_mac": "aabbccddeeff", "total": True}]},
        {"gateways": [{"gateway_mac": "aabbccddeeff", "degraded": float("nan")}]},
        {"gateways": [], "total_count": -1},
        {"gateways": [], "total_count": True},
        {"gateways": [], "metric": "another_metric"},
        {"gateways": [{"gateway_mac": "aabbccddeeff", "name": {"not": "a label"}}]},
        {"gateways": [{"gateway_mac": "aabbccddeeff"}] * 1001},
    ],
)
def test_sle_invalid_responses_remain_unavailable(client, live_service, sle_api, body):
    """Reject malformed rows and invented totals rather than converting them into evidence."""
    _, impacted = sle_api
    impacted.return_value.data = body
    page = client.get("/wan-performance/live/sle").get_data(as_text=True)
    token = re.findall(r'name="csrf_token" value="([^"]+)"', page)[0]
    response = client.post(
        "/wan-performance/live/sle", data={"csrf_token": token, "site_id": "site-one", "metric": "application_health"}
    )
    assert response.status_code == 503
    assert 'data-testid="wan-sle-error"' in response.get_data(as_text=True)


def test_table_filter_keeps_full_scoped_history_and_csv_identity(client, live_service):
    """Filtering the table must not hide persisted detail history or widen CSV scope."""
    import csv
    import io

    path = "/wan-performance/live/port/site-one/ge-0/0/0?gateway_id=aabbccddeeff"
    response = client.get(path + "&q=NO-MATCH")
    assert response.status_code == 200
    assert "0 matching cached observations" in response.get_data(as_text=True)
    live_service.history.read.assert_called_once()
    live_service.history.read.reset_mock()
    response = client.get(path + "&download=csv")
    assert response.status_code == 200
    rows = list(csv.DictReader(io.StringIO(response.get_data(as_text=True))))
    assert {row["port_name"] for row in rows} == {"ge-0/0/0"}
    assert {row["peer_mac"] for row in rows} == {""}
    assert {row["org_id"] for row in rows} == {"org-one"}
    assert {row["gateway_id"] for row in rows} == {"aabbccddeeff"}
    assert any(row["value"] == "" and row["missing_reason"] for row in rows)
    assert "observation_hour_utc" in rows[0]
    assert response.headers["Cache-Control"] == "no-store"
    live_service.history.read.assert_not_called()
    live_service.store.acquire.assert_not_called()


def test_cached_controls_preserve_scope_and_reject_foreign_cache(client, live_service):
    """Keep canonical route arguments and refuse a cache from another organization."""
    response = client.get(
        "/wan-performance/live/port/site-one/ge-0/0/0?gateway_id=aabbccddeeff&site_id=wrong&endpoint=wrong&q=NO-MATCH"
    )
    assert response.status_code == 200
    assert "gateway_id=aabbccddeeff" in response.get_data(as_text=True)
    live_service.store.cached.return_value["org_id"] = "other-org"
    response = client.get("/wan-performance/live/?download=csv")
    assert response.status_code == 503
    assert response.mimetype != "text/csv"
    live_service.store.acquire.assert_not_called()


def test_table_paginates_and_exports_all_matching_rows(client, live_service):
    """Use deterministic identity order and export the complete filtered cached set."""
    import csv
    import io

    snapshot = live_service.store.cached.return_value
    snapshot["ports"] = [{**snapshot["ports"][0], "port_id": f"ge-0/0/{number:02}"} for number in reversed(range(12))]
    response = client.get("/wan-performance/live/?sort=port_name&direction=asc")
    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert text.count('data-testid="wan-live-port-link"') == 10
    assert "Page 1 of 2" in text
    second = client.get("/wan-performance/live/?sort=port_name&direction=asc&page=2").get_data(as_text=True)
    assert second.count('data-testid="wan-live-port-link"') == 3
    response = client.get("/wan-performance/live/?q=GE-0%2F0%2F&sort=port_name&direction=desc&download=csv")
    rows = list(csv.DictReader(io.StringIO(response.get_data(as_text=True))))
    ports = list(dict.fromkeys(row["port_name"] for row in rows))
    assert ports == sorted(ports, key=str.casefold, reverse=True)
    assert len(ports) == 13
    live_service.store.acquire.assert_not_called()


@pytest.mark.parametrize(
    "query", ["sort=rx_bps", "direction=fast", "page=0", "page=2", "page=not-a-number", "q=" + "a" * 129]
)
def test_table_rejects_invalid_controls(client, live_service, query):
    """Reject invalid table inputs without making an API request."""
    assert client.get("/wan-performance/live/?" + query).status_code == 400
    live_service.store.acquire.assert_not_called()


@pytest.mark.parametrize("text", ["=1+1", " +SUM(1,2)", "-1+2", "@SUM(1)", "\t=1"])
def test_cached_csv_neutralizes_text_formulas(text):
    """Do not let text cells become spreadsheet formulas."""
    from src.interfaces.wan_performance.presentation.inspection.table import CachedCsv

    assert CachedCsv.cell(text) == "'" + text
    assert CachedCsv.cell(None) == ""
    assert CachedCsv.cell(4.2) == 4.2


@pytest.mark.parametrize("viewport", [(1440, 1100), (1280, 800), (390, 844)])
def test_browser_sle_explicit_inspection(page: Page, live_browser_url: str, live_service, sle_api, viewport):
    """Use an independently designed SLE form with only mocked SDK responses."""
    catalog, impacted = sle_api
    page.set_viewport_size({"width": viewport[0], "height": viewport[1]})
    page.goto(live_browser_url + "/wan-performance/live/")
    page.get_by_test_id("wan-live-sle-link").click()
    expect(page.get_by_test_id("wan-sle")).to_be_visible()
    catalog.assert_not_called()
    page.get_by_test_id("wan-sle-metric").fill("application_health")
    page.get_by_test_id("wan-sle-submit").click()
    expect(page.get_by_test_id("wan-sle-results")).to_contain_text("Synthetic gateway")
    expect(page.get_by_test_id("wan-sle-coverage")).to_contain_text("Partial page")
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    assert impacted.call_count == 1
    page.get_by_test_id("wan-sle-back").click()
    expect(page.get_by_test_id("wan-live-overview")).to_be_visible()


@pytest.fixture
def sle_display_rows(sle_api):
    """Provide an independent bounded response with ties, zero, and missing values."""
    catalog, impacted = sle_api
    order = [7, 2, 6, 1, 5, 3, 4]
    impacted.return_value.data = {
        "gateways": [
            {
                "gateway_mac": f"aa00000000{number:02x}",
                "name": "Same name",
                "gateway_model": "SRX" if number % 2 else "SSR",
                "degraded": 0,
                "total": None,
                "duration": None,
            }
            for number in order
        ],
        "total_count": 12,
    }
    return catalog, impacted, [f"aa00000000{number:02x}" for number in order]


class SleDisplayJourney:
    """Keep local SLE page and sorting expectations separate from transport assertions."""

    @staticmethod
    def pages(page: Page, rows: Locator, source_order: list[str]) -> None:
        """Verify the first page, next boundary, and return to the first page."""
        expect(page.get_by_test_id("wan-sle-page")).to_contain_text("Page 1 of 2. 7 returned rows")
        expect(rows).to_have_count(5)
        assert rows.locator("td:first-child").all_text_contents() == source_order[:5]
        page.get_by_test_id("wan-sle-next").click()
        expect(rows).to_have_count(2)
        expect(page.get_by_test_id("wan-sle-next")).to_be_disabled()
        page.get_by_test_id("wan-sle-first").click()
        expect(page.get_by_test_id("wan-sle-previous")).to_be_disabled()

    @staticmethod
    def sorting(page: Page, rows: Locator, source_order: list[str]) -> None:
        """Verify every identity column, stable ties, and response-order restoration."""
        page.get_by_test_id("wan-sle-sort").select_option("mac")
        assert rows.locator("td:first-child").all_text_contents() == sorted(source_order)[:5]
        page.get_by_test_id("wan-sle-direction").select_option("desc")
        assert rows.locator("td:first-child").all_text_contents() == sorted(source_order, reverse=True)[:5]
        page.get_by_test_id("wan-sle-sort").select_option("model")
        assert rows.locator("td:first-child").all_text_contents() == [
            f"aa00000000{number:02x}" for number in [2, 6, 4, 7, 1]
        ]
        page.get_by_test_id("wan-sle-sort").select_option("name")
        assert rows.locator("td:first-child").all_text_contents() == source_order[:5]
        page.get_by_test_id("wan-sle-sort").select_option("source")
        expect(page.get_by_test_id("wan-sle-direction")).to_be_disabled()
        assert rows.locator("td:first-child").all_text_contents() == source_order[:5]

    @staticmethod
    def scope(page: Page, rows: Locator, source_order: list[str]) -> None:
        """Verify last-page values, partial coverage, and unchanged site/metric scope."""
        page.get_by_test_id("wan-sle-last").click()
        assert rows.locator("td:first-child").all_text_contents() == source_order[5:]
        expect(rows.first).to_contain_text("Unknown")
        expect(rows.first.locator("td").nth(3)).to_have_text("0")
        expect(page.get_by_test_id("wan-sle-coverage")).to_contain_text("Partial page")
        expect(page.get_by_test_id("wan-sle-site")).to_have_value("site-one")
        expect(page.get_by_test_id("wan-sle-metric")).to_have_value("application_health")


@pytest.mark.parametrize("viewport", [(1440, 1100), (1280, 800), (390, 844)])
def test_browser_sle_local_sorting_and_display_pages(
    page: Page, live_browser_url: str, sle_display_rows, viewport, wan_browser_artifacts
):
    """Sort and page only returned rows without another scoped API submission."""
    catalog, impacted, source_order = sle_display_rows
    page.set_viewport_size({"width": viewport[0], "height": viewport[1]})
    page.goto(live_browser_url + "/wan-performance/live/sle")
    page.get_by_test_id("wan-sle-metric").fill("application_health")
    page.get_by_test_id("wan-sle-submit").click()
    rows = page.get_by_test_id("wan-sle-results").locator("tbody tr:not([hidden])")
    requests = []
    page.on("request", lambda request: requests.append(request.url) if "/wan-performance/" in request.url else None)
    SleDisplayJourney.pages(page, rows, source_order)
    SleDisplayJourney.sorting(page, rows, source_order)
    SleDisplayJourney.scope(page, rows, source_order)
    catalog.assert_called_once()
    impacted.assert_called_once()
    assert requests == []
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    page.screenshot(path=str(wan_browser_artifacts / f"sle-display-{viewport[0]}.png"), full_page=True)


@pytest.mark.parametrize("count", [0, 5])
def test_browser_sle_display_page_boundaries(page: Page, live_browser_url: str, sle_display_rows, count):
    """Disable every paging boundary for empty and exactly full responses."""
    catalog, impacted, _ = sle_display_rows
    impacted.return_value.data["gateways"] = impacted.return_value.data["gateways"][:count]
    page.goto(live_browser_url + "/wan-performance/live/sle")
    page.get_by_test_id("wan-sle-metric").fill("application_health")
    page.get_by_test_id("wan-sle-submit").click()
    expect(page.get_by_test_id("wan-sle-page")).to_contain_text(f"Page 1 of 1. {count} returned rows")
    for control in ["first", "previous", "next", "last"]:
        expect(page.get_by_test_id(f"wan-sle-{control}")).to_be_disabled()
    if count == 0:
        expect(page.get_by_test_id("wan-sle-results")).to_contain_text("This does not establish healthy service")
    assert catalog.call_count == impacted.call_count == 1


@pytest.mark.browser_context_args(java_script_enabled=False)
def test_browser_sle_all_rows_survive_without_javascript(page: Page, live_browser_url: str, sle_display_rows):
    """Leave the entire bounded raw response available without client-side scripts."""
    catalog, impacted, _ = sle_display_rows
    page.goto(live_browser_url + "/wan-performance/live/sle")
    page.get_by_test_id("wan-sle-metric").fill("application_health")
    page.get_by_test_id("wan-sle-submit").click()
    assert page.get_by_test_id("wan-sle-results").locator("tbody tr").count() == 7
    expect(page.get_by_test_id("wan-sle-next")).to_be_disabled()
    expect(page.get_by_test_id("wan-sle-sort")).to_be_disabled()
    expect(page.get_by_test_id("wan-sle-page")).to_contain_text("All returned rows remain in the table")
    catalog.assert_called_once()
    impacted.assert_called_once()


@pytest.mark.parametrize("viewport", [(1440, 1100), (1280, 800), (390, 844)])
def test_browser_cached_table_controls(page: Page, live_browser_url: str, live_service, viewport):
    """Navigate pages, sort identifiers, filter rows, and download the scoped cached CSV."""
    snapshot = live_service.store.cached.return_value
    page.set_viewport_size({"width": viewport[0], "height": viewport[1]})
    snapshot["ports"] = [{**snapshot["ports"][0], "port_id": f"ge-0/0/{number:02}"} for number in range(12)]
    page.goto(live_browser_url + "/wan-performance/live/")
    expect(page.get_by_test_id("wan-table-page")).to_contain_text("Page 1 of 2")
    page.get_by_test_id("wan-table-next").click()
    expect(page.get_by_test_id("wan-table-page")).to_contain_text("Page 2 of 2")
    page.get_by_test_id("wan-table-filter").fill("ge-0/0/11")
    page.get_by_test_id("wan-table-sort").select_option("port_name")
    page.get_by_test_id("wan-table-direction").select_option("desc")
    page.get_by_test_id("wan-table-apply").click()
    expect(page.get_by_test_id("wan-table-page")).to_contain_text("1 matching cached observations")
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    with page.expect_download() as downloaded:
        page.get_by_test_id("wan-table-export").click()
    assert downloaded.value.suggested_filename == "cached-wan-observations.csv"
    live_service.store.acquire.assert_not_called()


def test_second_gateway_refresh_keeps_selected_site_and_gateway(client, live_service):
    """The gateway journey can refresh another cached gateway rather than the first discovered device."""
    from src.interfaces.wan_performance.domain.identity import GatewayIdentity, SiteIdentity

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
    from src.interfaces.wan_performance.domain.identity import GatewayIdentity, SiteIdentity

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
    assert "complete 10-minute sample intervals above each threshold" in text


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
    assert "Current cached state does not establish availability duration" in text


def test_peer_history_keeps_old_missing_mos_readable_after_new_poll(client, live_service):
    """Render retained unknown MOS beside a new score without changing old records."""
    from dataclasses import replace
    from datetime import timedelta

    from src.interfaces.wan_performance.collection.snapshot_records import SnapshotRecords
    from src.interfaces.wan_performance.domain.measurement import MetricMeasurement

    snapshot = live_service.store.cached.return_value
    snapshot["peers"][0]["mos"] = 4.2
    current = SnapshotRecords.build(snapshot)[1]
    retained = replace(
        current,
        hour_start_utc=current.hour_start_utc - timedelta(days=1),
        collected_at_utc=current.collected_at_utc - timedelta(days=1),
        metrics={"mos": MetricMeasurement(None, "unknown", missing_reason="Unit unknown.")},
    )
    live_service.history.read.return_value = (retained, current)

    response = client.get("/wan-performance/live/vpn/site-one/11:22:33:44:55:66")

    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert "mos: mean 4.2, maximum 4.2, observed p95 4.2 score" in text
    assert "History is unavailable." not in text
    assert retained.metrics["mos"].unit == "unknown"


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
    from src.interfaces.wan_performance.domain.identity import GatewayIdentity, SiteIdentity

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


def test_port_history_refresh_requires_csrf(client, live_service):
    """Keep the separate selected-port history operation under portal protection."""
    response = client.post("/wan-performance/live/refresh-port")
    assert response.status_code == 400
    live_service.store.acquire.assert_not_called()


def test_peer_history_refresh_requires_csrf(client, live_service):
    """Keep the selected-peer read behind the portal's CSRF protection."""
    response = client.post("/wan-performance/live/refresh-peer")
    assert response.status_code == 400
    live_service.store.acquire.assert_not_called()


@pytest.mark.parametrize("invalid", ["missing", "malformed", "unknown", "store", "quota"])
def test_port_history_refresh_errors_are_explicit_without_snapshot_change(client, live_service, invalid):
    """Refuse unverified targets and unavailable stores before claiming success."""
    page = client.get("/wan-performance/live/port/site-one/ge-0/0/0?gateway_id=aabbccddeeff").get_data(as_text=True)
    token = re.findall(r'name="csrf_token" value="([^"]+)"', page)[0]
    fields = {"csrf_token": token, "gateway_id": "aabbccddeeff", "site_id": "site-one", "port_name": "ge-0/0/0"}
    if invalid == "missing":
        fields.pop("gateway_id")
    elif invalid == "malformed":
        fields["port_name"] = "../invalid"
    elif invalid == "unknown":
        fields["port_name"] = "other-port"
    elif invalid == "store":
        live_service.history = None
    else:
        live_service.store.acquire.side_effect = ConnectionError("quota")
    response = client.post("/wan-performance/live/refresh-port", data=fields)
    assert response.status_code == 503
    assert "Port history refresh failed" in response.get_data(as_text=True)
    live_service.store.publish.assert_not_called()
    if invalid != "quota":
        live_service.store.acquire.assert_not_called()


def test_browser_selected_port_history_refresh(page: Page, live_browser_url: str, live_service):
    """Submit the actual port form without refreshing organization snapshot pages."""
    from src.interfaces.wan_performance.domain.identity import CircuitIdentity, GatewayIdentity, SiteIdentity

    target = CircuitIdentity(GatewayIdentity(SiteIdentity("org-one", "site-one"), "aabbccddeeff"), "ge-0/0/0")
    page.goto(f"{live_browser_url}/wan-performance/live/port/site-one/ge-0/0/0?gateway_id=aabbccddeeff")
    with patch.object(live_service, "refresh_port", return_value=1) as refresh_port:
        page.get_by_test_id("wan-live-port-history-refresh").click()
        expect(page.get_by_test_id("wan-live-port")).to_be_visible()
    refresh_port.assert_called_once_with(target)
    live_service.store.publish.assert_not_called()


def test_browser_selected_peer_history_refresh(page: Page, live_browser_url: str, live_service):
    """Submit a peer history request with the exact cached path identifiers."""
    from src.interfaces.wan_performance.collection.snapshot_records import SnapshotRecords

    target = SnapshotRecords.build(live_service.store.cached.return_value)[1].identity
    page.goto(
        f"{live_browser_url}/wan-performance/live/vpn/site-one/{target.peer_mac}" f"?path_key={target.tunnel_identity}"
    )
    with patch.object(live_service, "refresh_peer", return_value=1) as refresh_peer:
        page.get_by_test_id("wan-live-peer-history-refresh").click()
        expect(page.get_by_test_id("wan-live-peer")).to_be_visible()
    refresh_peer.assert_called_once_with(target)
    live_service.store.publish.assert_not_called()


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
    from src.interfaces.wan_performance.collection.snapshot_records import SnapshotRecords

    records = SnapshotRecords.build(live_service.store.cached.return_value)
    live_service.history.read.return_value = (records[0],)
    response = client.get("/wan-performance/live/port/site-one/ge-0/0/0?gateway_id=aabbccddeeff")
    assert response.status_code == 200
    assert "daily: 2024-01-01" in response.get_data(as_text=True)
    assert "mean 40.0" in response.get_data(as_text=True)


def test_selected_port_quality_metrics_render_in_history(client, live_service):
    """Show persisted hourly link-health metrics on the selected-port detail page."""
    from datetime import UTC, datetime

    from src.interfaces.wan_performance.collection.snapshot_records import SnapshotRecords

    snapshot = live_service.store.cached.return_value
    gateway = {key: snapshot["ports"][0][key] for key in ("org_id", "site_id", "mac")}
    snapshot["insights"] = {
        "gateway": gateway,
        "port_id": "ge-0/0/0",
        "samples": [
            {
                "metric": name,
                "unit": unit,
                "value": value,
                "hour_start_utc": datetime(2024, 1, 1, 12, tzinfo=UTC).isoformat(),
            }
            for name, unit, value in (
                ("rx_bps", "bit/s", 100),
                ("tx_bps", "bit/s", 200),
                ("avg_loss_pct", "%", 0.25),
                ("avg_jitter_ms", "ms", 4.5),
                ("avg_latency_ms", "ms", 33.3),
                ("utilization_pct", "%", 25),
                ("congestion_minutes_over_70_pct", "min", 20),
                ("congestion_minutes_over_80_pct", "min", 10),
                ("congestion_minutes_over_90_pct", "min", 0),
                ("up_minutes", "min", 50),
                ("down_minutes", "min", 10),
                ("flap_count", "count", 2),
            )
        ],
    }
    live_service.history.read.return_value = SnapshotRecords.build(snapshot)

    response = client.get("/wan-performance/live/port/site-one/ge-0/0/0?gateway_id=aabbccddeeff")

    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert "avg_loss_pct: 0.25 %" in text
    assert "avg_jitter_ms: 4.5 ms" in text
    assert "avg_latency_ms: 33.3 ms" in text
    assert "up_minutes: 50 min" in text
    assert "congestion_minutes_over_70_pct: 20 min" in text


def test_threshold_history_displays_observation_counts_not_duration(client, live_service):
    """Keep sparse hourly threshold evidence distinct from measured congestion hours."""
    from src.interfaces.wan_performance.collection.snapshot_records import SnapshotRecords

    live_service.store.cached.return_value["ports"][0].update(speed=100, rx_bps=80000000, tx_bps=90000000)
    records = SnapshotRecords.build(live_service.store.cached.return_value)
    live_service.history.read.return_value = (records[0],)
    response = client.get("/wan-performance/live/port/site-one/ge-0/0/0?gateway_id=aabbccddeeff")
    text = response.get_data(as_text=True)
    assert response.status_code == 200
    assert 'data-testid="wan-live-threshold-observations"' in text
    assert "above 70%" in text
    assert "1 valid hourly observations" in text
    assert "not measured congestion duration" in text


def test_status_history_displays_sampled_state_not_availability(client, live_service):
    """Show persisted status evidence without claiming complete availability."""
    from src.interfaces.wan_performance.collection.snapshot_records import SnapshotRecords

    live_service.store.cached.return_value["ports"][0]["up"] = True
    records = SnapshotRecords.build(live_service.store.cached.return_value)
    live_service.history.read.return_value = (records[0],)

    response = client.get("/wan-performance/live/port/site-one/ge-0%2F0%2F0?gateway_id=aabbccddeeff")

    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert 'data-testid="wan-live-state-observations"' in text
    assert "sampled state, not measured availability" in text
    assert re.search(r"1 up and 0 down\s+observations of 1 known states", text)
    assert re.search(r"across\s+\d+\s+expected hours", text)


def test_live_link_event_view_renders_missing_evidence_as_unknown(client, live_service):
    """Render missing event evidence without adding None values or claiming zero."""
    from dataclasses import replace

    from src.interfaces.wan_performance.collection.snapshot_records import SnapshotRecords
    from src.interfaces.wan_performance.domain.measurement import MetricMeasurement

    record = SnapshotRecords.build(live_service.store.cached.return_value)[0]
    live_service.history.read.return_value = (
        replace(
            record,
            metrics={
                "up_minutes": MetricMeasurement(None, "min", missing_reason="The event search is incomplete."),
                "down_minutes": MetricMeasurement(None, "min", missing_reason="The event search is incomplete."),
                "flap_count": MetricMeasurement(None, "count", missing_reason="The event search is incomplete."),
            },
        ),
    )

    response = client.get("/wan-performance/live/port/site-one/ge-0/0/0?gateway_id=aabbccddeeff")

    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert 'data-testid="wan-live-link-event-summary"' in text
    assert "Known state duration: Unknown." in text
    assert "Up: Unknown minutes." in text
    assert "Down: Unknown minutes." in text
    assert "Matching transitions: Unknown." in text


def test_gateway_history_remains_visible_after_ordinary_refresh(client, live_service, tmp_path):
    """Keep scoped gateway history visible after the cache receives ordinary port rows."""
    import sqlite3
    from datetime import UTC, datetime, timedelta

    from src.interfaces.wan_performance.domain.identity import GatewayIdentity, SiteIdentity
    from src.interfaces.wan_performance.integration.sqlite_history import SQLiteHistory

    path = tmp_path / "application.db"
    sqlite3.connect(path).close()
    live_service.history = SQLiteHistory(path)
    instant = datetime.now(UTC)
    hour = instant.replace(minute=0, second=0, microsecond=0)
    gateway_snapshot = {
        "org_id": "org-one",
        "provenance": "live",
        "collected_at_utc": instant.isoformat(),
        "ports": [],
        "peers": [],
        "insights": {
            "gateway": {
                "org_id": "org-one",
                "site_id": "site-one",
                "mac": "aabbccddeeff",
                "id": "00000000-0000-0000-0000-000000000001",
            },
            "samples": [
                {"metric": name, "value": value, "unit": "bit/s", "hour_start_utc": hour.isoformat()}
                for name, value in (("rx_bps", 0), ("tx_bps", 10))
            ],
        },
    }
    ordinary_snapshot = {
        "org_id": "org-one",
        "provenance": "live",
        "collected_at_utc": (instant + timedelta(minutes=1)).isoformat(),
        "ports": [
            {
                "org_id": "org-one",
                "site_id": "site-one",
                "mac": "aabbccddeeff",
                "port_id": "ge-0/0/0",
            }
        ],
        "peers": [],
        "insights": {"samples": []},
    }
    live_service.store.publish.side_effect = lambda org_id, snapshot: setattr(
        live_service.store.cached, "return_value", snapshot
    )
    target = GatewayIdentity(SiteIdentity("org-one", "site-one"), "aabbccddeeff")
    with patch(
        "src.interfaces.wan_performance.collection.live_service.SnapshotClient.collect",
        side_effect=(gateway_snapshot, ordinary_snapshot),
    ) as collect:
        live_service.refresh(target)
        live_service.refresh()

    response = client.get("/wan-performance/live/gateway/aabbccddeeff?site_id=site-one")

    assert collect.call_count == 2
    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert f"daily: {hour:%Y-%m-%d}" in text
    assert "mean 0.0" in text


def test_gateway_history_rejects_ambiguous_or_foreign_gateway_identity(live_service):
    """Refuse gateway history when selected records cross gateway or organization scope."""
    from dataclasses import replace

    from src.interfaces.wan_performance.collection.snapshot_records import SnapshotRecords
    from src.interfaces.wan_performance.domain.identity import GatewayIdentity, SiteIdentity
    from src.interfaces.wan_performance.presentation.live_routes import LiveHistory

    record = SnapshotRecords.build(live_service.store.cached.return_value)[0]
    gateways = (
        GatewayIdentity(SiteIdentity("org-one", "site-one"), "aabbccddeeff"),
        GatewayIdentity(SiteIdentity("org-one", "site-two"), "112233445566"),
    )
    ambiguous = tuple(replace(record, identity=gateway) for gateway in gateways)
    periods, error = LiveHistory.read(live_service, ambiguous, "gateway")
    assert periods == ()
    assert error == "Select records for exactly one full gateway identity to read history."

    foreign = (replace(record, identity=GatewayIdentity(SiteIdentity("org-two", "site-one"), "aabbccddeeff")),)
    periods, error = LiveHistory.read(live_service, foreign, "gateway")
    assert periods == ()
    assert error == "Select records for exactly one full gateway identity to read history."
    live_service.history.read.assert_not_called()
