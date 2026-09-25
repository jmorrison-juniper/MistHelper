"""Browser journeys for the post-check capture card of a multi-site operation.

Why:
    Issue #3244. A single-site run takes a post-check capture after the last
    phase ends, and its page links the comparison of the two captures. The
    multi-site page took no post-check capture, so the operator could not
    compare a site before and after the upgrade. These journeys start a real
    multi-site upgrade of both stand-in sites. They read the post-check card in
    a real browser, and they open the comparison of one site.

    The browser server replaces the watch thread with a scripted starter. The
    starter ends the watch through the production close, so the production
    post-check stage takes each capture through the stand-in capture runner.

    Each journey ends with a cancel and a reload, so both stand-in sites go
    back for the later browser tests.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

from tests.e2e.upgrade_portal.org_cancel_steps import JOB_PATH, OrgCancelSteps
from tests.e2e.upgrade_portal.test_org_phase_cascade_journey import (
    SECOND_SITE_ID,
    SITE_ID,
    phase_snapshot,
    refreshed_snapshot,
    start_operation,
)

sync_api = pytest.importorskip(
    "playwright.sync_api", reason="Playwright is not installed."
)  # The test needs Playwright.

SITE_IDS = (SITE_ID, SECOND_SITE_ID)  # The two stand-in sites of each operation, in the plan order.
POST_KEY = re.compile(r"^cap-[0-9a-f]{32}-02$")  # FR-003: the key of a post-check capture.
COMPARE_PAGE = re.compile(r".*/compare\?before=[^&]+&after=cap-[0-9a-f]{32}-02$")  # FR-013: the compare page.
REFRESH_LIMIT = 10  # Four phases need five steps. The limit leaves room for the automatic poll.
RELOAD_MARKER = "window.__postCheckJourneyMarker"  # A reload removes this value from the page.


class OrgPostCheckSteps:
    """Read the post-check card, and move the watch to its end."""

    @staticmethod
    def row(page: Any, site_id: str) -> dict[str, Any]:
        """Return the state, the capture key, and the compare target of one site row.

        Args:
            page: The browser page on the progress page of the operation.
            site_id: The site of the row.

        Returns:
            The values that an operator reads on the row.
        """
        item = page.get_by_test_id(f"org-upgrade-postcheck-row-{site_id}")  # The row of the site.
        return {  # A hidden link still holds its text and its target.
            "state": item.get_by_test_id(f"org-upgrade-postcheck-state-{site_id}").text_content().strip(),
            "capture": item.get_by_test_id(f"org-upgrade-postcheck-capture-{site_id}").text_content().strip(),
            "compare": item.get_by_test_id(f"org-upgrade-postcheck-compare-{site_id}").get_attribute("href"),
        }

    @staticmethod
    def refresh_until_finished(page: Any) -> dict[str, Any]:
        """Press Refresh until the phase watch reads "Finished".

        Args:
            page: The browser page on the progress page of the operation.

        Returns:
            The last painted phase card.
        """
        card = phase_snapshot(page)  # The card before the first press.
        for _ in range(REFRESH_LIMIT):  # Each press shows one more step.
            if card["watch"] == "Finished":  # The close took the captures and ended the watch.
                break  # The final card is ready.
            card = refreshed_snapshot(page, card)  # The next card follows one poll.
        assert card["watch"] == "Finished", f"The watch did not end: {card}"  # FR-001: the watch ended.
        return card  # The caller reads the post-check card next.

    @staticmethod
    def require_verified_pairs(page: Any) -> list[str]:
        """Require a verified capture and a visible compare link for each site.

        Args:
            page: The browser page on the progress page of the operation.

        Returns:
            The compare target of each site, in the plan order.
        """
        targets = []  # One compare target for each site.
        for site_id in SITE_IDS:  # FR-005: one capture for each site of the plan.
            sync_api.expect(page.get_by_test_id(f"org-upgrade-postcheck-state-{site_id}")).to_have_text("Verified")
            compare = page.get_by_test_id(f"org-upgrade-postcheck-compare-{site_id}")  # The pair link.
            sync_api.expect(compare).to_be_visible()  # FR-013: the operation holds both captures.
            found = OrgPostCheckSteps.row(page, site_id)  # The painted row.
            assert POST_KEY.match(found["capture"]), found  # FR-003: the ordinal 2 key.
            assert found["compare"].endswith(f"&after={found['capture']}"), found  # The link names this capture.
            targets.append(found["compare"])  # The caller opens one comparison.
        return targets  # The caller opens one comparison.

    @staticmethod
    def require_repaint_with_no_reload(page: Any) -> None:
        """Require that one poll repaints a changed row, and that the page does not load again.

        Why:
            FR-014. The poll must repaint each row with no reload. The step
            writes a false label into the first row and a marker into the
            window. A reload removes the marker, and only the paint of the
            poll puts the true label back.

        Args:
            page: The browser page on the progress page of the operation.
        """
        state = page.get_by_test_id(f"org-upgrade-postcheck-state-{SITE_ID}")  # The label of the first row.
        page.evaluate(f"{RELOAD_MARKER} = true")  # A reload removes this value.
        state.evaluate("element => { element.textContent = 'Changed by the test'; }")  # A false label.
        with page.expect_response(
            lambda answer: "/api/org-upgrades/" in answer.url and answer.request.method == "GET"
        ):  # The refresh must reach the poll.
            page.get_by_test_id("org-upgrade-refresh").click()  # One poll of the final watch.
        sync_api.expect(state).to_have_text("Verified")  # The paint put the true label back.
        assert page.evaluate(f"{RELOAD_MARKER} === true"), "The poll loaded the page again."  # FR-014.


class TestMultiSitePostCheck:
    """Follow the post-check capture of each site of one multi-site operation in a real browser."""

    def test_each_site_gets_a_verified_post_check_and_a_compare_link(
        self, firmware_operator_page: Any, tmp_path: Path
    ) -> None:
        """FR-001, FR-012, FR-013, and FR-014: the finished watch shows a verified pair for each site."""
        page = firmware_operator_page  # This path starts firmware, so it needs a reachable operator address.
        start_operation(page)  # The test needs one running operation.
        sync_api.expect(page.get_by_test_id("org-upgrade-postcheck-list")).to_be_visible()  # FR-012: the card.
        for site_id in SITE_IDS:  # User story 2: each row waits while the phases run.
            sync_api.expect(page.get_by_test_id(f"org-upgrade-postcheck-state-{site_id}")).to_have_text("Waiting")
            sync_api.expect(page.get_by_test_id(f"org-upgrade-postcheck-compare-{site_id}")).to_be_hidden()
        page.screenshot(path=str(tmp_path / "postcheck-waiting.png"), full_page=True)  # The artifact of the wait.
        OrgPostCheckSteps.refresh_until_finished(page)  # The close takes both captures.
        targets = OrgPostCheckSteps.require_verified_pairs(page)  # FR-013: one pair for each site.
        page.screenshot(path=str(tmp_path / "postcheck-verified.png"), full_page=True)  # The artifact of the end.
        OrgPostCheckSteps.require_repaint_with_no_reload(page)  # FR-014: the poll paints the rows.
        page.get_by_test_id(f"org-upgrade-postcheck-compare-{SITE_ID}").click()  # The operator opens one pair.
        page.wait_for_url(COMPARE_PAGE)  # FR-013: the compare page opens with both keys.
        assert page.url.endswith(targets[0]), page.url  # The page opened the pair of the first site.
        sync_api.expect(page.get_by_test_id("compare-device-table")).to_be_visible()  # The comparison renders.
        page.screenshot(path=str(tmp_path / "postcheck-compare.png"), full_page=True)  # The artifact of the pair.
        page.go_back(wait_until="domcontentloaded")  # The progress page of the operation.
        page.wait_for_url(JOB_PATH)  # The cancel helper needs the progress page.
        OrgCancelSteps.cancel(page)  # Both stand-in sites go back for the later tests.

    def test_a_cancel_takes_the_post_check_captures_before_the_stop(
        self, firmware_operator_page: Any, tmp_path: Path
    ) -> None:
        """FR-002: a cancel during a phase takes the post-check captures, then writes the stopped state."""
        page = firmware_operator_page  # This path starts firmware, so it needs a reachable operator address.
        start_operation(page)  # The test needs one running operation.
        assert phase_snapshot(page)["watch"] == "Active"  # The cancel starts during the watch.
        OrgCancelSteps.cancel(page)  # The script reload takes the stop step, and the helper reload shows it.
        sync_api.expect(page.get_by_test_id("org-upgrade-phase-watch-state")).to_have_text("Stopped")  # The stop.
        OrgPostCheckSteps.require_verified_pairs(page)  # FR-002: the stop took both captures first.
        page.screenshot(path=str(tmp_path / "postcheck-after-cancel.png"), full_page=True)  # The artifact.
