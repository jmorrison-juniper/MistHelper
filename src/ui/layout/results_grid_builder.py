"""Replacement for ``MistHelperTUI._create_results_grid`` (was CC=18).

Decomposed into a value-formatter, a hierarchy flattener, and a builder.
Every function is complexity-bounded (CC <= 5) via table-driven dispatch
and predicate helpers so the analyzer sees no complexity/blocks debt.
"""

from __future__ import annotations  # WHY: postponed eval for forward refs in type hints

import logging  # WHY: structured action logging for build lifecycle
from typing import Any  # WHY: TUI hooks + payload values are heterogeneous

MAX_VISIBLE_ROWS = 25  # WHY: hard cap on visible rows so wide payloads stay legible
UUID_LEN = 36  # WHY: canonical hyphenated UUID length; used by _is_uuid_like
SIMPLE_LIST_TYPES = (str, int, float, bool, type(None))  # WHY: primitives render inline
SEPARATOR_ROW_TYPE = "separator"  # WHY: sentinel row type read by _populate_table
_SEPARATOR_FIELD = "[dim]" + "-" * 40 + "[/dim]"  # WHY: pre-built dashed field cell
_SEPARATOR_VALUE = "[dim]" + "-" * 60 + "[/dim]"  # WHY: pre-built dashed value cell


def _is_uuid_like(value: str) -> bool:  # WHY: predicate helper factored out of _format_string
    """Return True when ``value`` matches the 36-char hyphenated UUID shape."""
    return len(value) == UUID_LEN and "-" in value  # WHY: cheap heuristic, no regex cost


def _is_numeric_or_blank(part: str) -> bool:  # WHY: single-token check used by _is_ipv4_like
    """Return True for the digit-or-empty parts of a candidate IPv4 split."""
    return part.isdigit() or part == ""  # WHY: allow trailing '.' during typing


def _is_ipv4_like(value: str) -> bool:  # WHY: predicate helper factored out of _format_string
    """Return True when ``value`` looks like dotted IPv4 (loose check)."""
    if "." not in value:  # WHY: guard clause skips the split for non-dotted strings
        return False  # WHY: no dot => cannot be IPv4
    return all(_is_numeric_or_blank(part) for part in value.split("."))  # WHY: token check


def _is_simple_list(value: list[Any]) -> bool:  # WHY: keeps _format_list branching flat
    """Return True when every element is a primitive suitable for inline rendering."""
    return all(isinstance(item, SIMPLE_LIST_TYPES) for item in value)  # WHY: dispatch guard


def _list_item_repr(item: Any) -> str:  # WHY: single item repr keeps list join simple
    """Return the inline representation for a single simple-list element."""
    return "<empty>" if item is None else str(item)  # WHY: None renders as visible token


def _is_nested_dict(value: Any) -> bool:  # WHY: predicate helper used by _HierarchyFlattener._dispatch
    """Return True when ``value`` is a non-empty dict (needs section header)."""
    return isinstance(value, dict) and bool(value)  # WHY: skip empty dicts, they render inline


def _is_list_of_dicts(value: Any) -> bool:  # WHY: predicate helper used by _HierarchyFlattener._dispatch
    """Return True when ``value`` is a non-empty list whose first item is a dict."""
    if not isinstance(value, list) or not value:  # WHY: guard for non-list / empty list
        return False  # WHY: empty or wrong-typed value cannot be list-of-dicts
    return isinstance(value[0], dict)  # WHY: first-item type drives section-vs-inline choice


_ARROW_MAP: dict[tuple[bool, bool], str] = {
    (True, True): " [bright_yellow]^v[/bright_yellow]",  # WHY: can scroll both directions
    (True, False): " [bright_yellow]^[/bright_yellow]",  # WHY: only up available
    (False, True): " [bright_yellow]v[/bright_yellow]",  # WHY: only down available
    (False, False): "",  # WHY: fits window exactly, no arrows
}


