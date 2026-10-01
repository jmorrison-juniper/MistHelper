"""Run a device terminal: a Mist remote shell or a screen command.

Why:
    Issue #3671. The old runner used the shell client of the Mist SDK. That
    client removed the control codes and refused the keys that arrived before
    the first output. This runner sends the REST trigger, opens the own
    WebSocket client, and keeps each output byte for the xterm.js panel.
"""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # The runner logs the open and the close, never the keys or the output.
import threading  # The reader must not block the web request.
from typing import Any  # The Mist API session has no type stubs.

from src.websocket_streams.intake.fields import StreamRequestError  # The address check and the sends use it.
from src.websocket_streams.intake.start_request import StartRequest  # The request is already checked.
from src.websocket_streams.live.runners.utility.triggers import UtilityRequest, UtilityTriggerTable  # REST triggers.
from src.websocket_streams.live.sessions.record import SessionSink, SessionState  # The runner writes to the sink.
from src.websocket_streams.live.terminal.state import TerminalSize  # The default size when no terminal exists.
from src.websocket_streams.live.transport.endpoint import MistStreamEndpoint, ShellAddressPolicy  # Connection values.
from src.websocket_streams.live.transport.frames import ConnectionClosed  # The client reports each end with it.
from src.websocket_streams.live.transport.shell_client import ShellClient  # The own shell WebSocket client.

logger = logging.getLogger(__name__)  # Keep terminal runner records under this module.


class TerminalOpenError(Exception):
    """The Mist cloud did not give a usable terminal address."""


