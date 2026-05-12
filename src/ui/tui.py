"""Terminal User Interface for the MistHelper API explorer.

Provides the MistHelperTUI class - a keyboard-driven API browser that lets
users navigate, discover, and execute calls against the Juniper Mist
mistapi SDK hierarchy interactively.
"""

from __future__ import annotations

import json
import logging
import os
import platform
import shutil
import sys
import time
from datetime import datetime
from typing import Any


class MistHelperTUI:
    """Terminal User Interface for exploring the Mist API library hierarchy.

    This class provides an interactive, keyboard-driven API browser that lets you:
    - Navigate Thomas Munzer's mistapi package structure
    - Discover available modules (orgs, sites, const, etc.)
    - Explore functions within each module
    - View function signatures and documentation
    - Execute API calls with parameter prompts
    - Display results in formatted tables

    Navigation starts at mistapi.api.v1 and allows drill-down into:
    - Modules (orgs, sites, msps, etc.)
    - Sub-modules (orgs.devices, sites.clients, etc.)
    - Functions (listOrgSites, getSiteDevices, etc.)

    Design Philosophy:
    - Hierarchical: Mirror the actual mistapi package structure
    - Discovery-driven: Learn the API by exploring
    - Interactive: Execute calls directly from the browser
    - Safe: Read-only operations clearly marked
    - Educational: See signatures and docstrings
    """

    def __init__(self, debug_mode=False):  # type: ignore[no-untyped-def]  # noqa: PLR0915
        """Initialize the TUI API explorer.

        Args:
            debug_mode (bool): Enable detailed logging of navigation and input
        """
        self.debug_mode = debug_mode
        self.dotenv_values = self._load_dotenv_only()  # type: ignore[no-untyped-call]

        try:
            from rich import box
            from rich.console import Console
            from rich.layout import Layout
            from rich.live import Live
            from rich.markdown import Markdown
            from rich.panel import Panel
            from rich.syntax import Syntax
            from rich.table import Table

            self.Console = Console
            self.Live = Live
            self.Panel = Panel
            self.Table = Table
            self.Layout = Layout
            self.box = box
            self.Syntax = Syntax
            self.Markdown = Markdown
        except ImportError:
            logging.error("TUI_MODE: Rich library not available - cannot start TUI mode")
            print("[ERROR] Rich library required for TUI mode. Install with: pip install rich")
            sys.exit(1)

        # Create console without size override (let it detect terminal size naturally)
        self.console = self.Console()
        self.running = True

        # Navigation state - hierarchical path through the API
        self.current_path = []  # e.g., ['orgs', 'sites'] for mistapi.api.v1.orgs.sites
        self.current_items = []  # Current level's items (modules or functions)
        self.current_selection = 0  # Selected index in current_items
        self.breadcrumb = "mistapi.api.v1"  # Display path

        # Results from last API call
        self.last_result = None
        self.last_parsed_data = None  # Parsed data from APIResponse
        self.last_error = None

        # Execution control - state machine for function execution
        self.execution_state = None  # None, 'prompting', 'executing', 'viewing_results'
        self.current_function = None  # Function being executed
        self.function_params = {}  # Parameters collected so far
        self.param_list = []  # List of parameters to collect
        self.current_param_index = 0  # Current parameter being prompted
        self.input_buffer = ""  # Current input being typed
        self.output_lines: list[str] = []  # Lines to display in output panel
        self.results_scroll_offset = 0  # Scroll position for results grid (which result)
        self.result_row_scroll = 0  # Scroll position within current result (which row)

        if self.debug_mode:
            logging.debug("TUI_DEBUG: Debug mode ENABLED for TUI navigation")

        # Platform detection for keyboard input
        self.IS_WINDOWS = platform.system() == "Windows"

        # Import platform-specific keyboard modules
        if self.IS_WINDOWS:
            import msvcrt

            self.msvcrt = msvcrt
        else:
            import select
            import termios
            import tty

            self.select = select
            self.tty = tty
            self.termios = termios
            self.old_terminal_settings = None  # Will be set in run()

        # API session reference (needed for function execution)
        self.apisession = None  # Will be set by main script if available

        logging.info("TUI_MODE: MistHelperTUI API Explorer initialized")

    def _load_dotenv_only(self):  # type: ignore[no-untyped-def]
        """Load values ONLY from .env file, not system environment.

        Returns:
            dict: Key-value pairs from .env file only
        """
        dotenv_dict: dict[str, str] = {}
        env_file = ".env"

        if not os.path.exists(env_file):
            return dotenv_dict

        try:
            with open(env_file, encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()

                    # Skip empty lines and comments
                    if not line or line.startswith("#"):
                        continue

                    # Parse key=value
                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip()

                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]

                        dotenv_dict[key] = value

            if self.debug_mode:
                # Log loaded keys (not values, for security)
                logging.debug(f"TUI_DEBUG: Loaded {len(dotenv_dict)} values from .env file: {list(dotenv_dict.keys())}")

        except Exception as e:
            logging.warning(f"TUI: Could not read .env file: {e}")

        return dotenv_dict

    def _get_terminal_height(self):  # type: ignore[no-untyped-def]
        """Get the current terminal height, accounting for UI chrome.

        Returns:
            int: Number of rows available for data display (terminal height minus UI overhead)
        """
        try:
            # Get console size from Rich
            console_height = self.console.size.height

            # Account for UI chrome when viewing results grid:
            # - Main panel top border: 1 line
            # - Main panel title (breadcrumb): 1 line
            # - Results grid panel top border: 1 line
            # - Results grid panel title (Result X of Y...): 1 line
            # - Table header row (Field | Value): 1 line
            # - Results grid panel bottom border: 1 line
            # - Help text inside main panel footer: 2 lines
            # - Main panel bottom border: 1 line
            # Total overhead: 9 lines minimum
            ui_overhead = 10  # Extra buffer for safety

            # Calculate available rows for TABLE DATA only, with minimum of 10
            available_rows = max(10, console_height - ui_overhead)

            if self.debug_mode:
                logging.debug(
                    f"TUI_DEBUG: Terminal height={console_height}, UI overhead={ui_overhead}, "
                    f"available for TABLE DATA={available_rows}"
                )

            return available_rows

        except Exception as error:
            if self.debug_mode:
                logging.debug(f"TUI_DEBUG: Could not detect terminal height: {error}, defaulting to 20 rows")
            return 20  # Fallback default

    def _discover_current_level(self):  # type: ignore[no-untyped-def]  # noqa: C901, PLR0912, PLR0915
        """Discover modules and functions at the current navigation level.

        This method introspects the mistapi package to find:
        - Sub-modules (e.g., at mistapi.api.v1: orgs, sites, const, etc.)
        - Functions (e.g., at mistapi.api.v1.orgs: listOrgs, getOrg, etc.)

        Updates self.current_items with discovered elements.
        """
        import importlib
        import inspect

        self.current_items = []

        try:
            # Build the module path based on current navigation
            if not self.current_path:
                # Root level: mistapi.api.v1
                module_path = "mistapi.api.v1"
            else:
                # Deeper level: mistapi.api.v1.orgs, etc.
                module_path = "mistapi.api.v1." + ".".join(self.current_path)

            if self.debug_mode:
                logging.debug(f"TUI_DEBUG: Discovering items at module path: {module_path}")

            # Update breadcrumb
            self.breadcrumb = module_path

            # Try to import the module
            try:
                module = importlib.import_module(module_path)
                if self.debug_mode:
                    logging.debug(f"TUI_DEBUG: Successfully imported module: {module_path}")
            except ImportError as import_error:
                logging.error(f"TUI: Could not import {module_path}: {import_error}")
                self.current_items = [
                    {"type": "error", "name": "Import Error", "description": f"Module not found: {module_path}"}
                ]
                return

            # Discover sub-modules and functions
            for name in dir(module):
                # Skip private/internal items
                if name.startswith("_"):
                    continue

                try:
                    item = getattr(module, name)

                    # Check if it's a sub-module
                    if inspect.ismodule(item):
                        # Only show modules from mistapi package
                        if hasattr(item, "__package__") and "mistapi" in str(item.__package__):
                            self.current_items.append(
                                {"type": "module", "name": name, "object": item, "description": f"Module: {name}"}
                            )

                    # Check if it's a callable function
                    elif callable(item) and not inspect.isclass(item):
                        # Get function signature
                        try:
                            sig = inspect.signature(item)
                            params = str(sig)
                        except (ValueError, TypeError):
                            params = "(...)"

                        # Get docstring first line
                        doc = inspect.getdoc(item)
                        short_doc = doc.split("\n")[0] if doc else "No description"
                        if len(short_doc) > 60:
                            short_doc = short_doc[:57] + "..."

                        self.current_items.append(
                            {
                                "type": "function",
                                "name": name,
                                "object": item,
                                "signature": params,
                                "description": short_doc,
                                "full_doc": doc,
                            }
                        )

                except Exception as error:
                    logging.debug(f"TUI: Skipping {name}: {error}")
                    continue

            # Sort: modules first, then functions alphabetically
            self.current_items.sort(key=lambda x: (0 if x["type"] == "module" else 1, x["name"]))

            if not self.current_items:
                self.current_items = [
                    {"type": "empty", "name": "(empty)", "description": "No items found at this level"}
                ]

            logging.info(f"TUI: Discovered {len(self.current_items)} items at {module_path}")

            if self.debug_mode:
                modules_count = sum(1 for item in self.current_items if item.get("type") == "module")
                functions_count = sum(1 for item in self.current_items if item.get("type") == "function")
                logging.debug(f"TUI_DEBUG: Discovery complete - {modules_count} modules, {functions_count} functions")
                if self.current_items:
                    item_names = [item.get("name", "unknown") for item in self.current_items[:10]]
                    logging.debug(f"TUI_DEBUG: First items (max 10): {', '.join(item_names)}")

        except Exception as error:
            logging.error(f"TUI: Discovery error: {error}", exc_info=True)
            self.current_items = [{"type": "error", "name": "Error", "description": str(error)}]

    def check_keyboard_input(self):  # type: ignore[no-untyped-def]  # noqa: C901, PLR0912, PLR0915
        """Check for keyboard input in a cross-platform way.

        Returns:
            str or None: Key pressed, or None if no input
        """
        try:
            if self.IS_WINDOWS:
                # Windows: Use msvcrt for non-blocking keyboard check
                if self.msvcrt.kbhit():
                    key = self.msvcrt.getch()
                    if self.debug_mode:
                        logging.debug(f"TUI_DEBUG: Raw key byte received: {repr(key)}")
                    # Handle multi-byte sequences for arrow keys and page keys
                    if key == b"\xe0" or key == b"\x00":
                        key = self.msvcrt.getch()
                        if self.debug_mode:
                            logging.debug(f"TUI_DEBUG: Special key detected - second byte value: {repr(key)}")
                        if key == b"H":  # Up arrow
                            return "up"
                        elif key == b"P":  # Down arrow
                            return "down"
                        elif key == b"K":  # Left arrow
                            return "left"
                        elif key == b"M":  # Right arrow
                            return "right"
                        elif key == b"I":  # Page Up (0x49)
                            if self.debug_mode:
                                logging.debug("TUI_DEBUG: Page Up key detected")
                            return "page_up"
                        elif key == b"Q":  # Page Down (0x51)
                            if self.debug_mode:
                                logging.debug("TUI_DEBUG: Page Down key detected")
                            return "page_down"
                        elif key == b"G":  # Home
                            return "h"
                        elif key == b"O":  # End
                            return "e"
                        else:
                            # Log unhandled special keys for debugging
                            if self.debug_mode:
                                logging.debug(f"TUI_DEBUG: Unhandled special key: {repr(key)}")
                    decoded = key.decode("utf-8", errors="ignore").lower()
                    if self.debug_mode:
                        logging.debug(f"TUI_DEBUG: Decoded key: {repr(decoded)}")
                    return decoded
            else:
                # Unix/Linux: Use select for non-blocking check
                if self.select.select([sys.stdin], [], [], 0)[0]:
                    key = sys.stdin.read(1)
                    if self.debug_mode:
                        logging.debug(f"TUI_DEBUG: Unix - Raw key received: {repr(key)}")
                    # Handle escape sequences for arrow keys and special keys
                    if key == "\x1b":  # ESC
                        if self.debug_mode:
                            logging.debug("TUI_DEBUG: Unix - ESC character detected, checking for arrow sequence...")

                        # CRITICAL FIX: Container/TTY environments have extreme latency.
                        # Arrow keys send 3-byte sequences: ESC [ {A|B|C|D}
                        # The ESC arrives first, then the remaining bytes with significant latency.
                        # Container SSH forwarding can introduce >200ms inter-byte delays.
                        import time

                        # Progressive read strategy with multiple waits to handle variable latency
                        remaining_chars = ""
                        max_attempts = 4
                        wait_increment = 0.05  # 50ms per attempt = up to 200ms total

                        for attempt in range(max_attempts):
                            # Check if data already available
                            if self.select.select([sys.stdin], [], [], 0)[0]:
                                # Read all currently buffered data
                                while self.select.select([sys.stdin], [], [], 0)[0]:
                                    char = sys.stdin.read(1)
                                    remaining_chars += char
                                    if self.debug_mode:
                                        esc_char = "\x1b"
                                        full_sequence = esc_char + remaining_chars
                                        logging.debug(
                                            f"TUI_DEBUG: Unix - Read char: {repr(char)}, sequence so far: {repr(full_sequence)}"  # noqa: E501
                                        )

                                # If we got a complete arrow sequence, stop waiting
                                if remaining_chars.startswith("[") and len(remaining_chars) >= 2:
                                    if remaining_chars[1] in "ABCD":
                                        if self.debug_mode:
                                            logging.debug(
                                                f"TUI_DEBUG: Unix - Complete arrow sequence detected early (attempt {attempt + 1})"  # noqa: E501
                                            )
                                        break

                            # If this isn't the last attempt and we haven't found a complete sequence, wait for more data  # noqa: E501
                            if attempt < max_attempts - 1:
                                time.sleep(wait_increment)
                                if self.debug_mode:
                                    logging.debug(
                                        f"TUI_DEBUG: Unix - Waiting for more bytes (attempt {attempt + 1}/{max_attempts})"  # noqa: E501
                                    )

                        if self.debug_mode:
                            esc_char = "\x1b"
                            full_sequence = esc_char + remaining_chars
                            logging.debug(f"TUI_DEBUG: Unix - Complete escape sequence: {repr(full_sequence)}")

                        # Parse the complete escape sequence
                        if remaining_chars.startswith("["):
                            arrow_code = remaining_chars[1:2] if len(remaining_chars) > 1 else ""

                            if arrow_code == "A":
                                if self.debug_mode:
                                    logging.debug("TUI_DEBUG: Unix - UP arrow detected")
                                return "up"
                            elif arrow_code == "B":
                                if self.debug_mode:
                                    logging.debug("TUI_DEBUG: Unix - DOWN arrow detected")
                                return "down"
                            elif arrow_code == "C":
                                if self.debug_mode:
                                    logging.debug("TUI_DEBUG: Unix - RIGHT arrow detected")
                                return "right"
                            elif arrow_code == "D":
                                if self.debug_mode:
                                    logging.debug("TUI_DEBUG: Unix - LEFT arrow detected")
                                return "left"
                            elif arrow_code == "5" and len(remaining_chars) > 2 and remaining_chars[2] == "~":
                                if self.debug_mode:
                                    logging.debug("TUI_DEBUG: Page Up key detected (Unix)")
                                return "page_up"
                            elif arrow_code == "6" and len(remaining_chars) > 2 and remaining_chars[2] == "~":
                                if self.debug_mode:
                                    logging.debug("TUI_DEBUG: Page Down key detected (Unix)")
                                return "page_down"
                            elif arrow_code == "H":  # Home
                                return "h"
                            elif arrow_code == "F":  # End
                                return "e"
                            else:
                                if self.debug_mode:
                                    logging.debug(f"TUI_DEBUG: Unix - Unrecognized escape sequence: ESC[{arrow_code}")
                                return None
                        elif remaining_chars:
                            if self.debug_mode:
                                logging.debug(
                                    f"TUI_DEBUG: Unix - ESC followed by non-bracket sequence: {repr(remaining_chars)}"
                                )
                            return None
                        else:
                            if self.debug_mode:
                                logging.debug("TUI_DEBUG: Unix - Standalone ESCAPE key (no following characters)")
                        return "escape"
                    return key.lower()
        except Exception as error:
            logging.debug(f"TUI_MODE: Keyboard input error - {error}")
        return None

    def create_layout(self):  # type: ignore[no-untyped-def]  # noqa: C901, PLR0912, PLR0915
        """Create the TUI layout with hierarchical API navigation.

        Shows:
        - Breadcrumb header (current location in mistapi)
        - Left: List of modules/functions at current level
        - Right: Details panel (function signature, docstring, or result)

        Returns:
            Panel: Rich Panel containing the complete hierarchical layout
        """
        if self.debug_mode:
            logging.debug(
                f"TUI_DEBUG: create_layout() called - execution_state={self.execution_state}, path={self.current_path}, selection={self.current_selection}"  # noqa: E501
            )

        from rich.console import Group

        # Use fixed standard dimensions to prevent flickering
        # Standard terminal is typically 80x24, but we'll use comfortable modern size
        FIXED_PANEL_HEIGHT = 20  # Fixed height for stable rendering
        available_height = FIXED_PANEL_HEIGHT

        # Create breadcrumb display with btop-style header
        breadcrumb_text = f"[bold bright_cyan]{self.breadcrumb}[/bold bright_cyan]"
        if self.current_path:
            path_display = " -> ".join(self.current_path)
            breadcrumb_text += f" [dim bright_black]-> {path_display}[/dim bright_black]"

        breadcrumb_panel = self.Panel(
            breadcrumb_text, style="bright_white on grey11", border_style="bright_cyan", box=self.box.ROUNDED
        )

        # Miller Columns layout: each hierarchy level gets its own vertical column
        # btop-inspired color scheme: cyan borders, green accents, orange highlights

        # Create current level items column with btop-style colors and scrolling viewport
        # Calculate maximum name length for dynamic column width
        max_name_length = max((len(item.get("name", "")) for item in self.current_items), default=10)

        # Get terminal width and calculate percentage-based width for left panel
        # Use 40% of terminal width to ensure full names display without truncation

        terminal_width, _ = shutil.get_terminal_size()
        percentage_width = int(terminal_width * 0.40)

        # Account for Rich table/panel overhead:
        # - Table padding: (0, 1) = 2 chars left+right
        # - Grid padding: 1 = 2 chars
        # - Row content: prefix(1) + icon(2) + spaces(3) = 6 chars
        # Total overhead: ~10 chars
        content_width_needed = max_name_length + 10

        # Use percentage width, but ensure it fits content (min 35 chars for readability)
        column_width = max(35, min(content_width_needed, percentage_width))

        if self.debug_mode:
            logging.debug(
                f"TUI_DEBUG: Column sizing - terminal_width={terminal_width}, max_name={max_name_length}, "
                f"percentage_width={percentage_width}, final_column_width={column_width}"
            )

        items_table = self.Table(show_header=False, box=self.box.ROUNDED, padding=(0, 1))
        items_table.add_column("Item", style="white", width=column_width, no_wrap=False, overflow="ellipsis")

        # Calculate viewport for scrolling (show items around current selection)
        # Reserve 2 lines for panel borders, use remaining for items
        viewport_height = available_height - 2
        total_items = len(self.current_items)

        # Calculate scroll offset to keep selection visible
        # Try to keep selection in middle of viewport when possible
        if total_items <= viewport_height:
            # All items fit, no scrolling needed
            viewport_start = 0
            viewport_end = total_items
            if self.debug_mode:
                logging.debug(
                    f"TUI_DEBUG: All items fit - showing {total_items} items (viewport height: {viewport_height})"
                )
        else:
            # Need scrolling - center selection in viewport
            viewport_start = max(0, self.current_selection - viewport_height // 2)
            viewport_end = min(total_items, viewport_start + viewport_height)

            # Adjust if we're near the end
            if viewport_end == total_items:
                viewport_start = max(0, total_items - viewport_height)

            if self.debug_mode:
                logging.debug(
                    f"TUI_DEBUG: Scrolling viewport - selection={self.current_selection}, total={total_items}, "
                    f"viewport=[{viewport_start}:{viewport_end}], visible_items={viewport_end - viewport_start}"
                )

        # Render only visible items in viewport
        for idx in range(viewport_start, viewport_end):
            item = self.current_items[idx]
            item_type = item.get("type", "unknown")
            item_name = item.get("name", "unknown")

            # btop-inspired colors: cyan for modules, green for functions
            if item_type == "module":
                icon = ">"  # Right arrow for directories (like btop)
                color = "bright_cyan"
            elif item_type == "function":
                icon = "*"  # Bullet for items
                color = "bright_green"
            elif item_type == "error":
                icon = "x"
                color = "bright_red"
            else:
                icon = "-"
                color = "dim"

            # Highlight selected item with orange/yellow (btop highlight style)
            if idx == self.current_selection:
                prefix = "#"  # Solid block for selection
                color = "bright_yellow"
                style = "bold"

                if self.debug_mode:
                    logging.debug(
                        f"TUI_DEBUG: Highlighting selection - index={idx}, name='{item_name}', "
                        f"type={item_type}, viewport_position={idx - viewport_start}"
                    )
            else:
                prefix = " "
                style = ""

            # Don't truncate - let the full name show
            display_name = item_name

            if style:
                items_table.add_row(f"[{style} {color}]{prefix} {icon} {display_name}[/{style} {color}]")
            else:
                items_table.add_row(f"[{color}]{prefix} {icon} {display_name}[/{color}]")

        # Add scroll indicators if needed
        if self.debug_mode and total_items > viewport_height:
            logging.debug(
                f"TUI_DEBUG: Scroll indicators - can_scroll_up={viewport_start > 0}, "
                f"can_scroll_down={viewport_end < total_items}"
            )

        # Current level column with btop-style cyan border
        level_name = self.current_path[-1] if self.current_path else "root"
        # Dynamic width based on content, plus padding for borders (4 chars)
        panel_width = column_width + 4
        items_panel = self.Panel(
            items_table,
            title=f"[bold bright_cyan]{level_name}[/bold bright_cyan]",
            border_style="bright_cyan",
            height=available_height,
            width=panel_width,
        )

        # Create details panel (right panel)
        details_lines = []

        if 0 <= self.current_selection < len(self.current_items):
            selected = self.current_items[self.current_selection]
            item_type = selected.get("type")

            if item_type == "function":
                # Show function signature and docstring
                func_name = selected.get("name", "unknown")
                signature = selected.get("signature", "(...)")
                full_doc = selected.get("full_doc", "No documentation available")

                details_lines.append(f"[bold bright_green]Function:[/bold bright_green] {func_name}")
                details_lines.append("")
                details_lines.append("[bold bright_cyan]Signature:[/bold bright_cyan]")
                details_lines.append(f"[bright_yellow]{func_name}{signature}[/bright_yellow]")
                details_lines.append("")
                details_lines.append("[bold]Documentation:[/bold]")

                # Limit doc display to fit available height
                doc_lines = full_doc.split("\n")
                max_doc_lines = max(5, available_height - 10)  # Reserve space for header/signature
                for line in doc_lines[:max_doc_lines]:
                    details_lines.append(line)
                if len(doc_lines) > max_doc_lines:
                    details_lines.append(f"[dim]...(truncated, {len(doc_lines) - max_doc_lines} more lines)[/dim]")

            elif item_type == "module":
                # Show module info
                module_name = selected.get("name", "unknown")
                details_lines.append(f"[bold bright_cyan]Module:[/bold bright_cyan] {module_name}")
                details_lines.append("")
                details_lines.append("[dim bright_black]Press Enter to explore this module[/dim bright_black]")

            elif item_type == "error":
                details_lines.append("[bold red]Error:[/bold red]")
                details_lines.append(selected.get("description", "Unknown error"))

        # Show last result if available (limit to prevent overflow)
        if self.last_result is not None:
            details_lines.append("")
            details_lines.append("[bold green]Last Result:[/bold green]")
            result_preview = str(self.last_result)
            max_result_chars = 300
            if len(result_preview) > max_result_chars:
                result_preview = result_preview[:max_result_chars] + "..."
            # Limit result lines too
            result_lines = result_preview.split("\n")
            max_result_lines = 10
            for line in result_lines[:max_result_lines]:
                details_lines.append(f"[dim]{line}[/dim]")
            if len(result_lines) > max_result_lines:
                details_lines.append(f"[dim]...({len(result_lines) - max_result_lines} more lines)[/dim]")

        if self.last_error:
            details_lines.append("")
            details_lines.append("[bold red]Last Error:[/bold red]")
            details_lines.append(f"[dim]{self.last_error}[/dim]")

        if not details_lines:
            details_lines.append("[dim]Select an item to view details[/dim]")

        # Limit total details lines to fit in panel
        max_total_lines = available_height - 2  # Account for panel borders
        if len(details_lines) > max_total_lines:
            details_lines = details_lines[:max_total_lines]
            details_lines.append("[dim]...(content truncated to fit screen)[/dim]")

        details_panel = self.Panel(
            "\n".join(details_lines),
            title="[bold bright_green]Details[/bold bright_green]",
            border_style="bright_green",
            box=self.box.ROUNDED,
            height=available_height,
        )

        # Create output panel at bottom for execution results and input prompts
        output_height = 8
        output_content = []

        if self.execution_state == "prompting":
            # Show parameter input prompt with clear header
            output_content.append("[bold bright_cyan]=== Function Execution - Parameter Input ===[/bold bright_cyan]")
            output_content.append("")
            if self.current_function:
                output_content.append(
                    f"[bright_green]Function:[/bright_green] {self.current_function.get('name', 'unknown')}"
                )

            # Show current parameter being requested with prominent display
            if self.current_param_index < len(self.param_list):
                output_content.append("")
                param_info = self.param_list[self.current_param_index]
                param_name = param_info["name"]
                required_tag = "[red][REQUIRED][/red]" if not param_info.get("has_default") else "[dim][optional][/dim]"
                default_info = (
                    f" [dim](default: {param_info.get('default')})[/dim]" if param_info.get("has_default") else ""
                )

                # Create a clear input prompt box
                output_content.append(
                    f"[bold bright_yellow]+-- Input Needed: {param_name} {required_tag}[/bold bright_yellow]"
                )
                if default_info:
                    output_content.append(f"[bright_yellow]|[/bright_yellow] {default_info}")
                output_content.append(
                    f"[bright_yellow]+-->[/bright_yellow] [bold white on grey11]{self.input_buffer}#[/bold white on grey11]"  # noqa: E501
                )

            # Show previously collected parameters at bottom
            if self.current_param_index > 0:
                output_content.append("")
                output_content.append(
                    f"[dim]Already provided ({self.current_param_index}/{len(self.param_list)}):[/dim]"
                )
                for idx in range(min(3, self.current_param_index)):  # Show last 3
                    param_info = self.param_list[self.current_param_index - 1 - idx]
                    param_name = param_info["name"]
                    param_value = self.function_params.get(param_name, "")
                    # Redact sensitive values
                    if any(x in param_name.lower() for x in ["pass", "token", "key", "secret"]):
                        display_value = "***REDACTED***"
                    else:
                        display_value = str(param_value)[:40]  # Truncate long values
                    output_content.append(f"  [dim][OK] {param_name}:[/dim] {display_value}")

        elif self.execution_state == "executing":
            output_content.append("[bold bright_cyan]Executing API Call...[/bold bright_cyan]")
            output_content.append("")
            output_content.append("[dim]Please wait...[/dim]")

        elif self.output_lines:
            # Show output from last execution
            for line in self.output_lines[-output_height + 2 :]:  # Show last N lines that fit
                output_content.append(line)
        else:
            output_content.append("[dim]Output will appear here after executing functions[/dim]")

        output_panel = self.Panel(
            "\n".join(output_content) if output_content else "[dim]No output[/dim]",
            title="[bold bright_magenta]Output[/bold bright_magenta]",
            border_style="bright_magenta",
            box=self.box.ROUNDED,
            height=output_height,
        )

        # Create help text with btop-style colors
        if self.execution_state == "viewing_results":
            help_text = (
                "[bold bright_yellow]Results View:[/bold bright_yellow] "
                "[bright_cyan]Up/Dn[/bright_cyan] Scroll (10)  "
                "[bright_cyan]PgUp/PgDn[/bright_cyan] Scroll (20)  "
                "[bright_green]H[/bright_green] Top  "
                "[bright_green]E[/bright_green] End  "
                "[bright_magenta]Esc[/bright_magenta] Close  "
                "[bright_red]Q[/bright_red] Quit"
            )
        elif self.execution_state == "prompting":
            help_text = (
                "[bold bright_yellow]Input Mode:[/bold bright_yellow] "
                "[bright_green]Type[/bright_green] value  "
                "[bright_cyan]Enter[/bright_cyan] Submit  "
                "[bright_magenta]Esc[/bright_magenta] Cancel"
            )
        else:
            help_text = (
                "[bold bright_yellow]Navigation:[/bold bright_yellow] "
                "[bright_cyan]Up/Dn[/bright_cyan] Move  "
                "[bright_green]Enter[/bright_green] Drill/Execute  "
                "[bright_magenta]Esc[/bright_magenta] Back  "
                "[bright_red]Q[/bright_red] Quit"
            )

        # Combine into side-by-side layout using Table.grid for reliable column rendering
        from rich.table import Table as RichTable

        layout_table = RichTable.grid(padding=1, expand=True)
        # Use dynamic panel width (already includes border padding)
        layout_table.add_column(width=panel_width, no_wrap=True)
        layout_table.add_column(ratio=1)  # Details column (fills remaining space)
        layout_table.add_row(items_panel, details_panel)

        # Group all elements
        content_group = Group(breadcrumb_panel, "", layout_table, "", output_panel, "", help_text)

        main_panel = self.Panel(
            content_group,
            title="[bold bright_cyan]MistHelper TUI[/bold bright_cyan]",
            border_style="bright_blue",
            box=self.box.ROUNDED,
        )

        # If viewing results, show the results grid instead of main panel
        if self.execution_state == "viewing_results":
            results_grid = self._create_results_grid()  # type: ignore[no-untyped-call]
            if results_grid:
                # Create a Layout to properly position help text at the bottom
                # Use minimum_size=0 to prevent width constraints
                results_layout = self.Layout(minimum_size=0)
                results_layout.split_column(
                    self.Layout(results_grid, name="results", ratio=95, minimum_size=0),
                    self.Layout(
                        self.Panel(
                            "[yellow]Controls: [bright_yellow]L/R[/bright_yellow] Results | [bright_yellow]Up/Dn[/bright_yellow] Scroll (10) | [bright_yellow]PgUp/PgDn[/bright_yellow] Scroll (20) | [bright_yellow]H[/bright_yellow] Top | [bright_yellow]E[/bright_yellow] End | [bright_yellow]ESC[/bright_yellow] Close | [bright_yellow]Q[/bright_yellow] Quit[/yellow]",  # noqa: E501
                            border_style="dim",
                            box=self.box.SIMPLE,
                        ),
                        name="footer",
                        size=3,  # Fixed height for footer (1 line text + 2 lines borders)
                    ),
                )
                if self.debug_mode:
                    logging.debug("TUI_DEBUG: create_layout() returning results grid with footer layout")
                return results_layout

        if self.debug_mode:
            logging.debug("TUI_DEBUG: create_layout() completed successfully - returning main_panel")

        return main_panel

    def handle_input(self, key):  # type: ignore[no-untyped-def]  # noqa: C901, PLR0912, PLR0915
        """Handle keyboard input for Miller Columns navigation and input prompts.

        Controls (Navigation Mode):
        - Up/Down: Navigate through items in current column
        - Enter: Drill into module (shows new column to right) or execute function
        - Escape: Go back up one level (removes rightmost column)
        - Q: Quit TUI mode

        Controls (Input Mode):
        - Type: Add characters to input buffer
        - Backspace: Remove last character
        - Enter: Submit current parameter value
        - Escape: Cancel execution

        Args:
            key (str): Key pressed by user
        """
        if self.debug_mode:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            logging.debug(
                f"TUI_DEBUG: [{timestamp}] Key pressed: {repr(key)} (state={self.execution_state}, path={self.current_path}, selection={self.current_selection})"  # noqa: E501
            )

        # Handle results viewing mode
        if self.execution_state == "viewing_results":
            if self.debug_mode:
                logging.debug(f"TUI_DEBUG: In viewing_results mode - testing key {repr(key)} against handlers")

            if key == "left":
                # Previous result
                self.results_scroll_offset = max(0, self.results_scroll_offset - 1)
                self.result_row_scroll = 0  # Reset row scroll for new result
                if self.debug_mode:
                    logging.debug(f"TUI_DEBUG: Previous result - offset now {self.results_scroll_offset}")
            elif key == "right":
                # Next result
                if self.last_parsed_data:
                    results = self.last_parsed_data.get("results", [])
                    max_offset = max(0, len(results) - 1)
                    self.results_scroll_offset = min(max_offset, self.results_scroll_offset + 1)
                    self.result_row_scroll = 0  # Reset row scroll for new result
                    if self.debug_mode:
                        logging.debug(
                            f"TUI_DEBUG: Next result - offset now {self.results_scroll_offset} (max {max_offset})"
                        )
            elif key == "up":
                # Scroll up within current result (show earlier rows) - 10 rows at a time for faster navigation
                old_scroll = self.result_row_scroll
                self.result_row_scroll = max(0, self.result_row_scroll - 10)
                if self.debug_mode:
                    logging.debug(f"TUI_DEBUG: UP key - row scroll {old_scroll} -> {self.result_row_scroll}")
            elif key == "down":
                # Scroll down within current result (show later rows) - 10 rows at a time for faster navigation
                # Don't cap here - let _create_results_grid() handle bounds checking
                old_scroll = self.result_row_scroll
                self.result_row_scroll += 10
                if self.debug_mode:
                    logging.debug(f"TUI_DEBUG: DOWN key - row scroll {old_scroll} -> {self.result_row_scroll}")
            elif key == "page_up":
                # Page up - scroll up 20 rows at a time (2x faster than arrow keys)
                self.result_row_scroll = max(0, self.result_row_scroll - 20)
                if self.debug_mode:
                    logging.debug(f"TUI_DEBUG: Page up - row offset now {self.result_row_scroll}")
            elif key == "page_down":
                # Page down - scroll down 20 rows at a time (2x faster than arrow keys)
                self.result_row_scroll += 20
                if self.debug_mode:
                    logging.debug(f"TUI_DEBUG: Page down - row offset now {self.result_row_scroll}")
            elif key == "h":
                # Jump to top (Home)
                self.result_row_scroll = 0
                if self.debug_mode:
                    logging.debug(f"TUI_DEBUG: Jump to top - row offset now {self.result_row_scroll}")
            elif key == "e":
                # Jump to end
                if self.last_parsed_data:
                    results = self.last_parsed_data.get("results", [])
                    if results and self.results_scroll_offset < len(results):
                        # Set to large number, windowing logic will cap it properly
                        self.result_row_scroll = 999999
                        if self.debug_mode:
                            logging.debug("TUI_DEBUG: Jump to end - row offset set to max")
            elif key in ["escape", "\x1b"]:
                # Close results grid
                self.execution_state = None
                self.results_scroll_offset = 0
                self.result_row_scroll = 0
                if self.debug_mode:
                    logging.debug("TUI_DEBUG: Closed results grid, returned to navigation")
            elif key == "q":
                # Quit from results view
                self.running = False
                if self.debug_mode:
                    logging.debug("TUI_DEBUG: Q pressed in results view - quitting")
            else:
                # Unhandled key in results view
                if self.debug_mode:
                    logging.debug(f"TUI_DEBUG: Unhandled key in viewing_results mode: {repr(key)}")
            return  # Don't process navigation commands while viewing results

        # Handle input mode for parameter collection
        if self.execution_state == "prompting":
            if key in ["\r", "\n"]:  # Enter - submit parameter
                self._submit_parameter()  # type: ignore[no-untyped-call]
            elif key in ["escape", "\x1b"]:  # Escape - cancel execution
                self._cancel_execution()  # type: ignore[no-untyped-call]
            elif key == "\x7f" or key == "\x08" or key == "backspace":  # Backspace
                if self.input_buffer:
                    self.input_buffer = self.input_buffer[:-1]
            elif len(key) == 1 and key.isprintable():  # Regular character
                self.input_buffer += key
            return  # Don't process navigation commands in input mode

        # Navigation mode
        if key == "up":
            if self.debug_mode:
                logging.debug("TUI_DEBUG: Processing UP arrow key")
            # Move selection up in current column
            old_selection = self.current_selection
            self.current_selection = max(0, self.current_selection - 1)

            if self.debug_mode:
                item_name = (
                    self.current_items[self.current_selection].get("name", "unknown") if self.current_items else "none"
                )
                logging.debug(
                    f"TUI_DEBUG: UP arrow - selection moved {old_selection} -> {self.current_selection} (now on: {item_name})"  # noqa: E501
                )
                logging.debug("TUI_DEBUG: UP arrow processing complete")

        elif key == "down":
            if self.debug_mode:
                logging.debug("TUI_DEBUG: Processing DOWN arrow key")
            # Move selection down in current column
            old_selection = self.current_selection
            self.current_selection = min(len(self.current_items) - 1, self.current_selection + 1)

            if self.debug_mode:
                item_name = (
                    self.current_items[self.current_selection].get("name", "unknown") if self.current_items else "none"
                )
                logging.debug(
                    f"TUI_DEBUG: DOWN arrow - selection moved {old_selection} -> {self.current_selection} (now on: {item_name})"  # noqa: E501
                )
                logging.debug("TUI_DEBUG: DOWN arrow processing complete")

        elif key in ["\r", "\n"]:  # Enter key
            if self.debug_mode:
                logging.debug("TUI_DEBUG: Processing ENTER key")
            # Select current item
            if 0 <= self.current_selection < len(self.current_items):
                selected = self.current_items[self.current_selection]
                item_type = selected.get("type")
                item_name = selected.get("name")

                if self.debug_mode:
                    logging.debug(f"TUI_DEBUG: ENTER pressed - selected item: {item_name} (type={item_type})")

                if item_type == "module":
                    # Drill into module
                    module_name = selected.get("name")
                    self.current_path.append(module_name)
                    self.current_selection = 0
                    self._discover_current_level()  # type: ignore[no-untyped-call]
                    logging.info(f"TUI: Navigated into module: {module_name}")

                    if self.debug_mode:
                        logging.debug(
                            f"TUI_DEBUG: Module drill-down complete - new path: {self.current_path}, items count: {len(self.current_items)}"  # noqa: E501
                        )

                elif item_type == "function":
                    # Start function execution (parameter prompting)
                    if self.debug_mode:
                        logging.debug(f"TUI_DEBUG: Starting function execution: {item_name}")
                    self._start_function_execution(selected)  # type: ignore[no-untyped-call]

                if self.debug_mode:
                    logging.debug("TUI_DEBUG: ENTER key processing complete")

        elif key in ["escape", "\x1b"]:
            if self.debug_mode:
                logging.debug(f"TUI_DEBUG: Processing ESCAPE key - current path: {self.current_path}")
            # Go back up one level
            if self.current_path:
                removed = self.current_path.pop()
                self.current_selection = 0
                self._discover_current_level()  # type: ignore[no-untyped-call]
                logging.info(f"TUI: Navigated back from: {removed}")

                if self.debug_mode:
                    logging.debug(
                        f"TUI_DEBUG: ESCAPE pressed - backed out of {removed}, new path: {self.current_path}, items count: {len(self.current_items)}"  # noqa: E501
                    )
            else:
                # Already at root, escape quits
                if self.debug_mode:
                    logging.debug("TUI_DEBUG: ESCAPE pressed at root level - quitting TUI")
                self.running = False

            if self.debug_mode:
                logging.debug("TUI_DEBUG: ESCAPE key processing complete")

        elif key == "q":
            if self.debug_mode:
                logging.debug("TUI_DEBUG: Processing Q key - initiating quit")
            # Quit TUI mode
            self.running = False
            if self.debug_mode:
                logging.debug("TUI_DEBUG: Q key processing complete - running flag set to False")

        else:
            # Unknown/unhandled key
            if self.debug_mode:
                logging.debug(f"TUI_DEBUG: Unhandled key: {repr(key)}")

    def _start_function_execution(self, selected_item):  # type: ignore[no-untyped-def]  # noqa: C901, PLR0912
        """Start function execution by preparing parameter collection."""
        import inspect

        self.current_function = selected_item
        func = selected_item.get("object")
        func_name = selected_item.get("name")

        if not func or not callable(func):
            self.output_lines = ["[ERROR] Selected item is not callable"]
            return

        if self.debug_mode:
            logging.debug(f"TUI_DEBUG: Preparing parameter collection for: {func_name}")

        # Get function signature
        try:
            sig = inspect.signature(func)
            self.param_list = []
            self.function_params = {}

            # Build list of parameters to collect
            for param_name, param in sig.parameters.items():
                if param_name == "self":
                    continue

                # Auto-fill mist_session
                if param_name in ("mist_session", "apisession"):
                    if hasattr(self, "apisession") and self.apisession is not None:
                        self.function_params[param_name] = self.apisession
                        continue
                    else:
                        self.output_lines = ["[ERROR] API session not available"]
                        return

                # Auto-fill from .env file (not system environment)
                if param_name in self.dotenv_values:
                    self.function_params[param_name] = self.dotenv_values[param_name]
                    if self.debug_mode:
                        logging.debug(
                            f"TUI_DEBUG: Auto-filled {param_name} from .env file: {self.dotenv_values[param_name]}"
                        )
                    continue

                # Add to collection list
                has_default = param.default != inspect.Parameter.empty
                self.param_list.append(
                    {"name": param_name, "has_default": has_default, "default": param.default if has_default else None}
                )

            # Start prompting for parameters
            if self.param_list:
                self.execution_state = "prompting"
                self.current_param_index = 0
                self.input_buffer = ""
                if self.debug_mode:
                    logging.debug(
                        f"TUI_DEBUG: Starting parameter prompting - {len(self.param_list)} parameters to collect"
                    )
            else:
                # No parameters needed, execute immediately
                self._execute_function()  # type: ignore[no-untyped-call]

        except Exception as error:
            self.output_lines = [f"[ERROR] Failed to prepare execution: {error}"]
            logging.error(f"TUI: Failed to prepare execution of {func_name}: {error}", exc_info=True)

    def _submit_parameter(self):  # type: ignore[no-untyped-def]  # noqa: C901, PLR0912
        """Submit the current parameter value and move to next parameter or execute.

        Rules:
        - Required parameters: Must have a value, error if empty
        - Optional parameters with value: Add to function params
        - Optional parameters without value (blank): Skip entirely, don't add to params
        """
        if self.current_param_index >= len(self.param_list):
            return

        param_info = self.param_list[self.current_param_index]
        param_name = param_info["name"]
        value = self.input_buffer.strip()

        # Handle parameter based on required/optional and value presence
        if not value:
            # Empty input
            if not param_info["has_default"]:
                # Required parameter missing
                self.output_lines = [f"[ERROR] {param_name} is required"]
                return
            else:
                # Special handling for 'limit' parameter - default to 1000
                if param_name == "limit":
                    self.function_params[param_name] = 1000
                    if self.debug_mode:
                        logging.debug(f"TUI_DEBUG: Parameter set to default 1000 - {param_name}")
                else:
                    # Optional parameter with no value - explicitly set to None to override function defaults
                    self.function_params[param_name] = None
                    if self.debug_mode:
                        logging.debug(f"TUI_DEBUG: Parameter set to None (optional, no value provided) - {param_name}")
        else:
            # Value provided - store parameter (convert to int if it's the limit parameter)
            if param_name == "limit":
                try:
                    self.function_params[param_name] = int(value)
                    if self.debug_mode:
                        logging.debug(f"TUI_DEBUG: Parameter stored as int - {param_name}: {value}")
                except ValueError:
                    self.output_lines = [f"[ERROR] {param_name} must be a number"]
                    return
            else:
                self.function_params[param_name] = value
                if self.debug_mode:
                    display_value = (
                        "***REDACTED***"
                        if any(x in param_name.lower() for x in ["pass", "token", "key", "secret"])
                        else value
                    )
                    logging.debug(f"TUI_DEBUG: Parameter stored - {param_name}: {display_value}")

        # Move to next parameter
        self.current_param_index += 1
        self.input_buffer = ""

        # Check if all parameters collected
        if self.current_param_index >= len(self.param_list):
            self._execute_function()  # type: ignore[no-untyped-call]

    def _cancel_execution(self):  # type: ignore[no-untyped-def]
        """Cancel the current function execution."""
        if self.debug_mode:
            logging.debug("TUI_DEBUG: Function execution cancelled by user")

        self.execution_state = None
        self.current_function = None
        self.function_params = {}
        self.param_list = []
        self.current_param_index = 0
        self.input_buffer = ""
        self.output_lines = ["[CANCELLED] Execution cancelled by user"]

    def _execute_function(self):  # type: ignore[no-untyped-def]  # noqa: C901, PLR0912, PLR0915
        """Execute the function with collected parameters and handle pagination."""
        if not self.current_function:
            return

        func = self.current_function.get("object")
        func_name = self.current_function.get("name")

        self.execution_state = "executing"
        self.output_lines = ["[EXECUTING] Running API call..."]

        if self.debug_mode:
            param_summary = {
                k: "***REDACTED***" if any(x in k.lower() for x in ["pass", "token", "key", "secret"]) else v
                for k, v in self.function_params.items()
            }
            logging.debug(f"TUI_DEBUG: Executing {func_name} with parameters: {param_summary}")

        try:
            # Execute the API call
            result = func(**self.function_params)

            # Extract actual data from APIResponse if applicable
            parsed_data = self._parse_api_response(result)  # type: ignore[no-untyped-call]

            # Handle pagination using mistapi's next() method (cursor-based pagination)
            if isinstance(parsed_data, dict) and "results" in parsed_data:
                accumulated_results = list(parsed_data.get("results", []))
                page_count = 1

                # Check if we should paginate (next URL exists means more results available)
                while hasattr(result, "next") and result.next is not None:
                    page_count += 1
                    self.output_lines = [
                        f"[EXECUTING] Fetching page {page_count} (total results so far: {len(accumulated_results)})..."
                    ]

                    if self.debug_mode:
                        logging.debug(
                            f"TUI_DEBUG: Following next URL for pagination - page {page_count}, next: {result.next}"
                        )

                    try:
                        # Get the next page using the mist_session and the next URL
                        # result.next is a string URL, not a method
                        next_url = result.next

                        # Use the mist_session from parameters to make the next request
                        mist_session = self.function_params.get("mist_session") or self.function_params.get(
                            "apisession"
                        )
                        if mist_session and next_url:
                            # Make a GET request to the next URL
                            result = mist_session.mist_get(next_url)
                        else:
                            if self.debug_mode:
                                logging.debug("TUI_DEBUG: Missing mist_session or next_url, stopping pagination")
                            break

                        if result:
                            parsed_data = self._parse_api_response(result)  # type: ignore[no-untyped-call]

                            if isinstance(parsed_data, dict) and "results" in parsed_data:
                                new_results = parsed_data.get("results", [])
                                if new_results:
                                    accumulated_results.extend(new_results)

                                    if self.debug_mode:
                                        logging.debug(
                                            f"TUI_DEBUG: Page {page_count} retrieved - added {len(new_results)} results (total: {len(accumulated_results)})"  # noqa: E501
                                        )
                                else:
                                    # No more results
                                    if self.debug_mode:
                                        logging.debug(
                                            f"TUI_DEBUG: Page {page_count} returned no results, stopping pagination"
                                        )
                                    break
                            else:
                                if self.debug_mode:
                                    logging.debug(
                                        f"TUI_DEBUG: Page {page_count} response format unexpected, stopping pagination"
                                    )
                                break
                        else:
                            if self.debug_mode:
                                logging.debug("TUI_DEBUG: next() returned None, stopping pagination")
                            break
                    except Exception as e:
                        if self.debug_mode:
                            logging.debug(f"TUI_DEBUG: Error during pagination: {e}, stopping")
                        break

                # Update parsed_data with all accumulated results
                if page_count > 1:
                    parsed_data["results"] = accumulated_results
                    if self.debug_mode:
                        logging.debug(
                            f"TUI_DEBUG: Pagination complete - {page_count} pages, {len(accumulated_results)} total results"  # noqa: E501
                        )
                elif hasattr(result, "next") and result.next is not None:
                    if self.debug_mode:
                        logging.debug(
                            "TUI_DEBUG: Single page retrieved but next URL exists - may need different pagination approach"  # noqa: E501
                        )

            # Save result to file if debug mode is enabled
            if self.debug_mode:
                self._save_debug_result(func_name, result, parsed_data)  # type: ignore[no-untyped-call]

            # Store and format result
            self.last_result = result
            self.last_parsed_data = parsed_data
            self.output_lines = self._format_result_output(parsed_data, func_name, result)  # type: ignore[no-untyped-call]

            # Check if results should be displayed in popup grid
            if self._should_show_results_grid(parsed_data):  # type: ignore[no-untyped-call]
                self.execution_state = "viewing_results"
                self.results_scroll_offset = 0
                logging.info(
                    f"TUI: Results grid available - entering viewing_results state with {len(parsed_data.get('results', []))} items"  # noqa: E501
                )
                if self.debug_mode:
                    logging.debug("TUI_DEBUG: Results available for grid view - entering viewing_results state")
            else:
                logging.info(f"TUI: Execution complete - no grid display (data type: {type(parsed_data).__name__})")

            logging.info(f"TUI: Successfully executed {func_name}")

        except Exception as error:
            self.last_error = str(error)
            self.output_lines = ["[ERROR] Execution failed", f"Function: {func_name}", f"Error: {error}"]
            logging.error(f"TUI: Execution of {func_name} failed - {error}", exc_info=True)

            if self.debug_mode:
                logging.debug(f"TUI_DEBUG: Exception details: {type(error).__name__}: {error}")

        finally:
            # Reset execution state (but preserve 'viewing_results' if set)
            if self.execution_state != "viewing_results":
                self.execution_state = None

            # Always reset these
            self.current_function = None
            self.function_params = {}
            self.param_list = []
            self.current_param_index = 0
            self.input_buffer = ""

    def _parse_api_response(self, result):  # type: ignore[no-untyped-def]
        """Parse APIResponse object to extract actual data."""
        # Check if this is a mistapi APIResponse object
        if hasattr(result, "data"):
            if self.debug_mode:
                logging.debug("TUI_DEBUG: Detected APIResponse object, extracting data attribute")
            return result.data
        else:
            return result

    def _should_show_results_grid(self, parsed_data):  # type: ignore[no-untyped-def]
        """Determine if parsed data should be shown in a grid popup.

        Returns True if:
        - Data is a dict with 'results' key
        - Results is a non-empty list
        - Results contain dict items (tabular data)
        """
        if self.debug_mode:
            logging.debug(
                f"TUI_DEBUG: Checking if results should show in grid - data type: {type(parsed_data).__name__}"
            )

        if not isinstance(parsed_data, dict):
            if self.debug_mode:
                logging.debug("TUI_DEBUG: Not a dict - skipping grid display")
            return False

        results = parsed_data.get("results")
        if self.debug_mode:
            logging.debug(
                f"TUI_DEBUG: Results type: {type(results).__name__}, length: {len(results) if isinstance(results, list) else 'N/A'}"  # noqa: E501
            )

        if not isinstance(results, list) or len(results) == 0:
            if self.debug_mode:
                logging.debug("TUI_DEBUG: Results empty or not a list - skipping grid display")
            return False

        # Check if results contain dict items (tabular data)
        if len(results) > 0 and isinstance(results[0], dict):
            if self.debug_mode:
                logging.debug(f"TUI_DEBUG: Results contain {len(results)} dict items - WILL SHOW GRID")
            return True

        if self.debug_mode:
            logging.debug("TUI_DEBUG: Results items are not dicts - skipping grid display")
        return False

    def _create_results_grid(self):  # type: ignore[no-untyped-def]  # noqa: C901, PLR0915
        """Create a Rich display showing results as individual cards/panels.

        Shows one result at a time with prev/next navigation.
        Returns a Panel containing the current result card.
        """
        if not self.last_parsed_data or not isinstance(self.last_parsed_data, dict):
            return None

        results = self.last_parsed_data.get("results", [])
        if not results:
            return None

        from rich.table import Table as RichTable

        # Calculate which result to show based on scroll offset
        current_result_idx = self.results_scroll_offset
        if current_result_idx >= len(results):
            current_result_idx = len(results) - 1
            self.results_scroll_offset = current_result_idx

        result = results[current_result_idx]

        # Format single result as a readable table
        def format_value(value, depth=0):  # type: ignore[no-untyped-def]  # noqa: C901, PLR0912
            """Format a value with proper indentation and styling."""
            if value is None or value == "":
                return "[dim]<empty>[/dim]"
            elif isinstance(value, bool):
                return f"[bright_cyan]{str(value)}[/bright_cyan]"
            elif isinstance(value, (int, float)):
                return f"[bright_green]{value}[/bright_green]"
            elif isinstance(value, str):
                # Highlight UUIDs and IPs
                if len(value) == 36 and "-" in value:  # UUID format
                    return f"[bright_magenta]{value}[/bright_magenta]"
                elif "." in value and all(part.isdigit() or part == "" for part in value.split(".")):  # IP-like
                    return f"[bright_cyan]{value}[/bright_cyan]"
                else:
                    return f"[white]{value}[/white]"
            elif isinstance(value, list):
                if not value:
                    return "[dim]<empty list>[/dim]"
                elif all(isinstance(item, (str, int, float, bool, type(None))) for item in value):
                    # Simple list - always show all items inline, no limit
                    return f"[bright_yellow][ {', '.join(str(v) if v is not None else '<empty>' for v in value)} ][/bright_yellow]"  # noqa: E501
                else:
                    # Complex list (contains dicts/lists) - will be expanded by flatten_for_display
                    return f"[yellow]v {len(value)} items (expanded below)[/yellow]"
            elif isinstance(value, dict):
                return f"[magenta]v {len(value)} keys (expanded below)[/magenta]"
            else:
                return f"[white]{str(value)}[/white]"

        def flatten_for_display(data, depth=0):  # type: ignore[no-untyped-def]  # noqa: C901, PLR0912
            """Flatten dict/list for display with proper grouping and visual hierarchy."""
            rows = []

            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, dict) and value:
                        indent = "  " * depth
                        if depth == 0:
                            key_style = (
                                f"[bold bright_cyan on grey15]{indent}> {key.upper()}[/bold bright_cyan on grey15]"
                            )
                        elif depth == 1:
                            key_style = f"[bold bright_yellow]{indent}+- {key}[/bold bright_yellow]"
                        else:
                            key_style = f"[bold white]{indent}+- {key}[/bold white]"
                        rows.append([key_style, f"[dim italic]{len(value)} fields[/dim italic]", "section_header"])
                        rows.extend(flatten_for_display(value, depth + 1))  # type: ignore[no-untyped-call]
                        if depth == 0:
                            rows.append(["", "", "separator"])
                    elif isinstance(value, list) and value and isinstance(value[0], dict):
                        indent = "  " * depth
                        if depth == 0:
                            key_style = (
                                f"[bold bright_cyan on grey15]{indent}> {key.upper()}[/bold bright_cyan on grey15]"
                            )
                        elif depth == 1:
                            key_style = f"[bold bright_yellow]{indent}+- {key}[/bold bright_yellow]"
                        else:
                            key_style = f"[bold white]{indent}+- {key}[/bold white]"
                        rows.append([key_style, f"[dim italic]{len(value)} items[/dim italic]", "section_header"])
                        # Show ALL items, fully expanded
                        for idx, item in enumerate(value):
                            sub_indent = "  " * (depth + 1)
                            rows.append([f"[magenta]{sub_indent}[{idx}][/magenta]", "", "list_item"])
                            rows.extend(flatten_for_display(item, depth + 2))  # type: ignore[no-untyped-call]
                        if depth == 0:
                            rows.append(["", "", "separator"])
                    else:
                        indent = "  " * depth
                        if depth == 0:
                            key_style = f"[bold bright_white]{indent}{key}[/bold bright_white]"
                        elif depth == 1:
                            key_style = f"[yellow]{indent}  {key}[/yellow]"
                        else:
                            key_style = f"[dim white]{indent}    {key}[/dim white]"
                        rows.append([key_style, format_value(value, 0), "value"])  # type: ignore[no-untyped-call]
            return rows

        # Create table with visual gridlines for sections
        table = RichTable(
            show_header=True,
            header_style="bold bright_cyan on grey15",
            box=self.box.HEAVY,  # Heavy box for better visual separation
            expand=True,  # Allow table to fill available space
            show_lines=True,  # Show lines between rows for grouping
            padding=(0, 1),
            row_styles=["", "on grey3"],  # Alternate row backgrounds
            width=None,  # Let it auto-size to fill panel
        )

        # Two columns: Field and Value with ratio-based widths that respect expand=True
        # Field gets 35%, Value gets 65% of available width
        table.add_column("Field", style="bright_white", ratio=35, no_wrap=False, overflow="fold")
        table.add_column("Value", style="bright_white", ratio=65, no_wrap=False, overflow="fold")

        # Add rows for this result with visual grouping and scrolling
        all_rows = flatten_for_display(result)  # type: ignore[no-untyped-call]
        total_rows = len(all_rows)

        # Calculate visible window based on actual terminal height
        # Cap at 25 rows max for better scrolling UX even on large terminals
        max_visible = min(25, self._get_terminal_height())  # type: ignore[no-untyped-call]
        start_row = min(self.result_row_scroll, max(0, total_rows - max_visible))
        end_row = min(start_row + max_visible, total_rows)

        if self.debug_mode:
            logging.debug(
                f"TUI_DEBUG: Grid windowing - total_rows={total_rows}, max_visible={max_visible}, "
                f"scroll_offset={self.result_row_scroll}, start_row={start_row}, end_row={end_row}, "
                f"will_show={end_row - start_row}_rows"
            )

        # Add only visible rows to table
        for field_name, value, row_type in all_rows[start_row:end_row]:
            if row_type == "separator":
                # Visual separator between major sections
                table.add_row("[dim]" + "-" * 40 + "[/dim]", "[dim]" + "-" * 60 + "[/dim]")
            else:
                table.add_row(field_name, value)

        # Get metadata
        total = self.last_parsed_data.get("total", len(results))
        actual_limit = self.function_params.get("limit", 1000)  # Default to 1000 if not set
        distinct = self.last_parsed_data.get("distinct", "N/A")

        # Navigation info with row scroll indicator
        nav_info = f"Result {current_result_idx + 1} of {len(results)}"
        result_pct = int(((current_result_idx + 1) / len(results)) * 100) if len(results) > 0 else 100

        # Row scroll info with scroll indicators
        if total_rows > max_visible:
            can_scroll_up = start_row > 0
            can_scroll_down = end_row < total_rows
            scroll_indicator = ""
            if can_scroll_up and can_scroll_down:
                scroll_indicator = " [bright_yellow]^v[/bright_yellow]"
            elif can_scroll_up:
                scroll_indicator = " [bright_yellow]^[/bright_yellow]"
            elif can_scroll_down:
                scroll_indicator = " [bright_yellow]v[/bright_yellow]"
            row_info = f" | Rows {start_row + 1}-{end_row} of {total_rows}{scroll_indicator}"
        else:
            row_info = f" | All {total_rows} rows visible"

        title = (
            f"[bold bright_yellow]{nav_info}[/bold bright_yellow] "
            f"| Total: {total} | Limit: {actual_limit} | Distinct: {distinct} "
            f"{row_info} | {result_pct}%"
        )

        # Wrap in panel - it will auto-size based on table content
        # The max_visible calculation already accounts for the panel borders and help text
        panel = self.Panel(table, title=title, border_style="bright_yellow", box=self.box.DOUBLE, expand=True)

        return panel

    def _save_debug_result(self, func_name, raw_result, parsed_data):  # type: ignore[no-untyped-def]  # noqa: C901
        """Save API result to file when debug mode is enabled.

        Saves the complete raw result as JSON without any parsing or transformation,
        preserving all attributes and structure from the mistapi response.
        """
        from datetime import datetime

        try:
            # Create debug output directory
            debug_dir = os.path.join("data", "tui_debug_results")
            os.makedirs(debug_dir, exist_ok=True)

            # Create timestamped filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{func_name}_{timestamp}.json"
            filepath = os.path.join(debug_dir, filename)

            # Helper function to convert object to serializable dict
            def make_serializable(obj):  # type: ignore[no-untyped-def]
                """Convert any object to JSON-serializable format, preserving all attributes."""
                # Handle None, primitives
                if obj is None or isinstance(obj, (str, int, float, bool)):
                    return obj

                # Handle dict
                if isinstance(obj, dict):
                    return {k: make_serializable(v) for k, v in obj.items()}  # type: ignore[no-untyped-call]

                # Handle list/tuple
                if isinstance(obj, (list, tuple)):
                    return [make_serializable(item) for item in obj]  # type: ignore[no-untyped-call]

                # Handle objects with __dict__ (like APIResponse)
                if hasattr(obj, "__dict__"):
                    result: dict[str, Any] = {"__type__": type(obj).__name__}
                    for attr_name in dir(obj):
                        # Skip private/magic methods and callables
                        if attr_name.startswith("_") or callable(getattr(obj, attr_name, None)):
                            continue
                        try:
                            attr_value = getattr(obj, attr_name)  # nosec B112
                            result[attr_name] = make_serializable(attr_value)  # type: ignore[no-untyped-call]
                        except Exception:  # nosec B112
                            # Skip attributes that can't be accessed
                            continue
                    return result

                # Fallback to string representation
                return str(obj)

            # Prepare debug data with complete raw response
            debug_output = {
                "function": func_name,
                "timestamp": timestamp,
                "parameters": {},
                "raw_response": make_serializable(raw_result),  # type: ignore[no-untyped-call]
                "parsed_data": parsed_data,
            }

            # Copy and redact sensitive parameters
            for key, value in self.function_params.items():
                if any(x in key.lower() for x in ["pass", "token", "key", "secret"]):
                    debug_output["parameters"][key] = "***REDACTED***"
                else:
                    # Also serialize parameter values properly
                    debug_output["parameters"][key] = make_serializable(value)  # type: ignore[no-untyped-call]

            # Write to file
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(debug_output, f, indent=2, default=str)

            logging.debug(f"TUI_DEBUG: Raw result saved to {filepath}")

        except Exception as error:
            logging.error(f"TUI_DEBUG: Failed to save debug result: {error}", exc_info=True)

    def _format_result_output(self, parsed_data, func_name, raw_result=None):  # type: ignore[no-untyped-def]
        """Format API result for display in output panel with hierarchical structure."""
        output = []
        output.append(f"[SUCCESS] {func_name} completed")
        output.append("")

        if self.debug_mode and raw_result:
            output.append(f"[dim]Debug: Result saved to data/tui_debug_results/{func_name}_*.json[/dim]")
            output.append("")

        # Format hierarchically based on structure
        self._format_value_hierarchical(parsed_data, output, indent=0, key_name="results")  # type: ignore[no-untyped-call]

        # Add hint for viewing full data
        if isinstance(parsed_data, (list, dict)) and len(str(parsed_data)) > 500:
            output.append("")
            output.append("[dim]Tip: Full data available in debug log (run with --debug)[/dim]")

        return output

    def _format_value_hierarchical(self, value, output, indent=0, key_name=None, max_items=5):  # type: ignore[no-untyped-def]  # noqa: C901, PLR0912, PLR0915
        """Recursively format a value with hierarchical indentation."""
        indent_str = "  " * indent

        # Handle None
        if value is None:
            if key_name:
                output.append(f"{indent_str}{key_name}: None")
            else:
                output.append(f"{indent_str}None")
            return

        # Handle dictionaries
        if isinstance(value, dict):
            if key_name:
                output.append(f"{indent_str}{key_name}: dict ({len(value)} keys)")
            else:
                output.append(f"{indent_str}dict ({len(value)} keys)")

            # Show each key-value pair
            for _idx, (k, v) in enumerate(value.items()):
                if isinstance(v, (dict, list)):
                    # Nested structure - recurse
                    self._format_value_hierarchical(v, output, indent + 1, key_name=k)  # type: ignore[no-untyped-call]
                else:
                    # Simple value - display inline
                    value_str = str(v)
                    if len(value_str) > 60:
                        value_str = value_str[:60] + "..."
                    output.append(f"{indent_str}  {k}: {value_str}")
            return

        # Handle lists/tuples
        if isinstance(value, (list, tuple)):
            item_count = len(value)
            type_name = "list" if isinstance(value, list) else "tuple"

            if key_name:
                output.append(f"{indent_str}{key_name}: {type_name} ({item_count} items)")
            else:
                output.append(f"{indent_str}{type_name} ({item_count} items)")

            if item_count == 0:
                output.append(f"{indent_str}  (empty)")
                return

            # Determine if items are dicts, and show structure
            display_count = min(max_items, item_count)
            for idx in range(display_count):
                item = value[idx]
                if isinstance(item, dict):
                    # Show dict item with its keys
                    output.append(f"{indent_str}  [{idx}]: dict ({len(item)} keys)")
                    # Show first few key-value pairs
                    for k, v in list(item.items())[:3]:
                        v_str = str(v)
                        if len(v_str) > 50:
                            v_str = v_str[:50] + "..."
                        output.append(f"{indent_str}    {k}: {v_str}")
                    if len(item) > 3:
                        output.append(f"{indent_str}    ... {len(item) - 3} more keys")
                elif isinstance(item, (list, tuple)):
                    # Nested list - recurse
                    self._format_value_hierarchical(item, output, indent + 1, key_name=f"[{idx}]", max_items=3)  # type: ignore[no-untyped-call]
                else:
                    # Simple item
                    item_str = str(item)
                    if len(item_str) > 60:
                        item_str = item_str[:60] + "..."
                    output.append(f"{indent_str}  [{idx}]: {item_str}")

            if item_count > display_count:
                output.append(f"{indent_str}  ... {item_count - display_count} more items")
            return

        # Handle simple types (string, int, float, bool, etc.)
        value_str = str(value)
        if len(value_str) > 200:
            value_str = value_str[:200] + "..."

        if key_name:
            output.append(f"{indent_str}{key_name}: {value_str}")
        else:
            output.append(f"{indent_str}{value_str}")

    def execute_current_item(self):  # type: ignore[no-untyped-def]  # noqa: C901, PLR0912, PLR0915
        """Execute the currently selected API function with parameter prompting.

        This method:
        1. Gets the selected function and its signature
        2. Prompts user for required parameters
        3. Executes the API call with collected parameters
        4. Displays results or errors
        """
        import inspect

        if not (0 <= self.current_selection < len(self.current_items)):
            return

        selected = self.current_items[self.current_selection]
        if selected.get("type") != "function":
            return

        func = selected.get("object")
        func_name = selected.get("name")

        if not func or not callable(func):
            self.last_error = "Selected item is not callable"
            return

        if self.debug_mode:
            logging.debug(f"TUI_DEBUG: Preparing to execute function: {func_name}")

        # Clear last results
        self.last_result = None
        self.last_error = None

        # Restore terminal for input prompts
        if not self.IS_WINDOWS:
            self.termios.tcsetattr(sys.stdin, self.termios.TCSADRAIN, self.old_terminal_settings)

        try:
            # Get function signature
            sig = inspect.signature(func)
            params = {}

            if self.debug_mode:
                logging.debug(f"TUI_DEBUG: Function signature: {func_name}{sig}")

            # Display function info (screen already cleared by exiting Live() context)
            print(f"\n[Executing] {func_name}")
            print(f"Signature: {func_name}{sig}\n")

            # Prompt for parameters
            for param_name, param in sig.parameters.items():
                # Skip self parameter if present
                if param_name == "self":
                    continue

                # Check if mist_session or apisession is available globally
                if param_name in ("mist_session", "apisession"):
                    if hasattr(self, "apisession") and self.apisession is not None:
                        params[param_name] = self.apisession
                        continue
                    else:
                        print("[ERROR] API session not available")
                        self.last_error = "API session not initialized"
                        return

                # Check if parameter has a default value
                has_default = param.default != inspect.Parameter.empty
                default_str = f" (default: {param.default})" if has_default else ""
                required_str = "" if has_default else " [required]"

                # Check if parameter value is available from environment variables
                # Common parameters: org_id, site_id, device_id, etc.
                env_value = os.getenv(param_name)
                if env_value:
                    # Use environment variable value without prompting
                    params[param_name] = env_value
                    print(f"  {param_name}: [from .env] {env_value}")
                    if self.debug_mode:
                        logging.debug(f"TUI_DEBUG: Using environment variable for {param_name}: {env_value}")
                    continue

                # Prompt user for parameter value
                prompt = f"  {param_name}{default_str}{required_str}: "
                value = input(prompt).strip()

                if self.debug_mode:
                    # Redact sensitive values in logs
                    display_value = (
                        "***REDACTED***"
                        if any(x in param_name.lower() for x in ["pass", "token", "key", "secret"])
                        else value
                    )
                    logging.debug(f"TUI_DEBUG: User input for {param_name}: {display_value}")

                # Use default if no value provided
                if not value and has_default:
                    continue

                # Validate required parameters
                if not value and not has_default:
                    print(f"[ERROR] {param_name} is required")
                    self.last_error = f"Missing required parameter: {param_name}"
                    if self.debug_mode:
                        logging.debug(f"TUI_DEBUG: Execution aborted - missing required parameter: {param_name}")
                    return

                # Store parameter (basic type conversion)
                params[param_name] = value

            if self.debug_mode:
                param_summary = {
                    k: "***REDACTED***" if any(x in k.lower() for x in ["pass", "token", "key", "secret"]) else v
                    for k, v in params.items()
                }
                logging.debug(f"TUI_DEBUG: Calling {func_name} with parameters: {param_summary}")

            # Execute the API call
            print("\nExecuting API call...")
            result = func(**params)

            # Store result (but create smart preview to avoid OOM)
            self.last_result = result
            print("\n[SUCCESS]")

            # Smart result preview to prevent OOM errors with large responses
            result_type = type(result).__name__

            # Build safe preview without converting entire result to string
            if result is None:
                preview = "None"
            elif isinstance(result, (list, tuple)):
                item_count = len(result)
                if item_count == 0:
                    preview = f"{result_type}: [] (empty)"
                elif item_count <= 3:
                    # Small list, safe to show
                    preview = f"{result_type} with {item_count} items:\n"
                    for idx, item in enumerate(result):
                        item_preview = repr(item)[:100]
                        preview += f"  [{idx}]: {item_preview}\n"
                else:
                    # Large list, show summary + first few items
                    preview = f"{result_type} with {item_count} items (showing first 3):\n"
                    for idx in range(3):
                        item_preview = repr(result[idx])[:100]
                        if len(repr(result[idx])) > 100:
                            item_preview += "..."
                        preview += f"  [{idx}]: {item_preview}\n"
                    preview += f"  ... and {item_count - 3} more items"
            elif isinstance(result, dict):
                key_count = len(result)
                if key_count == 0:
                    preview = f"{result_type}: {{}} (empty)"
                elif key_count <= 5:
                    # Small dict, show all keys
                    preview = f"{result_type} with {key_count} keys: {list(result.keys())}"
                else:
                    # Large dict, show first few keys
                    first_keys = list(result.keys())[:5]
                    preview = f"{result_type} with {key_count} keys (first 5): {first_keys}..."
            elif isinstance(result, str):
                if len(result) <= 200:
                    preview = f"String: {result}"
                else:
                    preview = f"String ({len(result)} chars): {result[:200]}..."
            elif isinstance(result, (int, float, bool)):
                preview = f"{result_type}: {result}"
            else:
                # Unknown type, use safe repr with limit
                preview = f"{result_type}: {repr(result)[:200]}"
                if len(repr(result)) > 200:
                    preview += "..."

            print(f"\n{preview}")

            # Offer to save large results
            if isinstance(result, (list, tuple, dict)) and len(result) > 10:
                print(
                    f"\n[TIP] Result has {len(result)} items. Consider using main menu options to save full data to CSV/SQLite."  # noqa: E501
                )

            logging.info(f"TUI: Successfully executed {func_name}")

            if self.debug_mode:
                result_len = len(result) if hasattr(result, "__len__") else "N/A"  # type: ignore[arg-type]  # guarded by hasattr
                logging.debug(f"TUI_DEBUG: Execution successful - result type: {result_type}, length: {result_len}")

        except KeyboardInterrupt:
            print("\n[CANCELLED] Execution cancelled by user")
            logging.info(f"TUI: Execution of {func_name} cancelled by user")
            if self.debug_mode:
                logging.debug(f"TUI_DEBUG: KeyboardInterrupt during {func_name} execution")
        except Exception as error:
            self.last_error = str(error)
            print(f"\n[ERROR] {error}")
            logging.error(f"TUI: Execution of {func_name} failed - {error}", exc_info=True)
            if self.debug_mode:
                logging.debug(f"TUI_DEBUG: Exception during {func_name} execution: {type(error).__name__}: {error}")
        finally:
            # Wait for user acknowledgment before returning to TUI
            print("\nPress any key to return to explorer...")
            if self.IS_WINDOWS:
                self.msvcrt.getch()
            else:
                # Wait for keypress with normal terminal settings
                sys.stdin.read(1)

            # Restore raw mode for TUI navigation on Unix systems
            if not self.IS_WINDOWS:
                self.tty.setcbreak(sys.stdin.fileno())

            if self.debug_mode:
                logging.debug(
                    f"TUI_DEBUG: Returning to API explorer from {func_name} execution, terminal mode restored"
                )

    def run(self):  # type: ignore[no-untyped-def]  # noqa: C901, PLR0912, PLR0915
        """Main TUI loop with hierarchical API navigation."""
        logging.info("TUI: Starting hierarchical API explorer")

        if self.debug_mode:
            logging.debug("TUI_DEBUG: run() method started - initializing terminal settings")

        # Set terminal to raw mode for Unix systems
        if not self.IS_WINDOWS:
            if self.debug_mode:
                logging.debug("TUI_DEBUG: Unix platform detected - setting terminal to raw mode")
            self.old_terminal_settings = self.termios.tcgetattr(sys.stdin)
            self.tty.setcbreak(sys.stdin.fileno())
            if self.debug_mode:
                logging.debug("TUI_DEBUG: Terminal set to raw mode successfully")
        else:
            if self.debug_mode:
                logging.debug("TUI_DEBUG: Windows platform detected - skipping terminal mode setup")

        try:
            # Initial discovery at root level
            if self.debug_mode:
                logging.debug("TUI_DEBUG: Starting initial discovery at root level")
            self._discover_current_level()  # type: ignore[no-untyped-call]
            if self.debug_mode:
                logging.debug(f"TUI_DEBUG: Initial discovery complete - found {len(self.current_items)} items")

            # Use higher refresh rate for more responsive feel
            # screen=True prevents content from scrolling off-screen
            if self.debug_mode:
                logging.debug("TUI_DEBUG: Entering Live() context for TUI rendering")

            loop_iteration = 0
            # Higher refresh rate for responsive input - 20/sec for smooth scrolling
            # screen=True keeps content from scrolling
            with self.Live(self.create_layout(), console=self.console, refresh_per_second=20, screen=True) as live:  # type: ignore[no-untyped-call]
                if self.debug_mode:
                    logging.debug("TUI_DEBUG: Live() context entered successfully - starting main loop")

                while self.running:
                    loop_iteration += 1

                    if self.debug_mode and loop_iteration % 100 == 0:  # Log every 100 iterations
                        logging.debug(f"TUI_DEBUG: Main loop iteration {loop_iteration} - running={self.running}")

                    # Check for keyboard input
                    key = self.check_keyboard_input()  # type: ignore[no-untyped-call]
                    if key:
                        if self.debug_mode:
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                            logging.debug(f"TUI_DEBUG: [{timestamp}] Keyboard input detected in main loop: {repr(key)}")

                        self.handle_input(key)  # type: ignore[no-untyped-call]

                        if self.debug_mode:
                            logging.debug(f"TUI_DEBUG: Input handled - running flag now: {self.running}")

                        # Explicit check after handling input for immediate exit
                        if not self.running:
                            if self.debug_mode:
                                logging.debug("TUI_DEBUG: Running flag is False - breaking main loop")
                            break

                        # Update layout - let Live() handle refresh timing automatically
                        if self.debug_mode:
                            logging.debug("TUI_DEBUG: Updating Live() display with new layout")
                        new_layout = self.create_layout()  # type: ignore[no-untyped-call]
                        live.update(new_layout)  # Remove refresh=True to let Live() manage refresh
                        if self.debug_mode:
                            logging.debug("TUI_DEBUG: Live() display updated")

                    # Minimal sleep - just yield to prevent CPU spin (10ms for responsive input)
                    time.sleep(0.01)

                if self.debug_mode:
                    logging.debug(
                        f"TUI_DEBUG: Main loop exited after {loop_iteration} iterations - exiting Live() context"
                    )

        except Exception as error:
            logging.error(f"TUI: Critical error in run() method: {error}", exc_info=True)
            if self.debug_mode:
                logging.debug(f"TUI_DEBUG: Exception caught in run() try block: {type(error).__name__}: {error}")
            raise

        finally:
            if self.debug_mode:
                logging.debug("TUI_DEBUG: Entered finally block - restoring terminal settings")

            # Restore terminal settings on Unix
            if not self.IS_WINDOWS:
                try:
                    if self.debug_mode:
                        logging.debug("TUI_DEBUG: Restoring terminal settings on Unix platform")
                    self.termios.tcsetattr(sys.stdin, self.termios.TCSADRAIN, self.old_terminal_settings)
                    if self.debug_mode:
                        logging.debug("TUI_DEBUG: Terminal settings restored successfully")
                except Exception as term_error:
                    logging.error(f"TUI: Error restoring terminal settings: {term_error}", exc_info=True)
                    if self.debug_mode:
                        logging.debug(
                            f"TUI_DEBUG: Terminal restoration failed: {type(term_error).__name__}: {term_error}"
                        )
            else:
                if self.debug_mode:
                    logging.debug("TUI_DEBUG: Windows platform - no terminal restoration needed")

            if self.debug_mode:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                logging.debug(f"TUI_DEBUG: [{timestamp}] Explorer exiting - run() finally block executing")

            logging.info("TUI: Explorer exited cleanly")
            if self.debug_mode:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                logging.debug(f"TUI_DEBUG: [{timestamp}] run() method ending - about to print exit message")
            print("\n[EXIT] MistHelper TUI - Hierarchical API Explorer closed")
            if self.debug_mode:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                logging.debug(f"TUI_DEBUG: [{timestamp}] Exit message printed - run() method complete")
