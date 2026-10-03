"""Provide bounded terminal operations for web routes in issue #3671."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # Structured events use standard logging levels.
import threading  # Long-poll reads share one process-wide wait cap.
from abc import abstractmethod  # Protocol methods are explicit abstract methods.
from typing import TYPE_CHECKING, Protocol, runtime_checkable  # Keep session types out of runtime imports.

from src.mist.realtime.websocket_streams.intake.fields.error import (
    StreamRequestError,
)  # Contract refusals use shared codes.
from src.mist.realtime.websocket_streams.live.terminal.input_queue import TerminalInput  # Writable terminals use input.
from src.mist.realtime.websocket_streams.live.terminal.state.chunk_payload import (
    TerminalChunk,
)  # Build terminal read payloads.
from src.mist.realtime.websocket_streams.live.terminal.state.status import TerminalStatus  # Hold terminal read status.
from src.mist.realtime.websocket_streams.live.terminal.state.terminal_state import (
    TerminalState,
)  # Hold shared terminal state.
from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # Use the shared bounded logger from T072.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Apply the shared logging boundary.

if TYPE_CHECKING:  # Runtime gateway imports must not load session construction dependencies.
    from src.mist.realtime.websocket_streams.live.sessions.record.session import (
        StreamSession,
    )  # Lookups return session records.


@runtime_checkable
class TerminalRunner(Protocol):
    """Define writable terminal runner operations."""

    def send_input(self, text: str) -> None:
        """Send exact terminal input text."""

    def resize(self, cols: int, rows: int) -> None:
        """Send a terminal size to the device."""


@runtime_checkable
class SessionLookup(Protocol):
    """Define terminal session lookup behavior."""

    @abstractmethod
    def session(self, session_id: str) -> StreamSession:
        """Return one session or raise a contract error."""


class TerminalSessionAccess:
    """Resolve terminal state and writable session context."""

    def __init__(self, sessions: SessionLookup) -> None:
        """Store the session lookup service."""
        self._sessions = sessions  # The session manager owns records and refusal behavior.

    def session(self, session_id: str) -> StreamSession:
        """Return the selected session."""
        return self._sessions.session(session_id)  # Preserve manager lookup behavior.

    def terminal(self, session: StreamSession) -> TerminalState:
        """Return terminal state or refuse another session type."""
        terminal = session.terminal  # Terminal sessions carry this state.
        if terminal is None:  # Message-list sessions are not terminals.
            raise StreamRequestError("not_terminal", "The session is not a terminal.")  # Refuse it.
        return terminal  # The caller can use terminal operations.

    def input_context(self, session: StreamSession) -> tuple[TerminalState, TerminalInput]:
        """Return writable terminal state and input."""
        terminal = self.terminal(session)  # Refuse sessions without terminal state.
        if terminal.input is None:  # Screen command terminals are read-only.
            raise StreamRequestError("read_only", "The terminal is read-only.")  # Refuse it.
        return terminal, terminal.input  # Return one checked input context.


class WaitingReadRegistry:
    """Reserve and release process-wide long-poll slots."""

    LIMIT = 8  # The portal process permits eight waiting terminal reads.

    def __init__(self) -> None:
        """Build an empty waiting-read registry."""
        self._lock = threading.Lock()  # The count is shared by all terminal sessions.
        self.count = 0  # No long-poll read waits at startup.

    def reserve(self, wait_seconds: float) -> float:
        """Reserve one slot and return the effective wait."""
        if wait_seconds <= 0.0:  # An immediate read needs no slot.
            return 0.0  # The history read returns at once.
        with self._lock:  # The count must change atomically.
            if self.count >= self.LIMIT:  # All process-wide slots already wait.
                return 0.0  # The extra read returns at once.
            self.count += 1  # Reserve one slot for this read.
        return wait_seconds  # The caller may now block.

    def release(self, wait_seconds: float) -> None:
        """Release a slot when the read reserved one."""
        if wait_seconds <= 0.0:  # An immediate read reserved no slot.
            return  # Keep the current count unchanged.
        with self._lock:  # The count must change atomically.
            self.count -= 1  # Make the slot available to another read.


class TerminalGateway:
    """Validate route requests and coordinate terminal collaborators."""

    MAX_WAIT_SECONDS = 25.0  # One read waits at most 25 seconds.
    MAX_INPUT_BYTES = 16 * 1024  # One input request accepts at most 16 KiB.

    def __init__(self, sessions: SessionLookup) -> None:
        """Build one terminal gateway."""
        self._access = TerminalSessionAccess(sessions)  # Centralize terminal session checks.
        self._waits = WaitingReadRegistry()  # Share the process-wide long-poll cap.

    @property
    def _waiting_reads(self) -> int:
        """Return the current waiting-read count for focused diagnostics."""
        return self._waits.count  # Tests observe the process-wide reservation count.

    def read(self, session_id: str, after: int, wait_seconds: float) -> dict[str, object]:
        """Read terminal bytes after one absolute position."""
        if isinstance(after, bool) or not isinstance(after, int) or after < 0:  # Require a nonnegative integer.
            raise StreamRequestError("bad_request", "The terminal read position is not valid.")  # Refuse it.
        if isinstance(wait_seconds, bool) or not isinstance(wait_seconds, (int, float)):  # Require a number.
            raise StreamRequestError("bad_request", "The terminal wait time is not valid.")  # Refuse it.
        if wait_seconds < 0.0:  # Negative waits are invalid.
            raise StreamRequestError("bad_request", "The terminal wait time is not valid.")  # Refuse it.
        session = self._access.session(session_id)  # Preserve lookup and not-found behavior.
        terminal = self._access.terminal(session)  # Refuse sessions without terminal state.
        session.mark_read()  # A read keeps the idle reaper from stopping the session.
        actual_wait = self._waits.reserve(min(wait_seconds, self.MAX_WAIT_SECONDS))  # Apply both wait caps.
        try:  # Always release the process-wide slot.
            read = terminal.history.read(after, actual_wait)  # Read or wait for output bytes.
        finally:  # A history refusal must also release the slot.
            self._waits.release(actual_wait)  # Immediate reads change no reservation count.
        status = TerminalStatus(session.state.value, session.reason, session.input_ready)  # Copy metadata.
        payload = TerminalChunk(read, status, terminal).payload()  # Build the JSON-safe route answer.
        logger.emit(logging.DEBUG, "terminal_gateway_read_complete", {"byte_count": len(read.data)})  # Log size.
        return payload  # Return the contract payload.

    def send(self, session_id: str, data: str) -> dict[str, object]:
        """Send input text to a writable terminal session."""
        if not isinstance(data, str) or data == "":  # The route requires nonempty text.
            raise StreamRequestError("bad_request", "The terminal input is not valid.")  # Refuse it.
        session = self._access.session(session_id)  # Preserve lookup and not-found behavior.
        _terminal, terminal_input = self._access.input_context(session)  # Check terminal and write state.
        count = terminal_input.rate.check()  # Count input before the size check.
        if not session.live:  # Ended sessions cannot accept input.
            raise StreamRequestError("not_open", "The terminal session is not open.")  # Refuse it.
        accepted = len(data.encode("utf-8"))  # The contract counts UTF-8 bytes.
        if accepted > self.MAX_INPUT_BYTES:  # One request cannot exceed 16 KiB.
            raise StreamRequestError("too_large", "The terminal input is too large.")  # Refuse it.
        fields = {"byte_count": accepted, "count": count}  # Log bounded operational values only.
        logger.emit(logging.INFO, "terminal_gateway_send_start", fields)  # Never log input text.
        queued = terminal_input.submit(data)  # Queue or send the exact text.
        result_fields = {"byte_count": accepted, "status": "queued" if queued else "sent"}  # Safe fields.
        logger.emit(logging.DEBUG, "terminal_gateway_send_complete", result_fields)  # Log the result.
        return {"accepted": accepted, "queued": queued}  # Return the contract payload.

    def resize(self, session_id: str, cols: int, rows: int) -> dict[str, object]:
        """Resize a writable terminal session."""
        session = self._access.session(session_id)  # Preserve lookup and not-found behavior.
        terminal, terminal_input = self._access.input_context(session)  # Check terminal and write state.
        count = terminal_input.rate.check()  # Resize shares the session request cap.
        if not session.live:  # Ended sessions cannot accept resize.
            raise StreamRequestError("not_open", "The terminal session is not open.")  # Refuse it.
        terminal.set_size(cols, rows)  # Store the size after contract range checks.
        runner = session.runner  # The session record holds the active runner.
        if isinstance(runner, TerminalRunner):  # Writable runners accept resize frames.
            runner.resize(cols, rows)  # Send the accepted size to the device.
        fields = {"count": count, "detail": f"{cols}x{rows}"}  # Bound the safe request result.
        logger.emit(logging.DEBUG, "terminal_gateway_resize_complete", fields)  # Log without session data.
        return {"cols": cols, "rows": rows}  # Return the accepted size.
