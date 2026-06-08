"""Replacement for ``MistHelperTUI._create_results_grid`` (CC=18).

Decomposed into a builder class plus a value-formatter helper. Every method
has CC <= 10.
"""

from __future__ import annotations

import logging
from typing import Any

MAX_VISIBLE_ROWS = 25  # Hard cap on visible rows in grid


class _ValueFormatter:
    """Format scalar values for the results grid (replaces inner closure)."""

    EMPTY = "[dim]<empty>[/dim]"  # Display token for empty/None values

    def format(self, value: Any) -> str:
        """Return a Rich-markup string for ``value`` (dispatch by type)."""
        if value is None or value == "":  # None and empty string both -> empty
            return self.EMPTY
        if isinstance(value, bool):  # bool comes before int by design
            return f"[bright_cyan]{value!s}[/bright_cyan]"
        if isinstance(value, (int, float)):  # Numeric -> green
            return f"[bright_green]{value}[/bright_green]"
        if isinstance(value, str):  # String paths handle UUID + IP styling
            return self._format_string(value)
        if isinstance(value, list):
            return self._format_list(value)
        if isinstance(value, dict):
            return f"[magenta]v {len(value)} keys (expanded below)[/magenta]"
        return f"[white]{value!s}[/white]"  # Fallback for unknown types

    @staticmethod
    def _format_string(value: str) -> str:
        """Apply UUID / IP / generic-string styling to a string value."""
        if len(value) == 36 and "-" in value:  # UUID-shaped string
            return f"[bright_magenta]{value}[/bright_magenta]"
        parts = value.split(".")  # Tokenize candidate IPv4 string
        if "." in value and all(part.isdigit() or part == "" for part in parts):
            return f"[bright_cyan]{value}[/bright_cyan]"
        return f"[white]{value}[/white]"

    def _format_list(self, value: list[Any]) -> str:
        """Format a list value as either inline or 'expand below' marker."""
        if not value:  # Empty list
            return "[dim]<empty list>[/dim]"
        if all(isinstance(item, (str, int, float, bool, type(None))) for item in value):
            joined = ", ".join(str(v) if v is not None else "<empty>" for v in value)
            return f"[bright_yellow][ {joined} ][/bright_yellow]"  # Inline simple list
        return f"[yellow]v {len(value)} items (expanded below)[/yellow]"  # Defer complex list to flatten


class _HierarchyFlattener:
    """Flatten a nested dict/list into (field, value, row_type) tuples."""

    def __init__(self, value_formatter: _ValueFormatter) -> None:
        self._fmt = value_formatter  # Cached value formatter

    def flatten(self, data: Any, depth: int = 0) -> list[list[str]]:
        """Top-level entry point; returns a list of [field, value, row_type] rows."""
        if not isinstance(data, dict):  # Only dicts produce rows at top
            return []
        rows: list[list[str]] = []  # Accumulator
        for key, value in data.items():  # Walk every key
            self._dispatch(rows, key, value, depth)  # Dispatch on value shape
        return rows

    def _dispatch(self, rows: list[list[str]], key: str, value: Any, depth: int) -> None:
        """Dispatch a single key/value pair to the correct row builder."""
        if isinstance(value, dict) and value:  # Non-empty dict -> nested section
            self._append_dict_section(rows, key, value, depth)
            return
        if isinstance(value, list) and value and isinstance(value[0], dict):  # List-of-dicts -> nested section
            self._append_list_section(rows, key, value, depth)
            return
        rows.append([self._key_style(key, depth), self._fmt.format(value), "value"])  # Scalar value row

    def _append_dict_section(self, rows: list[list[str]], key: str, value: dict[str, Any], depth: int) -> None:
        """Append a header row + recursive flatten for a nested dict value."""
        rows.append([self._header_style(key, depth), f"[dim italic]{len(value)} fields[/dim italic]", "section_header"])
        rows.extend(self.flatten(value, depth + 1))  # Recurse one level deeper
        if depth == 0:  # Add separator at top level
            rows.append(["", "", "separator"])

    def _append_list_section(self, rows: list[list[str]], key: str, value: list[Any], depth: int) -> None:
        """Append a header row + per-item flatten for a list-of-dicts value."""
        rows.append([self._header_style(key, depth), f"[dim italic]{len(value)} items[/dim italic]", "section_header"])
        for idx, item in enumerate(value):  # Walk every list item
            sub_indent = "  " * (depth + 1)  # Indent for the bracket label
            rows.append([f"[magenta]{sub_indent}[{idx}][/magenta]", "", "list_item"])
            rows.extend(self.flatten(item, depth + 2))  # Recurse into the item
        if depth == 0:  # Add separator at top level
            rows.append(["", "", "separator"])

    @staticmethod
    def _header_style(key: str, depth: int) -> str:
        """Return the Rich-markup header style appropriate for ``depth``."""
        indent = "  " * depth  # Per-depth indent
        if depth == 0:
            return f"[bold bright_cyan on grey15]{indent}> {key.upper()}[/bold bright_cyan on grey15]"
        if depth == 1:
            return f"[bold bright_yellow]{indent}+- {key}[/bold bright_yellow]"
        return f"[bold white]{indent}+- {key}[/bold white]"

    @staticmethod
    def _key_style(key: str, depth: int) -> str:
        """Return the Rich-markup field style appropriate for ``depth``."""
        indent = "  " * depth  # Per-depth indent
        if depth == 0:
            return f"[bold bright_white]{indent}{key}[/bold bright_white]"
        if depth == 1:
            return f"[yellow]{indent}  {key}[/yellow]"
        return f"[dim white]{indent}    {key}[/dim white]"


