"""Own session completion, stop, input, read, and payload behavior."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # Lifecycle actions use the shared structured logger.
import threading  # Lifecycle methods share the session lock.
from collections.abc import Callable  # The session injects a monotonic clock.

from src.mist.realtime.websocket_streams.catalog.model import Safety  # Payload safety follows the selected definition.
from src.mist.realtime.websocket_streams.live.sessions.record.state import (
    SessionAttributes,
    SessionCounters,
    SessionState,
)  # Stable public values.
from src.mist.realtime.websocket_streams.live.terminal.state.terminal_state import (
    TerminalState,
)  # Final states close terminal work.


class SessionLifecycle(SessionAttributes):
    """Own final state, stop state, input readiness, reads, and payloads."""

    _lock: threading.RLock  # Runner and web threads share this record lock.
    _clock: Callable[[], float]  # State times use the injected monotonic clock.
    terminal: TerminalState | None  # Terminal sessions close child state at finish.
    counters: SessionCounters  # Payloads expose these counters.
    state: SessionState  # Public state changes under the lock.

    def finish(self, state: SessionState, reason: str) -> None:
        """Set the first final result and close terminal state."""
        terminal = None  # Close child state after the record lock releases.
        with self._lock:  # Two callbacks can try to finish together.
            if not self.live:  # The first final result already won.
                return  # Later close events cannot change the outcome.
            self._log_state("session_finish_start", state.value, logging.INFO)  # Log state only.
            self._set_final_state(state, reason)  # Preserve stop reasons and public times.
            terminal = self.terminal  # Copy the terminal reference for safe close.
        if terminal is not None:  # Message-list sessions have no terminal child state.
            terminal.close()  # Wake reads and reject later input.

    def request_stop(self, reason: str) -> bool:
        """Mark the session stopping and preserve the first stop reason."""
        with self._lock:  # A stop request can race with a final callback.
            if not self.live or self.state == SessionState.STOPPING:  # Ended and repeated stops change nothing.
                return False  # The manager can return the current payload.
            self._log_state("session_stop_start", "stopping", logging.INFO)  # Log bounded state only.
            self.state = SessionState.STOPPING  # The runner now owns the close.
            self.reason, self.stop_requested = reason, True  # Preserve the original stop cause.
            self.stopping_mono = self._clock()  # Reaper logic detects a stuck stop.
            self._log_state("session_stop_complete", "stopping", logging.DEBUG)  # Confirm safely.
            return True  # The manager must wake the runner.

    def mark_input_ready(self) -> None:
        """Release queued shell input one time."""
        terminal_input = None  # Network sends must run outside the session lock.
        with self._lock:  # The reader thread owns the first-output transition.
            if self.input_ready:  # Later output must not release the queue again.
                return  # The first output already opened input.
            self.input_ready = True  # The manager can now accept direct shell input.
            terminal_input = self.terminal.input if self.terminal is not None else None  # Copy the queue reference.
        if terminal_input is not None:  # Read-only terminal sessions have no queue.
            terminal_input.release()  # Send queued early input in exact order.

    def mark_read(self) -> None:
        """Record one successful page read."""
        with self._lock:  # The reaper reads this value concurrently.
            self.last_read_mono = self._clock()  # Reset the idle interval.

    def payload(self) -> dict[str, object]:
        """Return one consistent public session payload."""
        with self._lock:  # Build all fields from one state snapshot.
            definition = self.request.definition  # Output and safety use the selected definition.
            output = "json" if self.request.kind == "channel" else getattr(definition, "output", "lines")  # Renderer.
            safety = (
                Safety.READ.value
                if self.request.kind == "channel"
                else getattr(definition, "safety", Safety.READ).value
            )
            return self._payload_values(output, safety)  # Build the stable route contract.