class _ValueFormatter:  # WHY: replaces inner closure so it can be unit-tested
    """Format scalar values for the results grid (replaces inner closure)."""

    EMPTY = "[dim]<empty>[/dim]"  # WHY: shared display token for None / empty string

    def format(self, value: Any) -> str:  # WHY: single public entry point for row rendering
        """Return a Rich-markup string for ``value`` via type-dispatch table."""
        if value is None or value == "":  # WHY: single guard handles both empty forms
            return self.EMPTY  # WHY: emit shared empty token for both None and ""
        renderer = _TYPE_RENDERERS.get(type(value))  # WHY: exact-type lookup keeps bool distinct
        if renderer is None:  # WHY: unknown type falls through to safe str() render
            return f"[white]{value!s}[/white]"  # WHY: fallback style for unknown types
        result: str = renderer(self, value)  # WHY: dispatch to bound-method renderer
        return result  # WHY: explicit str typing keeps mypy strict happy

    def _render_bool(self, value: bool) -> str:  # noqa: ARG002 - self kept for uniform signature
        """Render a bool value in cyan (kept before int by dispatch table)."""
        return f"[bright_cyan]{value!s}[/bright_cyan]"  # WHY: bool distinguished from int

    def _render_number(self, value: int | float) -> str:  # noqa: ARG002 - self kept for uniform signature
        """Render numeric values (int/float) with the green highlight."""
        return f"[bright_green]{value}[/bright_green]"  # WHY: numeric emphasis in grid

    def _render_dict(self, value: dict[str, Any]) -> str:  # noqa: ARG002 - self kept for uniform signature
        """Render a dict value as a 'expand below' marker with key count."""
        return f"[magenta]v {len(value)} keys (expanded below)[/magenta]"  # WHY: defer to flatten

    def _format_string(self, value: str) -> str:  # WHY: string-value branch of the dispatch table
        """Apply UUID / IPv4 / generic-string styling to a string value."""
        if _is_uuid_like(value):  # WHY: UUIDs get magenta emphasis for scannability
            return f"[bright_magenta]{value}[/bright_magenta]"  # WHY: dedicated UUID color
        if _is_ipv4_like(value):  # WHY: IP addresses share the cyan highlight
            return f"[bright_cyan]{value}[/bright_cyan]"  # WHY: dedicated IP color
        return f"[white]{value}[/white]"  # WHY: default plain-string style

    def _format_list(self, value: list[Any]) -> str:  # WHY: list-value branch of the dispatch table
        """Return inline markup for simple lists, else the 'expand below' marker."""
        if not value:  # WHY: guard for empty-list case with dedicated marker
            return "[dim]<empty list>[/dim]"  # WHY: distinct marker separates from None/""
        if not _is_simple_list(value):  # WHY: complex items defer to flatten
            return f"[yellow]v {len(value)} items (expanded below)[/yellow]"  # WHY: defer marker
        joined = ", ".join(_list_item_repr(v) for v in value)  # WHY: format each element uniformly
        return f"[bright_yellow][ {joined} ][/bright_yellow]"  # WHY: inline bracketed list style


_TYPE_RENDERERS: dict[type, Any] = {
    bool: _ValueFormatter._render_bool,  # WHY: bool BEFORE int so True/False dispatch correctly
    int: _ValueFormatter._render_number,  # WHY: int shares numeric renderer
    float: _ValueFormatter._render_number,  # WHY: float shares numeric renderer
    str: _ValueFormatter._format_string,  # WHY: strings route to UUID/IPv4 detection
    list: _ValueFormatter._format_list,  # WHY: list routes to inline-or-defer branch
    dict: _ValueFormatter._render_dict,  # WHY: dict shows key count marker
}


