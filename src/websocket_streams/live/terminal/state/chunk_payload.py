"""Build the JSON payload for one terminal read."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import base64  # Terminal read answers carry bytes as base64 text.
import logging  # Payload actions use the shared structured logger.

from src.websocket_streams.live.terminal.byte_history import HistoryRead  # Payloads use history cursor values.
from src.websocket_streams.live.terminal.state.status import TerminalStatus  # Payloads include session status.
from src.websocket_streams.live.terminal.state.terminal_state import TerminalState  # Payloads include terminal state.
from src.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # Use the shared bounded logger from T072.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Apply the shared logging boundary.


class TerminalChunk:
    """Build the JSON payload of one terminal read."""

    def __init__(self, read: HistoryRead, status: TerminalStatus, terminal: TerminalState) -> None:
        """Store the read values that form one payload."""
        self._read = read  # The payload uses the history cursor values.
        self._status = status  # The payload uses these session status fields.
        self._terminal = terminal  # The payload uses terminal read-only and expiry fields.

    @property
    def data_text(self) -> str:
        """Return the base64 terminal data text."""
        return base64.b64encode(self._read.data).decode("ascii")  # Base64 is safe JSON text.

    def payload(self) -> dict[str, object]:
        """Return the terminal read payload."""
        logger.emit(
            logging.DEBUG,
            "terminal_chunk_payload_start",
            {"byte_count": len(self._read.data), "status": self._status.state},
        )  # Log bounded metadata without terminal content.
        payload = self._read_fields()  # Build the five history fields first.
        payload.update(self._status_fields())  # Add the four terminal state fields.
        logger.emit(
            logging.DEBUG,
            "terminal_chunk_payload_complete",
            {"byte_count": len(self._read.data), "status": self._status.state},
        )  # Log the bounded result without terminal content.
        return payload  # Return the JSON-safe terminal answer.

    def _read_fields(self) -> dict[str, object]:
        """Return the terminal history payload fields."""
        return {
            "data": self.data_text,  # The browser decodes the terminal bytes.
            "first": self._read.first,  # The browser detects retained history from this value.
            "next": self._read.next_position,  # The browser sends this cursor on the next read.
            "gap": self._read.gap,  # The browser shows the count of lost bytes.
            "state": self._status.state,  # The browser shows the session state.
        }  # Keep each payload mapping within the five-item limit.

    def _status_fields(self) -> dict[str, object]:
        """Return the terminal status payload fields."""
        return {
            "reason": self._status.reason,  # The browser shows the end reason.
            "input_ready": self._status.input_ready,  # The browser enables input after first output.
            "read_only": self._terminal.read_only,  # The browser disables input for screen commands.
            "expires_at": self._terminal.expires_at,  # The browser shows the expiry notice.
        }  # Keep the existing terminal HTTP payload shape.