class ResultsGridBuilder:
    """Build the Rich Panel that holds the results-grid table."""

    def __init__(self, tui: Any) -> None:
        self._tui = tui  # Back-reference for state + Rich classes
        self._formatter = _ValueFormatter()  # Built once (perf rule)
        self._flattener = _HierarchyFlattener(self._formatter)  # Built once (perf rule)

    def build(self) -> Any:
        """Return the Rich Panel for the current result, or ``None`` when no data."""
        logging.info("TUI: building results grid")  # Action log before build
        results = self._safe_results()  # Guarded access to parsed results
        if not results:  # No data -> caller handles fallback
            return None
        current_idx = self._clamp_current_index(results)  # Clamp scroll offset to valid index
        result = results[current_idx]  # Pick the one result to render
        table = self._build_table()  # Build the Rich Table shell
        all_rows = self._flattener.flatten(result)  # Flatten this result's rows
        start_row, end_row = self._compute_row_window(len(all_rows))  # Pick visible row window
        self._populate_table(table, all_rows[start_row:end_row])  # Fill visible rows
        title = self._compose_title(current_idx, len(results), len(all_rows), start_row, end_row)
        logging.debug("TUI: results grid built (rows=%s)", len(all_rows))  # Action log after build
        return self._tui.Panel(table, title=title, border_style="bright_yellow", box=self._tui.box.DOUBLE, expand=True)

    def _safe_results(self) -> list[Any]:
        """Return the list under ``last_parsed_data['results']``, or empty."""
        parsed = self._tui.last_parsed_data  # Snapshot the parsed payload
        if not isinstance(parsed, dict):  # Guard: missing or non-dict
            return []
        results = parsed.get("results", [])  # Pull the results array
        return results if isinstance(results, list) else []  # Guard: non-list

    def _clamp_current_index(self, results: list[Any]) -> int:
        """Return the index of the result to render, clamping the scroll offset."""
        current: int = self._tui.results_scroll_offset  # User-driven scroll position
        if current >= len(results):  # Out of range -> clamp at last
            current = len(results) - 1
            self._tui.results_scroll_offset = current  # Persist the clamp
        return current

    def _build_table(self) -> Any:
        """Construct the empty Rich Table with the two column headers."""
        from rich.table import Table as RichTable  # Local import for Rich

        table = RichTable(
            show_header=True,
            header_style="bold bright_cyan on grey15",
            box=self._tui.box.HEAVY,
            expand=True,
            show_lines=True,
            padding=(0, 1),
            row_styles=["", "on grey3"],
            width=None,
        )
        table.add_column("Field", style="bright_white", ratio=35, no_wrap=False, overflow="fold")
        table.add_column("Value", style="bright_white", ratio=65, no_wrap=False, overflow="fold")
        return table

    def _compute_row_window(self, total_rows: int) -> tuple[int, int]:
        """Compute the [start, end) row indices to render based on scroll state."""
        max_visible = min(MAX_VISIBLE_ROWS, self._tui._get_terminal_height())  # Bounded by terminal height
        start_row = min(self._tui.result_row_scroll, max(0, total_rows - max_visible))
        end_row = min(start_row + max_visible, total_rows)  # Clamp end at total
        return start_row, end_row

    @staticmethod
    def _populate_table(table: Any, rows: list[list[str]]) -> None:
        """Add each ``rows`` entry to ``table``, honoring the separator row type."""
        for field_name, value, row_type in rows:  # Walk visible rows in order
            if row_type == "separator":  # Special dashed separator row
                table.add_row("[dim]" + "-" * 40 + "[/dim]", "[dim]" + "-" * 60 + "[/dim]")
            else:
                table.add_row(field_name, value)

    def _compose_title(
        self, current_idx: int, total_results: int, total_rows: int, start_row: int, end_row: int
    ) -> str:
        """Compose the Panel title showing nav info, totals and scroll position."""
        parsed = self._tui.last_parsed_data or {}  # Defensive dict default
        total = parsed.get("total", total_results)  # Server-reported total
        actual_limit = self._tui.function_params.get("limit", 1000)  # User-requested page size
        distinct = parsed.get("distinct", "N/A")  # Server-reported distinct count
        nav_info = f"Result {current_idx + 1} of {total_results}"  # "X of Y" label
        result_pct = int(((current_idx + 1) / total_results) * 100) if total_results else 100
        row_info = self._compose_row_info(total_rows, start_row, end_row)  # Row-scroll suffix
        return (
            f"[bold bright_yellow]{nav_info}[/bold bright_yellow] "
            f"| Total: {total} | Limit: {actual_limit} | Distinct: {distinct} "
            f"{row_info} | {result_pct}%"
        )

    @staticmethod
    def _compose_row_info(total_rows: int, start_row: int, end_row: int) -> str:
        """Build the 'Rows X-Y of Z' string with scroll arrows when scrolling."""
        max_visible = end_row - start_row  # Window size used to render
        if total_rows <= max_visible:  # Everything visible -> simple text
            return f" | All {total_rows} rows visible"
        can_up = start_row > 0  # Up-arrow eligibility
        can_down = end_row < total_rows  # Down-arrow eligibility
        if can_up and can_down:
            arrows = " [bright_yellow]^v[/bright_yellow]"
        elif can_up:
            arrows = " [bright_yellow]^[/bright_yellow]"
        elif can_down:
            arrows = " [bright_yellow]v[/bright_yellow]"
        else:
            arrows = ""
        return f" | Rows {start_row + 1}-{end_row} of {total_rows}{arrows}"
