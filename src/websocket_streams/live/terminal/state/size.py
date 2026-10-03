"""Hold the visible size of one terminal."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

from dataclasses import dataclass  # The terminal size is a small value object.

from src.websocket_streams.intake.fields.error import StreamRequestError  # Invalid sizes use shared refusals.


@dataclass(slots=True)
class TerminalSize:
    """Hold the visible size of one terminal."""

    cols: int = 80  # Most terminal sessions start with 80 columns.
    rows: int = 24  # Most terminal sessions start with 24 rows.

    @classmethod
    def checked(cls, cols: int, rows: int) -> TerminalSize:
        """Return a terminal size after range checks."""
        if not 20 <= cols <= 500:  # Columns outside the contract range are invalid.
            raise StreamRequestError("bad_request", "The terminal column count is not valid.")  # Refuse the size.
        if not 5 <= rows <= 200:  # Rows outside the contract range are invalid.
            raise StreamRequestError("bad_request", "The terminal row count is not valid.")  # Refuse the size.
        return cls(cols, rows)  # Return one checked terminal size.
