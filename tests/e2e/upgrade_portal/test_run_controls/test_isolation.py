"""Prove the run-control browser lifecycle and the owner check of the isolated test portal.

Why:
    Issue #3501. The test portal holds its runs, its captures, its actions,
    and its locks in the stores of the test process. The child environment
    points ArangoDB and Redis at port 1 of the loopback address. The stand-in
    cloud sessions hold no request method. The trail guard of issue #3498
    counts the checkout audit trail. Each response names the run that owns
    the portal, and it carries no other test header.
"""

from __future__ import annotations  # Keep annotations independent from import order.

import json  # Read and write the JSON bodies of the stubbed and the lost responses.
from typing import Any  # Playwright objects have no public type in this suite.

import pytest  # Fail a test with a clear message, and skip when Playwright is absent.

from tests.support.upgrade_portal_e2e import RunOwnerHeaderCheck  # Issue #3501: list the test headers.

sync_api = pytest.importorskip("playwright.sync_api", reason="The Playwright package is not installed.")

HISTORY_PATH = "/history"  # The page that lists the lifecycle fixture run.
RUN_ID = "e2e-lifecycle-run-0001"  # The run that the test portal seeds for these journeys.
SITE_ID = "66666666-6666-6666-6666-666666666666"  # The site of the lifecycle fixture run.
SEED_TRIES = 20  # The number of history reads before the test gives up on the seed.
SEED_PAUSE_MILLISECONDS = 500  # The pause between two history reads.
VIEWPORT_WIDTHS = (360, 768, 1280)  # A phone, a tablet, and a desktop width.
OWNER_HEADER_ONLY = ("x-misthelper-e2e-run-id",)  # Issue #3501: the one test header of each response.


def _open_history(page: Any) -> None:
    """Open history after the process-owned lifecycle run is visible."""
    for _attempt in range(SEED_TRIES):  # The seed can land after the first read.
        response = page.goto(HISTORY_PATH)  # Read the history page again.
        assert response is not None and response.ok  # A failed read means that no portal answered.
        if page.get_by_test_id(f"history-run-select-{RUN_ID}").count() == 1:  # The seed is visible.
            return  # The caller can now select the run.
        page.wait_for_timeout(SEED_PAUSE_MILLISECONDS)  # Give the seed time to land.
    pytest.fail("The isolated portal did not show the lifecycle fixture run.")  # Name the missing seed.


def _bounds(locator: Any) -> dict[str, float]:
    """Return the box of one element, or fail the test when the page does not show the element."""
    box = locator.bounding_box()  # Playwright gives None for an element that the page does not show.
    if box is None:  # A hidden element cannot prove a layout rule.
        pytest.fail("The element has no box, so the page did not show it.")  # Name the cause.
    return box  # The caller compares the edges with the viewport width.


def test_each_isolated_response_names_its_owner_and_no_other_test_header(page: Any, e2e_test_run_id: str) -> None:
    """Each isolated response names its owner and carries no other test header."""
    response = page.goto("/healthz")  # A route that needs no session.
    assert response is not None and response.ok  # A failed read means that no portal answered.
    assert response.headers["x-misthelper-e2e-run-id"] == e2e_test_run_id  # The portal of this run answered.
    assert RunOwnerHeaderCheck.e2e_header_names(response.headers) == OWNER_HEADER_ONLY  # No fixed counter.


