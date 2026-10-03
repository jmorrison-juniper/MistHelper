"""Handle read-only screen timing and final outcomes."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # Screen limit actions use structured JSON records.
import time  # Screen command limits use a monotonic clock.
from collections.abc import Callable  # The behavior closes the owned client at its limit.
from dataclasses import dataclass  # Screen timing state stays in one small value.

from src.websocket_streams.intake.start_request.models import (
    StartRequest,  # The trigger table reads checked parameters.
)
from src.websocket_streams.live.runners.shell.modes.behavior import TerminalBehavior  # Screen extends mode behavior.
from src.websocket_streams.live.runners.utility.triggers.models import UtilityRequest  # Trigger result type.
from src.websocket_streams.live.runners.utility.triggers.table import UtilityTriggerTable  # Screen trigger builder.
from src.websocket_streams.live.sessions.record.state import SessionState  # A reached limit is a finished outcome.
from src.websocket_streams.live.transport.runtime.logging.structured_logger import StructuredTransportLogger

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Apply the shared bounded logging boundary.


@dataclass(slots=True)
class ScreenTiming:
    """Hold the mutable screen limit state."""

    seconds: float = float("inf")  # No limit applies before the trigger is built.
    started: float = 0.0  # The trigger records the monotonic limit origin.
    reached: bool = False  # The outcome distinguishes a limit from a failed write.


class ScreenBehavior(TerminalBehavior):
    """Build a screen trigger and enforce its total time limit."""

    def __init__(self, request: StartRequest, triggers: UtilityTriggerTable, close_action: Callable[[], None]) -> None:
        """Store screen trigger and close collaborators."""
        self._request = request  # The trigger table reads checked targets and parameters.
        self._triggers = triggers  # Tests can supply a shorter timing table.
        self._close_action = close_action  # The limit closes the same owned client as stop.
        self._timing = ScreenTiming()  # One state record keeps the class child count bounded.

    def trigger(self) -> UtilityRequest:
        """Build the screen trigger and start its total limit."""
        trigger = self._triggers.request_for(self._request)  # Build the SDK-parity screen request.
        self._timing.seconds = trigger.listen.timing.total_seconds  # Use the catalog timing.
        self._timing.started = time.monotonic()  # Count the limit from trigger construction.
        logger.emit(logging.DEBUG, "screen_limit_started", {"timeout_seconds": self._timing.seconds})
        return trigger  # The opening owner sends this trigger.

    def check_limit(self) -> None:
        """Close the terminal when the screen command reaches its limit."""
        if self._timing.reached:  # A close is already in progress.
            return
        if time.monotonic() - self._timing.started < self._timing.seconds:  # The command still has time.
            return
        self._close_at_limit()  # Set the outcome before the close wakes the reader.

    def _close_at_limit(self) -> None:
        """Close the client and record the reached limit."""
        logger.emit(logging.INFO, "screen_limit_close_started", {"timeout_seconds": self._timing.seconds})
        self._timing.reached = True  # Set the outcome before the close wakes the reader.
        self._close_action()  # End the read loop through the shared local-close contract.
        logger.emit(logging.DEBUG, "screen_limit_close_completed", {"status": "closed"})

    def closed_override(self) -> tuple[SessionState, str] | None:
        """Return the successful limit outcome when the limit closed the client."""
        if not self._timing.reached:  # Other closes use the shared terminal outcome rules.
            return None
        limit = int(self._timing.seconds)  # Public text uses whole seconds.
        reason = f"The screen command reached its time limit of {limit} seconds."  # Keep the existing page text.
        return SessionState.FINISHED, reason  # A reached total limit is a normal screen completion.
