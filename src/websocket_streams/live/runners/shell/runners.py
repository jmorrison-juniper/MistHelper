"""Coordinate Mist shell and screen terminal runners."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # Runner actions use structured JSON records.
import threading  # Each terminal reader runs outside the web request thread.
from typing import Any  # The Mist API session has no complete type stubs.

from src.websocket_streams.intake.start_request.models import StartRequest  # Runners accept checked requests only.
from src.websocket_streams.live.runners.shell.lifecycle.contracts import TerminalConfiguration
from src.websocket_streams.live.runners.shell.lifecycle.opening import TerminalOpening
from src.websocket_streams.live.runners.shell.lifecycle.outcomes import OutcomeReasons, TerminalOutcomes
from src.websocket_streams.live.runners.shell.lifecycle.reading import TerminalReading
from src.websocket_streams.live.runners.shell.modes.input import ShellInput
from src.websocket_streams.live.runners.shell.modes.screen import ScreenBehavior
from src.websocket_streams.live.runners.utility.triggers.models import UtilityRequest  # Trigger return type.
from src.websocket_streams.live.runners.utility.triggers.table import UtilityTriggerTable  # SDK-parity triggers.
from src.websocket_streams.live.sessions.record.state import SessionSink  # Runners write through the shared sink.
from src.websocket_streams.live.transport.endpoint import MistStreamEndpoint  # The endpoint supplies safe transport.
from src.websocket_streams.live.transport.runtime.logging.structured_logger import StructuredTransportLogger

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Apply the shared bounded logging boundary.


class DeviceTerminalRunner:
    """Coordinate one terminal opening, reader, outcome mapper, and stop event."""

    def __init__(self, opening: TerminalOpening, sink: SessionSink, configuration: TerminalConfiguration) -> None:
        """Build the terminal lifecycle collaborators."""
        self._opening = opening  # Tests can inject bounded client write failures through this owner.
        self._stopping = threading.Event()  # A stop changes open and close outcome decisions.
        outcomes = TerminalOutcomes(self._stopping, sink, configuration)  # One mapper owns final states.
        self._reading = TerminalReading(opening, sink, outcomes, configuration, self._stopping)  # One reader owns I/O.

    def start(self) -> None:
        """Start the terminal reader thread and return."""
        logger.emit(logging.INFO, "terminal_runner_start_started")  # Log before the thread starts.
        thread = threading.Thread(target=self._reading.run, name=f"ws-terminal-{self._opening.key}", daemon=True)
        thread.start()  # Let the web request return while the terminal runs.
        logger.emit(logging.DEBUG, "terminal_runner_start_completed", {"status": "started"})  # Log after start.

    def stop(self) -> None:
        """Request a terminal stop and return."""
        logger.emit(logging.INFO, "terminal_runner_stop_started")  # Log before the stop request.
        self._stopping.set()  # Make the stopped outcome win over a local close.
        self._opening.close()  # Wake the reader within one bounded socket wait.
        logger.emit(logging.DEBUG, "terminal_runner_stop_completed", {"status": "requested"})  # Log after stop.

    def resize(self, cols: int, rows: int) -> None:
        """Send or defer one terminal resize."""
        self._opening.resize(cols, rows)  # Preserve pre-open deferral and live write failures.


class ShellRunner(DeviceTerminalRunner, ShellInput):
    """Run one two-way Mist remote shell."""

    NO_ANSWER_REASON = OutcomeReasons.NO_ANSWER  # Preserve issue #3710 public behavior.
    WRITE_FAILED_REASON = OutcomeReasons.WRITE_FAILED  # Preserve issue #3741 public behavior.

    def __init__(
        self,
        apisession: Any,
        endpoint: MistStreamEndpoint,
        request: StartRequest,
        sink: SessionSink,
        triggers: UtilityTriggerTable | None = None,
    ) -> None:
        """Build one shell runner."""
        self._request = request  # The shell trigger reads the checked site and device targets.
        self._triggers = triggers or UtilityTriggerTable()  # Tests can provide bounded timing definitions.
        opening = TerminalOpening(apisession, endpoint, request, sink)  # Own the terminal connection.
        ShellInput.__init__(self, sink, opening.client)  # Bind exact input and deferred queue release.
        DeviceTerminalRunner.__init__(
            self,
            opening,
            sink,
            TerminalConfiguration("The shell opened.", "The device closed the shell.", self._trigger, self),
        )  # Build the shared lifecycle.

    def _trigger(self) -> UtilityRequest:
        """Return the checked shell trigger."""
        site_id = self._request.target("site_id")  # Read the checked site identifier.
        device_id = self._request.target("device_id")  # Read the checked device identifier.
        return self._triggers.shell_request(site_id, device_id)  # Build the SDK-parity shell request.


class ScreenRunner(DeviceTerminalRunner):
    """Run one read-only screen command with a total time limit."""

    SCREEN_COLS = 80  # Mist screen commands render correctly at exactly 80 columns.
    SCREEN_ROWS = 40  # Mist screen commands render correctly at exactly 40 rows.

    def __init__(
        self,
        apisession: Any,
        endpoint: MistStreamEndpoint,
        request: StartRequest,
        sink: SessionSink,
        triggers: UtilityTriggerTable | None = None,
    ) -> None:
        """Build one screen runner."""
        opening = TerminalOpening(apisession, endpoint, request, sink)  # Own the terminal connection.
        behavior = ScreenBehavior(request, triggers or UtilityTriggerTable(), opening.close)  # Own screen timing.
        configuration = TerminalConfiguration(
            "The screen command started.", "The device ended the screen command.", behavior.trigger, behavior
        )  # Keep mode text and actions in one immutable contract.
        super().__init__(opening, sink, configuration)  # Build the shared terminal lifecycle.

    def resize(self, cols: int, rows: int) -> None:
        """Keep the fixed screen size after the initial device frame."""
        logger.emit(
            logging.INFO, "screen_resize_ignored", {"count": cols, "code": rows}
        )  # Log the rejected panel size.
        logger.emit(logging.DEBUG, "screen_resize_ignore_completed", {"status": "fixed"})  # Confirm fixed geometry.
