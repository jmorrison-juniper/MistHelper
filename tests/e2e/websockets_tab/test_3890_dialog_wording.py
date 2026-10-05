"""Browser proof for the DHCP release and MAC table purpose text.

Why:
    Issue #3890. The WebSockets page must show the new purpose text when an
    operator selects a DHCP release entry or the MAC table entry. This module
    serves the real catalog payload and never starts a session.
"""

from __future__ import annotations  # Keep annotations lazy for Playwright imports.

import logging  # Keep browser test records under this module.
import socket  # Find an unused local port.
import threading  # Serve Flask beside the browser.
from collections.abc import Iterator  # Type the server fixture.
from pathlib import Path  # Save screenshots under the test artifact folder.
from types import SimpleNamespace  # Build fake service groups and SDK answers.
from typing import Any  # Type Playwright objects without importing private types.

import pytest  # Use fixtures and Playwright integration.

logger = logging.getLogger(__name__)  # Keep this test module visible in logs.

pytest.importorskip("playwright", reason="playwright is absent, so the browser proof cannot run")  # Browser guard.

READY_TIMEOUT_MS = 15000  # Bound every browser wait.
ARTIFACT_DIR = Path(__file__).resolve().parents[3] / "test-artifacts" / "websockets"  # Git ignores this folder.
ORG_ID = "99999999-8888-7777-6666-555555555555"  # Fake organization identifier.
SITE_ID = "11111111-2222-3333-4444-555555555555"  # Fake site identifier.
STATE_CHANGE = "This changes client state, so each client must ask for a new address."  # Required effect text.
EX_TARGETS = "Network and MAC addresses, Network and Port, or Port only."  # The three EX target sets.
SRX_TARGETS = "Network only, Network and MAC addresses, Network and Port, Port only, or Port and MAC addresses."
EXPECTED_TEXT = {
    "ex.releaseDhcpLeases": f"Release DHCP leases on an EX switch. {STATE_CHANGE} Use one of these target sets: "
    + EX_TARGETS,
    "srx.releaseDhcpLeases": f"Release DHCP leases on an SRX device. {STATE_CHANGE} Use one of these target sets: "
    + SRX_TARGETS,
    "ssr.releaseDhcpLeases": f"Release DHCP leases on an SSR device. {STATE_CHANGE} Use one of these target sets: "
    + SRX_TARGETS,
    "ex.retrieveMacTable": "Get the MAC table from the switch. All filters are optional. Leave them empty to get "
    "the full table. Type a MAC address, a port, or a VLAN ID to show fewer entries.",
}  # The purpose text that each selected entry must show.


class FixedLimits:
    """Supply fixed session limits to the real catalog service."""

    def limits_payload(self) -> dict[str, int]:
        """Return the limits that the page shows."""
        return {"max_sessions": 2, "idle_seconds": 120, "capture_seconds": 60}  # Small fixed limits.


class CatalogOnlyServices:
    """Serve the real catalog payload and refuse every session action."""

    def __init__(self) -> None:
        """Build the real catalog service and empty fake groups."""
        from src.mist.realtime.websocket_streams.catalog.channels import ChannelCatalog  # Real channels.
        from src.mist.realtime.websocket_streams.catalog.registry.stream_catalog import (
            StreamCatalog,
        )  # Real combined catalog.
        from src.mist.realtime.websocket_streams.catalog.utilities.utility_catalog import (
            UtilityCatalog,
        )  # Real SDK utility catalog.
        from src.mist.realtime.websocket_streams.web.services.operations.catalog import (
            WebSocketCatalogService,
        )  # Real catalog payload builder.

        catalog = StreamCatalog(
            ChannelCatalog(), UtilityCatalog(), changes_enabled=False, shell_enabled=False
        )  # Keep both locks in their default closed state.
        self.catalog = WebSocketCatalogService(catalog, FixedLimits(), None)  # Real payload with fixed limits.
        lifecycle = SimpleNamespace(
            start=self._refuse, list=self._list, stop=self._refuse, shutdown=self._noop
        )  # This proof never starts a session.
        self.sessions = SimpleNamespace(lifecycle=lifecycle, messages=SimpleNamespace(read=self._refuse))  # Group.
        self.artifacts = SimpleNamespace(delete=self._refuse, download=self._refuse)  # No artifacts exist.
        self.terminal = self  # No terminal exists.
        self.pickers = SimpleNamespace(site=self, related=self)  # Picker calls are not used here.

    def _list(self) -> dict[str, object]:
        """Return an empty session list."""
        return {"sessions": [], "limits": {"max_sessions": 2, "live_count": 0}}  # No sessions run.

    def _refuse(self, *_args: object) -> dict[str, object]:
        """Refuse a session action that this proof must never send."""
        raise AssertionError("The wording proof must not start, read, stop, or delete a session.")  # Fail loud.

    def _noop(self) -> None:
        """Accept the portal shutdown call."""
        logger.debug("Fake session shutdown called")  # Record the shutdown call.


