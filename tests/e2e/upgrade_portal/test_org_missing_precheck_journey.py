"""Browser journey for the multi-site pre-check gate.

Why:
    Issue #3243. The single-site confirmation page locks the start until the
    site holds a verified pre-check capture. The multi-site confirmation page
    had no such rule, so an operator could start a firmware write at many
    sites with no capture to compare against after the upgrade. This journey
    proves the same rule in a real browser for each selected site.

    The file name sorts before each journey that submits a multi-site
    operation. The second stand-in site therefore holds no pre-check when this
    journey opens the confirmation page. The journey ends with a submit and a
    cancel, so both stand-in sites go back for the later browser tests.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import pytest

from tests.e2e.upgrade_portal.org_cancel_steps import JOB_PATH, OrgCancelSteps
from tests.e2e.upgrade_portal.org_precheck_steps import CAPTURE_PREFIX, OrgPrecheckSteps

sync_api = pytest.importorskip("playwright.sync_api", reason="Playwright is not installed.")

logger = logging.getLogger(__name__)

MODE_PATH = "/select/mode"  # The first page of the multi-site journey.
SITE_ID = "22222222-2222-2222-2222-222222222222"  # The first stand-in site of `conftest.py`.
SECOND_SITE_ID = "33333333-3333-3333-3333-333333333333"  # The second stand-in site. It holds no seeded capture.
SITE_IDS = (SITE_ID, SECOND_SITE_ID)  # Both selected sites, in the page order.
CHOSEN_TIER = "3"  # The operator reads the port state, the radio state, and the alarms too.


def open_confirmation(page: Any) -> None:
    """Select both stand-in sites, save a plan, and open the confirmation page.

    Args:
        page: The browser page of the firmware operator.
    """
    page.goto(MODE_PATH, wait_until="domcontentloaded")  # The journey starts at the mode choice.
    page.get_by_test_id("mode-multi-site").check()  # The operator selects many sites.
    page.get_by_test_id("mode-continue").click()  # The page must advance.
    page.wait_for_url(re.compile(r".*/select/site$"))  # The site page must open.
    for site in SITE_IDS:  # The plan includes both stand-in sites.
        page.get_by_test_id(f"site-select-{site}").check()
    page.get_by_test_id("multi-site-continue").click()  # The selected sites must persist.
    page.wait_for_url(re.compile(r".*/upgrade/org/options$"))  # The options page must open.
    page.get_by_test_id("org-upgrade-version").fill("0.15.1")  # The access point version is fixed.
    page.get_by_test_id("org-upgrade-switch-version").fill("0.15.1")  # The switch version is fixed.
    page.get_by_test_id("org-upgrade-gateway-version").fill("0.15.1")  # The gateway version is fixed.
    page.get_by_test_id("org-upgrade-review").click()  # The review page must use the plan.
    page.wait_for_url(re.compile(r".*/upgrade/org/confirm$"))  # The confirmation page must open.


def capture_of(page: Any, site: str) -> str:
    """Return the capture identifier that the row of one site names.

    Args:
        page: The browser page on the confirmation page.
        site: The site identifier of the row.
    """
    return page.get_by_test_id(CAPTURE_PREFIX + site).inner_text().strip()  # The link text is the identifier.


def is_precheck_start(request: Any) -> bool:
    """Return True for the request that starts one multi-site pre-check capture.

    Args:
        request: One network request of the browser page.
    """
    return request.method == "POST" and "/api/org-upgrades/prechecks/" in request.url  # The start of the card.


class TestMultiSitePrecheckGate:
    """Take each missing pre-check, start the operation, and read the stored captures."""

    def test_the_gate_locks_the_start_until_each_site_holds_a_pre_check(
        self, firmware_operator_page: Any, tmp_path: Path
    ) -> None:
        """The operator takes the missing pre-check, retakes both, and starts the upgrade."""
        page = firmware_operator_page  # This path starts firmware, so it needs a reachable operator address.
        open_confirmation(page)  # Both sites are selected and the plan is saved.
        second_row = page.get_by_test_id(f"org-upgrade-precheck-row-{SECOND_SITE_ID}")  # The second site row.
        sync_api.expect(second_row).to_have_attribute("data-ready", "false")  # No seeded capture exists.
        sync_api.expect(page.get_by_test_id(CAPTURE_PREFIX + SECOND_SITE_ID)).to_have_text("None saved")
        sync_api.expect(page.get_by_test_id(f"org-upgrade-precheck-state-{SECOND_SITE_ID}")).to_have_text("missing")
        sync_api.expect(page.get_by_test_id("org-upgrade-precheck-hint")).to_be_visible()  # The page names the rule.
        sync_api.expect(page.get_by_test_id("org-upgrade-confirmation")).to_be_disabled()  # No word before a capture.
        sync_api.expect(page.get_by_test_id("org-upgrade-start")).to_be_disabled()  # No start before a capture.
        sync_api.expect(page.get_by_test_id("org-upgrade-precheck-missing")).to_be_enabled()  # One site misses one.
        page.screenshot(path=str(tmp_path / "precheck-01-missing.png"), full_page=True)

        page.get_by_test_id("org-upgrade-precheck-tier").select_option(CHOSEN_TIER)  # The operator picks tier 3.
        with page.expect_request(is_precheck_start) as sent:  # The card sends the chosen tier to the route.
            page.get_by_test_id("org-upgrade-precheck-missing").click()  # Capture the site with no pre-check.
        assert sent.value.url.endswith(f"/api/org-upgrades/prechecks/{SECOND_SITE_ID}")  # Only the missing site.
        assert json.loads(sent.value.post_data or "{}").get("tier") == int(CHOSEN_TIER)  # The tier of the select.
        OrgPrecheckSteps.wait_until_ready(page)  # The card loads the page again after the capture verifies.
        sync_api.expect(second_row).to_have_attribute("data-ready", "true")  # The server stored the capture.
        sync_api.expect(page.get_by_test_id(f"org-upgrade-precheck-state-{SECOND_SITE_ID}")).to_have_text("verified")
        assert page.get_by_test_id("org-upgrade-precheck-hint").count() == 0  # The rule holds, so no hint shows.
        sync_api.expect(page.get_by_test_id("org-upgrade-precheck-missing")).to_be_disabled()  # Nothing is missing.
        sync_api.expect(page.get_by_test_id("org-upgrade-start")).to_be_disabled()  # The word is still missing.
        page.screenshot(path=str(tmp_path / "precheck-02-taken.png"), full_page=True)

        link = page.get_by_test_id(CAPTURE_PREFIX + SECOND_SITE_ID)  # The capture link of the second site.
        sync_api.expect(link).to_have_attribute("href", f"/captures/{capture_of(page, SECOND_SITE_ID)}")

        page.get_by_test_id("org-upgrade-precheck-tier").select_option("2")  # The retake reads the standard tier.
        before = {site: capture_of(page, site) for site in SITE_IDS}  # The captures before the retake.
        OrgPrecheckSteps.take_all(page)  # The card captures both sites again and loads the page again.
        after = {site: capture_of(page, site) for site in SITE_IDS}  # The captures after the retake.
        assert all(after[site] != before[site] for site in SITE_IDS), f"The retake kept a capture: {after}"
        page.screenshot(path=str(tmp_path / "precheck-03-retaken.png"), full_page=True)

        page.get_by_test_id("org-upgrade-confirmation").fill("CONFIRM")  # The operator confirms the write.
        sync_api.expect(page.get_by_test_id("org-upgrade-start")).to_be_enabled()  # Each site holds a capture.
        page.get_by_test_id("org-upgrade-start").click()  # The page starts the operation.
        page.wait_for_url(JOB_PATH)  # The progress page must open.
        stored = page.get_by_test_id("org-upgrade-precheck-list")  # The captures that the operation stored.
        sync_api.expect(stored).to_be_visible()
        for site in SITE_IDS:  # The operation stored the newest capture of each site.
            stored_link = page.get_by_test_id(f"org-upgrade-precheck-link-{site}")
            sync_api.expect(stored_link).to_have_text(after[site])
            sync_api.expect(stored_link).to_have_attribute("href", f"/captures/{after[site]}")
        page.screenshot(path=str(tmp_path / "precheck-04-progress.png"), full_page=True)

        OrgCancelSteps.cancel(page)  # Both stand-in sites go back for the later browser tests.
        sync_api.expect(stored).to_be_visible()  # The stored captures stay after the cancel.
        page.screenshot(path=str(tmp_path / "precheck-05-cancelled.png"), full_page=True)
        logger.debug("The pre-check journey ended with a cancel")  # Log after the last step.
