"""TimeUtils -- dynamic lookback window helpers for test-vs-production runs.

Extracted from MistHelper.py during initiative 1014 (Cat E, position 6).
Callers reach the class either through direct ``from src.time.time_utils import TimeUtils``
(preferred, FR-005) or via the ``MistHelper.TimeUtils`` re-export alias which continues
to point at this canonical body.

``IS_TEST_MODE`` is recomputed here from ``sys.argv`` so the module has no MistHelper.py
backref (FR-028 IG-health). The value is captured at import time — identical to how
MistHelper.py evaluates it — so all callers observe the same flag regardless of which
module imported first.
"""

# pylint: disable=broad-exception-caught

from __future__ import annotations  # WHY: PEP 604 unions for method signatures.

import logging  # WHY: fallback + informational log lines.
import sys  # WHY: recompute IS_TEST_MODE from sys.argv (no MistHelper backref).

IS_TEST_MODE = "--test" in sys.argv or "--testinteractive" in sys.argv  # WHY: mirror MistHelper.py flag.


class TimeUtils:
    """Centralized time-related utilities.

    Handles dynamic lookback windows, timestamp conversions, and so on
    """

    @staticmethod
    def get_dynamic_lookback_hours(default_hours: int = 24, test_hours: int = 1) -> int:
        """Return lookback hours adjusted for test mode (shrinks to test_hours under --test).

        Outside test mode the caller's default_hours window is honored. Both values are
        clamped to a 1-hour minimum so a misconfiguration never yields a sub-hour window.
        """
        try:
            chosen_hours = test_hours if IS_TEST_MODE else default_hours  # Pick the window for the active mode
            return max(1, chosen_hours)  # Never return less than 1 hour (clamp misconfigured values)
        except Exception as error:  # Never let lookback math crash a caller
            logging.debug("get_dynamic_lookback_hours fallback due to error: %s", error)  # Log the unexpected failure
            return test_hours if IS_TEST_MODE else default_hours  # Fall back to a sensible default per mode

    @staticmethod
    def log_dynamic_lookback(context: str, hours: int) -> None:
        """Helper to produce a consistent log line when dynamic lookback applies."""
        if IS_TEST_MODE:  # Surface the reduced window prominently during tests
            logging.info(
                "[TEST MODE] Using reduced lookback window of %sh for %s (normally 24h)", hours, context
            )  # Visible test-mode notice
        else:  # Production: keep the note at debug level
            logging.debug("Using standard lookback window of %sh for %s", hours, context)  # Quiet production notice
