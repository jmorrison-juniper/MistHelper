"""Terminal User Interface for the MistHelper API explorer.

Provides the MistHelperTUI class - a keyboard-driven API browser that lets
users navigate, discover, and execute calls against the Juniper Mist
mistapi SDK hierarchy interactively.

Internally this class is now a *thin orchestrator* that composes focused
collaborators (input, layout, execution, runtime) under ``src/ui/``. All
heavy logic lives in those collaborator modules; this class wires them
together and exposes the original public surface unchanged.
"""

from __future__ import annotations  # WHY: postponed evaluation for forward-ref type hints

import logging  # WHY: action logs for TUI lifecycle and debug traces
import platform  # WHY: Windows vs Unix keyboard-IO branch selection
import sys  # WHY: fatal exit when Rich is missing
from typing import Any  # WHY: broad typing on Rich cache attrs + apisession

from src.ui.execution import (  # WHY: execution collaborators (parse/format/execute)
    APIResponseParser,
    DebugResultSaver,
    FunctionExecutor,
    HierarchicalFormatter,
    ItemExecutor,
    ParameterCollector,
)
from src.ui.input_handlers import KeyboardDispatchTable, KeyPoller  # WHY: keystroke poll + dispatch
from src.ui.layout import LayoutBuilder, ResultsGridBuilder  # WHY: Rich Panel composition
from src.ui.runtime import DotenvLoader, LevelDiscoverer, TuiRunner  # WHY: .env, discovery, lifecycle

UI_OVERHEAD_ROWS = 10  # Reserved rows for borders/title/help


