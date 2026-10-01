"""Own packet capture admission and its asynchronous worker."""

from __future__ import annotations

import logging
import threading
from collections.abc import Iterable

from src.websocket_streams.catalog.model import Safety, UtilityDefinition
from src.websocket_streams.intake.fields import StreamRequestError
from src.websocket_streams.intake.start_request import StartRequest
from src.websocket_streams.live.captures.control import CaptureBodies
from src.websocket_streams.live.captures.model import CaptureContext, CaptureDependencies
from src.websocket_streams.live.captures.runner.lifecycle import CaptureMonitor
from src.websocket_streams.live.sessions.record import SessionSink

logger = logging.getLogger(__name__)


class CaptureScope:
    """Prevent overlapping captures whose cloud stop shares one scope."""

    @staticmethod
    def key(request: StartRequest) -> tuple[str, str] | None:
        """Return the cloud stop scope for a packet request only."""
        definition = request.definition
        if not isinstance(definition, UtilityDefinition) or definition.safety is not Safety.CAPTURE:
            return None
        org = definition.scope == "organization"
        return ("orgs" if org else "sites", request.target("org_id" if org else "site_id").lower())

    @classmethod
    def check(cls, request: StartRequest, live: Iterable[StartRequest]) -> None:
        """Refuse a second capture before any SDK work in the same scope."""
        key = cls.key(request)
        if key is not None and any(cls.key(existing) == key for existing in live):
            raise StreamRequestError("session_live", "A packet capture is already active in this scope.")

    @staticmethod
    def life_limit(runner: object, configured: int) -> int:
        """Keep the capture interval separate from channel and shell limits."""
        return (
            max(configured, runner.context.plan.duration + 90)
            if isinstance(runner, PacketCaptureRunner)
            else configured
        )


class PacketCaptureRunner:
    """Own one capture worker and asynchronous operator stop."""

    def __init__(
        self,
        apisession: object,
        request: StartRequest,
        sink: SessionSink,
        dependencies: CaptureDependencies | None = None,
    ) -> None:
        """Prepare a checked capture without starting SDK or network work."""
        self.context = CaptureContext(CaptureBodies.build(request), sink, dependencies or CaptureDependencies())
        self._monitor = CaptureMonitor(apisession, self.context)
        self.worker = threading.Thread(target=self._monitor.run, name=f"ws-pcap-{request.key}", daemon=True)

    def start(self) -> None:
        """Start the owned capture worker and return."""
        logger.info("Starting packet capture worker key=%s", self.context.plan.request.key)
        self.worker.start()
        logger.debug("Started packet capture worker key=%s", self.context.plan.request.key)

    def stop(self) -> None:
        """Signal stop without creating another stop thread."""
        logger.info("Requesting packet capture stop key=%s", self.context.plan.request.key)
        with self.context.events.lock:
            self.context.events.stopping.set()
            self.context.events.wake.set()
        logger.debug("Requested packet capture stop key=%s", self.context.plan.request.key)

    def send_input(self, text: str) -> None:
        """Reject shell input for a packet capture."""
        raise StreamRequestError("not_open", "This packet capture does not accept shell input.")
