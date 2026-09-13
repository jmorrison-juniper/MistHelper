"""Unit tests for src/ui/execution/item_executor.py."""

from __future__ import annotations

import builtins
from unittest.mock import MagicMock

import pytest

from src.ui.execution.item_executor import ItemExecutor, _ResultPreview


def _patch_input(monkeypatch: pytest.MonkeyPatch, answers: list[str]) -> None:
    """Replace input() with a sequenced answer queue."""
    queue = iter(answers)  # Pop-front iterator

    def _input(_prompt: str = "") -> str:
        return next(queue)  # Yield next pre-canned reply

    monkeypatch.setattr(builtins, "input", _input)  # Patch global input()


def _patch_keypress(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch ``sys.stdin.read(1)`` so the post-run wait completes immediately."""
    import sys as _sys

    monkeypatch.setattr(_sys.stdin, "read", lambda _n=1: "\n")  # Single-char read


def _api(org_id: str, limit: int = 100):
    """Test API stub returning a small dict."""
    return {"org_id": org_id, "limit": limit}


def _zero_arg_api() -> dict[str, str]:
    """Zero-argument API stub used for the auto-execute path."""
    return {"ok": "yes"}


def test_execute_invalid_selection_returns_silently(tui_stub) -> None:
    """Out-of-range selection produces no work and no error."""
    tui_stub.current_items = []  # Nothing selectable
    tui_stub.current_selection = 5  # Out of range
    ItemExecutor(tui_stub).execute()  # Should not raise
    assert tui_stub.last_error is None  # No error set


def test_execute_skips_non_function_selection(tui_stub, make_item) -> None:
    """If the selection is a module/error, execute() exits early."""
    tui_stub.current_items = [make_item("module", "orgs")]  # Module item
    tui_stub.current_selection = 0
    ItemExecutor(tui_stub).execute()  # Should noop
    assert tui_stub.last_result is None  # No result set


def test_execute_rejects_non_callable_object(tui_stub, make_item) -> None:
    """A function-typed item with a non-callable object surfaces an error."""
    tui_stub.current_items = [make_item("function", "fn", object=None)]
    tui_stub.current_selection = 0
    ItemExecutor(tui_stub).execute()  # Trigger
    assert tui_stub.last_error == "Selected item is not callable"


def test_execute_happy_path_with_user_input(tui_stub, make_item, monkeypatch: pytest.MonkeyPatch) -> None:
    """Walk through prompt collection + API call + result storage."""
    tui_stub.current_items = [make_item("function", "list", object=_api)]
    tui_stub.current_selection = 0
    _patch_input(monkeypatch, answers=["abc", ""])  # org_id then empty limit
    _patch_keypress(monkeypatch)  # post-run wait
    ItemExecutor(tui_stub).execute()  # Trigger
    assert tui_stub.last_result == {"org_id": "abc", "limit": 100}  # Default kept


def test_execute_aborts_on_missing_required_param(tui_stub, make_item, monkeypatch: pytest.MonkeyPatch) -> None:
    """Empty input for a required parameter aborts the call."""
    tui_stub.current_items = [make_item("function", "list", object=_api)]
    tui_stub.current_selection = 0
    _patch_input(monkeypatch, answers=[""])  # Empty required input
    _patch_keypress(monkeypatch)
    ItemExecutor(tui_stub).execute()  # Trigger
    assert "Missing required parameter" in (tui_stub.last_error or "")  # Error set
    assert tui_stub.last_result is None  # No call made


def test_execute_uses_env_autofill(tui_stub, make_item, monkeypatch: pytest.MonkeyPatch) -> None:
    """Parameters present in environment are autofilled and not prompted."""
    monkeypatch.setenv("org_id", "envOrg")  # .env autofill source
    tui_stub.current_items = [make_item("function", "list", object=_api)]
    tui_stub.current_selection = 0
    _patch_input(monkeypatch, answers=[""])  # Only the 'limit' default
    _patch_keypress(monkeypatch)
    ItemExecutor(tui_stub).execute()  # Trigger
    assert tui_stub.last_result == {"org_id": "envOrg", "limit": 100}  # Env used


def test_execute_handles_keyboard_interrupt(tui_stub, make_item, monkeypatch: pytest.MonkeyPatch) -> None:
    """A KeyboardInterrupt during input cancels cleanly with a message."""

    def _interrupt(_prompt: str = "") -> str:
        raise KeyboardInterrupt()  # Force cancel

    monkeypatch.setattr(builtins, "input", _interrupt)  # Force interrupt
    _patch_keypress(monkeypatch)
    tui_stub.current_items = [make_item("function", "fn", object=_api)]
    tui_stub.current_selection = 0
    ItemExecutor(tui_stub).execute()  # Should not propagate
    assert tui_stub.last_result is None  # No result captured


def test_execute_handles_generic_exception(tui_stub, make_item, monkeypatch: pytest.MonkeyPatch) -> None:
    """A raising API call surfaces last_error and a stdout banner."""

    def _broken():  # zero-arg so no prompts run
        raise RuntimeError("boom")

    tui_stub.current_items = [make_item("function", "broken", object=_broken)]
    tui_stub.current_selection = 0
    _patch_keypress(monkeypatch)
    ItemExecutor(tui_stub).execute()  # Trigger
    assert tui_stub.last_error == "boom"  # Error captured


def test_execute_autofills_apisession(tui_stub, make_item, monkeypatch: pytest.MonkeyPatch) -> None:
    """A 'mist_session' parameter is autofilled from tui.apisession."""
    sentinel = MagicMock(name="session")  # Distinct session sentinel
    tui_stub.apisession = sentinel  # Wire shared session

    def _needs_session(mist_session):
        return {"got": mist_session}

    tui_stub.current_items = [make_item("function", "fn", object=_needs_session)]
    tui_stub.current_selection = 0
    _patch_keypress(monkeypatch)
    ItemExecutor(tui_stub).execute()  # Trigger
    assert tui_stub.last_result == {"got": sentinel}  # Session injected


def test_inject_session_errors_when_session_missing(tui_stub, make_item) -> None:
    """Missing apisession sets last_error and returns False."""
    tui_stub.apisession = None  # No session
    ok = ItemExecutor(tui_stub)._inject_session("mist_session", {})  # Direct call
    assert ok is False  # Reports failure
    assert tui_stub.last_error == "API session not initialized"


def test_result_preview_none_and_primitives() -> None:
    """_ResultPreview.build covers all primitive branches."""
    assert _ResultPreview.build(None) == "None"  # None branch
    assert _ResultPreview.build(7) == "int: 7"  # int branch
    assert _ResultPreview.build(True) == "bool: True"  # bool branch
    assert _ResultPreview.build(2.5) == "float: 2.5"  # float branch
    assert _ResultPreview.build("short") == "String: short"  # short string
    long_str = "x" * 250  # 250-char string -> truncated branch
    out = _ResultPreview.build(long_str)
    assert "String (250 chars):" in out and out.endswith("...")


def test_result_preview_sequence_and_dict() -> None:
    """Sequence + dict preview branches produce the expected summaries."""
    empty_list = _ResultPreview.build([])  # Empty list branch
    assert "empty" in empty_list
    short_list = _ResultPreview.build([1, 2])  # Short list path
    assert "with 2 items" in short_list
    long_list = _ResultPreview.build(list(range(10)))  # Long list path
    assert "showing first 3" in long_list
    empty_dict = _ResultPreview.build({})  # Empty dict branch
    assert "empty" in empty_dict
    small_dict = _ResultPreview.build({"a": 1, "b": 2})  # Small dict branch
    assert "with 2 keys" in small_dict
    big_dict = _ResultPreview.build({f"k{i}": i for i in range(10)})  # Big dict path
    assert "first 5" in big_dict


def test_result_preview_generic_object_fallback() -> None:
    """Non-standard objects fall back to repr() with a length cap."""

    class _Obj:
        def __repr__(self) -> str:  # pragma: no cover - tiny passthrough
            return "x" * 300  # > 200 char cap

    preview = _ResultPreview.build(_Obj())  # Generic branch
    assert preview.startswith("_Obj: ")  # Type prefix
    assert preview.endswith("...")  # Truncation indicator
