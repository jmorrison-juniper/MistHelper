"""Unit tests for src.refactors.keyboard_listener.

Wave 13 P2 coverage lift — KeyboardListener.listen is a no-op stub
preserving the legacy signature. Cover the pass-through invocation
with both positional and keyword args to close the 62% gap in one
file.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on older type checkers

from src.refactors.keyboard_listener import KeyboardListener  # WHY: subject under test


def test_listen_returns_none_with_no_args(caplog) -> None:
    """listen() with no arguments returns None and emits info/debug logs."""
    listener = KeyboardListener()  # WHY: instance-based API
    with caplog.at_level("DEBUG"):  # WHY: capture both info and debug lines
        listener.listen()  # WHY: exercise the no-op path (returns None; mypy short-circuits assignment)
    messages = [rec.message for rec in caplog.records]  # WHY: collect all messages for assertions
    assert any("KeyboardListener.listen invoked" in m for m in messages)  # WHY: info trace preserved
    assert any("returning None" in m for m in messages)  # WHY: debug trace preserved


def test_listen_accepts_positional_and_keyword_args(caplog) -> None:
    """listen() accepts arbitrary *args/**kwargs without raising and returns None."""
    listener = KeyboardListener()
    with caplog.at_level("DEBUG"):
        listener.listen("first", "second", on_release=lambda: None, delay_second_char=0)  # WHY: no-op returns None
    messages = [rec.message for rec in caplog.records]
    assert any("args_len=2" in m for m in messages)  # WHY: positional arg count logged
    assert any("delay_second_char" in m or "on_release" in m for m in messages)  # WHY: kwargs surface in log
