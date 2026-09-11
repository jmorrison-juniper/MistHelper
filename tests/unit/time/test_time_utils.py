"""Wave 2 P2 coverage for src/time/time_utils.py (initiative #1018).

Covers both branches of `TimeUtils.get_dynamic_lookback_hours` (test-mode + production
mode, plus the exception fallback), and both branches of `TimeUtils.log_dynamic_lookback`
(test-mode INFO vs production DEBUG). IS_TEST_MODE is a module-level constant computed
from sys.argv at import time; we monkeypatch it on the imported module so each test can
observe both branches deterministically. No source edits, no live I/O.
"""

from __future__ import annotations  # WHY: PEP 604 unions in method signatures on Python 3.10+.

import logging  # WHY: caplog-level configuration and logger-name assertions.

import pytest  # WHY: caplog + monkeypatch fixtures.

from src.time import time_utils as tu  # WHY: import as module so IS_TEST_MODE can be monkeypatched by attr name.
from src.time.time_utils import TimeUtils  # WHY: SUT static-method callsite convenience.


class TestGetDynamicLookbackHours:
    """`TimeUtils.get_dynamic_lookback_hours` returns the correct window per mode + clamp."""

    def test_returns_default_in_production_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Outside test mode the caller's default_hours wins."""
        monkeypatch.setattr(tu, "IS_TEST_MODE", False)  # WHY: force production branch of the ternary.
        assert TimeUtils.get_dynamic_lookback_hours(default_hours=24, test_hours=1) == 24  # WHY: production path.

    def test_returns_test_hours_in_test_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Under --test IS_TEST_MODE=True and the shorter test_hours window wins."""
        monkeypatch.setattr(tu, "IS_TEST_MODE", True)  # WHY: force test-mode branch of the ternary.
        assert TimeUtils.get_dynamic_lookback_hours(default_hours=24, test_hours=2) == 2  # WHY: test-mode path.

    def test_clamps_to_one_hour_minimum(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Zero/negative inputs clamp up to 1 hour to prevent sub-hour windows."""
        monkeypatch.setattr(tu, "IS_TEST_MODE", False)  # WHY: keep the production branch active for a clean clamp.
        assert TimeUtils.get_dynamic_lookback_hours(default_hours=0, test_hours=1) == 1  # WHY: max(1,0) == 1.
        assert TimeUtils.get_dynamic_lookback_hours(default_hours=-5, test_hours=1) == 1  # WHY: max(1,-5) == 1.

    def test_defaults_use_24_and_1(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Calling with no args exercises the signature defaults (default_hours=24, test_hours=1)."""
        monkeypatch.setattr(tu, "IS_TEST_MODE", False)  # WHY: exercise the signature default in production mode.
        assert TimeUtils.get_dynamic_lookback_hours() == 24  # WHY: default_hours=24 default arg is applied.
        monkeypatch.setattr(tu, "IS_TEST_MODE", True)  # WHY: exercise the signature default under test mode.
        assert TimeUtils.get_dynamic_lookback_hours() == 1  # WHY: test_hours=1 default arg is applied.

    def test_exception_fallback_returns_test_hours_in_test_mode(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """If the inner branch raises, the except fallback returns the correct value for the current mode."""
        monkeypatch.setattr(tu, "IS_TEST_MODE", True)  # WHY: force test-mode both in try and except.

        def _boom(_a: int, _b: int) -> int:  # WHY: local double replaces builtins.max to raise inside try block.
            raise RuntimeError("simulated max failure")  # WHY: trigger the broad-except fallback in the SUT.

        monkeypatch.setattr(tu, "max", _boom, raising=False)  # WHY: shadow builtins.max in the module namespace.
        caplog.set_level(logging.DEBUG, logger=tu.__name__)  # WHY: capture the DEBUG fallback log line.
        assert TimeUtils.get_dynamic_lookback_hours(default_hours=24, test_hours=3) == 3  # WHY: fallback -> test_hours.

    def test_exception_fallback_returns_default_hours_in_production_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """If the inner branch raises in production mode, the except fallback returns default_hours."""
        monkeypatch.setattr(tu, "IS_TEST_MODE", False)  # WHY: force production branch of the fallback ternary.

        def _boom(_a: int, _b: int) -> int:  # WHY: local double replaces builtins.max to raise inside try block.
            raise RuntimeError("simulated max failure")  # WHY: trigger the broad-except fallback in the SUT.

        monkeypatch.setattr(tu, "max", _boom, raising=False)  # WHY: shadow builtins.max in the module namespace.
        assert TimeUtils.get_dynamic_lookback_hours(default_hours=17, test_hours=1) == 17  # WHY: fallback -> default.


class TestLogDynamicLookback:
    """`TimeUtils.log_dynamic_lookback` emits an INFO line in test mode and a DEBUG line in production."""

    def test_test_mode_emits_info_line(self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
        """Under test mode the reduced-window notice is emitted at INFO level with the [TEST MODE] prefix."""
        monkeypatch.setattr(tu, "IS_TEST_MODE", True)  # WHY: force the info branch of the log emission.
        caplog.set_level(logging.INFO)  # WHY: capture INFO and above for this assertion.
        TimeUtils.log_dynamic_lookback("audit fetch", 3)  # WHY: exercise the info path with a representative context.
        info_records = [r for r in caplog.records if r.levelno == logging.INFO]  # WHY: filter to INFO records only.
        assert any(  # WHY: locate a record containing both the [TEST MODE] tag and the hours + context substrings.
            "[TEST MODE]" in r.getMessage() and "3h" in r.getMessage() and "audit fetch" in r.getMessage()
            for r in info_records
        )

    def test_production_mode_emits_debug_line(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Outside test mode the reduced-window notice drops to DEBUG level."""
        monkeypatch.setattr(tu, "IS_TEST_MODE", False)  # WHY: force the debug branch of the log emission.
        caplog.set_level(logging.DEBUG)  # WHY: capture DEBUG and above for this assertion.
        TimeUtils.log_dynamic_lookback("audit fetch", 24)  # WHY: exercise the debug path with production window.
        debug_records = [r for r in caplog.records if r.levelno == logging.DEBUG]  # WHY: filter to DEBUG only.
        assert any(  # WHY: locate the standard-window debug record with the context marker.
            "standard lookback" in r.getMessage() and "audit fetch" in r.getMessage() for r in debug_records
        )
