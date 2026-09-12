"""Parameter prep + Live-mode execution path (replaces ``_execute_function`` CC=36).

Also owns ``_start_function_execution`` (CC=14) parameter discovery.
Every helper here has CC <= 10.
"""

from __future__ import annotations  # WHY: postponed evaluation for PEP 604 unions on 3.13

import inspect  # WHY: probe callable signatures for parameter discovery
import logging  # WHY: action-log start/execute/error transitions
from typing import Any  # WHY: TUI back-ref + parsed payloads are opaque

_SECRET_TOKENS = ("pass", "token", "key", "secret")  # Substrings that flag secret-like names


def _redact(name: str, value: Any) -> Any:  # WHY: log-safe value transform for secret-ish names
    """Redact ``value`` when ``name`` looks like a secret parameter."""
    if any(token in name.lower() for token in _SECRET_TOKENS):  # Substring scan for secrets
        return "***REDACTED***"  # WHY: mask secret payload before returning to caller
    return value  # Pass-through for non-secret names


class FunctionExecutor:  # WHY: extracted from MistHelperTUI to own Live-mode execution
    """Executes the currently-selected API function in Live (in-TUI) mode."""

    def __init__(self, tui: Any) -> None:  # WHY: bind owning TUI for shared state
        """Store a back-reference to the owning TUI for shared state access."""
        self._tui = tui  # Back-reference for shared TUI state

    # ---- start: parameter discovery & prompting kickoff -----------------

    def start(self, selected_item: dict[str, Any]) -> None:  # WHY: entrypoint from nav-Enter dispatch
        """Begin function execution: prep parameters, then either prompt or run."""
        tui = self._tui  # Local alias
        tui.current_function = selected_item  # Store under exec context
        func = selected_item.get("object")  # Callable to invoke
        func_name = selected_item.get("name")  # For logging + error messages
        if not func or not callable(func):  # Guard: invalid selection
            tui.output_lines = ["[ERROR] Selected item is not callable"]  # WHY: user-visible error line
            return  # WHY: nothing to execute, bail out early
        logging.info("TUI: starting execution of %s", func_name)  # Action log before signature probe
        try:
            self._prepare_parameter_list(func)  # Build tui.param_list / function_params
        except Exception as error:  # Signature probing can fail on builtins
            tui.output_lines = [f"[ERROR] Failed to prepare execution: {error}"]  # WHY: surface probe failure
            logging.exception("TUI: Failed to prepare execution of %s: %s", func_name, error)  # WHY: log traceback
            return  # WHY: probe failed, cannot execute
        self._begin_collection_or_execute()  # Branch on whether params remain

    def _prepare_parameter_list(self, func: Any) -> None:  # WHY: signature probe + autofill dispatcher
        """Inspect ``func``'s signature. Build param_list + auto-fill known names."""
        tui = self._tui  # Local alias
        sig = inspect.signature(func)  # Signature object
        tui.param_list = []  # Reset collection list
        tui.function_params = {}  # Reset captured params
        for param_name, param in sig.parameters.items():  # Walk each parameter
            self._process_signature_param(param_name, param)  # Delegate per-param handling to helper

    def _process_signature_param(self, param_name: str, param: Any) -> None:  # WHY: per-param branch helper
        """Handle one signature parameter: skip self, try autofills, else queue prompt."""
        if param_name == "self":  # Skip implicit self
            return  # WHY: never prompt for self
        if self._try_autofill_session(param_name):  # Try mist_session/apisession autofill
            return  # WHY: session handled by helper
        if self._try_autofill_dotenv(param_name):  # Try .env autofill
            return  # WHY: dotenv handled by helper
        has_default = param.default != inspect.Parameter.empty  # Required vs optional flag
        self._tui.param_list.append(  # Defer to interactive prompt
            {
                "name": param_name,
                "has_default": has_default,
                "default": param.default if has_default else None,
            }
        )

    def _try_autofill_session(self, param_name: str) -> bool:  # WHY: session autofill probe
        """Autofill ``mist_session`` / ``apisession`` from the shared TUI session."""
        if param_name not in ("mist_session", "apisession"):  # Only specific session names
            return False  # WHY: not a session param, let caller continue
        tui = self._tui  # Local alias
        if getattr(tui, "apisession", None) is None:  # Guard: session missing
            tui.output_lines = ["[ERROR] API session not available"]  # WHY: user-visible error
            return True  # Stop iteration with error already set
        tui.function_params[param_name] = tui.apisession  # Inject session reference
        return True  # WHY: session param handled

    def _try_autofill_dotenv(self, param_name: str) -> bool:  # WHY: .env autofill probe
        """Autofill parameter from ``.env`` values when present."""
        tui = self._tui  # Local alias
        if param_name not in tui.dotenv_values:  # Not in .env -> caller continues
            return False  # WHY: no .env match, caller keeps trying
        tui.function_params[param_name] = tui.dotenv_values[param_name]  # Use .env value directly
        return True  # WHY: .env value injected

    def _begin_collection_or_execute(self) -> None:
        """Start prompting when params remain. Otherwise execute immediately."""
        tui = self._tui  # Local alias
        if tui.param_list:  # Prompt mode if any params remain
            tui.execution_state = "prompting"
            tui.current_param_index = 0
            tui.input_buffer = ""
            return
        self.execute()  # No params -> jump straight to call

    # ---- execute: API call + pagination + result handling ---------------

    def execute(self) -> None:
        """Run the prepared function call with pagination + final state mgmt."""
        tui = self._tui  # Local alias
        if not tui.current_function:  # Guard: nothing to do
            return
        func = tui.current_function.get("object")  # Callable
        func_name = tui.current_function.get("name")  # For logging
        tui.execution_state = "executing"  # Switch to running state
        tui.output_lines = ["[EXECUTING] Running API call..."]
        logging.info("TUI: executing %s", func_name)  # Action log before call
        try:
            self._execute_and_paginate(func, func_name)  # Heavy lifting in helper
        except Exception as error:  # Surface and log any failure
            tui.last_error = str(error)
            tui.output_lines = ["[ERROR] Execution failed", f"Function: {func_name}", f"Error: {error}"]
            logging.exception("TUI: Execution of %s failed - %s", func_name, error)
        finally:
            self._reset_post_execute()  # Always clear ephemeral exec state

    def _execute_and_paginate(self, func: Any, func_name: str) -> None:
        """Make the initial call, paginate via ``result.next``, then format output."""
        tui = self._tui  # Local alias
        result = func(**tui.function_params)  # Initial API call
        parsed_data = tui._api_parser.parse(result)  # Strip APIResponse wrapper via the parser collaborator
        result, parsed_data = self._paginate_if_possible(result, parsed_data)  # Follow next URL if applicable
        if tui.debug_mode:  # Save debug artifact when in debug mode
            tui._debug_saver.save(func_name, result, parsed_data)
        tui.last_result = result  # Stash for details panel
        tui.last_parsed_data = parsed_data  # Stash for grid display
        tui.output_lines = tui._hier_formatter.format_result(parsed_data, func_name, result)  # Format via collaborator
        if tui._should_show_results_grid(parsed_data):  # Switch into grid view when tabular
            tui.execution_state = "viewing_results"
            tui.results_scroll_offset = 0
            logging.info(
                "TUI: Results grid available - entering viewing_results state with %s items",
                len(parsed_data.get("results", [])),
            )
        else:
            logging.info("TUI: Execution complete - no grid display (data type: %s)", type(parsed_data).__name__)
        logging.debug("TUI: %s completed", func_name)  # Action log after success

    def _paginate_if_possible(self, result: Any, parsed_data: Any) -> tuple[Any, Any]:  # WHY: cursor-pagination entry
        """Follow ``result.next`` cursor pagination, accumulating results."""
        tui = self._tui  # Local alias
        if not (isinstance(parsed_data, dict) and "results" in parsed_data):  # Only paginate result-wrapped payloads
            return result, parsed_data
        session = tui.function_params.get("mist_session") or tui.function_params.get(
            "apisession"
        )  # WHY: pager needs a session
        if not session:  # Guard: no session -> return single page as-is
            return result, parsed_data
        return self._collect_pages(result, parsed_data, session)  # Delegate page loop to helper

    def _collect_pages(self, result: Any, parsed_data: Any, session: Any) -> tuple[Any, Any]:  # WHY: pagination loop
        """Iterate ``result.next`` until exhausted, patching accumulated results back in."""
        tui = self._tui  # Local alias
        accumulated = list(parsed_data.get("results", []))  # Seed with first page
        page_count = 1  # Track for logging
        while self._has_next_cursor(result):  # Loop while cursor is available
            page_count += 1  # Increment page counter
            tui.output_lines = [f"[EXECUTING] Fetching page {page_count} (total results so far: {len(accumulated)})..."]
            result, parsed_data, stop = self._fetch_next_page(
                result, session, page_count, accumulated
            )  # WHY: one page step
            if stop:  # Error or empty page -> exit loop
                break
        if page_count > 1:  # Patch the accumulated list in
            parsed_data["results"] = accumulated
        return result, parsed_data

    @staticmethod
    def _has_next_cursor(result: Any) -> bool:  # WHY: encapsulate hasattr+None guard for while-cond
        """Return True when ``result`` carries a non-None ``next`` cursor."""
        return hasattr(result, "next") and result.next is not None  # WHY: cursor may be attr-missing or None

    def _fetch_next_page(  # WHY: single-step pager: fetch + parse + append
        self,
        result: Any,
        session: Any,
        page_count: int,
        accumulated: list[Any],
    ) -> tuple[Any, Any, bool]:
        """Fetch one page via ``session.mist_get``, append to accumulator, signal stop."""
        tui = self._tui  # Local alias
        try:
            result = session.mist_get(result.next)  # Fetch next page via shared session
        except Exception as error:  # Tolerate transient pagination errors
            logging.debug("TUI: pagination error on page %s - %s, stopping", page_count, error)
            return result, None, True  # WHY: signal caller to break out of the loop
        parsed_data = tui._api_parser.parse(result)  # Re-parse the wrapper via the parser collaborator
        new_results = self._extract_page_results(parsed_data)  # Pull this page's items
        if not new_results:  # Empty page -> done
            return result, parsed_data, True  # WHY: end of stream, tell caller to stop
        accumulated.extend(new_results)  # Append to running list
        return result, parsed_data, False  # WHY: more pages may follow

    @staticmethod
    def _extract_page_results(parsed_data: Any) -> list[Any]:
        """Return the ``results`` list from a paginated page, or ``[]``."""
        if not isinstance(parsed_data, dict):  # Defensive guard
            return []
        results = parsed_data.get("results", [])  # Pull the array
        return results if isinstance(results, list) else []  # Guard: non-list

    def _reset_post_execute(self) -> None:
        """Reset transient execution state (preserves 'viewing_results' if set)."""
        tui = self._tui  # Local alias
        if tui.execution_state != "viewing_results":  # Do not clobber grid mode
            tui.execution_state = None
        tui.current_function = None  # Drop the function reference
        tui.function_params = {}  # Drop captured params
        tui.param_list = []  # Drop pending param list
        tui.current_param_index = 0  # Reset prompt index
        tui.input_buffer = ""  # Drop typed buffer
