"""Run a Mist WebSocket channel stream.

Why:
    Issue #3671 removes the private Mist SDK WebSocket dependency. The runner
    uses the owned transport client, keeps Mist paths and credentials on the
    server, and keeps the existing page message shape.
"""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # The runner logs connection state without secrets.
import threading  # The reader runs in a daemon thread.
from dataclasses import dataclass, field  # Runner mutable state stays grouped.

from src.websocket_streams.catalog.model import ChannelDefinition  # Channel runners need channel-only methods.
from src.websocket_streams.intake.fields import StreamRequestError  # Invalid channel requests raise this error.
from src.websocket_streams.intake.start_request import StartRequest  # The request is already checked.
from src.websocket_streams.live.runners.text import MessageShaper  # The shaper decodes channel payloads.
from src.websocket_streams.live.sessions.record import (
    SessionSink,
    SessionState,
)  # The runner writes through this protocol.
from src.websocket_streams.live.transport.endpoint import MistStreamEndpoint  # The endpoint owns transport settings.
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


class ChannelStreamRunner:
    """Drive the owned WebSocket client for one channel request."""

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
        failures = 0  # Failure count resets after a successful subscription.
        while not self._state.stop.is_set():  # stop() ends reconnect and read loops.
            result = self._connect_once()  # Open and read one connection attempt.
            if result == "stopped":  # The operator stopped the runner.
                self._finish(SessionState.STOPPED, "The operator stopped the session.")  # Keep existing stop reason.
                return  # No reconnect after a local stop.
            if result == "subscribed":  # A successful subscribe means future drops start a new retry budget.
                failures = 0  # Reset failure count after the stream became live.
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
        subscribed = False  # Drops before subscribe must count as failed opens.
        try:  # Convert subscribe and read outcomes into retry state.
            client.open()  # Subscribe before declaring the session live.
            if self._state.stop.is_set():  # A stop after subscribe must not leave a live stream.
                return "stopped"  # The outer loop records the stopped state.
            subscribed = True  # open() returned only after every channel subscribed.
            self._sink.mark_live("The WebSocket connection opened.")  # The page can show the connection state.
            client.run(self._on_event)  # Read until local close or drop.
            return "stopped" if self._state.stop.is_set() else "dropped"  # A normal return after stop is local.
        except SubscribeError as error:
            if error.detail == "timeout":  # A missing subscribe answer is an open failure that can retry.
                logger.info("WebSockets channel subscription timed out")  # Do not log the channel path.
                logger.debug("WebSockets channel subscription timeout will retry")  # Safe retry state.
                return "dropped"  # The outer loop applies the retry budget.
            self._finish(SessionState.FAILED, f"The stream subscription failed: {error.detail}.")  # Hide path.
            return "final"  # Subscribe refusal does not retry.
        except ConnectionClosed as error:
            if not error.dropped:  # Local close is a stop.
                return "stopped"  # The outer loop maps this to stopped.
            return "subscribed" if subscribed else "dropped"  # Only subscribed drops reset the budget.
        except Exception as error:
            logger.info("WebSockets channel runner connection attempt failed")  # Log before retry handling.
            logger.debug("WebSockets channel runner connection failure type=%s", type(error).__name__)  # Safe detail.
            return "dropped"  # Open failures retry through the outer loop.
        finally:
            client.close()  # Ensure each attempt releases its socket.

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
            self._finish(SessionState.FAILED, "The WebSocket connection failed after retry attempts.")  # Plain reason.
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
        kind, content, path = self._shaper.channel_message(message)  # Decode the message.
        source = self._source_by_path.get(path or "")  # Convert the path to an identifier.
        self._sink.add_message(kind, content, source=source)  # Store the page-safe message.

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
