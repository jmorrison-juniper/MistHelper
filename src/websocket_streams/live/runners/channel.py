"""Run a Mist WebSocket channel stream.

Why:
    Issue #3671 removes the private Mist SDK WebSocket dependency. The runner
    uses the owned transport client, keeps Mist paths and credentials on the
    server, and keeps the existing page message shape.
"""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # The runner logs connection state without secrets.
import threading  # The reader runs in a daemon thread.
import time  # The monotonic clock measures stable connection operation.
from dataclasses import dataclass, field  # Runner mutable state stays grouped.

from src.websocket_streams.catalog.model import ChannelDefinition  # Channel runners need channel-only methods.
from src.websocket_streams.intake.fields import StreamRequestError  # Invalid channel requests raise this error.
from src.websocket_streams.intake.start_request import StartRequest  # The request is already checked.
from src.websocket_streams.live.runners.text import MessageShaper  # The shaper decodes channel payloads.
from src.websocket_streams.live.sessions.record import (
    SessionSink,
    SessionState,
)  # The runner writes through this protocol.
from src.websocket_streams.live.transport.endpoint import ConnectFailure, MistStreamEndpoint  # Connection reasons.
from src.websocket_streams.live.transport.frames import ConnectionClosed, SubscribeError  # Transport errors.
from src.websocket_streams.live.transport.stream_client import StreamClient  # The owned stream client.

logger = logging.getLogger(__name__)  # Keep channel runner records under this module.


@dataclass(slots=True)
class _ChannelRunnerState:
    """Mutable state for one channel runner."""

    client: StreamClient | None = None  # stop() closes the live client.
    thread: threading.Thread | None = None  # start() stores the reader thread.
    stop: threading.Event = field(default_factory=threading.Event)  # stop() wakes loops and waits.
    finish_lock: threading.Lock = field(default_factory=threading.Lock)  # Only one final state can win.
    finished: bool = False  # The first finish call wins.
    last_open_failure: str | None = None  # Retry exhaustion reports the last connection failure.
    attempt_received_event: bool = False  # A data event proves that the current connection operated.


