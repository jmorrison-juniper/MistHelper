"""Unit tests for src/ui/layout/results_grid_builder.py."""

from __future__ import annotations

from typing import Any

import pytest
from rich.console import Console

from src.ui.layout.results_grid_builder import (
    MAX_VISIBLE_ROWS,
    ResultsGridBuilder,
    _HierarchyFlattener,
    _ValueFormatter,
)


def _render(panel: Any) -> str:
    """Render a Rich renderable into plain text for substring assertions."""
    console = Console(width=160, record=True, force_terminal=False)
    console.print(panel)
    return console.export_text()


# --- _ValueFormatter ---------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "expected_substring"),
    [
        (None, "<empty>"),  # None branch
        ("", "<empty>"),  # Empty string branch
        (True, "True"),  # bool branch (cyan)
        (False, "False"),  # bool branch
        (7, "7"),  # int branch
        (1.5, "1.5"),  # float branch
        ("plain text", "plain text"),  # Generic string
        ("12345678-1234-1234-1234-123456789012", "magenta"),  # UUID branch (36 chars + '-')
        ("10.0.0.1", "bright_cyan"),  # IPv4-like branch
        ({"a": 1, "b": 2}, "expanded below"),  # Dict marker branch
    ],
)
def test_value_formatter_dispatch(value: Any, expected_substring: str) -> None:
    """Each value type takes the correct formatting branch."""
    out = _ValueFormatter().format(value)  # Run dispatch
    assert expected_substring in out  # Substring assertion


def test_value_formatter_inline_list_of_scalars() -> None:
    """A list of primitives is rendered inline."""
    out = _ValueFormatter().format([1, "two", None, True])  # Mixed primitives
    assert "[" in out and "]" in out  # Inline brackets


def test_value_formatter_complex_list_uses_marker() -> None:
    """A list containing non-primitive items shows the 'expand below' marker."""
    out = _ValueFormatter().format([{"a": 1}])  # List-of-dicts
    assert "expanded below" in out


def test_value_formatter_empty_list_marker() -> None:
    """Empty list returns the '<empty list>' marker."""
    assert "<empty list>" in _ValueFormatter().format([])


def test_value_formatter_unknown_type_uses_fallback() -> None:
    """Objects of unknown type fall back to bracketed str()."""

    class _X:
        def __str__(self) -> str:  # pragma: no cover - tiny passthrough
            return "x-instance"

    out = _ValueFormatter().format(_X())  # Generic branch
    assert "x-instance" in out


# --- _HierarchyFlattener ------------------------------------------------------


def test_flatten_returns_empty_for_non_dict() -> None:
    """Non-dict top-level input returns []."""
    assert _HierarchyFlattener(_ValueFormatter()).flatten([1, 2, 3]) == []


def test_flatten_scalar_value_rows() -> None:
    """Each scalar dict entry produces one 'value' row."""
    rows = _HierarchyFlattener(_ValueFormatter()).flatten({"a": 1, "b": "x"})
    types = [r[2] for r in rows]  # Pull row-type column
    assert types == ["value", "value"]  # Both scalars


def test_flatten_nested_dict_creates_section_header() -> None:
    """A nested dict value creates a section_header + recursive rows."""
    rows = _HierarchyFlattener(_ValueFormatter()).flatten({"meta": {"k": "v"}})
    types = [r[2] for r in rows]  # Pull row types
    assert "section_header" in types  # Header emitted
    assert any(r[2] == "value" for r in rows)  # Recursive row
    assert any(r[2] == "separator" for r in rows)  # Depth-0 separator


def test_flatten_list_of_dicts_emits_item_rows() -> None:
    """List-of-dicts produces a section header + per-item bracket label + values."""
    rows = _HierarchyFlattener(_ValueFormatter()).flatten({"items": [{"x": 1}, {"x": 2}]})
    types = [r[2] for r in rows]  # Pull row types
    assert types.count("list_item") == 2  # Two list items
    assert "section_header" in types  # Header present


# --- ResultsGridBuilder -------------------------------------------------------


def test_build_returns_none_when_no_results(tui_stub) -> None:
    """No results -> build() returns None."""
    tui_stub.last_parsed_data = {"results": []}  # Empty
    assert ResultsGridBuilder(tui_stub).build() is None


def test_build_returns_none_when_parsed_not_dict(tui_stub) -> None:
    """Non-dict parsed payload -> build() returns None."""
    tui_stub.last_parsed_data = ["raw", "list"]  # Wrong shape
    assert ResultsGridBuilder(tui_stub).build() is None


