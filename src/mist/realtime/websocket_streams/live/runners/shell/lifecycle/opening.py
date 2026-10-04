"""Open, resize, and close one Mist terminal connection."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # Terminal open actions use structured JSON records.
import threading  # A stop request can arrive during the REST trigger or socket open.
from typing import Any  # The Mist API session has no complete type stubs.

from src.mist.realtime.websocket_streams.intake.fields.error import (
    StreamRequestError,  # Address and write refusals use this contract.
)
from src.mist.realtime.websocket_streams.intake.start_request.models import (
    StartRequest,
)  # The checked request supplies safe targets.
from src.mist.realtime.websocket_streams.live.runners.utility.triggers.models import (
    UtilityRequest,
)  # The trigger record is stable.
from src.mist.realtime.websocket_streams.live.sessions.record.state import (  # Open behavior reads session state.
    SessionSink,
    SessionState,
)
from src.mist.realtime.websocket_streams.live.terminal.state.size import (
    TerminalSize,
)  # Start with a bounded terminal size.
from src.mist.realtime.websocket_streams.live.transport.endpoint import (
    ConnectFailure,
    MistStreamEndpoint,
    ShellAddressPolicy,
)
from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)
from src.mist.realtime.websocket_streams.live.transport.runtime.reader.contracts import (
    ConnectionClosed,
)  # Stops use one contract.
from src.mist.realtime.websocket_streams.live.transport.shell_client import (
    ShellClient,
)  # The owned client preserves raw bytes.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Apply the shared bounded logging boundary.


class TerminalOpenError(Exception):
    """Report a terminal address or connection failure."""


class TerminalTrigger:
    """Send one terminal REST trigger and validate its response."""

    def __init__(self, apisession: Any) -> None:
        """Store the signed-in Mist API session."""
        self._apisession = apisession  # The trigger uses the existing authenticated REST client.

    def url(self, trigger: UtilityRequest) -> str:
        """Send the trigger and return its checked terminal address."""
        logger.emit(logging.INFO, "terminal_trigger_started", {"action": trigger.key})  # Log before the REST call.
        response = self._apisession.mist_post(trigger.path, body=trigger.body)  # Ask Mist to open the terminal.
        logger.emit(
            logging.DEBUG,
            "terminal_trigger_completed",
            {"status": getattr(response, "status_code", None)},
        )  # Log only bounded metadata.
        return self._url(response)  # Validate the response without logging the terminal address.

    @staticmethod
    def _status(response: object) -> int:
        """Return a successful integer status."""
        status = getattr(response, "status_code", None)  # Read the SDK status from its response object.
        if not isinstance(status, int) or not 200 <= status < 300:  # Refuse each non-success response.
            raise TerminalOpenError(f"The Mist cloud refused the terminal request with status {status}.")
        return status  # The URL validation can continue after a successful response.

    def _url(self, response: object) -> str:
        """Return the non-empty URL from a successful response."""
        self._status(response)  # Refuse a failed HTTP response before inspecting its body.
        data = getattr(response, "data", None)  # Read decoded JSON without logging its terminal address.
        url = data.get("url") if isinstance(data, dict) else None  # Accept an address only from an object response.
        if not isinstance(url, str) or not url:  # A missing address cannot create a terminal.
            raise TerminalOpenError("The Mist cloud did not return a terminal address.")
        return url  # The client applies the address policy before it sends credentials.


class TerminalOpening:
    """Own terminal trigger, connector, resize, and close collaborators."""

    def __init__(self, apisession: Any, endpoint: MistStreamEndpoint, request: StartRequest, sink: SessionSink) -> None:
        """Build one terminal connection owner."""
        self._sink = sink  # Resize decisions use the current session state and terminal size.
        self.key = request.key  # The thread name uses the checked catalog key.
        self.client = ShellClient(
            endpoint, ShellAddressPolicy(endpoint.cloud_host, endpoint.profile.allow_loopback)
        )  # Prevent credential leaks before the client opens.
        self.trigger = TerminalTrigger(apisession)  # One collaborator owns the REST trigger response.
        self.connector = TerminalConnector(self.client, sink)  # One collaborator owns the socket open.

    def resize(self, cols: int, rows: int) -> None:
        """Send a live size or retain a pre-open size."""
        logger.emit(logging.DEBUG, "terminal_resize_started", {"count": cols, "code": rows})  # Log bounded dimensions.
        try:  # A connecting session can receive a browser resize before the socket exists.
            self.client.resize(cols, rows)  # Send the newest size when the socket is ready.
        except StreamRequestError:
            if self._sink.state == SessionState.CONNECTING:  # The terminal state already retained this size.
                logger.emit(logging.DEBUG, "terminal_resize_deferred", {"status": "connecting"})
                return
            logger.emit(logging.WARNING, "terminal_resize_failed", {"status": "write"})
            raise
        logger.emit(logging.DEBUG, "terminal_resize_completed", {"status": "sent"})  # Log after the write.

    def close(self) -> None:
        """Close the owned terminal client."""
        logger.emit(logging.INFO, "terminal_close_started")  # Log before the close action.
        self.client.close()  # Wake the reader and prevent later writes.
        logger.emit(logging.DEBUG, "terminal_close_completed", {"status": "closed"})  # Log after the close action.

    def mark_live(self, note: str) -> None:
        """Mark the session live with the mode note."""
        logger.emit(logging.INFO, "terminal_live_started")  # Log before the live state change.
        self._sink.mark_live(note)  # Show the mode-specific open event.
        logger.emit(logging.DEBUG, "terminal_live_completed", {"status": "live"})  # Log after the state change.


class TerminalConnector:
    """Connect one terminal client with stop and resize race handling."""

    def __init__(self, client: ShellClient, sink: SessionSink) -> None:
        """Store the client and terminal state source."""
        self._client = client  # The connector opens and resizes this owned client.
        self._sink = sink  # The terminal stores size changes that arrive during the open.

    def open(self, url: str, stopping: threading.Event) -> None:
        """Connect with the current terminal size."""
        opened = self._size()  # Copy the size before the network connection starts.
        if stopping.is_set():  # A stop during the REST trigger must prevent a socket connection.
            raise ConnectionClosed(dropped=False)
        self._connect(url, opened)  # Open the socket and send the initial size.
        if stopping.is_set():  # A stop can arrive while the WebSocket handshake runs.
            raise ConnectionClosed(dropped=False)
        self._latest_resize(opened)  # Send a resize that arrived during the socket open.

    def _connect(self, url: str, opened: TerminalSize) -> None:
        """Open the client and translate known connection failures."""
        logger.emit(logging.INFO, "terminal_open_started")  # Log before the network connection.
        try:  # Preserve policy errors and translate known network open failures.
            self._client.open(url, opened.cols, opened.rows)  # Connect and send the initial size.
        except StreamRequestError:
            raise  # Keep the safe address-policy reason unchanged.
        except Exception as error:
            reason = ConnectFailure.reason(error)  # Convert known transport failures to operator text.
            if reason is None:  # Unknown program failures need the shared unexpected-error path.
                raise
            logger.emit(logging.INFO, "terminal_open_failed", {"detail": type(error).__name__})
            raise TerminalOpenError(reason) from error
        logger.emit(logging.DEBUG, "terminal_open_completed", {"status": "open"})  # Log after the open.

    def _latest_resize(self, opened: TerminalSize) -> None:
        """Send the newest size when it changed during the open."""
        current = self._size()  # Read the newest browser size after the connection opens.
        if current != opened:  # Preserve a resize that arrived before the socket existed.
            self._client.resize(current.cols, current.rows)

    def _size(self) -> TerminalSize:
        """Return the stored size or the terminal default."""
        terminal = self._sink.terminal  # A terminal session normally holds a size state.
        return terminal.size() if terminal is not None else TerminalSize()  # Keep defensive default behavior.
