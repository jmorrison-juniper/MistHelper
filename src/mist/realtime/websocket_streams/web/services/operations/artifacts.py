"""Own ended-session deletion and download behavior."""

from __future__ import annotations  # Keep collaborator annotations lazy.

import logging  # Structured events use repository handlers.
from collections.abc import Iterator  # Type the JSON Lines stream.
from typing import Any  # The manager uses behavior typing.

from src.mist.realtime.websocket_streams.intake.fields.error import (
    StreamRequestError,
)  # Refuse actions while not ready.
from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # Use the shared bounded JSON logger.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Keep artifact fields safe and bounded.


class SessionArtifactService:
    """Delete ended sessions and create their downloads."""

    def __init__(self, manager: Any, reason: str | None) -> None:
        """Store the manager and readiness."""
        self._manager = manager  # The ready manager owns retained session data.
        self._reason = reason  # A reason blocks artifact actions.

    def delete(self, session_id: str) -> dict[str, object]:
        """Delete one ended session."""
        self._require_ready()  # A not-ready portal has no retained session.
        logger.emit(logging.INFO, "web.artifact.delete.start")  # Record the bounded delete action.
        self._manager.delete(session_id)  # Let the manager refuse live or unknown sessions.
        logger.emit(logging.DEBUG, "web.artifact.delete.finish", {"status": "deleted"})  # Confirm deletion.
        return {"ok": True}  # Preserve the route confirmation.

    def download(self, session_id: str) -> tuple[str, Iterator[str]]:
        """Return one session file name and JSON Lines iterator."""
        self._require_ready()  # A not-ready portal has no retained session.
        logger.emit(logging.INFO, "web.artifact.download.start")  # Record stream preparation.
        filename, lines = self._manager.download(session_id)  # Build the lazy JSON Lines stream.
        logger.emit(logging.DEBUG, "web.artifact.download.finish", {"status": "ready"})  # Log no filename.
        return filename, lines  # Preserve lazy download behavior.

    def _require_ready(self) -> None:
        """Raise when the WebSocket engine is not ready."""
        if self._reason is not None:  # Missing credentials or imports block artifact actions.
            raise StreamRequestError("not_ready", self._reason)  # Preserve the contract error.
