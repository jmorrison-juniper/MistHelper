"""Run owned Mist WebSocket channel connections with bounded retries."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # Connection actions use structured JSON records.
import threading  # The reader runs outside the web request thread.
import time  # A monotonic clock measures stable subscribed operation.

from src.websocket_streams.intake.start_request.models import StartRequest  # The runner accepts checked requests.
from src.websocket_streams.live.runners.channel.contracts import AttemptResult, ChannelRunnerState  # State contracts.
from src.websocket_streams.live.runners.channel.retry import ChannelRetryController  # Retry and finish ownership.
from src.websocket_streams.live.runners.channel.routing import ChannelEventRouter  # Event shaping and source routing.
from src.websocket_streams.live.sessions.record.state import (  # Runner outcomes use session states.
    SessionSink,
    SessionState,
)
from src.websocket_streams.live.transport.endpoint import MistStreamEndpoint  # The endpoint owns connection values.
from src.websocket_streams.live.transport.runtime.frame_decoder import SubscribeError  # Subscription refusal contract.
from src.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # T072 supplies the bounded JSON logging boundary.
from src.websocket_streams.live.transport.runtime.reader.contracts import ConnectionClosed  # Closed connection result.
from src.websocket_streams.live.transport.stream_client import StreamClient  # The owned stream transport client.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Apply one safe structured logger.

HEALTHY_OPERATION_SECONDS = 5.0  # A quiet connection must stay stable before retries reset.


class ChannelHealthClassifier:
    """Classify dropped connections from bounded health evidence."""

    @staticmethod
    def classify(state: ChannelRunnerState) -> AttemptResult:
        """Return a healthy or unhealthy drop result."""
        status, operation_seconds = ChannelHealthClassifier._status(state)  # Measure one drop.
        fields = {"status": status.value, "timeout_seconds": operation_seconds}
        logger.emit(logging.DEBUG, "channel_drop_classified", fields)  # Log bounded health evidence only.
        return status  # Reset retries only after an event or five stable seconds.

    @staticmethod
    def _status(state: ChannelRunnerState) -> tuple[AttemptResult, float]:
        """Return the drop status and subscribed operation time."""
        subscribed_at = state.attempt.subscribed_at  # Read the attempt time once.
        if subscribed_at is None:  # A connection that never subscribed did not operate.
            return AttemptResult.DROPPED, 0.0  # Preserve the current retry budget.
        operation_seconds = time.monotonic() - subscribed_at  # Measure subscribed operation.
        status = (
            AttemptResult.HEALTHY_DROP
            if state.attempt.received_event or operation_seconds >= HEALTHY_OPERATION_SECONDS
            else AttemptResult.DROPPED
        )  # Preserve #3740 reset rules.
        return status, operation_seconds  # Report only bounded health evidence.


class ChannelAttemptReader:
    """Open subscriptions and read events for one connection attempt."""

    def __init__(self, state: ChannelRunnerState, router: ChannelEventRouter) -> None:
        """Build one channel attempt reader."""
        self._state = state  # Read and write current attempt health state.
        self._router = router  # Mark live and deliver decoded events.

    def read(self, client: StreamClient) -> AttemptResult:
        """Open subscriptions, read events, and classify a normal end."""
        if not self._open_if_running(client):  # Do not open a client after an operator stop.
            return AttemptResult.STOPPED  # The outer runner records the stopped state.
        if self._state.runtime.stop.is_set():  # A stop after open must not leave a live stream.
            return AttemptResult.STOPPED  # The outer runner records the stopped state.
        self._run(client)  # Read and route events until close or drop.
        if self._state.runtime.stop.is_set():  # A stop during reading is a local outcome.
            return AttemptResult.STOPPED  # Do not classify a local stop as a dropped connection.
        return ChannelHealthClassifier.classify(self._state)  # Apply event-or-five-seconds health rules.

    def _open_if_running(self, client: StreamClient) -> bool:
        """Open subscriptions only while the runner accepts new work."""
        if self._state.runtime.stop.is_set():  # A completed stop prohibits a new connection.
            return False  # Leave the client unopened after the stop request.
        self._open(client)  # Complete every subscription before the session becomes live.
        return True  # Tell the reader that the connection opened.

    def _open(self, client: StreamClient) -> None:
        """Open all subscriptions and record attempt start state."""
        logger.emit(logging.INFO, "channel_transport_open_started")  # Log before the network action.
        client.open()  # Complete every subscription before the session becomes live.
        logger.emit(logging.DEBUG, "channel_transport_open_completed", {"status": "subscribed"})
        self._state.attempt.subscribed_at = time.monotonic()  # Start the stable-operation interval.
        self._state.outcome.last_open_failure = None  # A successful subscribe replaces an old failure.

    def _run(self, client: StreamClient) -> None:
        """Mark the session live and read decoded events."""
        self._router.mark_live()  # Preserve one live transition for each successful connection.
        logger.emit(logging.INFO, "channel_event_read_started")  # Log before the long-running read.
        client.run(self._router.deliver)  # Read and route events until close or drop.
        logger.emit(logging.DEBUG, "channel_event_read_completed", {"status": "ended"})  # Confirm completion.


class ChannelAttemptFailure:
    """Map known attempt failures to stable results."""

    def __init__(self, state: ChannelRunnerState, retry: ChannelRetryController) -> None:
        """Build one known-failure mapper."""
        self._state = state  # Subscription and close results use current attempt state.
        self._retry = retry  # Permanent subscription refusals finish through one owner.

    def result(self, error: SubscribeError | ConnectionClosed) -> AttemptResult:
        """Return the stable result for one known transport failure."""
        if isinstance(error, SubscribeError):  # Subscription failures use timeout and refusal rules.
            return self._subscription(error)  # Preserve existing subscription semantics.
        if not error.dropped:  # A clean local close is an operator stop.
            return AttemptResult.STOPPED  # Do not reconnect after a local close.
        return ChannelHealthClassifier.classify(self._state)  # Classify a dropped subscribed connection.

    def unexpected(self, error: Exception) -> AttemptResult:
        """Map an unexpected open or read failure through the safe classifier."""
        return self._retry.failure_result(error)  # Preserve refusal and retry behavior.

    def _subscription(self, error: SubscribeError) -> AttemptResult:
        """Map a subscription timeout or refusal to its stable result."""
        if error.detail == "timeout":  # A missing answer can heal on a later connection.
            self._state.outcome.last_open_failure = None  # Do not report an older open failure.
            logger.emit(logging.DEBUG, "channel_subscribe_timeout", {"status": "retry"})  # Log safe retry state.
            return AttemptResult.DROPPED  # The outer runner consumes one retry.
        reason = f"The stream subscription failed: {error.detail}."  # Preserve the existing safe reason.
        self._retry.finish(SessionState.FAILED, reason)  # Subscription refusal ends without a retry.
        return AttemptResult.FINAL  # The session already holds its final result.


class ChannelConnectionAttempt:
    """Open, read, classify, and close one channel connection."""

    def __init__(
        self,
        endpoint: MistStreamEndpoint,
        state: ChannelRunnerState,
        router: ChannelEventRouter,
        retry: ChannelRetryController,
    ) -> None:
        """Build one reusable connection attempt."""
        self._endpoint = endpoint  # Each attempt opens with the same safe endpoint.
        self._state = state  # Stop and health signals stay shared with the runner.
        self._reader = ChannelAttemptReader(state, router)  # Own subscription and event reading.
        self._failure = ChannelAttemptFailure(state, retry)  # Own known failure mapping.
        self._paths = router.paths  # The client subscribes to each checked private path.

    def run(self) -> AttemptResult:
        """Run one connection attempt and return its retry result."""
        client = self._prepare_client()  # Reset health state and expose the active client to stop().
        try:  # Convert transport outcomes into stable attempt results.
            return self._reader.read(client)  # Open and read until stop or connection end.
        except (SubscribeError, ConnectionClosed) as error:  # Known failures keep stable semantics.
            return self._failure.result(error)  # Preserve timeout, refusal, close, and drop behavior.
        except Exception as error:  # Open and read failures use the safe failure mapper.
            return self._failure.unexpected(error)  # Preserve client refusal and retry semantics.
        finally:
            logger.emit(logging.INFO, "channel_transport_close_started")  # Log before resource cleanup.
            client.close()  # Ensure every attempt releases its socket.
            logger.emit(logging.DEBUG, "channel_transport_close_completed", {"status": "closed"})  # Confirm cleanup.

    def _prepare_client(self) -> StreamClient:
        """Build one client and reset current attempt health state."""
        client = StreamClient(self._endpoint, self._paths)  # Watch every checked channel path.
        self._state.runtime.client = client  # stop() can close this client from another thread.
        self._state.attempt.received_event = False  # This connection must prove its own operation.
        self._state.attempt.subscribed_at = None  # A new attempt has not completed subscriptions.
        return client  # The caller owns open, read, and close actions.


class ChannelStreamRunner:
    """Drive the owned WebSocket client for one channel request."""

    def __init__(self, endpoint: MistStreamEndpoint, request: StartRequest, sink: SessionSink) -> None:
        """Build one channel runner."""
        self._state = ChannelRunnerState()  # Group mutable runtime, outcome, and attempt state.
        self._retry = ChannelRetryController(endpoint, self._state, sink)  # Own retries and final outcomes.
        router = ChannelEventRouter(request, sink, self._state)  # Own message shaping and event routing.
        self._attempt = ChannelConnectionAttempt(endpoint, self._state, router, self._retry)  # Own one attempt.

    def start(self) -> None:
        """Start the connection loop and return."""
        logger.emit(logging.INFO, "channel_runner_start_started")  # Log before the thread starts.
        thread = threading.Thread(target=self._run, name="ws-channel", daemon=True)  # Run outside the request.
        self._state.runtime.thread = thread  # Keep the thread for bounded runtime state.
        thread.start()  # Return immediately while the reader connects.
        logger.emit(logging.DEBUG, "channel_runner_start_completed", {"status": "started"})  # Confirm start.

    def stop(self) -> None:
        """Ask the connection to close and return."""
        logger.emit(logging.INFO, "channel_runner_stop_started")  # Log before the stop request.
        self._state.runtime.stop.set()  # Wake a reconnect wait or read loop.
        client = self._state.runtime.client  # Copy the current client reference.
        if client is not None:  # A stop before the first open is valid.
            client.close()  # Close can run from any thread.
        logger.emit(logging.DEBUG, "channel_runner_stop_completed", {"status": "requested"})  # Confirm request.

    def _run(self) -> None:
        """Run connection attempts until stop or final failure."""
        failures = 0  # Failure count resets only after measurable healthy operation.
        while not self._state.runtime.stop.is_set():  # stop() ends reconnect and read loops.
            logger.emit(logging.INFO, "channel_attempt_started", {"count": failures + 1})  # Log safe attempt count.
            result = self._attempt.run()  # Open and read one complete connection attempt.
            next_failures = self._retry.advance(result, failures)  # Apply final, reset, and retry rules.
            if next_failures is None:  # Stop, refusal, or exhaustion ended the sequence.
                return  # The retry controller recorded a final state when required.
            failures = next_failures  # Continue with the consecutive failure count.
