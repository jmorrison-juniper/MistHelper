"""Guards for the Operations portal stream fallback."""

from __future__ import annotations

import re
from pathlib import Path

OPERATIONS_SCRIPT = (
    Path(__file__).parents[3] / "web_portal" / "static" / "js" / "operations.js"
)  # Read the served controller.


def _function_body(source: str, name: str) -> str:
    """Return the body of a simple top-level JavaScript function."""
    match = re.search(rf"function {name}\([^)]*\) \{{(?P<body>.*?)\n\}}", source, re.S)  # Isolate one function.
    assert (
        match is not None
    ), f"The {name} function is missing from operations.js."  # Fail if a refactor moves the path.
    return match.group("body")  # Return one body so each assertion checks the intended path.


def test_stream_arms_status_fallback_for_quiet_runs() -> None:
    """Issue #3183. A quiet stream must ask the status route before timeout."""
    source = OPERATIONS_SCRIPT.read_text(encoding="utf-8")  # Inspect the JavaScript that the portal serves.
    start_body = _function_body(source, "startSSEStream")  # Check the stream setup path.
    arm_body = _function_body(source, "armStatusFallback")  # Check the timer helper.
    check_body = _function_body(source, "checkRunStatus")  # Check the REST fallback path.
    finish_body = _function_body(source, "finishRun")  # Check terminal cleanup.

    assert "STATUS_FALLBACK_MS = 15000" in source, "The quiet stream window must stay below 20 seconds."
    assert "armStatusFallback(runId);" in start_body, "The stream must arm fallback when it starts."
    assert "setTimeout(function()" in arm_body, "The fallback helper must use a bounded timer."
    assert "checkRunStatus(runId, true);" in arm_body, "The timer must ask the status route and rearm if running."
    assert "rearmWhenRunning" in check_body, "The status check must know when to keep watching a running server state."
    assert "armStatusFallback(runId);" in check_body, "A running status answer must arm another bounded check."
    assert "clearStatusFallbackTimer();" in finish_body, "A terminal run must cancel stale fallback timers."