def test_reload_back_forward_and_two_tabs_restore_only_local_candidates(page: Any) -> None:
    """Reload and history navigation restore one tab without changing another tab."""
    _open_history(page)  # Wait for the lifecycle fixture run.
    selected = page.get_by_test_id(f"history-run-select-{RUN_ID}")  # The check box of the fixture run.
    selected.check()  # Select the run in this tab.
    page.goto("/select/site")  # Leave the history page.
    page.go_back()  # Return through the browser history.
    sync_api.expect(selected).to_be_checked()  # The tab restores its selection.
    page.go_forward()  # Leave the history page again.
    page.go_back()  # Return again.
    sync_api.expect(selected).to_be_checked()  # The tab restores its selection again.
    page.reload()  # Reload the history page.
    sync_api.expect(selected).to_be_checked()  # A reload keeps the selection.
    page.get_by_test_id("history-runs-clear").click()  # Clear the selection.
    sync_api.expect(selected).not_to_be_checked()  # The clear removes the selection.
    page.reload()  # Reload after the clear.
    sync_api.expect(selected).not_to_be_checked()  # The clear lasts across a reload.
    selected.check()  # Select the run again before the second tab opens.

    other_tab = page.context.new_page()  # A second tab of the same browser.
    try:  # Close the second tab also when an expectation fails.
        _open_history(other_tab)  # Wait for the fixture run in the second tab.
        sync_api.expect(other_tab.get_by_test_id(f"history-run-select-{RUN_ID}")).not_to_be_checked()  # No share.
        sync_api.expect(other_tab.get_by_test_id("history-runs-selection-count")).to_have_text("0 runs selected")
    finally:  # A tab left open would hold a browser target for the whole run.
        other_tab.close()  # Close the second tab.
    assert selected.is_checked()  # The second tab left the selection of the first tab in place.


def test_keyboard_dialog_focus_alert_and_required_viewports(page: Any, e2e_test_run_id: str) -> None:
    """Keyboard controls and the dialog remain usable at all required widths."""
    for width in VIEWPORT_WIDTHS:  # Each width that an operator can use.
        page.set_viewport_size({"width": width, "height": 900})  # Set the width of this pass.
        _open_history(page)  # Wait for the lifecycle fixture run.
        checkbox = page.get_by_test_id(f"history-run-select-{RUN_ID}")  # The check box of the fixture run.
        checkbox_box = _bounds(checkbox)  # The page must show the check box.
        assert checkbox_box["x"] >= 0  # The check box starts inside the viewport.
        assert checkbox_box["x"] + checkbox_box["width"] <= width  # The check box ends inside the viewport.
        checkbox.focus()  # Move the keyboard focus to the check box.
        page.keyboard.press("Space")  # Select the run with the keyboard.
        sync_api.expect(checkbox).to_be_checked()  # The keyboard selects the run.
        opener = page.get_by_test_id("history-runs-cancel")  # The button that opens the preview dialog.
        opener.focus()  # Move the keyboard focus to the button.
        page.keyboard.press("Enter")  # Open the dialog with the keyboard.
        dialog = page.get_by_test_id("history-runs-preview-dialog")  # The preview dialog.
        sync_api.expect(dialog).to_be_visible()  # The dialog opens.
        sync_api.expect(page.get_by_test_id("history-runs-preview-title")).to_be_focused()  # The title takes focus.
        box = _bounds(dialog)  # The page must show the dialog.
        assert box["x"] >= 0  # The dialog starts inside the viewport.
        assert box["x"] + box["width"] <= width  # The dialog ends inside the viewport.
        phrase_input = page.get_by_test_id("history-runs-preview-confirmation")  # The confirmation phrase field.
        phrase_box = _bounds(phrase_input)  # The page must show the field.
        assert phrase_box["x"] + phrase_box["width"] <= width  # The field ends inside the viewport.
        page.keyboard.press("Escape")  # Close the dialog with the keyboard.
        sync_api.expect(dialog).to_be_hidden()  # The dialog closes.
        sync_api.expect(opener).to_be_focused()  # The focus returns to the button.
        checkbox.uncheck()  # Clear the selection before the next width.

    _open_history(page)  # Open the history page for the refusal pass.
    page.get_by_test_id(f"history-run-select-{RUN_ID}").check()  # Select the run again.
    page.route(  # Answer the next preview request with a refusal.
        "**/api/runs/bulk-actions/preview",
        lambda route: route.fulfill(
            status=503,
            headers={
                "Content-Type": "application/json",
                "X-MistHelper-E2E-Run-ID": e2e_test_run_id,  # Issue #3501: the one test header.
            },
            body=json.dumps({"error": {"code": "preview_unavailable", "message": "Preview unavailable."}}),
        ),
        times=1,
    )
    page.get_by_test_id("history-runs-cancel").click()  # Ask for the preview.
    error = page.get_by_test_id("history-runs-preview-error")  # The alert of the refusal.
    sync_api.expect(error).to_be_visible()  # The page shows the refusal.
    assert error.get_attribute("role") == "alert"  # A screen reader announces the refusal.


