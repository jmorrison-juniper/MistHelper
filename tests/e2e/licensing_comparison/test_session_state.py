"""Verify browser-session persistence with the isolated feature blueprint."""

from collections.abc import Iterator
from pathlib import Path
from threading import Thread
from types import SimpleNamespace
from typing import Any

import pytest
from flask import Flask
from werkzeug.serving import make_server

import src.interfaces.portals.licensing_comparison.service as licensing_service
from src.interfaces.portals.licensing_comparison import licensing_comparison_bp


@pytest.fixture
def licensing_portal_url(monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    """Serve a synthetic local portal on loopback with no Mist credentials."""
    app = Flask(__name__)  # Build the feature blueprint without editing the shared portal.
    app.config.update(
        TESTING=True, SECRET_KEY="browser-test-key", APISESSION=object(), ORG_ID="org-1", ORG_NAME="Primary"
    )
    app.jinja_env.globals["csrf_token"] = lambda: "test-csrf-token"  # Supply the standard template token.
    app.register_blueprint(licensing_comparison_bp)  # Mount only the isolated feature routes.

    @app.get("/test-away")
    def away() -> str:
        """Provide a same-origin destination for the history navigation check."""
        return "away"  # Keep the navigation target local to this fixture.

    responses = {
        "getSelf": {"privileges": []},
        "listLicenseTypes": [{"name": "SUB-AI", "key": "sub_ai", "includes": []}],
        "getOrgLicensesSummary": {"summary": {"SUB-AI": 1}},
        "getOrgLicensesBySite": [],
        "getOrgInventory": [],
    }  # Use synthetic data for every browser request.
    for module, operation in (
        (licensing_service.self_api, "getSelf"),
        (licensing_service.license_types_api, "listLicenseTypes"),
        (licensing_service.licenses_api, "getOrgLicensesSummary"),
        (licensing_service.licenses_api, "getOrgLicensesBySite"),
        (licensing_service.inventory_api, "getOrgInventory"),
    ):  # Replace the SDK calls that the page can trigger.
        monkeypatch.setattr(
            module,
            operation,
            lambda *_arguments, _operation=operation, **_keywords: SimpleNamespace(
                status_code=200, data=responses[_operation], next=None
            ),
        )  # Return a local success response with no network access.
    monkeypatch.setattr(
        licensing_service.RateLimitingUtils,
        "get_rate_limited_delay",
        lambda *_arguments: (None, 0.0),
    )  # Prevent test requests from sleeping.
    server = make_server("127.0.0.1", 0, app, threaded=True)  # Bind only to loopback on an available port.
    thread = Thread(target=server.serve_forever, daemon=True)  # Keep the local test server bounded.
    thread.start()  # Start the route server for the browser fixture.
    try:
        yield f"http://127.0.0.1:{server.server_port}"  # Expose only the loopback test address.
    finally:
        server.shutdown()  # Stop the server after the browser flow.
        thread.join(timeout=5)  # Wait for its request loop to exit.
        server.server_close()  # Release the loopback socket after the test.


def fill_session_values(page: Any, portal_url: str) -> None:
    """Save one purchased value and one manual organization in the browser session."""
    page.goto(portal_url + "/license-comparison")  # Open the feature page.
    page.locator("#organization-select option[value='org-1']").wait_for()  # Wait for the API choice.
    page.get_by_test_id("organization-select").select_option("org-1")  # Select the synthetic organization.
    purchase = page.get_by_test_id("purchased-license-input")  # Find its purchase field.
    purchase.fill('{"SUB-AI": 4}')  # Enter a synthetic purchased amount.
    purchase.press("Tab")  # Commit the change event that stores session state.
    page.get_by_test_id("add-manual-row").click()  # Add a session-only organization row.
    page.locator(".manual-name").fill("Manual office")  # Name the synthetic row.
    page.locator(".manual-licenses").fill('{"SUB-MAN": 2}')  # Add a valid license count.
    page.locator(".manual-inventory").fill('{"ap": 3}')  # Add a valid inventory count.
    page.locator(".manual-inventory").press("Tab")  # Save the manual values on the change event.


def assert_session_values(page: Any) -> None:
    """Check the selected organization, manual row, and purchase value."""
    page.locator("#organization-select option:checked").wait_for()  # Wait for restored selection.
    assert page.locator("#organization-select").input_value() == "org-1"  # Keep the selected organization.
    assert page.locator(".manual-name").input_value() == "Manual office"  # Restore the manual row name.
    assert page.locator(".manual-licenses").input_value() == '{"SUB-MAN":2}'  # Restore its license counts.
    assert page.locator(".manual-inventory").input_value() == '{"ap":3}'  # Restore its inventory counts.
    organization_purchase = page.locator(
        ".purchase-input[data-row-id='org-1'] [data-testid='purchased-license-input']"
    )  # Select the organization field when manual rows add more purchase inputs.
    assert organization_purchase.input_value() == '{"SUB-AI":4}'  # Restore the purchase value.


def save_failure_screenshot(page: Any) -> Path:
    """Write a browser screenshot to the CI artifact directory after a failure."""
    target = Path("test-artifacts/licensing-comparison-session-state.png")  # Use the ignored artifact directory.
    target.parent.mkdir(parents=True, exist_ok=True)  # Create the artifact directory when needed.
    page.screenshot(path=str(target), full_page=True)  # Preserve the failed browser state for review.
    return target  # Return the exact evidence path.


def test_session_values_survive_reload_and_same_tab_navigation(
    page: Any, browser: Any, licensing_portal_url: str
) -> None:
    """Keep manual and purchase values in one browser session and clear them in a new context."""
    try:
        fill_session_values(page, licensing_portal_url)  # Store the test values in the current tab.
        page.reload()  # Verify persistence across a page reload.
        assert_session_values(page)  # Check the restored values.
        page.goto(licensing_portal_url + "/test-away")  # Navigate within the same origin.
        page.go_back()  # Return to the dashboard in the same browser tab.
        assert_session_values(page)  # Check values after in-page history navigation.
        fresh_context = browser.new_context()  # Create a separate browser session.
        fresh_page = fresh_context.new_page()  # Open a tab with empty session storage.
        fresh_page.goto(licensing_portal_url + "/license-comparison")  # Load the dashboard in the new session.
        assert fresh_page.locator(".manual-row").count() == 0  # Keep the prior manual row private to its session.
        assert (
            fresh_page.evaluate("sessionStorage.getItem('misthelper.licensingComparison.v1')") is None
        )  # Start empty.
        fresh_context.close()  # Close the isolated browser context.
    except Exception:
        save_failure_screenshot(page)  # Preserve the failure for the CI artifact step.
        raise  # Keep the original browser failure visible to pytest.
