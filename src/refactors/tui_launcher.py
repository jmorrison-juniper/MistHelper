"""TUILauncher extracted from MistHelper.

Launches the Rich-based Terminal User Interface (TUI) for interactive Mist API
exploration from the numbered CLI menu. This module owns the console-handler
suppression/restore ceremony required so the TUI can take exclusive control of
stdout while the background logging channel keeps writing to file.

Runtime dependencies (``apisession`` global, ``initialize_mist_session``, and
the runtime ``args`` namespace) are resolved through the source dependency
resolver, so this module does not import the root module.
"""

from __future__ import annotations  # Enable postponed evaluation for forward-ref typing on 3.10+

import logging  # Structured action logging required by coding standards
from datetime import UTC, datetime  # Timestamp string for debug-only completion breadcrumb
from types import SimpleNamespace  # Bundle runtime dependencies without coupling to a dataclass

from src.config.source_dependency_resolver import (
    SourceDependencyResolver,  # WHY: resolve source dependencies without importing the root module.
)

logger = logging.getLogger(__name__)  # Name the logger for this module so a reader can filter by source.


def _resolve_runtime_dependencies() -> SimpleNamespace:
    """Resolve source-owned runtime dependencies without static cross-module imports."""
    logger.info("Resolving TUILauncher runtime dependencies from the source resolver")  # Log before lookup.
    misthelper_module = SourceDependencyResolver  # WHY: resolve source dependencies without importing the root module.
    logger.debug("TUILauncher runtime dependencies resolved successfully")  # Log after resolution
    return SimpleNamespace(
        misthelper_module=misthelper_module,  # Retained so apisession/args lookups honour monkeypatch
    )


