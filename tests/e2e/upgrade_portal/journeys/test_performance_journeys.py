"""Measure upgrade portal browser and API performance."""

from __future__ import annotations

import json
import logging  # Record the measured form save and its explicit target count.
import math
import re  # Replace dynamic run and site identifiers in ranked paths.
import statistics
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any  # Type the browser preparation without changing optional imports.

import pytest

from tests.support.upgrade_portal_e2e.model_version_picker import ModelVersionPicker  # Measure actual device controls.

if TYPE_CHECKING:  # Preserve the existing missing-browser capability reason.
    from playwright.sync_api import Page  # Read actual browser request and page values.

sync_api = pytest.importorskip("playwright.sync_api", reason="Playwright is not installed.")

REPO_ROOT = Path(__file__).parents[4]  # Keep artifacts in the worktree, not the pytest run directory.
ARTIFACT_ROOT = REPO_ROOT / "test-artifacts" / "upgrade-portal-journeys" / "upj-perf"
RESULTS_PATH = ARTIFACT_ROOT / "perf-results.json"
SITE_ID = "22222222-2222-2222-2222-222222222222"
SECOND_SITE_ID = "33333333-3333-3333-3333-333333333333"
PREPARED_RUN_ID = "e2e-prepared-run-0001"
START_READY_RUN_ID = "e2e-start-ready-run-0001"
STOPPED_RUN_ID = "e2e-stopped-run-0001"  # This seeded record renders the stop control without a write.
PRE_CAPTURE_ID = "e2e-capture-pre-0001"
POST_CAPTURE_ID = "e2e-capture-post-0001"
TIER3_CAPTURE_ID = "e2e-capture-tier3-0001"
IDENTIFIER_PATTERN = re.compile(  # Local IDs must not make one report path differ from the next.
    r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}|e2e-[a-z0-9-]+"
)


def _summary(values: list[float]) -> dict[str, float]:
    """Return stable summary values for one timing series."""
    return {
        "median_ms": round(statistics.median(values), 3),
        "p95_ms": _percentile(values, 0.95),
        "max_ms": round(max(values), 3),
    }  # Keep the median and the slow tail.


def _percentile(values: list[float], percentile: float) -> float:
    """Return one nearest-rank percentile from a non-empty timing sample."""
    if not values:  # A missing sample cannot produce a ranking.
        raise ValueError("A performance percentile needs at least one sample.")
    rank = max(1, math.ceil(percentile * len(values)))  # Use a stable nearest-rank index.
    return round(sorted(values)[rank - 1], 3)  # Keep milliseconds to three decimal places.


def _path_template(path: str) -> str:
    """Replace each stand-in or UUID identifier with a stable placeholder."""
    return IDENTIFIER_PATTERN.sub("{identifier}", path)  # Keep rankings comparable across local runs.


def _rank_entries(entries: list[dict[str, Any]], method_key: str, duration_key: str) -> list[dict[str, Any]]:
    """Return the ten slowest pages or API calls by the 95th percentile."""
    ranked = [
        {
            "name": str(entry.get("name", "")),
            "method": str(entry.get(method_key, "GET")),
            "path_template": _path_template(str(entry["path"])),
            "p50_ms": float(entry[duration_key]["median_ms"]),
            "p95_ms": float(entry[duration_key]["p95_ms"]),
            "max_ms": float(entry[duration_key]["max_ms"]),
            "count": int(entry["count"]),
            "cloud_calls_p95": 0,
        }
        for entry in entries
    ]  # Convert full samples into the stable report contract.
    ranked.sort(key=lambda entry: entry["p95_ms"], reverse=True)  # Put the slowest route first.
    return ranked[:10]  # The report names only the ten slowest entries.


