"""Unit tests for ``src.ui.tui.MistHelperTUI``.

Why: Un-omitting this thin-orchestrator TUI entrypoint from
``[tool.coverage.run].omit`` requires 100% line + branch coverage across the
construction pipeline (``_init_rich``, ``_init_platform_io``, ``_init_state``,
``_init_collaborators``), the Rich-missing ImportError fallback that calls
``sys.exit(1)``, the Windows-vs-Unix platform branch, the terminal-height
fallback path, and every thin delegate method that forwards to a collaborator.
Collaborators are patched at ``src.ui.tui`` import site so construction is
free of real Rich work while still exercising the wiring code paths.
"""

from __future__ import annotations

import builtins
import logging  # WHY (#886 Phase 2): capture Rich-missing error via caplog since tui.py now uses logging.error.
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Shared construction helper
# ---------------------------------------------------------------------------


def _patch_collaborators() -> Any:
    """Return a nested ``patch.multiple`` context stubbing every collaborator class.

    Why: MistHelperTUI's ``_init_collaborators`` instantiates 15 collaborator
    classes at construction time. Replacing each class with a ``MagicMock``
    lets tests drive ``__init__`` end-to-end without importing collaborator
    implementations or reaching real I/O.
    """
    return patch.multiple(
        "src.ui.tui",
        DotenvLoader=MagicMock(),
        LevelDiscoverer=MagicMock(),
        KeyPoller=MagicMock(),
        KeyboardDispatchTable=MagicMock(),
        FunctionExecutor=MagicMock(),
        ParameterCollector=MagicMock(),
        ItemExecutor=MagicMock(),
        APIResponseParser=MagicMock(),
        HierarchicalFormatter=MagicMock(),
        DebugResultSaver=MagicMock(),
        ResultsGridBuilder=MagicMock(),
        LayoutBuilder=MagicMock(),
        TuiRunner=MagicMock(),
    )


def _fake_unix_modules() -> dict[str, Any]:
    """Return fake select/termios/tty modules for injection into sys.modules.

    Why: The Unix branch of ``_init_platform_io`` imports select, termios, and
    tty inline. termios and tty are Unix-only C modules that don't exist on
    Windows CI runners; inject cheap SimpleNamespace stand-ins so the branch
    executes on any platform.
    """
    return {
        "termios": SimpleNamespace(tcgetattr=lambda _fd: None, tcsetattr=lambda *_a: None),
        "tty": SimpleNamespace(setcbreak=lambda _fd: None),
    }


def _construct(debug: bool = False, is_windows: bool = False) -> Any:
    """Construct a MistHelperTUI with all collaborators stubbed and platform selectable.

    Args:
        debug: Passed straight to ``MistHelperTUI(debug_mode=...)``.
        is_windows: When True, forces ``platform.system()`` to report Windows.

    Returns:
        A fully-constructed MistHelperTUI with mocked collaborators.
    """
    import sys as _sys

    from src.ui import tui as tui_module

    module_patch = (
        {"msvcrt": SimpleNamespace(kbhit=lambda: False, getch=lambda: b"")} if is_windows else _fake_unix_modules()
    )
    with (
        _patch_collaborators(),
        patch.object(tui_module.platform, "system", return_value="Windows" if is_windows else "Linux"),
        patch.dict(_sys.modules, module_patch),
    ):
        return tui_module.MistHelperTUI(debug_mode=debug)


# ---------------------------------------------------------------------------
# _init_rich — success + ImportError branch
# ---------------------------------------------------------------------------


class TestInitRich:
    """Cover the Rich lazy-import block in ``_init_rich``."""

    def test_success_caches_rich_classes(self):
        """Successful import assigns Rich classes/instances onto self."""
        tui = _construct()
        # Every Rich class is cached on the instance as an attribute.
        for name in ("Console", "Live", "Panel", "Table", "Layout", "box", "Syntax", "Markdown"):
            assert hasattr(tui, name)
        assert tui.console is not None  # Console instance created

    def test_import_error_triggers_sys_exit(self, caplog: pytest.LogCaptureFixture) -> None:
        """Missing Rich library aborts the process with sys.exit(1)."""
        # WHY (#886 Phase 2): tui.py now emits the diagnostic via logging.error, so assert via caplog.
        import sys as _sys

        from src.ui import tui as tui_module

        real_import = builtins.__import__

        def blocked_import(name, *args, **kwargs):
            if name.startswith("rich"):
                raise ImportError("blocked for test")
            return real_import(name, *args, **kwargs)

        with (
            _patch_collaborators(),
            patch.object(tui_module.platform, "system", return_value="Linux"),
            patch.dict(_sys.modules, _fake_unix_modules()),
            patch.object(builtins, "__import__", side_effect=blocked_import),
            caplog.at_level(logging.ERROR),
            pytest.raises(SystemExit) as exc_info,
        ):
            tui_module.MistHelperTUI()

        assert exc_info.value.code == 1
        assert "Rich library not available" in caplog.text


# ---------------------------------------------------------------------------
# _init_platform_io — Windows vs Unix branches
# ---------------------------------------------------------------------------


