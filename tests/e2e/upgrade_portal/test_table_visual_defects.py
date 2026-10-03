"""Browser coverage for the organization, site, and device table defects of #3216."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

from tests.e2e.upgrade_portal.empty_site_seeds import EMPTY_SITE_ID

sync_api = pytest.importorskip("playwright.sync_api", reason="Playwright is not installed.")

MODE_PATH = "/select/mode"
ORG_PATH = "/select/org"
SITE_ID = "22222222-2222-2222-2222-222222222222"
SCREENSHOT_DIRECTORY = Path(__file__).parents[3] / "test-artifacts" / "upgrade-portal-journeys" / "issue-3216"


def save_screenshot(page: Any, name: str) -> Path:
    """Save one screenshot for the issue acceptance evidence."""
    SCREENSHOT_DIRECTORY.mkdir(parents=True, exist_ok=True)  # Keep evidence in the ignored test-artifacts tree.
    path = SCREENSHOT_DIRECTORY / name  # Use one stable path for each affected page.
    page.screenshot(path=str(path), full_page=True)  # Capture the complete page, including table layout.
    return path  # The caller proves that the screenshot exists.


def computed_style(page: Any, selector: str, property_name: str) -> str:
    """Read one computed style from a visible table cell."""
    return str(
        page.locator(selector).first.evaluate(
            "(node, propertyName) => getComputedStyle(node).getPropertyValue(propertyName)",
            property_name,
        )
    )  # Browser styles prove the rendered result, not only the stylesheet text.


def open_multi_site_picker(page: Any) -> None:
    """Open the multi-site site picker."""
    page.goto(MODE_PATH, wait_until="domcontentloaded")  # Start at the mode page with the signed test session.
    page.get_by_test_id("mode-multi-site").check()  # Choose the page that owns the site table.
    page.get_by_test_id("mode-continue").click()  # Submit the mode choice.
    page.wait_for_url(re.compile(r".*/select/site$"))  # Wait for the site picker route.


def test_table_visual_defects_are_fixed(page: Any, empty_site_operator_page: Any) -> None:
    """Prove the reported colors, text, sorting, filtering, and layout fixes."""
    page.goto(ORG_PATH, wait_until="domcontentloaded")  # Open the organization table.
    page.get_by_test_id("org-search").fill("E2E Stand-In Organization")  # Leave one organization match.
    page.get_by_test_id("org-search-submit").click()  # Apply the server-side organization filter.
    note = page.get_by_test_id("org-search-note")  # Read the count sentence beside the search field.
    sync_api.expect(note).to_contain_text("The filter matches 1 organization.")  # Keep the singular noun.
    sync_api.expect(note).not_to_contain_text("1 organizations")  # Reject the reported grammar defect.
    sync_api.expect(page.get_by_test_id("org-search")).to_have_attribute(
        "placeholder", "Type an organization name"
    )  # Keep the full placeholder visible to the operator.
    org_row = page.locator('[data-testid^="org-row-"]').first  # Read one organization row.
    org_header = org_row.locator("th[scope='row']")  # The first column must use table-cell styling.
    org_cell = org_row.locator("td").first  # Compare it with a data cell in the same row.
    assert computed_style(page, '[data-testid^="org-row-"] th[scope="row"]', "background-color") == computed_style(
        page, '[data-testid^="org-row-"] td', "background-color"
    )  # The row has one surface color.
    assert org_header.evaluate("(node) => getComputedStyle(node).textAlign") == "left"  # The row header aligns left.
    assert org_cell.is_visible()  # The table still renders its identifier cell.
    assert save_screenshot(page, "organizations.png").exists()  # Keep visual evidence for the organization page.

    page = empty_site_operator_page  # Use the fixture with one zero-device site.
    open_multi_site_picker(page)  # Open the site table.
    site_rows = page.locator('[data-testid^="site-row-"]')  # Read all dynamic site rows.
    names = site_rows.locator("th[scope='row']").all_text_contents()  # Read the displayed site order.
    assert names == sorted(names, key=str.casefold)  # The site list is predictable by name.
    site_row = site_rows.first  # Read one non-empty site row for the color and alignment proof.
    assert computed_style(page, '[data-testid^="site-row-"] th[scope="row"]', "background-color") == computed_style(
        page, '[data-testid^="site-row-"] td', "background-color"
    )  # The site row has one surface color.
    assert (
        site_row.locator("th[scope='row']").evaluate("(node) => getComputedStyle(node).textAlign") == "left"
    )  # Align names left.
    sync_api.expect(page.get_by_test_id("multi-site-continue")).to_be_visible()  # Keep Continue visible.
    page.get_by_test_id("site-has-devices").check()  # Enable the reported device-count filter.
    sync_api.expect(page.get_by_test_id(f"site-row-{EMPTY_SITE_ID}")).to_be_hidden()  # Hide the zero-device site.
    visible_rows = page.locator('[data-testid^="site-row-"]:visible')  # Read the rows that remain after filtering.
    assert visible_rows.count() > 0  # The filter keeps sites with devices.
    assert visible_rows.locator("[data-device-count='0']").count() == 0  # No visible row has zero devices.
    page.locator("#site-table thead th").first.click()  # Exercise the browser sort control.
    sync_api.expect(page.locator("#site-table thead th").first).to_have_attribute(
        "aria-sort", "ascending"
    )  # Name sort is active.
    assert save_screenshot(page, "sites.png").exists()  # Keep visual evidence for the site page.

    page.get_by_test_id(f"site-select-{SITE_ID}").check()  # Select one populated site for the options page.
    page.get_by_test_id("multi-site-continue").click()  # Open the multi-site device table.
    page.wait_for_url(re.compile(r".*/upgrade/org/options$"))  # Wait for the options route.
    device_table = page.get_by_test_id("org-upgrade-device-summary")  # Read the multi-site device table.
    sync_api.expect(device_table).to_be_visible()  # The selected site must provide device rows.
    assert computed_style(
        page,
        '[data-testid="org-upgrade-device-summary"] tbody th[scope="row"]',
        "background-color",
    ) == computed_style(
        page,
        '[data-testid="org-upgrade-device-summary"] tbody td',
        "background-color",
    )  # The first device column uses the row surface color.
    assert (
        page.locator('[data-testid="org-upgrade-device-summary"] tbody th[scope="row"]').first.evaluate(
            "(node) => getComputedStyle(node).textAlign"
        )
        == "left"
    )  # Device names align left.
    assert save_screenshot(page, "options.png").exists()  # Keep visual evidence for the device page.
