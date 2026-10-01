"""Hold terminal state and read payloads for issue #3671.

Why:
    Issue #3671 needs one shared state object per terminal session. The web
    routes read the history, the size, the read-only flag, and the expiry from
    that object.
"""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import base64  # Terminal read answers carry bytes as base64 text.
import logging  # Terminal state changes need operator-safe logs.
import threading  # Web threads can resize while runner threads close.
from dataclasses import dataclass  # The terminal size is a small value object.

from src.websocket_streams.intake.fields import StreamRequestError  # Size refusals use shared codes.
from src.websocket_streams.live.terminal.byte_history import ByteHistory, HistoryRead  # State owns byte history.
from src.websocket_streams.live.terminal.input_queue import TerminalInput  # Shell sessions own input queues.

logger = logging.getLogger(__name__)  # Keep terminal state logs under this module.


@dataclass(slots=True)
class TerminalSize:
    """The visible size of one terminal."""

    cols: int = 80  # Most terminal sessions start with 80 columns.
    rows: int = 24  # Most terminal sessions start with 24 rows.


@dataclass(frozen=True, slots=True)
class TerminalStatus:
    """The session status fields for one terminal read answer."""

    state: str  # The page shows the session state.
    reason: str  # The page shows the end reason.
    input_ready: bool  # The page enables input after first output.


class TerminalState:
    """Thread-safe terminal state for one shell or screen session."""

    def __init__(
        self, history: ByteHistory, input_queue: TerminalInput | None, expires_mono: float, expires_at: str
    ) -> None:
        """Build one terminal state.

        Args:
            history: The byte history for terminal output.
            input_queue: The input queue, or None for read-only terminals.
            expires_mono: The monotonic expiry time.
            expires_at: The UTC expiry text for the browser.
        """
        self.history = history  # The gateway reads output through this history.
        self.input = input_queue  # None marks a read-only screen command.
        self.expires_mono = expires_mono  # The page can warn before this time.
        self.expires_at = expires_at  # The read answer returns this public time.
        self._size = TerminalSize()  # Start with the default terminal size.
        self._lock = threading.RLock()  # Resizes and reads share the size state.

    @property
    def read_only(self) -> bool:
        """Return whether this terminal refuses input and resize."""
        return self.input is None  # Screen command terminals have no input queue.

    def size(self) -> TerminalSize:
        """Return a copy of the terminal size.

        Returns:
            The current terminal size.
        """
        with self._lock:  # Copy both values from the same resize.
            return TerminalSize(self._size.cols, self._size.rows)  # Return a copy so callers cannot mutate state.

    def set_size(self, cols: int, rows: int) -> None:
        """Set the terminal size after range checks.

        Args:
            cols: The terminal column count.
            rows: The terminal row count.

        Raises:
            StreamRequestError: The size is outside the contract range.
        """
        if not 20 <= cols <= 500:  # Columns outside the contract range are invalid.
            raise StreamRequestError("bad_request", "The terminal column count is not valid.")  # Contract error.
        if not 5 <= rows <= 200:  # Rows outside the contract range are invalid.
            raise StreamRequestError("bad_request", "The terminal row count is not valid.")  # Contract error.
        logger.info("Setting terminal size cols=%s rows=%s", cols, rows)  # Log only size numbers.
        with self._lock:  # The page and runner can resize at the same time.
            self._size = TerminalSize(cols, rows)  # Replace the value object atomically.
        logger.debug("Set terminal size cols=%s rows=%s", cols, rows)  # Log the stored size.

    def close(self) -> None:
        """Close the history and the input queue."""
        logger.info("Closing terminal state")  # Log before closing child state.
        self.history.close()  # Wake each read that waits on output.
        if self.input is not None:  # Read-only terminals have no input queue.
            self.input.close()  # Refuse later input and drop queued text.
        logger.debug("Closed terminal state")  # Log after closing child state.


class TerminalChunk:
    """Build the JSON payload of a terminal read answer."""

    def __init__(self, read: HistoryRead, status: TerminalStatus, terminal: TerminalState) -> None:
        """Build one terminal read chunk.

        Args:
            read: The byte history answer.
            status: The session status fields.
            terminal: The terminal state for read-only and expiry fields.
        """
        self._read = read  # The payload uses the history cursor values.
        self._status = status  # The payload uses these session status fields.
        self._terminal = terminal  # The payload uses terminal read-only and expiry fields.

    @property
    def data_text(self) -> str:
        """Return the base64 terminal data text."""
        return base64.b64encode(self._read.data).decode("ascii")  # Base64 is safe JSON text.

    def payload(self) -> dict[str, object]:
        """Return the terminal read answer payload.

        Returns:
            The JSON-safe terminal read answer.
        """
        return {
            "data": self.data_text,  # The browser decodes the terminal bytes.
            "first": self._read.first,  # The browser detects retained history from this value.
            "next": self._read.next_position,  # The browser sends this cursor on the next read.
            "gap": self._read.gap,  # The browser shows the count of lost bytes.
            "state": self._status.state,  # The browser shows the session state.
            "reason": self._status.reason,  # The browser shows the end reason.
            "input_ready": self._status.input_ready,  # The browser enables input after first output.
            "read_only": self._terminal.read_only,  # The browser disables input for screen commands.
            "expires_at": self._terminal.expires_at,  # The browser shows the expiry notice.
        }


__all__ = ["TerminalChunk", "TerminalSize", "TerminalState", "TerminalStatus"]  # Export the shared state interface.
