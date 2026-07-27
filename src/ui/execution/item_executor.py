"""Synchronous-prompt execution path (replaces ``execute_current_item`` CC=54).

This is the legacy fall-out-of-Live ``input()``-prompt path used outside the
in-TUI prompting flow. Decomposed here so every helper is CC <= 5 and every
function is <= 25 LoC; state is bundled in frozen slotted dataclasses and
result-preview branches are driven by a table-of-handlers dispatch.
"""

from __future__ import annotations  # WHY: postponed evaluation for PEP 604 unions and forward refs

import inspect  # WHY: probe callable signatures for interactive parameter discovery
import logging  # WHY: action-log start / cancel / error / success transitions
import os  # WHY: read .env-style autofill values via os.getenv
import sys  # WHY: swap stdin between raw and cooked modes on Unix
from collections.abc import Callable  # WHY: modern ABC location for callable annotations
from dataclasses import dataclass  # WHY: frozen slotted bundles keep per-run context compact
from typing import Any  # WHY: TUI back-ref and parameter payloads are opaque

from src.ui.execution.function_executor import _redact  # WHY: shared redactor masks secret args in call logs
from src.utils.input_utils import InputUtils  # WHY: EOF-safe input wrapper (issue #452)

# --- Module-level constants --------------------------------------------------
_LARGE_RESULT_HINT_THRESHOLD = 10  # WHY: results above this size get a CSV/SQLite export tip
_SESSION_PARAM_NAMES: tuple[str, ...] = ("mist_session", "apisession")  # WHY: names that autofill from tui.apisession
_UNKNOWN_NAME = "<unknown>"  # WHY: fallback display name when selected item lacks a 'name'
_OUTCOME_OK = "ok"  # WHY: sentinel returned by param-collection helpers on success
_OUTCOME_ABORT = "abort"  # WHY: sentinel returned when a hard error should abort the whole run

_PREVIEW_MAX_ITEMS = 3  # WHY: cap on list/tuple preview items
_PREVIEW_MAX_KEYS = 5  # WHY: cap on dict preview keys shown up-front
_PREVIEW_STRING_CAP = 200  # WHY: char cap for string previews
_PREVIEW_REPR_CAP = 200  # WHY: char cap for generic repr previews
_PREVIEW_ITEM_REPR_CAP = 100  # WHY: char cap for per-item repr in sequence preview

_MSG_NOT_CALLABLE = "Selected item is not callable"  # WHY: user-facing error stored on tui.last_error
_MSG_SESSION_ERROR = "API session not initialized"  # WHY: user-facing error when tui.apisession is None
_MSG_SESSION_PRINT = "[ERROR] API session not available"  # WHY: logged banner when tui.apisession is None
_MSG_CANCEL_BANNER = "\n[CANCELLED] Execution cancelled by user"  # WHY: logged banner on KeyboardInterrupt
_MSG_EXECUTING = "\nExecuting API call..."  # WHY: logged status line before the API call
_MSG_SUCCESS = "\n[SUCCESS]"  # WHY: logged success banner after the API call
_MSG_PRESS_KEY = "\nPress any key to return to explorer..."  # WHY: logged cue before wait-and-restore

_LOG_START = "TUI: prompt-exec start for %s"  # WHY: log format for pre-run breadcrumb
_LOG_DONE = "TUI: prompt-exec done for %s"  # WHY: log format for post-run breadcrumb
_LOG_CANCEL = "TUI: Execution of %s cancelled by user"  # WHY: log format for KeyboardInterrupt path
_LOG_FAIL = "TUI: Execution of %s failed - %s"  # WHY: log format for generic exception path
_LOG_SUCCESS = "TUI: Successfully executed %s"  # WHY: log format for success path
_LOG_CALL = "TUI: calling %s with %s"  # WHY: log format for redacted call site


@dataclass(frozen=True, slots=True)
class _Selection:  # WHY: immutable bundle of the validated callable + its display name
    """Validated function selection carrying the callable and its display name."""

    func: Callable[..., Any]  # WHY: callable to invoke with the collected params
    name: str  # WHY: display name for prompts, logging, and error messages


