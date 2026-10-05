"""Audit-only options. The parent owns environment and browser installation."""

import socket  # Deny Python egress during isolated catalog and template work.
from pathlib import Path  # Resolve repository assets without working-directory guesses.

import pytest  # Register local options and fixtures, not repository-wide configuration.

from tests.e2e.websockets_tab.dialog_audit.support.inventory import InventoryBuilder  # Read real definitions.
from tests.e2e.websockets_tab.dialog_audit.support.journeys import IsolatedPage  # Render without a server.
from tests.e2e.websockets_tab.dialog_audit.support.policy import BrowserRequestPolicy  # Guard before page creation.


def pytest_addoption(parser):
    """Expose inspection and the separately selected exact-key read-only lifecycle."""
    group = parser.getgroup("websocket-dialog-audit")  # Keep options local to the selected audit.
    group.addoption(
        "--ws-audit-mode", choices=("isolated", "live-inspection", "live-readonly"), default="isolated"
    )  # Default offline; only live-readonly admits the reviewed channel lifecycle.
    group.addoption("--ws-audit-base-url", default=None)  # Never guess a live URL.
    group.addoption("--ws-audit-artifacts", default=None)  # Write reports only when explicitly requested.


def pytest_ignore_collect(collection_path, config):
    """Ordinary directory collection must not include the live probe."""
    return (
        collection_path.name == "test_live.py" and config.getoption("--ws-audit-mode") == "isolated"
    )  # No implicit probe.


@pytest.fixture  # Standard pytest fixture registration requires a function.
def audit_inventory(monkeypatch):
    """Prevent network calls while discovering real installed SDK facades."""

    def deny(*_arguments, **_keywords):
        raise RuntimeError("Isolated audit denied Python network egress.")  # Stop before socket transmission.

    monkeypatch.setattr(socket.socket, "connect", deny)  # Cover normal outbound TCP connections.
    monkeypatch.setattr(socket.socket, "connect_ex", deny)  # Cover the alternate TCP connection method.
    monkeypatch.setattr(socket.socket, "sendto", deny)  # Cover unconnected UDP transmission.
    if hasattr(socket.socket, "sendmsg"):
        monkeypatch.setattr(socket.socket, "sendmsg", deny)  # Cover the alternate API where the platform provides it.
    monkeypatch.setattr(socket, "create_connection", deny)  # Reject SDK connection helpers before resolution.
    return InventoryBuilder().build()  # Discover catalog entries only, never construct a service or runner.


@pytest.fixture  # Standard pytest fixture registration requires a function.
def audit_page(browser, audit_inventory):
    """Fulfill approved requests locally. No Flask listener or SDK session exists."""
    renderer = IsolatedPage(Path(__file__).resolve().parents[4], audit_inventory)  # Use tracked source assets.
    context = browser.new_context(service_workers="block")  # Prevent worker requests from bypassing routing.
    policy = BrowserRequestPolicy("https://audit.invalid", renderer.responses())  # Deny every unknown request.
    policy.install(context)  # Install HTTP and WebSocket routing before page creation.
    page = context.new_page()  # Only a guarded context can create this page.
    page.set_default_timeout(15000)  # Bound selection and rendering waits.
    page.goto("https://audit.invalid/websockets")  # Fulfill the real rendered template without transmission.
    page.locator(".ws-catalog-entry").first.wait_for()  # Zero rendered operations must fail, not pass.
    yield page, policy  # Keep policy counters available to assertions.
    context.close()  # Close only the audit-owned browser context.
