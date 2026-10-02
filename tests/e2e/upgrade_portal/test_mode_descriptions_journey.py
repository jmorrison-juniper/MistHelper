"""Read upgrade mode descriptions with the existing isolated Chromium portal."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from playwright.sync_api import Page

sync_api = pytest.importorskip("playwright.sync_api", reason="The Playwright package is not installed.")
expect = sync_api.expect

logger = logging.getLogger(__name__)


class TestModeDescriptionJourney:
    """Read the real pages without a capture start or a firmware request."""

    descriptions = {
        "mode-single-site-description": (
            "Single-site: Open the inventory of one site. "
            "If no verified pre-check capture exists, take one. "
            "Set the upgrade options for that site. "
            "For each device, select a target version that its model supports. "
            "Access points, switches, and Junos gateways use site routes "
            "(upgradeSiteDevices or upgradeDevice). "
            "Session Smart Router (SSR) gateways use the organization SSR route (upgradeOrgSsrs)."
        ),
        "mode-multi-site-description": (
            "Multi-site: Select one or more sites. "
            "Set the upgrade options for the selected sites. "
            "For each device, select a target version that its model supports. "
            "One portal operation tracks one or more child jobs. "
            "If all selected access points use one target version, they use an organization cloud job "
            "(upgradeOrgDevices). "
            "If access points use different target versions, they use separate site jobs "
            "(upgradeSiteDevices or upgradeDevice). "
            "Switches and Junos gateways use site routes (upgradeSiteDevices or upgradeDevice). "
            "Session Smart Router (SSR) gateways use the organization SSR route (upgradeOrgSsrs)."
        ),
        "mode-capture-description": (
            "Both modes require a verified pre-check capture for each site. "
            "The portal can use each site's newest verified standalone pre-check capture. "
            "In multi-site mode, take missing pre-check captures from the confirmation page. "
            "After the upgrade phases end, automatic post-check mode takes captures "
            "at sites with accepted upgrade jobs. "
            "In manual post-check mode, take those captures yourself. "
            "Compare each verified pre-check and post-check pair."
        ),
    }

    def _choose_mode(self, page: Page, mode: str) -> None:
        """Select a mode through its existing form and check its destination."""
        logger.info("Choose the %s mode in the isolated browser", mode)
        response = page.goto("/select/mode", wait_until="domcontentloaded")
        if response is None:
            pytest.fail("The mode page returned no browser response.")
        assert response.status == 200
        marker = "mode-single-site" if mode == "single_site" else "mode-multi-site"
        page.get_by_test_id(marker).check()
        page.get_by_test_id("mode-continue").click()
        expect(page).to_have_url(re.compile(r".*/select/site$"))
        logger.debug("The mode selection reached the site page")

    @pytest.mark.parametrize("mode", ("single_site", "multi_site"))
    def test_mode_descriptions(self, page: Page, mode: str) -> None:
        """Read both mode descriptions after either mode is selected."""
        self._choose_mode(page, mode)
        response = page.goto("/select/mode", wait_until="domcontentloaded")
        if response is None:
            pytest.fail("The selected mode page returned no browser response.")
        assert response.status == 200
        expect(page.get_by_test_id("mode-picker")).not_to_contain_text("one organization-level upgrade job")
        for marker, text in self.descriptions.items():
            expect(page.get_by_test_id(marker)).to_have_text(text)
        selected = "mode-single-site" if mode == "single_site" else "mode-multi-site"
        expect(page.get_by_test_id(selected)).to_be_checked()
        expect(page.get_by_test_id("mode-single-site")).to_have_attribute("required", "")
        logger.debug("The browser read both modes and saved the selected state")

    @pytest.mark.parametrize("count", (0, 1, 2))
    def test_multi_site_descriptions(self, page: Page, count: int) -> None:
        """Retain correct guidance with zero, one, or two saved sites."""
        self._choose_mode(page, "single_site")
        self._choose_mode(page, "multi_site")
        site_ids = ("22222222-2222-2222-2222-222222222222", "33333333-3333-3333-3333-333333333333")
        expect(page.get_by_role("main")).not_to_contain_text("one organization-level upgrade job")
        if count:
            for site_id in site_ids[:count]:
                page.get_by_test_id(f"site-select-{site_id}").check()
            page.get_by_test_id("multi-site-continue").click()
            expect(page).to_have_url(re.compile(r".*/upgrade/org/options$"))
            page.goto("/select/site", wait_until="domcontentloaded")
        expect(page.get_by_test_id("site-mode-description")).to_have_text(
            self.descriptions["mode-multi-site-description"]
        )
        expect(page.get_by_test_id("site-capture-description")).to_have_text(
            self.descriptions["mode-capture-description"]
        )
        assert page.get_by_test_id("multi-site-form").get_attribute("action") == "/select/site"
        expect(page.get_by_test_id("multi-site-form")).to_have_attribute("method", "post")
        for position, site_id in enumerate(site_ids):
            expect(page.get_by_test_id(f"site-select-{site_id}")).to_be_checked(checked=position < count)
        logger.debug("The browser retained %d selected sites", count)

    def test_single_site_description_and_capture_route(self, page: Page) -> None:
        """Keep the existing inventory and pre-check route after the description changes."""
        self._choose_mode(page, "single_site")
        expect(page.get_by_test_id("site-mode-description")).to_have_text(
            self.descriptions["mode-single-site-description"]
        )
        expect(page.get_by_test_id("site-capture-description")).to_have_text(
            self.descriptions["mode-capture-description"]
        )
        expect(page.get_by_test_id("multi-site-form")).to_have_count(0)
        site_id = "22222222-2222-2222-2222-222222222222"
        page.get_by_test_id(f"site-open-{site_id}").click()
        expect(page).to_have_url(re.compile(rf".*/select/site/{site_id}$"))
        assert page.get_by_test_id("site-capture-link").get_attribute("href") == f"/captures/new?site_id={site_id}"
        page.get_by_test_id("site-capture-link").click()
        expect(page.get_by_test_id("capture-start-button")).to_be_visible()
        logger.debug("The browser reached the capture page without starting a capture")