class ItemExecutor:  # WHY: extracted from MistHelperTUI to own the synchronous prompt path
    """Drives the synchronous (stdin-prompt) execution flow."""

    def __init__(self, tui: Any) -> None:  # WHY: bind owning TUI for shared state
        """Store a back-reference to the owning TUI for shared state access."""
        self._tui = tui  # WHY: TUI holds selection, session, and mode-switch helpers

    def execute(self) -> None:  # WHY: main entry point invoked from TUI dispatch
        """Main entry point - guarded selection check, then run-and-render."""
        selection = self._prepared_selection()  # WHY: validate + log + prep terminal in one step
        if selection is None:  # WHY: guard - nothing runnable was selected
            return  # WHY: nothing to run, exit before touching any state
        try:
            self._run_selection(selection)  # WHY: collect params, invoke, and render preview
        except KeyboardInterrupt:  # WHY: Ctrl-C during input() cancels cleanly
            self._on_cancel(selection.name)  # WHY: banner + action-log cancellation
        except Exception as error:  # WHY: any other failure surfaces as last_error and banner
            self._on_error(selection.name, error)  # WHY: expose error and log traceback
        finally:
            self._wait_and_restore_raw()  # WHY: always restore raw mode for the TUI
        logging.debug(_LOG_DONE, selection.name)  # WHY: post-run breadcrumb

    def _prepared_selection(self) -> _Selection | None:  # WHY: validate + prep gathered in one place
        """Validate the current selection, clear state, log start, and prep stdin for input()."""
        raw = self._validated_selection()  # WHY: bounds + type check
        if raw is None:  # WHY: guard - out-of-range or not a function item
            return None  # WHY: not runnable, caller aborts
        selection = self._extract_callable(raw)  # WHY: pull callable + name off the item
        if selection is None:  # WHY: guard - object was missing or not callable
            self._tui.last_error = _MSG_NOT_CALLABLE  # WHY: expose to caller for later render
            return None  # WHY: no callable, caller aborts
        self._begin_run(selection.name)  # WHY: reset state + switch to cooked mode
        return selection  # WHY: pass packed selection back to execute()

    @staticmethod
    def _extract_callable(selected: dict[str, Any]) -> _Selection | None:  # WHY: pack callable + display name
        """Return a ``_Selection`` iff the item carries a callable ``object``."""
        func = selected.get("object")  # WHY: callable to invoke
        if not func or not callable(func):  # WHY: guard - invalid or missing object
            return None  # WHY: nothing to invoke, signal caller
        name = str(selected.get("name") or _UNKNOWN_NAME)  # WHY: fallback name for logging + display
        return _Selection(func=func, name=name)  # WHY: bundle callable + name for downstream helpers

    def _begin_run(self, func_name: str) -> None:  # WHY: pre-run state reset + terminal switch
        """Log run start, clear last-run state, and switch stdin to cooked mode."""
        tui = self._tui  # WHY: local alias for repeated access
        logging.info(_LOG_START, func_name)  # WHY: action-log before any input()
        tui.last_result = None  # WHY: clear previous result to avoid stale render
        tui.last_error = None  # WHY: clear previous error to avoid stale render
        self._restore_terminal_for_prompt()  # WHY: cooked mode required for input()

    def _run_selection(self, selection: _Selection) -> None:  # WHY: main body extracted from execute()
        """Collect params interactively and invoke the callable with a rendered preview."""
        params = self._collect_params_interactively(selection.func, selection.name)  # WHY: signature walk
        if params is None:  # WHY: collection aborted - abort the whole run
            return  # WHY: abort signal from param collection, do not invoke
        self._invoke_and_display(selection.func, selection.name, params)  # WHY: call + preview

    def _on_cancel(self, func_name: str) -> None:  # WHY: KeyboardInterrupt path
        """Print the cancel banner and log the cancelled run."""
        # WHY (#886 Phase 2): retire print() in favor of logging.warning so the cancel banner
        # reaches the operator on the default root-logger config (INFO is suppressed by default).
        logging.warning(_MSG_CANCEL_BANNER)  # User-visible banner
        logging.info(_LOG_CANCEL, func_name)  # WHY: action-log the cancellation

    def _on_error(self, func_name: str, error: BaseException) -> None:  # WHY: generic exception path
        """Capture the error on the TUI, print a banner, and log with traceback."""
        self._tui.last_error = str(error)  # WHY: expose to caller for render
        # WHY (#886 Phase 2): retire print() in favor of logging.exception which already emits the
        # error string plus traceback via the shared handler chain (banner + triage in one call).
        logging.exception(_LOG_FAIL, func_name, error)  # WHY: include traceback for triage

    def _validated_selection(self) -> dict[str, Any] | None:  # WHY: bounds + type guard
        """Return the selected item iff it is a function; otherwise ``None``."""
        tui = self._tui  # WHY: local alias
        if not 0 <= tui.current_selection < len(tui.current_items):  # WHY: bounds check
            return None  # WHY: index out of range, not runnable
        selected: dict[str, Any] = tui.current_items[tui.current_selection]  # WHY: item snapshot
        if selected.get("type") != "function":  # WHY: only function items are runnable
            return None  # WHY: non-function items are ignored by execute()
        return selected  # WHY: pass validated item to caller for callable extraction

    def _restore_terminal_for_prompt(self) -> None:  # WHY: switch stdin to cooked mode on Unix
        """Switch the Unix terminal back to cooked mode for ``input()``."""
        tui = self._tui  # WHY: local alias
        if tui.IS_WINDOWS:  # WHY: Windows uses msvcrt; nothing to do
            return
        tui.termios.tcsetattr(
            sys.stdin, tui.termios.TCSADRAIN, tui.old_terminal_settings
        )  # WHY: cooked line-buffered mode

    def _collect_params_interactively(  # WHY: signature walk collecting one param at a time
        self, func: Any, func_name: str
    ) -> dict[str, Any] | None:
        """Walk the signature, prompting for each param; ``None`` on hard error."""
        sig = inspect.signature(func)  # WHY: signature for introspection
        params: dict[str, Any] = {}  # WHY: accumulator for collected values
        # WHY (#886 Phase 2): retire print() in favor of logging.warning so the pre-prompt banners
        # reach the operator on the default root-logger config (INFO is suppressed by default).
        logging.warning("\n[Executing] %s", func_name)  # Banner before prompts
        logging.warning("Signature: %s%s\n", func_name, sig)  # Show signature for user context
        for param_name, param in sig.parameters.items():  # WHY: walk each parameter
            if param_name == "self":  # WHY: skip implicit self
                continue
            outcome = self._collect_one_param(param_name, param, params)  # WHY: autofill or prompt
            if outcome == _OUTCOME_ABORT:  # WHY: hard error - abort whole run
                return None
        return params

    def _collect_one_param(  # WHY: single-param table-driven dispatch (session -> env -> prompt)
        self, param_name: str, param: Any, params: dict[str, Any]
    ) -> str:
        """Collect a single parameter; returns ``_OUTCOME_ABORT`` on hard error, else ``_OUTCOME_OK``."""
        outcome = self._session_autofill_outcome(param_name, params)  # WHY: mist_session / apisession branch
        if outcome is not None:  # WHY: session branch handled the param
            return outcome
        outcome = self._env_autofill_outcome(param_name, params)  # WHY: .env autofill branch
        if outcome is not None:  # WHY: .env branch handled the param
            return outcome
        return self._prompt_outcome(param_name, param, params)  # WHY: fall through to interactive prompt

    def _session_autofill_outcome(self, param_name: str, params: dict[str, Any]) -> str | None:  # WHY: session branch
        """Inject the shared session for session-named params; ``None`` when not applicable."""
        if param_name not in _SESSION_PARAM_NAMES:  # WHY: only 'mist_session' / 'apisession'
            return None
        return (
            _OUTCOME_OK if self._inject_session(param_name, params) else _OUTCOME_ABORT
        )  # WHY: propagate injector result

    def _env_autofill_outcome(self, param_name: str, params: dict[str, Any]) -> str | None:  # WHY: .env autofill branch
        """Autofill from ``os.getenv``; ``None`` when the env value is empty/missing."""
        env_value = os.getenv(param_name)  # WHY: environment autofill source
        if not env_value:  # WHY: no env value - defer to prompt
            return None
        params[param_name] = env_value  # WHY: store env value on accumulator
        # WHY (#886 Phase 2): retire print() in favor of logging.warning so the autofill provenance
        # reaches the operator on the default root-logger config (INFO is suppressed by default).
        logging.warning("  %s: [from .env] %s", param_name, env_value)  # Show autofill provenance to user
        return _OUTCOME_OK

    def _prompt_outcome(
        self, param_name: str, param: Any, params: dict[str, Any]
    ) -> str:  # WHY: interactive prompt branch
        """Prompt the user for ``param_name``; abort when required-and-empty."""
        has_default = param.default != inspect.Parameter.empty  # WHY: required-vs-optional flag
        value = self._prompt_for_value(param_name, param.default, has_default)  # WHY: EOF-safe stdin read
        if not value and not has_default:  # WHY: required-but-empty - hard error
            # WHY (#886 Phase 2): retire print() in favor of logging.error so the required-param
            # banner reaches the operator on the default root-logger config.
            logging.error("[ERROR] %s is required", param_name)  # User-visible error banner
            self._tui.last_error = f"Missing required parameter: {param_name}"  # WHY: expose to caller for render
            return _OUTCOME_ABORT
        if value:  # WHY: store user-provided value only when supplied
            params[param_name] = value
        return _OUTCOME_OK

    def _inject_session(self, param_name: str, params: dict[str, Any]) -> bool:  # WHY: session injector
        """Inject ``mist_session`` / ``apisession`` when available."""
        if param_name not in _SESSION_PARAM_NAMES:  # WHY: only specific names accepted
            return False
        tui = self._tui  # WHY: local alias
        if getattr(tui, "apisession", None) is None:  # WHY: guard - no session available
            # WHY (#886 Phase 2): retire print() in favor of logging.error so the missing-session
            # banner reaches the operator on the default root-logger config.
            logging.error(_MSG_SESSION_PRINT)  # User-visible banner
            tui.last_error = _MSG_SESSION_ERROR  # WHY: expose to caller for render
            return False
        params[param_name] = tui.apisession  # WHY: inject the session reference
        return True

    @staticmethod
    def _prompt_for_value(param_name: str, default: Any, has_default: bool) -> str:  # WHY: single prompt render
        """Prompt the user for a single parameter via ``input()``."""
        default_str = f" (default: {default})" if has_default else ""  # WHY: inline default hint
        required_str = "" if has_default else " [required]"  # WHY: inline required tag
        prompt = f"  {param_name}{default_str}{required_str}: "  # WHY: compose the prompt text
        return InputUtils.safe_input(prompt, context="tui_param_value")  # WHY: EOF-safe read + strip

    def _invoke_and_display(  # WHY: call, capture, and render a bounded preview
        self, func: Any, func_name: str, params: dict[str, Any]
    ) -> None:
        """Invoke ``func`` with ``params``; render a safe preview to stdout."""
        tui = self._tui  # WHY: local alias
        redacted = {k: _redact(k, v) for k, v in params.items()}  # WHY: redact secrets before logging
        logging.info(_LOG_CALL, func_name, redacted)  # WHY: log the redacted call site
        # WHY (#886 Phase 2): retire print() in favor of logging.warning so the executing/success/
        # preview banners reach the operator on the default root-logger config.
        logging.warning(_MSG_EXECUTING)  # Status line for user
        result = func(**params)  # WHY: the actual API call
        tui.last_result = result  # WHY: stash for caller / details panel
        logging.warning(_MSG_SUCCESS)  # Success banner
        logging.warning("\n%s", _ResultPreview.build(result))  # Smart preview (no full repr)
        self._maybe_print_export_hint(result)  # WHY: hint when result is large enough
        logging.info(_LOG_SUCCESS, func_name)  # WHY: action-log after success

    @staticmethod
    def _maybe_print_export_hint(result: Any) -> None:  # WHY: guarded tip extracted for CC
        """Print the CSV/SQLite export hint when the result carries more than the threshold."""
        if not isinstance(result, (list, tuple, dict)):  # WHY: only sized containers get the tip
            return
        if len(result) <= _LARGE_RESULT_HINT_THRESHOLD:  # WHY: only large enough to warrant the tip
            return
        # WHY (#886 Phase 2): retire print() in favor of logging.warning so the export tip reaches
        # the operator on the default root-logger config (INFO is suppressed by default).
        logging.warning(  # User-visible tip banner
            "\n[TIP] Result has %d items. Consider using main menu options " "to save full data to CSV/SQLite.",
            len(result),
        )

    def _wait_and_restore_raw(self) -> None:  # WHY: wait-for-key + restore raw mode
        """Block on a single keypress, then restore Unix raw mode for the TUI."""
        tui = self._tui  # WHY: local alias
        # WHY (#886 Phase 2): retire print() in favor of logging.warning so the press-key cue
        # reaches the operator on the default root-logger config.
        logging.warning(_MSG_PRESS_KEY)  # User cue
        self._read_single_keypress(tui)  # WHY: platform-specific single-char read
        if not tui.IS_WINDOWS:  # WHY: restore raw mode for the TUI on Unix
            tui.tty.setcbreak(sys.stdin.fileno())

    @staticmethod
    def _read_single_keypress(tui: Any) -> None:  # WHY: platform-branch extracted for CC
        """Read a single keypress via ``msvcrt.getch`` on Windows, else ``sys.stdin.read(1)``."""
        if tui.IS_WINDOWS:  # WHY: Windows path uses msvcrt.getch
            tui.msvcrt.getch()
            return
        sys.stdin.read(1)  # WHY: Unix cooked-mode single-char read