class DeviceTerminalRunner:
    """Run one device terminal connection, and keep each output byte."""

    OPENED_NOTE = "The terminal opened."  # Each subclass names its own open event.
    CLOSED_REASON = "The device closed the terminal."  # A close frame from the device is a normal end.
    DROPPED_REASON = "The connection to the device dropped."  # A loss with no close frame is a failure.
    STOPPED_REASON = "The operator stopped the session."  # The record keeps a more exact stop reason.

    def __init__(
        self,
        apisession: Any,
        endpoint: MistStreamEndpoint,
        request: StartRequest,
        sink: SessionSink,
        triggers: UtilityTriggerTable | None = None,
    ) -> None:
        """Build one device terminal runner.

        Args:
            apisession: The Mist API session that sends the REST trigger.
            endpoint: The connection values for the WebSocket.
            request: The checked start request.
            sink: The session that keeps the output bytes.
            triggers: The trigger table, or None for the standard table. Tests can shorten the timing.
        """
        self._apisession = apisession  # The REST trigger uses the signed-in session.
        self._request = request  # The checked request names the site and the device.
        self._sink = sink  # The runner reports the output and the state through this sink.
        self._triggers = triggers or UtilityTriggerTable()  # The table builds the REST path and the body.
        policy = ShellAddressPolicy(endpoint.cloud_host, endpoint.profile.allow_loopback)  # Mist addresses only.
        self._client = ShellClient(endpoint, policy)  # One client for the life of this runner.
        self._stopping = threading.Event()  # A stop request maps the close to the stopped state.
        self._output_seen = False  # The first output opens the input of a shell.

    def start(self) -> None:
        """Start the reader thread and return at once."""
        logger.info("Starting the terminal runner for key %s", self._request.key)  # Log before the thread starts.
        thread = threading.Thread(
            target=self._run, name=f"ws-terminal-{self._request.key}", daemon=True
        )  # A daemon thread keeps the portal exit fast.
        thread.start()  # The web request returns at once.
        logger.debug("Started the terminal runner thread for key %s", self._request.key)  # Log safe metadata only.

    def stop(self) -> None:
        """Ask the terminal to close and return at once."""
        logger.info("Stopping the terminal runner for key %s", self._request.key)  # Log before the close.
        self._stopping.set()  # The reader maps the close to the stopped state.
        self._client.close()  # The reader sees the local close within one short socket wait.
        logger.debug("Stop requested for the terminal runner key %s", self._request.key)  # Log after the request.

    def resize(self, cols: int, rows: int) -> None:
        """Send a new terminal size to the device.

        Args:
            cols: The terminal columns.
            rows: The terminal rows.
        """
        logger.debug("Sending the terminal size for key %s", self._request.key)  # Debug level: drags send many sizes.
        try:
            self._client.resize(cols, rows)  # The device redraws for the new size.
        except StreamRequestError:
            logger.debug("Kept the terminal size until the connection opens")  # The open sends the stored size.
            return  # The stored size is not lost.
        logger.debug("Sent the terminal size for key %s", self._request.key)  # Log after the send.

    def _run(self) -> None:
        """Open the terminal and read until it closes."""
        try:
            url = self._terminal_url()  # Send the REST trigger and read the address.
            self._open(url)  # Check the address, connect, and send the size.
            self._sink.mark_live(self.OPENED_NOTE)  # The page shows the terminal as open.
            self._read_loop()  # Read until the connection ends.
        except ConnectionClosed as closed:
            state, reason = self._outcome(closed)  # Map the close to a final state.
            self._sink.finish(state, reason)  # The page shows the end reason.
        except (TerminalOpenError, StreamRequestError) as error:
            self._fail(str(getattr(error, "message", "") or error))  # The reason is plain operator text.
        except Exception:  # A broad catch keeps one bad terminal from ending the portal worker.
            logger.exception("The terminal runner failed for key %s", self._request.key)  # Traceback, no output.
            self._fail("The terminal failed. Read the portal log for the cause.")  # Plain reason for the page.
        finally:
            self._client.close()  # Close the socket on each path.

    def _terminal_url(self) -> str:
        """Send the REST trigger and return the WebSocket address.

        Returns:
            The terminal address from the Mist cloud.

        Raises:
            TerminalOpenError: The cloud refused the request or sent no address.
        """
        trigger = self._trigger()  # Each subclass builds its own trigger.
        logger.info("Sending the terminal trigger for key %s", self._request.key)  # Log before the REST call.
        response = self._apisession.mist_post(trigger.path, body=trigger.body)  # Ask Mist to open the terminal.
        status = getattr(response, "status_code", None)  # The SDK answer holds the HTTP status.
        data = getattr(response, "data", None)  # The SDK answer holds the decoded JSON body.
        logger.debug("Received the terminal trigger answer with status %s", status)  # Never log the address.
        if not isinstance(status, int) or not 200 <= status < 300:  # Mist refused the request.
            raise TerminalOpenError(f"The Mist cloud refused the terminal request with status {status}.")  # Plain.
        url = data.get("url") if isinstance(data, dict) else None  # The answer names the WebSocket address.
        if not isinstance(url, str) or not url:  # An answer without an address cannot open a terminal.
            raise TerminalOpenError("The Mist cloud did not return a terminal address.")  # Plain reason.
        return url  # The client checks the address before it sends credentials.

    def _open(self, url: str) -> None:
        """Connect and send the stored terminal size.

        Args:
            url: The terminal address from the Mist cloud.

        Raises:
            ConnectionClosed: A stop request arrived during the open.
        """
        terminal = self._sink.terminal  # The gateway stores each size that the page sends.
        opened = terminal.size() if terminal is not None else TerminalSize()  # Copy the size before the open.
        if self._stopping.is_set():  # The operator stopped the session during the REST trigger.
            raise ConnectionClosed(dropped=False)  # Do not open a connection that nobody wants.
        self._client.open(url, opened.cols, opened.rows)  # Check the address, connect, and send the size.
        if self._stopping.is_set():  # A stop arrived while the connection opened.
            raise ConnectionClosed(dropped=False)  # The finally block closes the new socket.
        current = terminal.size() if terminal is not None else opened  # A resize can arrive during the open.
        if current != opened:  # The page changed the size before the socket existed.
            self._client.resize(current.cols, current.rows)  # Send the newest size.

    def _read_loop(self) -> None:
        """Keep each output byte until the connection ends.

        Raises:
            ConnectionClosed: The connection ended.
        """
        while True:  # The client raises ConnectionClosed at the end.
            data = self._client.read()  # Bytes, or None after one quiet interval.
            if data:  # A quiet interval adds nothing.
                self._sink.add_bytes(data)  # The history keeps the raw bytes with the control codes.
                self._first_output()  # The first output opens the input of a shell.
            self._check_limit()  # A screen command ends at its time limit.

    def _first_output(self) -> None:
        """Run the first-output action one time."""
        if self._output_seen:  # Only the first output changes the state.
            return  # Later output needs no action.
        self._output_seen = True  # Remember that the device answered.
        try:
            self._on_first_output()  # A shell sends the queued keys now.
        except StreamRequestError:
            logger.debug("The connection closed before the queued keys left")  # The next read reports the close.

    def _on_first_output(self) -> None:
        """Act on the first output. A read-only terminal does nothing."""

    def _check_limit(self) -> None:
        """End the terminal at a time limit. A shell has no limit of its own."""

    def _trigger(self) -> UtilityRequest:
        """Return the REST trigger of this terminal.

        Returns:
            The REST trigger request.
        """
        raise NotImplementedError("Each terminal runner supplies its own trigger.")  # Subclasses must override.

    def _outcome(self, closed: ConnectionClosed) -> tuple[SessionState, str]:
        """Map the end of the connection to a final state.

        Args:
            closed: The close that ended the read loop.

        Returns:
            The final state and the plain reason.
        """
        if self._stopping.is_set() or not closed.dropped:  # The operator or the reaper closed the terminal.
            return SessionState.STOPPED, self.STOPPED_REASON  # The record keeps the exact stop reason.
        if closed.code is not None:  # The device sent a close frame, for example after exit.
            return SessionState.FINISHED, self.CLOSED_REASON  # A normal end of the terminal.
        return SessionState.FAILED, self.DROPPED_REASON  # The network lost the connection.

    def _fail(self, reason: str) -> None:
        """End the session as failed, unless a stop request won.

        Args:
            reason: The plain reason for the operator.
        """
        if self._stopping.is_set():  # A stop during the open is not a failure.
            self._sink.finish(SessionState.STOPPED, self.STOPPED_REASON)  # The record keeps the stop reason.
            return  # The stop state wins.
        logger.warning("The terminal for key %s did not open: %s", self._request.key, reason)  # Plain reason only.
        self._sink.finish(SessionState.FAILED, reason)  # The page shows the plain reason.


class ShellRunner(DeviceTerminalRunner):
    """Run one Mist remote shell as a two-way terminal."""

    OPENED_NOTE = "The shell opened."  # The page shows this event.
    CLOSED_REASON = "The device closed the shell."  # The device ends the shell after exit.

    def send_input(self, text: str) -> None:
        """Send terminal input to the device.

        Args:
            text: The exact text from the page. The runner adds nothing.

        Raises:
            StreamRequestError: The shell connection is not open.
        """
        logger.debug("Sending shell input length=%s", len(text))  # Debug level: each key is one request.
        self._client.send(text)  # The client adds the NUL prefix and sends one binary frame.
        logger.debug("Sent shell input length=%s", len(text))  # Log the length only, never the text.

    def _trigger(self) -> UtilityRequest:
        """Return the shell REST trigger.

        Returns:
            The shell trigger request.
        """
        site_id = self._request.target("site_id")  # The checked site identifier.
        device_id = self._request.target("device_id")  # The checked device identifier.
        return self._triggers.shell_request(site_id, device_id)  # POST to the shell path with an empty body.

    def _on_first_output(self) -> None:
        """Open the input, and send the keys that arrived before the first output."""
        self._sink.mark_input_ready()  # The input queue sends the early keys in order.
