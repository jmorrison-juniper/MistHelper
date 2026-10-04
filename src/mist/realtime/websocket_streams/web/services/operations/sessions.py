"""Own WebSocket session lifecycle service behavior."""

from __future__ import annotations  # Keep collaborator annotations lazy.

import logging  # Structured events use repository handlers.
from typing import Any, cast  # Session collaborators use behavior types.

from src.mist.realtime.websocket_streams.intake.fields.error import (
    StreamRequestError,
)  # Refuse actions while not ready.
from src.mist.realtime.websocket_streams.live.sessions.buffer.page import MessagePage  # Type message reads.
from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # Use the shared bounded JSON logger.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Keep session fields safe and bounded.


class WebSocketSessionService:
    """Start, list, stop, and shut down sessions."""

    def __init__(self, checker: Any | None, manager: Any, reason: str | None) -> None:
        """Store the request checker, manager, and readiness."""
        self._checker = checker  # A not-ready service has no request checker.
        self._manager = manager  # The fallback manager still lists and shuts down.
        self._reason = reason  # A reason blocks actions that need Mist.

    def start(self, body: object) -> dict[str, object]:
        """Check and start one WebSocket session."""
        if self._reason is not None or self._checker is None:  # Starts need all production collaborators.
            raise StreamRequestError("not_ready", self._reason or "The WebSocket engine is not ready.")  # Refuse.
        logger.emit(logging.INFO, "web.session.start.begin")  # Record the bounded start action.
        checked = self._checker.check(body)  # Validate identifiers, targets, parameters, and confirmation.
        payload = cast(dict[str, object], self._manager.start(checked))  # Start the selected runner.
        logger.emit(logging.DEBUG, "web.session.start.finish", {"status": "started"})  # Log no identifier.
        return payload  # Return the established session payload.

    def list(self) -> dict[str, object]:
        """Return live and ended session payloads."""
        logger.emit(logging.DEBUG, "web.session.list.start")  # Polling uses debug-level structured events.
        payload = cast(dict[str, object], self._manager.list_payload())  # Read the manager snapshot.
        sessions = payload.get("sessions")  # Read the public session list for a bounded count.
        count = len(sessions) if isinstance(sessions, list) else 0  # Refuse a non-list count shape.
        logger.emit(logging.DEBUG, "web.session.list.finish", {"count": count})  # Report the bounded count.
        return payload  # Preserve limits and session fields.

    def stop(self, session_id: str) -> dict[str, object]:
        """Stop one live session."""
        logger.emit(logging.INFO, "web.session.stop.start")  # Record the bounded stop action.
        payload = cast(dict[str, object], self._manager.stop(session_id))  # Ask the manager to stop the runner.
        logger.emit(logging.DEBUG, "web.session.stop.finish", {"status": "stopped"})  # Log no identifier.
        return payload  # Preserve the stopped session payload.

    def shutdown(self) -> None:
        """Stop all sessions and helper threads."""
        logger.emit(logging.INFO, "web.session.shutdown.start")  # Record shutdown start.
        self._manager.shutdown()  # Stop live runners and the reaper.
        logger.emit(logging.DEBUG, "web.session.shutdown.finish", {"status": "stopped"})  # Confirm shutdown.


class WebSocketMessageService:
    """Read bounded message pages from one session manager."""

    def __init__(self, manager: Any) -> None:
        """Store the session manager."""
        self._manager = manager  # The manager owns each bounded message buffer.

    def read(self, session_id: str, after: int, limit: int) -> MessagePage:
        """Return messages after one sequence number."""
        page = cast(MessagePage, self._manager.read(session_id, after, limit))  # Read the bounded buffer page.
        logger.emit(logging.DEBUG, "web.session.read.finish", {"count": len(page.messages)})  # Report count only.
        return page  # Preserve direct JSON text generation.
