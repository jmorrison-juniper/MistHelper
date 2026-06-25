"""Synchronous-prompt execution path (replaces ``execute_current_item`` CC=54).

This is the legacy fall-out-of-Live ``input()``-prompt path used outside the
in-TUI prompting flow. Decomposed here so every helper is CC <= 10.
"""

from __future__ import annotations

import inspect
import logging
import os
import sys
from typing import Any

from src.ui.execution.function_executor import _redact
from src.utils.input_utils import InputUtils  # EOF-safe input wrapper (issue #452).

_LARGE_RESULT_HINT_THRESHOLD = 10  # Items above which we hint at exporting


class ItemExecutor:
    """Drives the synchronous (stdin-prompt) execution flow."""

    def __init__(self, tui: Any) -> None:
        """Store a back-reference to the owning TUI for shared state access."""
        self._tui = tui  # Back-reference for TUI state

    def execute(self) -> None:
        """Main entry point - guarded selection check, then run-and-render."""
        tui = self._tui  # Local alias
        selected = self._validated_selection()  # Validate selection first
        if selected is None:  # Nothing to do
            return
        func = selected.get("object")  # Callable to run
        func_name = str(selected.get("name") or "<unknown>")  # For logging + display
        if not func or not callable(func):  # Guard: invalid object
            tui.last_error = "Selected item is not callable"
            return
        logging.info("TUI: prompt-exec start for %s", func_name)  # Action log before run
        tui.last_result = None  # Clear previous result
        tui.last_error = None  # Clear previous error
        self._restore_terminal_for_prompt()  # Cooked mode for input()
        try:
            params = self._collect_params_interactively(func, func_name)  # Collect via stdin
            if params is None:  # Collection failed/aborted
                return
            self._invoke_and_display(func, func_name, params)  # Run + show preview
        except KeyboardInterrupt:  # Ctrl-C during prompts -> cancel
            print("\n[CANCELLED] Execution cancelled by user")
            logging.info("TUI: Execution of %s cancelled by user", func_name)
        except Exception as error:  # Any other failure -> log + display
            tui.last_error = str(error)
            print(f"\n[ERROR] {error}")
            logging.exception("TUI: Execution of %s failed - %s", func_name, error)
        finally:
            self._wait_and_restore_raw()  # Resume raw mode for TUI
        logging.debug("TUI: prompt-exec done for %s", func_name)  # Action log after run

    def _validated_selection(self) -> dict[str, Any] | None:
        """Return the selected item iff it's a function; otherwise ``None``."""
        tui = self._tui  # Local alias
        if not 0 <= tui.current_selection < len(tui.current_items):  # Bounds check
            return None
        selected: dict[str, Any] = tui.current_items[tui.current_selection]  # Snapshot
        if selected.get("type") != "function":  # Only functions are runnable
            return None
        return selected

    def _restore_terminal_for_prompt(self) -> None:
        """Switch the Unix terminal back to cooked mode for ``input()``."""
        tui = self._tui  # Local alias
        if tui.IS_WINDOWS:  # Windows uses msvcrt; nothing to do
            return
        tui.termios.tcsetattr(sys.stdin, tui.termios.TCSADRAIN, tui.old_terminal_settings)

    def _collect_params_interactively(self, func: Any, func_name: str) -> dict[str, Any] | None:
        """Walk the signature, prompting for each param; ``None`` on hard error."""
        sig = inspect.signature(func)  # Signature for introspection
        params: dict[str, Any] = {}  # Accumulator
        print(f"\n[Executing] {func_name}")  # Banner
        print(f"Signature: {func_name}{sig}\n")  # Show signature
        for param_name, param in sig.parameters.items():  # Walk each parameter
            if param_name == "self":  # Skip implicit self
                continue
            outcome = self._collect_one_param(param_name, param, params)  # Collect (or autofill)
            if outcome == "abort":  # Hard error -> abort run
                return None
        return params

    def _collect_one_param(self, param_name: str, param: Any, params: dict[str, Any]) -> str:
        """Collect a single parameter; returns 'abort' on hard error, else 'ok'."""
        if param_name in ("mist_session", "apisession"):  # Session-name autofill branch
            return "ok" if self._inject_session(param_name, params) else "abort"
        has_default = param.default != inspect.Parameter.empty  # Required vs optional flag
        env_value = os.getenv(param_name)  # Try environment autofill
        if env_value:  # .env autofill path
            params[param_name] = env_value
            print(f"  {param_name}: [from .env] {env_value}")
            return "ok"
        value = self._prompt_for_value(param_name, param.default, has_default)
        if not value and not has_default:  # Missing required -> abort
            print(f"[ERROR] {param_name} is required")
            self._tui.last_error = f"Missing required parameter: {param_name}"
            return "abort"
        if value:  # Store user-provided value when supplied
            params[param_name] = value
        return "ok"

    def _inject_session(self, param_name: str, params: dict[str, Any]) -> bool:
        """Inject ``mist_session`` / ``apisession`` when available."""
        if param_name not in ("mist_session", "apisession"):  # Only specific names
            return False
        tui = self._tui  # Local alias
        if getattr(tui, "apisession", None) is None:  # No session -> caller handles abort
            print("[ERROR] API session not available")
            tui.last_error = "API session not initialized"
            return False
        params[param_name] = tui.apisession  # Inject the session
        return True

    @staticmethod
    def _prompt_for_value(param_name: str, default: Any, has_default: bool) -> str:
        """Prompt the user for a single parameter via ``input()``."""
        default_str = f" (default: {default})" if has_default else ""  # Inline default hint
        required_str = "" if has_default else " [required]"  # Inline required tag
        prompt = f"  {param_name}{default_str}{required_str}: "  # Compose the prompt text
        return InputUtils.safe_input(prompt, context="tui_param_value")  # EOF-safe read + strip.

    def _invoke_and_display(self, func: Any, func_name: str, params: dict[str, Any]) -> None:
        """Invoke ``func`` with ``params``; render a safe preview to stdout."""
        tui = self._tui  # Local alias
        logging.info("TUI: calling %s with %s", func_name, {k: _redact(k, v) for k, v in params.items()})
        print("\nExecuting API call...")  # Status line for user
        result = func(**params)  # The actual API call
        tui.last_result = result  # Stash for caller
        print("\n[SUCCESS]")  # Success banner
        preview = _ResultPreview.build(result)  # Smart preview (no full repr)
        print(f"\n{preview}")  # Show preview
        if isinstance(result, (list, tuple, dict)) and len(result) > _LARGE_RESULT_HINT_THRESHOLD:
            print(
                f"\n[TIP] Result has {len(result)} items. Consider using main menu options "
                "to save full data to CSV/SQLite."
            )
        logging.info("TUI: Successfully executed %s", func_name)  # Action log after success

    def _wait_and_restore_raw(self) -> None:
        """Block on a single keypress, then restore Unix raw mode for the TUI."""
        tui = self._tui  # Local alias
        print("\nPress any key to return to explorer...")  # User cue
        if tui.IS_WINDOWS:  # Windows path
            tui.msvcrt.getch()
        else:
            sys.stdin.read(1)  # Unix cooked-mode read
        if not tui.IS_WINDOWS:  # Restore raw mode for TUI
            tui.tty.setcbreak(sys.stdin.fileno())


