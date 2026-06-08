"""Construct the main TUI layout (Panels + Table.grid).

Replaces ``MistHelperTUI.create_layout`` (CC=52) by decomposing each visual
region into its own focused helper, all CC <= 10.
"""

from __future__ import annotations

import logging
import shutil
from typing import Any

FIXED_PANEL_HEIGHT = 20  # Stable rendering height
OUTPUT_PANEL_HEIGHT = 8  # Reserved height for output panel
LEFT_PANEL_PCT = 0.40  # Left column width % of terminal


class LayoutBuilder:
    """Builds the composite Rich Panel that represents the TUI main screen."""

    def __init__(self, tui: Any) -> None:
        self._tui = tui  # Back-reference to shared TUI state

    def build(self) -> Any:
        """Return the top-level Rich renderable for the current TUI frame."""
        tui = self._tui  # Local alias
        logging.info("TUI: building layout (state=%s)", tui.execution_state)  # Action log before composition
        from rich.console import Group  # Lazy import — Rich is optional dep

        column_width = self._compute_column_width()  # Dynamic left-panel width
        panel_width = column_width + 4  # Add border + padding overhead
        items_panel = self._build_items_panel(column_width, panel_width)  # Left column (items list)
        details_panel = self._build_details_panel()  # Right column (details)
        output_panel = self._build_output_panel()  # Bottom output panel
        breadcrumb_panel = self._build_breadcrumb_panel()  # Top breadcrumb
        help_text = self._build_help_text()  # Footer help line
        layout_table = self._build_side_by_side(panel_width, items_panel, details_panel)
        content_group = Group(breadcrumb_panel, "", layout_table, "", output_panel, "", help_text)
        main_panel = tui.Panel(  # Wrap everything in outer Panel
            content_group,
            title="[bold bright_cyan]MistHelper TUI[/bold bright_cyan]",
            border_style="bright_blue",
            box=tui.box.ROUNDED,
        )
        logging.debug("TUI: layout build complete")  # Action log after composition
        if tui.execution_state == "viewing_results":  # Results-grid overlay path
            results_layout = self._maybe_wrap_results_grid()
            if results_layout is not None:
                return results_layout
        return main_panel

    # ---- top breadcrumb --------------------------------------------------

    def _build_breadcrumb_panel(self) -> Any:
        """Build the top breadcrumb panel showing the current API path."""
        tui = self._tui  # Local alias
        breadcrumb_text = f"[bold bright_cyan]{tui.breadcrumb}[/bold bright_cyan]"
        if tui.current_path:  # Append "-> a -> b -> c" suffix
            path_display = " -> ".join(tui.current_path)
            breadcrumb_text += f" [dim bright_black]-> {path_display}[/dim bright_black]"
        return tui.Panel(
            breadcrumb_text,
            style="bright_white on grey11",
            border_style="bright_cyan",
            box=tui.box.ROUNDED,
        )

    # ---- left items column ----------------------------------------------

    def _compute_column_width(self) -> int:
        """Choose left-panel inner width based on terminal width + content size."""
        tui = self._tui  # Local alias
        max_name_length = max((len(item.get("name", "")) for item in tui.current_items), default=10)
        terminal_width, _ = shutil.get_terminal_size()  # Detect terminal columns
        percentage_width = int(terminal_width * LEFT_PANEL_PCT)  # 40% of terminal width
        content_width_needed = max_name_length + 10  # Reserve room for icon/prefix/padding
        return max(35, min(content_width_needed, percentage_width))  # Bounded by min 35 and pct cap

    def _build_items_panel(self, column_width: int, panel_width: int) -> Any:
        """Build the left-column Rich Panel containing the scrolling items list."""
        tui = self._tui  # Local alias
        items_table = tui.Table(show_header=False, box=tui.box.ROUNDED, padding=(0, 1))
        items_table.add_column("Item", style="white", width=column_width, no_wrap=False, overflow="ellipsis")
        viewport_start, viewport_end = self._compute_viewport()  # Slice indices for visible items
        for idx in range(viewport_start, viewport_end):  # Render each visible row
            items_table.add_row(self._format_item_row(idx))
        level_name = tui.current_path[-1] if tui.current_path else "root"  # Show level name in panel title
        return tui.Panel(
            items_table,
            title=f"[bold bright_cyan]{level_name}[/bold bright_cyan]",
            border_style="bright_cyan",
            height=FIXED_PANEL_HEIGHT,
            width=panel_width,
        )

    def _compute_viewport(self) -> tuple[int, int]:
        """Return [start, end) item indices to render so selection stays visible."""
        tui = self._tui  # Local alias
        total_items = len(tui.current_items)  # Total count of items
        viewport_height = FIXED_PANEL_HEIGHT - 2  # Reserve 2 rows for panel borders
        if total_items <= viewport_height:  # All items fit -> no scrolling
            return 0, total_items
        viewport_start = max(0, tui.current_selection - viewport_height // 2)  # Center selection in viewport
        viewport_end = min(total_items, viewport_start + viewport_height)  # Clamp end at total
        if viewport_end == total_items:  # If at bottom, snap start backward
            viewport_start = max(0, total_items - viewport_height)
        return viewport_start, viewport_end

    def _format_item_row(self, idx: int) -> str:
        """Format a single items-list row with icon, prefix and color."""
        tui = self._tui  # Local alias
        item = tui.current_items[idx]  # Item dict (type/name/...)
        item_type = item.get("type", "unknown")  # Module/function/error/empty
        item_name = item.get("name", "unknown")  # Display name
        icon, color = self._icon_for_type(item_type)  # Icon + base color
        if idx == tui.current_selection:  # Highlighted selection row
            return f"[bold bright_yellow]# {icon} {item_name}[/bold bright_yellow]"
        return f"[{color}]  {icon} {item_name}[/{color}]"  # Non-selected row

    @staticmethod
    def _icon_for_type(item_type: str) -> tuple[str, str]:
        """Map an item ``type`` string to its (icon, color) pair (CC=1 dispatch)."""
        return {  # Inline dispatch dict
            "module": (">", "bright_cyan"),
            "function": ("*", "bright_green"),
            "error": ("x", "bright_red"),
        }.get(
            item_type, ("-", "dim")
        )  # Fallback for empty/unknown

    # ---- right details column -------------------------------------------

    def _build_details_panel(self) -> Any:
        """Build the right-column Details panel for the selected item."""
        tui = self._tui  # Local alias
        details_lines = self._collect_detail_lines()  # Build all body lines first
        self._truncate_to_panel(details_lines)  # Truncate to panel height
        return tui.Panel(
            "\n".join(details_lines),
            title="[bold bright_green]Details[/bold bright_green]",
            border_style="bright_green",
            box=tui.box.ROUNDED,
            height=FIXED_PANEL_HEIGHT,
        )

    def _collect_detail_lines(self) -> list[str]:
        """Assemble the list of detail body lines for the current selection."""
        lines: list[str] = []  # Accumulator
        self._append_selection_details(lines)  # Function/module/error info
        self._append_last_result(lines)  # Optional last-result preview
        self._append_last_error(lines)  # Optional last-error preview
        if not lines:  # Fallback prompt when empty
            lines.append("[dim]Select an item to view details[/dim]")
        return lines

    def _append_selection_details(self, lines: list[str]) -> None:
        """Append selection-specific detail lines based on item type (CC <= 6)."""
        tui = self._tui  # Local alias
        if not 0 <= tui.current_selection < len(tui.current_items):  # Guard: no valid selection
            return
        selected = tui.current_items[tui.current_selection]  # Snapshot the selection
        item_type = selected.get("type")  # Dispatch on type
        if item_type == "function":
            self._append_function_details(lines, selected)
        elif item_type == "module":
            lines.append(f"[bold bright_cyan]Module:[/bold bright_cyan] {selected.get('name', 'unknown')}")
            lines.append("")
            lines.append("[dim bright_black]Press Enter to explore this module[/dim bright_black]")
        elif item_type == "error":
            lines.append("[bold red]Error:[/bold red]")
            lines.append(selected.get("description", "Unknown error"))

    @staticmethod
    def _append_function_details(lines: list[str], selected: dict[str, Any]) -> None:
        """Append detail lines describing a function selection (signature + doc)."""
        func_name = selected.get("name", "unknown")  # Name for headings
        signature = selected.get("signature", "(...)")  # Pre-formatted signature
        full_doc = selected.get("full_doc", "No documentation available")  # Full docstring text
        lines.append(f"[bold bright_green]Function:[/bold bright_green] {func_name}")
        lines.append("")
        lines.append("[bold bright_cyan]Signature:[/bold bright_cyan]")
        lines.append(f"[bright_yellow]{func_name}{signature}[/bright_yellow]")
        lines.append("")
        lines.append("[bold]Documentation:[/bold]")
        doc_lines = full_doc.split("\n")  # Split docstring for truncation
        max_doc_lines = max(5, FIXED_PANEL_HEIGHT - 10)  # Reserve room for headings
        lines.extend(doc_lines[:max_doc_lines])
        if len(doc_lines) > max_doc_lines:  # Indicate truncation
            lines.append(f"[dim]...(truncated, {len(doc_lines) - max_doc_lines} more lines)[/dim]")

    def _append_last_result(self, lines: list[str]) -> None:
        """Append a short preview of ``self.last_result`` when present."""
        tui = self._tui  # Local alias
        if tui.last_result is None:  # Nothing to preview
            return
        lines.append("")
        lines.append("[bold green]Last Result:[/bold green]")
        result_preview = str(tui.last_result)  # Stringify the raw result
        if len(result_preview) > 300:  # Char-cap to avoid overflow
            result_preview = result_preview[:300] + "..."
        result_lines = result_preview.split("\n")[:10]  # Line-cap to 10 lines
        lines.extend(f"[dim]{line}[/dim]" for line in result_lines)

    def _append_last_error(self, lines: list[str]) -> None:
        """Append a one-line preview of ``self.last_error`` when present."""
        tui = self._tui  # Local alias
        if not tui.last_error:  # Nothing to show
            return
        lines.append("")
        lines.append("[bold red]Last Error:[/bold red]")
        lines.append(f"[dim]{tui.last_error}[/dim]")

    @staticmethod
    def _truncate_to_panel(lines: list[str]) -> None:
        """Trim ``lines`` in-place so they fit in the details panel height."""
        max_total = FIXED_PANEL_HEIGHT - 2  # Reserve panel border rows
        if len(lines) > max_total:  # Need to truncate
            del lines[max_total:]  # Drop overflow
            lines.append("[dim]...(content truncated to fit screen)[/dim]")

    # ---- bottom output panel --------------------------------------------

    def _build_output_panel(self) -> Any:
        """Build the bottom Output panel showing exec status or prompts."""
        tui = self._tui  # Local alias
        content = self._collect_output_lines()  # State-specific content lines
        body = "\n".join(content) if content else "[dim]No output[/dim]"
        return tui.Panel(
            body,
            title="[bold bright_magenta]Output[/bold bright_magenta]",
            border_style="bright_magenta",
            box=tui.box.ROUNDED,
            height=OUTPUT_PANEL_HEIGHT,
        )

    def _collect_output_lines(self) -> list[str]:
        """Pick the appropriate output-panel content for the current state."""
        tui = self._tui  # Local alias
        if tui.execution_state == "prompting":  # Parameter-collection UI
            return self._build_prompt_lines()
        if tui.execution_state == "executing":  # Spinner-style status
            return [
                "[bold bright_cyan]Executing API Call...[/bold bright_cyan]",
                "",
                "[dim]Please wait...[/dim]",
            ]
        if tui.output_lines:  # Replay last execution output
            return list(tui.output_lines[-OUTPUT_PANEL_HEIGHT + 2 :])
        return ["[dim]Output will appear here after executing functions[/dim]"]

    def _build_prompt_lines(self) -> list[str]:
        """Build the prompting-mode output (header + current param + history)."""
        tui = self._tui  # Local alias
        lines: list[str] = [
            "[bold bright_cyan]=== Function Execution - Parameter Input ===[/bold bright_cyan]",
            "",
        ]
        if tui.current_function:  # Show function name when known
            lines.append(f"[bright_green]Function:[/bright_green] {tui.current_function.get('name', 'unknown')}")
        if tui.current_param_index < len(tui.param_list):  # Current parameter prompt
            self._append_current_param_prompt(lines)
        if tui.current_param_index > 0:  # History of provided params
            self._append_param_history(lines)
        return lines

    def _append_current_param_prompt(self, lines: list[str]) -> None:
        """Append the currently-being-asked parameter prompt to ``lines``."""
        tui = self._tui  # Local alias
        param_info = tui.param_list[tui.current_param_index]  # Current parameter dict
        param_name = param_info["name"]  # Parameter name to display
        required_tag = (  # Required vs optional tag
            "[red][REQUIRED][/red]" if not param_info.get("has_default") else "[dim][optional][/dim]"
        )
        default_info = (  # Inline default-value hint
            f" [dim](default: {param_info.get('default')})[/dim]" if param_info.get("has_default") else ""
        )
        lines.append("")
        lines.append(f"[bold bright_yellow]+-- Input Needed: {param_name} {required_tag}[/bold bright_yellow]")
        if default_info:  # Optional second line for default
            lines.append(f"[bright_yellow]|[/bright_yellow] {default_info}")
        lines.append(
            f"[bright_yellow]+-->[/bright_yellow] " f"[bold white on grey11]{tui.input_buffer}#[/bold white on grey11]"
        )

    def _append_param_history(self, lines: list[str]) -> None:
        """Append the 'Already provided' history block to ``lines``."""
        tui = self._tui  # Local alias
        lines.append("")
        lines.append(f"[dim]Already provided ({tui.current_param_index}/{len(tui.param_list)}):[/dim]")
        for idx in range(min(3, tui.current_param_index)):  # Show at most the last 3 entries
            param_info = tui.param_list[tui.current_param_index - 1 - idx]  # Walk backwards from current
            param_name = param_info["name"]  # Name for the OK line
            param_value = tui.function_params.get(param_name, "")  # Captured value (may be None)
            display_value = self._redact_value(param_name, param_value)  # Apply secret redaction
            lines.append(f"  [dim][OK] {param_name}:[/dim] {display_value}")

    @staticmethod
    def _redact_value(param_name: str, param_value: Any) -> str:
        """Return a display-safe parameter value, masking secret-like names."""
        sensitive = any(token in param_name.lower() for token in ("pass", "token", "key", "secret"))
        if sensitive:  # Mask secret-shaped names
            return "***REDACTED***"
        return str(param_value)[:40]  # Truncate long values

    # ---- footer help text -----------------------------------------------

    def _build_help_text(self) -> str:
        """Return the mode-specific footer help string."""
        state = self._tui.execution_state  # Read once
        return _HELP_TEXT_TABLE.get(state, _HELP_TEXT_TABLE["navigation"])  # Dispatch dict lookup

    # ---- side-by-side composition + results overlay ---------------------

    def _build_side_by_side(self, panel_width: int, items_panel: Any, details_panel: Any) -> Any:
        """Combine items and details into a two-column grid table."""
        from rich.table import Table as RichTable  # Local import — keeps top clean

        layout_table = RichTable.grid(padding=1, expand=True)
        layout_table.add_column(width=panel_width, no_wrap=True)  # Fixed-width left column
        layout_table.add_column(ratio=1)  # Right column fills the rest
        layout_table.add_row(items_panel, details_panel)  # Single composite row
        return layout_table

    def _maybe_wrap_results_grid(self) -> Any:
        """When in results-view state, replace the main panel with the grid."""
        tui = self._tui  # Local alias
        results_grid = tui._results_grid_builder.build()  # Delegate to grid collaborator
        if results_grid is None:  # No results to show -> stay on main
            return None
        results_layout = tui.Layout(minimum_size=0)  # Outer Rich Layout container
        results_layout.split_column(  # Two rows: results body + footer
            tui.Layout(results_grid, name="results", ratio=95, minimum_size=0),
            tui.Layout(
                tui.Panel(
                    _RESULTS_FOOTER_TEXT,
                    border_style="dim",
                    box=tui.box.SIMPLE,
                ),
                name="footer",
                size=3,
            ),
        )
        return results_layout


_HELP_TEXT_TABLE: dict[str | None, str] = {  # Mode -> help string dispatch
    "viewing_results": (
        "[bold bright_yellow]Results View:[/bold bright_yellow] "
        "[bright_cyan]Up/Dn[/bright_cyan] Scroll (10)  "
        "[bright_cyan]PgUp/PgDn[/bright_cyan] Scroll (20)  "
        "[bright_green]H[/bright_green] Top  "
        "[bright_green]E[/bright_green] End  "
        "[bright_magenta]Esc[/bright_magenta] Close  "
        "[bright_red]Q[/bright_red] Quit"
    ),
    "prompting": (
        "[bold bright_yellow]Input Mode:[/bold bright_yellow] "
        "[bright_green]Type[/bright_green] value  "
        "[bright_cyan]Enter[/bright_cyan] Submit  "
        "[bright_magenta]Esc[/bright_magenta] Cancel"
    ),
    "navigation": (
        "[bold bright_yellow]Navigation:[/bold bright_yellow] "
        "[bright_cyan]Up/Dn[/bright_cyan] Move  "
        "[bright_green]Enter[/bright_green] Drill/Execute  "
        "[bright_magenta]Esc[/bright_magenta] Back  "
        "[bright_red]Q[/bright_red] Quit"
    ),
}

_RESULTS_FOOTER_TEXT = (  # Footer text under the results grid
    "[yellow]Controls: [bright_yellow]L/R[/bright_yellow] Results | "
    "[bright_yellow]Up/Dn[/bright_yellow] Scroll (10) | "
    "[bright_yellow]PgUp/PgDn[/bright_yellow] Scroll (20) | "
    "[bright_yellow]H[/bright_yellow] Top | "
    "[bright_yellow]E[/bright_yellow] End | "
    "[bright_yellow]ESC[/bright_yellow] Close | "
    "[bright_yellow]Q[/bright_yellow] Quit[/yellow]"
)
