"""Unit tests for src/ui/layout/layout_builder.py."""

from __future__ import annotations

from typing import Any

import pytest
from rich.console import Console

from src.ui.layout.layout_builder import (
    _HELP_TEXT_TABLE,
    FIXED_PANEL_HEIGHT,
    OUTPUT_PANEL_HEIGHT,
    LayoutBuilder,
)


def _render(panel: Any) -> str:
    """Render a Rich Panel into plain text for substring assertions."""
    console = Console(width=120, record=True, force_terminal=False)  # Recording console
    console.print(panel)  # Render into capture buffer
    return console.export_text()


def test_build_returns_main_panel_in_navigation_state(tui_stub, make_item) -> None:
    """Default state returns the main panel (not the results overlay)."""
    tui_stub.current_items = [make_item("module", "orgs"), make_item("function", "listOrgs")]
    panel = LayoutBuilder(tui_stub).build()  # Build top-level
    text = _render(panel)  # Render for inspection
    assert "MistHelper TUI" in text  # Outer title rendered
    assert "Navigation" in text  # Nav-mode help present


def test_build_returns_results_overlay_when_grid_available(tui_stub) -> None:
    """In viewing_results state, an available grid replaces the main panel."""
    tui_stub.execution_state = "viewing_results"  # Switch mode
    tui_stub._results_grid_builder.build.return_value = tui_stub.Panel("grid contents", title="Grid")  # Real Panel ok
    layout = LayoutBuilder(tui_stub).build()  # Build
    # Rich Layout objects expose .renderable, not a Panel:
    assert layout.__class__.__name__ == "Layout"  # Outer Layout returned


def test_build_falls_back_when_results_builder_returns_none(tui_stub) -> None:
    """If the results builder returns None, the main panel is rendered."""
    tui_stub.execution_state = "viewing_results"  # Switch mode
    tui_stub._results_grid_builder.build.return_value = None  # No data -> fallback
    panel = LayoutBuilder(tui_stub).build()  # Build
    assert panel.__class__.__name__ == "Panel"  # Main panel returned


def test_breadcrumb_includes_current_path(tui_stub, make_item) -> None:
    """Current path segments appear in the breadcrumb panel."""
    tui_stub.current_path = ["orgs", "sites"]  # Two levels deep
    tui_stub.current_items = [make_item("module", "alpha")]
    panel = LayoutBuilder(tui_stub).build()
    assert "orgs" in _render(panel) and "sites" in _render(panel)  # Both path crumbs


def test_compute_column_width_respects_min(tui_stub, make_item) -> None:
    """Column width is at least 35 even for very short item names."""
    tui_stub.current_items = [make_item("module", "x")]  # 1-char names
    width = LayoutBuilder(tui_stub)._compute_column_width()
    assert width >= 35  # Floor enforced


def test_compute_viewport_no_scroll_needed(tui_stub, make_item) -> None:
    """If total items fit in the panel, the viewport is [0, total]."""
    tui_stub.current_items = [make_item("function", f"f{i}") for i in range(5)]  # 5 items
    start, end = LayoutBuilder(tui_stub)._compute_viewport()
    assert (start, end) == (0, 5)  # Whole list visible


def test_compute_viewport_scrolls_to_keep_selection_centered(tui_stub, make_item) -> None:
    """When list overflows, viewport recenters around the current selection."""
    tui_stub.current_items = [make_item("function", f"f{i}") for i in range(60)]  # Larger than panel
    tui_stub.current_selection = 30  # Mid-list
    start, end = LayoutBuilder(tui_stub)._compute_viewport()
    assert start <= 30 < end  # Selection inside window


def test_compute_viewport_snaps_at_bottom(tui_stub, make_item) -> None:
    """When near the bottom, viewport snaps so end matches total."""
    tui_stub.current_items = [make_item("function", f"f{i}") for i in range(60)]
    tui_stub.current_selection = 59  # Last item
    start, end = LayoutBuilder(tui_stub)._compute_viewport()
    assert end == 60  # Snapped to total


@pytest.mark.parametrize(
    ("item_type", "expected_icon"),
    [
        ("module", ">"),  # Module icon
        ("function", "*"),  # Function icon
        ("error", "x"),  # Error icon
        ("empty", "-"),  # Fallback icon
        ("unknown", "-"),  # Fallback icon
    ],
)
def test_icon_for_type_dispatch(item_type: str, expected_icon: str) -> None:
    """Icon dispatch returns expected (icon, color) tuple per type."""
    icon, _color = LayoutBuilder._icon_for_type(item_type)  # Static dispatch
    assert icon == expected_icon  # Icon matches


def test_format_item_row_highlights_selected(tui_stub, make_item) -> None:
    """Selected row uses 'bold bright_yellow' styling and # marker."""
    tui_stub.current_items = [make_item("module", "orgs"), make_item("function", "listOrgs")]
    tui_stub.current_selection = 1  # Second item selected
    builder = LayoutBuilder(tui_stub)
    row_selected = builder._format_item_row(1)  # Selected row
    row_other = builder._format_item_row(0)  # Non-selected row
    assert "bold bright_yellow" in row_selected and row_selected.startswith("[bold bright_yellow]#")
    assert "bright_cyan" in row_other  # Module color


def test_function_details_panel_includes_signature_and_doc(tui_stub, make_item) -> None:
    """Function selection populates Signature + Documentation sections."""
    tui_stub.current_items = [
        make_item("function", "listOrgs", signature="(self, org_id)", full_doc="Get all orgs.\nWith details.")
    ]
    panel = LayoutBuilder(tui_stub)._build_details_panel()
    text = _render(panel)
    assert "Signature:" in text and "listOrgs(self, org_id)" in text
    assert "Documentation:" in text and "Get all orgs" in text


