"""Browser coverage for the menu 256 organization webhook control."""

from __future__ import annotations  # Keep modern annotations import-safe.

import json  # Return a local JSON run response inside the browser.
import logging  # Record server startup, request, and cleanup actions.
import threading  # Serve the real Flask portal beside the browser.
from collections.abc import Iterator  # Type the yielding server fixture.
from types import SimpleNamespace  # Build a local Mist response double.
from typing import Any  # Type Playwright objects without importing browser internals.
from unittest.mock import patch  # Keep every Mist SDK boundary offline.

import pytest  # Provide the browser fixture and cleanup checks.

logger = logging.getLogger(__name__)  # Keep browser evidence tied to this module.

pytest.importorskip("playwright", reason="playwright is absent, so no browser test can run")

_PROVIDER_MODULE = "web_portal.routes.settings"  # Keep SDK patch targets on the assigned route module.
_MENU_NUMBER = "256"  # Select the issue-specific portal operation.
_RUN_ROUTE = "**/api/operations/run"  # Observe and stop the browser run request.
_TIMEOUT_MS = 15000  # Bound each browser wait.
_WEBHOOKS = [  # Return stable identifiers in a known Mist order.
    {"id": "wh-a", "name": "Alpha webhook"},
    {"id": "wh-b", "name": "Beta webhook"},
]


@pytest.fixture(scope="module")
def webhook_portal(tmp_path_factory: pytest.TempPathFactory) -> Iterator[str]:
    """Serve the real portal with mocked webhook choices and owned cleanup."""
    from werkzeug.serving import make_server  # Use the cross-platform local test server.

    from web_portal.app import WebPortalApp  # Build the real portal application.
    from web_portal.menu_registry import build_static_menu_actions  # Use the shipped menu catalog.

    data_dir = tmp_path_factory.mktemp("issue_3188_webhook_control")  # Isolate generated portal files.
    response = SimpleNamespace(status_code=200)  # Provide one successful local Mist response.
    with (
        patch(f"{_PROVIDER_MODULE}.mistapi.api.v1.orgs.webhooks.listOrgWebhooks", return_value=response),
        patch(f"{_PROVIDER_MODULE}.mistapi.get_all", return_value=_WEBHOOKS),
    ):
        app = WebPortalApp.create_app(  # Build the same application factory that production uses.
            apisession=object(),  # Use a local session marker instead of a credential.
            menu_actions=build_static_menu_actions(),  # Include menu 256 in the operations list.
            org_id="org-1",  # Supply the organization required by the parameter route.
        )
        app.config["TESTING"] = True  # Surface any route failure directly.
        app.config["DATA_DIR"] = str(data_dir)  # Keep output discovery inside the temporary directory.
        server = make_server("127.0.0.1", 0, app, threaded=True)  # Bind one ephemeral loopback port.
        thread = threading.Thread(target=server.serve_forever, daemon=True)  # Own the server lifecycle.
        logger.info("Starting the menu 256 portal test server on port %d", server.server_port)
        thread.start()  # Accept the browser request.
        logger.debug("Started the menu 256 portal test server")
        try:
            yield f"http://127.0.0.1:{server.server_port}"  # Hand the owned portal address to the test.
        finally:
            logger.info("Stopping the menu 256 portal test server")  # Log before cleanup.
            server.shutdown()  # Stop the request loop.
            thread.join(timeout=10)  # Wait a bounded time for the owned thread.
            server.server_close()  # Release the ephemeral socket.
            WebPortalApp.shutdown_app(app)  # Stop portal-owned background services.
            logger.debug("Stopped the menu 256 portal test server")
            assert not thread.is_alive(), "The menu 256 portal server thread did not stop."


def _select_menu(page: Any, portal_url: str) -> None:
    """Open the operations page and select menu 256 through the real list."""
    logger.info("Opening the operations page for menu %s", _MENU_NUMBER)  # Log before browser navigation.
    page.goto(f"{portal_url}/operations", wait_until="networkidle", timeout=_TIMEOUT_MS)  # Load shipped assets.
    row = page.locator(f".op-item[data-menu='{_MENU_NUMBER}']")  # Find the exact operation row.
    headers = page.locator("#operationAccordion .accordion-button")  # Read each collapsed category header.
    for index in range(headers.count()):  # Open categories until menu 256 becomes visible.
        headers.nth(index).click()  # Use the same accordion control as an operator.
        page.wait_for_timeout(150)  # Let Bootstrap finish the collapse transition.
        if row.is_visible():  # Stop when the assigned menu is reachable.
            break  # Keep later categories unchanged.
    row.wait_for(state="visible", timeout=_TIMEOUT_MS)  # Fail clearly if menu 256 is not portal-visible.
    row.click()  # Trigger the existing JavaScript parameter request.
    page.wait_for_selector("#param-webhook_id", state="visible", timeout=_TIMEOUT_MS)  # Wait for the choice.
    logger.debug("Menu %s shows the webhook control", _MENU_NUMBER)  # Log after the parameter request.


def _capture_run_body(page: Any) -> dict[str, Any]:
    """Stop one run request in the browser and return its JSON body."""

    def stop_run(route: Any) -> None:
        """Return a local response so no menu handler or Mist search starts."""
        route.fulfill(  # Answer inside the browser before the request reaches Flask.
            status=200,
            content_type="application/json",
            body=json.dumps({"error": "Browser test stopped the run before execution."}),
        )

    page.route(_RUN_ROUTE, stop_run)  # Keep the operation and delivery search offline.
    with page.expect_request(_RUN_ROUTE, timeout=_TIMEOUT_MS) as request_info:
        page.locator('[data-testid="run-btn"]').click()  # Use the existing Run button and JavaScript.
    return dict(request_info.value.post_data_json)  # Return the exact queued portal payload.


class TestMenu256WebhookControl:
    """Prove the existing JavaScript renders and queues the stable choice."""

    def test_browser_uses_stable_webhook_identifier(self, page: Any, webhook_portal: str) -> None:
        """Render the required choice, enforce selection, and queue one stable identifier."""
        _select_menu(page, webhook_portal)  # Reach the issue-specific control through the real page.
        control = page.locator("#param-webhook_id")  # Read the choice that the static route supplied.
        labels = control.locator("option").all_text_contents()  # Include the existing placeholder for context.
        values = control.locator("option").evaluate_all("options => options.map(option => option.value)")
        run_button = page.locator('[data-testid="run-btn"]')  # Read the existing JavaScript validation target.
        assert "Webhook" in page.locator("#param-group-webhook_id label").inner_text()
        assert labels == ["-- Select --", "Alpha webhook", "Beta webhook"]
        assert values == ["", "wh-a", "wh-b"]  # Prove browser values use stable Mist identifiers.
        assert run_button.is_disabled()  # A required empty choice must prevent a run.
        control.select_option("wh-b")  # Select the second stable identifier.
        assert run_button.is_enabled()  # The existing JavaScript should now allow the run.
        body = _capture_run_body(page)  # Observe the queued answer without starting the operation.
        assert str(body["menu_number"]) == _MENU_NUMBER
        assert body["parameters"]["input_answers"] == ["wh-b"]  # Send the stable identifier to the exporter.