def _rank_performance(pages: list[dict[str, Any]], apis: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the ranked performance report for the local stand-in fleet."""
    page_entries = [
        {**page, "method": "GET", "count": len(page["wall_samples_ms"]), "wall": _summary(page["wall_samples_ms"])}
        for page in pages
    ]  # Rank pages by complete navigation time.
    api_entries = [
        {**api, "count": len(api["elapsed_samples_ms"])} for api in apis
    ]  # Preserve API timing summaries from the HTTP exchanges.
    return {
        "stand_in": {
            "pages": _rank_entries(page_entries, "method", "wall"),
            "api_calls": _rank_entries(api_entries, "method", "server_time"),
        }
    }  # The tests make no calls to a Mist cloud.


def _poll_cost_ms_per_minute(apis: list[dict[str, Any]], intervals: dict[str, int]) -> dict[str, float]:
    """Estimate loopback server time for each configured polling route."""
    return {
        api["name"]: round((60.0 / intervals[api["name"]]) * api["server_time"]["median_ms"], 3)
        for api in apis
        if api["name"] in intervals and intervals[api["name"]] > 0
    }  # Count polling calls per minute, then multiply by median milliseconds.


def _assert_ranked_report(performance: dict[str, Any]) -> None:
    """Check ranking length, required fields, and descending p95 order."""
    for kind in ("pages", "api_calls"):  # Verify both report categories.
        entries = performance["stand_in"][kind]  # The single local test fleet.
        assert 1 <= len(entries) <= 10  # Rank all available entries, up to ten.
        assert [entry["p95_ms"] for entry in entries] == sorted(
            (entry["p95_ms"] for entry in entries), reverse=True
        )  # The slowest entry must appear first.
        for entry in entries:  # Check the contract for each route.
            assert {
                "name",
                "method",
                "path_template",
                "p50_ms",
                "p95_ms",
                "max_ms",
                "count",
                "cloud_calls_p95",
            } <= set(entry)


def test_performance_report_ranks_pages_and_api_calls_by_p95() -> None:
    """Keep the slowest page and API at the top of the local report."""
    pages = [
        {"path": "/fast", "wall_samples_ms": [2.0, 3.0, 4.0]},
        {"path": "/slow", "wall_samples_ms": [5.0, 10.0, 30.0]},
    ]
    apis = [
        {
            "method": "GET",
            "path": "/api/fast",
            "server_time": {"median_ms": 3.0, "p95_ms": 5.0, "max_ms": 5.0},
            "elapsed_samples_ms": [2.0, 5.0],
        },
        {
            "method": "POST",
            "path": "/api/slow",
            "server_time": {"median_ms": 10.0, "p95_ms": 30.0, "max_ms": 30.0},
            "elapsed_samples_ms": [5.0, 30.0],
        },
    ]
    report = _rank_performance(pages, apis)  # Build the same structure as the browser report.
    _assert_ranked_report(report)  # Enforce the shape and order for both categories.
    assert report["stand_in"]["pages"][0]["path_template"] == "/slow"
    assert report["stand_in"]["api_calls"][0]["path_template"] == "/api/slow"
    assert _path_template("/runs/e2e-stopped-run-0001") == "/runs/{identifier}"  # Hide local job identities.
    assert _poll_cost_ms_per_minute(
        [{"name": "capture-status", "server_time": {"median_ms": 5.0}}],  # One five-millisecond call.
        {"capture-status": 3},  # The route runs every three seconds.
    ) == {
        "capture-status": 100.0
    }  # Twenty calls cost one hundred milliseconds per minute.


def _install_monitors(page: Any, bucket: dict[str, list[str]]) -> None:
    """Collect browser faults while each performance page opens."""
    page.on(
        "console",
        lambda msg: bucket["console"].append(msg.text) if msg.type == "error" else None,
    )  # Keep only console errors.
    page.on("pageerror", lambda err: bucket["page_errors"].append(str(err)))  # Keep script error evidence.
    page.on("requestfailed", lambda req: bucket["failed_requests"].append(req.url))  # Keep failed request URLs.
    page.on(
        "response", lambda res: bucket["bad_responses"].append(f"{res.status} {res.url}") if res.status >= 400 else None
    )  # Keep bad status URLs.


def _navigation_sample(page: Any, path: str) -> dict[str, Any]:
    """Open one page once and return browser timing and resource data."""
    started = time.perf_counter()  # Measure the complete browser navigation wall time.
    response = page.goto(path, wait_until="load")  # Wait for page resources, not only the HTML.
    elapsed_ms = (time.perf_counter() - started) * 1000.0  # Convert wall time to milliseconds.
    status = response.status if response is not None else 0  # Record a missing response as status zero.
    timing = page.evaluate("""() => {
            const nav = performance.getEntriesByType('navigation')[0] || {};
            const resources = performance.getEntriesByType('resource') || [];
            const longTasks = performance.getEntriesByType('longtask') || [];
            return {
                ttfb: nav.responseStart || 0,
                domContentLoaded: nav.domContentLoadedEventEnd || 0,
                load: nav.loadEventEnd || 0,
                transferSize: nav.transferSize || 0,
                requestCount: resources.length + 1,
                resources: resources.map((entry) => ({
                    name: entry.name,
                    duration: entry.duration || 0,
                    transferSize: entry.transferSize || 0,
                    encodedBodySize: entry.encodedBodySize || 0,
                })).sort((left, right) => right.duration - left.duration).slice(0, 10),
                longTasks: longTasks.map((entry) => ({duration: entry.duration || 0, name: entry.name || ''})),
            };
        }""")  # Read the browser performance buffer for this page.
    return {"path": path, "status": status, "wall_ms": elapsed_ms, **timing}  # Merge all timing fields.


def _measure_page(page: Any, name: str, path: str) -> dict[str, Any]:
    """Measure one page five times and save one screenshot."""
    samples = [_navigation_sample(page, path) for _index in range(5)]  # Repeat to reduce random noise.
    screenshot_path = ARTIFACT_ROOT / f"{name}.png"  # One full-page screenshot per page.
    page.screenshot(path=str(screenshot_path), full_page=True)  # Save visual evidence for manual review.
    return {
        "name": name,
        "path": path,
        "screenshot": str(screenshot_path),
        "status_codes": [sample["status"] for sample in samples],
        "ttfb": _summary([float(sample["ttfb"]) for sample in samples]),
        "domContentLoaded": _summary([float(sample["domContentLoaded"]) for sample in samples]),
        "load": _summary([float(sample["load"]) for sample in samples]),
        "wall": _summary([float(sample["wall_ms"]) for sample in samples]),
        "transferSize": _summary([float(sample["transferSize"]) for sample in samples]),
        "requestCount": _summary([float(sample["requestCount"]) for sample in samples]),
        "largestResources": samples[-1]["resources"],
        "longTasks": samples[-1]["longTasks"],
        "wall_samples_ms": [float(sample["wall_ms"]) for sample in samples],
    }  # Keep the full evidence needed by the parent task.


def _api_call(request_context: Any, path: str) -> dict[str, Any]:
    """Measure one read-only API request through the browser request context."""
    started = time.perf_counter()  # Measure only this HTTP exchange.
    response = request_context.get(path)  # Use the signed browser request context.
    elapsed_ms = (time.perf_counter() - started) * 1000.0  # Convert wall time to milliseconds.
    return {"status": response.status, "elapsed_ms": elapsed_ms, "bytes": len(response.body())}  # Save response size.


def _measure_api(request_context: Any, name: str, path: str) -> dict[str, Any]:
    """Measure one read-only JSON API with twenty calls."""
    samples = [_api_call(request_context, path) for _index in range(20)]  # Repeat enough to see tails.
    return {
        "name": name,
        "method": "GET",
        "path": path,
        "status_codes": [sample["status"] for sample in samples],
        "server_time": _summary([float(sample["elapsed_ms"]) for sample in samples]),
        "bytes": _summary([float(sample["bytes"]) for sample in samples]),
        "elapsed_samples_ms": [float(sample["elapsed_ms"]) for sample in samples],
    }  # Keep only summaries and status proof.


def _read_static_asset(request_context: Any, path: str) -> dict[str, Any]:
    """Read one static asset and record cache and size headers."""
    response = request_context.get(path)  # Static files travel through the same server under test.
    body = response.body()  # Body length is the transfer-free size on loopback.
    return {
        "path": path,
        "status": response.status,
        "bytes": len(body),
        "cache_control": response.headers.get("cache-control", ""),
        "etag": response.headers.get("etag", ""),
        "content_encoding": response.headers.get("content-encoding", ""),
    }  # Keep cache and compression evidence.


def _prepare_multisite(page: Page) -> None:
    """Save one local organization plan and stop before the write gate."""
    page.goto("/select/mode", wait_until="domcontentloaded")  # Open the mode chooser with the signed session.
    page.get_by_test_id("mode-multi-site").check()  # Choose the organization workflow.
    page.get_by_test_id("mode-continue").click()  # Store the mode in the signed session.
    page.wait_for_url("**/select/site")  # Wait until the site list opens.
    page.get_by_test_id(f"site-select-{SITE_ID}").check()  # Select the first stand-in site.
    page.get_by_test_id(f"site-select-{SECOND_SITE_ID}").check()  # Select the second stand-in site.
    page.get_by_test_id("multi-site-continue").click()  # Store the selected sites.
    page.wait_for_url("**/upgrade/org/options")  # Wait until the organization options page opens.
    ModelVersionPicker(page).select("0.15.1", 6)  # Require every expected device before measuring the job.
    logging.info("Save the six-device performance plan")  # Record the request before measuring the same body.
    with page.expect_request("**/api/org-upgrades/options") as sent:  # Capture the real per-device submit.
        page.get_by_test_id("org-upgrade-review").click()  # Save the organization options.
    body = sent.value.post_data_json  # Reuse explicit MAC/version pairs instead of a legacy family payload.
    assert isinstance(body, dict), "The performance plan must send a JSON object."  # Type the request boundary.
    logging.debug("The performance plan sent %s targets", len(body["targets"]))  # Report only the target count.
    assert len(body["targets"]) == 6  # Preserve all six device choices in later option-save measurements.
    page.wait_for_url("**/upgrade/org/confirm")  # Wait until the confirmation page opens.
    return None  # Stop before the typed start gate.


def _poll_intervals() -> dict[str, int]:
    """Return the portal.js poll intervals in seconds."""
    return {
        "capture-status": 3,
        "run-status": 30,
        "org-status": 30,
        "heartbeat": 60,
    }  # Read from portal.js comments and data attributes.


# WHY: One journey measures about 15 pages 5 times and about 8 APIs 20 times. It
# needs its own server and a longer budget than the 300-second default, or the
# thread timeout ends the whole shared pytest process (issue #3200).
@pytest.mark.fresh_server
@pytest.mark.timeout(1800)
def test_upgrade_portal_performance_measurement(firmware_operator_page: Any) -> None:
    """Measure browser pages, JSON APIs, static assets, and poll cost."""
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)  # Ensure the evidence directory exists.
    page = firmware_operator_page  # Firmware operator can submit the stand-in organization job.
    faults: dict[str, list[str]] = {
        "console": [],
        "page_errors": [],
        "failed_requests": [],
        "bad_responses": [],
    }  # Collect browser faults.
    _install_monitors(page, faults)  # Attach the browser fault collectors.
    _prepare_multisite(page)  # Save a local options plan without starting an upgrade.
    pages = [
        ("select-org", "/select/org"),
        ("select-mode", "/select/mode"),
        ("select-site", "/select/site"),
        ("inventory", f"/select/site/{SITE_ID}"),
        ("capture", f"/captures/new?site_id={SITE_ID}"),
        ("options", f"/runs/{PREPARED_RUN_ID}/options"),
        ("confirm", f"/runs/{PREPARED_RUN_ID}/confirm"),
        ("run", f"/runs/{START_READY_RUN_ID}"),
        ("stop", f"/runs/{STOPPED_RUN_ID}"),
        ("org-options", "/upgrade/org/options"),
        ("org-confirm", "/upgrade/org/confirm"),
        ("history", f"/history?site_id={SITE_ID}"),
        ("compare-select", "/compare"),
        ("compare", f"/compare?before={PRE_CAPTURE_ID}&after={POST_CAPTURE_ID}"),
    ]  # Cover every requested page family.
    page_results = [_measure_page(page, name, path) for name, path in pages]  # Measure all HTML pages.
    request_context = page.request  # Reuse the signed request context for JSON APIs.
    apis = [
        _measure_api(request_context, "sites", "/api/sites"),
        _measure_api(request_context, "inventory", f"/api/sites/{SITE_ID}/inventory"),
        _measure_api(request_context, "run-status", f"/api/runs/{START_READY_RUN_ID}/status"),
        _measure_api(request_context, "run-versions", f"/api/runs/{PREPARED_RUN_ID}/versions"),
        _measure_api(request_context, "capture-status", f"/api/captures/{TIER3_CAPTURE_ID}/status"),
    ]  # Cover JSON readers and control-like paths.
    static_assets = [
        _read_static_asset(request_context, "/static/js/portal.js"),
        _read_static_asset(request_context, "/static/css/portal.css"),
        _read_static_asset(request_context, "/static/vendor/bootstrap/bootstrap.bundle.min.js"),
    ]  # Measure the shipped JavaScript and CSS assets.
    intervals = _poll_intervals()  # Use the script poll settings for cost math.
    poll_cost = _poll_cost_ms_per_minute(apis, intervals)  # Compute server time per minute of polling.
    performance = _rank_performance(page_results, apis)  # Name the slowest stand-in pages and API calls.
    _assert_ranked_report(performance)  # Fail if the report loses its ranking contract.
    RESULTS_PATH.write_text(
        json.dumps(
            {
                "browser_pages": page_results,
                "apis": apis,
                "static_assets": static_assets,
                "poll_intervals_seconds": intervals,
                "poll_cost_ms_per_minute": poll_cost,
                "performance": performance,
                "browser_faults": faults,
                "budgets": {"ttfb_ms": 200, "load_ms": 1000, "api_median_ms": 100, "asset_kb": 250},
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )  # Write the raw browser and API evidence.
    assert all(status == 200 for result in page_results for status in result["status_codes"])  # Require valid pages.
    assert all(status == 200 for result in apis for status in result["status_codes"])  # Require valid API samples.
    assert all(not values for values in faults.values())  # Keep the performance journey free of browser faults.
    assert RESULTS_PATH.exists()  # Prove the measurement artifact exists.
