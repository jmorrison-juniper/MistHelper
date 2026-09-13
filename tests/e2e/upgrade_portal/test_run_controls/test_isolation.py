"""Prove the run-control browser lifecycle and hard E2E isolation."""

from __future__ import annotations

import json
from typing import Any

import pytest

sync_api = pytest.importorskip("playwright.sync_api", reason="The Playwright package is not installed.")

HISTORY_PATH = "/history"
RUN_ID = "e2e-lifecycle-run-0001"
SITE_ID = "66666666-6666-6666-6666-666666666666"
SEED_TRIES = 20
SEED_PAUSE_MILLISECONDS = 500
VIEWPORT_WIDTHS = (360, 768, 1280)
TRAP_HEADERS = (
    "x-misthelper-e2e-arango-trap-calls",
    "x-misthelper-e2e-redis-trap-calls",
    "x-misthelper-e2e-mist-trap-calls",
    "x-misthelper-e2e-file-trap-calls",
)


def _open_history(page: Any) -> None:
    """Open history after the process-owned lifecycle run is visible."""
    for _attempt in range(SEED_TRIES):
        response = page.goto(HISTORY_PATH)
        assert response is not None and response.ok
        if page.get_by_test_id(f"history-run-select-{RUN_ID}").count() == 1:
            return
        page.wait_for_timeout(SEED_PAUSE_MILLISECONDS)
    pytest.fail("The isolated portal did not show the lifecycle fixture run.")


def test_each_isolated_response_has_owner_and_zero_hard_trap_counts(page: Any, e2e_test_run_id: str) -> None:
    """Each isolated response names its owner and reports zero external calls."""
    response = page.goto("/healthz")
    assert response is not None and response.ok
    assert response.headers["x-misthelper-e2e-run-id"] == e2e_test_run_id
    for header in TRAP_HEADERS:
        assert response.headers[header] == "0"
    assert response.headers["x-misthelper-e2e-persistent-runs"] == "0"
    assert response.headers["x-misthelper-e2e-persistent-actions"] == "0"
    assert response.headers["x-misthelper-e2e-persistent-audits"] == "0"


def test_reload_back_forward_and_two_tabs_restore_only_local_candidates(page: Any) -> None:
    """Reload and history navigation restore one tab without changing another tab."""
    _open_history(page)
    selected = page.get_by_test_id(f"history-run-select-{RUN_ID}")
    selected.check()
    page.goto("/select/site")
    page.go_back()
    sync_api.expect(selected).to_be_checked()
    page.go_forward()
    page.go_back()
    sync_api.expect(selected).to_be_checked()
    page.reload()
    sync_api.expect(selected).to_be_checked()
    page.get_by_test_id("history-runs-clear").click()
    sync_api.expect(selected).not_to_be_checked()
    page.reload()
    sync_api.expect(selected).not_to_be_checked()
    selected.check()

    other_tab = page.context.new_page()
    try:
        _open_history(other_tab)
        sync_api.expect(other_tab.get_by_test_id(f"history-run-select-{RUN_ID}")).not_to_be_checked()
        sync_api.expect(other_tab.get_by_test_id("history-runs-selection-count")).to_have_text("0 runs selected")
    finally:
        other_tab.close()


