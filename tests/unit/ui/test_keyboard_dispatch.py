"""Unit tests for src/ui/input_handlers/keyboard_dispatch.py."""

from __future__ import annotations

import pytest

from src.ui.input_handlers.keyboard_dispatch import KeyboardDispatchTable

# --- viewing_results mode ------------------------------------------------------


def _grid_state(tui_stub, results: list[dict[str, str]] | None = None) -> None:
    """Place the tui_stub into viewing_results state with the given dataset."""
    tui_stub.execution_state = "viewing_results"  # Mode under test
    tui_stub.last_parsed_data = {"results": results if results is not None else [{"id": "a"}, {"id": "b"}, {"id": "c"}]}


def test_dispatch_unknown_key_in_results_is_noop(tui_stub) -> None:
    """An unknown key in viewing_results mode is silently dropped."""
    _grid_state(tui_stub)  # Enter mode
    KeyboardDispatchTable(tui_stub).dispatch("z")  # Unknown handler
    assert tui_stub.execution_state == "viewing_results"  # Unchanged


def test_results_navigation_left_right(tui_stub) -> None:
    """Left/right move scroll offset, clamped at zero and len-1."""
    _grid_state(tui_stub)  # 3 results
    dt = KeyboardDispatchTable(tui_stub)
    dt.dispatch("right")  # 0 -> 1
    assert tui_stub.results_scroll_offset == 1
    dt.dispatch("right")  # 1 -> 2 (last)
    dt.dispatch("right")  # Clamped at 2
    assert tui_stub.results_scroll_offset == 2
    dt.dispatch("left")  # 2 -> 1
    dt.dispatch("left")  # 1 -> 0
    dt.dispatch("left")  # Clamped at 0
    assert tui_stub.results_scroll_offset == 0


def test_results_row_scroll_keys(tui_stub) -> None:
    """Up/down/page_up/page_down adjust result_row_scroll in 10/20 steps."""
    _grid_state(tui_stub)  # Need data so jump_end works
    tui_stub.result_row_scroll = 25  # Mid-scroll position
    dt = KeyboardDispatchTable(tui_stub)
    dt.dispatch("up")  # -10
    assert tui_stub.result_row_scroll == 15
    dt.dispatch("page_up")  # -20
    assert tui_stub.result_row_scroll == 0  # Clamped at 0
    dt.dispatch("down")  # +10
    assert tui_stub.result_row_scroll == 10
    dt.dispatch("page_down")  # +20
    assert tui_stub.result_row_scroll == 30


def test_results_jump_top_and_end(tui_stub) -> None:
    """'h' jumps to top, 'e' jumps to a large sentinel value (clamped by builder)."""
    _grid_state(tui_stub)
    tui_stub.result_row_scroll = 50  # Arbitrary
    dt = KeyboardDispatchTable(tui_stub)
    dt.dispatch("h")  # Top
    assert tui_stub.result_row_scroll == 0
    dt.dispatch("e")  # End
    assert tui_stub.result_row_scroll == 999999  # Sentinel


def test_results_close_via_escape(tui_stub) -> None:
    """Escape (either key alias) exits results mode and resets scroll."""
    _grid_state(tui_stub)
    tui_stub.results_scroll_offset = 2
    tui_stub.result_row_scroll = 50
    KeyboardDispatchTable(tui_stub).dispatch("escape")  # Close mode
    assert tui_stub.execution_state is None  # Returned to navigation
    assert tui_stub.results_scroll_offset == 0  # Reset
    assert tui_stub.result_row_scroll == 0  # Reset


def test_results_q_sets_quit(tui_stub) -> None:
    """'q' in results mode sets running = False."""
    _grid_state(tui_stub)
    KeyboardDispatchTable(tui_stub).dispatch("q")  # Quit
    assert tui_stub.running is False


def test_results_jump_end_does_nothing_without_data(tui_stub) -> None:
    """'e' is a no-op when there are no results to display."""
    _grid_state(tui_stub, results=[])  # Empty results
    tui_stub.result_row_scroll = 5
    KeyboardDispatchTable(tui_stub).dispatch("e")  # Should not modify
    assert tui_stub.result_row_scroll == 5  # Unchanged


# --- prompting mode -----------------------------------------------------------


def test_prompting_enter_submits(tui_stub) -> None:
    """Enter ('\\r' / '\\n') delegates to _submit_parameter."""
    tui_stub.execution_state = "prompting"  # Mode under test
    KeyboardDispatchTable(tui_stub).dispatch("\r")  # CR
    tui_stub._submit_parameter.assert_called_once()


