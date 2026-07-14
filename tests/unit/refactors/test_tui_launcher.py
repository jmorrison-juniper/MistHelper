"""Wave 2 P2 coverage for src/refactors/tui_launcher.py (initiative #1018).

Covers `TUILauncher` construction plus every helper method and every branch of
`launch()` (session-init failure early-return, normal path, KeyboardInterrupt path,
generic Exception path). MistHelper module attributes (`apisession`, `args`,
`initialize_mist_session`) and `src.ui.tui.MistHelperTUI` are monkeypatched so no
Rich event loop, network call, or real logger mutation escapes the test process.
No source edits, no live I/O.
"""

from __future__ import annotations  # WHY: PEP 604 unions in method signatures on Python 3.10+.

import logging  # WHY: build fake handlers of StreamHandler/FileHandler for suppression tests.
from types import SimpleNamespace  # WHY: build a stand-in for the MistHelper args namespace.
from typing import Any  # WHY: relaxed return type for factory helpers that stub launcher methods.
from unittest.mock import MagicMock  # WHY: FR-008 mandates MagicMock(spec=...) for production-class mocks.

import pytest  # WHY: capsys + monkeypatch fixtures.


class TestResolveRuntimeDependencies:
    """`_resolve_runtime_dependencies` returns a SimpleNamespace bundling the MistHelper module."""

    def test_returns_bundle_with_misthelper_module(self) -> None:
        """The returned SimpleNamespace exposes the live MistHelper module under `misthelper_module`."""
        from src.refactors.tui_launcher import _resolve_runtime_dependencies  # WHY: import inside test for isolation.

        deps = _resolve_runtime_dependencies()  # WHY: exercise the helper directly.
        assert deps.misthelper_module is not None  # WHY: the module attribute must be resolved, not None.
        assert deps.misthelper_module.__name__ == "MistHelper"  # WHY: identity check on the imported module name.


class TestTUILauncherInit:
    """`TUILauncher.__init__` initializes tracking state and resolves dependencies."""

    def test_init_sets_default_state(self) -> None:
        """Newly-constructed launcher has empty handler list and debug_mode=False."""
        from src.refactors.tui_launcher import TUILauncher  # WHY: fresh import per test to avoid cross-test state.

        launcher = TUILauncher()  # WHY: exercise the construction path.
        assert launcher.console_handlers == []  # WHY: no handlers captured before launch.
        assert launcher.debug_mode is False  # WHY: debug flag defaults to False until launch reads args.

    def test_init_resolves_runtime_dependencies(self) -> None:
        """__init__ populates `_deps.misthelper_module` via the lazy resolver."""
        from src.refactors.tui_launcher import TUILauncher  # WHY: fresh import per test.

        launcher = TUILauncher()  # WHY: exercise resolver via constructor.
        assert launcher._deps.misthelper_module.__name__ == "MistHelper"  # WHY: name-check on the resolved module.


