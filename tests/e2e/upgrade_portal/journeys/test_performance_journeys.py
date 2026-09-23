"""Measure upgrade portal browser and API performance."""

from __future__ import annotations

import json
import statistics
import time
from pathlib import Path
from typing import Any

import pytest

sync_api = pytest.importorskip("playwright.sync_api", reason="Playwright is not installed.")

REPO_ROOT = Path(__file__).parents[4]  # Keep artifacts in the worktree, not the pytest run directory.
ARTIFACT_ROOT = REPO_ROOT / "data" / "test-artifacts" / "upgrade-portal-journeys" / "upj-perf"
RESULTS_PATH = ARTIFACT_ROOT / "perf-results.json"
SITE_ID = "22222222-2222-2222-2222-222222222222"
SECOND_SITE_ID = "33333333-3333-3333-3333-333333333333"
ORG_ID = "11111111-1111-1111-1111-111111111111"
PREPARED_RUN_ID = "e2e-prepared-run-0001"
START_READY_RUN_ID = "e2e-start-ready-run-0001"
PRE_CAPTURE_ID = "e2e-capture-pre-0001"
POST_CAPTURE_ID = "e2e-capture-post-0001"
TIER3_CAPTURE_ID = "e2e-capture-tier3-0001"


def _summary(values: list[float]) -> dict[str, float]:
    """Return stable summary values for one timing series."""
    return {"median_ms": round(statistics.median(values), 3), "max_ms": round(max(values), 3)}  # Keep output small.


def _install_monitors(page: Any, bucket: dict[str, list[str]]) -> None:
    """Collect browser faults while each performance page opens."""
    page.on("console", lambda msg: bucket["console"].append(f"{msg.type}: {msg.text}"))  # Keep console evidence.
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
    }  # Keep the full evidence needed by the parent task.


