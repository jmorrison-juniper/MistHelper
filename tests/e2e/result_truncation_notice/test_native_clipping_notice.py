"""Prove the clipped-value notice through the real menu 55 portal."""

from __future__ import annotations  # Keep annotations unevaluated for consistent test typing.

import json  # Prove malformed JSON errors without a network response.
from collections.abc import Iterator  # Type the portal fixture lifecycle.
from pathlib import Path  # Type the private temporary directory.
from typing import Any  # Match existing Playwright fixture annotations.
from unittest.mock import MagicMock  # Model only the completed response boundary.

import pytest  # Parametrize bounded failure-mode cases and assert expected errors.
from playwright.sync_api import expect  # Assert the real browser contract.

from tests.support.result_truncation_notice.native_portal import NativeResultPortal  # Use the actual private harness.


@pytest.fixture
def native_portal(tmp_path: Any) -> Iterator[NativeResultPortal]:
    """Start one isolated portal and always stop its owned resources."""
    portal = NativeResultPortal(tmp_path)  # Keep generated files outside the checkout.
    try:
        portal.start()  # Install refusal boundaries before the portal can invoke the handler.
        yield portal  # Expose the actual app, handler, SDK, and output ledger to one test.
    finally:
        portal.close()  # Restore process state and remove only this fixture's directory.


def test_native_menu_55_discloses_clipped_values(page: Any, native_portal: NativeResultPortal) -> None:
    """The long result must disclose clipping without changing its exported bytes."""
    page.set_viewport_size({"width": 1280, "height": 800})  # Use a fixed browser layout for repeatable geometry.
    native_portal.guard_browser_page(page)  # Refuse every browser request outside the private portal.
    short_result = native_portal.run_scenario(page, "short")  # Invoke the safe registered operation once.
    short_snapshot = native_portal.capture_dom_snapshot(page, "short")  # Bind the short run and visible DOM.
    assert short_result["csv_write_open_count"] == 1  # The real exporter must write exactly one control file.
    assert short_result["csv_record_count"] == 1  # The short control must retain its one complete record.
    assert short_result["sdk_request_count"] == 1  # The short control must use one real SDK data page.
    assert short_result["sdk_refused_requests"] == [
        {"method": "GET", "host": "api.mist.com", "path": "/api/v1/self/usage"}
    ]  # The SDK usage probe must be refused before it can reach Mist.
    assert short_snapshot["first_vrf_cell"]["text_length"] == 6  # The complete short value must remain visible.
    assert short_snapshot["first_vrf_cell"]["clipped"] is False  # A complete short value must not be marked clipped.
    assert short_snapshot["notice"]["visible"] is False  # A complete short value must not show a clipping notice.
    long_result = native_portal.run_scenario(page, "long")  # Invoke the same registered operation with 30 records.
    long_snapshot = native_portal.capture_dom_snapshot(page, "long")  # Capture the run and current DOM atomically.
    assert long_result["csv_write_open_count"] == 2  # Both native runs must make one real CSV write.
    assert long_result["csv_record_count"] == 30  # The exporter must preserve all synthetic records.
    assert str(long_result["menu_number"]) == "55"  # Verify the portal ran the registered menu operation.
    assert long_result["sdk_request_count"] == 3  # The real SDK must request all three controlled pages.
    assert [request["returned_records"] for request in long_result["sdk_requests"]] == [
        10,
        10,
        10,
    ]  # Preserve all rows.
    assert len(native_portal.blocked_browser_requests) == 0  # Every browser request must stay on loopback.
    assert len(native_portal.socket_refusals) == 0  # No socket attempt may reach an external endpoint.
    assert native_portal.browser_errors == []  # Fail on every browser console or page error.
    assert native_portal.response_failures == []  # Fail if response matching, completion, or parsing failed.
    assert (
        long_result["sdk_refused_requests"] == []
    )  # The SDK reuses the one-time refused usage probe from the control.
    assert long_result["preview"]["total_rows"] == 30  # The actual preview must report the full file total.
    assert long_snapshot["association"]["run_id"] == long_result["run_id"]  # Bind the DOM to this completed run.
    assert long_snapshot["selected_file"] == "OrgOspfstats.csv"  # Confirm the actual exported file is selected.
    assert long_snapshot["current_page_rows"] == 25  # Confirm the real renderer displays one bounded page.
    assert long_snapshot["summary"] == (
        "Showing 1 to 25 of 30 rows. Select a column heading to sort. " "Select a row to open it."
    )  # Preserve the exact real summary rather than weakening its contract.
    assert long_snapshot["first_vrf_cell"]["text_length"] == 246  # Measure the controlled long value in the cell.
    assert long_snapshot["first_vrf_cell"]["clipped"] is True  # Require actual rendered overflow before disclosure.
    assert long_snapshot["notice"]["visible"] is True  # Fail against the unchanged renderer when notice is absent.
    assert "shortens values" in long_snapshot["notice"]["text"]  # Require a clear explanation of the clipping.
    assert long_snapshot["output_file"]["text"] == "OrgOspfstats.csv"  # Preserve the complete output file link.
    expect(page.get_by_role("button", name="Open details for row 1")).to_be_visible()
    detail_button = page.get_by_role("button", name="Open details for row 1")
    expect(detail_button).to_have_attribute("aria-controls", "result-detail-0")
    expect(detail_button).to_have_attribute("aria-expanded", "false")
    detail_button.click()  # Open the existing row detail accessibly.
    detail = page.get_by_test_id("results-row-detail")  # Read the actual detail row rendered by the application.
    expect(detail).to_be_visible()  # Confirm the notice control uses the existing row detail.
    expect(detail.locator("dd").nth(6)).to_have_text(long_result["csv_records"][0]["vrf_name"])
    expect(detail_button).to_have_attribute("aria-expanded", "true")
    detail_button.click()  # Close the same existing row detail through the accessible control.
    expect(page.get_by_test_id("results-row-detail")).to_have_count(0)
    output_link = page.get_by_role("link", name="Output Files")  # Locate the notice's actual output-panel link.
    expect(output_link).to_have_attribute("href", "#outputFiles")  # Require the link to target the existing panel.
    output_link.click()  # Follow the link to the complete file list.
    expect(page.locator("#outputFiles")).to_be_visible()  # Confirm the complete output panel is available.
    with page.expect_response(native_portal._is_preview_response, timeout=15000):
        page.evaluate("() => OperationResults.nextPage()")  # Request the actual next server page.
    expect(page.locator("#resultsPageInfo")).to_have_text("Page 2 of 2")
    expect(page.locator("#resultsTruncated")).to_be_hidden()  # The long row is not on the second page.
    with page.expect_response(native_portal._is_preview_response, timeout=15000):
        page.evaluate("() => OperationResults.previousPage()")  # Return to the page with the long value.
    expect(page.locator("#resultsPageInfo")).to_have_text("Page 1 of 2")
    expect(page.locator("#resultsTruncated")).to_be_visible()
    with page.expect_response(
        lambda response: native_portal._is_preview_response(response)
        and "sort_column=6" in response.url
        and "sort_dir=asc" in response.url,
        timeout=15000,
    ):
        page.evaluate("() => OperationResults.sortBy(6)")  # Move the long value beyond the first page.
    expect(page.locator("#resultsTruncated")).to_be_hidden()
    with page.expect_response(
        lambda response: native_portal._is_preview_response(response)
        and "sort_column=6" in response.url
        and "sort_dir=desc" in response.url,
        timeout=15000,
    ):
        page.evaluate("() => OperationResults.sortBy(6)")  # Put the long value back on the first page.
    expect(page.locator("#resultsTruncated")).to_be_visible()
    with page.expect_response(
        lambda response: native_portal._is_preview_response(response) and "search=synthetic-vrf-" in response.url,
        timeout=15000,
    ):
        page.locator("#resultsSearch").fill("synthetic-vrf-")  # Filter to the affected native record.
    expect(page.locator("#resultsSummary")).to_contain_text("of 1 rows")
    expect(page.locator("#resultsTruncated")).to_be_visible()
    old_button = page.get_by_role("button", name="Open details for row 1").element_handle()
    page.set_viewport_size({"width": 800, "height": 800})  # Trigger the actual browser resize lifecycle.
    page.wait_for_function("(button) => !button.isConnected", arg=old_button, timeout=5000)
    expect(page.locator("#resultsTruncated")).to_be_visible()
    page.wait_for_function(
        "() => { const cell = document.querySelector('#resultsBody tr[data-row] td:nth-child(7)');"
        " return Boolean(cell && cell.scrollWidth > cell.clientWidth); }",
        timeout=5000,
    )
    print(
        "Issue 3161 native evidence: "
        f"short={short_result['csv_sha256']} notice={short_snapshot['notice']['visible']}; "
        f"long={long_result['csv_sha256']} records={long_result['csv_record_count']} "
        f"pages={long_result['sdk_request_count']} cell={long_snapshot['first_vrf_cell']['text_length']} "
        f"chars/{long_snapshot['first_vrf_cell']['client_width']}px/"
        f"{long_snapshot['first_vrf_cell']['scroll_width']}px notice={long_snapshot['notice']['visible']}."
    )  # Record a compact, source-free summary of the actual native browser measurement.


