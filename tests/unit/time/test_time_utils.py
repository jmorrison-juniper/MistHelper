"""Wave 2 P2 coverage for src/foundation/runtime/time/time_utils.py (initiative #1018).

Covers both branches of `TimeUtils.get_dynamic_lookback_hours` (test-mode + production
mode, plus the exception fallback), and both branches of `TimeUtils.log_dynamic_lookback`
(test-mode INFO vs production DEBUG). IS_TEST_MODE is a module-level constant computed
from sys.argv at import time; we monkeypatch it on the imported module so each test can
observe both branches deterministically. No live I/O.
"""

from __future__ import annotations  # WHY: PEP 604 unions in method signatures on Python 3.10+.

import logging  # WHY: caplog-level configuration and logger-name assertions.
from io import StringIO

import pytest  # WHY: caplog + monkeypatch fixtures.

from src.foundation.runtime.time import (
    time_utils as tu,
)  # WHY: import as module so IS_TEST_MODE can be monkeypatched by attr name.
from src.foundation.runtime.time.time_utils import TimeUtils  # WHY: SUT static-method callsite convenience.
from src.foundation.support.utils.logger_utils import SensitiveFilter


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

    @pytest.mark.parametrize("test_mode", [False, True])
    @pytest.mark.parametrize("hours", [0, -5])
    def test_clamps_to_one_hour_minimum(self, monkeypatch: pytest.MonkeyPatch, test_mode: bool, hours: int) -> None:
        """Zero/negative inputs clamp up to 1 hour to prevent sub-hour windows."""
        monkeypatch.setattr(tu, "IS_TEST_MODE", test_mode)
        assert TimeUtils.get_dynamic_lookback_hours(default_hours=hours, test_hours=hours) == 1

    def test_defaults_use_24_and_1(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Calling with no args exercises the signature defaults (default_hours=24, test_hours=1)."""
        monkeypatch.setattr(tu, "IS_TEST_MODE", False)  # WHY: exercise the signature default in production mode.
        assert TimeUtils.get_dynamic_lookback_hours() == 24  # WHY: default_hours=24 default arg is applied.
        monkeypatch.setattr(tu, "IS_TEST_MODE", True)  # WHY: exercise the signature default under test mode.
        assert TimeUtils.get_dynamic_lookback_hours() == 1  # WHY: test_hours=1 default arg is applied.

    @pytest.mark.parametrize("error_type", [RuntimeError, TypeError])
    def test_exception_fallback_returns_test_hours_in_test_mode(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, error_type: type[Exception]
    ) -> None:
        """If the inner branch raises, the except fallback returns the correct value for the current mode."""
        monkeypatch.setattr(tu, "IS_TEST_MODE", True)  # WHY: force test-mode both in try and except.

        def _boom(_a: int, _b: int) -> int:  # WHY: local double replaces builtins.max to raise inside try block.
            raise error_type("simulated max failure")

        monkeypatch.setattr(tu, "max", _boom, raising=False)  # WHY: shadow builtins.max in the module namespace.
        caplog.set_level(logging.ERROR, logger=tu.__name__)
        assert TimeUtils.get_dynamic_lookback_hours(default_hours=24, test_hours=3) == 3  # WHY: fallback -> test_hours.
        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert (record.name, record.levelno) == (tu.__name__, logging.ERROR)
        assert record.getMessage() == f"Lookback calculation failed ({error_type.__name__}). Using test fallback."
        assert record.exc_info is None
        assert "simulated max failure" not in caplog.text

    @pytest.mark.parametrize("error_type", [RuntimeError, TypeError])
    def test_exception_fallback_returns_default_hours_in_production_mode(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, error_type: type[Exception]
    ) -> None:
        """If the inner branch raises in production mode, the except fallback returns default_hours."""
        monkeypatch.setattr(tu, "IS_TEST_MODE", False)  # WHY: force production branch of the fallback ternary.

        def _boom(_a: int, _b: int) -> int:  # WHY: local double replaces builtins.max to raise inside try block.
            raise error_type("simulated max failure")

        monkeypatch.setattr(tu, "max", _boom, raising=False)  # WHY: shadow builtins.max in the module namespace.
        caplog.set_level(logging.ERROR, logger=tu.__name__)
        assert TimeUtils.get_dynamic_lookback_hours(default_hours=17, test_hours=1) == 17  # WHY: fallback -> default.
        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert (record.name, record.levelno) == (tu.__name__, logging.ERROR)
        assert record.getMessage() == f"Lookback calculation failed ({error_type.__name__}). Using production fallback."
        assert record.exc_info is None
        assert "simulated max failure" not in caplog.text

    @pytest.mark.parametrize("test_mode", [False, True])
    def test_invalid_fallback_value_is_not_logged(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, test_mode: bool
    ) -> None:
        """Keep an invalid input out of logs while preserving the fallback."""
        monkeypatch.setattr(tu, "IS_TEST_MODE", test_mode)
        caplog.set_level(logging.ERROR, logger=tu.__name__)
        sentinel = "private-test-input"
        result = TimeUtils.get_dynamic_lookback_hours(
            default_hours=sentinel, test_hours=sentinel  # type: ignore[arg-type]
        )
        assert result == sentinel
        assert len(caplog.records) == 1
        record = caplog.records[0]
        mode = "test" if test_mode else "production"
        assert (record.name, record.levelno) == (tu.__name__, logging.ERROR)
        assert record.getMessage() == f"Lookback calculation failed (TypeError). Using {mode} fallback."
        assert record.exc_info is None
        assert sentinel not in caplog.text
        assert sentinel not in repr(record.args)

    @pytest.mark.parametrize("test_mode", [False, True])
    def test_handler_output_excludes_exception_token(self, monkeypatch: pytest.MonkeyPatch, test_mode: bool) -> None:
        """Exclude private exception text from the complete filtered handler output."""
        monkeypatch.setattr(tu, "IS_TEST_MODE", test_mode)
        output = StringIO()
        handler = logging.StreamHandler(output)
        handler.addFilter(SensitiveFilter())
        handler.setFormatter(logging.Formatter("%(levelname)s %(name)s %(message)s"))
        sentinel = "synthetic-private-time-token"

        def fail_max(_minimum: int, _chosen: int) -> int:
            """Raise an error with synthetic private text to exercise logging."""
            raise RuntimeError(f"token={sentinel}")

        monkeypatch.setattr(tu, "max", fail_max, raising=False)
        tu.logger.addHandler(handler)
        try:
            assert TimeUtils.get_dynamic_lookback_hours(default_hours=17, test_hours=3) == (3 if test_mode else 17)
        finally:
            tu.logger.removeHandler(handler)
            handler.close()
        mode = "test" if test_mode else "production"
        assert output.getvalue() == (
            f"ERROR {tu.__name__} Lookback calculation failed (RuntimeError). Using {mode} fallback.\n"
        )
        assert sentinel not in output.getvalue()
        assert "Traceback" not in output.getvalue()


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