class TUILauncher:  # Launch TUI mode from interactive menu.
    """Launch Terminal User Interface mode from interactive menu.

    Replicates the --tui CLI flag behavior but returns to menu instead of exiting.
    Provides an interactive, keyboard-driven API browser.

    SECURITY: Read-only browser mode with safe API exploration

    Usage:
        TUILauncher().launch()
    """

    def __init__(self) -> None:
        """Initialize TUI launcher with console handler tracking."""
        logger.info("TUILauncher init: starting new launcher instance")  # Log construction start
        self.console_handlers: list = []  # type: ignore[type-arg]  # Track suppressed handlers to restore later
        self.debug_mode: bool = False  # Populated from MistHelper args namespace at launch time
        self._deps: SimpleNamespace = _resolve_runtime_dependencies()  # Late-bound MistHelper handles
        logger.debug("TUILauncher init complete")  # Log after construction

    def _apisession(self) -> object | None:
        """Return the current MistHelper apisession so monkeypatched values are honoured."""
        return getattr(self._deps.misthelper_module, "apisession", None)  # Resolve at call-time, not import-time

    def launch(self) -> None:
        """Main entry point: launch TUI mode from menu."""
        logger.info("TUI_MODE: Starting Terminal User Interface mode from menu")  # Log launch entry
        self._print_welcome()  # Announce TUI activation on stdout

        if not self._ensure_api_session():  # Bail out early if session initialization fails
            logger.debug("TUI_MODE: launch aborted because API session could not be initialized")  # Log abort
            return  # Nothing further to run

        self._suppress_console_logging()  # Silence console handlers so Rich TUI owns stdout

        try:  # Guarded run to guarantee handler restoration in finally
            self._run_tui()  # Enter the Rich event loop
        except KeyboardInterrupt:  # User hit Ctrl+C inside the TUI
            self._handle_keyboard_interrupt()  # Log and print exit banner
        except Exception as error:  # TUI errors must never crash the numbered menu
            self._handle_fatal_error(error)  # Log traceback and surface user-visible error
        finally:  # Always run regardless of exception path
            self._restore_console_logging()  # Re-attach console handlers before returning to menu

        self._print_exit_message()  # Show "returned from TUI" banner on stdout
        logger.debug("TUI_MODE: launch() finished cleanly")  # Log after launch completes

    def _print_welcome(self) -> None:
        """Print TUI activation messages."""
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info("\n>> Terminal User Interface mode activated")
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info(">> Use arrow keys to navigate, Enter to select, Q to quit")

    def _ensure_api_session(self) -> bool:
        """Initialize Mist API session if needed."""
        logger.info("TUI_MODE: ensuring apisession is initialized")  # Log before session check
        if self._apisession():  # Session already exists - no reinitialization required
            logger.debug("TUI_MODE: apisession already initialized; reusing existing session")  # Log reuse
            return True  # Signal caller that session is ready

        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info(">> Initializing Mist API session...")
        misthelper_module = self._deps.misthelper_module  # Cache the module handle for both calls below
        if not misthelper_module.initialize_mist_session():  # Delegate to MistHelper's session bootstrap
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            logger.info("[ERROR] Failed to initialize Mist API session")
            logger.error("TUI_MODE: Could not initialize API session")  # Log the failure with error level
            return False  # Signal caller that session initialization failed

        # initialize_mist_session mutates MistHelper.apisession. No additional sync needed since we read via getattr
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info(">> API session initialized successfully")
        logger.debug("TUI_MODE: apisession initialized successfully")  # Log after successful init
        return True  # Signal caller that session is ready

    def _suppress_console_logging(self) -> None:
        """Remove console handlers to prevent interference with Rich TUI."""
        logger.info("TUI_MODE: suppressing console handlers before Rich TUI takes stdout")  # Log before mutation
        root_logger = logging.getLogger()  # Root logger owns the StreamHandler set
        self.console_handlers = [
            h  # Retain each handler so it can be re-attached in _restore_console_logging
            for h in root_logger.handlers
            if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
        ]  # Filter to StreamHandler-only (exclude FileHandler which is stdio-safe under Rich)
        for handler in self.console_handlers:  # Detach every captured handler
            root_logger.removeHandler(handler)  # Remove from root so it stops writing to stdout
            logger.debug("TUI_MODE: Removed console handler to prevent interference with Rich TUI")  # Log removal

    def _get_debug_mode(self) -> bool:
        """Get debug mode from global args if available."""
        # Read args off MistHelper module rather than globals() to keep the extracted class self-contained
        args_obj = getattr(self._deps.misthelper_module, "args", type("obj", (), {"debug": False})())
        return getattr(args_obj, "debug", False)  # Fall back to False when args namespace lacks 'debug' attribute

    def _run_tui(self) -> None:
        """Create and run the TUI instance."""
        logger.info("TUI_MODE: entering Rich TUI run loop")  # Log entry to TUI loop
        self.debug_mode = self._get_debug_mode()  # Latch debug flag once so exit path can reuse it

        from src.ui import tui as tui_module  # PLC0415: lazy import keeps the startup path light.

        tui = tui_module.MistHelperTUI(debug_mode=self.debug_mode)  # Build the Rich TUI after session checks pass.
        tui.apisession = self._apisession()  # Hand the already-initialized apisession to the TUI

        if self.debug_mode:  # Only log the debug-enabled banner when caller opted in
            logger.debug("TUI_MODE: Debug mode is ACTIVE - enhanced logging enabled")  # Debug-active breadcrumb

        tui.run()  # Enter the Rich event loop (blocks until user quits)
        logger.debug("TUI_MODE: Rich TUI run loop returned")  # Log after TUI loop finishes

    def _handle_keyboard_interrupt(self) -> None:
        """Handle user Ctrl+C interruption."""
        logger.info("TUI_MODE: User interrupted with Ctrl+C")  # Log the intentional keyboard abort
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info("\n[EXIT] TUI mode stopped by user")

    def _handle_fatal_error(self, error: Exception) -> None:
        """Handle fatal TUI errors."""
        logger.error("TUI_MODE: Fatal error - %s", error, exc_info=True)  # Log with traceback for postmortem
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info("\n[ERROR] TUI mode crashed: %s", error)

    def _restore_console_logging(self) -> None:
        """Restore console handlers after TUI mode exits."""
        logger.info("TUI_MODE: restoring console handlers after Rich TUI exit")  # Log before re-attach
        root_logger = logging.getLogger()  # Same root logger we detached from earlier
        for handler in self.console_handlers:  # Re-attach every previously-suppressed handler
            root_logger.addHandler(handler)  # Restore the handler so console logging resumes
        logger.debug("TUI_MODE: Restored console handler after TUI exit")  # Log after restoration completes

    def _print_exit_message(self) -> None:
        """Print exit messages and debug timestamp if enabled."""
        self.debug_mode = self._get_debug_mode()  # Re-read debug flag in case args changed during TUI session

        if self.debug_mode:  # Only emit the timestamped completion trace when debug mode is on
            timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Local wall-clock for eyeball parity
            logger.debug("TUI_DEBUG: [%s] TUI_MODE function completed - returning to caller", timestamp)  # Trace

        logger.info("TUI_MODE: TUI mode completed successfully")  # Success-path summary log
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info("\n>> Returned from TUI mode to main menu")
