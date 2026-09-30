"""Hold one live WebSocket stream session.

Why:
    Issue #3551. SDK callbacks can arrive on threads that the portal did not
    start. Each callback writes through this record, so the state, counters,
    and buffer must stay consistent across Gunicorn and SDK threads.
"""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # The session logs each state change.
import threading  # The session protects its state with a lock.
from collections import deque  # The rate window uses the newest receive times.
from collections.abc import Callable  # The manager injects a fake clock in tests.
from dataclasses import dataclass  # Counters are a small value record.
from datetime import UTC, datetime  # Public payload times use UTC text.
from enum import StrEnum  # The state values are also their JSON text.
from typing import Protocol  # Runners depend on the sink behavior only.

from src.websocket_streams.catalog.model import Safety  # Payload safety depends on the definition.
from src.websocket_streams.intake.start_request import StartRequest  # A session is created from a checked request.
from src.websocket_streams.live.sessions.buffer import MessageBuffer  # The bounded buffer stores messages.

logger = logging.getLogger(__name__)  # Keep session log records under this module.


class SessionState(StrEnum):
    """The state of one stream session."""

    CONNECTING = "connecting"  # The runner started, but no live signal arrived.
    LIVE = "live"  # The stream accepts more output.
    STOPPING = "stopping"  # A stop request reached the runner.
    STOPPED = "stopped"  # The stream stopped after an operator or reaper request.
    FINISHED = "finished"  # A utility ended after it sent output.
    TIMED_OUT = "timed_out"  # A utility ended without output.
    FAILED = "failed"  # Mist or the SDK reported a failure.


@dataclass(slots=True)
class SessionCounters:
    """The message counters of one session."""

    received: int = 0  # Count every accepted message.
    dropped: int = 0  # Count messages removed by the buffer caps.
    shortened: int = 0  # Count messages shortened by the single-message cap.
    bytes: int = 0  # Count bytes currently in the buffer.

    def to_payload(self) -> dict[str, int]:
        """Return the public counter payload.

        Returns:
            The JSON-safe counter dictionary.
        """
        return {
            "received": self.received,  # The card shows all accepted messages.
            "dropped": self.dropped,  # The card warns when old messages left.
            "shortened": self.shortened,  # The card marks large-message shortening.
            "bytes": self.bytes,  # The card can show memory use.
        }


class SessionSink(Protocol):
    """The methods that runners call on a session."""

    def mark_live(self, note: str = "") -> None:
        """Mark the session as live.

        Args:
            note: An optional status line for the message buffer.
        """

    def add_message(self, kind: str, content: object, *, source: str | None = None, summary: str | None = None) -> None:
        """Add one message from a runner.

        Args:
            kind: The message kind.
            content: The page-safe content.
            source: The repeated identifier value, or None.
            summary: The packet summary, or None.
        """

    def finish(self, state: SessionState, reason: str) -> None:
        """End the session.

        Args:
            state: The final state.
            reason: The plain end reason.
        """

    def mark_input_ready(self) -> None:
        """Allow shell input after the first output."""


