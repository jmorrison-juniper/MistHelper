"""Browser journey for the cancel outcome panel of a multi-site operation.

Why:
    Issue #3246. The single-site stop page shows which devices stopped, which
    devices still write firmware, and which devices have no cancel path. This
    journey cancels a seeded multi-site operation through a real browser, and
    it reads the same three lists for each child job. A reload must show the
    same lists, because the page builds them from the stored record.

    The server seeds the operation for the controls operator, because no safe
    journey reaches a rebooting access point. See `org_cancel_seeds.py`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from tests.e2e.upgrade_portal.org_cancel_seeds import CANCEL_OPERATION_ID, CHILD_IDS, SECOND_GATEWAY_MAC
from tests.e2e.upgrade_portal.org_control_seeds import FIRST_AP_MAC, FIRST_SWITCH_MAC, SECOND_AP_MAC

sync_api = pytest.importorskip("playwright.sync_api", reason="Playwright is not installed.")

JOB_PATH = f"/upgrade/org/jobs/{CANCEL_OPERATION_ID}"  # The progress page of the seeded operation.
SEED_TRIES = 20  # The server writes the seeds on a thread, so the first read can come too early.
SEED_PAUSE_MS = 500  # The pause between two reads of the seeded page.
CAUTION_START = "Caution: the cancellation stops each upgrade that waits to start."  # The first caution sentence.
NEVER_STARTED = "No upgrade of this child job exists in the cloud, so no device of it writes firmware."
NONE_CANCELLED = ["The portal canceled no device."]  # The empty text of the cancelled list.
NONE_WRITING = ["No device writes firmware."]  # The empty text of the writing list.
ALL_CANCELABLE = ["Every device has a cancel path."]  # The empty text of the no-cancel list.
EXPECTED_LISTS = {  # The three lists of each child job after the cancel.
    "ap": ([FIRST_AP_MAC], [SECOND_AP_MAC], ALL_CANCELABLE),
    "switch": ([FIRST_SWITCH_MAC], NONE_WRITING, ALL_CANCELABLE),
    "gateway": (NONE_CANCELLED, NONE_WRITING, ALL_CANCELABLE),
}


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


def panel_lists(page: Any) -> dict[str, tuple[list[str], list[str], list[str]]]:
    """Return the three lists of each child job, as the browser shows them."""
    lists = {}  # One entry for each device family.
    for family, child_id in CHILD_IDS.items():  # The plan order of the seed.
        names = ("cancelled", "writing", "no-cancel")  # The three list identifiers of one child job.
        found = [page.get_by_test_id(f"org-cancel-outcome-{name}-{child_id}").locator("li") for name in names]
        lists[family] = tuple([text.strip() for text in items.all_inner_texts()] for items in found)
    return lists  # The caller compares every list at one time.


class TestMultiSiteCancelOutcomes:
    """Cancel a running multi-site operation, and read the three lists of each child job."""

    def test_the_cancel_shows_three_lists_for_each_child_job(self, controls_operator_page: Any, tmp_path: Path) -> None:
        """The cancel sorts each device, and a reload shows the same lists."""
        page = controls_operator_page  # The operator that owns the seeded operation.
        open_seeded_page(page)
        sync_api.expect(page.get_by_test_id("org-upgrade-cancel-caution")).to_contain_text(CAUTION_START)
        sync_api.expect(page.get_by_test_id("org-cancel-outcome")).to_have_count(0)  # No cancel result exists yet.
        page.screenshot(path=str(tmp_path / "cancel-before.png"), full_page=True)
        page.get_by_test_id("org-upgrade-cancel-confirmation").fill("CANCEL")
        sync_api.expect(page.get_by_test_id("org-upgrade-cancel")).to_be_enabled()
        page.get_by_test_id("org-upgrade-cancel").click()
        sync_api.expect(page.get_by_test_id("org-cancel-outcome")).to_be_visible()  # The redirect shows the panel.
        assert panel_lists(page) == EXPECTED_LISTS  # Each device sits in one list.
        gateway_note = page.get_by_test_id(f"org-cancel-outcome-note-{CHILD_IDS['gateway']}")
        sync_api.expect(gateway_note).to_have_text(NEVER_STARTED)  # The refused child job has no cloud job.
        assert SECOND_GATEWAY_MAC not in page.get_by_test_id("org-cancel-outcome").inner_text()  # No list names it.
        page.screenshot(path=str(tmp_path / "cancel-after.png"), full_page=True)
        page.reload(wait_until="domcontentloaded")
        sync_api.expect(page.get_by_test_id("org-cancel-outcome")).to_be_visible()
        assert panel_lists(page) == EXPECTED_LISTS  # The stored record keeps the same lists.
        page.screenshot(path=str(tmp_path / "cancel-reload.png"), full_page=True)
