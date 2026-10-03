"""Hold the status fields for one terminal read."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

from dataclasses import dataclass  # Terminal status is an immutable value object.


@dataclass(frozen=True, slots=True)
class TerminalStatus:
    """Hold the session status fields for one terminal read."""

    state: str  # The page shows the session state.
    reason: str  # The page shows the end reason.
    input_ready: bool  # The page enables input after first output.