def test_response_loss_recovers_by_read_and_preserves_actor_scope(
    page: Any,
    second_operator_page: Any,
    renewed_operator_cookie_records: list[dict[str, str]],
    e2e_test_run_id: str,
    site_lock: Any,
) -> None:
    """A lost action response recovers by read for the same actor and hides from another actor."""
    page.set_viewport_size({"width": 360, "height": 900})  # The narrowest width.
    _open_history(page)  # Wait for the lifecycle fixture run.
    site_lock.take(SITE_ID)  # Issue #3508: the test releases this lock before it drops the first session.
    captured: dict[str, Any] = {}  # The body of the response that the browser loses.

    def lose_response(route: Any) -> None:
        """Read the real answer, then drop the connection so the browser never sees it."""
        response = route.fetch()  # The portal does the action and answers.
        captured.update(json.loads(response.body()))  # Keep the answer for the later read.
        route.abort("connectionreset")  # The browser sees a lost connection.

    page.route("**/api/runs/bulk-actions", lose_response, times=1)  # Lose the next action answer.
    page.get_by_test_id(f"history-run-select-{RUN_ID}").check()  # Select the run.
    page.get_by_test_id("history-runs-cancel").click()  # Ask for the preview.
    page.get_by_test_id("history-runs-preview-confirmation").fill("CANCEL 1 RUNS")  # Type the phrase.
    page.get_by_test_id("history-runs-preview-confirm").click()  # Send the action.

    refresh = page.get_by_test_id("bulk-result-refresh")  # The control that reads the result again.
    sync_api.expect(refresh).to_be_visible()  # The page offers a read after the lost answer.
    assert page.get_by_test_id("bulk-result-panel").count() == 0  # The page shows no result it did not read.
    refresh.click()  # Read the result again.
    result = page.get_by_test_id("bulk-result-panel")  # The panel of the result.
    sync_api.expect(result).to_be_visible()  # The read shows the result.
    sync_api.expect(result).to_contain_text("Succeeded: 1")  # The action succeeded one time.
    sync_api.expect(result.locator("h3")).to_be_focused()  # The heading takes focus.
    result_box = _bounds(result)  # The page must show the panel.
    assert result_box["x"] + result_box["width"] <= 360  # The panel ends inside the viewport.

    action_id = str(captured["action_id"])  # The action that the lost answer named.
    await_header = {"Accept": "application/json"}  # Ask for a JSON answer.
    site_lock.release(SITE_ID)  # Issue #3508: the first session holds the lock record and the token of the page.
    page.context.clear_cookies()  # Drop the first browser session.
    page.context.add_cookies(renewed_operator_cookie_records)  # Sign in again as the same operator.
    renewed = page.request.get(f"/api/run-actions/{action_id}", headers=await_header)  # Read the action again.
    assert renewed.status == 200  # The same operator can read the action.
    assert renewed.json()["action_id"] == action_id  # The read names the same action.
    assert renewed.headers["x-misthelper-e2e-run-id"] == e2e_test_run_id  # The portal of this run answered.
    assert RunOwnerHeaderCheck.e2e_header_names(renewed.headers) == OWNER_HEADER_ONLY  # No fixed counter.

    hidden = second_operator_page.request.get(f"/api/run-actions/{action_id}", headers=await_header)  # Other actor.
    assert hidden.status == 404  # Another operator cannot read the action.
    assert hidden.json()["error"]["code"] == "action_not_found"  # The refusal hides that the action exists.
    assert hidden.headers["x-misthelper-e2e-run-id"] == e2e_test_run_id  # The portal of this run answered.
