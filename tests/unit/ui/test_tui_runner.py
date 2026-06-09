"""Unit tests for src/ui/runtime/tui_runner.py."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from src.ui.runtime.tui_runner import TuiRunner


class _FakeLive:
    """Minimal context-manager stand-in for rich.live.Live."""

    def __init__(self, *_a: Any, **_kw: Any) -> None:
        """Capture constructor args (unused) and record update calls."""
        self.updates: list[Any] = []  # Tracks update() invocations

    def __enter__(self) -> _FakeLive:
        """Enter context: returns the live instance for the with-block."""
        return self  # Mimic Rich Live ctx-manager protocol

    def __exit__(self, *exc: Any) -> bool:
        """Exit context: never suppress exceptions."""
        return False

    def update(self, layout: Any) -> None:
        """Record a layout update for assertion."""
        self.updates.append(layout)


def _drive_runner(tui_stub, keys: list[str | None]) -> TuiRunner:
    """Wire ``tui_stub`` so the runner consumes ``keys`` and exits after them."""
    queue = list(keys)  # Mutable queue popped left-to-right

    def _poll() -> str | None:
        if not queue:  # Queue drained -> request quit and return None
            tui_stub.running = False  # Break loop
            return None
        return queue.pop(0)  # Otherwise emit next key

    tui_stub.check_keyboard_input = MagicMock(side_effect=_poll)  # Wire poll
    tui_stub.handle_input = MagicMock()  # Receives keystrokes
    tui_stub.create_layout = MagicMock(return_value="<layout>")  # Stable layout
    tui_stub.Live = _FakeLive  # Inject context-manager stand-in
    return TuiRunner(tui_stub)  # Ready-to-run runner


def test_run_unix_path_drives_discover_and_loop(tui_stub) -> None:
    """Unix run() calls discover, enters Live loop, then restores terminal."""
    tui_stub.IS_WINDOWS = False  # Unix branch
    tui_stub._discover_current_level = MagicMock()  # Track the discover call
    runner = _drive_runner(tui_stub, keys=["a", "b"])  # Two keys then auto-quit
    runner.run()  # Drive the full lifecycle
    assert tui_stub._discover_current_level.called  # Discovery ran once
    assert tui_stub.handle_input.call_count == 2  # Both keys dispatched
    assert tui_stub.tty.setcbreak.called  # Raw mode entered
    assert tui_stub.termios.tcsetattr.called  # Restore performed


def test_run_windows_path_skips_termios(tui_stub) -> None:
    """Windows run() does not touch termios/tty."""
    tui_stub.IS_WINDOWS = True  # Windows branch
    tui_stub._discover_current_level = MagicMock()  # Track discover
    runner = _drive_runner(tui_stub, keys=[None])  # One empty poll then quit
    runner.run()  # Run lifecycle
    assert not tui_stub.tty.setcbreak.called  # Skipped on Windows
    assert not tui_stub.termios.tcsetattr.called  # Skipped on Windows


def test_run_propagates_critical_error(tui_stub) -> None:
    """A render-loop exception bubbles, but terminal is still restored."""
    tui_stub.IS_WINDOWS = False  # Unix path so restore is exercised
    tui_stub._discover_current_level = MagicMock(side_effect=RuntimeError("boom"))
    tui_stub.Live = _FakeLive  # Stub Live for safety
    runner = TuiRunner(tui_stub)  # Construct runner
    with pytest.raises(RuntimeError, match="boom"):  # Original error propagates
        runner.run()
    assert tui_stub.termios.tcsetattr.called  # finally-block still restored terminal


def test_render_loop_breaks_when_quit_requested(tui_stub) -> None:
    """When handle_input flips ``running`` False, the loop ends cleanly."""

    def _flip_off(key: str) -> None:  # pragma: no cover - tiny callback
        tui_stub.running = False  # Quit immediately after first key

    tui_stub.handle_input = MagicMock(side_effect=_flip_off)  # Wire side effect
    tui_stub.check_keyboard_input = MagicMock(return_value="q")  # Always return 'q'
    tui_stub.create_layout = MagicMock(return_value="<layout>")  # Stable layout
    tui_stub.Live = _FakeLive  # Stub Live
    runner = TuiRunner(tui_stub)  # Construct
    runner._render_loop()  # Run only the inner loop (bypass setup)
    tui_stub.handle_input.assert_called_once_with("q")  # Single dispatch


def test_teardown_terminal_swallows_restore_failure(tui_stub) -> None:
    """Restore errors must not propagate from teardown."""
    tui_stub.IS_WINDOWS = False  # Unix path
    tui_stub.termios.tcsetattr.side_effect = RuntimeError("restore-fail")  # Force failure
    TuiRunner(tui_stub)._teardown_terminal()  # Should not raise


def test_teardown_terminal_windows_noop(tui_stub) -> None:
    """Windows teardown does nothing and never calls termios."""
    tui_stub.IS_WINDOWS = True  # Windows branch
    TuiRunner(tui_stub)._teardown_terminal()  # No-op call
    tui_stub.termios.tcsetattr.assert_not_called()  # Never touched