class StreamSession:
    """The thread-safe state and message sink of one stream session."""

    LIVE_STATES = {
        SessionState.CONNECTING,
        SessionState.LIVE,
        SessionState.STOPPING,
    }  # These states count against the limit.

    def __init__(
        self, session_id: str, request: StartRequest, buffer: MessageBuffer, clock: Callable[[], float]
    ) -> None:
        """Build one stream session.

        Args:
            session_id: The public session identifier.
            request: The checked start request.
            buffer: The bounded message buffer.
            clock: The monotonic clock for age and rate calculations.
        """
        self.session_id = session_id  # The browser names the session with this value.
        self.request = request  # The runner and payload use the checked request.
        self.buffer = buffer  # The buffer owns the message caps.
        self._clock = clock  # A fake clock keeps tests fast.
        self._lock = threading.RLock()  # SDK callbacks and web requests can overlap.
        self.state = SessionState.CONNECTING  # Every session starts while the runner connects.
        self.reason = ""  # A live session has no end reason.
        self.started_mono = clock()  # Reaper decisions use monotonic time.
        self.last_read_mono = self.started_mono  # A new session is fresh.
        self.ended_mono: float | None = None  # Live sessions have no end time.
        self.stopping_mono: float | None = None  # Stopping sessions use this for stuck-stop detection.
        self.started_at = self._utc_text()  # Public payload time.
        self.ended_at: str | None = None  # Public payload end time.
        self.input_ready = False  # Shell input opens only after first output.
        self.stop_requested = False  # Runners use this to choose the final state.
        self.counters = SessionCounters()  # The card reads these counters.
        self._rate_times: deque[float] = deque()  # Only the last ten seconds matter.
        self.runner: object | None = None  # The manager sets the runner after build.

    @property
    def live(self) -> bool:
        """Return whether the session still counts as live."""
        return self.state in self.LIVE_STATES  # The manager uses this for the limit.

    def mark_live(self, note: str = "") -> None:
        """Mark the session as live, and add an event when supplied.

        Args:
            note: An optional event line.
        """
        with self._lock:  # A callback can race with a stop request.
            if not self.live:  # Ended sessions ignore late callbacks.
                return  # The first final state wins.
            logger.info("Marking WebSockets session %s live", self.session_id)  # Log before the state change.
            self.state = SessionState.LIVE  # The stream can now receive messages.
            logger.debug("Marked WebSockets session %s live", self.session_id)  # Log after the state change.
        if note:  # A status note becomes a visible event.
            self.add_message("event", note)  # Reuse the normal message path.

    def add_message(self, kind: str, content: object, *, source: str | None = None, summary: str | None = None) -> None:
        """Add one message unless the session ended.

        Args:
            kind: The message kind.
            content: The message content.
            source: The repeated identifier value, or None.
            summary: The packet summary, or None.
        """
        with self._lock:  # The buffer and counters must change together.
            if not self.live:  # Ended sessions ignore late SDK callbacks.
                return  # A late callback cannot change an ended session.
            now = self._clock()  # Use one time value for rate and read logic.
            message = self.buffer.add(self._utc_text(), kind, content, source, summary)  # Store the message.
            self._rate_times.append(now)  # Count the message in the rate window.
            self._trim_rate(now)  # Keep only ten seconds of rate data.
            self.counters.received = message.seq  # Sequence numbers equal accepted count.
            self.counters.dropped = self.buffer.dropped  # Mirror the buffer drop count.
            self.counters.shortened = self.buffer.shortened  # Mirror the buffer shortening count.
            self.counters.bytes = self.buffer.bytes_used  # Mirror the buffer byte count.

    def finish(self, state: SessionState, reason: str) -> None:
        """Set the first final state of the session.

        Args:
            state: The final state.
            reason: The plain reason for the operator.
        """
        with self._lock:  # Two callbacks can try to finish at the same time.
            if not self.live:  # The first final state already won.
                return  # Later close events do not change the outcome.
            logger.info("Finishing WebSockets session %s", self.session_id)  # Log before the state change.
            self.state = state  # Store the final state.
            self.reason = reason  # Store the reason for the page.
            self.ended_mono = self._clock()  # Store a monotonic age for the reaper.
            self.ended_at = self._utc_text()  # Store a public UTC end time.
            logger.debug("Finished WebSockets session %s state=%s", self.session_id, state.value)  # Log safe metadata.

    def request_stop(self, reason: str) -> bool:
        """Mark the session as stopping.

        Args:
            reason: The reason that the manager sends to the runner.

        Returns:
            True when this call changed the state.
        """
        with self._lock:  # A stop request can race with a final callback.
            if not self.live:  # Ended sessions need no runner call.
                return False  # The caller can return the existing payload.
            if self.state == SessionState.STOPPING:  # A previous stop already ran.
                return False  # Stop is safe to repeat.
            logger.info("Stopping WebSockets session %s", self.session_id)  # Log before the state change.
            self.state = SessionState.STOPPING  # The runner now owns the close.
            self.reason = reason  # The page can show why the stop started.
            self.stop_requested = True  # Runners map close events to stopped.
            self.stopping_mono = self._clock()  # The reaper marks stuck stops after this time.
            logger.debug("Stopping WebSockets session %s requested", self.session_id)  # Log after the state change.
            return True  # The caller should call the runner.

    def mark_input_ready(self) -> None:
        """Allow input for a shell session."""
        with self._lock:  # The shell reader thread changes this flag.
            logger.info("Marking WebSockets session %s input ready", self.session_id)  # Log before the state change.
            self.input_ready = True  # The manager now accepts shell input.
            logger.debug("Marked WebSockets session %s input ready", self.session_id)  # Log after the state change.

    def mark_read(self) -> None:
        """Record that a page read the session."""
        with self._lock:  # The reaper reads this value.
            self.last_read_mono = self._clock()  # The session is no longer idle.

    def payload(self) -> dict[str, object]:
        """Return the public session payload.

        Returns:
            The session object for list and read routes.
        """
        with self._lock:  # Build a consistent snapshot.
            rate = self._rate_per_second()  # Calculate the newest message rate.
            definition = self.request.definition  # The payload needs the output and safety.
            output = (
                "json" if self.request.kind == "channel" else getattr(definition, "output", "lines")
            )  # Channel output is JSON.
            safety = (
                Safety.READ.value
                if self.request.kind == "channel"
                else getattr(definition, "safety", Safety.READ).value
            )  # Channel streams are read-only.
            return {
                "session_id": self.session_id,  # The browser uses this identifier.
                "kind": self.request.kind,  # The page groups sessions by kind.
                "key": self.request.key,  # The catalog key names the command.
                "title": self.request.title,  # The operator-facing title.
                "output": output,  # The page picks the renderer from this value.
                "safety": safety,  # The page can show the safety class.
                "state": self.state.value,  # The page shows the current state.
                "live": self.live,  # The page enables live controls from this flag.
                "reason": self.reason,  # The page shows the end or stop reason.
                "input_ready": self.input_ready,  # The shell input uses this flag.
                "started_at": self.started_at,  # The page shows the start time.
                "ended_at": self.ended_at,  # Live sessions return None here.
                "counters": self.counters.to_payload(),  # The card shows these counters.
                "rate_per_second": rate,  # The card shows the recent rate.
                "last_seq": self.buffer.last_seq,  # The message poll cursor uses this value.
            }

    def _rate_per_second(self) -> float:
        """Return the message rate over the newest ten seconds."""
        now = self._clock()  # Use the injected clock for deterministic tests.
        self._trim_rate(now)  # Drop old timestamps before counting.
        return round(len(self._rate_times) / 10.0, 1)  # The contract asks for one decimal place.

    def _trim_rate(self, now: float) -> None:
        """Drop rate samples older than ten seconds.

        Args:
            now: The current monotonic time.
        """
        while self._rate_times and now - self._rate_times[0] > 10.0:  # Only the newest ten seconds count.
            self._rate_times.popleft()  # Drop the oldest rate sample.

    def _utc_text(self) -> str:
        """Return the current UTC time in the public format."""
        return (
            datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        )  # The contract wants a trailing Z.
