"""Run an SDK remote shell session.

Why:
    Issue #3551. A remote shell gives full device command-line access. The
    portal must keep the shell server-side, remove ANSI control text, refuse
    input before the first output, and never log the operator input.
"""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import importlib  # EX and SRX expose separate shell factory functions.
import logging  # The runner logs shell open and close without shell text.
import threading  # Shell reading must not block the web request.
import time  # The reader loop uses a short sleep on empty reads.
from collections.abc import Callable  # Tests inject a no-op sleeper.
from typing import Any  # The SDK shell session is untyped.

from src.websocket_streams.catalog.model import UtilityDefinition  # Shell runners need utility-only fields.
from src.websocket_streams.intake.fields import StreamRequestError  # The runner raises contract errors for input.
from src.websocket_streams.intake.start_request import StartRequest  # The request is already checked.
from src.websocket_streams.live.runners.text import MessageShaper  # Shell output needs ANSI removal.
from src.websocket_streams.live.sessions.record import (
    SessionSink,
    SessionState,
)  # The runner writes through this protocol.

logger = logging.getLogger(__name__)  # Keep shell runner records under this module.


class ShellRunner:
    """Run one Mist remote shell session."""

    def __init__(
        self,
        apisession: object,
        request: StartRequest,
        sink: SessionSink,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        """Build one shell runner.

        Args:
            apisession: The Mist API session.
            request: The checked shell request.
            sink: The session sink that receives shell output.
            sleeper: The sleep function used by the reader loop.
        """
        self._apisession = apisession  # The SDK uses this object for authentication.
        self._request = request  # The checked request names the device.
        self._sink = sink  # The runner reports output through this sink.
        self._sleeper = sleeper  # Tests inject a no-op sleeper.
        self._session: Any | None = None  # The SDK shell session is untyped.
        self._stopping = threading.Event()  # Close state uses this flag.
        self._input_ready = threading.Event()  # Input opens after first output.
        self._shaper = MessageShaper()  # The runner removes ANSI control text.

    def start(self) -> None:
        """Start the shell reader and return at once."""
        logger.info("Starting WebSockets shell runner for key %s", self._request.key)  # Log before the thread starts.
        thread = threading.Thread(
            target=self._run, name=f"ws-shell-{self._request.key}", daemon=True
        )  # A daemon thread reads the SDK shell.
        thread.start()  # The web request returns at once.
        logger.debug("Started WebSockets shell runner thread for key %s", self._request.key)  # Log safe metadata only.

    def stop(self) -> None:
        """Ask the shell session to close and return at once."""
        logger.info(
            "Stopping WebSockets shell runner for key %s", self._request.key
        )  # Log before closing the SDK shell.
        self._stopping.set()  # The reader maps the final state to stopped.
        session = self._session  # Copy the untyped reference for safety.
        if session is not None:  # A stop before open is valid.
            disconnect = getattr(session, "disconnect", None)  # The SDK exposes this method.
            if callable(disconnect):  # A fake can omit the method.
                disconnect()  # The SDK close returns quickly.
        logger.debug("Stop requested for WebSockets shell runner key %s", self._request.key)  # Log safe metadata only.

    def send_input(self, text: str) -> None:
        """Send checked shell input to the SDK session.

        Args:
            text: The checked input text or key byte.

        Raises:
            StreamRequestError: When the first output did not arrive yet.
        """
        if not self._input_ready.is_set():  # The SDK is not safe before first output.
            raise StreamRequestError("not_open", "The shell is not ready for input.")  # Keep the page reason plain.
        session = self._session  # Copy the untyped reference for safety.
        if session is None:  # The shell closed before input arrived.
            raise StreamRequestError("not_open", "The shell is not open.")  # Keep the page reason plain.
        logger.info("Sending WebSockets shell input length=%s", len(text))  # Log length only, never shell text.
        send_text = getattr(session, "send_text", None)  # The SDK shell uses send_text.
        if callable(send_text):  # A fake can expose the same method.
            send_text(text)  # The checked manager already added carriage return when needed.
        logger.debug("Sent WebSockets shell input length=%s", len(text))  # Log length only.

    def _run(self) -> None:
        """Open the shell and read until it closes."""
        try:  # The shell API can fail before the reader starts.
            self._open_session()  # Create the SDK shell session.
            self._sink.mark_live("The shell opened.")  # Tell the page the shell is open.
            self._read_loop()  # Read output until the session closes.
            self._finish_after_loop()  # Map the close to a final state.
        except Exception as exc:  # Broad catch protects the portal worker.
            logger.exception(
                "WebSockets shell runner failed for key %s", self._request.key
            )  # Log traceback without shell text.
            self._sink.finish(SessionState.FAILED, str(exc) or "The shell failed.")  # Report a plain failure.

    def _open_session(self) -> None:
        """Create the SDK shell session."""
        logger.info("Opening WebSockets shell session for key %s", self._request.key)  # Log before the SDK call.
        definition = self._shell_definition()  # The checked definition names the SDK family.
        module = importlib.import_module(f"mistapi.device_utils.{definition.family}")  # Load ex or srx SDK module.
        factory = module.createShellSession  # Get the SDK shell factory.
        self._session = factory(
            self._apisession, self._request.target("site_id"), self._request.target("device_id"), rows=24, cols=80
        )  # Open the shell.
        logger.debug("Opened WebSockets shell session for key %s", self._request.key)  # Log safe metadata only.

    def _shell_definition(self) -> UtilityDefinition:
        """Return the checked shell definition.

        Returns:
            The utility definition for the shell.
        """
        definition = self._request.definition  # Store the union before narrowing.
        if not isinstance(definition, UtilityDefinition):  # Shell runners require utility definitions.
            raise StreamRequestError(
                "bad_request", "The shell definition is not valid."
            )  # Fail safely if callers break the contract.
        return definition  # The caller can read utility-only fields.

    def _read_loop(self) -> None:
        """Read shell output until the SDK session closes."""
        while not self._stopping.is_set():  # Stop requests end the read loop.
            session = self._session  # Copy the untyped reference for safety.
            if session is None or not bool(getattr(session, "connected", False)):  # The SDK session is closed.
                return  # The final state is set after the loop.
            data = session.recv(timeout=0.1)  # The SDK returns bytes, text, or None.
            if data is None:  # No shell output was ready.
                self._sleeper(0.01)  # Keep the thread from spinning.
                continue  # Try again until stop or close.
            text = self._shaper.clean_shell_text(data)  # Remove ANSI control text.
            self._sink.add_message("text", text)  # Store the plain output.
            self._mark_first_output()  # Allow input after the first output.

    def _mark_first_output(self) -> None:
        """Open shell input after the first output."""
        if self._input_ready.is_set():  # Only the first output changes the flag.
            return  # Input is already ready.
        self._input_ready.set()  # Local input checks now pass.
        self._sink.mark_input_ready()  # The manager and page now accept shell input.

    def _finish_after_loop(self) -> None:
        """Set the final shell state after the reader loop."""
        if self._stopping.is_set():  # An operator or reaper closed the shell.
            self._sink.finish(SessionState.STOPPED, "The operator stopped the session.")  # Report a normal stop.
            return  # No further state applies.
        self._sink.finish(SessionState.FINISHED, "The shell closed.")  # Report a remote close.
