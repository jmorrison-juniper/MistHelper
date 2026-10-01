"""Use the actual checker, manager, services, and portal for local capture tests."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable

from flask import Flask

from src.websocket_streams.catalog.channels import ChannelCatalog
from src.websocket_streams.catalog.registry import StreamCatalog
from src.websocket_streams.catalog.utilities import UtilityCatalog
from src.websocket_streams.intake.pickers import StreamPickerService
from src.websocket_streams.intake.start_request import StartRequestChecker
from src.websocket_streams.live.captures.model import CaptureDependencies
from src.websocket_streams.live.captures.runner import PacketCaptureRunner
from src.websocket_streams.live.sessions.manager import RunnerFactory, StreamSessionManager
from src.websocket_streams.live.sessions.record import StreamSession
from src.websocket_streams.live.sessions.settings import StreamSettings
from src.websocket_streams.web.services import WebSocketsServiceParts, WebSocketsServices
from tests.unit.websocket_streams.live.captures.support.sdk import (
    ControlledClock,
    ControlledSocket,
    FakeMistSession,
    Identities,
)
from web_portal.app import WebPortalApp
from web_portal.menu_registry import build_static_menu_actions


class CaptureHarness:
    """Keep the real service path and replace only clock and SDK transport."""

    def __init__(self, family: str = "ap", settings: StreamSettings | None = None) -> None:
        """Build one isolated set of real WebSockets services."""
        self.api = FakeMistSession(family)
        self.clock = ControlledClock()
        settings = settings or StreamSettings()
        catalog = StreamCatalog(ChannelCatalog(), UtilityCatalog(), changes_enabled=False, shell_enabled=False)
        pickers = StreamPickerService(self.api, Identities.ORG)
        checker = StartRequestChecker(catalog, pickers, Identities.ORG)
        dependencies = CaptureDependencies(self.clock, self.clock.wait, ControlledSocket)
        self.manager = StreamSessionManager(settings, RunnerFactory(self.api, dependencies), self.clock)
        self.services = WebSocketsServices(
            WebSocketsServiceParts(catalog, checker, pickers, self.manager, settings, None)
        )
        self.app: Flask | None = None

    @staticmethod
    def body(duration: object = 120, key: str = "ap.remotePcapWired") -> dict[str, object]:
        """Build a browser-shaped request without bypassing target checks."""
        targets = {"site_id": Identities.SITE, "device_id": Identities.DEVICE}
        parameters = {"duration": duration, "num_packets": 10000, "max_pkt_len": 512}
        if key.startswith(("ex.", "srx.", "ssr.")):
            parameters["port_ids"] = ["ge-0/0/1"]
        if key == "ap.remotePcapWireless":
            parameters["band"] = "5"
        if key.startswith("mxedge."):
            targets = {"mxedge_id": Identities.DEVICE}
            parameters["interfaces"] = ["port0"]
            if key == "mxedge.siteRemotePcap":
                targets["site_id"] = Identities.SITE
        return {"kind": "utility", "key": key, "targets": targets, "parameters": parameters}

    def start(self, duration: int = 120, key: str = "ap.remotePcapWired") -> StreamSession:
        """Start through the real service and return its actual session record."""
        payload = self.services.start_session(self.body(duration, key))
        return self.manager._get(str(payload["session_id"]))

    @staticmethod
    def wait(condition: Callable[[], bool]) -> None:
        """Bound a local asynchronous state wait to two seconds."""
        deadline = time.monotonic() + 2.0
        while not condition():
            if time.monotonic() >= deadline:
                raise AssertionError("The local capture did not reach the expected state.")
            threading.Event().wait(0.005)

    def close(self) -> None:
        """Stop actual workers and all app services before fixture teardown."""
        self.api.script.start.release.set()
        self.manager.shutdown()
        for session in tuple(self.manager._sessions.values()):
            if isinstance(session.runner, PacketCaptureRunner):
                session.runner.worker.join(timeout=3.0)
                assert not session.runner.worker.is_alive(), "The fixture left a capture worker running."
                client = session.runner._monitor.connection.client
                assert client is None or not client.ready(), "The fixture left a packet connection open."
        if self.app is not None:
            WebPortalApp.shutdown_app(self.app)
        self.api._session.close()


class PortalFixture:
    """Build the actual portal without disabling its request protections."""

    @staticmethod
    def app(harness: CaptureHarness) -> Flask:
        """Install real services rather than a replacement controller."""
        app = WebPortalApp.create_app(harness.api, build_static_menu_actions(), Identities.ORG)
        app.config["TESTING"] = True
        app.config[WebSocketsServices.CONFIG_KEY] = harness.services
        harness.app = app
        return app


class PacketEvents:
    """Create synthetic packet events for the actual SDK callback path."""

    @staticmethod
    def packet(timestamp: int, capture_id: str = Identities.CAPTURE, channel: str | None = None) -> dict[str, object]:
        """Use reserved documentation addresses and no real packet bytes."""
        return {
            "event": "data",
            "channel": channel or f"/sites/{Identities.SITE}/pcaps",
            "data": {
                "capture_id": capture_id,
                "pcap_dict": {
                    "timestamp": timestamp,
                    "src_ip": "192.0.2.1",
                    "dst_ip": "192.0.2.2",
                    "proto": "TCP",
                    "length": 64,
                },
                "pcap_raw": "AA==",
            },
        }

    @staticmethod
    def end(channel: str | None = None) -> dict[str, object]:
        """End the exact synthetic capture with the documented null record."""
        return {
            "event": "data",
            "channel": channel or f"/sites/{Identities.SITE}/pcaps",
            "data": {"capture_id": Identities.CAPTURE, "pcap_dict": None},
        }