def test_keyboard_dialog_focus_alert_and_required_viewports(page: Any, e2e_test_run_id: str) -> None:
    """Keyboard controls and the dialog remain usable at all required widths."""
    for width in VIEWPORT_WIDTHS:
        page.set_viewport_size({"width": width, "height": 900})
        _open_history(page)
        checkbox = page.get_by_test_id(f"history-run-select-{RUN_ID}")
        checkbox_box = checkbox.bounding_box()
        assert checkbox_box is not None
        assert checkbox_box["x"] >= 0
        assert checkbox_box["x"] + checkbox_box["width"] <= width
        checkbox.focus()
        page.keyboard.press("Space")
        sync_api.expect(checkbox).to_be_checked()
        opener = page.get_by_test_id("history-runs-cancel")
        opener.focus()
        page.keyboard.press("Enter")
        dialog = page.get_by_test_id("history-runs-preview-dialog")
        sync_api.expect(dialog).to_be_visible()
        sync_api.expect(page.get_by_test_id("history-runs-preview-title")).to_be_focused()
        box = dialog.bounding_box()
        assert box is not None
        assert box["x"] >= 0
        assert box["x"] + box["width"] <= width
        phrase_input = page.get_by_test_id("history-runs-preview-confirmation")
        phrase_box = phrase_input.bounding_box()
        assert phrase_box is not None
        assert phrase_box["x"] + phrase_box["width"] <= width
        page.keyboard.press("Escape")
        sync_api.expect(dialog).to_be_hidden()
        sync_api.expect(opener).to_be_focused()
        checkbox.uncheck()

    _open_history(page)
    page.get_by_test_id(f"history-run-select-{RUN_ID}").check()
    page.route(
        "**/api/runs/bulk-actions/preview",
        lambda route: route.fulfill(
            status=503,
            headers={
                "Content-Type": "application/json",
                "X-MistHelper-E2E-Run-ID": e2e_test_run_id,
                "X-MistHelper-E2E-Arango-Trap-Calls": "0",
                "X-MistHelper-E2E-Redis-Trap-Calls": "0",
                "X-MistHelper-E2E-Mist-Trap-Calls": "0",
                "X-MistHelper-E2E-File-Trap-Calls": "0",
            },
            body=json.dumps({"error": {"code": "preview_unavailable", "message": "Preview unavailable."}}),
        ),
        times=1,
    )
    page.get_by_test_id("history-runs-cancel").click()
    error = page.get_by_test_id("history-runs-preview-error")
    sync_api.expect(error).to_be_visible()
    assert error.get_attribute("role") == "alert"


def test_response_loss_recovers_by_read_and_preserves_actor_scope(
    page: Any,
    second_operator_page: Any,
    renewed_operator_cookie_records: list[dict[str, str]],
    e2e_test_run_id: str,
    site_lock: Any,
) -> None:
    """A lost action response recovers by read for the same actor and hides from another actor."""
    page.set_viewport_size({"width": 360, "height": 900})
    _open_history(page)
    site_lock(SITE_ID)  # The fixture releases this lock, so the next test finds the site free.
    captured: dict[str, Any] = {}

    def lose_response(route: Any) -> None:
        response = route.fetch()
        captured.update(json.loads(response.body()))
        route.abort("connectionreset")

    page.route("**/api/runs/bulk-actions", lose_response, times=1)
    page.get_by_test_id(f"history-run-select-{RUN_ID}").check()
    page.get_by_test_id("history-runs-cancel").click()
    page.get_by_test_id("history-runs-preview-confirmation").fill("CANCEL 1 RUNS")
    page.get_by_test_id("history-runs-preview-confirm").click()

    refresh = page.get_by_test_id("bulk-result-refresh")
    sync_api.expect(refresh).to_be_visible()
    assert page.get_by_test_id("bulk-result-panel").count() == 0
    refresh.click()
    result = page.get_by_test_id("bulk-result-panel")
    sync_api.expect(result).to_be_visible()
    sync_api.expect(result).to_contain_text("Succeeded: 1")
    sync_api.expect(result.locator("h3")).to_be_focused()
    result_box = result.bounding_box()
    assert result_box is not None
    assert result_box["x"] + result_box["width"] <= 360

    action_id = str(captured["action_id"])
    await_header = {"Accept": "application/json"}
    page.context.clear_cookies()
    page.context.add_cookies(renewed_operator_cookie_records)
    renewed = page.request.get(f"/api/run-actions/{action_id}", headers=await_header)
    assert renewed.status == 200
    assert renewed.json()["action_id"] == action_id
    assert renewed.headers["x-misthelper-e2e-run-id"] == e2e_test_run_id
    for header in TRAP_HEADERS:
        assert renewed.headers[header] == "0"

    hidden = second_operator_page.request.get(f"/api/run-actions/{action_id}", headers=await_header)
    assert hidden.status == 404
    assert hidden.json()["error"]["code"] == "action_not_found"
    assert hidden.headers["x-misthelper-e2e-run-id"] == e2e_test_run_id
