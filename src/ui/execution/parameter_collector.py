"""Replacement for ``MistHelperTUI._submit_parameter`` (CC=14).

Each parameter-handling branch is a small dispatch helper (CC <= 5).
"""

from __future__ import annotations  # WHY: postponed evaluation for forward-ref type hints

import logging  # WHY: action-log before/after every parameter capture
from typing import Any  # WHY: TUI back-ref is loosely typed

from src.ui.execution.function_executor import FunctionExecutor, _redact  # WHY: run + secret-redaction helpers


class ParameterCollector:  # WHY: extracted from MistHelperTUI._submit_parameter (was CC=14)
    """Captures keystroke-collected parameter values and advances state."""

    def __init__(self, tui: Any, executor: FunctionExecutor) -> None:  # WHY: bind TUI + executor for submit flow
        """Store back-references to the TUI state and the FunctionExecutor used after submit."""
        self._tui = tui  # Back-reference to TUI state
        self._executor = executor  # Used to run when collection is done

    def submit(self) -> None:  # WHY: user pressed Enter on the parameter prompt
        """Submit the current parameter value. Advance index or run the call."""
        tui = self._tui  # Local alias
        if tui.current_param_index >= len(tui.param_list):  # Guard: nothing pending
            return  # WHY: idempotent no-op when collection already complete
        param_info = tui.param_list[tui.current_param_index]  # Current parameter dict
        value = tui.input_buffer.strip()  # Trim typed buffer
        logging.info("TUI: parameter submit %s", param_info["name"])  # Action log before processing
        if not self._capture_value(param_info, value):  # Capture into function_params
            return  # Error already surfaced
        tui.current_param_index += 1  # Advance to next parameter
        tui.input_buffer = ""  # Reset typed buffer
        logging.debug("TUI: parameter submit done %s", param_info["name"])  # Action log after processing
        if tui.current_param_index >= len(tui.param_list):  # All params collected -> run
            self._executor.execute()  # WHY: hand off to executor now that inputs are complete

    def _capture_value(self, param_info: dict[str, Any], value: str) -> bool:  # WHY: dispatch empty vs typed branches
        """Apply the value capture rules for one parameter. Returns False on error."""
        if not value:  # Empty input branch
            return self._capture_empty(param_info)  # WHY: empty-value rules differ from typed
        return self._capture_nonempty(param_info, value)  # Non-empty value branch

    def _capture_empty(self, param_info: dict[str, Any]) -> bool:  # WHY: required->error, optional->default/None
        """Handle empty input: required -> error. Optional -> default/None."""
        tui = self._tui  # Local alias
        param_name = param_info["name"]  # Used in messages
        if not param_info["has_default"]:  # Required parameter must have a value
            tui.output_lines = [f"[ERROR] {param_name} is required"]  # WHY: surface error to TUI output pane
            return False  # WHY: signal caller to abort collection
        if param_name == "limit":  # Special-case: default 'limit' to 1000
            tui.function_params[param_name] = 1000  # WHY: sensible default page size
            return True  # WHY: value captured, continue collection
        tui.function_params[param_name] = None  # Optional w/o value -> explicit None
        return True  # WHY: optional param recorded as None, continue

    def _capture_nonempty(self, param_info: dict[str, Any], value: str) -> bool:  # WHY: parse + store typed value
        """Handle a typed value: convert ints for ``limit``, redact secrets."""
        tui = self._tui  # Local alias
        param_name = param_info["name"]  # Used in messages + logs
        if param_name == "limit":  # 'limit' must be an int
            try:
                tui.function_params[param_name] = int(value)  # WHY: coerce user text to int
            except ValueError:  # Bad numeric input -> user error
                tui.output_lines = [f"[ERROR] {param_name} must be a number"]  # WHY: surface parse error
                return False  # WHY: abort collection so user can retype
            return True  # WHY: int stored, continue collection
        tui.function_params[param_name] = value  # Generic string capture
        if tui.debug_mode:  # Redacted debug log of capture
            logging.debug("TUI_DEBUG: Parameter stored - %s: %s", param_name, _redact(param_name, value))
        return True  # WHY: string captured, continue collection
