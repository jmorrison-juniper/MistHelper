"""Prove authoritative bulk preview behavior in the isolated browser portal.

Why:
    Issue #3507. The two stale seed runs sit on the stale site, which the picker
    does not list. The bulk cancel test and the reconcile test take the lock of
    that site, so no create journey on the first site meets either seed run.

    Each bulk test also checks one value with a plain assertion. The test
    quality gate counts a plain assertion only, and each value proves one
    claim of its test.
"""

from __future__ import annotations  # Keep the annotations independent from the import order.

import logging  # Record the plan and the result of each bulk journey.
from typing import Any  # Playwright gives each page and each answer, so their type is Any.
from urllib.parse import parse_qs, urlsplit  # Read the new run key from the address of the pre-check page.

import pytest  # The skip of a missing Playwright package and the failure of a missing seed.

from tests.e2e.upgrade_portal.stale_run_seeds import (  # Issue #3507: one copy of each stale key.
    STALE_PRE_CLOUD_RUN_ID,
    STALE_SITE_ID,
    STALE_STOPPING_RUN_ID,
)

sync_api = pytest.importorskip("playwright.sync_api", reason="The Playwright package is not installed.")

logger = logging.getLogger(__name__)  # Keep the records of this module under one name.

HISTORY_PATH = "/history"  # The page that lists each run and holds the bulk controls.
BULK_PREVIEW_PATH = "/api/runs/bulk-actions/preview"  # The route that counts the selection for the dialog.
CANCELLED_STATE = "cancelled"  # The state that the history page shows after a cancel.
FAILED_RUN_ID = "e2e-failed-run-0001"  # A seed run in the state failed.
STOPPED_RUN_ID = "e2e-stopped-run-0001"  # A seed run in the state stopped, on the same site.
BULK_RETRY_RUN_ID = "e2e-bulk-retry-run-0001"  # The seed run that the bulk retry test retries.
BULK_RETRY_SITE_ID = "55555555-5555-5555-5555-555555555555"  # The site of that seed run.
SEED_TRIES = 20  # The number of reads before the seed runs must show.
SEED_PAUSE_MILLISECONDS = 500  # The pause between two reads of the history page.


def _open_history(page: Any, run_id: str = FAILED_RUN_ID) -> None:
    """Open history after the process-owned fixture runs are visible."""
    for _attempt in range(SEED_TRIES):
        response = page.goto(HISTORY_PATH)
        assert response is not None and response.ok
        if page.get_by_test_id(f"history-run-select-{run_id}").count() == 1:
            return
        page.wait_for_timeout(SEED_PAUSE_MILLISECONDS)
    pytest.fail("The isolated portal did not show the bulk preview fixture runs.")


def _open_the_preview(page: Any, control_id: str) -> dict[str, Any]:
    """Press one bulk control, and return the preview answer of the server.

    Args:
        page: The browser page that shows the history list.
        control_id: The test identifier of the bulk control to press.

    Returns:
        The preview answer, which holds the run keys, the counts, and the phrase.
    """
    logger.info("Press %s, and read the preview answer of the server", control_id)  # Log before the press.
    with page.expect_response(f"**{BULK_PREVIEW_PATH}") as preview_event:  # The dialog reads its counts from it.
        page.get_by_test_id(control_id).click()  # The press posts the selection to the preview route.
    preview: dict[str, Any] = preview_event.value.json()  # The preview, as the server built it.
    counts = (preview.get("run_count"), preview.get("site_count"))  # The two counts that the dialog shows.
    logger.debug("The preview holds %s run(s) on %s site(s)", *counts)  # Log after the read.
    return preview  # The caller compares the answer with the dialog.


