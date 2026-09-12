"""Unit tests for the PhaseTimer diagnostic timer (1003-site-address-audit)."""

import time

from src.site.address_audit.perf import PhaseTimer


class TestPhaseTimer:
    """PhaseTimer accumulates per-phase wall-clock time and formats a summary."""

    def test_empty_by_default(self):
        """A fresh timer records nothing and reports the empty marker."""
        timer = PhaseTimer()
        assert timer.is_empty() is True
        assert "no timings" in timer.summary()

    def test_add_accumulates_count_and_total(self):
        """Manual add() sums duration and counts occurrences per label."""
        timer = PhaseTimer()
        timer.add("tier2_nominatim", 1.0)
        timer.add("tier2_nominatim", 2.0)
        assert timer.total("tier2_nominatim") == 3.0
        assert timer.is_empty() is False

    def test_negative_duration_is_clamped(self):
        """A negative delta (clock skew) never subtracts from the total."""
        timer = PhaseTimer()
        timer.add("x", -5.0)
        assert timer.total("x") == 0.0

    def test_phase_context_manager_records_time(self):
        """The phase() context manager records a positive elapsed time."""
        timer = PhaseTimer()
        with timer.phase("work"):
            time.sleep(0.01)  # Small, real sleep to accrue measurable time.
        assert timer.total("work") > 0.0

    def test_phase_records_even_on_exception(self):
        """Time is recorded even when the wrapped block raises."""
        timer = PhaseTimer()
        try:
            with timer.phase("boom"):
                raise ValueError("x")
        except ValueError:
            pass
        assert timer.total("boom") >= 0.0  # Slot created and recorded despite the raise.
        assert timer.is_empty() is False

    def test_summary_sorted_slowest_first(self):
        """The summary lists phases from slowest to fastest total."""
        timer = PhaseTimer()
        timer.add("fast", 0.10)
        timer.add("slow", 9.00)
        timer.add("mid", 1.00)
        lines = timer.summary().splitlines()
        assert "slow" in lines[0] and "mid" in lines[1] and "fast" in lines[2]

    def test_total_of_unknown_label_is_zero(self):
        """Querying a never-timed label returns 0.0, not an error."""
        assert PhaseTimer().total("nope") == 0.0
