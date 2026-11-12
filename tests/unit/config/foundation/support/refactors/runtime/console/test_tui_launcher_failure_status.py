"""Verify accurate TUI completion reports without external services or a real TUI."""

from __future__ import annotations

import logging
import socket
import sys
from collections.abc import Iterator
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock

import pytest

from src.foundation.support.refactors import tui_launcher


@pytest.fixture
def offline_launcher(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> Iterator[SimpleNamespace]:
    """Provide isolated logging and mocked runtime state while blocking network access."""
    blocked = Mock(side_effect=AssertionError("Network access is forbidden"))  # Fail on accidental external access.
    for name in ("socket", "create_connection", "getaddrinfo", "gethostbyname", "gethostbyname_ex", "gethostbyaddr"):
        monkeypatch.setattr(socket, name, blocked)  # Prevent socket and DNS access in each launcher path.
    runtime = SimpleNamespace(apisession=Mock(spec=object), args=SimpleNamespace(debug=False))  # Avoid real sessions.
    runtime.initialize_mist_session = Mock(return_value=False)  # Keep session initialization offline.
    monkeypatch.setattr(
        tui_launcher, "_resolve_runtime_dependencies", Mock(return_value=SimpleNamespace(misthelper_module=runtime))
    )
    root = logging.getLogger()  # Exercise real handler restoration on an isolated handler list.
    console = logging.StreamHandler()  # Represent the console handler that the TUI suppresses.
    file_handler = Mock(spec=logging.FileHandler)  # Retain a file handler without opening a file.
    monkeypatch.setattr(root, "handlers", [console, file_handler])  # Preserve the original list through teardown.
    monkeypatch.setattr(
        tui_launcher.logger, "handlers", [caplog.handler]
    )  # Capture records while root handlers detach.
    monkeypatch.setattr(tui_launcher.logger, "propagate", False)  # Avoid any real root-handler output.
    caplog.set_level(logging.DEBUG, logger=tui_launcher.__name__)  # Include neutral completion traces.
    launcher = tui_launcher.TUILauncher()  # Use the real orchestration and helper methods.
    run = Mock()  # Replace the event loop so no interactive operation starts.
    monkeypatch.setattr(launcher, "_run_tui", run)  # Keep each outcome under test control.
    yield SimpleNamespace(launcher=launcher, runtime=runtime, run=run, root=root, console=console, file=file_handler)
    blocked.assert_not_called()  # Prove the tested paths did not even attempt a connection.
    console.close()  # Release the test-owned handler without affecting other logging.


class TestTUILaunchCompletionStatus:
    """Check all completion outcomes and preserve the common menu return path."""

    @pytest.mark.parametrize("debug", [False, True])
    @pytest.mark.parametrize("outcome", [None, RuntimeError("synthetic failure"), KeyboardInterrupt()])
    def test_completion_outcome(
        self,
        offline_launcher: SimpleNamespace,
        caplog: pytest.LogCaptureFixture,
        outcome: BaseException | None,
        debug: bool,
    ) -> None:
        """Only a normal return reports success, and every entered TUI restores handlers."""
        state = offline_launcher  # Keep all test dependencies in the isolated fixture.
        state.runtime.args.debug = debug  # Exercise both timestamp branches.
        state.run.side_effect = outcome  # Simulate completion, an ordinary exception, or interruption.
        assert state.launcher.launch() is None  # The caller returns to the menu without an exception.
        messages = [record.getMessage() for record in caplog.records]  # Examine actual formatted log records.
        assert messages.count("TUI_MODE: TUI mode completed successfully") == int(outcome is None)
        assert sum("TUI_MODE: Fatal error" in message for message in messages) == int(isinstance(outcome, Exception))
        assert messages.count("TUI_MODE: User interrupted with Ctrl+C") == int(isinstance(outcome, KeyboardInterrupt))
        assert messages.count("\n>> Returned from TUI mode to main menu") == 1
        assert sum("TUI_DEBUG:" in message for message in messages) == int(debug)
        assert state.root.handlers.count(state.file) == 1  # The file handler remains attached exactly once.
        assert state.root.handlers.count(state.console) == 1  # The console handler returns without duplication.
        state.run.assert_called_once_with()  # Each launch starts the mocked TUI once.
        state.runtime.initialize_mist_session.assert_not_called()  # A ready session requires no initialization.
        if isinstance(outcome, Exception):  # Preserve the fatal error and its traceback for diagnosis.
            fatal = [record for record in caplog.records if record.levelno == logging.ERROR]
            assert len(fatal) == 1 and fatal[0].exc_info is not None
            assert fatal[0].exc_info[1] is outcome
            assert "\n[ERROR] TUI mode crashed: synthetic failure" in messages
        if outcome is not None:
            assert "TUI_MODE: launch() finished cleanly" not in messages

    def test_restore_precedes_completion_reports(
        self, offline_launcher: SimpleNamespace, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Restore the console before success or menu return records reach the logger."""
        state = offline_launcher  # Use real suppression and restoration with no global logging side effects.
        original_info = tui_launcher.logger.info  # Observe records without replacing their behavior.

        def verify_report(message: str, *arguments: object, **keywords: object) -> None:
            """Check console availability at each final report."""
            if "completed successfully" in message or "Returned from TUI" in message:
                assert state.console in state.root.handlers
            original_info(message, *arguments, **keywords)  # Preserve capture of the actual messages.

        def verify_suppression() -> None:
            """Keep the console detached and the file handler attached during the TUI run."""
            assert state.console not in state.root.handlers
            assert state.file in state.root.handlers

        monkeypatch.setattr(tui_launcher.logger, "info", verify_report)  # Inspect state when reports occur.
        state.run.side_effect = verify_suppression
        assert state.launcher.launch() is None  # The normal path must return without leaking errors.
        state.run.assert_called_once_with()
        assert not [record for record in caplog.records if record.levelno >= logging.ERROR]
        assert "TUI_MODE: TUI mode completed successfully" in [record.getMessage() for record in caplog.records]

    def test_session_initialization_failure(
        self, offline_launcher: SimpleNamespace, caplog: pytest.LogCaptureFixture
    ) -> None:
        """An unavailable session prevents TUI entry and success reporting."""
        state = offline_launcher  # The initializer is already mocked to fail safely.
        handlers_before = list(state.root.handlers)  # Include pytest's own per-test capture handlers.
        state.runtime.apisession = None  # Require initialization without contacting Mist.
        assert state.launcher.launch() is None
        state.run.assert_not_called()  # No event loop starts without a session.
        state.runtime.initialize_mist_session.assert_called_once_with()
        messages = [record.getMessage() for record in caplog.records]
        assert "TUI_MODE: Could not initialize API session" in messages
        assert "TUI_MODE: TUI mode completed successfully" not in messages
        assert "\n>> Returned from TUI mode to main menu" not in messages
        assert state.root.handlers == handlers_before  # Early return must not alter logging.

    @pytest.mark.parametrize(
        "outcomes", [[None, RuntimeError("synthetic failure")], [RuntimeError("synthetic failure"), None]]
    )
    def test_repeated_launches(
        self, offline_launcher: SimpleNamespace, caplog: pytest.LogCaptureFixture, outcomes: list[Exception | None]
    ) -> None:
        """A previous launch cannot change the completion result of the next launch."""
        state = offline_launcher  # Reuse the same launcher to detect retained status.
        state.run.side_effect = outcomes  # Exercise success before failure and failure before success.
        for outcome in outcomes:  # Inspect each call separately to prevent an aggregate false positive.
            caplog.clear()  # Discard records from the previous call.
            assert state.launcher.launch() is None
            messages = [record.getMessage() for record in caplog.records]
            assert messages.count("TUI_MODE: TUI mode completed successfully") == int(outcome is None)
            assert messages.count("\n>> Returned from TUI mode to main menu") == 1
            assert state.root.handlers.count(state.console) == 1
            assert state.root.handlers.count(state.file) == 1
        assert state.run.call_count == 2  # Both independent calls enter the mocked event loop.

    @pytest.mark.parametrize("debug", [False, True])
    @pytest.mark.parametrize("outcome", [None, RuntimeError("synthetic failure"), KeyboardInterrupt()])
    def test_real_run_helper_with_mocked_tui(
        self,
        offline_launcher: SimpleNamespace,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
        debug: bool,
        outcome: BaseException | None,
    ) -> None:
        """Integrate launch and its run helper without importing or starting a real TUI."""
        from src.interfaces.visualization import ui

        state = offline_launcher
        state.runtime.args.debug = debug
        instance = SimpleNamespace(apisession=None, run=Mock(side_effect=outcome))
        factory = Mock(return_value=instance)  # Prevent constructor side effects and credential loading.
        module = ModuleType("src.interfaces.visualization.ui.tui")
        module.MistHelperTUI = factory
        monkeypatch.setitem(sys.modules, module.__name__, module)
        monkeypatch.setattr(ui, "tui", module, raising=False)  # Keep the lazy import under test offline.
        monkeypatch.setattr(state.launcher, "_run_tui", tui_launcher.TUILauncher._run_tui.__get__(state.launcher))
        assert state.launcher.launch() is None
        factory.assert_called_once_with(debug_mode=debug)
        instance.run.assert_called_once_with()
        assert instance.apisession is state.runtime.apisession
        messages = [record.getMessage() for record in caplog.records]
        assert messages.count("TUI_MODE: TUI mode completed successfully") == int(outcome is None)
        assert messages.count("\n>> Returned from TUI mode to main menu") == 1
        assert state.root.handlers.count(state.console) == 1
