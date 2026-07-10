"""DisplayUtils -- centralized display and output utilities.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 11).
Groups PrettyTable rendering + ASCII progress-bar helpers so callers can invoke
them without reaching into the monolith. All methods are static -- no state is
kept on the class.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on Python 3.9+.

import logging  # WHY: emit rendered PrettyTable at debug level.
from typing import Any  # WHY: duck-typed row dicts flow through PrettyTable.

from prettytable import PrettyTable  # WHY: rendering engine for dict_list_as_pretty_table.

from src.data.data_processing_utils import (
    DataProcessingUtils,
)  # WHY: 1015 T-10 canonical import (eliminates mh.DataProcessingUtils).


class DisplayUtils:
    """Centralized display and output utilities.

    Handles table formatting, pretty printing, etc.
    """

    @staticmethod
    def _apply_sort_if_valid(table: PrettyTable, sortby: str | None, fields: list[str]) -> None:
        """Set table.sortby only when caller supplied a column name that exists in `fields`."""
        if not sortby:  # No sort request
            return
        if sortby not in fields:  # Column not in this rendering -- ignore silently
            return
        table.sortby = sortby  # Honor request

    @staticmethod
    def _populate_table_rows(table: PrettyTable, data: list[dict[str, Any]], fields: list[str]) -> None:
        """Append one row per input dict, pulling each cell in `fields` column order (default '')."""
        for item in data:  # Walk every input row
            row = [item.get(field, "") for field in fields]  # Pull cells in column order, default ""
            table.add_row(row)

    @staticmethod
    def dict_list_as_pretty_table(
        data: list[dict[str, Any]], fields: list[str] | None = None, sortby: str | None = None
    ) -> None:
        """Render a PrettyTable from a list of dicts; debug-log the result. No-op if data is empty."""
        if not data:  # Nothing to render
            return
        if fields is None:
            fields = DataProcessingUtils.get_unique_keys(data)
        table = PrettyTable()  # Build a fresh table per call
        table.field_names = fields  # Apply column ordering
        DisplayUtils._apply_sort_if_valid(table, sortby, fields)  # Optional sort
        DisplayUtils._populate_table_rows(table, data, fields)  # Fill cells
        logging.debug("\n%s", table.get_string())  # Emit fully rendered table at debug level

    @staticmethod
    def create_progress_bar(progress_percentage: float | None, bar_length: int = 20) -> str:
        """Create an ASCII progress bar visualization for upgrade progress.

        Args:
            progress_percentage: Progress value from 0 to 100 (int or float)
            bar_length: Total length of the progress bar in characters

        Returns:
            str: Formatted progress bar string like "[=========>          ] 45%"
        """
        clamped = DisplayUtils._clamp_progress_percentage(progress_percentage)  # Constrain to the 0..100 range
        filled_length = int(bar_length * clamped / 100)  # How many characters of the bar are filled
        bar = DisplayUtils._render_progress_bar(filled_length, bar_length)  # Build the filled/arrow/empty bar string
        return f"[{bar}] {clamped:3d}%"  # Bar plus right-aligned percentage label

    @staticmethod
    def _clamp_progress_percentage(progress_percentage: float | None) -> int:  # Constrain progress into 0..100
        """Clamp a progress value (or None) into the inclusive 0..100 range."""
        if progress_percentage is None or progress_percentage < 0:  # Missing or negative progress
            return 0  # Treat as not started
        if progress_percentage > 100:  # Above the maximum
            return 100  # Treat as complete
        return progress_percentage  # type: ignore[return-value]  # Already within range (preserve caller's numeric type)

    @staticmethod
    def _render_progress_bar(filled_length: int, bar_length: int) -> str:  # Build the bar glyph string
        """Render the bar glyphs for a given filled length: all-filled, all-empty, or filled+arrow+empty."""
        if filled_length == bar_length:  # Complete: every cell filled
            return "=" * bar_length  # Solid bar
        if filled_length == 0:  # Just started: every cell empty
            return " " * bar_length  # Empty bar
        return "=" * (filled_length - 1) + ">" + " " * (bar_length - filled_length)  # Filled + arrow + empty
