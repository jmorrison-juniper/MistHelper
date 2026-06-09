"""Terminal User Interface for the MistHelper API explorer.

Provides the MistHelperTUI class - a keyboard-driven API browser that lets
users navigate, discover, and execute calls against the Juniper Mist
mistapi SDK hierarchy interactively.

Internally this class is now a *thin orchestrator* that composes focused
collaborators (input, layout, execution, runtime) under ``src/ui/``. All
heavy logic lives in those collaborator modules; this class wires them
together and exposes the original public surface unchanged.
"""

from __future__ import annotations

import logging
import platform
import sys
from typing import Any

from src.ui.execution import (
    APIResponseParser,
    DebugResultSaver,
    FunctionExecutor,
    HierarchicalFormatter,
    ItemExecutor,
    ParameterCollector,
)
from src.ui.input_handlers import KeyboardDispatchTable, KeyPoller
from src.ui.layout import LayoutBuilder, ResultsGridBuilder
from src.ui.runtime import DotenvLoader, LevelDiscoverer, TuiRunner

UI_OVERHEAD_ROWS = 10  # Reserved rows for borders/title/help


class MistHelperTUI:
    """Terminal User Interface for exploring the Mist API library hierarchy.

    Public surface (unchanged from the pre-refactor implementation):

    - ``MistHelperTUI(debug_mode=False)``
    - ``self.apisession`` attribute, settable by the main script
    - ``self.run()`` to start the interactive loop

    Internally, every meaningful operation is delegated to a collaborator
    under ``src/ui/`` so each callable here is CC <= 10.
    """

    def __init__(self, debug_mode: bool = False) -> None:
        """Construct the TUI and all collaborator objects."""
        self.debug_mode = debug_mode  # Verbose-logging flag
        self._init_rich()  # Import Rich classes onto self
        self._init_platform_io()  # Cache msvcrt or select/termios/tty
        self._init_state()  # Reset navigation + execution state
        self._init_collaborators()  # Build collaborator instances
        self.dotenv_values = self._dotenv_loader.load()  # Load .env via collaborator
        self.apisession: Any = None  # Will be set by main script
        if self.debug_mode:  # Optional debug trace
            logging.debug("TUI_DEBUG: Debug mode ENABLED for TUI navigation")
        logging.info("TUI_MODE: MistHelperTUI API Explorer initialized")  # Action log after construction

    # ---- construction helpers (each CC <= 6) ----------------------------

    def _init_rich(self) -> None:
        """Import the Rich classes the TUI needs and cache them on ``self``."""
        try:
            from rich import box  # Lazy import keeps startup fast
            from rich.console import Console
            from rich.layout import Layout
            from rich.live import Live
            from rich.markdown import Markdown
            from rich.panel import Panel
            from rich.syntax import Syntax
            from rich.table import Table
        except ImportError:  # Rich missing -> fatal in TUI mode
            logging.error("TUI_MODE: Rich library not available - cannot start TUI mode")
            print("[ERROR] Rich library required for TUI mode. Install with: pip install rich")
            sys.exit(1)
        self.Console = Console  # Public attrs reused by collaborators
        self.Live = Live
        self.Panel = Panel
        self.Table = Table
        self.Layout = Layout
        self.box = box
        self.Syntax = Syntax
        self.Markdown = Markdown
        self.console = self.Console()  # Single Console instance for the run

    def _init_platform_io(self) -> None:
        """Import platform-specific keyboard modules and cache them on ``self``."""
        self.IS_WINDOWS = platform.system() == "Windows"  # Platform detection
        if self.IS_WINDOWS:  # Windows uses msvcrt
            import msvcrt

            self.msvcrt = msvcrt
            return
        import select  # Unix non-blocking read path
        import termios  # Unix terminal mode mgmt
        import tty  # Unix cbreak mgmt

        self.select = select
        self.termios = termios
        self.tty = tty
        self.old_terminal_settings: Any = None  # Captured in TuiRunner.setup

    def _init_state(self) -> None:
        """Initialize navigation, execution, and results-view state to defaults."""
        self.running = True  # Main-loop flag
        self.current_path: list[str] = []  # Path segments below mistapi.api.v1
        self.current_items: list[dict[str, Any]] = []  # Items at the current level
        self.current_selection = 0  # Highlighted index
        self.breadcrumb = "mistapi.api.v1"  # Header text
        self.last_result: Any = None  # Raw last APIResponse
        self.last_parsed_data: Any = None  # Parsed payload
        self.last_error: str | None = None  # Last surfaced error message
        self.execution_state: str | None = None  # None|prompting|executing|grid
        self.current_function: dict[str, Any] | None = None  # Function under execution
        self.function_params: dict[str, Any] = {}  # Collected parameters
        self.param_list: list[dict[str, Any]] = []  # Remaining params to prompt for
        self.current_param_index = 0  # Index into param_list
        self.input_buffer = ""  # Per-keystroke buffer
        self.output_lines: list[str] = []  # Output panel lines
        self.results_scroll_offset = 0  # Which result is shown
        self.result_row_scroll = 0  # Row offset within current result

    def _init_collaborators(self) -> None:
        """Build all collaborator instances (one per submodule responsibility)."""
        self._dotenv_loader = DotenvLoader(self)  # .env parsing
        self._level_discoverer = LevelDiscoverer(self)  # Module/function introspection
        self._key_poller = KeyPoller(self)  # Non-blocking key polling
        self._keyboard_dispatch = KeyboardDispatchTable(self)  # handle_input dispatch
        self._function_executor = FunctionExecutor(self)  # Live-mode execution
        self._parameter_collector = ParameterCollector(self, self._function_executor)
        self._item_executor = ItemExecutor(self)  # Sync-mode prompt execution
        self._api_parser = APIResponseParser()  # APIResponse -> data
        self._hier_formatter = HierarchicalFormatter()  # Indented value renderer
        self._debug_saver = DebugResultSaver(self)  # Debug JSON writer
        self._results_grid_builder = ResultsGridBuilder(self)  # Results-grid Panel builder
        self._layout_builder = LayoutBuilder(self)  # Main layout Panel builder
        self._tui_runner = TuiRunner(self)  # Lifecycle + render loop

    # ---- thin orchestrator methods (each CC <= 4) -----------------------

    def _get_terminal_height(self) -> int:
        """Return available rows for table data after subtracting UI chrome."""
        try:
            console_height = self.console.size.height  # Rich detects current terminal height
        except Exception as error:  # Detection can fail in containers
            if self.debug_mode:
                logging.debug("TUI_DEBUG: terminal-height detection failed: %s", error)
            return 20  # Conservative fallback
        return max(10, console_height - UI_OVERHEAD_ROWS)  # Floor at 10 rows

    def _discover_current_level(self) -> None:
        """Discover modules/functions at the current path (delegate)."""
        self._level_discoverer.discover()  # Heavy lifting in collaborator

    def check_keyboard_input(self) -> str | None:
        """Poll for the next pressed key (delegate)."""
        return self._key_poller.poll()  # Cross-platform poll

    def handle_input(self, key: str) -> None:
        """Dispatch ``key`` based on the current execution state (delegate)."""
        self._keyboard_dispatch.dispatch(key)  # Mode-scoped dispatch table

    def create_layout(self) -> Any:
        """Build the Rich layout for the current frame (delegate)."""
        return self._layout_builder.build()  # Full layout composition

    def _create_results_grid(self) -> Any:
        """Build the Rich Panel for the results grid (delegate)."""
        return self._results_grid_builder.build()  # Returns None when no data

    def _start_function_execution(self, selected_item: dict[str, Any]) -> None:
        """Begin Live-mode function execution (delegate)."""
        self._function_executor.start(selected_item)  # Param discovery + collection kickoff

    def _submit_parameter(self) -> None:
        """Submit the currently-typed parameter value (delegate)."""
        self._parameter_collector.submit()  # Advance index or run the call

    def _cancel_execution(self) -> None:
        """Cancel the current function execution and reset prompt state."""
        if self.debug_mode:  # Optional debug trace
            logging.debug("TUI_DEBUG: Function execution cancelled by user")
        self.execution_state = None  # Drop prompt mode
        self.current_function = None  # Drop function reference
        self.function_params = {}  # Drop captured params
        self.param_list = []  # Drop param list
        self.current_param_index = 0  # Reset index
        self.input_buffer = ""  # Drop typed buffer
        self.output_lines = ["[CANCELLED] Execution cancelled by user"]  # User feedback

    def _execute_function(self) -> None:
        """Execute the currently prepared function (delegate)."""
        self._function_executor.execute()  # Includes pagination + state mgmt

    def _parse_api_response(self, result: Any) -> Any:
        """Extract ``.data`` from an APIResponse object (delegate)."""
        return self._api_parser.parse(result)

    def _should_show_results_grid(self, parsed_data: Any) -> bool:
        """Return True iff ``parsed_data`` looks like list-of-dicts tabular data."""
        if not isinstance(parsed_data, dict):  # Not a dict -> not tabular
            return False
        results = parsed_data.get("results")  # Pull candidate list
        if not isinstance(results, list) or not results:  # Missing/empty -> not tabular
            return False
        return isinstance(results[0], dict)  # Only show grid for dict rows

    def _save_debug_result(self, func_name: str, raw_result: Any, parsed_data: Any) -> None:
        """Save the API call artifact when in debug mode (delegate)."""
        self._debug_saver.save(func_name, raw_result, parsed_data)

    def _format_result_output(self, parsed_data: Any, func_name: str, raw_result: Any = None) -> list[str]:
        """Format an API result for the output panel (delegate)."""
        return self._hier_formatter.format_result(parsed_data, func_name, raw_result)

    def _format_value_hierarchical(
        self,
        value: Any,
        output: list[str],
        indent: int = 0,
        key_name: str | None = None,
        max_items: int = 5,
    ) -> None:
        """Recursively format ``value`` into ``output`` (delegate)."""
        # ``max_items`` is preserved in the signature for back-compat; the collaborator
        # uses its own MAX_SAMPLE_ITEMS constant.
        del max_items  # Explicitly acknowledge unused param
        self._hier_formatter._render(value, output, indent, key_name)  # Reuse the internal renderer

    def execute_current_item(self) -> None:
        """Run the synchronous-prompt execution flow (delegate)."""
        self._item_executor.execute()

    def run(self) -> None:
        """Start the TUI render loop and block until quit (delegate)."""
        self._tui_runner.run()
