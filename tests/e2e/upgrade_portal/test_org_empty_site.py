"""Browser journey for a multi-site plan that selects a site with no device.

Why:
    Issue #3389. The multi-site save kept the options of the last selected
    site only. A site with no device answers an empty record, so the choices
    of the operator became the defaults when that site came last. This journey
    drives a real browser through the refusal and through the recovery. A
    screenshot records each page for a visual review. The stand-in cloud of
    the browser fixtures answers every read, so the journey sends no firmware
    request.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

from tests.e2e.upgrade_portal.empty_site_seeds import EMPTY_SITE_ID, EMPTY_SITE_NAME

sync_api = pytest.importorskip("playwright.sync_api", reason="Playwright is not installed.")

MODE_PATH = "/select/mode"  # The mode chooser, where the journey starts.
SITE_ID = "22222222-2222-2222-2222-222222222222"  # The first stand-in site, which holds one device of each type.
TARGET_VERSION = "0.15.1"  # The newer version that the stand-in cloud offers for every model.
DEVICE_TYPES = ("ap", "switch", "gateway")  # The three device types of the multi-site form.
VERSION_FIELD_IDS = ("org-upgrade-version", "org-upgrade-switch-version", "org-upgrade-gateway-version")
CHOSEN_STRATEGY = "serial"  # Neither the form default nor the service default, so a reset shows on the page.
UNREAD_TEXT = f"The portal read no device at these sites: {EMPTY_SITE_NAME}."  # The start of the refusal.
SCREENSHOT_DIRECTORY = (  # The evidence folder of this journey.
    Path(__file__).parents[3] / "data" / "test-artifacts" / "upgrade-portal-journeys" / "org-empty-site"
)


def save_screenshot(page: Any, name: str) -> Path:
    """Save one journey screenshot.

    Args:
        page: The browser page.
        name: The file name of the screenshot.

    Returns:
        The path of the saved file.
    """
    SCREENSHOT_DIRECTORY.mkdir(parents=True, exist_ok=True)  # Keep the evidence under the repository data tree.
    path = SCREENSHOT_DIRECTORY / name  # One stable file name for each page state.
    page.screenshot(path=str(path), full_page=True)  # Capture the full page for the visual review.
    return path  # The caller proves that the file exists.


def open_the_site_picker(page: Any) -> None:
    """Choose the multi-site mode and open the site picker.

    Args:
        page: The browser page.
    """
    page.goto(MODE_PATH, wait_until="domcontentloaded")  # Start at the mode chooser with a signed session.
    page.get_by_test_id("mode-multi-site").check()  # Choose the multi-site mode.
    page.get_by_test_id("mode-continue").click()  # Move to the site picker.
    page.wait_for_url(re.compile(r".*/select/site$"))  # Wait until the site picker owns the page.


def continue_to_the_options(page: Any) -> None:
    """Send the site choice and wait for the multi-site options form.

    Args:
        page: The browser page.
    """
    page.get_by_test_id("multi-site-continue").click()  # Store the site set.
    page.wait_for_url(re.compile(r".*/upgrade/org/options$"))  # Wait until the form script is ready.


def fill_the_plan(page: Any) -> None:
    """Check each device type, type one version for each type, and choose the serial strategy.

    Args:
        page: The browser page.
    """
    for device_type in DEVICE_TYPES:  # A checked type shows its version field.
        page.get_by_test_id(f"org-upgrade-type-{device_type}").check()  # A checked box stays checked.
    for field_id in VERSION_FIELD_IDS:  # The first site holds one device of each type.
        page.get_by_test_id(field_id).fill(TARGET_VERSION)  # The newer version of every stand-in model.
    page.get_by_test_id(f"org-strategy-{CHOSEN_STRATEGY}").check()  # The choice that the old save lost.


def test_an_empty_last_site_stops_the_save_and_the_operator_recovers(empty_site_operator_page: Any) -> None:
    """The save names the empty site, and the plan keeps each choice after the operator clears that site."""
    page = empty_site_operator_page  # The separate operator, so no other journey sees the empty site.
    open_the_site_picker(page)  # Choose the multi-site mode.
    empty_row = page.get_by_test_id(f"site-row-{EMPTY_SITE_ID}")  # The last row of the picker.
    sync_api.expect(empty_row.locator("td.cell-number")).to_have_text("0")  # The picker shows zero devices.
    page.get_by_test_id(f"site-select-{SITE_ID}").check()  # Select a site that holds devices.
    page.get_by_test_id(f"site-select-{EMPTY_SITE_ID}").check()  # Select the empty site, which comes last.
    assert save_screenshot(page, "picker-with-empty-site.png").exists()  # The two selected sites.
    continue_to_the_options(page)  # Open the shared options form.
    fill_the_plan(page)  # Type the plan of the operator.
    page.get_by_test_id("org-upgrade-review").click()  # Try to save the plan.
    flash = page.get_by_test_id("flash-message")  # The shared message region of the layout.
    sync_api.expect(flash).to_contain_text(UNREAD_TEXT)  # The refusal names the empty site.
    sync_api.expect(flash).to_contain_text("clear that site on the Sites page")  # The refusal names the repair.
    sync_api.expect(flash).not_to_contain_text(EMPTY_SITE_ID)  # The site name replaces the identifier.
    assert re.search(r".*/upgrade/org/options$", page.url)  # The page stays on the form, so no plan exists.
    assert save_screenshot(page, "empty-site-refusal.png").exists()  # The refusal on the form.
    page.get_by_test_id("nav-sites").click()  # Follow the refusal to the Sites page.
    page.wait_for_url(re.compile(r".*/select/site$"))  # Wait until the site picker owns the page.
    empty_box = page.get_by_test_id(f"site-select-{EMPTY_SITE_ID}")  # The box of the empty site.
    sync_api.expect(empty_box).to_be_checked()  # The picker keeps the stored site set.
    empty_box.uncheck()  # Clear the empty site, as the refusal tells the operator.
    continue_to_the_options(page)  # Open the form again with one site.
    fill_the_plan(page)  # The refused save stored no options, so the operator types the plan again.
    page.get_by_test_id("org-upgrade-review").click()  # Save the plan.
    page.wait_for_url(re.compile(r".*/upgrade/org/confirm$"))  # The save accepted the plan.
    confirm = page.get_by_test_id("org-upgrade-confirm")  # The summary card of the confirm page.
    sync_api.expect(confirm).to_contain_text(f"Strategy: {CHOSEN_STRATEGY}")  # The choice, not a default.
    sync_api.expect(confirm).to_contain_text("Sites: 1")  # The plan covers the one site that holds devices.
    sync_api.expect(page.get_by_test_id(f"org-upgrade-precheck-row-{SITE_ID}")).to_be_visible()  # The site row.
    sync_api.expect(page.get_by_test_id(f"org-upgrade-precheck-row-{EMPTY_SITE_ID}")).to_have_count(0)  # No row.
    assert save_screenshot(page, "recovered-confirm.png").exists()  # The summary before the typed word.
