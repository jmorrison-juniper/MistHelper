"""Coordinate all state for one WebSocket stream session."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # State transitions use the shared structured logger.
import threading  # SDK callbacks and web requests share one record.
from collections import deque  # The message rate keeps recent receive times.
from datetime import UTC, datetime  # Public times use UTC text.

from src.websocket_streams.intake.start_request.models import StartRequest  # Sessions retain checked requests.
from src.websocket_streams.live.sessions.buffer.message import StreamMessage  # Counter updates use accepted records.
from src.websocket_streams.live.sessions.record.lifecycle import SessionLifecycle  # Own lifecycle behavior.
from src.websocket_streams.live.sessions.record.output import SessionOutput  # Own output behavior.
from src.websocket_streams.live.sessions.record.state import (
    SessionAttributes,
    SessionCounters,
    SessionResources,
    SessionState,
)  # Values.
from src.websocket_streams.live.transport.runtime.logging.structured_logger import StructuredTransportLogger  # T072.


class SessionStateSupport(SessionAttributes):
    """Provide state, rate, time, and message counter helpers."""

    def _trim_rate(self, now: float) -> None:
        """Drop rate samples older than ten seconds."""
        while self._rate_times and now - self._rate_times[0] > 10.0:  # Keep only the newest rate interval.
            self._rate_times.popleft()  # Remove the oldest sample first.

    def _rate_per_second(self) -> float:
        """Return the newest ten-second message rate."""
        now = self._clock()  # Use the injected clock for deterministic tests.
        self._trim_rate(now)  # Remove expired samples before counting.
        return round(len(self._rate_times) / 10.0, 1)  # Preserve one decimal place.

    @staticmethod
    def _utc_text() -> str:
        """Return current UTC time with a trailing Z."""
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")  # Preserve public format.

    def _mark_live_state(self) -> None:
        """Apply the connecting-to-live transition."""
        if not self.live or self.state != SessionState.CONNECTING:  # Ended and stopping sessions keep their state.
            return  # The first final or stop result wins.
        self._log_state("session_live_start", "live", logging.INFO)  # Log state only.
        self.state = SessionState.LIVE  # The stream can now receive output.
        self._log_state("session_live_complete", "live", logging.DEBUG)  # Confirm safely.

    def _sync_message_counters(self, message: StreamMessage) -> None:
        """Mirror bounded message totals into the public counters."""
        self.counters.received = message.seq  # Sequence numbers equal accepted message count.
        self.counters.dropped = self.buffer.dropped  # Mirror removed message count.
        self.counters.shortened = self.buffer.shortened  # Mirror shortened message count.
        self.counters.bytes = self.buffer.bytes_used  # Mirror retained message memory.


class SessionPayloadSupport(SessionAttributes):
    """Provide terminal storage, final-state, payload, and safe log helpers."""

    def _store_bytes(self, data: bytes) -> None:
        """Store exact terminal bytes and update public counters."""
        now = self._clock()  # Use one time for rate changes.
        terminal = self.terminal  # Read the optional terminal state once.
        if terminal is None:  # Reject an invalid direct call instead of relying on an assertion.
            raise RuntimeError("Terminal state is required for byte output.")  # Preserve data instead of losing it.
        terminal.history.append(data)  # Preserve exact output bytes in terminal history.
        self._rate_times.append(now)  # Count this output chunk in the rate window.
        self._trim_rate(now)  # Keep only recent rate samples.
        self.counters.received += 1  # Terminal chunks count as received messages.
        self.counters.bytes += len(data)  # Terminal counters show received output bytes.

    def _set_final_state(self, state: SessionState, reason: str) -> None:
        """Store one final state and preserve an earlier stop cause."""
        keep_stop = state == SessionState.STOPPED and self.stop_requested and bool(self.reason)  # Keep reaper cause.
        self.state = state  # Store the first final state.
        self.reason = self.reason if keep_stop else reason  # Preserve issue #3671 stop semantics.
        self.ended_mono = self._clock()  # Retention uses a monotonic end time.
        self.ended_at = self._utc_text()  # Public payloads use UTC text.
        self._log_state("session_finish_complete", state.value, logging.DEBUG)  # Log state only.

    def _payload_values(self, output: str, safety: str) -> dict[str, object]:
        """Return the stable public payload values."""
        return {
            "session_id": self.session_id,
            "kind": self.request.kind,
            "key": self.request.key,
            "title": self.request.title,
            "output": output,
            "safety": safety,
            "state": self.state.value,
            "live": self.live,
            "reason": self.reason,
            "input_ready": self.input_ready,
            "terminal": self.terminal is not None,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "counters": self.counters.to_payload(),
            "rate_per_second": self._rate_per_second(),
            "last_seq": self.buffer.last_seq,
        }  # Preserve every existing list and read payload field.

    @staticmethod
    def _log_state(event: str, status: str, level: int) -> None:
        """Write one bounded structured state event."""
        logger = StructuredTransportLogger(logging.getLogger(__name__))  # Apply the shared safe boundary.
        logger.emit(level, event, {"status": status})  # Log no title, identifier, reason, or output.


class StreamSession(SessionOutput, SessionLifecycle, SessionStateSupport, SessionPayloadSupport):
    """Coordinate thread-safe output, lifecycle, and public payload state."""

    LIVE_STATES = {SessionState.CONNECTING, SessionState.LIVE, SessionState.STOPPING}  # These states count as live.

    def __init__(self, session_id: str, request: StartRequest, resources: SessionResources) -> None:
        """Build one connecting stream session."""
        self.session_id, self.request = session_id, request  # Public identity stays immutable.
        self.buffer, self.terminal = resources.buffer, resources.terminal  # Store bounded child state.
        self._clock, self._lock = resources.clock, threading.RLock()  # Coordinate deterministic thread-safe work.
        self.state, self.reason = SessionState.CONNECTING, ""  # Each session starts without an end reason.
        self.started_mono = resources.clock()  # Reaper decisions use monotonic time.
        self.last_read_mono = self.started_mono  # A new session starts as recently read.
        self.ended_mono = self.stopping_mono = None  # Live sessions have no end or stop time.
        self.started_at, self.ended_at = self._utc_text(), None  # Public times use UTC text.
        self.input_ready = self.stop_requested = False  # Input and stop signals start closed.
        self.counters, self._rate_times = SessionCounters(), deque()  # Start public counts and rate empty.
        self.runner: object | None = None  # The manager attaches the runner after construction.

    @property
    def live(self) -> bool:
        """Return whether this session counts against the live limit."""
        return self.state in self.LIVE_STATES  # The manager uses the stable state set.
