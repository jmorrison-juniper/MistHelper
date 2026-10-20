"""Verify the cache-only WAN dashboard in a real browser."""

from __future__ import annotations

import json  # Build fixed local API responses for the browser.
import logging  # Record the local test server lifecycle.
import socket  # Select an unused local port.
import threading  # Serve Flask while Playwright loads the page.
from collections.abc import Iterator  # Type the server fixture lifetime.
from typing import Any  # Type the shared Flask and browser fixtures.
from urllib.parse import urlsplit  # Compare route paths without host details.

import pytest  # Provide fixtures and the optional browser dependency.

pytest.importorskip("playwright", reason="playwright is absent, so no browser test can run")  # Require browser support.
from playwright.sync_api import expect  # Wait for browser-rendered state.

logger = logging.getLogger(__name__)  # Keep browser evidence under this test module.
OVERVIEW_RESPONSE = json.dumps(  # Keep browser data fictional and complete.
    {
        "status": "stale",
        "data": [
            {
                "device_id": "gw-a",
                "site_id": "site-a",
                "site_name": "Test Site",
                "name": "Gateway A",
                "model": "Synthetic Model",
                "status": "connected",
                "wan_port_count": 1,
            }
        ],
        "notice": "Showing cached gateway data.",
    }
)
DETAIL_RESPONSE = json.dumps(  # Keep missing detail explicit and safe.
    {"status": "unavailable", "data": [], "notice": "Gateway details are unavailable."}
)
REFRESH_STATUS_RESPONSE = json.dumps(  # Keep browser refresh progress fictional and bounded.
    {
        "status": "disabled",
        "current_phase": None,
        "completed_pages": {},
        "last_complete_at": None,
        "safe_error": None,
        "queued_follow_up": False,
    }
)


@pytest.fixture(scope="module")
def dashboard_url(flask_app: Any) -> Iterator[str]:
    """Serve the existing portal for one browser test module."""
    from werkzeug.serving import make_server  # Reuse the Flask test app without a new service.

    with socket.socket() as probe:  # Ask the operating system for an unused port.
        probe.bind(("127.0.0.1", 0))  # Keep the test server on the local host.
        port = int(probe.getsockname()[1])  # Read the assigned port before closing the probe.
    server = make_server("127.0.0.1", port, flask_app, threaded=True)  # Serve only this test's portal.
    thread = threading.Thread(target=server.serve_forever, daemon=True)  # Keep browser requests responsive.
    logger.info("WAN dashboard browser server starting on port %d", port)  # Record the local server action.
    thread.start()  # Start the portal before the browser navigates.
    logger.debug("WAN dashboard browser server started on port %d", port)  # Record the ready state.
    try:
        yield f"http://127.0.0.1:{port}"  # Give the browser the local portal address.
    finally:
        logger.info("WAN dashboard browser server stopping on port %d", port)  # Record the shutdown action.
        server.shutdown()  # Stop the local server after the browser test.
        thread.join(timeout=10)  # Wait for the serving thread to exit.
        logger.debug("WAN dashboard browser server stopped on port %d", port)  # Record the shutdown result.


def test_cached_dashboard_disables_refresh_and_reports_missing_details(
    page: Any, dashboard_url: str, flask_app: Any
) -> None:
    """Show a stale cached overview and unavailable detail without a Mist request."""
    flask_app.extensions.pop("wan_dashboard_worker", None)  # Keep the worker disabled for this page.
    observed_paths: list[str] = []  # Keep only dashboard API paths from browser traffic.
    page.on(  # Observe each request made by the shipped dashboard script.
        "request",
        lambda browser_request: (
            observed_paths.append(urlsplit(browser_request.url).path)
            if "/wan-dashboard/api/" in browser_request.url
            else None
        ),
    )
    page.route(  # Supply one fictional cached overview without contacting Mist.
        "**/wan-dashboard/api/overview",
        lambda route: route.fulfill(status=200, content_type="application/json", body=OVERVIEW_RESPONSE),
    )
    page.route(  # Supply an explicit disabled state without a Mist request.
        "**/wan-dashboard/api/refresh-status",
        lambda route: route.fulfill(status=200, content_type="application/json", body=REFRESH_STATUS_RESPONSE),
    )
    page.route(  # Supply an explicit unavailable detail response.
        "**/wan-dashboard/api/gateways/gw-a/ports",
        lambda route: route.fulfill(status=503, content_type="application/json", body=DETAIL_RESPONSE),
    )
    page.goto(f"{dashboard_url}/wan-dashboard", wait_until="networkidle", timeout=15000)  # Load the portal page.
    expect(page.locator("#wan-refresh")).to_be_disabled()  # Prevent an unsupported refresh request.
    expect(page.locator("#wan-status")).to_have_text("Showing cached gateway data.")  # Label stale data.
    expect(page.get_by_test_id("wan-gateway-row")).to_contain_text("Gateway A")  # Render the fictional gateway.
    page.get_by_role("button", name="Show details for Gateway A").click()  # Request its cached detail.
    expect(page.get_by_test_id("wan-port-details-row")).to_contain_text(
        "Gateway details are unavailable."
    )  # Show the safe unavailable state.
    assert observed_paths == [  # Prove the browser used only cache-backed dashboard routes.
        "/wan-dashboard/api/overview",
        "/wan-dashboard/api/refresh-status",
        "/wan-dashboard/api/gateways/gw-a/ports",
    ]


def test_refresh_button_queues_work_with_csrf_header(page: Any, dashboard_url: str, flask_app: Any) -> None:
    """An enabled Refresh control posts one queue request with its CSRF token."""
    flask_app.extensions["wan_dashboard_worker"] = object()  # Enable only the page control in this test.
    queued_requests: list[dict[str, str]] = []  # Keep request evidence local to the browser.
    page.route(  # Serve the fictional overview without a Mist request.
        "**/wan-dashboard/api/overview",
        lambda route: route.fulfill(status=200, content_type="application/json", body=OVERVIEW_RESPONSE),
    )
    page.route(  # Keep status reads fictional and bounded.
        "**/wan-dashboard/api/refresh-status",
        lambda route: route.fulfill(status=200, content_type="application/json", body=REFRESH_STATUS_RESPONSE),
    )

    def queue_request(route: Any) -> None:
        """Record the HTTP method and CSRF header before returning a local result."""
        queued_requests.append(
            {
                "method": route.request.method,
                "csrf": route.request.headers.get("x-csrftoken", ""),
            }
        )
        route.fulfill(status=202, content_type="application/json", body='{"status":"coalesced"}')

    page.route("**/wan-dashboard/api/refresh", queue_request)  # Prevent network access beyond the test browser.
    page.goto(f"{dashboard_url}/wan-dashboard", wait_until="networkidle", timeout=15000)  # Load the local portal.
    csrf_token = page.locator('meta[name="csrf-token"]').get_attribute("content") or ""
    expect(page.get_by_test_id("wan-refresh")).to_be_enabled()  # Show Refresh only for the registered worker.
    page.get_by_test_id("wan-refresh").click()  # Ask the worker queue to refresh the cache.

    expect(page.get_by_test_id("wan-refresh")).to_be_enabled()  # Re-enable the control after the queue reply.
    assert queued_requests == [{"method": "POST", "csrf": csrf_token}]  # Send one CSRF-protected request.
