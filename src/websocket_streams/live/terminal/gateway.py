"""Provide terminal operations for web routes in issue #3671.

Why:
    Issue #3671 adds terminal HTTP routes. The routes need one small gateway
    that finds sessions, checks the terminal contract, and never exposes typed
    text or output bytes in logs.
"""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # The gateway logs identifiers and counts only.
import threading  # Long-poll reads need one shared waiting-read cap.
from abc import abstractmethod  # Protocol methods are explicit abstract methods.
from typing import Protocol, runtime_checkable  # Protocols keep the gateway decoupled from runners.

from src.websocket_streams.intake.fields import StreamRequestError  # Contract refusals use shared codes.
from src.websocket_streams.live.sessions.record import StreamSession  # The lookup returns session records.
from src.websocket_streams.live.terminal.input_queue import TerminalInput  # Writable terminals use this queue.
from src.websocket_streams.live.terminal.state import (
    TerminalChunk,
    TerminalState,
    TerminalStatus,
)  # Payloads come from terminal state.

logger = logging.getLogger(__name__)  # Keep terminal gateway logs under this module.


@runtime_checkable
class TerminalRunner(Protocol):
    """The runner behavior needed for a writable terminal."""

    def send_input(self, text: str) -> None:
        """Send text to the device.

        Args:
            text: The exact terminal input text.
        """

    def resize(self, cols: int, rows: int) -> None:
        """Send a terminal size to the device.

        Args:
            cols: The column count.
            rows: The row count.
        """


@runtime_checkable
class SessionLookup(Protocol):
    """The session lookup behavior that terminal routes need."""

    @abstractmethod
    def session(self, session_id: str) -> StreamSession:
        """Return a session or raise a contract error.

        Args:
            session_id: The public session identifier.

        Returns:
            The matching session.
        """


