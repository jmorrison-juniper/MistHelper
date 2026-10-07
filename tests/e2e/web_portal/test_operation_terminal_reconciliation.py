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
    page.evaluate("""
        () => {
          const nativeSetTimeout = window.setTimeout.bind(window);
          window.setTimeout = (callback, delay) =>
            nativeSetTimeout(callback, delay === 5000 ? 20 : delay);
          window.__statusCalls = 0;
          window.__statusAnswers = {};
          window.__eventSource = null;
          window.__resultCalls = [];
          window.readJsonAnswer = (response) => response.json();
          window.OperationResults = {
            reset() {
              document.getElementById("resultsPanel").classList.add("d-none");
              document.getElementById("resultsSummary").textContent = "";
            },
            showForRun(files) {
              window.__resultCalls.push(files.slice());
              const panel = document.getElementById("resultsPanel");
              const summary = document.getElementById("resultsSummary");
              if (files.length === 0) {
                panel.classList.add("d-none");
                summary.textContent = "";
                return;
              }
              panel.classList.remove("d-none");
              summary.textContent = "Loading the results...";
            }
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
            emit(name, payload) {
              this.listeners[name]({ data: JSON.stringify(payload) });
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
            if (String(url).includes("/api/operations/status/")) {
              window.__statusCalls += 1;
              const runId = String(url).split("/").pop();
              return jsonResponse(window.__statusAnswers[runId] || { status: "running" });
            }
            return jsonResponse({ active: [] });
          };
        }
        """)  # Install an open SSE stream and an authoritative completed status.
    page.add_script_tag(path=str(OPERATIONS_SCRIPT))  # Load the production controller after its dependencies.
    logger.debug("Loaded the operation reconciliation browser shell")  # Confirm setup completion.


def test_terminal_rest_state_recovers_a_lost_terminal_sse_event(page: Any) -> None:
    """A completed REST record must finish a run when terminal SSE is absent."""
    _load_operation_shell(page)  # Build the isolated browser state.
    page.evaluate("""
        () => {
          currentRunId = "run-4027";
          resetExecutionPanel();
          setStatus("running", "Running...");
          startSSEStream(currentRunId);
        }
        """)  # Start a stream that never sends a complete event.

    page.wait_for_function("window.__statusCalls > 0", timeout=READY_TIMEOUT_MS)  # Wait for reconciliation.

    assert page.locator("#statusBadge").inner_text() == "Complete"  # The stale Running badge must change.
    assert page.locator("#statusMessage").inner_text() == "Operation completed"  # Keep the server message.
    assert page.evaluate("currentRunId") is None  # A terminal REST record must finish the active run.
    assert page.evaluate("window.__eventSource.closed") is True  # The finished run must release its SSE stream.


def test_sse_error_does_not_overlap_a_pending_status_request(page: Any) -> None:
    """An SSE error must reuse the one-request reconciliation guard."""
    _load_operation_shell(page)  # Build the isolated browser state.
    page.evaluate("""
        () => {
          window.__activeStatusRequests = 0;
          window.__maximumStatusRequests = 0;
          window.__releaseStatusRequest = null;
          window.fetch = async (url) => {
            if (String(url).includes("/api/operations/status/run-4027-pending")) {
              window.__activeStatusRequests += 1;
              window.__maximumStatusRequests = Math.max(
                window.__maximumStatusRequests,
                window.__activeStatusRequests
              );
              return new Promise((resolve) => {
                window.__releaseStatusRequest = () => {
                  window.__activeStatusRequests -= 1;
                  resolve(new Response(JSON.stringify({ status: "running" }), {
                    status: 200,
                    headers: { "Content-Type": "application/json" }
                  }));
                };
              });
            }
            return new Response(JSON.stringify({ active: [] }), {
              status: 200,
              headers: { "Content-Type": "application/json" }
            });
          };
          currentRunId = "run-4027-pending";
          resetExecutionPanel();
          setStatus("running", "Running...");
          startSSEStream(currentRunId);
        }
        """)  # Hold the scheduled status request open before the SSE error arrives.
    page.wait_for_function("window.__activeStatusRequests === 1", timeout=READY_TIMEOUT_MS)  # Wait for the first read.

    page.evaluate("window.__eventSource.onerror()")  # Reproduce a stream error during the pending REST request.
    page.wait_for_timeout(100)  # Allow any incorrect second fetch to start.

    assert page.evaluate("window.__maximumStatusRequests") == 1  # The browser must keep one request in flight.
    assert page.evaluate("window.__activeStatusRequests") == 1  # The first request must remain the only pending read.
    page.evaluate("window.__releaseStatusRequest()")  # Release the held request before the page fixture closes.


