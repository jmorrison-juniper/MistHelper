"""Wave 3 top-up tests for ConfigUtils.check_stop_signal (initiative 1018).

Targets the last uncovered branch in
``src/config/config_utils.py`` -- the ``except OSError: pass`` block
on lines 153-154 of ``check_stop_signal``. The existing test module
``test_config_utils.py`` covers the happy path and the missing-file
path; this file adds the OSError race path.
"""

from __future__ import annotations  # WHY: PEP 604 unions retained across whole test module.

from unittest.mock import patch  # WHY: patch os.remove to raise OSError deterministically.

import pytest

from src.config.config_utils import ConfigUtils  # WHY: SUT under test.


@pytest.fixture(autouse=True)
def _reset_state(tmp_path, monkeypatch):
    """Isolate cwd so stop_loop.txt cannot leak between tests."""
    monkeypatch.chdir(tmp_path)  # WHY: put test cwd in tmp so real stop_loop.txt never affects prod dir.
    yield  # WHY: yields fixture control back for the test body.


class TestCheckStopSignalOSError:
    """Cover the ``except OSError`` swallow branch when the removal race triggers."""

    def test_os_remove_oserror_still_returns_true(self, tmp_path) -> None:
        """When os.remove raises OSError, check_stop_signal must swallow and still return True."""
        stop_file = tmp_path / "stop_loop.txt"  # WHY: signal file must exist for os.path.exists to be True.
        stop_file.write_text("")  # WHY: sentinel content is irrelevant; presence is what matters.
        with patch("src.config.config_utils.os.remove", side_effect=OSError("simulated race")):  # WHY: force line 153.
            result = ConfigUtils.check_stop_signal()  # WHY: exercise the except-branch swallow.
        assert result is True  # WHY: the swallow must not change the return contract.