def _api_call(request_context: Any, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    """Measure one API request through the browser request context."""
    started = time.perf_counter()  # Measure only this HTTP exchange.
    if method == "GET":  # GET calls read no request body.
        response = request_context.get(path)  # Use the signed browser request context.
    elif method == "DELETE":  # DELETE calls release a lock after lock tests.
        response = request_context.delete(path)  # Use the signed browser request context.
    else:  # POST calls send JSON bodies for lock, heartbeat, and controls.
        response = request_context.post(
            path, data=json.dumps(body or {}), headers={"Content-Type": "application/json"}
        )  # Send JSON.
    elapsed_ms = (time.perf_counter() - started) * 1000.0  # Convert wall time to milliseconds.
    return {"status": response.status, "elapsed_ms": elapsed_ms, "bytes": len(response.body())}  # Save response size.


def _measure_api(
    request_context: Any, name: str, method: str, path: str, body: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Measure one JSON API with twenty calls."""
    samples = [_api_call(request_context, method, path, body) for _index in range(20)]  # Repeat enough to see tails.
    return {
        "name": name,
        "method": method,
        "path": path,
        "status_codes": [sample["status"] for sample in samples],
        "server_time": _summary([float(sample["elapsed_ms"]) for sample in samples]),
        "bytes": _summary([float(sample["bytes"]) for sample in samples]),
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


def _prepare_multisite(page: Any) -> str:
    """Create one organization job and return its identifier."""
    page.goto("/select/mode", wait_until="domcontentloaded")  # Open the mode chooser with the signed session.
    page.get_by_test_id("mode-multi-site").check()  # Choose the organization workflow.
    page.get_by_test_id("mode-continue").click()  # Store the mode in the signed session.
    page.wait_for_url("**/select/site")  # Wait until the site list opens.
    page.get_by_test_id(f"site-select-{SITE_ID}").check()  # Select the first stand-in site.
    page.get_by_test_id(f"site-select-{SECOND_SITE_ID}").check()  # Select the second stand-in site.
    page.get_by_test_id("multi-site-continue").click()  # Store the selected sites.
    page.wait_for_url("**/upgrade/org/options")  # Wait until the organization options page opens.
    page.get_by_test_id("org-upgrade-version").fill("0.15.1")  # Pick the AP target version.
    page.get_by_test_id("org-upgrade-switch-version").fill("0.15.1")  # Pick the switch target version.
    page.get_by_test_id("org-upgrade-gateway-version").fill("0.15.1")  # Pick the gateway target version.
    page.get_by_test_id("org-upgrade-review").click()  # Save the organization options.
    page.wait_for_url("**/upgrade/org/confirm")  # Wait until the confirmation page opens.
    page.get_by_test_id("org-upgrade-confirmation").fill("CONFIRM")  # Unlock the organization start button.
    page.get_by_test_id("org-upgrade-start").click()  # Submit against the stand-in service only.
    page.wait_for_url("**/upgrade/org/jobs/*")  # Wait until the job page opens.
    return page.url.rsplit("/", 1)[-1]  # Return the generated job identifier.


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
    org_job_id = _prepare_multisite(page)  # Create one durable organization job for the job page and API.
    pages = [
        ("select-org", "/select/org"),
        ("select-mode", "/select/mode"),
        ("select-site", "/select/site"),
        ("inventory", f"/select/site/{SITE_ID}"),
        ("capture", f"/captures/new?site_id={SITE_ID}"),
        ("options", f"/runs/{PREPARED_RUN_ID}/options"),
        ("confirm", f"/runs/{PREPARED_RUN_ID}/confirm"),
        ("run", f"/runs/{START_READY_RUN_ID}"),
        ("stop", "/runs/e2e-stopping-run-0001"),
        ("org-options", "/upgrade/org/options"),
        ("org-confirm", "/upgrade/org/confirm"),
        ("org-job", f"/upgrade/org/jobs/{org_job_id}"),
        ("history", f"/history?site_id={SITE_ID}"),
        ("compare-select", "/compare"),
        ("compare", f"/compare?before={PRE_CAPTURE_ID}&after={POST_CAPTURE_ID}"),
    ]  # Cover every requested page family.
    page_results = [_measure_page(page, name, path) for name, path in pages]  # Measure all HTML pages.
    request_context = page.request  # Reuse the signed request context for JSON APIs.
    lock = _api_call(
        request_context, "POST", f"/api/sites/{SITE_ID}/lock", {"takeover": ""}
    )  # Create a heartbeat token.
    apis = [
        _measure_api(request_context, "sites", "GET", "/api/sites"),
        _measure_api(request_context, "inventory", "GET", f"/api/sites/{SITE_ID}/inventory"),
        _measure_api(request_context, "run-status", "GET", f"/api/runs/{START_READY_RUN_ID}/status"),
        _measure_api(request_context, "run-versions", "GET", f"/api/runs/{PREPARED_RUN_ID}/versions"),
        _measure_api(request_context, "capture-status", "GET", f"/api/captures/{TIER3_CAPTURE_ID}/status"),
        _measure_api(request_context, "org-options", "POST", "/api/org-upgrades/options", {"version": "0.15.1"}),
        _measure_api(request_context, "org-status", "GET", f"/api/org-upgrades/{org_job_id}"),
        _measure_api(request_context, "lock", "POST", f"/api/sites/{SITE_ID}/lock", {"takeover": ""}),
    ]  # Cover JSON readers and control-like paths.
    if lock["status"] == 200:  # A token is necessary for the heartbeat route.
        apis.append(
            _measure_api(request_context, "heartbeat", "POST", f"/api/sites/{SITE_ID}/lock/heartbeat", {})
        )  # Measure lock keepalive.
        _api_call(request_context, "DELETE", f"/api/sites/{SITE_ID}/lock")  # Release the site lock for later tests.
    static_assets = [
        _read_static_asset(request_context, "/static/js/portal.js"),
        _read_static_asset(request_context, "/static/css/portal.css"),
        _read_static_asset(request_context, "/static/vendor/bootstrap/bootstrap.bundle.min.js"),
    ]  # Measure the shipped JavaScript and CSS assets.
    intervals = _poll_intervals()  # Use the script poll settings for cost math.
    poll_cost = {
        api["name"]: round((60000.0 / intervals.get(api["name"], 30)) * api["server_time"]["median_ms"], 3)
        for api in apis
        if api["name"] in intervals
    }  # Compute milliseconds of server time per minute.
    RESULTS_PATH.write_text(
        json.dumps(
            {
                "browser_pages": page_results,
                "apis": apis,
                "static_assets": static_assets,
                "poll_intervals_seconds": intervals,
                "poll_cost_ms_per_minute": poll_cost,
                "browser_faults": faults,
                "budgets": {"ttfb_ms": 200, "load_ms": 1000, "api_median_ms": 100, "asset_kb": 250},
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )  # Write the raw browser and API evidence.
    assert RESULTS_PATH.exists()  # Prove the measurement artifact exists.
