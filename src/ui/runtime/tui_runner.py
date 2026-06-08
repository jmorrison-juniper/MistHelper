"""Replacement for ``MistHelperTUI.run`` (CC=33).

Decomposes the main TUI loop into setup, loop, and teardown phases.
Each helper is CC <= 10.
"""

from __future__ import annotations

import logging
import sys
import time
from typing import Any

LOOP_SLEEP_S = 0.01  # 10ms yield between loop iterations
REFRESH_PER_SECOND = 20  # Live() refresh frequency


class TuiRunner:
    """Owns the lifecycle of the TUI: terminal setup, render loop, teardown."""

    def __init__(self, tui: Any) -> None:
        self._tui = tui  # Back-reference for shared TUI state

    def run(self) -> None:
        """Public entry point matching the original ``MistHelperTUI.run`` shape."""
        tui = self._tui  # Local alias
        logging.info("TUI: Starting hierarchical API explorer")  # Action log before setup
        self._setup_terminal()  # Switch Unix terminal to cbreak mode
        try:
            tui._discover_current_level()  # Populate the root level items
            self._render_loop()  # Drive the main Live() loop
        except Exception as error:  # Surface critical errors loudly
            logging.error("TUI: Critical error in run() method: %s", error, exc_info=True)
            raise
        finally:
            self._teardown_terminal()  # Restore terminal even on error
            logging.info("TUI: Explorer exited cleanly")  # Action log after teardown
            print("\n[EXIT] MistHelper TUI - Hierarchical API Explorer closed")

    def _setup_terminal(self) -> None:
        """Put the Unix terminal into raw (cbreak) mode for keypress capture."""
        tui = self._tui  # Local alias
        if tui.IS_WINDOWS:  # Windows uses msvcrt; nothing to set up
            return
        tui.old_terminal_settings = tui.termios.tcgetattr(sys.stdin)  # Save current termios for restore
        tui.tty.setcbreak(sys.stdin.fileno())  # Enter cbreak mode

    def _render_loop(self) -> None:
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
                    tui.handle_input(key)  # Dispatch through KeyboardDispatchTable
                    if not tui.running:  # Quit may have just been requested
                        break
                    live.update(tui.create_layout())  # Repaint with fresh layout
                time.sleep(LOOP_SLEEP_S)  # Yield CPU briefly

    def _teardown_terminal(self) -> None:
        """Restore the Unix terminal to its original (pre-cbreak) settings."""
        tui = self._tui  # Local alias
        if tui.IS_WINDOWS:  # Windows has no termios state to restore
            return
        try:
            tui.termios.tcsetattr(sys.stdin, tui.termios.TCSADRAIN, tui.old_terminal_settings)
        except Exception as term_error:  # Restore failures are non-fatal
            logging.error("TUI: Error restoring terminal settings: %s", term_error, exc_info=True)