def test_prompting_escape_cancels(tui_stub) -> None:
    """Escape in prompt mode delegates to _cancel_execution."""
    tui_stub.execution_state = "prompting"
    KeyboardDispatchTable(tui_stub).dispatch("escape")  # Cancel
    tui_stub._cancel_execution.assert_called_once()


def test_prompting_backspace_pops_buffer(tui_stub) -> None:
    """Backspace removes the last char from input_buffer."""
    tui_stub.execution_state = "prompting"
    tui_stub.input_buffer = "abc"  # Initial buffer
    dt = KeyboardDispatchTable(tui_stub)
    dt.dispatch("\x7f")  # Unicode DEL
    assert tui_stub.input_buffer == "ab"
    dt.dispatch("backspace")  # Alias
    assert tui_stub.input_buffer == "a"
    dt.dispatch("\x08")  # Backspace alias
    assert tui_stub.input_buffer == ""
    dt.dispatch("backspace")  # Empty -> no-op
    assert tui_stub.input_buffer == ""


def test_prompting_printable_char_appends(tui_stub) -> None:
    """Printable characters append to input_buffer."""
    tui_stub.execution_state = "prompting"
    tui_stub.input_buffer = ""
    dt = KeyboardDispatchTable(tui_stub)
    for ch in "xyz":  # Type three chars
        dt.dispatch(ch)
    assert tui_stub.input_buffer == "xyz"  # All three captured


def test_prompting_multichar_unknown_dropped(tui_stub) -> None:
    """A multi-char unhandled key in prompt mode is dropped (not appended)."""
    tui_stub.execution_state = "prompting"
    tui_stub.input_buffer = "k"
    KeyboardDispatchTable(tui_stub).dispatch("noise")  # Multi-char -> dropped
    assert tui_stub.input_buffer == "k"  # Unchanged


# --- navigation mode ---------------------------------------------------------


@pytest.mark.parametrize(
    ("starting", "key", "expected"),
    [
        (0, "up", 0),  # Up clamped at top
        (1, "up", 0),  # Up moves -1
        (0, "down", 1),  # Down moves +1
        (2, "down", 2),  # Down clamped at end
    ],
)
def test_nav_up_down_clamping(tui_stub, make_item, starting: int, key: str, expected: int) -> None:
    """Up/down arrows clamp at the top/bottom of current_items."""
    tui_stub.current_items = [make_item("module", f"m{i}") for i in range(3)]  # 3 items
    tui_stub.current_selection = starting
    KeyboardDispatchTable(tui_stub).dispatch(key)  # Trigger
    assert tui_stub.current_selection == expected


def test_nav_enter_module_drills_in(tui_stub, make_item) -> None:
    """Enter on a module pushes to current_path and refreshes items."""
    tui_stub.current_items = [make_item("module", "orgs")]  # Single module
    tui_stub.current_selection = 0
    KeyboardDispatchTable(tui_stub).dispatch("\r")  # Enter
    assert tui_stub.current_path == ["orgs"]  # Path pushed
    tui_stub._discover_current_level.assert_called_once()  # Refreshed


def test_nav_enter_function_starts_execution(tui_stub, make_item) -> None:
    """Enter on a function starts execution via the function-executor collaborator."""
    tui_stub.current_items = [make_item("function", "list", object=lambda: None)]
    tui_stub.current_selection = 0
    KeyboardDispatchTable(tui_stub).dispatch("\r")
    tui_stub._function_executor.start.assert_called_once()


def test_nav_back_pops_path(tui_stub) -> None:
    """Escape at non-root pops the deepest path segment and re-discovers."""
    tui_stub.current_path = ["a", "b"]  # Two levels deep
    KeyboardDispatchTable(tui_stub).dispatch("escape")  # Back
    assert tui_stub.current_path == ["a"]  # Pop b
    tui_stub._discover_current_level.assert_called_once()  # Refreshed


def test_nav_back_at_root_quits(tui_stub) -> None:
    """Escape at root sets running = False (graceful quit)."""
    tui_stub.current_path = []  # Already at root
    KeyboardDispatchTable(tui_stub).dispatch("escape")  # Quit
    assert tui_stub.running is False


def test_nav_enter_does_nothing_on_invalid_selection(tui_stub) -> None:
    """Enter with selection out of range is a no-op."""
    tui_stub.current_items = []  # Nothing selectable
    tui_stub.current_selection = 5  # Out of bounds
    KeyboardDispatchTable(tui_stub).dispatch("\r")  # No-op
    tui_stub._discover_current_level.assert_not_called()


def test_drill_into_empty_module_name_is_noop(tui_stub) -> None:
    """An item with no name doesn't push to current_path."""
    dt = KeyboardDispatchTable(tui_stub)
    dt._drill_into_module(None)  # Direct call
    assert tui_stub.current_path == []