class TestInitPlatformIO:
    """Cover the platform branch in ``_init_platform_io``."""

    def test_unix_path_caches_select_termios_tty(self):
        """Non-Windows path caches select/termios/tty and sets old_terminal_settings None."""
        tui = _construct(is_windows=False)
        assert tui.IS_WINDOWS is False
        assert tui.select is not None
        assert tui.termios is not None
        assert tui.tty is not None
        assert tui.old_terminal_settings is None

    def test_windows_path_caches_msvcrt_and_skips_unix_modules(self):
        """Windows path caches msvcrt and skips select/termios/tty entirely."""
        tui = _construct(is_windows=True)

        assert tui.IS_WINDOWS is True
        assert tui.msvcrt is not None
        # Unix module attributes are not set on the Windows branch.
        assert not hasattr(tui, "select")
        assert not hasattr(tui, "termios")
        assert not hasattr(tui, "tty")


# ---------------------------------------------------------------------------
# _init_state — initial defaults
# ---------------------------------------------------------------------------


class TestInitState:
    """Cover ``_init_state`` default-value assignments."""

    def test_defaults_are_reset(self):
        """Every mutable state attribute has its documented default."""
        tui = _construct()
        assert tui.running is True
        assert tui.current_path == []
        assert tui.current_items == []
        assert tui.current_selection == 0
        assert tui.breadcrumb == "mistapi.api.v1"
        assert tui.last_result is None
        assert tui.last_parsed_data is None
        assert tui.last_error is None
        assert tui.execution_state is None
        assert tui.current_function is None
        assert tui.function_params == {}
        assert tui.param_list == []
        assert tui.current_param_index == 0
        assert tui.input_buffer == ""
        assert tui.output_lines == []
        assert tui.results_scroll_offset == 0
        assert tui.result_row_scroll == 0


# ---------------------------------------------------------------------------
# _init_collaborators + dotenv load
# ---------------------------------------------------------------------------


class TestInitCollaborators:
    """Cover collaborator wiring and post-init dotenv/apisession assignments."""

    def test_all_collaborators_assigned(self):
        """Every collaborator attribute is set to a mock instance."""
        tui = _construct()
        for name in (
            "_dotenv_loader",
            "_level_discoverer",
            "_key_poller",
            "_keyboard_dispatch",
            "_function_executor",
            "_parameter_collector",
            "_item_executor",
            "_api_parser",
            "_hier_formatter",
            "_debug_saver",
            "_results_grid_builder",
            "_layout_builder",
            "_tui_runner",
        ):
            assert getattr(tui, name) is not None

    def test_dotenv_values_populated_from_loader(self):
        """``dotenv_values`` is assigned from the DotenvLoader mock's load() call."""
        tui = _construct()
        # DotenvLoader was replaced by a MagicMock class; .load() returns a Mock.
        assert tui.dotenv_values is tui._dotenv_loader.load.return_value

    def test_apisession_starts_none(self):
        """``apisession`` starts as None until the main script wires it."""
        tui = _construct()
        assert tui.apisession is None

    def test_debug_mode_true_logs_trace(self, caplog):
        """debug_mode=True emits the debug trace log line."""
        import logging as _lg

        with caplog.at_level(_lg.DEBUG):
            tui = _construct(debug=True)
        assert tui.debug_mode is True
        # The construction trace is at DEBUG level.
        assert any("Debug mode ENABLED" in rec.getMessage() for rec in caplog.records)


# ---------------------------------------------------------------------------
# _get_terminal_height — success + exception fallback + floor
# ---------------------------------------------------------------------------


class TestGetTerminalHeight:
    """Cover the terminal-height helper's three code paths."""

    def test_returns_height_minus_overhead(self):
        """Normal path returns console_height - UI_OVERHEAD_ROWS."""
        tui = _construct()
        tui.console = SimpleNamespace(size=SimpleNamespace(height=50))
        assert tui._get_terminal_height() == 40  # 50 - 10

    def test_returns_floor_when_terminal_small(self):
        """Very small terminals are floored at 10 rows."""
        tui = _construct()
        tui.console = SimpleNamespace(size=SimpleNamespace(height=5))
        assert tui._get_terminal_height() == 10

    def test_returns_fallback_when_detection_fails(self):
        """Detection exception returns the conservative 20-row fallback."""
        tui = _construct()

        class _Bad:
            @property
            def size(self):
                raise RuntimeError("no tty")

        tui.console = _Bad()
        assert tui._get_terminal_height() == 20

    def test_debug_mode_logs_fallback_trace(self, caplog):
        """debug_mode=True logs the fallback-path trace."""
        import logging as _lg

        tui = _construct(debug=True)

        class _Bad:
            @property
            def size(self):
                raise RuntimeError("no tty")

        tui.console = _Bad()
        with caplog.at_level(_lg.DEBUG):
            tui._get_terminal_height()
        assert any("terminal-height detection failed" in rec.getMessage() for rec in caplog.records)


# ---------------------------------------------------------------------------
# Thin delegates
# ---------------------------------------------------------------------------


