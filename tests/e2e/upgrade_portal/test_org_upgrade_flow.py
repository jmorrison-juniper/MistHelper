"""Browser tests for the organization multi-site upgrade workflow."""

from __future__ import annotations

import re
from typing import Any

import pytest

sync_api = pytest.importorskip("playwright.sync_api", reason="Playwright is not installed.")

MODE_PATH = "/select/mode"
SITE_ID = "22222222-2222-2222-2222-222222222222"
SECOND_SITE_ID = "33333333-3333-3333-3333-333333333333"
UPGRADE_ID = "44444444-4444-4444-4444-444444444444"


class TestOrganizationUpgradeBrowserFlow:
    """Drive the organization mode from site selection through cancellation."""

    def test_multisite_options_confirmation_progress_and_cancel(self, page: Any) -> None:
        """The browser completes every organization page without a live Mist call."""
        page.goto(MODE_PATH, wait_until="domcontentloaded")
        page.get_by_test_id("mode-multi-site").check()
        page.get_by_test_id("mode-continue").click()
        page.wait_for_url(re.compile(r".*/select/site$"))

        page.get_by_test_id(f"site-select-{SITE_ID}").check()
        page.get_by_test_id(f"site-select-{SECOND_SITE_ID}").check()
        page.get_by_test_id("multi-site-continue").click()
        page.wait_for_url(re.compile(r".*/upgrade/org/options$"))
        sync_api.expect(page.get_by_test_id("org-upgrade-options")).to_be_visible()

        page.get_by_test_id("org-upgrade-version").fill("0.15.1")
        page.get_by_test_id("org-strategy-canary").check()
        page.get_by_test_id("org-upgrade-canary-phases").fill("10,100")
        page.get_by_test_id("org-upgrade-max-failures").fill("0")
        page.get_by_test_id("org-upgrade-review").click()
        page.wait_for_url(re.compile(r".*/upgrade/org/confirm$"))
        sync_api.expect(page.get_by_test_id("org-upgrade-confirm")).to_be_visible()
        sync_api.expect(page.get_by_test_id("org-upgrade-start")).to_be_disabled()

        page.get_by_test_id("org-upgrade-confirmation").fill("CONFIRM")
        sync_api.expect(page.get_by_test_id("org-upgrade-start")).to_be_enabled()
        page.get_by_test_id("org-upgrade-start").click()
        page.wait_for_url(re.compile(rf".*/upgrade/org/jobs/{UPGRADE_ID}$"))
        sync_api.expect(page.get_by_test_id("org-upgrade-progress")).to_be_visible()
        sync_api.expect(page.get_by_test_id("org-upgrade-site-progress")).to_be_visible()

        cancel_input = page.get_by_test_id("org-upgrade-cancel-confirmation")
        sync_api.expect(page.get_by_test_id("org-upgrade-cancel")).to_be_disabled()
        cancel_input.fill("CAN")

        def updated_status(route: Any) -> None:
            if route.request.method != "GET":
                route.continue_()
                return
            route.fulfill(
                status=200,
                content_type="application/json",
                body='{"upgrade_id":"44444444-4444-4444-4444-444444444444","status":"completed","current_phase":2,"total":4,"upgraded_count":3,"failed_count":1,"site_upgrades":[{"site_id":"22222222-2222-2222-2222-222222222222","id":"55555555-5555-5555-5555-555555555555","status":"completed","total":2,"upgraded":2,"failed":0},{"site_id":"33333333-3333-3333-3333-333333333333","id":"66666666-6666-6666-6666-666666666666","status":"failed","total":2,"upgraded":1,"failed":1}]}',
            )

        page.route(re.compile(r".*/api/org-upgrades/[^/]+$"), updated_status)
        page.get_by_test_id("org-upgrade-refresh").click()
        sync_api.expect(cancel_input).to_have_value("CAN")
        sync_api.expect(page.get_by_test_id("org-upgrade-site-progress")).to_contain_text("completed")
        sync_api.expect(page.get_by_test_id("org-upgrade-site-progress")).to_contain_text("failed")
        cancel_input.fill("CANCEL")
        sync_api.expect(page.get_by_test_id("org-upgrade-cancel")).to_be_enabled()
        page.get_by_test_id("org-upgrade-cancel").click()
        page.wait_for_url(re.compile(rf".*/upgrade/org/jobs/{UPGRADE_ID}$"))
