"""Define stable session states, counters, and construction resources."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import threading  # Shared record attributes include the session lock.
from abc import abstractmethod  # Concrete sessions implement shared computed properties.
from collections import deque  # Shared record attributes include recent rate samples.
from collections.abc import Callable  # Tests inject a monotonic clock.
from dataclasses import dataclass  # Session values use small typed records.
from enum import StrEnum  # State values are also their public JSON text.
from typing import Protocol  # Runners depend on session behavior only.

from src.mist.realtime.websocket_streams.intake.start_request.models import (
    StartRequest,
)  # Sessions retain checked requests.
from src.mist.realtime.websocket_streams.live.sessions.buffer.message import (
    StreamMessage,
)  # Helper callables accept message records.
from src.mist.realtime.websocket_streams.live.sessions.buffer.message_buffer import (
    MessageBuffer,
)  # Sessions own bounded messages.
from src.mist.realtime.websocket_streams.live.terminal.state.terminal_state import (
    TerminalState,
)  # Terminal sessions own raw history.


class SessionState(StrEnum):
    """Name each stable session state."""

    CONNECTING = "connecting"  # The runner started, but no live signal arrived.
    LIVE = "live"  # The stream accepts more output.
    STOPPING = "stopping"  # A stop request reached the runner.
    STOPPED = "stopped"  # The stream stopped after an operator or reaper request.
    FINISHED = "finished"  # A utility ended after it sent output.
    TIMED_OUT = "timed_out"  # A utility ended without output.
    FAILED = "failed"  # Mist or the owned transport reported a failure.


@dataclass(slots=True)
class SessionCounters:
    """Hold the public counters of one session."""

    received: int = 0  # Count every accepted message or terminal chunk.
    dropped: int = 0  # Count messages removed by buffer caps.
    shortened: int = 0  # Count messages shortened by the message cap.
    bytes: int = 0  # Count retained message memory or received terminal bytes.

    def to_payload(self) -> dict[str, int]:
        """Return the public counter payload."""
        return {
            "received": self.received,  # The card shows all accepted messages.
            "dropped": self.dropped,  # The card warns when old messages left.
            "shortened": self.shortened,  # The card marks large-message shortening.
            "bytes": self.bytes,  # The card shows the applicable byte count.
        }


@dataclass(frozen=True, slots=True)
class SessionResources:
    """Hold collaborators required to build one stream session."""

    buffer: MessageBuffer  # Message-list sessions keep bounded message records.
    clock: Callable[[], float]  # Reaper and rate decisions use monotonic time.
    terminal: TerminalState | None = None  # Shell and screen sessions keep terminal state.


class SessionSink(Protocol):
    """Describe the session behavior that each runner can use."""

    terminal: TerminalState | None  # Shell and screen runners read stored terminal values.
    state: SessionState  # Runners distinguish opening failures from live failures.

    def mark_live(self, note: str = "") -> None:
        """Mark the session live and optionally add one event."""

    def add_message(self, kind: str, content: object, **metadata: str | None) -> None:
        """Add one page-safe message with optional source metadata."""

    def add_bytes(self, data: bytes) -> None:
        """Add one exact terminal output chunk."""

    def finish(self, state: SessionState, reason: str) -> None:
        """Set the first final session result."""

    def mark_input_ready(self) -> None:
        """Release queued shell input after the first output."""


class SessionAttributes:
    """Declare state shared by the concrete session behavior classes."""

    session_id: str  # Public routes use the hard-to-guess session identifier.
    request: StartRequest  # Payloads and runners use the checked start request.
    buffer: MessageBuffer  # Message-list sessions retain bounded records.
    terminal: TerminalState | None  # Terminal sessions retain exact byte history.
    _clock: Callable[[], float]  # Rate and cleanup values use monotonic time.
    _lock: threading.RLock  # SDK callbacks and web requests share this lock.
    _rate_times: deque[float]  # Rate calculations keep ten seconds of samples.
    state: SessionState  # Public state changes under the session lock.
    reason: str  # Public payloads show one plain stop or end reason.
    started_mono: float  # Cleanup uses monotonic session age.
    last_read_mono: float  # Idle cleanup uses the last successful page read.
    ended_mono: float | None  # Retention uses the final monotonic time.
    stopping_mono: float | None  # Stuck-stop cleanup uses the stop request time.
    started_at: str  # Public payloads show the UTC start time.
    ended_at: str | None  # Public payloads show the UTC end time when present.
    input_ready: bool  # Shell input opens after the first output.
    stop_requested: bool  # Runner outcomes preserve operator stop semantics.
    counters: SessionCounters  # Public payloads expose bounded counters.
    runner: object | None  # The manager attaches one concrete runner.
    _mark_live_state: Callable[[], None]  # Output behavior applies the live transition.
    _utc_text: Callable[[], str]  # State changes create public UTC text.
    _trim_rate: Callable[[float], None]  # Output behavior removes old rate samples.
    _sync_message_counters: Callable[[StreamMessage], None]  # Output mirrors buffer counts.
    _store_bytes: Callable[[bytes], None]  # Output preserves exact terminal bytes.
    _log_state: Callable[[str, str, int], None]  # Lifecycle records bounded state events.
    _set_final_state: Callable[[SessionState, str], None]  # Lifecycle stores one final outcome.
    _payload_values: Callable[[str, str], dict[str, object]]  # Lifecycle builds the route payload.
    _rate_per_second: Callable[[], float]  # Payloads expose the recent message rate.

    @property
    @abstractmethod
    def live(self) -> bool:
        """Return whether the concrete session counts against the live limit."""
