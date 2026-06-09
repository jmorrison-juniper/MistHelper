"""Replacement for ``MistHelperTUI._submit_parameter`` (CC=14).

Each parameter-handling branch is a small dispatch helper (CC <= 5).
"""

from __future__ import annotations

import logging
from typing import Any

from src.ui.execution.function_executor import FunctionExecutor, _redact


class ParameterCollector:
    """Captures keystroke-collected parameter values and advances state."""

    def __init__(self, tui: Any, executor: FunctionExecutor) -> None:
        """Store back-references to the TUI state and the FunctionExecutor used after submit."""
        self._tui = tui  # Back-reference to TUI state
        self._executor = executor  # Used to run when collection is done

    def submit(self) -> None:
        """Submit the current parameter value; advance index or run the call."""
        tui = self._tui  # Local alias
        if tui.current_param_index >= len(tui.param_list):  # Guard: nothing pending
            return
        param_info = tui.param_list[tui.current_param_index]  # Current parameter dict
        value = tui.input_buffer.strip()  # Trim typed buffer
        logging.info("TUI: parameter submit %s", param_info["name"])  # Action log before processing
        if not self._capture_value(param_info, value):  # Capture into function_params
            return  # Error already surfaced
        tui.current_param_index += 1  # Advance to next parameter
        tui.input_buffer = ""  # Reset typed buffer
        logging.debug("TUI: parameter submit done %s", param_info["name"])  # Action log after processing
        if tui.current_param_index >= len(tui.param_list):  # All params collected -> run
            self._executor.execute()

    def _capture_value(self, param_info: dict[str, Any], value: str) -> bool:
        """Apply the value capture rules for one parameter. Returns False on error."""
        if not value:  # Empty input branch
            return self._capture_empty(param_info)
        return self._capture_nonempty(param_info, value)  # Non-empty value branch

    def _capture_empty(self, param_info: dict[str, Any]) -> bool:
        """Handle empty input: required -> error; optional -> default/None."""
        tui = self._tui  # Local alias
        param_name = param_info["name"]  # Used in messages
        if not param_info["has_default"]:  # Required parameter must have a value
            tui.output_lines = [f"[ERROR] {param_name} is required"]
            return False
        if param_name == "limit":  # Special-case: default 'limit' to 1000
            tui.function_params[param_name] = 1000
            return True
        tui.function_params[param_name] = None  # Optional w/o value -> explicit None
        return True

    def _capture_nonempty(self, param_info: dict[str, Any], value: str) -> bool:
        """Handle a typed value: convert ints for ``limit``, redact secrets."""
        tui = self._tui  # Local alias
        param_name = param_info["name"]  # Used in messages + logs
        if param_name == "limit":  # 'limit' must be an int
            try:
                tui.function_params[param_name] = int(value)
            except ValueError:  # Bad numeric input -> user error
                tui.output_lines = [f"[ERROR] {param_name} must be a number"]
                return False
            return True
        tui.function_params[param_name] = value  # Generic string capture
        if tui.debug_mode:  # Redacted debug log of capture
            logging.debug("TUI_DEBUG: Parameter stored - %s: %s", param_name, _redact(param_name, value))
        return True