class _ResultPreview:
    """Build a safe preview string for arbitrary API results."""

    @classmethod
    def build(cls, result: Any) -> str:
        """Return a short, OOM-safe textual preview for ``result``."""
        if result is None:  # None short-circuit
            return "None"
        result_type = type(result).__name__  # Used in every branch
        if isinstance(result, (list, tuple)):
            return cls._preview_sequence(result, result_type)
        if isinstance(result, dict):
            return cls._preview_dict(result, result_type)
        if isinstance(result, str):
            return cls._preview_string(result)
        if isinstance(result, (int, float, bool)):
            return f"{result_type}: {result}"
        truncated = repr(result)[:200] + ("..." if len(repr(result)) > 200 else "")
        return f"{result_type}: {truncated}"  # Generic repr-with-cap

    @staticmethod
    def _preview_sequence(seq: Any, result_type: str) -> str:
        """Preview a list/tuple result safely (show <=3 items)."""
        count = len(seq)  # Cached length
        if count == 0:  # Empty fast path
            return f"{result_type}: [] (empty)"
        head = seq[: min(3, count)]  # Sample at most 3 items
        body = "".join(f"  [{idx}]: {repr(item)[:100]}\n" for idx, item in enumerate(head))
        if count <= 3:
            return f"{result_type} with {count} items:\n{body}"
        return f"{result_type} with {count} items (showing first 3):\n{body}  ... and {count - 3} more items"

    @staticmethod
    def _preview_dict(result: dict[str, Any], result_type: str) -> str:
        """Preview a dict result safely (show <=5 keys)."""
        key_count = len(result)  # Cached size
        if key_count == 0:  # Empty dict
            return f"{result_type}: {{}} (empty)"
        if key_count <= 5:  # Small enough to show all keys
            return f"{result_type} with {key_count} keys: {list(result.keys())}"
        first_keys = list(result.keys())[:5]  # First 5 keys only
        return f"{result_type} with {key_count} keys (first 5): {first_keys}..."

    @staticmethod
    def _preview_string(result: str) -> str:
        """Preview a string result safely (truncated above 200 chars)."""
        if len(result) <= 200:  # Short string: show in full
            return f"String: {result}"
        return f"String ({len(result)} chars): {result[:200]}..."  # Truncated string with size hint