@pytest.mark.parametrize("status_code", [404, 503])
def test_preview_reader_rejects_http_failure_status(status_code: int, tmp_path: Path) -> None:
    """The private response reader must stop before parsing HTTP failures."""
    portal = NativeResultPortal(tmp_path)  # Construct the reader without starting a server or operation.
    response = MagicMock()  # Model only the completed Playwright response boundary.
    response.status = status_code  # Exercise one client or server error status.
    response.body.return_value = b'{"error":"preview unavailable"}'  # Supply a complete error response body.
    with pytest.raises(RuntimeError, match=f"HTTP {status_code}"):  # Require the expected status error.
        portal._read_preview_response(response)  # Require the actual qualification reader to reject the status.
    response.body.assert_called_once_with()  # Confirm the reader completed the response before status handling.
    response.json.assert_not_called()  # Do not parse an unsuccessful preview response.
    assert portal.response_failures[-1]["stage"] == "preview_status"  # Keep the failure stage explicit.


@pytest.mark.parametrize(("body", "message"), [(b"", "empty body"), (b"{", "bad json")])
def test_preview_reader_reports_empty_and_malformed_json(body: bytes, message: str, tmp_path: Path) -> None:
    """The private response reader must report incomplete or malformed JSON bodies."""
    portal = NativeResultPortal(tmp_path)  # Construct the reader without starting a server or operation.
    response = MagicMock()  # Model only the completed Playwright response boundary.
    response.status = 200  # Keep JSON parsing as the failure source.
    response.body.return_value = body  # Exercise an empty body or invalid JSON bytes.
    response.json.side_effect = json.JSONDecodeError(message, body.decode("utf-8"), 0)  # Model exact parser failure.
    with pytest.raises(json.JSONDecodeError):  # Require the original parser error to reach the caller.
        portal._read_preview_response(response)  # Require the actual qualification reader to propagate parse failure.
    response.body.assert_called_once_with()  # Confirm body completion precedes parsing.
    assert portal.response_failures[-1]["stage"] == "preview_response_parse"  # Keep the parse failure explicit.
