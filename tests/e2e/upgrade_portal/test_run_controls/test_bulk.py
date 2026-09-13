"""Prove authoritative bulk preview behavior in the isolated browser portal."""

from __future__ import annotations

from typing import Any

import pytest

sync_api = pytest.importorskip("playwright.sync_api", reason="The Playwright package is not installed.")

HISTORY_PATH = "/history"
FAILED_RUN_ID = "e2e-failed-run-0001"
STOPPED_RUN_ID = "e2e-stopped-run-0001"
STALE_PRE_CLOUD_RUN_ID = "e2e-stale-precloud-0001"
STALE_STOPPING_RUN_ID = "e2e-stale-stopping-0001"
BULK_RETRY_RUN_ID = "e2e-bulk-retry-run-0001"
BULK_RETRY_SITE_ID = "55555555-5555-5555-5555-555555555555"
SITE_ID = "22222222-2222-2222-2222-222222222222"
SEED_TRIES = 20
SEED_PAUSE_MILLISECONDS = 500


def _open_history(page: Any, run_id: str = FAILED_RUN_ID) -> None:
    """Open history after the process-owned fixture runs are visible."""
    for _attempt in range(SEED_TRIES):
        response = page.goto(HISTORY_PATH)
        assert response is not None and response.ok
        if page.get_by_test_id(f"history-run-select-{run_id}").count() == 1:
            return
        page.wait_for_timeout(SEED_PAUSE_MILLISECONDS)
    pytest.fail("The isolated portal did not show the bulk preview fixture runs.")


def test_bulk_preview_replaces_selection_and_gates_the_exact_phrase(page: Any) -> None:
    """The dialog uses server counts and enables Continue only for the exact phrase."""
    _open_history(page)
    page.get_by_test_id(f"history-run-select-{FAILED_RUN_ID}").check()
    page.get_by_test_id(f"history-run-select-{STOPPED_RUN_ID}").check()
    sync_api.expect(page.get_by_test_id("history-runs-selection-count")).to_have_text("2 runs selected")

    page.get_by_test_id("history-runs-retry").click()
    dialog = page.get_by_test_id("history-runs-preview-dialog")
    sync_api.expect(dialog).to_be_visible()
    sync_api.expect(page.get_by_test_id("history-runs-preview-summary")).to_contain_text("2 run(s) across 1 site(s)")
    sync_api.expect(page.get_by_test_id("history-runs-preview-phrase")).to_have_text("RETRY 2 RUNS")
    confirm = page.get_by_test_id("history-runs-preview-confirm")
    sync_api.expect(confirm).to_be_disabled()
    page.get_by_test_id("history-runs-preview-confirmation").fill("retry 2 runs")
    sync_api.expect(confirm).to_be_disabled()
    page.get_by_test_id("history-runs-preview-confirmation").fill("RETRY 2 RUNS")
    sync_api.expect(confirm).to_be_enabled()


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
    _open_history(page)
    page.get_by_test_id(f"history-run-select-{FAILED_RUN_ID}").check()
    page.get_by_test_id("history-runs-cancel").click()
    sync_api.expect(page.get_by_test_id("history-runs-preview-dialog")).to_be_visible()

    page.get_by_test_id("history-runs-preview-close").click()

    sync_api.expect(page.get_by_test_id("history-runs-preview-dialog")).to_be_hidden()
    sync_api.expect(page.get_by_test_id(f"history-run-select-{FAILED_RUN_ID}")).to_be_enabled()


def test_bulk_cancel_shows_the_durable_atomic_result(page: Any, site_lock: Any) -> None:
    """Bulk cancel changes one stale pre-cloud run and shows its durable result."""
    _open_history(page)
    site_lock(SITE_ID)  # The fixture releases this lock, so the next test finds the site free.
    page.get_by_test_id(f"history-run-select-{STALE_PRE_CLOUD_RUN_ID}").check()
    page.get_by_test_id("history-runs-cancel").click()
    page.get_by_test_id("history-runs-preview-confirmation").fill("CANCEL 1 RUNS")
    page.get_by_test_id("history-runs-preview-confirm").click()

    result = page.get_by_test_id("history-runs-action-result")
    sync_api.expect(result).to_be_visible()
    sync_api.expect(result).to_contain_text("Succeeded: 1")


def test_bulk_retry_links_the_new_run_to_a_fresh_precheck(page: Any, site_lock: Any) -> None:
    """Bulk retry creates one run and links directly to its fresh pre-check."""
    _open_history(page, BULK_RETRY_RUN_ID)
    site_lock(BULK_RETRY_SITE_ID)  # The fixture releases this lock, so the next test finds the site free.
    page.get_by_test_id(f"history-run-select-{BULK_RETRY_RUN_ID}").check()
    page.get_by_test_id("history-runs-retry").click()
    page.get_by_test_id("history-runs-preview-confirmation").fill("RETRY 1 RUNS")
    page.get_by_test_id("history-runs-preview-confirm").click()

    result = page.get_by_test_id("bulk-result-panel")
    sync_api.expect(result).to_be_visible()
    sync_api.expect(result).to_contain_text("Succeeded: 1")
    link = page.get_by_test_id(f"bulk-result-open-{BULK_RETRY_RUN_ID}")
    sync_api.expect(link).to_have_text("Start fresh pre-check")
    link.click()
    page.wait_for_url(f"**/captures/new?site_id={BULK_RETRY_SITE_ID}&run_id=*&role=pre")
    sync_api.expect(page.get_by_test_id("capture-start-button")).to_be_visible()


def test_stale_stopping_run_reconciles_from_read_only_evidence(page: Any, site_lock: Any) -> None:
    """The run page changes stopping only to stopped after complete evidence."""
    _open_history(page)
    site_lock(SITE_ID)  # The fixture releases this lock, so the next test finds the site free.
    response = page.goto(f"/runs/{STALE_STOPPING_RUN_ID}")
    assert response is not None and response.ok
    sync_api.expect(page.get_by_test_id("run-reconciliation-controls")).to_be_visible()
    page.get_by_test_id("run-reconciliation-confirmation").fill(f"RECONCILE {STALE_STOPPING_RUN_ID}")
    page.get_by_test_id("run-reconciliation-submit").click()

    result = page.get_by_test_id("run-reconciliation-result")
    sync_api.expect(result).to_be_visible()
    sync_api.expect(result).to_contain_text("Succeeded: 1")
    page.reload()
    sync_api.expect(page.get_by_test_id("upgrade-state")).to_have_text("stopped")
