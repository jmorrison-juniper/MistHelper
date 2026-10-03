"""Own message and terminal output for one stream session."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # Output actions use the shared structured logger.
import threading  # Output and web reads share one record lock.
from collections import deque  # The rate window keeps recent receive times.
from collections.abc import Callable  # The session injects a monotonic clock.

from src.mist.realtime.websocket_streams.live.sessions.buffer.message import (
    MessageDraft,
    StreamMessage,
)  # Buffer message records.
from src.mist.realtime.websocket_streams.live.sessions.buffer.message_buffer import (
    MessageBuffer,
)  # Store bounded message records.
from src.mist.realtime.websocket_streams.live.sessions.record.state import (
    SessionAttributes,
    SessionCounters,
)  # Shared state.
from src.mist.realtime.websocket_streams.live.terminal.state.terminal_state import (
    TerminalState,
)  # Terminal sessions keep byte history.
from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # T072.


class SessionOutput(SessionAttributes):
    """Own accepted output and consistent read snapshots."""

    _lock: threading.RLock  # SDK callbacks and web requests share this lock.
    _clock: Callable[[], float]  # Rate calculations use the injected clock.
    _rate_times: deque[float]  # Keep only the newest ten seconds.
    buffer: MessageBuffer  # Message-list sessions store records here.
    terminal: TerminalState | None  # Terminal sessions store exact bytes here.
    counters: SessionCounters  # Public payloads expose these values.

    def mark_live(self, note: str = "") -> None:
        """Mark a connecting session live and add an optional event."""
        with self._lock:  # A live callback can race with a stop request.
            self._mark_live_state()  # Preserve a stopping state and the first final result.
        if note:  # A supplied status note becomes a visible event.
            self.add_message("event", note)  # Reuse the normal bounded message path.

    def add_message(self, kind: str, content: object, **metadata: str | None) -> None:
        """Add one message unless the session ended."""
        with self._lock:  # The buffer and counters must change together.
            if not self.live:  # Ended sessions ignore late callbacks.
                return  # The first final state remains unchanged.
            now = self._clock()  # Use one time for rate and counter changes.
            draft = MessageDraft(
                self._utc_text(), kind, content, metadata.get("source"), metadata.get("summary")
            )  # Shape input.
            message = self.buffer.add(draft)  # Store the compact bounded message.
            self._rate_times.append(now)  # Count the accepted message in the rate window.
            self._trim_rate(now)  # Keep only recent samples.
            self._sync_message_counters(message)  # Mirror the bounded buffer totals.

    def add_bytes(self, data: bytes) -> None:
        """Add raw terminal bytes unless the session ended."""
        logger = StructuredTransportLogger(logging.getLogger(__name__))  # Use the shared content-free boundary.
        logger.emit(logging.DEBUG, "session_terminal_bytes_start", {"byte_count": len(data)})  # Log size only.
        with self._lock:  # Terminal history and counters change together.
            if not self.live or self.terminal is None:  # Ignore late or non-terminal output.
                logger.emit(logging.DEBUG, "session_terminal_bytes_complete", {"status": "ignored"})  # Record outcome.
                return  # Do not change ended or message-list sessions.
            self._store_bytes(data)  # Preserve exact bytes and update rate counters.
        logger.emit(logging.DEBUG, "session_terminal_bytes_complete", {"status": "stored"})  # Confirm safely.

    def read_records(self, after: int, limit: int) -> tuple[list[StreamMessage], int, bool]:
        """Copy kept records after one sequence cursor."""
        with self._lock:  # Runner callbacks can add while the page reads.
            return self.buffer.read_after(after, limit)  # Copy immutable record references.

    def snapshot_records(self) -> list[StreamMessage]:
        """Copy every kept record for one download."""
        with self._lock:  # Runner callbacks can add while the page copies.
            return self.buffer.snapshot()  # Share immutable record content.
