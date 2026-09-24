"""Browser steps that take the multi-site pre-check captures before a submit.

Why:
    Issue #3243. The multi-site confirmation page locks the confirmation field
    until each selected site holds a verified pre-check capture. That is the
    same rule as the single-site confirmation page. Every browser journey that
    submits a multi-site operation must therefore take the missing pre-checks
    first, through the same buttons that an operator presses.
"""

from __future__ import annotations

import logging
from typing import Any

import pytest

sync_api = pytest.importorskip("playwright.sync_api", reason="Playwright is not installed.")

logger = logging.getLogger(__name__)

CARD_TESTID = "org-upgrade-prechecks"  # The pre-check card of the confirmation page.
MISSING_TESTID = "org-upgrade-precheck-missing"  # The button that captures the sites with no pre-check.
ALL_TESTID = "org-upgrade-precheck-all"  # The button that captures every selected site again.
CONFIRMATION_TESTID = "org-upgrade-confirmation"  # The typed-word field of the submit.
MISSING_ROWS = "[data-org-precheck-card] tr[data-ready='false']"  # The rows with no verified pre-check.
SITE_ROWS = "[data-org-precheck-card] tr[data-site-id]"  # One row for each selected site.
CAPTURE_PREFIX = "org-upgrade-precheck-capture-"  # The capture cell of one site row.
PRECHECK_TIMEOUT_MS = 30_000  # Two stand-in captures and one page load end well inside this bound.


class OrgPrecheckSteps:
    """Take the pre-check captures that the multi-site gate needs."""

    @staticmethod
    def take_missing(page: Any) -> None:
        """Take each missing pre-check capture, and wait for the unlocked field.

        Why:
            The card captures one site at a time and then loads the page again.
            The server paints the unlocked field only after the reload, so the
            step waits for that field and never for a fixed delay.

        Args:
            page: The browser page on the multi-site confirmation page.
        """
        sync_api.expect(page.get_by_test_id(CARD_TESTID)).to_be_visible()  # The card is on the page.
        missing = page.locator(MISSING_ROWS).count()  # The count of sites with no verified pre-check.
        logger.info("The browser takes %s missing pre-check capture(s)", missing)  # Log before the press.
        if missing:  # A site misses a pre-check, so the operator presses the missing button.
            page.get_by_test_id(MISSING_TESTID).click()  # Start the captures of the missing sites.
        OrgPrecheckSteps.wait_until_ready(page)  # The field unlocks after the reload.
        logger.debug("Each selected site holds a verified pre-check capture")  # Log after the wait.

    @staticmethod
    def take_all(page: Any) -> list[str]:
        """Take a new pre-check capture for every selected site.

        Why:
            Each row may hold a verified capture already, so the missing rows
            and the field prove nothing here. The step waits until the capture
            cell of each row names a new capture, which the server paints only
            after the reload.

        Args:
            page: The browser page on the multi-site confirmation page.

        Returns:
            The site identifiers of the rows, in the page order.
        """
        rows = page.locator(SITE_ROWS)  # One row for each selected site.
        sites = [str(site) for site in rows.evaluate_all("nodes => nodes.map(node => node.dataset.siteId)")]
        before = {site: page.get_by_test_id(CAPTURE_PREFIX + site).inner_text() for site in sites}  # Old captures.
        logger.info("The browser takes a new pre-check capture for %s site(s)", len(sites))  # Log before the press.
        page.get_by_test_id(ALL_TESTID).click()  # Start one capture for each selected site.
        for site in sites:  # Each row must name a new capture after the reload.
            cell = page.get_by_test_id(CAPTURE_PREFIX + site)  # The capture cell of this site.
            sync_api.expect(cell).not_to_have_text(before[site], timeout=PRECHECK_TIMEOUT_MS)  # A new capture.
        OrgPrecheckSteps.wait_until_ready(page)  # The field stays unlocked after the reload.
        logger.debug("The browser took a new pre-check capture for each site")  # Log after the wait.
        return sites  # The caller can read each row again.

    @staticmethod
    def wait_until_ready(page: Any) -> None:
        """Wait until no row misses a pre-check and the field is unlocked.

        Args:
            page: The browser page on the multi-site confirmation page.
        """
        sync_api.expect(page.locator(MISSING_ROWS)).to_have_count(0, timeout=PRECHECK_TIMEOUT_MS)  # All verified.
        field = page.get_by_test_id(CONFIRMATION_TESTID)  # The typed-word field of the submit.
        sync_api.expect(field).to_be_enabled(timeout=PRECHECK_TIMEOUT_MS)  # The reload unlocked the field.