class TestThinDelegates:
    """Cover every method that just forwards to a collaborator."""

    def test_discover_current_level_delegates(self):
        """``_discover_current_level`` calls the level-discoverer collaborator."""
        tui = _construct()
        tui._discover_current_level()
        tui._level_discoverer.discover.assert_called_once()

    def test_check_keyboard_input_returns_poller_result(self):
        """``check_keyboard_input`` returns whatever the KeyPoller returned."""
        tui = _construct()
        tui._key_poller.poll.return_value = "x"
        assert tui.check_keyboard_input() == "x"

    def test_create_layout_returns_builder_output(self):
        """``create_layout`` returns whatever the LayoutBuilder returned."""
        tui = _construct()
        tui._layout_builder.build.return_value = "<layout>"
        assert tui.create_layout() == "<layout>"

    def test_create_results_grid_returns_builder_output(self):
        """``_create_results_grid`` returns whatever the ResultsGridBuilder returned."""
        tui = _construct()
        tui._results_grid_builder.build.return_value = "<grid>"
        assert tui._create_results_grid() == "<grid>"

    def test_submit_parameter_delegates(self):
        """``_submit_parameter`` calls the ParameterCollector submit()."""
        tui = _construct()
        tui._submit_parameter()
        tui._parameter_collector.submit.assert_called_once()

    def test_execute_function_delegates(self):
        """``_execute_function`` calls the FunctionExecutor execute()."""
        tui = _construct()
        tui._execute_function()
        tui._function_executor.execute.assert_called_once()

    def test_format_value_hierarchical_delegates(self):
        """``_format_value_hierarchical`` forwards to the HierarchicalFormatter internal renderer."""
        tui = _construct()
        output: list[str] = []
        tui._format_value_hierarchical("value", output, indent=2, key_name="k", max_items=99)
        tui._hier_formatter._render.assert_called_once_with("value", output, 2, "k")

    def test_execute_current_item_delegates(self):
        """``execute_current_item`` calls the ItemExecutor execute()."""
        tui = _construct()
        tui.execute_current_item()
        tui._item_executor.execute.assert_called_once()

    def test_run_delegates(self):
        """``run`` calls the TuiRunner run()."""
        tui = _construct()
        tui.run()
        tui._tui_runner.run.assert_called_once()


# ---------------------------------------------------------------------------
# _cancel_execution — resets state; two branches (debug on/off)
# ---------------------------------------------------------------------------


class TestCancelExecution:
    """Cover ``_cancel_execution`` state-reset behavior on both debug branches."""

    def test_resets_all_execution_state(self):
        """Every execution-related attribute is reset to its default."""
        tui = _construct()
        tui.execution_state = "prompting"
        tui.current_function = {"name": "f"}
        tui.function_params = {"a": 1}
        tui.param_list = [{"name": "a"}]
        tui.current_param_index = 3
        tui.input_buffer = "abc"

        tui._cancel_execution()

        assert tui.execution_state is None
        assert tui.current_function is None
        assert tui.function_params == {}
        assert tui.param_list == []
        assert tui.current_param_index == 0
        assert tui.input_buffer == ""
        assert tui.output_lines == ["[CANCELLED] Execution cancelled by user"]

    def test_debug_mode_logs_cancel_trace(self, caplog):
        """debug_mode=True emits the cancel-trace log line."""
        import logging as _lg

        tui = _construct(debug=True)
        with caplog.at_level(_lg.DEBUG):
            tui._cancel_execution()
        assert any("cancelled by user" in rec.getMessage().lower() for rec in caplog.records)


# ---------------------------------------------------------------------------
# _should_show_results_grid — every branch
# ---------------------------------------------------------------------------


class TestShouldShowResultsGrid:
    """Cover all branches of ``_should_show_results_grid``."""

    def test_returns_false_when_not_dict(self):
        """Non-dict inputs are not tabular."""
        tui = _construct()
        assert tui._should_show_results_grid([1, 2, 3]) is False
        assert tui._should_show_results_grid("string") is False
        assert tui._should_show_results_grid(None) is False

    def test_returns_false_when_results_missing(self):
        """Dict without a ``results`` list is not tabular."""
        tui = _construct()
        assert tui._should_show_results_grid({}) is False
        assert tui._should_show_results_grid({"other": 1}) is False

    def test_returns_false_when_results_not_list(self):
        """``results`` that is not a list is not tabular."""
        tui = _construct()
        assert tui._should_show_results_grid({"results": "oops"}) is False

    def test_returns_false_when_results_empty(self):
        """Empty ``results`` list is not tabular."""
        tui = _construct()
        assert tui._should_show_results_grid({"results": []}) is False

    def test_returns_false_when_first_row_not_dict(self):
        """List whose first row is not a dict is not tabular."""
        tui = _construct()
        assert tui._should_show_results_grid({"results": [1, 2]}) is False

    def test_returns_true_when_first_row_is_dict(self):
        """List of dicts is tabular."""
        tui = _construct()
        assert tui._should_show_results_grid({"results": [{"k": "v"}]}) is True
