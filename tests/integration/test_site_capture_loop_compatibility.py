"""Parity tests for site capture loop compatibility path."""

from unittest.mock import MagicMock

from src.capture.site_capture_loop import SiteCaptureLoopRunner


def test_site_capture_loop_runner_stops_on_keyboard_interrupt() -> None:
    """Runner exits cleanly and emits loop-stop log callback on interrupt."""
    manager = MagicMock()
    manager._fetch_completed_pcaps.side_effect = KeyboardInterrupt
    runner = SiteCaptureLoopRunner(manager=manager)
    runner.run("site-1", {"duration": 60})
    manager._log_loop_stop.assert_called_once()