def test_rest_replay_and_terminal_sse_render_one_output_link(page: Any) -> None:
    """The same run file from REST and SSE must produce one output link."""
    _load_operation_shell(page)  # Build the isolated browser state.
    page.evaluate("""
        () => {
          window.__statusAnswers["run-4032-one"] = {
            run_id: "run-4032-one",
            status: "running",
            log_messages: [],
            debug_messages: [],
            output_files: ["Sites.csv"]
          };
          reconnectToOperation("run-4032-one", "2", "Export sites");
        }
        """)  # Replay one known file before the terminal stream event arrives.
    page.wait_for_function("window.__statusCalls > 0", timeout=READY_TIMEOUT_MS)  # Wait for REST replay.
    page.evaluate("""
        () => window.__eventSource.emit("complete", {
          run_id: "run-4032-one",
          message: "Operation completed",
          output_files: ["Sites.csv"]
        })
        """)  # Deliver the same stable file identity through terminal SSE.

    assert page.locator("#outputFileList a").count() == 1  # A repeated delivery must not append a second link.
    assert page.locator("#outputFileList a").all_inner_texts() == ["Sites.csv"]  # Keep the real file visible.


def test_output_deduplication_preserves_two_distinct_file_paths(page: Any) -> None:
    """Deduplication must keep every distinct server file path."""
    _load_operation_shell(page)  # Build the isolated browser state.
    page.evaluate("""
        () => {
          window.__statusAnswers["run-4032-two"] = {
            run_id: "run-4032-two",
            status: "running",
            log_messages: [],
            debug_messages: [],
            output_files: ["Sites.csv", "Sites.json"]
          };
          reconnectToOperation("run-4032-two", "2", "Export sites");
        }
        """)  # Replay two distinct server paths before terminal SSE repeats them.
    page.wait_for_function("window.__statusCalls > 0", timeout=READY_TIMEOUT_MS)  # Wait for REST replay.
    page.evaluate("""
        () => window.__eventSource.emit("complete", {
          run_id: "run-4032-two",
          message: "Operation completed",
          output_files: ["Sites.csv", "Sites.json"]
        })
        """)  # Repeat the complete ordered set through terminal SSE.

    assert page.locator("#outputFileList a").count() == 2  # Repeated delivery must not double the set.
    assert page.locator("#outputFileList a").all_inner_texts() == [  # Preserve both real file identities.
        "Sites.csv",
        "Sites.json",
    ]


def test_empty_terminal_output_clears_a_stale_loading_preview(page: Any) -> None:
    """A no-output terminal state must close a stale result preview."""
    _load_operation_shell(page)  # Build the isolated browser state.
    page.evaluate("""
        () => {
          currentRunId = "run-4032-empty";
          resetExecutionPanel();
          setStatus("running", "Running...");
          startSSEStream(currentRunId);
          showOutputFiles(["Old.csv"]);
        }
        """)  # Reproduce a preview that still reads Loading when terminal state arrives.
    assert page.locator("#resultsSummary").inner_text() == "Loading the results..."  # Prove the stale state exists.

    page.evaluate("""
        () => window.__eventSource.emit("complete", {
          run_id: "run-4032-empty",
          message: "Operation completed with no output file",
          output_files: []
        })
        """)  # Deliver the no-output terminal state through SSE.

    assert page.locator("#resultsPanel").is_hidden()  # The terminal empty set must close the stale preview.
    assert page.evaluate("window.__resultCalls.at(-1)") == []  # The result helper must receive the empty set.


OPERATION_SHELL = """
<div id="selectedOp" class="d-none"><h5 id="selectedOpTitle"></h5><p id="selectedOpDesc"></p></div>
<div id="parameterForm"></div>
<div id="cliOnlyPanel"></div>
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
<div id="resultsPanel" class="d-none"><p id="resultsSummary"></p></div>
"""