def test_bulk_preview_replaces_selection_and_gates_the_exact_phrase(page: Any) -> None:
    """The dialog uses server counts and enables Continue only for the exact phrase."""
    logger.info("Preview a retry of two runs, and type the phrase")  # Log the plan.
    _open_history(page)  # Wait until the seed runs show on the history page.
    page.get_by_test_id(f"history-run-select-{FAILED_RUN_ID}").check()  # Select the failed seed run.
    page.get_by_test_id(f"history-run-select-{STOPPED_RUN_ID}").check()  # Select the stopped seed run.
    selection_count = page.get_by_test_id("history-runs-selection-count")  # The count of the browser selection.
    sync_api.expect(selection_count).to_have_text("2 runs selected")  # Both boxes count.

    preview = _open_the_preview(page, "history-runs-retry")  # The server previews a retry of both runs.
    assert sorted(preview["run_ids"]) == sorted([FAILED_RUN_ID, STOPPED_RUN_ID]), "The server changed the selection."
    assert (preview["run_count"], preview["site_count"]) == (2, 1), "The server counted the wrong selection."
    dialog = page.get_by_test_id("history-runs-preview-dialog")  # The native dialog of the preview.
    sync_api.expect(dialog).to_be_visible()  # The answer opens the dialog.
    summary = page.get_by_test_id("history-runs-preview-summary")  # The counts that the dialog shows.
    sync_api.expect(summary).to_contain_text("2 run(s) across 1 site(s)")  # The same counts as the server.
    sync_api.expect(page.get_by_test_id("history-runs-preview-phrase")).to_have_text("RETRY 2 RUNS")  # The phrase.
    confirm = page.get_by_test_id("history-runs-preview-confirm")  # The Continue control.
    sync_api.expect(confirm).to_be_disabled()  # No phrase yet, so Continue stays off.
    phrase = page.get_by_test_id("history-runs-preview-confirmation")  # The field for the typed phrase.
    phrase.fill("retry 2 runs")  # The phrase in the wrong case.
    sync_api.expect(confirm).to_be_disabled()  # A near match does not turn Continue on.
    phrase.fill("RETRY 2 RUNS")  # The exact phrase.
    sync_api.expect(confirm).to_be_enabled()  # Only the exact phrase turns Continue on.


def test_bulk_selection_survives_reload_but_requires_a_new_preview(page: Any) -> None:
    """A restored visual selection cannot bypass the authoritative preview step."""
    _open_history(page)
    page.get_by_test_id(f"history-run-select-{FAILED_RUN_ID}").check()
    page.reload()

    sync_api.expect(page.get_by_test_id(f"history-run-select-{FAILED_RUN_ID}")).to_be_checked()
    sync_api.expect(page.get_by_test_id("history-runs-selection-count")).to_have_text("1 run selected")
    assert page.get_by_test_id("history-runs-preview-dialog").is_hidden()
    page.get_by_test_id("history-runs-cancel").click()
    sync_api.expect(page.get_by_test_id("history-runs-preview-phrase")).to_have_text("CANCEL 1 RUNS")


def test_bulk_preview_close_returns_focusable_history_controls(page: Any) -> None:
    """The operator can close the native dialog and change the selection."""
    logger.info("Open a cancel preview, close it, and clear the selection")  # Log the plan.
    _open_history(page)  # Wait until the seed runs show on the history page.
    selection = page.get_by_test_id(f"history-run-select-{FAILED_RUN_ID}")  # The box of the failed seed run.
    selection.check()  # Select the one run.
    page.get_by_test_id("history-runs-cancel").click()  # The press opens the cancel preview.
    dialog = page.get_by_test_id("history-runs-preview-dialog")  # The native dialog of the preview.
    sync_api.expect(dialog).to_be_visible()  # The preview opens the dialog.

    page.get_by_test_id("history-runs-preview-close").click()  # The operator closes the dialog.

    sync_api.expect(dialog).to_be_hidden()  # The close hides the dialog.
    sync_api.expect(selection).to_be_enabled()  # The box accepts a change again.
    selection.uncheck()  # The operator changes the selection after the close.
    assert selection.is_checked() is False, f"{FAILED_RUN_ID} stayed selected after the operator cleared it."
    logger.debug("The operator cleared the selection after the close")  # Log the result.


def test_bulk_cancel_shows_the_durable_atomic_result(page: Any, site_lock: Any) -> None:
    """Bulk cancel changes one stale pre-cloud run and shows its durable result."""
    logger.info("Cancel the stale pre-cloud run through the bulk controls")  # Log the plan.
    _open_history(page)  # Wait until the seed runs show on the history page.
    site_lock.take(STALE_SITE_ID)  # Issue #3507: the stale run holds the stale site, and the fixture frees it.
    page.get_by_test_id(f"history-run-select-{STALE_PRE_CLOUD_RUN_ID}").check()  # Select the stale run.
    page.get_by_test_id("history-runs-cancel").click()  # The press opens the cancel preview.
    page.get_by_test_id("history-runs-preview-confirmation").fill("CANCEL 1 RUNS")  # The exact phrase.
    page.get_by_test_id("history-runs-preview-confirm").click()  # Continue sends the cancel.

    result = page.get_by_test_id("history-runs-action-result")  # The result region of the bulk action.
    sync_api.expect(result).to_be_visible()  # The action reports a result.
    sync_api.expect(result).to_contain_text("Succeeded: 1")  # The one run changed.
    page.reload()  # A fresh read of the history page shows the stored state.
    shown = page.get_by_test_id(f"history-run-state-{STALE_PRE_CLOUD_RUN_ID}").inner_text().strip()  # The state.
    assert shown == CANCELLED_STATE, f"{STALE_PRE_CLOUD_RUN_ID} reads {shown!r} after a reload."
    logger.debug("The stale run reads %s after a reload", shown)  # Log the result.