# --- Result-preview handlers (table-driven dispatch) -------------------------
def _preview_none(_result: Any, _result_type: str) -> str:  # WHY: dispatch handler for None
    """Preview handler for ``None``."""
    return "None"


def _preview_sequence(seq: Any, result_type: str) -> str:  # WHY: dispatch handler for list/tuple
    """Preview a list/tuple result safely (show <=_PREVIEW_MAX_ITEMS)."""
    count = len(seq)  # WHY: cached length
    if count == 0:  # WHY: empty fast path
        return f"{result_type}: [] (empty)"
    head = seq[: min(_PREVIEW_MAX_ITEMS, count)]  # WHY: sample at most N items
    body = "".join(f"  [{idx}]: {repr(item)[:_PREVIEW_ITEM_REPR_CAP]}\n" for idx, item in enumerate(head))
    if count <= _PREVIEW_MAX_ITEMS:  # WHY: entire sequence already shown
        return f"{result_type} with {count} items:\n{body}"
    remaining = count - _PREVIEW_MAX_ITEMS  # WHY: how many items past the head
    header = f"{result_type} with {count} items (showing first {_PREVIEW_MAX_ITEMS}):"  # WHY: hoisted for line length
    return f"{header}\n{body}  ... and {remaining} more items"


def _preview_dict(result: dict[str, Any], result_type: str) -> str:  # WHY: dispatch handler for dict
    """Preview a dict result safely (show <=_PREVIEW_MAX_KEYS)."""
    key_count = len(result)  # WHY: cached size
    if key_count == 0:  # WHY: empty dict fast path
        return f"{result_type}: {{}} (empty)"
    if key_count <= _PREVIEW_MAX_KEYS:  # WHY: small enough - show all keys
        return f"{result_type} with {key_count} keys: {list(result.keys())}"
    first_keys = list(result.keys())[:_PREVIEW_MAX_KEYS]  # WHY: first N keys only
    return f"{result_type} with {key_count} keys (first {_PREVIEW_MAX_KEYS}): {first_keys}..."