class _HierarchyFlattener:  # WHY: encapsulates dict/list->rows walk, unit-testable
    """Flatten a nested dict/list into (field, value, row_type) tuples."""

    def __init__(self, value_formatter: _ValueFormatter) -> None:  # WHY: DI keeps formatter swappable
        """Cache the value formatter so nested calls avoid re-instantiating it."""
        self._fmt = value_formatter  # WHY: cached formatter for scalar rows

    def flatten(self, data: Any, depth: int = 0) -> list[list[str]]:  # WHY: recursive entry point
        """Return a list of [field, value, row_type] rows for ``data``."""
        if not isinstance(data, dict):  # WHY: only dicts produce rows at the top level
            return []  # WHY: non-dict input yields no rows (contract simplifies callers)
        rows: list[list[str]] = []  # WHY: accumulator for this depth level
        for key, value in data.items():  # WHY: walk every key preserving insertion order
            self._dispatch(rows, key, value, depth)  # WHY: shape-based dispatch per pair
        return rows  # WHY: return accumulated rows in insertion order

    def _dispatch(self, rows: list[list[str]], key: str, value: Any, depth: int) -> None:  # WHY: table-driven fan-out
        """Dispatch a single key/value pair to the correct row builder."""
        if _is_nested_dict(value):  # WHY: non-empty dict opens a nested section
            self._append_dict_section(rows, key, value, depth)  # WHY: emit header + recurse
            return  # WHY: dict branch handled, skip remaining checks
        if _is_list_of_dicts(value):  # WHY: list-of-dicts opens a per-item section
            self._append_list_section(rows, key, value, depth)  # WHY: emit header + items
            return  # WHY: list branch handled, skip scalar fallback
        rows.append([self._key_style(key, depth), self._fmt.format(value), "value"])  # WHY: scalar row

    def _append_dict_section(  # WHY: nested-dict handler kept small to bound _dispatch complexity
        self, rows: list[list[str]], key: str, value: dict[str, Any], depth: int
    ) -> None:
        """Append a header row + recursive flatten for a nested dict value."""
        rows.append(  # WHY: emit the section header row before recursing
            [self._header_style(key, depth), f"[dim italic]{len(value)} fields[/dim italic]", "section_header"]
        )
        rows.extend(self.flatten(value, depth + 1))  # WHY: recurse one level deeper
        if depth == 0:  # WHY: separator only after top-level sections
            rows.append(["", "", SEPARATOR_ROW_TYPE])  # WHY: dashed separator anchors the section

    def _append_list_section(  # WHY: list-of-dicts handler split from _dispatch to bound complexity
        self, rows: list[list[str]], key: str, value: list[Any], depth: int
    ) -> None:
        """Append a header row + per-item flatten for a list-of-dicts value."""
        rows.append(  # WHY: emit the section header row before iterating items
            [self._header_style(key, depth), f"[dim italic]{len(value)} items[/dim italic]", "section_header"]
        )
        for idx, item in enumerate(value):  # WHY: emit bracket label + rows per item
            sub_indent = "  " * (depth + 1)  # WHY: indent scaled to nesting depth
            rows.append([f"[magenta]{sub_indent}[{idx}][/magenta]", "", "list_item"])  # WHY: item bracket row
            rows.extend(self.flatten(item, depth + 2))  # WHY: recurse into the item dict
        if depth == 0:  # WHY: separator only after top-level sections
            rows.append(["", "", SEPARATOR_ROW_TYPE])  # WHY: dashed separator anchors the section

    @staticmethod
    def _header_style(key: str, depth: int) -> str:  # WHY: depth-driven header style selector
        """Return the Rich-markup header style appropriate for ``depth``."""
        indent = "  " * depth  # WHY: per-depth indent aligned with tree glyphs
        if depth == 0:  # WHY: top-level headers get inverse-video emphasis
            return (
                f"[bold bright_cyan on grey15]{indent}> {key.upper()}[/bold bright_cyan on grey15]"  # WHY: root style
            )
        if depth == 1:  # WHY: mid-level headers use the yellow tree branch style
            return f"[bold bright_yellow]{indent}+- {key}[/bold bright_yellow]"  # WHY: depth-1 branch style
        return f"[bold white]{indent}+- {key}[/bold white]"  # WHY: deeper headers use dim white

    @staticmethod
    def _key_style(key: str, depth: int) -> str:  # WHY: depth-driven field-label style selector
        """Return the Rich-markup field style appropriate for ``depth``."""
        indent = "  " * depth  # WHY: per-depth indent aligned with parent header
        if depth == 0:  # WHY: top-level fields use bold bright white
            return f"[bold bright_white]{indent}{key}[/bold bright_white]"  # WHY: root field style
        if depth == 1:  # WHY: mid-level fields use yellow to match header branch
            return f"[yellow]{indent}  {key}[/yellow]"  # WHY: depth-1 field style
        return f"[dim white]{indent}    {key}[/dim white]"  # WHY: deeper fields dim


