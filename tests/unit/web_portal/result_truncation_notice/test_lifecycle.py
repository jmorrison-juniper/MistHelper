"""Run deterministic Node lifecycle checks against the actual browser module."""

import subprocess
from pathlib import Path


class TestResultNoticeLifecycle:
    """Make browser work cancellation measurable without timing-dependent sleeps."""

    def test_pending_work_and_handlers_are_released(self) -> None:
        """The Node suite exercises callbacks that a browser normally schedules later."""
        script = Path(__file__).with_name("lifecycle.cjs")
        result = subprocess.run(
            ["node", "--test", "--test-reporter=tap", str(script)],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "# pass 6" in result.stdout, result.stdout