def test_build_returns_panel_for_simple_results(tui_stub) -> None:
    """A list of dicts yields a Rich Panel with the rendered grid."""
    tui_stub.last_parsed_data = {
        "results": [{"id": "abc", "name": "alpha"}, {"id": "def", "name": "beta"}],
        "total": 2,
    }
    panel = ResultsGridBuilder(tui_stub).build()  # Build first result
    assert panel is not None  # Real panel returned
    text = _render(panel)
    assert "abc" in text and "alpha" in text  # First result rendered
    assert "Result 1 of 2" in text  # Nav info present
    assert "Total: 2" in text  # Total preserved


def test_build_clamps_scroll_offset_when_out_of_range(tui_stub) -> None:
    """An out-of-range scroll offset is clamped to the last result index."""
    tui_stub.last_parsed_data = {"results": [{"a": 1}, {"a": 2}]}
    tui_stub.results_scroll_offset = 99  # Out of range
    ResultsGridBuilder(tui_stub).build()  # Triggers clamp
    assert tui_stub.results_scroll_offset == 1  # Clamped to last index


def test_clamp_current_index_persists_clamp(tui_stub) -> None:
    """_clamp_current_index updates the TUI's scroll offset in place."""
    tui_stub.last_parsed_data = {"results": [{"a": 1}]}  # Single result
    tui_stub.results_scroll_offset = 5  # Out of range
    idx = ResultsGridBuilder(tui_stub)._clamp_current_index([{"a": 1}])
    assert idx == 0  # Clamped
    assert tui_stub.results_scroll_offset == 0  # Side-effect persisted


def test_compute_row_window_no_scroll(tui_stub) -> None:
    """When total rows fit, the window is [0, total_rows]."""
    tui_stub._get_terminal_height = lambda: 100  # Plenty of room
    start, end = ResultsGridBuilder(tui_stub)._compute_row_window(10)
    assert (start, end) == (0, 10)


def test_compute_row_window_respects_scroll_offset(tui_stub) -> None:
    """When scrolled, start = scroll_offset and end clamps to total."""
    tui_stub._get_terminal_height = lambda: 30  # Limits visible rows
    tui_stub.result_row_scroll = 5  # User scrolled
    start, end = ResultsGridBuilder(tui_stub)._compute_row_window(100)
    assert start == 5
    assert end <= start + MAX_VISIBLE_ROWS  # Bounded by MAX_VISIBLE_ROWS


def test_compose_row_info_all_visible() -> None:
    """When start=0 and end>=total, the 'All N rows visible' label is used."""
    label = ResultsGridBuilder._compose_row_info(total_rows=10, start_row=0, end_row=10)
    assert label == " | All 10 rows visible"


@pytest.mark.parametrize(
    ("start", "end", "expected_arrows"),
    [
        (0, 5, "v"),  # Only down arrow (more below)
        (5, 10, "^"),  # Only up arrow (more above)
        (3, 7, "^v"),  # Both directions
    ],
)
def test_compose_row_info_with_arrows(start: int, end: int, expected_arrows: str) -> None:
    """The arrows indicator reflects available scroll directions."""
    label = ResultsGridBuilder._compose_row_info(total_rows=10, start_row=start, end_row=end)
    assert expected_arrows in label  # Expected arrow combo present


def test_populate_table_emits_separator(tui_stub) -> None:
    """The populator emits a dashed separator row for separator-typed rows."""

    class _StubTable:
        def __init__(self) -> None:
            self.rows: list[tuple[str, str]] = []

        def add_row(self, field: str, value: str) -> None:  # test helper
            self.rows.append((field, value))

    table = _StubTable()  # Capture writes
    ResultsGridBuilder._populate_table(table, [["a", "b", "value"], ["", "", "separator"]])
    assert len(table.rows) == 2  # Two rows added
    # The separator row uses '----' fill in both columns:
    assert "---" in table.rows[1][0] and "---" in table.rows[1][1]


def test_safe_results_handles_bad_shapes(tui_stub) -> None:
    """_safe_results returns [] for missing / wrong-typed data."""
    tui_stub.last_parsed_data = None  # No data
    assert ResultsGridBuilder(tui_stub)._safe_results() == []
    tui_stub.last_parsed_data = {"results": "not-a-list"}  # Wrong type
    assert ResultsGridBuilder(tui_stub)._safe_results() == []
    tui_stub.last_parsed_data = {"results": [{"x": 1}]}  # Valid
    assert ResultsGridBuilder(tui_stub)._safe_results() == [{"x": 1}]