def free_port() -> int:
    """Return an unused local TCP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:  # Ask the operating system for a port.
        probe.bind(("127.0.0.1", 0))  # Port zero means any free port.
        return int(probe.getsockname()[1])  # Return the selected port.


@pytest.fixture(scope="module")
def wording_portal() -> Iterator[str]:
    """Serve the web portal with the real catalog payload."""
    import mistapi  # Patch the site picker SDK seam.
    from werkzeug.serving import make_server  # Start an in-process server.

    from src.mist.realtime.websocket_streams.web.services.registry import (
        WebSocketServiceRegistry,
    )  # Inject the catalog-only services.
    from web_portal.app import WebPortalApp  # Build the same app as the portal.
    from web_portal.menu_registry import build_static_menu_actions  # Supply normal menu actions.

    def list_sites(_session: object, _org_id: str) -> SimpleNamespace:
        """Return one site for the site picker."""
        return SimpleNamespace(data=[{"id": SITE_ID, "name": "HQ"}])  # SDK answer shape.

    with pytest.MonkeyPatch.context() as patcher:  # Undo SDK patches when the server stops.
        patcher.setattr(mistapi.api.v1.orgs.sites, "listOrgSites", list_sites)  # Patch the site picker.
        app = WebPortalApp.create_app(SimpleNamespace(), build_static_menu_actions(), ORG_ID)  # Build the app.
        app.config["TESTING"] = True  # Raise route errors during the test.
        app.config[WebSocketServiceRegistry.CONFIG_KEY] = CatalogOnlyServices()  # Inject the services.
        server = make_server("127.0.0.1", free_port(), app, threaded=True)  # Bind a free port.
        thread = threading.Thread(target=server.serve_forever, daemon=True)  # Serve beside Playwright.
        logger.info("Starting the wording portal on port %d", server.server_port)  # Log server start.
        thread.start()  # Start the server loop.
        try:
            yield f"http://127.0.0.1:{server.server_port}"  # Give tests the base URL.
        finally:
            server.shutdown()  # Stop the server loop.
            thread.join(timeout=10)  # Wait for server thread exit.
            WebPortalApp.shutdown_app(app)  # Stop portal background threads.


@pytest.mark.parametrize("key", sorted(EXPECTED_TEXT))
def test_selected_entry_shows_issue_3890_text(page: Any, wording_portal: str, key: str) -> None:
    """Each selected entry shows its full purpose text in the start form."""
    page.goto(f"{wording_portal}/websockets", wait_until="networkidle", timeout=READY_TIMEOUT_MS)  # Open the page.
    entry = page.get_by_test_id(f"ws-catalog-entry-{key}")  # Find the catalog button for this key.
    entry.wait_for(state="visible", timeout=READY_TIMEOUT_MS)  # Wait for the catalog to render.
    entry.click()  # Select the entry. The proof never clicks Start.
    description = page.locator("#wsSelectedDescription")  # The purpose text in the start form.
    description.wait_for(state="visible", timeout=READY_TIMEOUT_MS)  # Wait for the form to update.
    assert description.inner_text().strip() == EXPECTED_TEXT[key]  # The page shows the full new text.
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)  # Ensure the screenshot folder exists.
    page.screenshot(path=str(ARTIFACT_DIR / f"issue3890-{key}.png"), full_page=True)  # Save visual evidence.
