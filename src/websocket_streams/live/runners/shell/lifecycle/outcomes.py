"""Map terminal connection ends to stable session outcomes."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # Outcome actions use structured JSON records.
import threading  # A stop request changes the final session state.

from src.websocket_streams.live.runners.shell.lifecycle.contracts import TerminalConfiguration
from src.websocket_streams.live.sessions.record.state import SessionSink, SessionState  # Outcomes finish the session.
from src.websocket_streams.live.transport.runtime.logging.structured_logger import StructuredTransportLogger
from src.websocket_streams.live.transport.runtime.reader.contracts import ConnectionClosed  # Close data selects state.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Apply the shared bounded logging boundary.


class OutcomeReasons:
    """Hold shared terminal end reasons."""

    STOPPED = "The operator stopped the session."  # An operator or reaper requested the close.
    DROPPED = "The connection to the device dropped."  # The peer vanished without a close frame.
    NO_ANSWER = (  # Issue #3710 requires one stable operator instruction.
        "The device sent no output before the Mist cloud closed the terminal. Start a new session after one minute."
    )
    WRITE_FAILED = "The terminal could not send data to the device."  # A local input or resize write failed.


class TerminalOutcomes:
    """Finish one terminal session with the correct state and reason."""

    def __init__(self, stopping: threading.Event, sink: SessionSink, configuration: TerminalConfiguration) -> None:
        """Store the final-state inputs."""
        self._stopping = stopping  # A requested stop wins over other close outcomes.
        self._sink = sink  # The session receives one final state and reason.
        self._configuration = configuration  # The terminal mode supplies its normal close text.
        self.output_seen = False  # Issue #3710 distinguishes silent connections from answered terminals.

    def note_output(self) -> None:
        """Record that the device sent terminal output."""
        self.output_seen = True  # Set the flag before deferred input can fail.

    def finish(self, closed: ConnectionClosed) -> None:
        """Map one connection close and finish the session."""
        override = self._configuration.behavior.closed_override()  # A screen limit can finish successfully.
        if self._stopping.is_set():  # Only an explicit stop produces the stopped state.
            result = (SessionState.STOPPED, OutcomeReasons.STOPPED)
        elif override is not None:  # A mode-specific successful end precedes shared failure rules.
            result = override
        elif not self.output_seen:  # Issue #3710 requires a silent close to fail with a next step.
            result = (SessionState.FAILED, OutcomeReasons.NO_ANSWER)
        elif not closed.dropped:  # Issue #3741 maps a failed local write to a failed session.
            result = (SessionState.FAILED, OutcomeReasons.WRITE_FAILED)
        elif closed.code is not None:  # A device close frame after output is a normal end.
            result = (SessionState.FINISHED, self._configuration.closed_reason)
        else:  # A lost connection after output is a transport failure.
            result = (SessionState.FAILED, OutcomeReasons.DROPPED)
        logger.emit(logging.INFO, "terminal_outcome_started", {"status": result[0].value})  # Log before the finish.
        self._sink.finish(*result)  # Publish the stable final state and reason.
        logger.emit(logging.DEBUG, "terminal_outcome_completed", {"status": result[0].value})  # Log the result.

    def fail(self, reason: str) -> None:
        """Finish an open failure unless a stop request won."""
        state = SessionState.STOPPED if self._stopping.is_set() else SessionState.FAILED  # Preserve stop precedence.
        final_reason = OutcomeReasons.STOPPED if state == SessionState.STOPPED else reason  # Use plain public text.
        logger.emit(logging.WARNING, "terminal_failure_started", {"status": state.value})  # Log before the finish.
        self._sink.finish(state, final_reason)  # Publish the failure without secret transport data.
        logger.emit(logging.DEBUG, "terminal_failure_completed", {"status": state.value})  # Log after the finish.
