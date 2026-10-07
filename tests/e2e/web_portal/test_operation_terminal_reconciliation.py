"""Browser tests for authoritative operation state and output replay."""

from __future__ import annotations  # Keep modern annotations out of runtime imports.

import logging  # Record browser setup and measured state for failed CI runs.
from pathlib import Path  # Build the production script path without platform-specific text.
from typing import Any  # Type the Playwright page without a hard runtime import.

import pytest  # Use the shared pytest-playwright page fixture.

logger = logging.getLogger(__name__)  # Name this browser module in the test log.

pytest.importorskip("playwright", reason="The Playwright package is not installed.")

ROOT = Path(__file__).parents[3]  # Anchor the production script at the repository root.
OPERATIONS_SCRIPT = ROOT / "web_portal" / "static" / "js" / "operations.js"  # Test the shipped controller.
READY_TIMEOUT_MS = 2000  # A missing reconciliation must fail quickly.


def _load_operation_shell(page: Any) -> None:
    """Load the minimum document and browser APIs for one active operation."""
    logger.info("Loading the operation reconciliation browser shell")  # Mark the setup action.
    page.set_content(OPERATION_SHELL)  # Provide every node that the run lifecycle reads.
    page.evaluate(
        """
        () => {
          const nativeSetTimeout = window.setTimeout.bind(window);
          window.setTimeout = (callback, delay) =>
            nativeSetTimeout(callback, delay === 5000 ? 20 : delay);
          window.__statusCalls = 0;
          window.__eventSource = null;
          window.readJsonAnswer = (response) => response.json();
          window.OperationResults = {
            reset() {},
            showForRun() {}
          };
          window.EventSource = class {
            constructor(url) {
              this.url = url;
              this.listeners = {};
              this.closed = false;
              window.__eventSource = this;
            }
            addEventListener(name, callback) {
              this.listeners[name] = callback;
            }
            close() {
              this.closed = true;
            }
          };
          const jsonResponse = (payload) => new Response(JSON.stringify(payload), {
            status: 200,
            headers: { "Content-Type": "application/json" }
          });
          window.fetch = async (url) => {
            if (String(url).includes("/api/operations/status/run-4027")) {
              window.__statusCalls += 1;
              return jsonResponse({
                run_id: "run-4027",
                status: "completed",
                completion_message: "Operation completed",
                output_files: []
              });
            }
            return jsonResponse({ active: [] });
          };
        }
        """
    )  # Install an open SSE stream and an authoritative completed status.
    page.add_script_tag(path=str(OPERATIONS_SCRIPT))  # Load the production controller after its dependencies.
    logger.debug("Loaded the operation reconciliation browser shell")  # Confirm setup completion.


def test_terminal_rest_state_recovers_a_lost_terminal_sse_event(page: Any) -> None:
    """A completed REST record must finish a run when terminal SSE is absent."""
    _load_operation_shell(page)  # Build the isolated browser state.
    page.evaluate(
        """
        () => {
          currentRunId = "run-4027";
          resetExecutionPanel();
          setStatus("running", "Running...");
          startSSEStream(currentRunId);
        }
        """
    )  # Start a stream that never sends a complete event.

    page.wait_for_function("window.__statusCalls > 0", timeout=READY_TIMEOUT_MS)  # Wait for reconciliation.

    assert page.locator("#statusBadge").inner_text() == "Complete"  # The stale Running badge must change.
    assert page.locator("#statusMessage").inner_text() == "Operation completed"  # Keep the server message.
    assert page.evaluate("currentRunId") is None  # A terminal REST record must finish the active run.
    assert page.evaluate("window.__eventSource.closed") is True  # The finished run must release its SSE stream.


OPERATION_SHELL = """
<button id="runBtn">Run Operation</button>
<button id="stopBtn" class="d-none">Stop Operation</button>
<div id="executionPanel" class="d-none">
  <div id="logViewer"></div>
  <div id="debugLogViewer"></div>
  <button id="debugLogToggle" class="d-none"></button>
  <div id="debugLogPanel" class="d-none"></div>
  <span id="debugLogCount">0</span>
  <div id="outputFiles" class="d-none"><ul id="outputFileList"></ul></div>
</div>
<div id="progressBar"></div>
<span id="statusBadge">Pending</span>
<span id="statusMessage"></span>
<div id="activeOpsPanel" class="d-none"><div id="activeOpsList"></div></div>
"""
