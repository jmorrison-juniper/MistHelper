"""Run a Mist WebSocket channel stream.

Why:
    Issue #3551. Channel streams are the safest WebSocket feature, but the
    browser must never receive a Mist path, token, or WebSocket address. This
    runner keeps the SDK connection server-side and writes only shaped messages
    into the session sink.
"""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # The runner logs connection state without secrets.
from typing import Any  # The mistapi SDK is untyped.

from mistapi.websockets.__ws_client import _MistWebsocket  # The private SDK class is pinned by a contract test.

from src.websocket_streams.catalog.model import ChannelDefinition  # Channel runners need channel-only methods.
from src.websocket_streams.intake.fields import StreamRequestError  # Non-shell input raises this contract error.
from src.websocket_streams.intake.start_request import StartRequest  # The request is already checked.
from src.websocket_streams.live.runners.text import MessageShaper  # The shaper decodes channel payloads.
from src.websocket_streams.live.sessions.record import (
    SessionSink,
    SessionState,
)  # The runner writes through this protocol.

logger = logging.getLogger(__name__)  # Keep channel runner records under this module.


class ChannelStreamRunner:
    """Drive the SDK WebSocket client for one channel request."""

    def __init__(
        self, apisession: object, request: StartRequest, sink: SessionSink, client_class: type[Any] = _MistWebsocket
    ) -> None:
        """Build one channel runner.

        Args:
            apisession: The Mist API session.
            request: The checked channel request.
            sink: The session sink that receives events.
            client_class: The SDK client class, or a fake in tests.
        """
        self._apisession = apisession  # The SDK uses this object for authentication.
        self._request = request  # The checked request builds channel paths.
        self._sink = sink  # The runner reports messages through this sink.
        self._client_class = client_class  # Tests inject a fake SDK client.
        self._client: Any | None = None  # The client exists after start.
        self._stopping = False  # Close callbacks use this to choose an end state.
        self._shaper = MessageShaper()  # Channel payloads need nested JSON decoding.
        self._source_by_path = self._build_source_map()  # The page receives an identifier, not a path.

    def start(self) -> None:
        """Start the SDK connection and return at once."""
        logger.info("Starting WebSockets channel runner for key %s", self._request.key)  # Log before starting SDK work.
        paths = list(self._source_by_path)  # The SDK accepts a list of channel paths.
        client = self._client_class(
            self._apisession,
            channels=paths,
            auto_reconnect=True,
            max_reconnect_attempts=3,
            ping_interval=30,
            queue_maxsize=1000,
        )  # Build the SDK client with the feature settings.
        self._client = client  # Keep it so stop can disconnect it.
        self._install_callbacks(client)  # Register callbacks before the connection starts.
        client.connect(run_in_background=True)  # The SDK starts a daemon thread.
        logger.debug("Started WebSockets channel runner for key %s", self._request.key)  # Log safe metadata only.

    def stop(self) -> None:
        """Ask the SDK connection to close and return at once."""
        logger.info("Stopping WebSockets channel runner for key %s", self._request.key)  # Log before stopping SDK work.
        self._stopping = True  # The close callback should map to stopped.
        client = self._client  # Copy the reference for a safe check.
        if client is not None:  # A stop before start is valid.
            client.disconnect(wait=False)  # The SDK close is non-blocking.
        logger.debug(
            "Stop requested for WebSockets channel runner key %s", self._request.key
        )  # Log safe metadata only.

    def send_input(self, text: str) -> None:
        """Reject shell input for a channel runner.

        Args:
            text: The ignored text.

        Raises:
            StreamRequestError: Always, because channel streams are not shells.
        """
        raise StreamRequestError(
            "not_open", "This session does not accept shell input."
        )  # Only shell runners accept input.

    def _install_callbacks(self, client: Any) -> None:
        """Install SDK callbacks on the client.

        Args:
            client: The SDK WebSocket client.
        """
        client.on_open(self._on_open)  # The SDK calls this when the socket opens.
        client.on_message(self._on_message)  # The SDK calls this for each message.
        client.on_error(self._on_error)  # The SDK calls this for errors.
        client.on_close(self._on_close)  # The SDK calls this after close.

    def _on_open(self) -> None:
        """Handle an SDK open callback."""
        self._sink.mark_live("The WebSocket connection opened.")  # The page can show the connection state.

    def _on_message(self, message: object) -> None:
        """Handle one SDK message callback.

        Args:
            message: The raw SDK message.
        """
        kind, content, path = self._shaper.channel_message(message)  # Decode the message.
        source = self._source_by_path.get(path or "")  # Convert the path to an identifier.
        self._sink.add_message(kind, content, source=source)  # Store the page-safe message.

    def _on_error(self, error: Exception) -> None:
        """Handle one SDK error callback.

        Args:
            error: The SDK exception.
        """
        logger.info("WebSockets channel runner received an SDK error")  # Log before ending the session.
        self._sink.finish(SessionState.FAILED, str(error) or "The WebSocket connection failed.")  # Report the failure.
        logger.debug("WebSockets channel runner recorded an SDK error")  # Log after ending the session.

    def _on_close(self, code: int | None, message: str | None) -> None:
        """Handle the final SDK close callback.

        Args:
            code: The WebSocket close code, or None.
            message: The WebSocket close message, or None.
        """
        state = SessionState.STOPPED if self._stopping else SessionState.FAILED  # Unexpected closes are failures.
        reason = (
            "The operator stopped the session." if self._stopping else (message or "The WebSocket connection closed.")
        )  # Keep text plain.
        self._sink.finish(state, reason)  # The first final state wins.

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
