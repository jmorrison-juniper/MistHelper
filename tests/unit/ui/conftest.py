"""Shared fixtures for src/ui collaborator unit tests."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
from rich import box  # Real Rich box constants used by collaborators
from rich.console import Console  # Real Rich Console
from rich.layout import Layout  # Real Rich Layout
from rich.panel import Panel  # Real Rich Panel
from rich.table import Table  # Real Rich Table


def _build_console() -> Console:
    """Return a Console bound to a fixed terminal size for deterministic tests."""
    return Console(width=120, force_terminal=False, record=False)  # Deterministic 120-col Console


@pytest.fixture(autouse=True)
def _patch_stdin_fileno(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure sys.stdin.fileno() returns an int under pytest's captured stdin.

    Several collaborators call ``sys.stdin.fileno()`` inline as an argument to
    a mocked ``tty.setcbreak()`` — pytest's capture replaces stdin with a
    pseudo-file whose ``fileno()`` raises ``UnsupportedOperation``. Patching
    the method to return a sentinel makes those call paths work in tests.
    """
    import sys as _sys

    monkeypatch.setattr(_sys.stdin, "fileno", lambda: 0, raising=False)  # Fake file descriptor


@pytest.fixture(autouse=True)
def _clear_param_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Strip env vars that the ItemExecutor uses for parameter autofill.

    The dev shell may carry a real ``org_id``, ``limit``, etc.; that would
    silently autofill the prompts and bypass the patched ``input()`` in tests.
    """
    for var in (  # Common parameter names that collide with real env vars
        "org_id",
        "site_id",
        "limit",
        "mac",
        "device_id",
        "msp_id",
        "mxedge_id",
        "wlan_id",
    ):
        monkeypatch.delenv(var, raising=False)  # No-op when unset


@pytest.fixture
def tui_stub() -> SimpleNamespace:
    """Return a SimpleNamespace satisfying the ``_tui`` back-reference contract.

    Each collaborator only reads/writes a handful of attributes on its TUI
    back-reference. We populate every attribute mentioned by any collaborator
    so a single fixture works for all of them; tests overwrite only the ones
    they exercise.
    """
    stub = SimpleNamespace()  # Base namespace; assigning is cheap
    stub.debug_mode = False  # Default off; tests flip when needed
    stub.Console = Console  # Class reference (the layout builder uses .Panel etc.)
    stub.Panel = Panel  # Real Panel class
    stub.Table = Table  # Real Table class
    stub.Layout = Layout  # Real Layout class
    stub.box = box  # Real box module
    stub.console = _build_console()  # Pre-built console at fixed size
    stub.IS_WINDOWS = False  # Default to Unix path for tests
    stub.msvcrt = MagicMock()  # Stub Windows API; tests override when needed
    stub.select = MagicMock()  # Stub Unix select module
    stub.termios = MagicMock()  # Stub termios; harmless for tests
    stub.tty = MagicMock()  # Stub tty; harmless for tests
    stub.old_terminal_settings = None  # Saved termios placeholder
    stub.running = True  # Main-loop flag
    stub.current_path = []  # Empty path at root
    stub.current_items = []  # No items by default
    stub.current_selection = 0  # Highlighted index
    stub.breadcrumb = "mistapi.api.v1"  # Header text
    stub.last_result = None  # No previous result
    stub.last_parsed_data = None  # No parsed data
    stub.last_error = None  # No error
    stub.execution_state = None  # No active execution
    stub.current_function = None  # No function selected
    stub.function_params = {}  # Empty parameter capture
    stub.param_list = []  # Empty param list
    stub.current_param_index = 0  # Index into param_list
    stub.input_buffer = ""  # Typed buffer
    stub.output_lines = []  # Output panel lines
    stub.results_scroll_offset = 0  # Current result index
    stub.result_row_scroll = 0  # Row offset within current result
    stub.dotenv_values = {}  # Loaded .env values
    stub.apisession = MagicMock()  # Default to a Mock session
    # Collaborator objects that other collaborators reach through on the TUI:
    stub._api_parser = MagicMock()  # APIResponse parser collaborator
    stub._api_parser.parse = MagicMock(side_effect=lambda r: r)  # Default passthrough
    stub._hier_formatter = MagicMock()  # Hierarchical output formatter collaborator
    stub._hier_formatter.format_result = MagicMock(return_value=["[SUCCESS] formatted"])
    stub._keyboard_dispatch = MagicMock()  # Keyboard dispatch table, used by TuiRunner
    stub._function_executor = MagicMock()  # Function executor, used by keyboard_dispatch enter handler
    stub._should_show_results_grid = MagicMock(return_value=False)
    stub._cancel_execution = MagicMock()  # Used by keyboard_dispatch escape handler
    stub._submit_parameter = MagicMock()  # Used by keyboard_dispatch enter handler
    stub._discover_current_level = MagicMock()  # Used by nav drill/back
    stub._debug_saver = MagicMock()  # Used by FunctionExecutor when debug_mode
    stub._results_grid_builder = MagicMock()  # Used by LayoutBuilder when viewing_results
    stub._results_grid_builder.build.return_value = None  # Default: no grid available
    stub._get_terminal_height = MagicMock(return_value=30)  # Stable terminal height
    # Lifecycle methods invoked by TuiRunner during render loop:
    stub.create_layout = MagicMock(return_value="<layout>")  # Stand-in layout object
    stub.check_keyboard_input = MagicMock(return_value=None)  # No keystroke by default
    # Rich Live class placeholder; tests override with their own context manager:
    stub.Live = MagicMock()  # Default: not used unless test exercises tui_runner
    return stub


@pytest.fixture
def make_item() -> Any:
    """Return a factory producing item-dicts of the requested type."""

    def _factory(item_type: str = "function", name: str = "demo", **extra: Any) -> dict[str, Any]:
        record = {"type": item_type, "name": name, "description": extra.pop("description", f"{item_type} {name}")}
        record.update(extra)  # Allow tests to add signature/object/full_doc/etc.
        return record

    return _factory
