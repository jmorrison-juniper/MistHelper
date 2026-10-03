"""Own terminal read, input, and resize service behavior."""

from __future__ import annotations  # Keep collaborator annotations lazy.

import logging  # Structured events use repository handlers.
from typing import Any  # The manager uses behavior typing.

from src.mist.realtime.websocket_streams.intake.fields.error import (
    StreamRequestError,
)  # Refuse terminal use while not ready.
from src.mist.realtime.websocket_streams.live.terminal.gateway import (
    TerminalGateway,
)  # Enforce terminal limits and state.
from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # Use the shared bounded JSON logger.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Keep terminal fields safe and bounded.


class WebSocketTerminalService:
    """Read terminal bytes, send text, and resize one terminal."""

    def __init__(self, manager: Any, reason: str | None) -> None:
        """Build one gateway for the process service bundle."""
        self._gateway = TerminalGateway(manager)  # Share the waiting-read counter across requests.
        self._reason = reason  # A reason blocks terminal actions.

    def read(self, session_id: str, after: int, wait_seconds: float) -> dict[str, object]:
        """Read terminal bytes with one bounded wait."""
        self._require_ready()  # A terminal requires the production manager.
        logger.emit(logging.DEBUG, "web.terminal.read.start", {"timeout_seconds": wait_seconds})  # Log wait only.
        payload = self._gateway.read(session_id, after, wait_seconds)  # Apply long-poll and rate limits.
        logger.emit(
            logging.DEBUG, "web.terminal.read.finish", {"byte_count": len(str(payload.get("data", "")))}
        )  # Size.
        return payload  # Preserve the terminal chunk contract.

    def send(self, session_id: str, data: str) -> dict[str, object]:
        """Send exact terminal input text."""
        self._require_ready()  # A terminal requires the production manager.
        logger.emit(logging.INFO, "web.terminal.send.start", {"byte_count": len(data.encode("utf-8"))})  # Size only.
        payload = self._gateway.send(session_id, data)  # Enforce input size and rate limits.
        logger.emit(logging.DEBUG, "web.terminal.send.finish", {"status": "accepted"})  # Log no content.
        return payload  # Preserve accepted byte and queue fields.

    def resize(self, session_id: str, columns: int, rows: int) -> dict[str, object]:
        """Send a checked terminal size."""
        self._require_ready()  # A terminal requires the production manager.
        logger.emit(logging.INFO, "web.terminal.resize.start", {"count": 2})  # Do not log remote dimensions.
        payload = self._gateway.resize(session_id, columns, rows)  # Enforce terminal size ranges.
        logger.emit(logging.DEBUG, "web.terminal.resize.finish", {"status": "accepted"})  # Confirm resize.
        return payload  # Preserve the stored size response.

    def _require_ready(self) -> None:
        """Raise when the WebSocket engine is not ready."""
        if self._reason is not None:  # Missing credentials or imports block terminal actions.
            raise StreamRequestError("not_ready", self._reason)  # Preserve the contract error.
