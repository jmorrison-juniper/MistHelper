"""Unit tests for src/ui/execution/function_executor.py."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from src.ui.execution.function_executor import FunctionExecutor, _redact


def _api_call(org_id: str, limit: int = 100):  # noqa: ANN201 — test stub
    """Test stand-in for an API function — returns a dict-shaped result."""
    return {"results": [{"id": org_id}], "next": None}  # Single page payload


def _api_call_with_session(mist_session, org_id: str):  # noqa: ANN001, ANN201
    """API stub requiring 'mist_session' to exercise the session autofill branch."""
    return {"results": [{"session": str(mist_session), "org": org_id}]}


def _missing_param_api():
    """No-arg API stub for the 'no-params-required' branch."""
    return {"results": [], "total": 0}


def test_redact_masks_secret_names() -> None:
    """Names containing pass/token/key/secret are redacted; others pass through."""
    assert _redact("password", "abc") == "***REDACTED***"  # 'pass' substring
    assert _redact("api_token", "abc") == "***REDACTED***"  # 'token' substring
    assert _redact("client_secret", "abc") == "***REDACTED***"  # 'secret' substring
    assert _redact("x_api_key", "abc") == "***REDACTED***"  # 'key' substring
    assert _redact("org_id", "abc") == "abc"  # Clean name


def test_start_rejects_non_callable(tui_stub) -> None:
    """A selected_item with no callable object yields an error line."""
    FunctionExecutor(tui_stub).start({"name": "fn", "object": None})  # No object
    assert tui_stub.output_lines == ["[ERROR] Selected item is not callable"]


def test_start_with_no_params_executes_immediately(tui_stub) -> None:
    """A zero-arg function jumps straight to execute() and stores the result."""
    tui_stub.function_params = {}  # Reset
    FunctionExecutor(tui_stub).start({"name": "noargs", "object": _missing_param_api})
    assert tui_stub.last_parsed_data == {"results": [], "total": 0}


def test_start_collects_remaining_params(tui_stub) -> None:
    """Required parameters that lack autofill are queued for prompting."""
    tui_stub.dotenv_values = {}  # No .env values
    FunctionExecutor(tui_stub).start({"name": "api", "object": _api_call})  # Build param list
    assert tui_stub.execution_state == "prompting"  # Prompting mode entered
    names = [p["name"] for p in tui_stub.param_list]
    assert "org_id" in names and "limit" in names  # Both args queued


def test_start_autofills_apisession(tui_stub) -> None:
    """A parameter named 'mist_session' is auto-filled from tui.apisession."""
    sentinel = object()  # Distinct session sentinel
    tui_stub.apisession = sentinel  # Wire shared session
    tui_stub.dotenv_values = {"org_id": "orgX"}  # Autofill org_id from .env
    # _api_call_with_session(mist_session, org_id) echoes its args into the result:
    FunctionExecutor(tui_stub).start({"name": "api", "object": _api_call_with_session})
    # function_params is cleared by _reset_post_execute; verify via the echoed result:
    assert tui_stub.last_parsed_data is not None  # Call completed successfully
    assert tui_stub.last_parsed_data["results"][0]["org"] == "orgX"  # org_id was injected
    assert "session" in tui_stub.last_parsed_data["results"][0]  # mist_session was injected


def test_start_aborts_when_session_missing(tui_stub) -> None:
    """Missing session for a session-requiring function yields an error."""
    tui_stub.apisession = None  # No session available
    FunctionExecutor(tui_stub).start({"name": "api", "object": _api_call_with_session})
    assert tui_stub.output_lines == ["[ERROR] API session not available"]


def test_start_handles_signature_failure(tui_stub) -> None:
    """An inspect.signature failure surfaces an [ERROR] line."""

    class _NoSig:  # Calling len(_NoSig()) raises but inspect.signature works.
        def __call__(self) -> int:  # pragma: no cover - presence is what matters
            return 0

    # Use a builtin that inspect.signature cannot introspect on Windows for some types:
    tui_stub.dotenv_values = {}  # No autofill
    executor = FunctionExecutor(tui_stub)
    executor._prepare_parameter_list = MagicMock(side_effect=RuntimeError("sig fail"))
    executor.start({"name": "bad", "object": lambda: None})  # type: ignore[arg-type]
    assert any("Failed to prepare execution" in line for line in tui_stub.output_lines)


def test_execute_handles_call_failure(tui_stub) -> None:
    """Any exception from the call is captured into last_error/output_lines."""

    def _raises():  # noqa: ANN202
        raise ValueError("api broke")

    tui_stub.current_function = {"name": "broken", "object": _raises}  # Pre-seed selection
    FunctionExecutor(tui_stub).execute()  # Trigger
    assert tui_stub.last_error == "api broke"  # Error captured
    assert any("Execution failed" in line for line in tui_stub.output_lines)


def test_execute_resets_state_post_run(tui_stub) -> None:
    """After execute(), the pending-execution state is cleared."""
    tui_stub.current_function = {"name": "noargs", "object": _missing_param_api}
    tui_stub.param_list = [{"name": "x", "has_default": False}]  # Pretend params remain
    tui_stub.current_param_index = 1  # ...index advanced
    tui_stub.input_buffer = "left-over"  # ...buffer dirty
    FunctionExecutor(tui_stub).execute()  # Run
    assert tui_stub.current_function is None  # Function dropped
    assert tui_stub.param_list == []  # Param list reset
    assert tui_stub.current_param_index == 0  # Index reset
    assert tui_stub.input_buffer == ""  # Buffer cleared


def test_execute_preserves_viewing_results_state(tui_stub) -> None:
    """When _should_show_results_grid is True, state stays in viewing_results."""
    tui_stub._should_show_results_grid = MagicMock(return_value=True)  # Force grid mode
    tui_stub.current_function = {"name": "noargs", "object": _missing_param_api}
    FunctionExecutor(tui_stub).execute()  # Run
    assert tui_stub.execution_state == "viewing_results"  # Preserved


def test_execute_paginates_via_next_cursor(tui_stub) -> None:
    """If result.next is truthy, the executor follows the cursor via mist_get."""

    class _PagedResult:
        def __init__(self, next_url, data) -> None:  # noqa: ANN001
            self.next = next_url  # Pagination cursor
            self.data = data  # Parsed-style payload

    page1 = _PagedResult("/next-url", {"results": [{"id": "a"}], "total": 2})
    page2 = _PagedResult(None, {"results": [{"id": "b"}], "total": 2})

    def _initial_call(**_kw: Any):
        return page1  # First page

    session = MagicMock()  # Shared session stand-in
    session.mist_get = MagicMock(return_value=page2)  # Pagination call
    tui_stub.apisession = session
    tui_stub.function_params = {"mist_session": session}  # Pre-seeded session
    tui_stub.current_function = {"name": "paged", "object": _initial_call}
    # Parser must unwrap .data to mimic real APIResponse contract:
    tui_stub._parse_api_response = MagicMock(side_effect=lambda r: r.data)
    FunctionExecutor(tui_stub).execute()  # Trigger
    # Both pages combined in last_parsed_data:
    ids = [row["id"] for row in tui_stub.last_parsed_data["results"]]
    assert ids == ["a", "b"]
    session.mist_get.assert_called_once_with("/next-url")  # Pagination call made


def test_execute_returns_early_when_no_current_function(tui_stub) -> None:
    """execute() is a no-op when nothing is currently selected."""
    tui_stub.current_function = None  # Nothing to do
    FunctionExecutor(tui_stub).execute()  # Should not raise
    assert tui_stub.last_parsed_data is None  # State untouched


def test_extract_page_results_returns_empty_on_bad_shape() -> None:
    """The static page extractor returns [] for non-dict / missing results."""
    assert FunctionExecutor._extract_page_results("not a dict") == []
    assert FunctionExecutor._extract_page_results({"results": "not a list"}) == []
    assert FunctionExecutor._extract_page_results({}) == []