class TerminalGateway:
    """Validate terminal route requests and operate on sessions."""

    MAX_WAIT_SECONDS = 25.0  # One read waits at most 25 seconds.
    MAX_WAITING_READS = 8  # The portal process permits 8 waiting terminal reads.
    MAX_INPUT_BYTES = 16 * 1024  # One input route request accepts at most 16 KiB.

    def __init__(self, sessions: SessionLookup) -> None:
        """Build one terminal gateway.

        Args:
            sessions: The session lookup service.
        """
        self._sessions = sessions  # The web service injects the session manager.
        self._wait_lock = threading.Lock()  # The wait counter is shared across sessions.
        self._waiting_reads = 0  # The process-wide long-poll count starts empty.

    def read(self, session_id: str, after: int, wait_seconds: float) -> dict[str, object]:
        """Read terminal bytes after one position.

        Args:
            session_id: The session identifier.
            after: The absolute byte position.
            wait_seconds: The requested wait time.

        Returns:
            The terminal read payload.
        """
        self._check_read_values(after, wait_seconds)  # Refuse invalid cursors and waits before lookup.
        session = self._sessions.session(session_id)  # Let the manager raise not_found.
        terminal = self._terminal(session)  # Refuse sessions without terminal state.
        session.mark_read()  # A terminal read keeps the idle reaper from stopping the session.
        actual_wait = self._reserve_wait(min(wait_seconds, self.MAX_WAIT_SECONDS))  # Enforce process-wide wait cap.
        try:  # Always release the waiting-read slot.
            read = terminal.history.read(after, actual_wait)  # Read or wait for output bytes.
        finally:  # A raised read still frees the slot.
            self._release_wait(actual_wait)  # No slot was reserved when actual wait is zero.
        status = TerminalStatus(session.state.value, session.reason, session.input_ready)  # Copy session metadata.
        chunk = TerminalChunk(read, status, terminal)  # Join history data with terminal metadata.
        payload = chunk.payload()  # Build the route answer.
        logger.debug("Read terminal session %s bytes=%s", session_id, len(read.data))  # Log only byte count.
        return payload  # The route returns this JSON-safe dictionary.

    def send(self, session_id: str, data: str) -> dict[str, object]:
        """Send input text to a terminal session.

        Args:
            session_id: The session identifier.
            data: The exact terminal input text.

        Returns:
            The accepted byte count and queued flag.
        """
        if not isinstance(data, str) or data == "":  # The input route requires non-empty text.
            raise StreamRequestError("bad_request", "The terminal input is not valid.")  # Contract error.
        session = self._sessions.session(session_id)  # Let the manager raise not_found.
        terminal = self._terminal(session)  # Refuse sessions without terminal state.
        input_queue = self._input(terminal)  # Refuse read-only terminals.
        input_queue.check_rate()  # Count each input request before size checks.
        self._check_live(session)  # Ended sessions accept no input.
        accepted = len(data.encode("utf-8"))  # The contract counts UTF-8 bytes.
        if accepted > self.MAX_INPUT_BYTES:  # One request cannot exceed 16 KiB.
            raise StreamRequestError("too_large", "The terminal input is too large.")  # Contract error.
        logger.info("Sending terminal input for session %s bytes=%s", session_id, accepted)  # Never log text.
        queued = input_queue.submit(data)  # Queue or send the exact text.
        logger.debug("Sent terminal input for session %s bytes=%s queued=%s", session_id, accepted, queued)  # Safe log.
        return {"accepted": accepted, "queued": queued}  # The route returns the contract payload.

    def resize(self, session_id: str, cols: int, rows: int) -> dict[str, object]:
        """Resize a writable terminal session.

        Args:
            session_id: The session identifier.
            cols: The column count.
            rows: The row count.

        Returns:
            The accepted terminal size.
        """
        session = self._sessions.session(session_id)  # Let the manager raise not_found.
        terminal = self._terminal(session)  # Refuse sessions without terminal state.
        input_queue = self._input(terminal)  # Refuse read-only terminals.
        input_queue.check_rate()  # Resize shares the per-session request rate cap.
        self._check_live(session)  # Ended sessions accept no resize.
        terminal.set_size(cols, rows)  # Store the size after range checks.
        runner = session.runner  # The manager stores the active runner on the record.
        if isinstance(runner, TerminalRunner):  # Shell runners can receive resize frames.
            runner.resize(cols, rows)  # Send each accepted size to the device.
        logger.debug("Resized terminal session %s cols=%s rows=%s", session_id, cols, rows)  # Log safe size data.
        return {"cols": cols, "rows": rows}  # The route returns the accepted size.

    def _terminal(self, session: StreamSession) -> TerminalState:
        """Return terminal state or refuse a non-terminal session.

        Args:
            session: The session record.

        Returns:
            The terminal state.
        """
        terminal = session.terminal  # Terminal sessions carry this state.
        if terminal is None:  # Message-list sessions are not terminals.
            raise StreamRequestError("not_terminal", "The session is not a terminal.")  # Contract error.
        return terminal  # Callers can now use terminal operations.

    def _input(self, terminal: TerminalState) -> TerminalInput:
        """Return input queue or refuse a read-only terminal.

        Args:
            terminal: The terminal state.

        Returns:
            The terminal input queue.
        """
        if terminal.input is None:  # Screen commands are read-only.
            raise StreamRequestError("read_only", "The terminal is read-only.")  # Contract error.
        return terminal.input  # The caller can send input or count rate.

    def _check_live(self, session: StreamSession) -> None:
        """Refuse when a session is not live.

        Args:
            session: The session record.

        Raises:
            StreamRequestError: The session is not live.
        """
        if not session.live:  # Ended sessions cannot send input or size.
            raise StreamRequestError("not_open", "The terminal session is not open.")  # Contract error.

    def _check_read_values(self, after: int, wait_seconds: float) -> None:
        """Refuse invalid read values.

        Args:
            after: The absolute byte position.
            wait_seconds: The requested wait time.
        """
        if isinstance(after, bool) or not isinstance(after, int) or after < 0:  # The cursor must be an integer.
            raise StreamRequestError("bad_request", "The terminal read position is not valid.")  # Contract error.
        if isinstance(wait_seconds, bool) or not isinstance(wait_seconds, (int, float)):  # Wait must be numeric.
            raise StreamRequestError("bad_request", "The terminal wait time is not valid.")  # Contract error.
        if wait_seconds < 0.0:  # Negative waits are invalid.
            raise StreamRequestError("bad_request", "The terminal wait time is not valid.")  # Contract error.

    def _reserve_wait(self, wait_seconds: float) -> float:
        """Reserve one waiting-read slot when available.

        Args:
            wait_seconds: The requested bounded wait.

        Returns:
            The effective wait value.
        """
        if wait_seconds <= 0.0:  # No wait needs no slot.
            return 0.0  # The history read returns at once.
        with self._wait_lock:  # The wait count is process-wide.
            if self._waiting_reads >= self.MAX_WAITING_READS:  # Too many long polls already wait.
                return 0.0  # The contract answers at once with no data.
            self._waiting_reads += 1  # Reserve one process-wide wait slot.
        return wait_seconds  # The caller may now block.

    def _release_wait(self, wait_seconds: float) -> None:
        """Release one waiting-read slot when one was reserved.

        Args:
            wait_seconds: The effective wait value.
        """
        if wait_seconds <= 0.0:  # No slot was reserved.
            return  # The counter must stay unchanged.
        with self._wait_lock:  # The wait count is process-wide.
            self._waiting_reads -= 1  # Release one slot for another read.


__all__ = ["SessionLookup", "TerminalGateway", "TerminalRunner"]  # Export the route-facing gateway API.
