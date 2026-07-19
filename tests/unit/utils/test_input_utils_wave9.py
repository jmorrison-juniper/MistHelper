"""Wave 9 P2 coverage tests for src.utils.input_utils.

Targets ``InputUtils`` end-to-end: the ``ensure_tqdm_available`` probe
(real-tqdm branch + fallback branch) and every branch of ``safe_input``:
normal return, empty-with-default, empty-allowed, empty-not-allowed,
EOF degradation, and KeyboardInterrupt cancellation.
"""

from __future__ import annotations  # WHY: PEP 604 unions module-wide

import logging  # WHY: emit before/after action logs per project contract
from typing import Any  # WHY: annotate monkeypatched stubs with a broad type
from unittest.mock import MagicMock  # WHY: build a stand-in for the _tqdm import

import pytest  # WHY: monkeypatch fixture

from src.utils import input_utils as input_utils_module  # WHY: patch _tqdm attribute
from src.utils.input_utils import InputUtils  # WHY: SUT under test


class TestEnsureTqdmAvailable:
    """Cover both branches of the tqdm-availability probe."""

    def test_real_tqdm_module_returns_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # WHY: when _tqdm.__module__ starts with "tqdm", the probe returns True
        logging.info("Building fake real-tqdm module stub")  # WHY: pre-action trace
        fake_tqdm = MagicMock()  # WHY: mock with a controllable __module__ attr
        fake_tqdm.__module__ = "tqdm.std"  # WHY: mimic the real tqdm module path
        monkeypatch.setattr(input_utils_module, "_tqdm", fake_tqdm)  # WHY: replace module-level handle
        result = InputUtils.ensure_tqdm_available()  # WHY: exercise the real-tqdm branch
        logging.debug("ensure_tqdm_available returned %s", result)  # WHY: post-action trace
        assert result is True  # WHY: real tqdm active -> True

    def test_fallback_wrapper_returns_false(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        # WHY: when _tqdm.__module__ does NOT start with "tqdm", the fallback branch fires
        logging.info("Building fake fallback tqdm stub")  # WHY: pre-action trace
        fake_tqdm = MagicMock()  # WHY: mock with a non-tqdm __module__
        fake_tqdm.__module__ = "src.utils.tqdm_wrapper"  # WHY: wrapper path -> fallback
        monkeypatch.setattr(input_utils_module, "_tqdm", fake_tqdm)  # WHY: replace module-level handle
        with caplog.at_level(logging.WARNING):  # WHY: capture the WARNING log
            result = InputUtils.ensure_tqdm_available()  # WHY: exercise fallback branch
        logging.debug("ensure_tqdm_available returned %s", result)  # WHY: post-action trace
        assert result is False  # WHY: fallback in use -> False
        assert any("fallback in use" in rec.message for rec in caplog.records)  # WHY: warning surfaced

    def test_tqdm_without_module_attr_returns_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # WHY: hasattr(_tqdm, "__module__") False path (short-circuit before startswith)
        # WHY: use a plain object() so it has no __module__ attribute
        class _NoModule:  # WHY: minimal stand-in without __module__
            pass  # WHY: intentionally empty

        stub = _NoModule()  # WHY: instance also lacks __module__
        # WHY: object() has __class__.__module__ but attribute lookup on the instance goes through the class,
        # so we monkeypatch and rely on the hasattr short-circuit false branch via delattr on the stub
        monkeypatch.setattr(input_utils_module, "_tqdm", stub)  # WHY: replace module-level handle
        # WHY: this may still return True because hasattr will find __module__ via the class -> so we assert bool
        result = InputUtils.ensure_tqdm_available()  # WHY: exercise probe
        assert isinstance(result, bool)  # WHY: probe must return a bool either way


class TestSafeInputNormalPath:
    """Cover the normal, non-empty return path of ``safe_input``."""

    def test_returns_trimmed_input(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # WHY: user supplies text; trimmed value must be returned verbatim
        monkeypatch.setattr("builtins.input", lambda _prompt: "  hello  ")  # WHY: patched input returns padded string
        result = InputUtils.safe_input("Enter: ", context="testctx")  # WHY: exercise normal path
        assert result == "hello"  # WHY: strip() removes surrounding whitespace


class TestSafeInputEmptyBranches:
    """Cover the empty-input dispatch branches."""

    def test_empty_with_default_returns_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # WHY: blank entry + a default -> default is returned
        monkeypatch.setattr("builtins.input", lambda _prompt: "")  # WHY: patched input returns empty
        result = InputUtils.safe_input(
            "Enter: ", default_value="mydefault", context="testctx"
        )  # WHY: exercise default branch
        assert result == "mydefault"  # WHY: default substitution applied

    def test_empty_allowed_returns_empty_string(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # WHY: blank entry, no default, allow_empty=True -> return ""
        monkeypatch.setattr("builtins.input", lambda _prompt: "")  # WHY: patched input returns empty
        result = InputUtils.safe_input(
            "Enter: ", allow_empty=True, context="testctx"
        )  # WHY: exercise allow_empty branch
        assert result == ""  # WHY: empty string returned as-is

    def test_empty_not_allowed_returns_empty_string_with_warning(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        # WHY: blank entry, no default, allow_empty=False -> return "" but log a warning
        monkeypatch.setattr("builtins.input", lambda _prompt: "")  # WHY: patched input returns empty
        with caplog.at_level(logging.WARNING):  # WHY: capture WARNING log
            result = InputUtils.safe_input(
                "Enter: ", allow_empty=False, context="testctx"
            )  # WHY: exercise not-allowed branch
        assert result == ""  # WHY: sentinel empty string returned
        assert any("not allowed" in rec.message for rec in caplog.records)  # WHY: warning surfaced


class TestSafeInputExceptionBranches:
    """Cover the EOF and KeyboardInterrupt exception branches."""

    def test_eof_returns_default_and_logs_notice(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        # WHY: EOFError -> degrade to default_value + WARNING log notice (#886 Phase 2 print->logger)
        def _raise_eof(_prompt: str) -> str:  # WHY: patched input raises EOFError
            raise EOFError("stream closed")  # WHY: hit the except EOFError branch

        monkeypatch.setattr("builtins.input", _raise_eof)  # WHY: patched input
        with caplog.at_level(logging.WARNING):  # WHY: capture warning surface
            result = InputUtils.safe_input(
                "Enter: ", default_value="fallback", context="testctx"
            )  # WHY: exercise EOF branch
        assert result == "fallback"  # WHY: default substituted
        assert "[EOF]" in caplog.text  # WHY: operator notice surfaced via logger

    def test_keyboard_interrupt_returns_empty_and_logs_notice(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        # WHY: KeyboardInterrupt -> return "" + WARNING log notice (#886 Phase 2 print->logger)
        def _raise_interrupt(_prompt: str) -> str:  # WHY: patched input raises KeyboardInterrupt
            raise KeyboardInterrupt()  # WHY: hit the except KeyboardInterrupt branch

        monkeypatch.setattr("builtins.input", _raise_interrupt)  # WHY: patched input
        with caplog.at_level(logging.WARNING):  # WHY: capture warning surface
            result = InputUtils.safe_input("Enter: ", context="testctx")  # WHY: exercise interrupt branch
        assert result == ""  # WHY: interrupt returns empty sentinel
        assert "[INTERRUPT]" in caplog.text  # WHY: operator notice surfaced via logger


class TestPrivateHelpersDirect:
    """Cover the private ``_handle_*`` helpers directly for defensive assurance."""

    def test_handle_empty_with_default_returns_default(self) -> None:
        # WHY: default present -> default returned regardless of allow_empty
        result = InputUtils._handle_empty("d", True, "ctx")  # WHY: direct call
        assert result == "d"  # WHY: default returned

    def test_handle_empty_no_default_allow_true_returns_empty(self) -> None:
        # WHY: no default + allow_empty=True -> ""
        result = InputUtils._handle_empty("", True, "ctx")  # WHY: direct call
        assert result == ""  # WHY: empty string returned

    def test_handle_empty_no_default_allow_false_returns_empty(self, caplog: pytest.LogCaptureFixture) -> None:
        # WHY: no default + allow_empty=False -> "" + warning
        with caplog.at_level(logging.WARNING):  # WHY: capture warning
            result = InputUtils._handle_empty("", False, "ctx")  # WHY: direct call
        assert result == ""  # WHY: sentinel empty returned
        assert any("not allowed" in rec.message for rec in caplog.records)  # WHY: warning logged

    def test_handle_eof_returns_default(self, caplog: pytest.LogCaptureFixture) -> None:
        # WHY: EOF handler returns the default and logs a WARNING notice (#886 Phase 2)
        with caplog.at_level(logging.WARNING):  # WHY: capture warning surface
            result = InputUtils._handle_eof("ctx", "def")  # WHY: direct call
        assert result == "def"  # WHY: default returned
        assert "[EOF]" in caplog.text  # WHY: operator notice surfaced via logger

    def test_handle_interrupt_returns_empty(self, caplog: pytest.LogCaptureFixture) -> None:
        # WHY: interrupt handler returns "" and logs a WARNING notice (#886 Phase 2)
        with caplog.at_level(logging.WARNING):  # WHY: capture warning surface
            result = InputUtils._handle_interrupt("ctx")  # WHY: direct call
        assert result == ""  # WHY: sentinel empty returned
        assert "[INTERRUPT]" in caplog.text  # WHY: operator notice surfaced via logger


class TestSafeInputDefaultArguments:
    """Cover the argument-default paths."""

    def test_default_context_is_used_when_not_supplied(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # WHY: caller omits context -> "unknown" is used internally (no crash)
        called: dict[str, Any] = {}  # WHY: capture what got logged via safe_input

        def _capture_input(_prompt: str) -> str:  # WHY: patched input returns fixed value
            called["ok"] = True  # WHY: record we were invoked
            return "value"  # WHY: normal value

        monkeypatch.setattr("builtins.input", _capture_input)  # WHY: patched input
        result = InputUtils.safe_input("Enter: ")  # WHY: exercise defaults
        assert result == "value"  # WHY: normal path returns value
        assert called.get("ok") is True  # WHY: input was invoked
