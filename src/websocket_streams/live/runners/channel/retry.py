"""Own retry budgets and final channel runner outcomes."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # Retry and finish actions use structured JSON records.
from collections.abc import Callable  # The retry budget reports final outcomes through one typed callback.

from src.websocket_streams.live.runners.channel.contracts import AttemptResult, ChannelRunnerState  # Retry contracts.
from src.websocket_streams.live.sessions.record.state import (  # Final outcomes use stable states.
    SessionSink,
    SessionState,
)
from src.websocket_streams.live.transport.endpoint import ConnectFailure, MistStreamEndpoint  # Safe failure mapping.
from src.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # T072 supplies the bounded JSON logging boundary.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Apply one safe structured logger.

RETRYABLE_CLIENT_STATUSES = (408, 429)  # Mist can heal these refusals after a wait.


class ChannelFailureClassifier:
    """Classify connection failures without exposing exception content."""

    def __init__(self, state: ChannelRunnerState) -> None:
        """Store the retry state that receives safe failure reasons."""
        self._state = state  # Retry exhaustion reads the last safe open failure.

    def classify(self, error: Exception) -> tuple[AttemptResult, str | None]:
        """Return the attempt result and an optional final reason."""
        reason = ConnectFailure.reason(error)  # Convert the exception to an operator-safe reason.
        if reason is not None and self._is_client_refusal(error):  # Most 4xx failures cannot heal.
            return AttemptResult.FINAL, reason  # The controller sends the final refusal reason.
        self._state.outcome.last_open_failure = reason  # Keep the last safe reason for exhaustion.
        return AttemptResult.DROPPED, None  # Other failures use the configured retry budget.

    @staticmethod
    def _is_client_refusal(error: BaseException) -> bool:
        """Return whether a 4xx failure must fail without a retry."""
        status_code = getattr(error, "status_code", 0)  # websocket-client stores handshake status here.
        return (
            isinstance(status_code, int) and 400 <= status_code <= 499 and status_code not in RETRYABLE_CLIENT_STATUSES
        )  # Retry only timeout and rate-limit client statuses.


class ChannelRetryBudget:
    """Wait within the configured retry budget and finish stopped waits."""

    def __init__(
        self,
        delays: tuple[float, ...],
        state: ChannelRunnerState,
        finish: Callable[[SessionState, str], None],
    ) -> None:
        """Build one retry budget."""
        self._delays = delays  # The profile defines one delay for each retry.
        self._state = state  # Stop and outcome state control retry readiness.
        self._finish = finish  # The owner records stop and exhaustion outcomes.

    def continue_after(self, failures: int) -> bool:
        """Wait for one retry and return whether work can continue."""
        delay = self._delay(failures)  # Validate the budget before any wait.
        if delay is None:  # A final or stopped state already ended the runner.
            return False  # Do not wait or reconnect.
        logger.emit(logging.INFO, "channel_retry_wait_started", {"timeout_seconds": delay})  # Log the safe delay.
        stopped = self._state.runtime.stop.wait(delay)  # Stop wakes the bounded wait immediately.
        return self._complete_wait(stopped)  # Log and map the bounded wait result.

    def _delay(self, failures: int) -> float | None:
        """Return the next delay, or finish when no retry can start."""
        if self._state.outcome.finished:  # A permanent failure already finished the session.
            return None  # Do not retry after a final result.
        if self._state.runtime.stop.is_set():  # A stop during error handling wins.
            self._finish(SessionState.STOPPED, "The operator stopped the session.")  # Preserve stop semantics.
            return None  # Do not retry after an operator stop.
        if failures > len(self._delays):  # The runner used each configured retry delay.
            reason = self._state.outcome.last_open_failure
            self._finish(SessionState.FAILED, reason or "The WebSocket connection failed after retry attempts.")
            return None  # The retry budget is empty.
        return self._delays[failures - 1]  # Failure counts start at one.

    def _complete_wait(self, stopped: bool) -> bool:
        """Log one wait result and finish a stop that occurred during it."""
        status = "stopped" if stopped else "ready"  # Convert the result to bounded status text.
        logger.emit(logging.DEBUG, "channel_retry_wait_completed", {"status": status})  # Log no remote data.
        if stopped:  # A stop during the wait must finish the session now.
            self._finish(SessionState.STOPPED, "The operator stopped the session.")  # Preserve stop semantics.
        return not stopped  # The runner continues only after a complete delay.


class ChannelRetryController:
    """Apply retry budgets and send one final session outcome."""

    def __init__(self, endpoint: MistStreamEndpoint, state: ChannelRunnerState, sink: SessionSink) -> None:
        """Build one retry controller."""
        self._state = state  # Retry decisions read and update shared runner state.
        self._sink = sink  # Final decisions update the session through its protocol.
        self._classifier = ChannelFailureClassifier(state)  # Classify failures without secret content.
        self._budget = ChannelRetryBudget(endpoint.profile.reconnect_delays, state, self.finish)  # Own waits.

    def failure_result(self, error: Exception) -> AttemptResult:
        """Map one open or read failure to a final result or a retry."""
        logger.emit(logging.INFO, "channel_connection_failure_started")  # Log before safe classification.
        result, reason = self._classifier.classify(error)  # Apply safe exception and status rules.
        if reason is not None:  # A permanent refusal includes one operator-safe reason.
            self.finish(SessionState.FAILED, reason)  # Preserve the safe refusal reason.
        logger.emit(logging.DEBUG, "channel_connection_failure_completed", {"status": type(error).__name__})
        return result  # Return the permanent or retryable result.

    def advance(self, result: AttemptResult, failures: int) -> int | None:
        """Return the next failure count, or end the attempt sequence."""
        logger.emit(logging.DEBUG, "channel_attempt_completed", {"status": result.value})  # Log the safe result.
        if result in (AttemptResult.STOPPED, AttemptResult.FINAL):  # Terminal results cannot reconnect.
            if result is AttemptResult.STOPPED:  # A local stop still needs one final session state.
                self.finish(SessionState.STOPPED, "The operator stopped the session.")  # Preserve stop reason.
            return None  # End the connection loop.
        next_failures = 1 if result is AttemptResult.HEALTHY_DROP else failures + 1  # Preserve #3740 reset rules.
        if not self._budget.continue_after(next_failures):  # Stop or exhaustion ends the sequence.
            return None  # The budget owner recorded the final state when required.
        return next_failures  # Continue with the updated consecutive failure count.

    def finish(self, state: SessionState, reason: str) -> None:
        """Send one final state to the session sink."""
        with self._state.outcome.finish_lock:  # Connection and stop paths can finish together.
            if self._state.outcome.finished:  # The first final state wins.
                return  # Do not send a duplicate finish event.
            logger.emit(logging.INFO, "channel_finish_started", {"status": state.value})  # Log safe state only.
            self._state.outcome.finished = True  # Set final state before the external callback.
            self._sink.finish(state, reason)  # Preserve the existing operator-facing reason.
            logger.emit(logging.DEBUG, "channel_finish_completed", {"status": state.value})  # Confirm completion.
