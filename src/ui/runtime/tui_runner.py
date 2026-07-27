"""Replacement for ``MistHelperTUI.run`` (CC=33).

Decomposes the main TUI loop into setup, loop, and teardown phases.
Each helper is CC <= 10.
"""

from __future__ import annotations  # WHY: postponed evaluation for forward-ref type hints

import logging  # WHY: action-log setup/loop/teardown transitions
import sys  # WHY: stdin fd for termios cbreak setup
import time  # WHY: sleep briefly between loop iterations
from typing import Any  # WHY: TUI back-ref is loosely typed

LOOP_SLEEP_S = 0.01  # 10ms yield between loop iterations
REFRESH_PER_SECOND = 20  # Live() refresh frequency


class TuiRunner:  # WHY: extracted from MistHelperTUI.run (was CC=33)
    """Owns the lifecycle of the TUI: terminal setup, render loop, teardown."""

    def __init__(self, tui: Any) -> None:  # WHY: bind owning TUI for shared state
        """Store a back-reference to the owning TUI for shared state access."""
        self._tui = tui  # Back-reference for shared TUI state

    def run(self) -> None:  # WHY: public entry point retained for compat
        """Public entry point matching the original ``MistHelperTUI.run`` shape."""
        tui = self._tui  # Local alias
        logging.info("TUI: Starting hierarchical API explorer")  # Action log before setup
        self._setup_terminal()  # Switch Unix terminal to cbreak mode
        try:  # WHY: teardown must always run even on setup/loop errors
            tui._discover_current_level()  # Populate the root level items
            self._render_loop()  # Drive the main Live() loop
        except Exception as error:  # Surface critical errors loudly
            logging.exception("TUI: Critical error in run() method: %s", error)  # WHY: preserve traceback
            raise  # WHY: re-raise so caller sees the failure
        finally:
            self._teardown_terminal()  # Restore terminal even on error
            logging.info("TUI: Explorer exited cleanly")  # Action log after teardown
            # WHY (#886 Phase 2): retire print() in favor of logging.warning so the exit banner
            # reaches the operator on the default root-logger config (INFO is suppressed by default).
            logging.warning("\n[EXIT] MistHelper TUI - Hierarchical API Explorer closed")  # User-visible exit banner

    def _setup_terminal(self) -> None:  # WHY: enter cbreak so keys read w/o Enter
        """Put the Unix terminal into raw (cbreak) mode for keypress capture."""
        tui = self._tui  # Local alias
        if tui.IS_WINDOWS:  # Windows uses msvcrt; nothing to prepare
            return  # WHY: no-op on Windows
        tui.old_terminal_settings = tui.termios.tcgetattr(sys.stdin)  # Save current termios for restore
        tui.tty.setcbreak(sys.stdin.fileno())  # Enter cbreak mode

    def _render_loop(self) -> None:  # WHY: main input/repaint loop
        """Run the inner ``Live()`` render+input loop while ``tui.running``."""
        tui = self._tui  # Local alias
        with tui.Live(  # Live() context auto-refreshes screen
            tui.create_layout(),
            console=tui.console,
            refresh_per_second=REFRESH_PER_SECOND,
            screen=True,
        ) as live:
            while tui.running:  # Main loop until quit
                key = tui.check_keyboard_input()  # Poll for next key (non-blocking)
                if key:  # Only handle when a key is ready
                    tui._keyboard_dispatch.dispatch(key)  # Dispatch keystroke via the dispatch table
                    if not tui.running:  # Quit may have just been requested
                        break  # WHY: exit loop immediately on quit
                    live.update(tui.create_layout())  # Repaint with fresh layout
                time.sleep(LOOP_SLEEP_S)  # Yield CPU briefly

    def _teardown_terminal(self) -> None:  # WHY: restore Unix termios if we changed it
        """Restore the Unix terminal to its original (pre-cbreak) settings."""
        tui = self._tui  # Local alias
        if tui.IS_WINDOWS:  # Windows has no termios state to restore
            return  # WHY: no-op on Windows
        try:  # WHY: swallow restore errors to keep exit clean
            tui.termios.tcsetattr(sys.stdin, tui.termios.TCSADRAIN, tui.old_terminal_settings)  # Restore cooked mode
        except Exception as term_error:  # Restore failures are non-fatal
            logging.exception("TUI: Error restoring terminal settings: %s", term_error)  # WHY: log for post-mortem
