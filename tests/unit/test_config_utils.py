"""Unit tests for ConfigUtils.check_stop_signal() logic.

Duplicates the pure function from MistHelper.py to avoid import side effects
(research.md R1 pattern). Tests the file-based stop signal mechanism that
allows users to cancel long-running loops by creating stop_loop.txt.
"""

import os

import pytest


# ---------------------------------------------------------------------------
# Duplicated pure function (R1: avoid MistHelper.py import side effects)
# ---------------------------------------------------------------------------
def check_stop_signal():
    """Mirror of ConfigUtils.check_stop_signal() from MistHelper.py."""
    if os.path.exists("stop_loop.txt"):
        try:
            os.remove("stop_loop.txt")
        except OSError:
            pass
        print("  Stop signal detected. Ending operation early.")
        return True
    return False


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _cleanup():
    """Remove stop_loop.txt before and after each test."""
    if os.path.exists("stop_loop.txt"):
        os.remove("stop_loop.txt")
    yield
    if os.path.exists("stop_loop.txt"):
        os.remove("stop_loop.txt")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
class TestCheckStopSignal:
    """Tests for the check_stop_signal file-based cancellation mechanism."""

    def test_no_file_returns_false(self):
        """No stop file present should return False."""
        assert check_stop_signal() is False

    def test_file_present_returns_true(self):
        """Stop file present should return True and delete the file."""
        with open("stop_loop.txt", "w") as handle:
            handle.write("")
        assert os.path.exists("stop_loop.txt")
        assert check_stop_signal() is True
        assert not os.path.exists("stop_loop.txt")

    def test_consumed_signal_returns_false(self):
        """After signal is consumed, next call should return False."""
        with open("stop_loop.txt", "w") as handle:
            handle.write("")
        check_stop_signal()
        assert check_stop_signal() is False

    def test_loop_breaks_on_signal(self):
        """Simulated site loop should break when stop signal is detected."""
        sites = ["site_a", "site_b", "site_c", "site_d", "site_e"]
        processed = []
        with open("stop_loop.txt", "w") as handle:
            handle.write("")
        for site in sites:
            if check_stop_signal():
                break
            processed.append(site)
        assert len(processed) == 0
        assert not os.path.exists("stop_loop.txt")

    def test_loop_processes_until_mid_run_signal(self):
        """Loop should process sites normally until stop file appears mid-run."""
        sites = ["site_a", "site_b", "site_c", "site_d", "site_e"]
        processed = []
        for i, site in enumerate(sites):
            if i == 3:
                with open("stop_loop.txt", "w") as handle:
                    handle.write("")
            if check_stop_signal():
                break
            processed.append(site)
        assert processed == ["site_a", "site_b", "site_c"]
