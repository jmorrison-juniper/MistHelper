"""Test clipping notice behavior with the real browser component."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from playwright.sync_api import expect


def test_notice_tracks_geometry_and_keeps_safe_row_access(page: Any) -> None:
    """The component measures layout, exposes row details, and rejects stale data."""
    page.set_viewport_size({"width": 1280, "height": 800})  # Keep the component viewport deterministic.
    page.set_content("""
        <style>
            #resultsTableWrap { width: 260px; }
            #resultsTable { width: 100%; table-layout: fixed; }
            #resultsTable td { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        </style>
        <div id="resultsPanel">
            <select id="resultsFileSelect"></select>
            <input id="resultsSearch">
            <p id="resultsSummary"></p>
            <div id="resultsTruncated" class="d-none"></div>
            <div id="resultsPagination" class="d-none"><span id="resultsPageInfo"></span></div>
            <div id="resultsTableWrap">
                <table id="resultsTable"><thead id="resultsHead"></thead><tbody id="resultsBody"></tbody></table>
            </div>
        </div>
        <div id="outputFiles"><ul id="outputFileList"></ul></div>
        """)  # Provide the existing component IDs without changing production markup.
    page.evaluate("""() => {
            window.escapeHtml = value => String(value).replace(/[&<>"']/g, character =>
                ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[character]));
            window.readJsonAnswer = response => response.json();
            window.__longValue = '<img src=x onerror=alert(1)>' + 'x'.repeat(240);
            window.__answers = {
                'long.csv': {columns: ['value'], rows: [[window.__longValue]], page: 1,
                    total_pages: 1, total_rows: 1, sort_truncated: false},
                'short.csv': {columns: ['value'], rows: [['short']], page: 1,
                    total_pages: 1, total_rows: 1, sort_truncated: false},
                'sort.csv': {columns: ['value'], rows: [['short']], page: 1,
                    total_pages: 1, total_rows: 1, sort_truncated: true, sort_limit: 50},
                'slow.csv': {columns: ['value'], rows: [[window.__longValue]], page: 1,
                    total_pages: 1, total_rows: 1, sort_truncated: false}
            };
            window.__pendingSlow = null;
            window.fetch = url => {
                const filename = decodeURIComponent(url.split('?')[0].split('/').pop());
                if (filename === 'slow.csv') {
                    return new Promise(resolve => { window.__pendingSlow = resolve; });
                }
                return Promise.resolve({json: () => Promise.resolve(window.__answers[filename])});
            };
        }""")  # Stub only the preview transport so the production browser component runs in isolation.
    component_path = Path(__file__).resolve().parents[4] / "web_portal" / "static" / "js" / "operation_results.js"
    page.add_script_tag(path=str(component_path))  # Load the actual results component source.
    page.evaluate("() => OperationResults.showForRun(['long.csv'])")
    notice = page.locator("#resultsTruncated")
    expect(notice).to_be_visible()  # The clipped value must show the notice.
    expect(notice).to_contain_text("The table shortens values that do not fit")  # Add the measured clipping warning.
    measured = page.locator("#resultsBody tr[data-row] td").first.evaluate(
        "(cell) => ({client: cell.clientWidth, scroll: cell.scrollWidth})"
    )  # Read actual browser geometry instead of estimating from string length.
    assert measured["client"] > 0 and measured["scroll"] > measured["client"]  # Require visible cell overflow.
    control = page.get_by_role("button", name="Open details for row 1")
    expect(control).to_have_attribute("aria-controls", "result-detail-0")  # Name the actual detail target.
    control.click()  # Use the notice control to open the existing full row detail.
    detail = page.get_by_test_id("results-row-detail")
    expect(detail.locator("dd")).to_have_text(page.evaluate("() => window.__longValue"))  # Keep safe full text.
    assert detail.locator("img").count() == 0  # Treat the supplied markup as text, not executable HTML.
    expect(control).to_have_attribute("aria-expanded", "true")  # Report the actual expanded state.
    output_link = page.get_by_role("link", name="Output Files")
    expect(output_link).to_have_attribute("href", "#outputFiles")  # Point to the existing output panel.
    old_control = control.element_handle()
    page.evaluate("() => { document.getElementById('resultsTableWrap').style.width = '3000px'; }")
    page.wait_for_function("(element) => !element.isConnected", arg=old_control, timeout=5000)
    expect(notice).to_be_hidden()  # Clear the notice after the value fits the resized cell.
    page.evaluate("() => { document.getElementById('resultsTableWrap').style.width = '260px'; }")
    expect(notice).to_be_visible()  # Recheck geometry when the resized cell clips the value again.
    page.evaluate("() => OperationResults.selectFile('slow.csv')")  # Start a preview that remains pending.
    page.evaluate("() => OperationResults.selectFile('short.csv')")  # Select a short result before the old reply.
    expect(page.locator("#resultsSummary")).to_contain_text("Showing 1 to 1 of 1 rows.")
    page.evaluate("""async () => {
            window.__pendingSlow({json: () => Promise.resolve(window.__answers['slow.csv'])});
            await new Promise(requestAnimationFrame);
        }""")  # Complete and drain the stale response only after the current file has rendered.
    expect(page.locator("#resultsSummary")).to_contain_text("Showing 1 to 1 of 1 rows.")
    expect(page.locator("#resultsBody tr[data-row] td").first).to_have_text("short")
    expect(notice).to_be_hidden()  # A stale long response must not restore another file's warning.
    page.evaluate("() => OperationResults.selectFile('sort.csv')")  # Load one short row with the server sort warning.
    expect(notice).to_have_text(
        "This file holds more rows than one sort can cover, so the order reads the first "
        "50 rows only. Filter the rows to narrow the result."
    )  # Preserve the existing warning text without a clipping false positive.
