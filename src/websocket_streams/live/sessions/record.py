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
from collections.abc import Callable  # The manager injects a fake clock.
from dataclasses import dataclass  # Counters are a small value record.
from datetime import UTC, datetime  # Public payload times use UTC text.
from enum import StrEnum  # The state values are also their JSON text.
from typing import Protocol  # Runners depend on the sink behavior only.

from src.websocket_streams.catalog.model import Safety  # Payload safety depends on the definition.
from src.websocket_streams.intake.start_request import StartRequest  # A session is created from a checked request.
from src.websocket_streams.live.sessions.buffer import MessageBuffer, StreamMessage  # The buffer keeps the records.
from src.websocket_streams.live.terminal.state import TerminalState  # Terminal sessions keep raw byte history.

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
    bytes: int = 0  # The memory that the kept messages use, in bytes. The byte cap applies to this value.

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

    terminal: TerminalState | None  # Shell and screen runners read the stored terminal size at open.

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

    def add_bytes(self, data: bytes) -> None:
        """Add raw terminal output bytes.

        Args:
            data: The raw terminal output bytes.
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
        self,
        session_id: str,
        request: StartRequest,
        buffer: MessageBuffer,
        clock: Callable[[], float],
        terminal: TerminalState | None = None,
    ) -> None:
        """Build one stream session.

        Args:
            session_id: The public session identifier.
            request: The checked start request.
            buffer: The bounded message buffer.
            clock: The monotonic clock for age and rate calculations.
            terminal: The terminal state, or None for a message-list session.
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
        self.terminal = terminal  # Terminal sessions expose byte history through this state.

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
            if self.state == SessionState.CONNECTING:  # A stop in progress must stay in the stopping state.
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
            self.counters.bytes = self.buffer.bytes_used  # Mirror the buffer memory total.

    def add_bytes(self, data: bytes) -> None:
        """Add raw terminal bytes unless the session ended.

        Args:
            data: The raw terminal output bytes.
        """
        logger.debug(
            "Adding terminal bytes to WebSockets session %s length=%s", self.session_id, len(data)
        )  # Debug level: a busy shell sends many chunks, and the log never holds the bytes.
        with self._lock:  # Terminal history and counters must change together.
            if not self.live or self.terminal is None:  # Ended or non-terminal sessions ignore raw bytes.
                logger.debug("Ignored terminal bytes for WebSockets session %s", self.session_id)  # Safe state log.
                return  # Late callbacks cannot change an ended session.
            now = self._clock()  # Use one time value for rate and counters.
            self.terminal.history.append(data)  # Store raw bytes for terminal reads.
            self._rate_times.append(now)  # Count the output message in the rate window.
            self._trim_rate(now)  # Keep only the newest ten seconds.
            self.counters.received += 1  # Terminal output chunks count as messages on the card.
            self.counters.bytes += len(data)  # Terminal byte count shows received output bytes.
        logger.debug("Added terminal bytes to WebSockets session %s length=%s", self.session_id, len(data))  # Safe log.

    def read_records(self, after: int, limit: int) -> tuple[list[StreamMessage], int, bool]:
        """Copy the kept records after a sequence number.

        Args:
            after: The newest sequence number that the page has.
            limit: The largest count of messages to return.

        Returns:
            The records, the first kept sequence, and the gap flag.
        """
        logger.debug("Reading WebSockets session %s messages", self.session_id)  # Debug level: the page polls often.
        with self._lock:  # A runner callback can add a message while the buffer copies its records.
            records, first_seq, gap = self.buffer.read_after(after, limit)  # Copy the record references only.
        logger.debug("Read %s WebSockets session messages", len(records))  # Log the result count.
        return records, first_seq, gap  # The manager formats the records outside the lock.

    def snapshot_records(self) -> list[StreamMessage]:
        """Copy every kept record for a download.

        Returns:
            The records in sequence order.
        """
        logger.info("Preparing the WebSockets session %s download", self.session_id)  # Log before the copy.
        with self._lock:  # A runner callback can add a message while the buffer copies its records.
            records = self.buffer.snapshot()  # Copy the record references only.
        logger.debug("Prepared %s WebSockets download messages", len(records))  # Log the result count.
        return records  # The manager formats one record at a time while the file streams.

    def finish(self, state: SessionState, reason: str) -> None:
        """Set the first final state of the session.

        Args:
            state: The final state.
            reason: The plain reason for the operator.
        """
        terminal: TerminalState | None = None  # Close outside the record lock.
        with self._lock:  # Two callbacks can try to finish at the same time.
            if not self.live:  # The first final state already won.
                return  # Later close events do not change the outcome.
            logger.info("Finishing WebSockets session %s", self.session_id)  # Log before the state change.
            keep_stop_reason = state == SessionState.STOPPED and self.stop_requested and bool(self.reason)  # #3671.
            self.state = state  # Store the final state.
            self.reason = self.reason if keep_stop_reason else reason  # An idle stop or a life stop keeps its cause.
            self.ended_mono = self._clock()  # Store a monotonic age for the reaper.
            self.ended_at = self._utc_text()  # Store a public UTC end time.
            terminal = self.terminal  # Copy the terminal so close can run outside the record lock.
            logger.debug("Finished WebSockets session %s state=%s", self.session_id, state.value)  # Log safe metadata.
        if terminal is not None:  # Non-terminal sessions have no history to close.
            terminal.close()  # Wake any terminal read that waits for output.

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
        """Allow input for a shell session, and send the early input one time."""
        terminal_input = None  # Release outside the record lock because it sends to the network.
        with self._lock:  # The shell reader thread changes this flag.
            if self.input_ready:  # A runner can report each output, but the queue opens one time.
                return  # The early input already went to the device.
            logger.info("Marking WebSockets session %s input ready", self.session_id)  # Log before the state change.
            self.input_ready = True  # The manager now accepts shell input.
            terminal_input = self.terminal.input if self.terminal is not None else None  # Copy the input queue.
            logger.debug("Marked WebSockets session %s input ready", self.session_id)  # Log after the state change.
        if terminal_input is not None:  # Read-only terminals have no input to release.
            terminal_input.release()  # Send queued early input outside the record lock.

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
                "terminal": self.terminal is not None,  # The page chooses the terminal panel from this flag.
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
