"""Guards for the Operations portal frontend state."""

from __future__ import annotations

import re
from pathlib import Path

OPERATIONS_SCRIPT = (
    Path(__file__).parents[3] / "web_portal" / "static" / "js" / "operations.js"
)  # Read the shipped browser controller.


def _function_body(source: str, name: str) -> str:
    """Return the body of a simple top-level JavaScript function."""
    match = re.search(rf"function {name}\([^)]*\) \{{(?P<body>.*?)\n\}}", source, re.S)  # Isolate one target function.
    assert (
        match is not None
    ), f"The {name} function is missing from operations.js."  # Fail fast when a refactor moves it.
    return match.group("body")  # Return only the function body so each assertion stays local.


def test_selection_clears_execution_state_without_revealing_panel() -> None:
    """Issue #3154. Selection must clear stale output without showing an empty panel."""
    source = OPERATIONS_SCRIPT.read_text(encoding="utf-8")  # Inspect the exact JavaScript that the portal serves.
    select_body = _function_body(source, "selectOperation")  # Check the operator selection path.
    clear_body = _function_body(source, "clearExecutionPanel")  # Check the clear-only helper.
    reset_body = _function_body(source, "resetExecutionPanel")  # Check the run-start reset helper.

    assert (
        "clearExecutionPanel();" in select_body
    ), "selectOperation() must clear stale run output."  # Guard issue #3154.
    assert (
        "setElementVisible('executionPanel', true)" not in clear_body
    ), "clearExecutionPanel() must not reveal the execution panel during selection."  # Keep command-line selections from showing an empty panel.
    assert (
        "OperationResults.reset()" in clear_body
    ), "The clear helper must clear the result table state."  # Clear result rows.
    assert (
        "setElementVisible('executionPanel', true)" in reset_body
    ), "Run starts must still reveal the execution panel."  # Preserve run behavior.
    assert (
        "clearExecutionPanel();" in reset_body
    ), "resetExecutionPanel() must reuse the shared clear helper."  # Keep one clear path.
