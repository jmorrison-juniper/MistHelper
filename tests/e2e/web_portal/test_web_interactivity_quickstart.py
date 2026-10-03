"""Browser coverage for the web interactivity quickstart closeout."""

from __future__ import annotations  # Keep modern annotations out of runtime imports.

import json  # Encode the mocked API records for browser-side route stubs.
import logging  # Record each browser setup and assertion step for diagnostics.
from pathlib import Path  # Build paths without platform-specific separators.
from typing import Any  # Type the Playwright page without a hard test dependency.

import pytest  # Use pytest fixtures and skip support for browser availability.

logger = logging.getLogger(__name__)  # A module logger keeps the record source readable.

pytest.importorskip("playwright.sync_api", reason="The Playwright package is not installed.")

ROOT = Path(__file__).parents[2]  # Anchor asset paths at the repository root.
SCRIPT_DIR = ROOT / "web_portal" / "static" / "js"  # Reuse the production browser scripts.
OPERATIONS_SCRIPT = SCRIPT_DIR / "operations.js"  # Load the Operations controller.
DATA_PREVIEW_SCRIPT = SCRIPT_DIR / "data_preview.js"  # Load the preview modal controller.
# Issue #3087: `base.html` loads `portal.js` on every page, and the other two
# scripts now read every answer through its `readJsonAnswer` helper. This shell
# must load the same file in the same order, or it tests a page that production
# never serves.
PORTAL_SCRIPT = SCRIPT_DIR / "portal.js"  # Load the shared helpers that base.html loads first.


def _install_browser_stubs(page: Any, preview_rows: list[list[str]]) -> None:
    """Install API, CSRF, event stream, and modal stubs in the browser page."""
    logger.info("Installing quickstart browser stubs")  # Mark the browser stub setup.
    page.evaluate(  # Install deterministic browser APIs before the production scripts run.
        """
        (config) => {
          window.__runBody = null;
          window.getCsrfToken = () => 'test-token';
          window.EventSource = class {
            constructor(url) { this.url = url; }
            addEventListener() {}
            close() {}
          };
          window.bootstrap = { Modal: class {
            constructor(el) { this.el = el; }
            show() { this.el.classList.add('show'); }
            hide() { this.el.classList.remove('show'); }
          } };
          // Issue #3087: every caller now reads an answer through
          // `readJsonAnswer`, which uses `response.text()`, `response.ok`, and
          // `response.status`. A bare object carrying only `json` does not hold
          // those members, so this stub returns a real `Response` and therefore
          // exercises the same interface that `fetch` returns in production.
          const jsonResponse = (payload) => new Response(JSON.stringify(payload), {
            status: 200,
            headers: { 'Content-Type': 'application/json' }
          });
          window.fetch = async (url, options = {}) => {
            if (String(url).includes('/api/operations/parameters/31')) {
              return jsonResponse({
                category: 'interactive',
                parameters: [{ name: 'site_id', label: 'Site', param_type: 'site', required: true }]
              });
            }
            if (String(url).includes('/api/operations/sites')) {
              return jsonResponse({ sites: [{ id: 'site-alpha', name: 'Alpha', address: 'Lab' }] });
            }
            if (String(url).includes('/api/operations/run')) {
              window.__runBody = JSON.parse(options.body);
              return jsonResponse({ run_id: 'run-issue-992' });
            }
            if (String(url).includes('/api/data/preview/')) {
              return jsonResponse({
                columns: ['site', 'device', 'status'],
                rows: config.rows,
                page: 1,
                total_pages: 1,
                total_rows: config.rows.length
              });
            }
            return jsonResponse({ active_runs: [] });
          };
        }
        """,
        json.loads(json.dumps({"rows": preview_rows})),
    )
    logger.debug("Installed browser stubs for %d preview rows", len(preview_rows))  # Record the stub size.


def _load_operations_shell(page: Any) -> None:
    """Load the minimum Operations page nodes that the production script needs."""
    logger.info("Loading the Operations quickstart shell")  # Mark the DOM setup.
    page.set_content(OPERATIONS_HTML)  # Provide the production script with its required element identifiers.
    page.add_script_tag(path=str(PORTAL_SCRIPT))  # Load the shared helpers first, exactly as base.html does.
    page.add_script_tag(path=str(DATA_PREVIEW_SCRIPT))  # Add the shared modal script before the Operations script.
    page.add_script_tag(path=str(OPERATIONS_SCRIPT))  # Add the production Operations controller.
    logger.debug("Loaded the Operations quickstart shell")  # Confirm the script setup.


