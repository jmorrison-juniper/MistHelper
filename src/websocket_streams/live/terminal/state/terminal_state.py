"""Coordinate shared state for one terminal session."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # State actions use the shared structured logger.

from src.websocket_streams.live.terminal.byte_history import ByteHistory  # State owns terminal history.
from src.websocket_streams.live.terminal.input_queue import TerminalInput  # Shell sessions own input queues.
from src.websocket_streams.live.terminal.state.size import TerminalSize  # Size state uses one value object.
from src.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # Use the shared bounded logger from T072.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Apply the shared logging boundary.


class TerminalState:
    """Coordinate thread-safe state for one terminal session."""

    def __init__(
        self, history: ByteHistory, input_queue: TerminalInput | None, expires_mono: float, expires_at: str
    ) -> None:
        """Build one terminal state."""
        self.history = history  # The gateway reads output through this history.
        self.input = input_queue  # None marks a read-only screen command.
        self.expires_mono = expires_mono  # The reaper compares this monotonic expiry.
        self.expires_at = expires_at  # The read answer returns this public UTC expiry.
        self._size = TerminalSize()  # Start with the default terminal size.

    @property
    def read_only(self) -> bool:
        """Return whether this terminal refuses input and resize."""
        return self.input is None  # Screen command terminals have no input queue.

    def size(self) -> TerminalSize:
        """Return a copy of the terminal size."""
        current = self._size  # Read one atomically replaced size object.
        return TerminalSize(current.cols, current.rows)  # Prevent callers from mutating stored state.

    def set_size(self, cols: int, rows: int) -> None:
        """Set the terminal size after range checks."""
        size = TerminalSize.checked(cols, rows)  # Refuse invalid dimensions before any state change.
        fields = {"count": cols, "code": rows}  # Log only bounded numeric dimensions.
        logger.emit(logging.INFO, "terminal_size_set_start", fields)  # Log before the atomic state change.
        self._size = size  # Replace both dimensions through one atomic reference assignment.
        logger.emit(logging.DEBUG, "terminal_size_set_complete", fields)  # Log the bounded result.

    def close(self) -> None:
        """Close the history and the input queue."""
        logger.emit(logging.INFO, "terminal_state_close_start")  # Log before closing child state.
        self.history.close()  # Wake each read that waits on output.
        if self.input is not None:  # Read-only terminals have no input queue.
            self.input.close()  # Refuse later input and drop queued text.
        logger.emit(logging.DEBUG, "terminal_state_close_complete", {"status": "closed"})  # Log the result.