def test_bulk_retry_links_the_new_run_to_a_fresh_precheck(page: Any, site_lock: Any) -> None:
    """Bulk retry creates one run and links directly to its fresh pre-check."""
    logger.info("Retry the seed run through the bulk controls, and open the new pre-check")  # Log the plan.
    _open_history(page, BULK_RETRY_RUN_ID)  # Wait until the retry seed run shows on the history page.
    site_lock.take(BULK_RETRY_SITE_ID)  # The fixture releases this lock, so the next test finds the site free.
    page.get_by_test_id(f"history-run-select-{BULK_RETRY_RUN_ID}").check()  # Select the retry seed run.
    page.get_by_test_id("history-runs-retry").click()  # The press opens the retry preview.
    page.get_by_test_id("history-runs-preview-confirmation").fill("RETRY 1 RUNS")  # The exact phrase.
    page.get_by_test_id("history-runs-preview-confirm").click()  # Continue sends the retry.

    result = page.get_by_test_id("bulk-result-panel")  # The result region of the bulk retry.
    sync_api.expect(result).to_be_visible()  # The action reports a result.
    sync_api.expect(result).to_contain_text("Succeeded: 1")  # The one retry succeeded.
    link = page.get_by_test_id(f"bulk-result-open-{BULK_RETRY_RUN_ID}")  # The link to the new pre-check.
    sync_api.expect(link).to_have_text("Start fresh pre-check")  # The link names its purpose.
    link.click()  # The operator follows the link.
    page.wait_for_url(f"**/captures/new?site_id={BULK_RETRY_SITE_ID}&run_id=*&role=pre")  # The pre-check page.
    sync_api.expect(page.get_by_test_id("capture-start-button")).to_be_visible()  # The capture can start.
    new_run_id = parse_qs(urlsplit(page.url).query).get("run_id", [""])[0]  # The run that the pre-check serves.
    assert new_run_id not in ("", BULK_RETRY_RUN_ID), f"The pre-check address {page.url} names no new run."
    logger.debug("The retry built the run %s", new_run_id)  # Log the result.


def test_stale_stopping_run_reconciles_from_read_only_evidence(page: Any, site_lock: Any) -> None:
    """The run page changes stopping only to stopped after complete evidence."""
    logger.info("Reconcile the stale stopping run from the scripted evidence")  # Log the plan.
    _open_history(page)  # Wait until the seed runs show on the history page.
    site_lock.take(STALE_SITE_ID)  # Issue #3507: the stale run holds the stale site, and the fixture frees it.
    response = page.goto(f"/runs/{STALE_STOPPING_RUN_ID}")  # Open the run page of the stale stopping run.
    assert response is not None and response.ok  # The run page opens.
    controls = page.get_by_test_id("run-reconciliation-controls")  # The controls that a stopping run shows.
    sync_api.expect(controls).to_be_visible()  # The stale stopping run offers the reconcile.
    page.get_by_test_id("run-reconciliation-confirmation").fill(f"RECONCILE {STALE_STOPPING_RUN_ID}")  # The phrase.
    page.get_by_test_id("run-reconciliation-submit").click()  # The press sends the reconcile.

    result = page.get_by_test_id("run-reconciliation-result")  # The result region of the reconcile.
    sync_api.expect(result).to_be_visible()  # The reconcile reports a result.
    sync_api.expect(result).to_contain_text("Succeeded: 1")  # The one run changed.
    page.reload()  # A fresh read of the run page shows the stored state.
    sync_api.expect(page.get_by_test_id("upgrade-state")).to_have_text("stopped")  # The run now reads stopped.
    logger.debug("The stale stopping run reads stopped after a reload")  # Log the result.