def test_module_details_panel_includes_explore_hint(tui_stub, make_item) -> None:
    """Module selection shows the 'Press Enter to explore' message."""
    tui_stub.current_items = [make_item("module", "orgs")]
    panel = LayoutBuilder(tui_stub)._build_details_panel()
    assert "Press Enter to explore" in _render(panel)


def test_error_details_panel_shows_description(tui_stub, make_item) -> None:
    """Error selection shows the description text."""
    tui_stub.current_items = [make_item("error", "Import Error", description="Module missing")]
    panel = LayoutBuilder(tui_stub)._build_details_panel()
    assert "Module missing" in _render(panel)


def test_details_panel_shows_last_result_preview(tui_stub) -> None:
    """When last_result is set, a preview is included in details."""
    tui_stub.last_result = "tiny result"  # Below 300-char cap
    panel = LayoutBuilder(tui_stub)._build_details_panel()
    assert "Last Result" in _render(panel)


def test_details_panel_truncates_long_last_result(tui_stub) -> None:
    """A long last_result is truncated to ≤300 chars."""
    tui_stub.last_result = "x" * 1000  # Over the 300-char cap
    panel = LayoutBuilder(tui_stub)._build_details_panel()
    text = _render(panel)
    assert "..." in text  # Truncation marker


def test_details_panel_shows_last_error(tui_stub) -> None:
    """When last_error is set, the error is rendered."""
    tui_stub.last_error = "API failed"  # Set error
    panel = LayoutBuilder(tui_stub)._build_details_panel()
    assert "API failed" in _render(panel)


def test_details_panel_truncates_overflow(tui_stub) -> None:
    """Detail body lines beyond panel capacity get a 'content truncated' notice."""
    tui_stub.current_items = [
        {
            "type": "function",
            "name": "x",
            "signature": "(...)",
            "full_doc": "\n".join(f"line {i}" for i in range(50)),  # 50 lines forces truncation
            "description": "x",
        }
    ]
    tui_stub.last_result = "y" * 100  # Force overflow
    # Inspect raw lines (avoids Rich panel-height truncation hiding the marker):
    lines = LayoutBuilder(tui_stub)._collect_detail_lines()
    LayoutBuilder._truncate_to_panel(lines)  # Run the truncation step
    assert any("content truncated" in line for line in lines)  # Marker appended


def test_output_panel_executing_state(tui_stub) -> None:
    """'executing' state shows the 'Executing API Call...' message."""
    tui_stub.execution_state = "executing"
    panel = LayoutBuilder(tui_stub)._build_output_panel()
    assert "Executing API Call" in _render(panel)


def test_output_panel_renders_output_lines(tui_stub) -> None:
    """Saved output_lines render in the output panel."""
    tui_stub.output_lines = ["[SUCCESS] foo completed"]
    panel = LayoutBuilder(tui_stub)._build_output_panel()
    assert "SUCCESS" in _render(panel)


def test_output_panel_default_when_empty(tui_stub) -> None:
    """Empty output_lines render the placeholder text."""
    tui_stub.output_lines = []  # No prior output
    panel = LayoutBuilder(tui_stub)._build_output_panel()
    assert "Output will appear here" in _render(panel)


def test_output_panel_prompting_state(tui_stub) -> None:
    """'prompting' state shows the current param + history headers."""
    tui_stub.execution_state = "prompting"
    tui_stub.current_function = {"name": "listOrgs"}
    tui_stub.param_list = [
        {"name": "org_id", "has_default": False},
        {"name": "limit", "has_default": True, "default": 100},
    ]
    tui_stub.current_param_index = 1  # Already entered org_id
    tui_stub.function_params = {"org_id": "abc"}
    tui_stub.input_buffer = "5"
    # Inspect raw lines (panel height squashes Rich output of long prompt blocks):
    lines = LayoutBuilder(tui_stub)._collect_output_lines()
    text = "\n".join(lines)  # Joined raw body
    assert "limit" in text  # Current parameter shown
    assert "Already provided" in text  # History header shown
    assert "org_id" in text  # Previously-collected param surfaced


def test_redact_value_masks_secret_names() -> None:
    """Secret-shaped names are masked in the param history block."""
    assert LayoutBuilder._redact_value("api_token", "abc") == "***REDACTED***"
    assert LayoutBuilder._redact_value("org_id", "abc") == "abc"


def test_redact_value_truncates_long_values() -> None:
    """Non-secret values longer than 40 chars are truncated to 40."""
    long_val = "y" * 100  # 100-char value
    assert len(LayoutBuilder._redact_value("normal", long_val)) == 40


def test_help_text_table_has_all_modes() -> None:
    """The help-text dispatch dict covers every documented mode."""
    assert "navigation" in _HELP_TEXT_TABLE  # Required default
    assert "viewing_results" in _HELP_TEXT_TABLE  # Grid mode
    assert "prompting" in _HELP_TEXT_TABLE  # Param mode


def test_help_text_unknown_state_falls_back_to_navigation(tui_stub) -> None:
    """Unknown execution_state falls back to the navigation help string."""
    tui_stub.execution_state = "nonsense"  # Not in table
    assert LayoutBuilder(tui_stub)._build_help_text() == _HELP_TEXT_TABLE["navigation"]


def test_fixed_panel_height_constant_sane() -> None:
    """The exported height constants must be positive and OUTPUT < FIXED."""
    assert FIXED_PANEL_HEIGHT > 0  # Positive height
    assert OUTPUT_PANEL_HEIGHT > 0 and OUTPUT_PANEL_HEIGHT < FIXED_PANEL_HEIGHT  # Output smaller