class ChannelStreamRunner:
    """Drive the owned WebSocket client for one channel request."""

    _RETRYABLE_CLIENT_STATUSES = (408, 429)  # Mist can heal timeout and rate-limit refusals after a wait.
    _HEALTHY_OPERATION_SECONDS = 5.0  # A quiet connection must stay stable before retries reset.

    def __init__(self, endpoint: MistStreamEndpoint, request: StartRequest, sink: SessionSink) -> None:
        """Build one channel runner.

        Args:
            endpoint: The stream endpoint with authentication and profile data.
            request: The checked channel request.
            sink: The session sink that receives events.
        """
        self._endpoint = endpoint  # The client reads connection values from this endpoint.
        self._request = request  # The checked request builds channel paths.
        self._sink = sink  # The runner reports messages through this sink.
        self._state = _ChannelRunnerState()  # Keep mutable runtime state in one field.
        self._shaper = MessageShaper()  # Channel payloads need nested JSON decoding.
        self._source_by_path = self._build_source_map()  # The page receives an identifier, not a path.

    def start(self) -> None:
        """Start the connection loop and return at once."""
        logger.info("Starting WebSockets channel runner for key %s", self._request.key)  # Log before starting work.
        self._state.thread = threading.Thread(target=self._run, daemon=True)  # One reader serves this runner.
        self._state.thread.start()  # Return immediately to the caller.
        logger.debug("Started WebSockets channel runner for key %s", self._request.key)  # Log safe metadata only.

    def stop(self) -> None:
        """Ask the connection to close and return at once."""
        logger.info("Stopping WebSockets channel runner for key %s", self._request.key)  # Log before stopping work.
        self._state.stop.set()  # Wake a reconnect wait or read loop.
        client = self._state.client  # Copy the current client reference.
        if client is not None:  # A stop before the first open is valid.
            client.close()  # Close can run from any thread.
        logger.debug(
            "Stop requested for WebSockets channel runner key %s", self._request.key
        )  # Log safe metadata only.

    def _run(self) -> None:
        """Run connection attempts until stop or final failure."""
        failures = 0  # Failure count resets only after measurable healthy operation.
        while not self._state.stop.is_set():  # stop() ends reconnect and read loops.
            logger.info("Opening a WebSockets channel connection attempt")  # Log before the connection action.
            result = self._connect_once()  # Open and read one connection attempt.
            logger.debug("WebSockets channel connection attempt ended with result=%s", result)  # Log safe state.
            if result == "stopped":  # The operator stopped the runner.
                self._finish(SessionState.STOPPED, "The operator stopped the session.")  # Keep existing stop reason.
                return  # No reconnect after a local stop.
            if result == "healthy_drop":  # Useful data or stable operation earns a new retry budget.
                logger.info("Resetting the WebSockets channel retry count after healthy operation")  # Log reset.
                failures = 0  # Reset only after the connection proved that it operated.
                logger.debug("Reset the WebSockets channel retry count")  # Confirm the state change.
            failures += 1  # Count this drop or open failure.
            if not self._wait_before_retry(failures):  # Retry budget exhausted or stop occurred.
                return  # The helper recorded the final state when needed.

    def _connect_once(self) -> str:
        """Open one client and run until it closes.

        Returns:
            A state marker for the outer retry loop.
        """
        client = StreamClient(self._endpoint, tuple(self._source_by_path))  # One client watches all channel paths.
        self._state.client = client  # stop() can close this client from another thread.
        subscribed_at: float | None = None  # Drops before subscribe cannot qualify as healthy operation.
        self._state.attempt_received_event = False  # Each connection must prove its own healthy operation.
        try:  # Convert subscribe and read outcomes into retry state.
            logger.info("Opening the WebSockets channel transport")  # Log before the network action.
            client.open()  # Subscribe before declaring the session live.
            logger.debug("Opened and subscribed the WebSockets channel transport")  # Confirm subscription.
            if self._state.stop.is_set():  # A stop after subscribe must not leave a live stream.
                return "stopped"  # The outer loop records the stopped state.
            subscribed_at = time.monotonic()  # Start the measurable healthy-operation interval.
            self._state.last_open_failure = None  # A completed subscribe supersedes an older open failure.
            logger.info("Marking the WebSockets channel session live")  # Log before the sink state change.
            self._sink.mark_live("The WebSocket connection opened.")  # The page can show the connection state.
            logger.debug("Marked the WebSockets channel session live")  # Confirm the sink state change.
            logger.info("Reading WebSockets channel events")  # Log before the long-running read action.
            client.run(self._on_event)  # Read until local close or drop.
            logger.debug("WebSockets channel event reading ended")  # Confirm the read action ended.
            return "stopped" if self._state.stop.is_set() else self._drop_result(subscribed_at)  # Classify return.
        except SubscribeError as error:
            if error.detail == "timeout":  # A missing subscribe answer is an open failure that can retry.
                logger.info("WebSockets channel subscription timed out")  # Do not log the channel path.
                logger.debug("WebSockets channel subscription timeout will retry")  # Safe retry state.
                self._state.last_open_failure = None  # Do not report an older open failure after subscribe timeout.
                return "dropped"  # The outer loop applies the retry budget.
            self._finish(SessionState.FAILED, f"The stream subscription failed: {error.detail}.")  # Hide path.
            return "final"  # Subscribe refusal does not retry.
        except ConnectionClosed as error:
            if not error.dropped:  # Local close is a stop.
                return "stopped"  # The outer loop maps this to stopped.
            return self._drop_result(subscribed_at)  # Only healthy subscribed operation resets the budget.
        except Exception as error:
            return self._open_failure_result(error)  # Fail at once or retry, by the cause of the failure.
        finally:
            logger.info("Closing the WebSockets channel transport attempt")  # Log before resource cleanup.
            client.close()  # Ensure each attempt releases its socket.
            logger.debug("Closed the WebSockets channel transport attempt")  # Confirm resource cleanup.

    def _drop_result(self, subscribed_at: float | None) -> str:
        """Classify a dropped connection by its measured operation.

        Args:
            subscribed_at: The monotonic subscription completion time.

        Returns:
            "healthy_drop" after useful or stable operation, else "dropped".
        """
        if subscribed_at is None:  # A connection that never subscribed did not operate.
            return "dropped"  # Preserve the retry count for an opening failure.
        operation_seconds = time.monotonic() - subscribed_at  # Measure stable subscribed operation.
        received_event = self._state.attempt_received_event  # Read the current attempt signal once.
        healthy = received_event or operation_seconds >= self._HEALTHY_OPERATION_SECONDS  # Apply bounded signals.
        logger.debug(
            "Classified WebSockets channel drop healthy=%s operation_seconds=%.3f received_event=%s",
            healthy,
            operation_seconds,
            received_event,
        )  # Record safe health evidence.
        return "healthy_drop" if healthy else "dropped"  # Reset retries only after measurable operation.

    def _open_failure_result(self, error: Exception) -> str:
        """Map one failed open to a final failure or a retry.

        Args:
            error: The exception from the open or the read.

        Returns:
            "final" for a refusal that a retry cannot heal, else "dropped".
        """
        logger.info("WebSockets channel runner connection attempt failed")  # Log before retry handling.
        logger.debug("WebSockets channel runner connection failure type=%s", type(error).__name__)  # Safe detail.
        reason = ConnectFailure.reason(error)  # Map open failures to operator-safe reasons.
        if reason is not None and self._is_client_refusal(error):  # A 4xx handshake will not heal by retrying.
            self._finish(SessionState.FAILED, reason)  # Show the safe HTTP refusal reason.
            return "final"  # Do not retry a client-side refusal.
        self._state.last_open_failure = reason  # Retry exhaustion can name the last open failure.
        return "dropped"  # Open failures retry through the outer loop.

    def _is_client_refusal(self, error: BaseException) -> bool:
        """Return whether a 4xx failure should fail without retry.

        Args:
            error: The WebSocket open exception.

        Returns:
            True when the status is 4xx, except retryable 408 and 429.
        """
        status_code = getattr(error, "status_code", 0)  # websocket-client stores handshake status here.
        return (
            isinstance(status_code, int)
            and 400 <= status_code <= 499
            and status_code not in self._RETRYABLE_CLIENT_STATUSES
        )  # Most 4xx refusals do not heal.

    def _wait_before_retry(self, failures: int) -> bool:
        """Wait before the next retry.

        Args:
            failures: The count of consecutive failed attempts.

        Returns:
            True when the runner should retry.
        """
        delays = self._endpoint.profile.reconnect_delays  # Profile owns the retry waits.
        if self._state.finished:  # Subscribe failure can already finish the session.
            return False  # Do not retry after a final state.
        if self._state.stop.is_set():  # Stop during error handling should become stopped.
            self._finish(SessionState.STOPPED, "The operator stopped the session.")  # Keep existing stop reason.
            return False  # Do not retry after stop.
        if failures > len(delays):  # The runner already used every retry delay.
            reason = self._state.last_open_failure or "The WebSocket connection failed after retry attempts."  # Reason.
            self._finish(SessionState.FAILED, reason)  # Plain reason.
            return False  # End after the retry budget.
        delay = delays[failures - 1]  # Delay indexes start at zero.
        logger.info("Waiting before WebSockets channel reconnect attempt")  # Do not log paths.
        stopped = self._state.stop.wait(delay)  # Stop wakes the reconnect wait at once.
        logger.debug("Reconnect wait ended for WebSockets channel runner stopped=%s", stopped)  # Safe state.
        if stopped:  # A stop during the wait must finish the session now.
            self._finish(SessionState.STOPPED, "The operator stopped the session.")  # Keep existing stop reason.
            return False  # Do not leave the session in stopping state.
        return not stopped  # Retry only when the delay completed normally.

    def _on_event(self, message: dict[str, object]) -> None:
        """Handle one decoded data event.

        Args:
            message: The decoded stream data event.
        """
        logger.info("Shaping a WebSockets channel data event")  # Log before the data transformation.
        kind, content, path = self._shaper.channel_message(message)  # Decode the message.
        logger.debug("Shaped a WebSockets channel data event with kind=%s", kind)  # Log safe result metadata.
        source = self._source_by_path.get(path or "")  # Convert the path to an identifier.
        self._state.attempt_received_event = True  # A delivered data event proves useful stream operation.
        logger.info("Adding a WebSockets channel data event to the session")  # Log before the sink action.
        self._sink.add_message(kind, content, source=source)  # Store the page-safe message.
        logger.debug("Added a WebSockets channel data event to the session")  # Confirm the sink action.

    def _finish(self, state: SessionState, reason: str) -> None:
        """Send one final state to the sink.

        Args:
            state: The final session state.
            reason: The plain end reason.
        """
        with self._state.finish_lock:  # Connection and stop paths can finish together.
            if self._state.finished:  # The first final state wins.
                return  # Do not send duplicate finish events.
            logger.info("Finishing WebSockets channel runner for key %s", self._request.key)  # Log before finish.
            self._state.finished = True  # Mark final state before calling the sink.
            self._sink.finish(state, reason)  # Store the final state on the session.
            logger.debug("Finished WebSockets channel runner for key %s", self._request.key)  # Log after finish.

    def _build_source_map(self) -> dict[str, str | None]:
        """Build the private path-to-source map.

        Returns:
            A dictionary keyed by channel path.
        """
        logger.info("Building WebSockets channel source map for key %s", self._request.key)  # Log before path build.
        definition = self._request.definition  # Store the union before narrowing.
        if not isinstance(definition, ChannelDefinition):  # A checked channel request must hold a channel definition.
            raise StreamRequestError(
                "bad_request", "The channel definition is not valid."
            )  # Fail safely if callers break the contract.
        paths = definition.build_paths(self._request.targets)  # Only checked targets reach this call.
        repeatable = definition.repeatable  # Only channels define a repeatable field.
        values = self._request.targets.get(str(repeatable), ()) if repeatable else ()  # Source values match path order.
        mapped = {
            path: values[index] if index < len(values) else None for index, path in enumerate(paths)
        }  # Map each path to a label source.
        logger.debug("Built WebSockets channel source map with %s path(s)", len(mapped))  # Log the count only.
        return mapped  # The map never leaves the server.
