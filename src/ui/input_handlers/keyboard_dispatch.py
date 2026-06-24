"""Dispatch-table-based replacement for ``MistHelperTUI.handle_input`` (CC=65).

Three mode-scoped dispatch tables (results-view / prompting / navigation) replace
the long if/elif chain in the original method. Each handler is a small bound
method on this class with CC <= 10. Tables are built once in ``__init__``
(performance constraint from the spec).
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any


class KeyboardDispatchTable:
    """Routes a key press to the correct handler based on TUI execution state."""

    def __init__(self, tui: Any) -> None:
        """Store TUI back-reference and pre-build the mode-specific handler tables once."""
        self._tui = tui  # Back-reference for shared TUI state
        # Build mode tables once at __init__ — no per-call rebuild (perf rule)
        self._results_handlers: dict[str, Callable[[], None]] = self._build_results_table()
        self._prompt_handlers: dict[str, Callable[[], None]] = self._build_prompt_table()
        self._nav_handlers: dict[str, Callable[[], None]] = self._build_nav_table()

    # ---- public entry point ----------------------------------------------

    def dispatch(self, key: str) -> None:
        """Route ``key`` to the handler appropriate for the current TUI state."""
        tui = self._tui  # Local alias for readability
        if tui.debug_mode:  # Trace key + state for debugging
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            logging.debug(
                "TUI_DEBUG: [%s] Key pressed: %r (state=%s, path=%s, selection=%s)",
                ts,
                key,
                tui.execution_state,
                tui.current_path,
                tui.current_selection,
            )
        if tui.execution_state == "viewing_results":  # Results-grid mode dispatch
            return self._dispatch_with(self._results_handlers, key, "viewing_results")
        if tui.execution_state == "prompting":  # Parameter prompt mode dispatch
            return self._dispatch_prompting(key)  # Special: needs printable-char fallback
        return self._dispatch_with(self._nav_handlers, key, "navigation")  # Default navigation dispatch

    # ---- shared helpers --------------------------------------------------

    def _dispatch_with(self, table: dict[str, Callable[[], None]], key: str, mode: str) -> None:
        """Invoke ``table[key]`` if present; otherwise debug-log the unhandled key."""
        handler = table.get(key)  # O(1) dispatch lookup
        if handler is None:  # Unknown key for this mode
            if self._tui.debug_mode:
                logging.debug("TUI_DEBUG: Unhandled key in %s mode: %r", mode, key)
            return
        logging.info("TUI: dispatching key %s in %s mode", key, mode)  # Action log: before handler
        handler()  # Run bound handler
        logging.debug("TUI: dispatched key %s in %s mode", key, mode)  # Action log: after handler

    # ---- dispatch table builders ----------------------------------------

    def _build_results_table(self) -> dict[str, Callable[[], None]]:
        """Build the {key: handler} table for ``execution_state == 'viewing_results'``."""
        return {  # Each value is a 1-line bound method
            "left": self._results_prev,
            "right": self._results_next,
            "up": self._results_row_up,
            "down": self._results_row_down,
            "page_up": self._results_page_up,
            "page_down": self._results_page_down,
            "h": self._results_jump_top,
            "e": self._results_jump_end,
            "escape": self._results_close,
            "\x1b": self._results_close,
            "q": self._set_quit,
        }

    def _build_prompt_table(self) -> dict[str, Callable[[], None]]:
        """Build the {key: handler} table for ``execution_state == 'prompting'``."""
        return {  # Printable-char fallback separately
            "\r": self._prompt_submit,
            "\n": self._prompt_submit,
            "escape": self._tui._cancel_execution,
            "\x1b": self._tui._cancel_execution,
            "\x7f": self._prompt_backspace,
            "\x08": self._prompt_backspace,
            "backspace": self._prompt_backspace,
        }

    def _build_nav_table(self) -> dict[str, Callable[[], None]]:
        """Build the {key: handler} table for navigation mode (no execution state)."""
        return {
            "up": self._nav_up,
            "down": self._nav_down,
            "\r": self._nav_enter,
            "\n": self._nav_enter,
            "escape": self._nav_back,
            "\x1b": self._nav_back,
            "q": self._set_quit,
        }

    # ---- results-view handlers (CC <= 2 each) ---------------------------

    def _results_prev(self) -> None:
        """Move scroll offset back to the previous result."""
        tui = self._tui  # Local alias
        tui.results_scroll_offset = max(0, tui.results_scroll_offset - 1)  # Clamp at zero
        tui.result_row_scroll = 0  # Reset row scroll on result change

    def _results_next(self) -> None:
        """Advance scroll offset to the next result, clamped at last index."""
        tui = self._tui  # Local alias
        results = self._safe_results()  # Defensive list access
        max_offset = max(0, len(results) - 1)  # Last valid index
        tui.results_scroll_offset = min(max_offset, tui.results_scroll_offset + 1)
        tui.result_row_scroll = 0  # Reset row scroll on result change

    def _results_row_up(self) -> None:
        """Scroll up 10 rows within the current result."""
        self._tui.result_row_scroll = max(0, self._tui.result_row_scroll - 10)

    def _results_row_down(self) -> None:
        """Scroll down 10 rows; ResultsGridBuilder clamps the upper bound."""
        self._tui.result_row_scroll += 10  # Builder handles bounds

    def _results_page_up(self) -> None:
        """Page up by 20 rows (2x arrow speed)."""
        self._tui.result_row_scroll = max(0, self._tui.result_row_scroll - 20)

    def _results_page_down(self) -> None:
        """Page down by 20 rows (2x arrow speed)."""
        self._tui.result_row_scroll += 20  # Builder handles bounds

    def _results_jump_top(self) -> None:
        """Jump to the top row of the current result."""
        self._tui.result_row_scroll = 0

    def _results_jump_end(self) -> None:
        """Jump to the end of the current result (builder caps the value)."""
        if self._safe_results():  # Only jump if there is data
            self._tui.result_row_scroll = 999999  # Sentinel; builder clamps

    def _results_close(self) -> None:
        """Exit the results-view state and return to navigation."""
        self._tui.execution_state = None
        self._tui.results_scroll_offset = 0
        self._tui.result_row_scroll = 0

    def _safe_results(self) -> list[Any]:
        """Return the parsed results list, or an empty list when unavailable."""
        parsed = self._tui.last_parsed_data  # Snapshot the current parsed payload
        if not isinstance(parsed, dict):  # Guard: missing or non-dict
            return []
        results = parsed.get("results")  # Pull the results array
        return results if isinstance(results, list) else []  # Guard: non-list

    # ---- prompting-mode handlers ----------------------------------------

    def _dispatch_prompting(self, key: str) -> None:
        """Prompt mode needs a printable-character fallback after the dict."""
        handler = self._prompt_handlers.get(key)  # Try the table first
        if handler is not None:  # Known control key
            logging.info("TUI: prompting dispatch %r", key)
            handler()
            return
        if len(key) == 1 and key.isprintable():  # Otherwise append printable char
            self._tui.input_buffer += key

    def _prompt_submit(self) -> None:
        """Delegate Enter-key submission to the parameter collector."""
        self._tui._submit_parameter()  # Existing collector path

    def _prompt_backspace(self) -> None:
        """Remove the last character from the input buffer."""
        if self._tui.input_buffer:  # Guard against empty buffer
            self._tui.input_buffer = self._tui.input_buffer[:-1]

    # ---- navigation handlers --------------------------------------------

    def _nav_up(self) -> None:
        """Move the selection cursor up by one item, clamped at zero."""
        tui = self._tui  # Local alias
        tui.current_selection = max(0, tui.current_selection - 1)  # Clamp at top

    def _nav_down(self) -> None:
        """Move the selection cursor down by one item, clamped at end."""
        tui = self._tui  # Local alias
        last_index = max(0, len(tui.current_items) - 1)  # Last valid index (or 0 if empty)
        tui.current_selection = min(last_index, tui.current_selection + 1)

    def _nav_enter(self) -> None:
        """Drill into a module or start execution of the selected function."""
        tui = self._tui  # Local alias
        if not 0 <= tui.current_selection < len(tui.current_items):  # Guard: selection out of range
            return
        selected = tui.current_items[tui.current_selection]  # Snapshot the item
        item_type = selected.get("type")  # Module vs function vs other
        if item_type == "module":
            self._drill_into_module(selected.get("name"))  # Push the module onto the path
        elif item_type == "function":
            tui._start_function_execution(selected)  # Begin parameter prompting

    def _drill_into_module(self, module_name: str | None) -> None:
        """Push ``module_name`` onto the current path and re-discover items."""
        if not module_name:  # Guard: empty/missing name
            return
        tui = self._tui  # Local alias
        tui.current_path.append(module_name)  # Descend one level
        tui.current_selection = 0  # Reset selection at new level
        tui._discover_current_level()  # Refresh current_items
        logging.info("TUI: Navigated into module: %s", module_name)

    def _nav_back(self) -> None:
        """Escape: pop one level off the path; quit when already at root."""
        tui = self._tui  # Local alias
        if not tui.current_path:  # Already at root -> escape quits
            tui.running = False
            return
        removed = tui.current_path.pop()  # Pop the deepest segment
        tui.current_selection = 0  # Reset selection at parent level
        tui._discover_current_level()  # Refresh current_items
        logging.info("TUI: Navigated back from: %s", removed)

    def _set_quit(self) -> None:
        """Set the TUI running flag to ``False`` (graceful exit)."""
        self._tui.running = False