def test_quickstart_menu31_posts_selected_site(page: Any) -> None:
    """Menu 31 renders a site field and sends the selected answer."""
    _load_operations_shell(page)  # Build the page before browser stubs use its elements.
    _install_browser_stubs(page, [["Alpha", "Switch-1", "ok"]])  # Serve one site and one preview row.
    logger.info("Rendering Menu 31 in the Operations list")  # Mark the accordion rendering step.
    page.evaluate(
        "renderAccordion([{name:'Site Data Exports',operations:["
        "{menu_number:31,description:'Site devices',category:'interactive'}]}])"
    )  # Render Menu 31.
    page.locator('[data-menu="31"]').click()  # Select the interactive operation from the list.
    page.wait_for_selector("#param-site_id:not([disabled])")  # Wait until the site API fills the dropdown.
    page.locator("#param-site_id").select_option("Alpha")  # Choose the only mocked site.
    page.evaluate("runSelectedOperation()")  # Start the operation with the selected parameter.
    page.wait_for_function("window.__runBody !== null")  # Wait until the mocked run endpoint receives the body.
    run_body = page.evaluate("window.__runBody")  # Read the submitted operation payload from the page.
    expected_body = {  # Define the expected payload.
        "menu_number": "31",
        "parameters": {"input_answers": ["Alpha"]},
    }
    assert run_body == expected_body  # Verify input injection order.
    logger.debug("Menu 31 submitted body: %s", run_body)  # Record the submitted body.


def test_quickstart_data_browser_modal_opens_csv(page: Any) -> None:
    """The shared preview modal opens a CSV table from the Data Browser path."""
    _load_operations_shell(page)  # Reuse the same modal markup that both pages render.
    _install_browser_stubs(page, [["Alpha", "Switch-1", "ok"], ["Bravo", "Gateway-1", "ok"]])  # Serve two CSV rows.
    logger.info("Opening the Data Browser CSV preview")  # Mark the modal action.
    page.evaluate("DataPreviewModal.openPreview('issue992_quickstart.csv')")  # Open the modal through the public API.
    page.wait_for_selector("#modalPreviewTable")  # Wait for CSV rows to render.
    rows = page.locator("#modalPreviewTable tbody tr").all_inner_texts()  # Read the visible CSV rows.
    assert rows == ["Alpha\tSwitch-1\tok", "Bravo\tGateway-1\tok"]  # Verify the modal rendered the table.
    assert "show" in page.locator("#dataPreviewModal").get_attribute("class")  # Verify the modal opened in place.
    logger.debug("Data Browser modal rows: %s", rows)  # Record the rendered rows.


def test_quickstart_operations_result_preview_reuses_modal(page: Any) -> None:
    """The Operations output list opens the same CSV preview modal."""
    _load_operations_shell(page)  # Load the Operations page shell with the output list.
    _install_browser_stubs(page, [["Alpha", "Switch-1", "ok"]])  # Serve the output preview row.
    logger.info("Rendering an Operations output file")  # Mark the result-list rendering step.
    page.evaluate("showOutputFiles(['issue992_quickstart.csv'])")  # Render an output file as a completed run would.
    page.locator("#outputFileList button").click()  # Open the preview from the Operations result list.
    page.wait_for_selector("#modalPreviewTable")  # Wait for the modal to render the CSV table.
    modal_title = page.locator("#dataPreviewModalLabel").inner_text()  # Read the modal title.
    assert modal_title == "Preview: issue992_quickstart.csv"  # Verify the file title.
    assert page.locator("#executionPanel").is_visible()  # Verify the Operations page state stays visible.
    logger.debug("Operations result preview stayed on the Operations page")  # Record the state preservation check.


OPERATIONS_HTML = """
<div id="operationAccordion"></div>
<input id="opSearch">
<div id="selectedOp"><h5 id="selectedOpTitle"></h5><p id="selectedOpDesc"></p></div>
<div id="cliOnlyPanel"><p id="cliOnlyMessage"></p></div>
<div id="parameterForm">
  <div id="parameterFields"></div>
  <div id="parameterLoading"></div>
  <div id="parameterError"><span id="parameterErrorMsg"></span></div>
</div>
<button id="runBtn"></button><button id="stopBtn"></button>
<div id="activeOpsPanel"><div id="activeOpsList"></div></div>
<div id="executionPanel">
  <div id="logViewer"></div>
  <div id="debugLogViewer"></div>
  <button id="debugLogToggle"></button>
  <div id="debugLogPanel"></div>
  <span id="debugLogCount">0</span>
  <div id="outputFiles"><ul id="outputFileList"></ul></div>
</div>
<div id="progressBar"></div><span id="statusBadge"></span><span id="statusMessage"></span>
<div class="modal fade modal-fullscreen-custom" id="dataPreviewModal">
  <h5 id="dataPreviewModalLabel"></h5>
  <div id="dataPreviewSearchRow" class="d-none"><input id="dataPreviewSearch"></div>
  <div id="dataPreviewLoading"></div>
  <div id="dataPreviewBody"></div>
  <div id="dataPreviewPagination"></div>
  <button id="dataPreviewPrev"></button>
  <span id="dataPreviewPageInfo"></span>
  <button id="dataPreviewNext"></button>
</div>
"""