class MistHelperTUI:  # WHY: public TUI entrypoint composing all collaborators
    """Terminal User Interface for exploring the Mist API library hierarchy.

    Public surface (unchanged from the pre-refactor implementation):

    - ``MistHelperTUI(debug_mode=False)``
    - ``self.apisession`` attribute, settable by the main script
    - ``self.run()`` to start the interactive loop

    Internally, every meaningful operation is delegated to a collaborator
    under ``src/ui/`` so each callable here is CC <= 10.
    """

    def __init__(self, debug_mode: bool = False) -> None:  # WHY: wire all collaborators at construction
        """Construct the TUI and all collaborator objects."""
        self.debug_mode = debug_mode  # Verbose-logging flag
        self._init_rich()  # Import Rich classes onto self
        self._init_platform_io()  # Cache msvcrt or select/termios/tty
        self._init_state()  # Reset navigation + execution state
        self._init_collaborators()  # Build collaborator instances
        self.dotenv_values = self._dotenv_loader.load()  # Load .env via collaborator
        self.apisession: Any = None  # Will be set by main script
        if self.debug_mode:  # Optional debug trace
            logging.debug("TUI_DEBUG: Debug mode ENABLED for TUI navigation")  # Trace when verbose logging active
        logging.info("TUI_MODE: MistHelperTUI API Explorer initialized")  # Action log after construction

    # ---- construction helpers (each CC <= 6) ----------------------------

    def _init_rich(self) -> None:  # WHY: lazy-import Rich to keep non-TUI startup fast
        """Import the Rich classes the TUI needs and cache them on ``self``."""
        try:
            from rich import box  # Lazy import keeps startup fast
            from rich.console import Console  # Console owns stdout rendering
            from rich.layout import Layout  # Layout tree primitive
            from rich.live import Live  # Live refresh context manager
            from rich.markdown import Markdown  # Markdown renderer for help text
            from rich.panel import Panel  # Bordered panel primitive
            from rich.syntax import Syntax  # Code syntax highlighter
            from rich.table import Table  # Table primitive for grids
        except ImportError:  # Rich missing -> fatal in TUI mode
            # WHY (#886 Phase 2): collapse paired logger+print into a single logging.error so the
            # install hint reaches the operator via the same handler chain as the diagnostic line.
            logging.error(
                "TUI_MODE: Rich library not available - cannot start TUI mode. " "Install with: pip install rich"
            )  # Diagnose fatal + surface install hint
            sys.exit(1)  # Cannot render without Rich
        self.Console = Console  # Public attrs reused by collaborators
        self.Live = Live  # Cached class for TuiRunner
        self.Panel = Panel  # Cached class for layout builders
        self.Table = Table  # Cached class for results grid
        self.Layout = Layout  # Cached class for LayoutBuilder
        self.box = box  # Cached box styles module
        self.Syntax = Syntax  # Cached class for code highlighting
        self.Markdown = Markdown  # Cached class for help panel
        self.console = self.Console()  # Single Console instance for the run

    def _init_platform_io(self) -> None:  # WHY: platform-branch selects Windows vs Unix keyboard modules
        """Import platform-specific keyboard modules and cache them on ``self``."""
        self.IS_WINDOWS = platform.system() == "Windows"  # Platform detection
        if self.IS_WINDOWS:  # Windows uses msvcrt
            import msvcrt  # Windows-only kbhit/getch

            self.msvcrt = msvcrt  # Cache module reference for KeyPoller
            return  # Windows path complete
        import select  # Unix non-blocking read path
        import termios  # Unix terminal mode mgmt
        import tty  # Unix cbreak mgmt

        self.select = select  # Cache select for KeyPoller
        self.termios = termios  # Cache termios for TuiRunner setup/teardown
        self.tty = tty  # Cache tty for cbreak switch
        self.old_terminal_settings: Any = None  # Captured in TuiRunner.setup

    def _init_state(self) -> None:  # WHY: reset all mutable navigation + execution state
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

    def _init_collaborators(self) -> None:  # WHY: build every collaborator once at startup
        """Build all collaborator instances (one per submodule responsibility)."""
        self._dotenv_loader = DotenvLoader(self)  # .env parsing
        self._level_discoverer = LevelDiscoverer(self)  # Module/function introspection
        self._key_poller = KeyPoller(self)  # Non-blocking key polling
        self._keyboard_dispatch = KeyboardDispatchTable(self)  # handle_input dispatch
        self._function_executor = FunctionExecutor(self)  # Live-mode execution
        self._parameter_collector = ParameterCollector(self, self._function_executor)  # Param capture -> execute
        self._item_executor = ItemExecutor(self)  # Sync-mode prompt execution
        self._api_parser = APIResponseParser()  # APIResponse -> data
        self._hier_formatter = HierarchicalFormatter()  # Indented value renderer
        self._debug_saver = DebugResultSaver(self)  # Debug JSON writer
        self._results_grid_builder = ResultsGridBuilder(self)  # Results-grid Panel builder
        self._layout_builder = LayoutBuilder(self)  # Main layout Panel builder
        self._tui_runner = TuiRunner(self)  # Lifecycle + render loop

    # ---- thin orchestrator methods (each CC <= 4) -----------------------

    def _get_terminal_height(self) -> int:  # WHY: compute usable rows after UI chrome
        """Return available rows for table data after subtracting UI chrome."""
        try:
            console_height = self.console.size.height  # Rich detects current terminal height
        except Exception as error:  # Detection can fail in containers
            if self.debug_mode:  # Optional debug trace only in verbose mode
                logging.debug("TUI_DEBUG: terminal-height detection failed: %s", error)  # Trace fallback path
            return 20  # Conservative fallback
        return max(10, console_height - UI_OVERHEAD_ROWS)  # Floor at 10 rows

    def _discover_current_level(self) -> None:
        """Discover modules/functions at the current path (delegate)."""
        self._level_discoverer.discover()  # Heavy lifting in collaborator

    def check_keyboard_input(self) -> str | None:
        """Poll for the next pressed key (delegate)."""
        return self._key_poller.poll()  # Cross-platform poll

    def create_layout(self) -> Any:
        """Build the Rich layout for the current frame (delegate)."""
        return self._layout_builder.build()  # Full layout composition

    def _create_results_grid(self) -> Any:
        """Build the Rich Panel for the results grid (delegate)."""
        return self._results_grid_builder.build()  # Returns None when no data

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

    def _should_show_results_grid(self, parsed_data: Any) -> bool:
        """Return True iff ``parsed_data`` looks like list-of-dicts tabular data."""
        if not isinstance(parsed_data, dict):  # Not a dict -> not tabular
            return False
        results = parsed_data.get("results")  # Pull candidate list
        if not isinstance(results, list) or not results:  # Missing/empty -> not tabular
            return False
        return isinstance(results[0], dict)  # Only show grid for dict rows

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