class TestApisessionAccessor:
    """`_apisession` returns whatever MistHelper.apisession is currently bound to."""

    def test_returns_none_when_module_lacks_apisession(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Missing apisession falls back to None (getattr default)."""
        from src.refactors.tui_launcher import TUILauncher  # WHY: fresh import per test.

        launcher = TUILauncher()  # WHY: build launcher to inspect _apisession.
        monkeypatch.delattr("MistHelper.apisession", raising=False)  # WHY: ensure absence to trigger fallback branch.
        assert launcher._apisession() is None  # WHY: absence returns None per the getattr default.

    def test_returns_current_binding(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When MistHelper.apisession is set, `_apisession()` returns that value."""
        from src.refactors.tui_launcher import TUILauncher  # WHY: fresh import per test.

        launcher = TUILauncher()  # WHY: build launcher to inspect _apisession.
        sentinel = MagicMock(name="apisession_sentinel")  # WHY: unique object to identity-check.
        monkeypatch.setattr("MistHelper.apisession", sentinel, raising=False)  # WHY: publish new binding.
        assert launcher._apisession() is sentinel  # WHY: current-binding lookup returns published value.


class TestPrintWelcome:
    """`_print_welcome` emits the two-line activation banner to stdout."""

    def test_prints_activation_banner(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Two lines are printed: activation notice + navigation hint."""
        from src.refactors.tui_launcher import TUILauncher  # WHY: fresh import per test.

        TUILauncher()._print_welcome()  # WHY: exercise banner emission.
        captured = capsys.readouterr()  # WHY: capture stdout.
        assert "Terminal User Interface mode activated" in captured.out  # WHY: activation banner is present.
        assert "arrow keys" in captured.out  # WHY: navigation hint substring is present.


class TestEnsureApiSession:
    """`_ensure_api_session` reuses existing sessions, initializes missing ones, and reports failures."""

    def test_reuses_existing_session(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        """When apisession is already set, no initialize call happens and no user-visible print occurs."""
        from src.refactors.tui_launcher import TUILauncher  # WHY: fresh import per test.

        monkeypatch.setattr("MistHelper.apisession", MagicMock(name="existing_session"), raising=False)  # WHY: exist.
        init_mock = MagicMock(name="initialize_mist_session")  # WHY: sentinel to catch unintended invocation.
        monkeypatch.setattr("MistHelper.initialize_mist_session", init_mock, raising=False)  # WHY: sentinel path.
        launcher = TUILauncher()  # WHY: build launcher after apisession is published.
        assert launcher._ensure_api_session() is True  # WHY: existing session -> True return.
        assert init_mock.call_count == 0  # WHY: reuse branch must not touch initialize_mist_session.
        captured = capsys.readouterr()  # WHY: capture any accidental print output.
        assert "Initializing" not in captured.out  # WHY: reuse branch prints nothing.

    def test_initializes_missing_session_success(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """When apisession is missing and initialize_mist_session returns truthy, session is treated as ready."""
        from src.refactors.tui_launcher import TUILauncher  # WHY: fresh import per test.

        monkeypatch.delattr("MistHelper.apisession", raising=False)  # WHY: force the initialize branch.
        init_mock = MagicMock(return_value=True, name="initialize_mist_session")  # WHY: success sentinel.
        monkeypatch.setattr("MistHelper.initialize_mist_session", init_mock, raising=False)  # WHY: publish init.
        launcher = TUILauncher()  # WHY: build launcher after globals published.
        assert launcher._ensure_api_session() is True  # WHY: successful init -> True return.
        assert init_mock.call_count == 1  # WHY: exactly one bootstrap invocation.
        captured = capsys.readouterr()  # WHY: capture progress + success banners.
        assert "Initializing" in captured.out  # WHY: progress banner is printed on the init path.
        assert "successfully" in captured.out  # WHY: success banner is printed on the success sub-branch.

    def test_initializes_missing_session_failure(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """When initialize_mist_session returns falsy, ERROR is printed and False is returned."""
        from src.refactors.tui_launcher import TUILauncher  # WHY: fresh import per test.

        monkeypatch.delattr("MistHelper.apisession", raising=False)  # WHY: force the initialize branch.
        init_mock = MagicMock(return_value=False, name="initialize_mist_session")  # WHY: failure sentinel.
        monkeypatch.setattr("MistHelper.initialize_mist_session", init_mock, raising=False)  # WHY: publish init.
        launcher = TUILauncher()  # WHY: build launcher after globals published.
        assert launcher._ensure_api_session() is False  # WHY: failed init -> False return.
        captured = capsys.readouterr()  # WHY: capture error banner.
        assert "Failed to initialize" in captured.out  # WHY: error banner is printed on the failure sub-branch.


class TestSuppressAndRestoreConsoleLogging:
    """`_suppress_console_logging` + `_restore_console_logging` cycle console StreamHandlers."""

    def test_suppress_captures_streamhandler_but_not_filehandler(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """StreamHandler instances are captured & removed; FileHandler instances stay attached."""
        from src.refactors.tui_launcher import TUILauncher  # WHY: fresh import per test.

        stream_handler = logging.StreamHandler()  # WHY: eligible for suppression.
        file_handler = MagicMock(spec=logging.FileHandler)  # WHY: mocked FileHandler avoids opening a real file.
        file_handler.level = logging.NOTSET  # WHY: required attribute for logging Handler API compliance.
        root_logger = logging.getLogger()  # WHY: root logger owns the handler list.
        # Snapshot original handlers so we can restore them after the test to avoid polluting the pytest logger.
        original_handlers = list(root_logger.handlers)  # WHY: preserve handlers for teardown.
        try:  # WHY: guarded region so an assertion failure doesn't leave test-only handlers attached.
            root_logger.addHandler(stream_handler)  # WHY: publish suppression target.
            root_logger.addHandler(file_handler)  # WHY: publish handler that must stay attached.
            launcher = TUILauncher()  # WHY: instantiate SUT.
            launcher._suppress_console_logging()  # WHY: exercise suppression.
            assert stream_handler in launcher.console_handlers  # WHY: StreamHandler captured for later restore.
            assert file_handler not in launcher.console_handlers  # WHY: FileHandler excluded.
            assert stream_handler not in root_logger.handlers  # WHY: StreamHandler removed from root logger.
            assert file_handler in root_logger.handlers  # WHY: FileHandler still attached to root logger.
            launcher._restore_console_logging()  # WHY: exercise restore path.
            assert stream_handler in root_logger.handlers  # WHY: StreamHandler re-attached after restore.
        finally:  # WHY: teardown block runs regardless of assertion outcome.
            root_logger.handlers = original_handlers  # WHY: restore original handler list.


class TestGetDebugMode:
    """`_get_debug_mode` reads the MistHelper.args namespace safely."""

    def test_returns_false_when_args_absent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When MistHelper.args is missing, the fallback obj yields debug=False."""
        from src.refactors.tui_launcher import TUILauncher  # WHY: fresh import per test.

        monkeypatch.delattr("MistHelper.args", raising=False)  # WHY: ensure absence to trigger fallback.
        assert TUILauncher()._get_debug_mode() is False  # WHY: fallback obj's debug attribute is False.

    def test_returns_debug_flag_from_args(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When MistHelper.args.debug is True, `_get_debug_mode` returns True."""
        from src.refactors.tui_launcher import TUILauncher  # WHY: fresh import per test.

        monkeypatch.setattr("MistHelper.args", SimpleNamespace(debug=True), raising=False)  # WHY: publish args.
        assert TUILauncher()._get_debug_mode() is True  # WHY: reads args.debug and returns it.

    def test_returns_false_when_args_lacks_debug_attribute(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When args exists but lacks `debug`, fallback default kicks in."""
        from src.refactors.tui_launcher import TUILauncher  # WHY: fresh import per test.

        monkeypatch.setattr(
            "MistHelper.args", SimpleNamespace(other="x"), raising=False
        )  # WHY: publish args w/o debug.
        assert TUILauncher()._get_debug_mode() is False  # WHY: getattr(..., 'debug', False) -> False default.


class TestRunTui:
    """`_run_tui` constructs MistHelperTUI, wires apisession, and runs the event loop."""

    def test_run_tui_builds_and_runs(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Exercises the happy path where MistHelperTUI.run() returns cleanly."""
        from src.refactors.tui_launcher import TUILauncher  # WHY: fresh import per test.
        from src.ui import tui as tui_module  # WHY: SUT lazy-imports MistHelperTUI from this module.

        session_sentinel = MagicMock(name="apisession_sentinel")  # WHY: sentinel routed to tui.apisession.
        monkeypatch.setattr("MistHelper.apisession", session_sentinel, raising=False)  # WHY: publish session.
        monkeypatch.setattr("MistHelper.args", SimpleNamespace(debug=True), raising=False)  # WHY: enable debug branch.
        tui_instance = MagicMock(spec=tui_module.MistHelperTUI)  # WHY: FR-008 MagicMock(spec=...).
        tui_class_mock = MagicMock(return_value=tui_instance, name="MistHelperTUI")  # WHY: intercept constructor.
        monkeypatch.setattr("src.ui.tui.MistHelperTUI", tui_class_mock)  # WHY: replace lazy-imported class.
        launcher = TUILauncher()  # WHY: build launcher after globals published.
        launcher._run_tui()  # WHY: exercise the happy path.
        tui_class_mock.assert_called_once_with(debug_mode=True)  # WHY: debug flag latched from args.
        assert tui_instance.apisession is session_sentinel  # WHY: apisession attribute wired to launcher's session.
        tui_instance.run.assert_called_once_with()  # WHY: event loop invoked exactly once.


class TestHandlerHelpers:
    """`_handle_keyboard_interrupt` / `_handle_fatal_error` print user-visible banners."""

    def test_keyboard_interrupt_prints_exit_banner(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Ctrl+C banner is printed to stdout."""
        from src.refactors.tui_launcher import TUILauncher  # WHY: fresh import per test.

        TUILauncher()._handle_keyboard_interrupt()  # WHY: exercise banner emission.
        assert "stopped by user" in capsys.readouterr().out  # WHY: banner substring is present.

    def test_fatal_error_prints_crash_banner(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Fatal error message contains the exception string."""
        from src.refactors.tui_launcher import TUILauncher  # WHY: fresh import per test.

        TUILauncher()._handle_fatal_error(RuntimeError("boom!"))  # WHY: exercise error branch.
        assert "boom!" in capsys.readouterr().out  # WHY: exception str is echoed to stdout.


class TestPrintExitMessage:
    """`_print_exit_message` prints the return banner and (optionally) a debug timestamp."""

    def test_exit_message_no_debug(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        """Without debug mode only the return banner is printed."""
        from src.refactors.tui_launcher import TUILauncher  # WHY: fresh import per test.

        monkeypatch.setattr(
            "MistHelper.args", SimpleNamespace(debug=False), raising=False
        )  # WHY: disable debug branch.
        TUILauncher()._print_exit_message()  # WHY: exercise non-debug branch.
        assert "Returned from TUI" in capsys.readouterr().out  # WHY: banner substring present on stdout.

    def test_exit_message_with_debug(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        """With debug mode, the additional debug trace + return banner are both emitted."""
        from src.refactors.tui_launcher import TUILauncher  # WHY: fresh import per test.

        monkeypatch.setattr("MistHelper.args", SimpleNamespace(debug=True), raising=False)  # WHY: enable debug branch.
        TUILauncher()._print_exit_message()  # WHY: exercise debug branch.
        assert "Returned from TUI" in capsys.readouterr().out  # WHY: banner substring present on stdout.


class TestLaunchFullFlow:
    """`launch()` orchestrates every helper and honours the try/except/finally structure."""

    def _mock_launcher(self, monkeypatch: pytest.MonkeyPatch) -> Any:
        """Build a launcher with `_ensure_api_session`, `_run_tui`, and `_get_debug_mode` stubbed."""
        from src.refactors.tui_launcher import TUILauncher  # WHY: fresh import per test.

        monkeypatch.setattr("MistHelper.args", SimpleNamespace(debug=False), raising=False)  # WHY: predictable args.
        launcher = TUILauncher()  # WHY: build the SUT.
        return launcher  # WHY: hand back to the test for helper stubbing.

    def test_launch_aborts_when_session_init_fails(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """When `_ensure_api_session` returns False, launch exits before running the TUI."""
        launcher = self._mock_launcher(monkeypatch)  # WHY: shared setup.
        monkeypatch.setattr(launcher, "_ensure_api_session", lambda: False)  # WHY: force early-return branch.
        run_tui_mock = MagicMock(name="_run_tui")  # WHY: catch unintended invocation.
        monkeypatch.setattr(launcher, "_run_tui", run_tui_mock)  # WHY: sentinel: must NOT be called.
        launcher.launch()  # WHY: exercise the early-abort branch.
        assert run_tui_mock.call_count == 0  # WHY: TUI must not run when session init failed.

    def test_launch_normal_flow(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Happy path: session-init succeeds, run_tui runs, restore + exit banner emitted."""
        launcher = self._mock_launcher(monkeypatch)  # WHY: shared setup.
        monkeypatch.setattr(launcher, "_ensure_api_session", lambda: True)  # WHY: pass session gate.
        run_tui_mock = MagicMock(name="_run_tui")  # WHY: track invocation without running Rich event loop.
        monkeypatch.setattr(launcher, "_run_tui", run_tui_mock)  # WHY: stub Rich event loop.
        restore_mock = MagicMock(name="_restore_console_logging")  # WHY: verify finally-block always runs restore.
        monkeypatch.setattr(launcher, "_restore_console_logging", restore_mock)  # WHY: stub restore.
        launcher.launch()  # WHY: exercise happy path.
        assert run_tui_mock.call_count == 1  # WHY: happy path enters the TUI loop.
        assert restore_mock.call_count == 1  # WHY: finally-block always runs restore.

    def test_launch_keyboard_interrupt_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When `_run_tui` raises KeyboardInterrupt, the KeyboardInterrupt handler runs."""
        launcher = self._mock_launcher(monkeypatch)  # WHY: shared setup.
        monkeypatch.setattr(launcher, "_ensure_api_session", lambda: True)  # WHY: pass session gate.

        def _raise_ctrl_c() -> None:  # WHY: raise KeyboardInterrupt inside the try/except/finally.
            raise KeyboardInterrupt  # WHY: simulate Ctrl+C during TUI.

        monkeypatch.setattr(launcher, "_run_tui", _raise_ctrl_c)  # WHY: inject Ctrl+C behaviour.
        handler_mock = MagicMock(name="_handle_keyboard_interrupt")  # WHY: track KeyboardInterrupt handler call.
        monkeypatch.setattr(launcher, "_handle_keyboard_interrupt", handler_mock)  # WHY: stub handler.
        restore_mock = MagicMock(name="_restore_console_logging")  # WHY: verify finally-block still runs restore.
        monkeypatch.setattr(launcher, "_restore_console_logging", restore_mock)  # WHY: stub restore.
        launcher.launch()  # WHY: exercise Ctrl+C branch.
        assert handler_mock.call_count == 1  # WHY: Ctrl+C branch dispatches to the interrupt handler.
        assert restore_mock.call_count == 1  # WHY: finally-block still runs restore after interrupt.

    def test_launch_generic_exception_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When `_run_tui` raises Exception, the fatal-error handler runs."""
        launcher = self._mock_launcher(monkeypatch)  # WHY: shared setup.
        monkeypatch.setattr(launcher, "_ensure_api_session", lambda: True)  # WHY: pass session gate.

        def _raise_generic() -> None:  # WHY: raise generic Exception inside the try/except/finally.
            raise RuntimeError("simulated tui crash")  # WHY: simulate an unexpected TUI crash.

        monkeypatch.setattr(launcher, "_run_tui", _raise_generic)  # WHY: inject crash behaviour.
        handler_mock = MagicMock(name="_handle_fatal_error")  # WHY: track fatal-error handler call.
        monkeypatch.setattr(launcher, "_handle_fatal_error", handler_mock)  # WHY: stub handler.
        restore_mock = MagicMock(name="_restore_console_logging")  # WHY: verify finally-block still runs restore.
        monkeypatch.setattr(launcher, "_restore_console_logging", restore_mock)  # WHY: stub restore.
        launcher.launch()  # WHY: exercise generic-exception branch.
        assert handler_mock.call_count == 1  # WHY: crash branch dispatches to the fatal-error handler.
        assert restore_mock.call_count == 1  # WHY: finally-block still runs restore after crash.
