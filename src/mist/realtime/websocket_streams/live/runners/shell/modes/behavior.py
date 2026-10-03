"""Base behavior for one terminal mode."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

from src.mist.realtime.websocket_streams.live.sessions.record.state import (
    SessionState,
)  # Overrides return stable session states.


class TerminalBehavior:
    """Provide optional first-output, limit, and close behavior."""

    def first_output(self) -> None:
        """Handle the first terminal output when the mode needs an action."""

    def check_limit(self) -> None:
        """Close the terminal when the mode has its own time limit."""

    def closed_override(self) -> tuple[SessionState, str] | None:
        """Return a mode-specific final outcome when one applies."""
        return None  # Shell terminals use the shared close outcome rules.