def _preview_string(result: str, _result_type: str) -> str:  # WHY: dispatch handler for str
    """Preview a string result safely (truncated above ``_PREVIEW_STRING_CAP``)."""
    if len(result) <= _PREVIEW_STRING_CAP:  # WHY: short string - show in full
        return f"String: {result}"
    return f"String ({len(result)} chars): {result[:_PREVIEW_STRING_CAP]}..."


def _preview_primitive(result: Any, result_type: str) -> str:  # WHY: dispatch handler for int/float/bool
    """Preview a numeric or bool result as ``type: value``."""
    return f"{result_type}: {result}"


def _preview_generic(result: Any, result_type: str) -> str:  # WHY: dispatch fallback
    """Fallback preview using ``repr()`` capped at ``_PREVIEW_REPR_CAP`` chars."""
    text = repr(result)  # WHY: full repr used for length check
    if len(text) > _PREVIEW_REPR_CAP:  # WHY: truncate only when we exceed the cap
        text = text[:_PREVIEW_REPR_CAP] + "..."
    return f"{result_type}: {text}"


# First-match-wins dispatch: (predicate, handler). ``_preview_string`` sits above
# the primitive branch so ``str`` never falls through to the ``(int, float, bool)``
# arm (``bool`` is an ``int`` subclass, but only the primitive arm captures it).
_PREVIEW_DISPATCH: tuple[tuple[Callable[[Any], bool], Callable[[Any, str], str]], ...] = (
    (lambda r: r is None, _preview_none),  # WHY: None handled before any isinstance
    (lambda r: isinstance(r, (list, tuple)), _preview_sequence),  # WHY: sized sequence
    (lambda r: isinstance(r, dict), _preview_dict),  # WHY: sized mapping
    (lambda r: isinstance(r, str), _preview_string),  # WHY: string checked before scalar arm
    (lambda r: isinstance(r, (int, float, bool)), _preview_primitive),  # WHY: scalar values
)


class _ResultPreview:  # WHY: single-shot preview builder for arbitrary API results
    """Build a safe preview string for arbitrary API results."""

    @classmethod
    def build(cls, result: Any) -> str:  # WHY: table-driven dispatch keeps CC = 3
        """Return a short, OOM-safe textual preview for ``result``."""
        result_type = type(result).__name__  # WHY: used by every handler
        for predicate, handler in _PREVIEW_DISPATCH:  # WHY: first match wins
            if predicate(result):
                return handler(result, result_type)
        return _preview_generic(result, result_type)  # WHY: fallback for everything else
