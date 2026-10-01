"""Real browser, portal, and local SDK stream fixtures for issue 3575."""

from __future__ import annotations

import threading
from collections.abc import Iterator

import pytest
from mistapi.websockets.__ws_client import _MistWebsocket
from playwright.sync_api import Page
from werkzeug.serving import make_server

from src.websocket_streams.live.captures.model import CaptureDependencies
from src.websocket_streams.live.sessions.manager import RunnerFactory
from tests.unit.websocket_streams.live.captures.support.local_stream import LocalPacketStream
from tests.unit.websocket_streams.live.captures.support.portal import CaptureHarness, PortalFixture


class BrowserCapture:
    """Own the actual controller server and SDK local stream for one journey."""

    def __init__(self, harness: CaptureHarness, stream: LocalPacketStream) -> None:
        """Serve the real portal on loopback with no production port."""
        self.harness = harness
        self.stream = stream
        self.server = make_server("127.0.0.1", 0, PortalFixture.app(harness), threaded=True)
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
        self.thread.start()

    @property
    def url(self) -> str:
        """Return the owned controller's local address."""
        return f"http://127.0.0.1:{self.server.server_port}"

    def close(self) -> None:
        """Stop capture, controller, local stream, and app services."""
        self.harness.close()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3.0)
        self.stream.close()
        assert not self.thread.is_alive(), "The fixture left a controller server running."


@pytest.fixture
def browser_capture(monkeypatch: pytest.MonkeyPatch) -> Iterator[BrowserCapture]:
    """Use the real SDK client with only its address directed to the local fixture."""
    harness = CaptureHarness()
    stream = LocalPacketStream(harness.api)
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
    monkeypatch.setattr(_MistWebsocket, "_build_ws_url", lambda _client: stream.url)
    harness.manager._runner_factory = RunnerFactory(harness.api, CaptureDependencies(harness.clock, harness.clock.wait))
    fixture = BrowserCapture(harness, stream)
    try:
        yield fixture
    finally:
        fixture.close()


@pytest.fixture(autouse=True)
def local_browser_network(page: Page) -> None:
    """Refuse every browser request outside the controlled loopback server."""
    from urllib.parse import urlsplit

    def route_request(route) -> None:
        """Permit actual local assets and refuse any external address."""
        if urlsplit(route.request.url).hostname == "127.0.0.1":
            route.continue_()
        else:
            route.abort()

    page.route("**/*", route_request)
