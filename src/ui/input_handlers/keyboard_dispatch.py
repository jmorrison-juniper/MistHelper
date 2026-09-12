"""Dispatch-table-based replacement for ``MistHelperTUI.handle_input`` (CC=65).

Three mode-scoped dispatch tables (results-view / prompting / navigation) replace
the long if/elif chain in the original method. Each handler is a small bound
method on this class with CC <= 10. Tables are built once in ``__init__``
(performance constraint from the spec).
"""

from __future__ import annotations  # WHY: PEP 604 union syntax + forward refs

import logging  # WHY: action-log every dispatched key + mode transition
from collections.abc import Callable  # WHY: precise type for zero-arg handler tables
from datetime import datetime  # WHY: high-resolution timestamp for debug traces
from typing import Any  # WHY: TUI back-reference is loosely typed


class KeyboardDispatchTable:  # WHY: replaces handle_input (was CC=65) with O(1) tables
    """Routes a key press to the correct handler based on TUI execution state."""

    def __init__(self, tui: Any) -> None:  # WHY: bind TUI + build tables once at construction
        """Store TUI back-reference and pre-build the mode-specific handler tables once."""
        self._tui = tui  # Back-reference for shared TUI state
        # Build mode tables once at __init__ — no per-call rebuild (perf rule)
        self._results_handlers: dict[str, Callable[[], None]] = self._build_results_table()  # WHY: results-view keys
        self._prompt_handlers: dict[str, Callable[[], None]] = self._build_prompt_table()  # WHY: parameter-prompt keys
        self._nav_handlers: dict[str, Callable[[], None]] = self._build_nav_table()  # WHY: navigation-mode keys

    # ---- public entry point ----------------------------------------------

    def dispatch(self, key: str) -> None:  # WHY: single entry point selects the mode-specific table
        """Route ``key`` to the handler appropriate for the current TUI state."""
        tui = self._tui  # Local alias for readability
        if tui.debug_mode:  # Trace key + state for debugging
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # WHY: ms-precision for keystroke ordering
            logging.debug(  # WHY: emit structured trace so we can reconstruct user's key sequence
                "TUI_DEBUG: [%s] Key pressed: %r (state=%s, path=%s, selection=%s)",
                ts,
                key,
                tui.execution_state,
                tui.current_path,
                tui.current_selection,
            )
        if tui.execution_state == "viewing_results":  # Results-grid mode dispatch
            return self._dispatch_with(self._results_handlers, key, "viewing_results")  # WHY: results table branch
        if tui.execution_state == "prompting":  # Parameter prompt mode dispatch
            return self._dispatch_prompting(key)  # Special: needs printable-char fallback
        return self._dispatch_with(self._nav_handlers, key, "navigation")  # Default navigation dispatch

    # ---- shared helpers --------------------------------------------------

    def _dispatch_with(self, table: dict[str, Callable[[], None]], key: str, mode: str) -> None:  # WHY: shared O(1)
        """Invoke ``table[key]`` if present. Otherwise debug-log the unhandled key."""
        handler = table.get(key)  # O(1) dispatch lookup
        if handler is None:  # Unknown key for this mode
            if self._tui.debug_mode:  # WHY: only trace unhandled keys in debug mode
                logging.debug("TUI_DEBUG: Unhandled key in %s mode: %r", mode, key)  # WHY: capture no-op keystroke
            return  # WHY: nothing to run, exit early
        logging.info("TUI: dispatching key %s in %s mode", key, mode)  # Action log: before handler
        handler()  # Run bound handler
        logging.debug("TUI: dispatched key %s in %s mode", key, mode)  # Action log: after handler

    # ---- dispatch table builders ----------------------------------------

    def _build_results_table(self) -> dict[str, Callable[[], None]]:  # WHY: built once — no per-call rebuild
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

    def _build_prompt_table(self) -> dict[str, Callable[[], None]]:  # WHY: built once — no per-call rebuild
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

    def _build_nav_table(self) -> dict[str, Callable[[], None]]:  # WHY: built once — no per-call rebuild
        """Build the {key: handler} table for navigation mode (no execution state)."""
        return {  # Standard navigation keys mapped to bound methods
            "up": self._nav_up,
            "down": self._nav_down,
            "\r": self._nav_enter,
            "\n": self._nav_enter,
            "escape": self._nav_back,
            "\x1b": self._nav_back,
            "q": self._set_quit,
        }

    # ---- results-view handlers (CC <= 2 each) ---------------------------

    def _results_prev(self) -> None:  # WHY: bound handler for left-arrow in results view
        """Move scroll offset back to the previous result."""
        tui = self._tui  # Local alias
        tui.results_scroll_offset = max(0, tui.results_scroll_offset - 1)  # Clamp at zero
        tui.result_row_scroll = 0  # Reset row scroll on result change

    def _results_next(self) -> None:  # WHY: bound handler for right-arrow in results view
        """Advance scroll offset to the next result, clamped at last index."""
        tui = self._tui  # Local alias
        results = self._safe_results()  # Defensive list access
        max_offset = max(0, len(results) - 1)  # Last valid index
        tui.results_scroll_offset = min(max_offset, tui.results_scroll_offset + 1)  # WHY: clamp at last index
        tui.result_row_scroll = 0  # Reset row scroll on result change

    def _results_row_up(self) -> None:  # WHY: bound handler for up-arrow in results view
        """Scroll up 10 rows within the current result."""
        self._tui.result_row_scroll = max(0, self._tui.result_row_scroll - 10)  # WHY: clamp at top row

    def _results_row_down(self) -> None:  # WHY: bound handler for down-arrow in results view
        """Scroll down 10 rows. ResultsGridBuilder clamps the upper bound."""
        self._tui.result_row_scroll += 10  # Builder handles bounds

    def _results_page_up(self) -> None:  # WHY: bound handler for page-up in results view
        """Page up by 20 rows (2x arrow speed)."""
        self._tui.result_row_scroll = max(0, self._tui.result_row_scroll - 20)  # WHY: clamp at top row

    def _results_page_down(self) -> None:  # WHY: bound handler for page-down in results view
        """Page down by 20 rows (2x arrow speed)."""
        self._tui.result_row_scroll += 20  # Builder handles bounds

    def _results_jump_top(self) -> None:  # WHY: bound handler for 'h' shortcut
        """Jump to the top row of the current result."""
        self._tui.result_row_scroll = 0  # WHY: reset to first row

    def _results_jump_end(self) -> None:  # WHY: bound handler for 'e' shortcut
        """Jump to the end of the current result (builder caps the value)."""
        if self._safe_results():  # Only jump if there is data
            self._tui.result_row_scroll = 999999  # Sentinel. Builder clamps

    def _results_close(self) -> None:  # WHY: bound handler for escape/q in results view
        """Exit the results-view state and return to navigation."""
        self._tui.execution_state = None  # WHY: leave results-view mode
        self._tui.results_scroll_offset = 0  # WHY: reset horizontal scroll for next visit
        self._tui.result_row_scroll = 0  # WHY: reset vertical scroll for next visit

    def _safe_results(self) -> list[Any]:  # WHY: defensive accessor for possibly-missing payload
        """Return the parsed results list, or an empty list when unavailable."""
        parsed = self._tui.last_parsed_data  # Snapshot the current parsed payload
        if not isinstance(parsed, dict):  # Guard: missing or non-dict
            return []  # WHY: caller treats empty list as "no data"
        results = parsed.get("results")  # Pull the results array
        return results if isinstance(results, list) else []  # Guard: non-list

    # ---- prompting-mode handlers ----------------------------------------

    def _dispatch_prompting(self, key: str) -> None:  # WHY: prompt mode has extra printable-char fallback
        """Prompt mode needs a printable-character fallback after the dict."""
        handler = self._prompt_handlers.get(key)  # Try the table first
        if handler is not None:  # Known control key
            logging.info("TUI: prompting dispatch %r", key)  # WHY: action-log control-key path
            handler()  # WHY: run the bound prompt handler
            return  # WHY: control key handled, skip printable-char fallback
        if len(key) == 1 and key.isprintable():  # Otherwise append printable char
            self._tui.input_buffer += key  # WHY: accumulate user text into the prompt buffer

    def _prompt_submit(self) -> None:  # WHY: bound handler for Enter in prompt mode
        """Delegate Enter-key submission to the parameter collector."""
        self._tui._submit_parameter()  # Existing collector path

    def _prompt_backspace(self) -> None:  # WHY: bound handler for backspace in prompt mode
        """Remove the last character from the input buffer."""
        if self._tui.input_buffer:  # Guard against empty buffer
            self._tui.input_buffer = self._tui.input_buffer[:-1]  # WHY: pop trailing char

    # ---- navigation handlers --------------------------------------------

    def _nav_up(self) -> None:  # WHY: bound handler for up-arrow in navigation
        """Move the selection cursor up by one item, clamped at zero."""
        tui = self._tui  # Local alias
        tui.current_selection = max(0, tui.current_selection - 1)  # Clamp at top

    def _nav_down(self) -> None:  # WHY: bound handler for down-arrow in navigation
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
            tui._function_executor.start(selected)  # Begin parameter prompting via the executor collaborator

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
        """Escape: pop one level off the path. Quit when already at root."""
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