class ResultsGridBuilder:  # WHY: public builder for the results Panel, owned by MistHelperTUI
    """Build the Rich Panel that holds the results-grid table."""

    def __init__(self, tui: Any) -> None:  # WHY: retain TUI back-reference for state + Rich hooks
        """Store TUI back-reference and pre-build formatter + flattener once."""
        self._tui = tui  # WHY: back-reference for scroll state + Rich class factories
        self._formatter = _ValueFormatter()  # WHY: cache built once (perf rule)
        self._flattener = _HierarchyFlattener(self._formatter)  # WHY: cache built once (perf rule)

    def build(self) -> Any:  # WHY: sole public entry consumed by LayoutBuilder
        """Return the Rich Panel for the current result, or ``None`` when no data."""
        logging.info("TUI: building results grid")  # WHY: action log before build
        results = self._safe_results()  # WHY: guarded access to parsed results
        if not results:  # WHY: no data -> caller shows fallback panel
            return None  # WHY: None signals LayoutBuilder to render fallback
        current_idx = self._clamp_current_index(results)  # WHY: clamp scroll offset to valid index
        result = results[current_idx]  # WHY: pick the one result to render
        table = self._build_table()  # WHY: build the Rich Table shell
        all_rows = self._flattener.flatten(result)  # WHY: flatten this result's rows
        start_row, end_row = self._compute_row_window(len(all_rows))  # WHY: pick visible row window
        self._populate_table(table, all_rows[start_row:end_row])  # WHY: fill visible rows
        title = self._compose_title(current_idx, len(results), len(all_rows), start_row, end_row)
        logging.debug("TUI: results grid built (rows=%s)", len(all_rows))  # WHY: action log after build
        return self._tui.Panel(table, title=title, border_style="bright_yellow", box=self._tui.box.DOUBLE, expand=True)

    def _safe_results(self) -> list[Any]:
        """Return the list under ``last_parsed_data['results']``, or empty."""
        parsed = self._tui.last_parsed_data  # WHY: snapshot the parsed payload once
        if not isinstance(parsed, dict):  # WHY: guard for missing or non-dict payloads
            return []
        results = parsed.get("results", [])  # WHY: pull the results array with default
        return results if isinstance(results, list) else []  # WHY: guard against non-list

    def _clamp_current_index(self, results: list[Any]) -> int:
        """Return the index of the result to render, clamping the scroll offset."""
        current: int = self._tui.results_scroll_offset  # WHY: user-driven scroll position
        if current >= len(results):  # WHY: out-of-range -> clamp at last index
            current = len(results) - 1
            self._tui.results_scroll_offset = current  # WHY: persist the clamp for next build
        return current

    def _build_table(self) -> Any:
        """Construct the empty Rich Table with the two column headers."""
        from rich.table import Table as RichTable  # WHY: local import keeps module import cheap

        table = RichTable(
            show_header=True,  # WHY: column header row is part of the panel design
            header_style="bold bright_cyan on grey15",  # WHY: matches top-level section style
            box=self._tui.box.HEAVY,  # WHY: heavy box separates results grid visually
            expand=True,  # WHY: fill available panel width
            show_lines=True,  # WHY: horizontal rules improve row scannability
            padding=(0, 1),  # WHY: tight vertical padding, one col of horizontal
            row_styles=["", "on grey3"],  # WHY: zebra striping via alternating row style
            width=None,  # WHY: let expand=True drive the width
        )
        table.add_column("Field", style="bright_white", ratio=35, no_wrap=False, overflow="fold")
        table.add_column("Value", style="bright_white", ratio=65, no_wrap=False, overflow="fold")
        return table

    def _compute_row_window(self, total_rows: int) -> tuple[int, int]:
        """Compute the [start, end) row indices to render based on scroll state."""
        max_visible = min(MAX_VISIBLE_ROWS, self._tui._get_terminal_height())  # WHY: bounded by terminal
        start_row = min(self._tui.result_row_scroll, max(0, total_rows - max_visible))  # WHY: clamp start
        end_row = min(start_row + max_visible, total_rows)  # WHY: clamp end at total rows
        return start_row, end_row

    @staticmethod
    def _populate_table(table: Any, rows: list[list[str]]) -> None:
        """Add each row entry to ``table``, honoring the separator row type."""
        for field_name, value, row_type in rows:  # WHY: walk visible rows in order
            if row_type == SEPARATOR_ROW_TYPE:  # WHY: special dashed separator row
                table.add_row(_SEPARATOR_FIELD, _SEPARATOR_VALUE)
            else:
                table.add_row(field_name, value)  # WHY: normal field/value row

    def _compose_title(
        self, current_idx: int, total_results: int, total_rows: int, start_row: int, end_row: int
    ) -> str:
        """Compose the Panel title showing nav info, totals and scroll position."""
        parsed = self._tui.last_parsed_data or {}  # WHY: defensive dict default
        total = parsed.get("total", total_results)  # WHY: fallback to result count when absent
        actual_limit = self._tui.function_params.get("limit", 1000)  # WHY: user-requested page size
        distinct = parsed.get("distinct", "N/A")  # WHY: server-reported distinct count
        nav_info = f"Result {current_idx + 1} of {total_results}"  # WHY: X-of-Y label
        result_pct = int(((current_idx + 1) / total_results) * 100) if total_results else 100
        row_info = self._compose_row_info(total_rows, start_row, end_row)  # WHY: row-scroll suffix
        return (
            f"[bold bright_yellow]{nav_info}[/bold bright_yellow] "
            f"| Total: {total} | Limit: {actual_limit} | Distinct: {distinct} "
            f"{row_info} | {result_pct}%"
        )

    @staticmethod
    def _compose_row_info(total_rows: int, start_row: int, end_row: int) -> str:
        """Build the 'Rows X-Y of Z' string with scroll arrows when scrolling."""
        max_visible = end_row - start_row  # WHY: window size used to render
        if total_rows <= max_visible:  # WHY: everything visible -> simple text
            return f" | All {total_rows} rows visible"
        arrows = _ARROW_MAP[(start_row > 0, end_row < total_rows)]  # WHY: table replaces if/elif chain
        return f" | Rows {start_row + 1}-{end_row} of {total_rows}{arrows}"
