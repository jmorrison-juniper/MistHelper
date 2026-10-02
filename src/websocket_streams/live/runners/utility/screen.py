"""Run a read-only screen command, such as Top or Monitor traffic.

Why:
    Issue #3671. A screen command sends full-screen output with control codes.
    The old runner removed those codes, so the page showed broken text. This
    runner keeps each byte for the xterm.js panel, and it ends the command at
    its time limit.
"""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # The runner logs the limit and the close.
import time  # The time limit uses the monotonic clock.

from src.websocket_streams.live.runners.shell import DeviceTerminalRunner  # The shared terminal reader.
from src.websocket_streams.live.runners.utility.triggers import UtilityRequest  # The REST trigger record.
from src.websocket_streams.live.sessions.record import SessionState  # The final states.
from src.websocket_streams.live.transport.frames import ConnectionClosed  # The client reports each end with it.

logger = logging.getLogger(__name__)  # Keep screen runner records under this module.


class ScreenRunner(DeviceTerminalRunner):
    """Run one screen command as a read-only terminal with a time limit."""

    SCREEN_COLS = 80  # Mist screen commands render correctly at exactly 80 columns.
    SCREEN_ROWS = 40  # Mist screen commands render correctly at exactly 40 rows.
    OPENED_NOTE = "The screen command started."  # The page shows this event.
    CLOSED_REASON = "The device ended the screen command."  # The device can end the command first.

    _limit_seconds = float("inf")  # No limit applies until the trigger sets the real limit.
    _started = 0.0  # The trigger sets the start time before the open.
    _limit_reached = False  # The limit check sets this flag.

    def _trigger(self) -> UtilityRequest:
        """Return the screen REST trigger, and start the time limit.

        Returns:
            The screen trigger request.
        """
        trigger = self._triggers.request_for(self._request)  # The table holds the screen command rows.
        self._limit_seconds = trigger.listen.timing.total_seconds  # The command ends at this limit.
        self._started = time.monotonic()  # The limit counts from the trigger.
        logger.debug("Set the screen limit to %s seconds", self._limit_seconds)  # Log the safe limit value.
        return trigger  # The base class sends the trigger.

    def _check_limit(self) -> None:
        """Close the screen command when it reaches its time limit."""
        if self._limit_reached:  # The close is already in progress.
            return  # Do not close two times.
        if time.monotonic() - self._started < self._limit_seconds:  # The command still has time.
            return  # Keep reading.
        logger.info("Ending the screen command at its limit of %s seconds", self._limit_seconds)  # Log the close.
        self._limit_reached = True  # The outcome reports the limit, not a stop.
        self._client.close()  # The next read raises ConnectionClosed.
        logger.debug("Closed the screen command at its limit")  # Log after the close.

    def _outcome(self, closed: ConnectionClosed) -> tuple[SessionState, str]:
        """Map the end of the screen command to a final state.

        Args:
            closed: The close that ended the read loop.

        Returns:
            The final state and the plain reason.
        """
        if self._limit_reached and not self._stopping.is_set():  # The time limit ended the command.
            limit = int(self._limit_seconds)  # Show whole seconds to the operator.
            return SessionState.FINISHED, f"The screen command reached its time limit of {limit} seconds."  # Plain.
        return super()._outcome(closed)  # The shared rules cover a stop, a close, and a drop.
