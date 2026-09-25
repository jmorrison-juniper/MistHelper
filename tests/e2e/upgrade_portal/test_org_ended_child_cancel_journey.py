"""Browser journey for the cancel of an operation with a child job that already ended.

Why:
    Issue #3367. A cancel of a running operation sent a cancel request to each
    child job, also to a child job that already ended. The cancel then listed
    each upgraded access point as a cancelled device. This journey cancels a
    seeded operation with one completed access point job and one running
    switch job. The panel must state that the access point job ended, and it
    must name no access point. A reload must show the same result.

    The server seeds the operation for the controls operator. See
    `org_ended_seeds.py`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from tests.e2e.upgrade_portal.org_control_seeds import FIRST_AP_MAC, FIRST_SWITCH_MAC, SECOND_AP_MAC
from tests.e2e.upgrade_portal.org_ended_seeds import ENDED_CHILD_IDS, ENDED_OPERATION_ID

sync_api = pytest.importorskip("playwright.sync_api", reason="Playwright is not installed.")

JOB_PATH = f"/upgrade/org/jobs/{ENDED_OPERATION_ID}"  # The progress page of the seeded operation.
SEED_TRIES = 20  # The server writes the seeds on a thread, so the first read can come too early.
SEED_PAUSE_MS = 500  # The pause between two reads of the seeded page.
ENDED_MESSAGE = "The child job already ended: completed. The portal sent no cancel request."  # The result sentence.
ENDED_NOTE = "This child job ended before the cancel, so the cancel changed no device of it."  # The panel note.
ENDED_CELL = f"Status: already_ended. {ENDED_MESSAGE}"  # The Cancellation cell of the site table.
AP_ID = ENDED_CHILD_IDS["ap"]  # The completed access point job.
SWITCH_ID = ENDED_CHILD_IDS["switch"]  # The running switch job.


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


def check_ended_result(page: Any) -> None:
    """Check the panel section and the site row of the completed access point job.

    Args:
        page: The browser page after the cancel.
    """
    sync_api.expect(page.get_by_test_id(f"org-cancel-outcome-status-{AP_ID}")).to_have_text("already_ended")
    sync_api.expect(page.get_by_test_id(f"org-cancel-outcome-message-{AP_ID}")).to_have_text(ENDED_MESSAGE)
    sync_api.expect(page.get_by_test_id(f"org-cancel-outcome-note-{AP_ID}")).to_have_text(ENDED_NOTE)
    sync_api.expect(page.get_by_test_id(f"org-cancel-outcome-cancelled-{AP_ID}")).to_have_count(0)  # No list.
    section = page.get_by_test_id(f"org-cancel-outcome-{AP_ID}").inner_text()  # The words of the section.
    assert FIRST_AP_MAC not in section and SECOND_AP_MAC not in section  # No access point reads as cancelled.
    sync_api.expect(page.locator("[data-org-upgrade-sites]")).to_contain_text(ENDED_CELL)  # The site row.
    stopped = page.get_by_test_id(f"org-cancel-outcome-cancelled-{SWITCH_ID}").locator("li")  # The switch list.
    assert [text.strip() for text in stopped.all_inner_texts()] == [FIRST_SWITCH_MAC]  # The running job stopped.


class TestEndedChildJobCancel:
    """Cancel an operation whose access point job completed first."""

    def test_the_cancel_skips_the_ended_job_and_stops_the_running_job(
        self, controls_operator_page: Any, tmp_path: Path
    ) -> None:
        """The panel states the end of the access point job, and a reload shows the same result."""
        page = controls_operator_page  # The operator that owns the seeded operation.
        open_seeded_page(page)
        sync_api.expect(page.get_by_test_id("org-cancel-outcome")).to_have_count(0)  # No cancel result exists yet.
        page.screenshot(path=str(tmp_path / "ended-before.png"), full_page=True)
        page.get_by_test_id("org-upgrade-cancel-confirmation").fill("CANCEL")
        sync_api.expect(page.get_by_test_id("org-upgrade-cancel")).to_be_enabled()
        page.get_by_test_id("org-upgrade-cancel").click()
        sync_api.expect(page.get_by_test_id("org-cancel-outcome")).to_be_visible()  # The redirect shows the panel.
        check_ended_result(page)
        first_section = page.get_by_test_id(f"org-cancel-outcome-{AP_ID}").inner_text()  # The first render.
        page.screenshot(path=str(tmp_path / "ended-after.png"), full_page=True)
        page.reload(wait_until="domcontentloaded")
        sync_api.expect(page.get_by_test_id("org-cancel-outcome")).to_be_visible()
        check_ended_result(page)
        assert page.get_by_test_id(f"org-cancel-outcome-{AP_ID}").inner_text() == first_section  # Stored result.
        page.screenshot(path=str(tmp_path / "ended-reload.png"), full_page=True)
