"""Browser journey for the operation state after a cancel that stopped part of the work.

Why:
    Issue #3371. After a cancel, an operation with one completed access point
    job and one cancelled switch job read completed. The status card stated
    that the operation was final with the word completed, and the history list
    showed the same success word. This journey cancels a seeded operation of
    that shape. The status card, the final note, and the history badge must
    read cancelled. A reload must show the same state.

    The server seeds the operation for the controls operator. See
    `org_ended_seeds.py`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from tests.e2e.upgrade_portal.org_ended_seeds import MIXED_CHILD_IDS, MIXED_OPERATION_ID

sync_api = pytest.importorskip("playwright.sync_api", reason="Playwright is not installed.")

JOB_PATH = f"/upgrade/org/jobs/{MIXED_OPERATION_ID}"  # The progress page of the seeded operation.
HISTORY_PATH = "/history"  # The history list of the portal.
SEED_TRIES = 20  # The server writes the seeds on a thread, so the first read can come too early.
SEED_PAUSE_MS = 500  # The pause between two reads of the seeded page.
STATUS_FIELD = "[data-org-upgrade-field='status']"  # The state word of the status card.
FINAL_NOTE = "The operation is final: cancelled. The portal sends no cancel request for it."  # The closed note.
AP_ID = MIXED_CHILD_IDS["ap"]  # The access point job, which completed before the cancel.
SWITCH_ID = MIXED_CHILD_IDS["switch"]  # The switch job, which the cancel stops.


def open_seeded_page(page: Any) -> None:
    """Open the progress page of the seeded operation, and wait until the seed exists.

    Args:
        page: The browser page of the controls operator.
    """
    for _ in range(SEED_TRIES):  # The seed thread can finish after the first test starts.
        page.goto(JOB_PATH, wait_until="domcontentloaded")
        if page.get_by_test_id("org-upgrade-progress").count() == 1:  # The seed exists.
            return
        page.wait_for_timeout(SEED_PAUSE_MS)
    sync_api.expect(page.get_by_test_id("org-upgrade-progress")).to_be_visible()  # Report the missing seed.


def check_cancelled_state(page: Any) -> None:
    """Check the status card and the final note of the operation.

    Args:
        page: The browser page after the cancel.
    """
    sync_api.expect(page.locator(STATUS_FIELD)).to_have_text("cancelled")  # Not the success word.
    closed = page.get_by_test_id("org-upgrade-cancel-closed")  # The note that replaces the cancel form.
    sync_api.expect(closed).to_be_visible()
    sync_api.expect(closed).to_have_text(FINAL_NOTE)
    sync_api.expect(page.get_by_test_id(f"org-cancel-outcome-status-{AP_ID}")).to_have_text("already_ended")
    sync_api.expect(page.get_by_test_id(f"org-cancel-outcome-status-{SWITCH_ID}")).to_have_text("requested")


class TestMixedCancelState:
    """Cancel an operation whose access point job completed first, and read the operation state."""

    def test_the_operation_reads_cancelled_after_a_cancel_that_stopped_part_of_the_work(
        self, controls_operator_page: Any, tmp_path: Path
    ) -> None:
        """The status card, the final note, and the history badge read cancelled, also after a reload."""
        page = controls_operator_page  # The operator that owns the seeded operation.
        open_seeded_page(page)
        sync_api.expect(page.locator(STATUS_FIELD)).to_have_text("running")  # The switch job still runs.
        page.screenshot(path=str(tmp_path / "mixed-before.png"), full_page=True)
        page.get_by_test_id("org-upgrade-cancel-confirmation").fill("CANCEL")
        sync_api.expect(page.get_by_test_id("org-upgrade-cancel")).to_be_enabled()
        page.get_by_test_id("org-upgrade-cancel").click()
        sync_api.expect(page.get_by_test_id("org-cancel-outcome")).to_be_visible()  # The redirect shows the panel.
        check_cancelled_state(page)
        page.screenshot(path=str(tmp_path / "mixed-after.png"), full_page=True)
        page.reload(wait_until="domcontentloaded")
        check_cancelled_state(page)
        page.screenshot(path=str(tmp_path / "mixed-reload.png"), full_page=True)
        page.goto(HISTORY_PATH, wait_until="domcontentloaded")
        badge = page.get_by_test_id(f"history-operation-state-{MIXED_OPERATION_ID}")  # The history row badge.
        sync_api.expect(badge).to_have_text("cancelled")
        page.screenshot(path=str(tmp_path / "mixed-history.png"), full_page=True)
        assert badge.inner_text().strip() == "cancelled"  # The history list shows no success word.
