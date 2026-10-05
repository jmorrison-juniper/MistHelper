"""Require the visible count and each version-change row through the real picker."""

from __future__ import annotations

import logging
from typing import ClassVar

import pytest

from tests.e2e.upgrade_portal.test_comparison import _click_and_wait, _require_built_route

try:
    from playwright.sync_api import Page
except ModuleNotFoundError:
    pytest.importorskip("playwright.sync_api", reason="The Playwright package is not installed.")

sync_api = pytest.importorskip("playwright.sync_api", reason="The Playwright package is not installed.")
logger = logging.getLogger(__name__)


class CaptureVersionComparison:
    """Read the shipped comparison without fabricated captures or missing-data skips."""

    MACS: ClassVar[frozenset[str]] = frozenset({"000000000001", "000000000002", "000000000003"})

    @staticmethod
    def open_picker(page: Page) -> None:
        """Require a real comparison picker before the selection."""
        logger.info("Open the comparison picker")
        response = page.goto("/compare", wait_until="domcontentloaded")
        assert response is not None, "The real comparison picker returned no HTTP response."
        _require_built_route(response.status, "/compare")
        logger.debug("Opened the comparison picker with HTTP=%d", response.status)

    @classmethod
    def select_pair(cls, page: Page) -> None:
        """Choose the existing pre-check and post-check through the visible picker."""
        cls.open_picker(page)
        before = page.get_by_test_id("compare-before-select")
        after = page.get_by_test_id("compare-after-select")
        sync_api.expect(before).to_be_visible()
        sync_api.expect(after).to_be_visible()
        logger.info("Select the existing pre-check and post-check capture IDs")
        before.select_option("e2e-capture-pre-0001")
        sync_api.expect(before).to_have_value("e2e-capture-pre-0001")
        after.select_option("e2e-capture-post-0001")
        sync_api.expect(after).to_have_value("e2e-capture-post-0001")
        logger.debug("Selected capture IDs=2")
        cls.submit_pair(page)

    @staticmethod
    def submit_pair(page: Page) -> None:
        """Submit the selected pair without a missing-data skip."""
        logger.info("Submit the selected comparison pair")
        status = _click_and_wait(page, "compare-run-button")
        page.wait_for_load_state("domcontentloaded")
        _require_built_route(status, page.url)
        notice = page.get_by_test_id("compare-refusal")  # The page-local alert of the compare picker (#3908).
        notice_text = " ".join(" ".join(notice.all_text_contents()).split())
        assert notice_text == "", f"The selected comparison was refused: {notice_text}"
        sync_api.expect(page.get_by_test_id("compare-statistics")).to_be_visible()
        logger.debug("Submitted capture IDs=2 comparison HTTP=%d", status)

    @classmethod
    def require_rows(cls, page: Page) -> None:
        """Require exactly the three normalized MAC keys in the rendered table."""
        logger.info("Check the three rendered comparison device rows")
        rows = page.locator('[data-testid^="compare-device-row-"]')
        sync_api.expect(rows).to_have_count(3)
        markers = rows.evaluate_all("rows => rows.map(row => row.getAttribute('data-testid'))")
        assert isinstance(markers, list) and all(isinstance(marker, str) for marker in markers)
        macs = {marker.removeprefix("compare-device-row-") for marker in markers}
        assert macs == cls.MACS, f"Checked device rows=3. Expected MACs={sorted(cls.MACS)}, received {sorted(macs)}."
        logger.debug("Checked rendered device rows=3 normalized MAC keys=3")


class TestCaptureVersionComparison:
    """Keep the count proof separate from all three required rendered-row proofs."""

    def test_visible_version_change_count(self, page: Page) -> None:
        """Select the exact existing pair and require three visible version changes."""
        CaptureVersionComparison.select_pair(page)
        CaptureVersionComparison.require_rows(page)
        logger.info("Check the visible count of devices with a version change")
        count = page.get_by_test_id("compare-stat-devices-version-changed")
        sync_api.expect(count).to_be_visible()
        sync_api.expect(count).to_have_text("3", use_inner_text=True)
        assert count.inner_text().strip() == "3"
        logger.debug("Checked visible version-change counts=1 expected devices=3")

    @pytest.mark.parametrize("mac", ["000000000001", "000000000002", "000000000003"])
    def test_rendered_version_change_row(self, page: Page, mac: str) -> None:
        """Select the exact existing pair before checking each required device row."""
        CaptureVersionComparison.select_pair(page)
        CaptureVersionComparison.require_rows(page)
        logger.info("Check the rendered version change for device %s", mac)
        row = page.get_by_test_id(f"compare-device-row-{mac}")
        sync_api.expect(row).to_be_visible()
        cells = row.get_by_role("cell")  # The Name header is not a data cell.
        sync_api.expect(cells).to_have_count(3)
        sync_api.expect(cells.nth(2)).to_have_text("version: 0.14.29216 to 0.15.1", use_inner_text=True)
        contents = [" ".join(text.split()) for text in cells.all_text_contents()]
        assert contents == [mac, "changed", "version: 0.14.29216 to 0.15.1"]
        logger.debug("Checked device rows=1 MAC=%s changed outcome=1 version fields=1", mac)
