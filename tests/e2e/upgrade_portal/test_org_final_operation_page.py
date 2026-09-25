"""Browser journeys for the page of a final multi-site operation.

Why:
    Issue #3225. The progress page of a final multi-site operation offered a
    cancel form, and the portal sent a cancel request for that operation. The
    single-site stop page offers no stop for a final run. These journeys prove
    the same rule in a real browser. They also prove that the word cells of
    the two tables break no word at a narrow width.

    The journeys read the two recovery seeds of `org_control_seeds.py`. They
    only read pages, so they change no seed that another journey reads.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

from tests.e2e.upgrade_portal.org_control_seeds import RECONCILE_OPERATION_ID, RETRY_OPERATION_ID

sync_api = pytest.importorskip("playwright.sync_api", reason="Playwright is not installed.")

SEED_TRIES = 20  # The server writes the seeds on a thread, so the first read can come too early.
SEED_PAUSE_MS = 500  # The pause between two reads of a seeded page.
NARROW = {"width": 960, "height": 900}  # The width of the defect report.
WIDE = {"width": 1280, "height": 900}  # A common laptop width.
POLL_PATH = re.compile(r".*/api/org-upgrades/[^/]+$")  # The status read of the page. The cancel path is longer.
SITE_WORD_COLUMNS = "[data-org-upgrade-sites] tr > td:nth-child(2), [data-org-upgrade-sites] tr > td:nth-child(3)"
DEVICE_WORD_COLUMNS = (
    "[data-org-upgrade-devices] tr > td:nth-child(1), "
    "[data-org-upgrade-devices] tr > td:nth-child(4), "
    "[data-org-upgrade-devices] tr > td:nth-child(5)"
)  # The site, type, and state cells of the device table.
BROKEN_WORDS_SCRIPT = """
(selector) => {
  const broken = [];
  document.querySelectorAll(selector).forEach((cell) => {
    const walker = document.createTreeWalker(cell, NodeFilter.SHOW_TEXT);
    for (let node = walker.nextNode(); node; node = walker.nextNode()) {
      for (const match of node.textContent.matchAll(/[^\\s-]+/g)) {
        const range = document.createRange();
        range.setStart(node, match.index);
        range.setEnd(node, match.index + match[0].length);
        const tops = new Set(Array.from(range.getClientRects()).map((rect) => Math.round(rect.top)));
        if (tops.size > 1) {
          broken.push(match[0]);
        }
      }
    }
  });
  return broken;
}
"""  # Each letter group that spans two lines of one cell. A wrap after a hyphen is a normal line break.


class FinalPageSteps:
    """Hold the steps that the journeys of this module share."""

    @staticmethod
    def open_seed(page: Any, operation_id: str) -> None:
        """Open the progress page of one seed, and wait until the seed exists.

        Args:
            page: The browser page of the controls operator.
            operation_id: The identity of the seeded operation.
        """
        for _ in range(SEED_TRIES):  # The seed thread can finish after the first test starts.
            page.goto(f"/upgrade/org/jobs/{operation_id}", wait_until="domcontentloaded")
            if page.get_by_test_id("org-upgrade-controls").count() == 1:  # The seed exists and shows its controls.
                return
            page.wait_for_timeout(SEED_PAUSE_MS)
        sync_api.expect(page.get_by_test_id("org-upgrade-controls")).to_be_visible()  # Report the missing seed.

    @staticmethod
    def shoot(page: Any, folder: Path, name: str) -> None:
        """Take one full-page screenshot at the narrow width and one at the wide width."""
        for label, size in (("960", NARROW), ("1280", WIDE)):  # Both widths of the review.
            page.set_viewport_size(size)
            page.screenshot(path=str(folder / f"{name}-{label}.png"), full_page=True)

    @staticmethod
    def final_poll(route: Any) -> None:
        """Answer the status read of a live seed with the same answer in a final state."""
        if route.request.method != "GET":  # Only the status read changes.
            route.continue_()
            return
        response = route.fetch()  # The real answer of the server.
        body = response.json()
        body["status"] = "completed"  # The cloud now reports a final state.
        body["cancel_allowed"] = False  # The server rule for a final state.
        route.fulfill(response=response, json=body)


class TestFinalOperationPage:
    """Drive the progress page of a final operation and of a live operation."""

    def test_a_final_operation_shows_no_cancel_form(self, controls_operator_page: Any, tmp_path: Path) -> None:
        """The page of a failed operation shows the closed note and no cancel control."""
        page = controls_operator_page  # The operator that owns the seeds.
        page.set_viewport_size(NARROW)
        FinalPageSteps.open_seed(page, RETRY_OPERATION_ID)  # The seed in the final state failed.
        closed = page.get_by_test_id("org-upgrade-cancel-closed")
        sync_api.expect(closed).to_be_visible()
        sync_api.expect(closed).to_contain_text("The operation is final: failed.")
        for test_id in ("org-upgrade-cancel-confirmation", "org-upgrade-cancel", "org-upgrade-cancel-caution"):
            sync_api.expect(page.get_by_test_id(test_id)).to_have_count(0)  # No cancel control exists.
        assert page.locator("[data-org-cancel-controls]").count() == 0  # The server rendered no form region.
        FinalPageSteps.shoot(page, tmp_path, "final-operation")

    def test_a_poll_that_reports_a_final_state_closes_the_cancel_form(
        self, controls_operator_page: Any, tmp_path: Path
    ) -> None:
        """A poll that reports a final state hides and disables the cancel form of the page."""
        page = controls_operator_page  # The operator that owns the seeds.
        page.set_viewport_size(NARROW)
        FinalPageSteps.open_seed(page, RECONCILE_OPERATION_ID)  # The seed in the live state attention_required.
        sync_api.expect(page.get_by_test_id("org-upgrade-cancel-confirmation")).to_be_visible()
        sync_api.expect(page.get_by_test_id("org-upgrade-cancel-closed")).to_be_hidden()
        page.route(POLL_PATH, FinalPageSteps.final_poll)
        page.get_by_test_id("org-upgrade-refresh").click()
        sync_api.expect(page.get_by_test_id("org-upgrade-cancel-controls")).to_be_hidden()
        sync_api.expect(page.get_by_test_id("org-upgrade-cancel-confirmation")).to_be_disabled()
        sync_api.expect(page.get_by_test_id("org-upgrade-cancel")).to_be_disabled()
        sync_api.expect(page.get_by_test_id("org-upgrade-cancel-closed")).to_be_visible()
        sync_api.expect(page.get_by_test_id("org-upgrade-cancel-closed")).to_contain_text(
            "The operation is final: completed."
        )
        assert page.locator("[data-org-cancel-controls] :enabled").count() == 0  # No closed control can act.
        page.unroute(POLL_PATH)  # The seed stays live on the server. Only the browser read changed.
        FinalPageSteps.shoot(page, tmp_path, "closed-by-poll")

    def test_the_word_cells_break_no_word_at_a_narrow_width(self, controls_operator_page: Any, tmp_path: Path) -> None:
        """The site, type, and state cells of both tables keep each word on one line at 960 pixels."""
        page = controls_operator_page  # The operator that owns the seeds.
        page.set_viewport_size(NARROW)
        FinalPageSteps.open_seed(page, RETRY_OPERATION_ID)  # The seed with two sites and three devices.
        site_rows = page.locator("[data-org-upgrade-sites] tr").count()
        device_rows = page.locator("[data-org-upgrade-devices] tr").count()
        assert page.locator("[data-org-upgrade-sites] td.cell-word").count() == 2 * site_rows  # Family and state.
        assert page.locator("[data-org-upgrade-devices] td.cell-word").count() == 3 * device_rows  # Site, type, state.
        for columns in (SITE_WORD_COLUMNS, DEVICE_WORD_COLUMNS):  # Measure both tables.
            assert page.evaluate(BROKEN_WORDS_SCRIPT, columns) == []  # No word spans two lines.
        page.get_by_test_id("org-upgrade-refresh").click()  # The poll paints every row again.
        sync_api.expect(page.get_by_test_id("flash-message")).to_contain_text("current")
        assert page.locator("[data-org-upgrade-sites] td.cell-word").count() == 2 * site_rows  # The paint keeps it.
        for columns in (SITE_WORD_COLUMNS, DEVICE_WORD_COLUMNS):  # Measure both tables after the paint.
            assert page.evaluate(BROKEN_WORDS_SCRIPT, columns) == []
        FinalPageSteps.shoot(page, tmp_path, "word-cells")
