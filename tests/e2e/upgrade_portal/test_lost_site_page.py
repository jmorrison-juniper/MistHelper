"""Browser journeys for a site picker whose cloud reads lose page two.

Why:
    Issue #3438. The site picker read each list through ``mistapi.get_all``.
    That helper adds a later page with no status check. A lost later page left
    a short site list that read as whole, and a device count of 0 for a site
    with devices. The picker now names each read that lost a page with a
    Caution note. These journeys drive a real browser through both modes and
    through the site list answer. The cloud session of the lost-page operator
    answers page one of each read and loses page two, so the real page walk of
    the portal runs. A screenshot records each page for a visual review. No
    journey sends a firmware request.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import pytest

from tests.e2e.upgrade_portal.lost_page_seeds import (
    LOST_NORTH_DEVICES,
    LOST_NORTH_ID,
    LOST_NORTH_NAME,
    LOST_SOUTH_DEVICES,
    LOST_SOUTH_ID,
    LOST_SOUTH_NAME,
)

sync_api = pytest.importorskip("playwright.sync_api", reason="Playwright is not installed.")

logger = logging.getLogger(__name__)  # The journey steps reach the pytest log.

MODE_PATH = "/select/mode"  # The mode chooser, where each journey starts.
SITES_API_PATH = "/api/sites"  # The site list answer. The session names the organization.
SITE_LIST_NOTE_ID = "site-list-partial"  # The Caution note of the site read.
SITE_COUNT_NOTE_ID = "site-count-partial"  # The Caution note of the device count read.
SITE_LIST_NOTE_TEXT = (  # The exact text of the note of the site read.
    "The portal did not read the complete site list. The list can leave out sites. "
    "Reload this page to read the list again."
)
SITE_COUNT_NOTE_TEXT = (  # The exact text of the note of the device count read.
    "The portal did not read every device count. A site can show 0 devices when it holds devices. "
    "Reload this page to read the counts again."
)
NOTES = ((SITE_LIST_NOTE_ID, SITE_LIST_NOTE_TEXT), (SITE_COUNT_NOTE_ID, SITE_COUNT_NOTE_TEXT))  # Both notes.
CAUTION_PREFIX = '"Caution: "'  # The value that `portal.css` gives the prefix of a caution.
PREFIX_SCRIPT = "(node) => getComputedStyle(node, '::before').content"  # Read the prefix of one note.
SITE_ROW_SELECTOR = '[data-testid^="site-row-"]'  # One table row for each site that the walk kept.
COUNT_CELL_SELECTOR = "td.cell-number"  # The device count cell of one site row.
KEPT_SITES = {LOST_NORTH_ID: LOST_NORTH_DEVICES, LOST_SOUTH_ID: LOST_SOUTH_DEVICES}  # The rows of page one.
TARGET_VERSION = "0.15.1"  # The newer version that the stand-in cloud offers for every model.
DEVICE_TYPES = ("ap", "switch", "gateway")  # The three device types of the multi-site form.
VERSION_FIELD_IDS = ("org-upgrade-version", "org-upgrade-switch-version", "org-upgrade-gateway-version")
CHOSEN_STRATEGY = "serial"  # Neither the form default nor the service default, so a reset shows on the page.
FETCH_SCRIPT = """async (path) => {
    const answer = await fetch(path, {headers: {Accept: "application/json"}});
    return {status: answer.status, body: await answer.json()};
}"""  # The browser reads the site list answer with its own session cookies.
OK_STATUS = 200  # A site list read answers 200, also when a read lost a page.
ROW_FIELDS = {"site_id", "name", "device_count", "locked_by", "lock_state"}  # The five fields of one site row.
SCREENSHOT_DIRECTORY = (  # The evidence folder of these journeys.
    Path(__file__).parents[3] / "data" / "test-artifacts" / "upgrade-portal-journeys" / "lost-site-page"
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
    logger.info("Save the screenshot %s", path.name)  # Record the capture before it runs.
    page.screenshot(path=str(path), full_page=True)  # Capture the full page for the visual review.
    logger.debug("Saved the screenshot %s", path.name)  # Record the capture after it ends.
    return path  # The caller proves that the file exists.


def open_the_site_picker(page: Any, mode_control: str) -> None:
    """Choose one mode and open the site picker.

    Args:
        page: The browser page.
        mode_control: The test identifier of the mode choice.
    """
    logger.info("Open the site picker with the mode control %s", mode_control)  # Record the step first.
    page.goto(MODE_PATH, wait_until="domcontentloaded")  # Start at the mode chooser with a signed session.
    page.get_by_test_id(mode_control).check()  # Choose the mode of this journey.
    page.get_by_test_id("mode-continue").click()  # Move to the site picker.
    page.wait_for_url(re.compile(r".*/select/site$"))  # Wait until the site picker owns the page.
    logger.debug("The site picker owns the page")  # Record the result of the step.


def assert_both_notes_sit_above(page: Any, anchor_id: str) -> None:
    """Prove that both notes show the exact text and the Caution prefix above one element.

    Args:
        page: The browser page, on the site picker.
        anchor_id: The test identifier of the element that each note must sit above.
    """
    logger.info("Read the two Caution notes above %s", anchor_id)  # Record the step before the reads.
    anchor_top = page.get_by_test_id(anchor_id).bounding_box()["y"]  # The top edge of the table or the form.
    for note_id, text in NOTES:  # The note of the site read, then the note of the device count read.
        note = page.get_by_test_id(note_id)  # One note of the picker.
        sync_api.expect(note).to_have_text(text)  # The exact text, with the reload instruction.
        assert note.evaluate(PREFIX_SCRIPT) == CAUTION_PREFIX  # A reload recovers the read, so Caution.
        assert note.bounding_box()["y"] < anchor_top  # The operator reads the note before the rows.
    logger.debug("Both Caution notes sit above %s", anchor_id)  # Record the result of the step.


def assert_the_kept_rows(page: Any) -> None:
    """Prove that the picker shows the two rows of page one with their device counts.

    Args:
        page: The browser page, on the site picker.
    """
    logger.info("Read the site rows that the page walk kept")  # Record the step before the reads.
    sync_api.expect(page.locator(SITE_ROW_SELECTOR)).to_have_count(len(KEPT_SITES))  # Page one only.
    for site_id, device_count in KEPT_SITES.items():  # Each row keeps the count of page one.
        cell = page.get_by_test_id(f"site-row-{site_id}").locator(COUNT_CELL_SELECTOR)  # The count cell.
        sync_api.expect(cell).to_have_text(str(device_count))  # The count that the cloud reported.
    logger.debug("The picker shows %s kept row(s)", len(KEPT_SITES))  # Record the result of the step.


def fill_the_plan(page: Any) -> None:
    """Check each device type, type one version for each type, and choose the serial strategy.

    Args:
        page: The browser page, on the multi-site options form.
    """
    logger.info("Fill the multi-site plan")  # Record the step before the first control changes.
    for device_type in DEVICE_TYPES:  # A checked type shows its version field.
        page.get_by_test_id(f"org-upgrade-type-{device_type}").check()  # A checked box stays checked.
    for field_id in VERSION_FIELD_IDS:  # The selected site holds one device of each type.
        page.get_by_test_id(field_id).fill(TARGET_VERSION)  # The newer version of every stand-in model.
    page.get_by_test_id(f"org-strategy-{CHOSEN_STRATEGY}").check()  # A choice that a reset would lose.
    logger.debug("The multi-site plan holds %s device type(s)", len(DEVICE_TYPES))  # Record the result.


def test_the_multi_site_picker_names_both_reads_and_the_plan_moves_on(lost_page_operator_page: Any) -> None:
    """Both notes sit above the form, and a site of page one reaches the confirm page."""
    page = lost_page_operator_page  # The separate operator, so no other journey sees the lost pages.
    open_the_site_picker(page, "mode-multi-site")  # Choose the multi-site mode.
    assert_both_notes_sit_above(page, "multi-site-form")  # The notes sit above the check boxes.
    assert_the_kept_rows(page)  # The rows of page one, with the counts of page one.
    page.get_by_test_id(f"site-select-{LOST_NORTH_ID}").check()  # Select a site that the walk kept.
    assert save_screenshot(page, "multi-site-picker.png").exists()  # The two notes above the form.
    page.get_by_test_id("multi-site-continue").click()  # Store the site set.
    page.wait_for_url(re.compile(r".*/upgrade/org/options$"))  # The forward post still works.
    summary = page.get_by_test_id("org-upgrade-site-summary")  # The table of the selected sites.
    sync_api.expect(summary).to_contain_text(LOST_NORTH_NAME)  # The site of page one, by name.
    sync_api.expect(summary).not_to_contain_text(LOST_SOUTH_NAME)  # The site that the operator did not select.
    assert save_screenshot(page, "multi-site-options.png").exists()  # The options form of one site.
    fill_the_plan(page)  # Type the plan of the operator.
    page.get_by_test_id("org-upgrade-review").click()  # Save the plan.
    page.wait_for_url(re.compile(r".*/upgrade/org/confirm$"))  # The save accepted the plan.
    sync_api.expect(page.get_by_test_id("org-upgrade-confirm")).to_contain_text("Sites: 1")  # One site.
    row = page.get_by_test_id(f"org-upgrade-precheck-row-{LOST_NORTH_ID}")  # The pre-check row of the site.
    sync_api.expect(row).to_contain_text(LOST_NORTH_NAME)  # The confirm page names the site of page one.
    assert save_screenshot(page, "multi-site-confirm.png").exists()  # The summary before the typed word.


def test_the_single_site_picker_names_both_reads_and_opens_a_kept_site(lost_page_operator_page: Any) -> None:
    """Both notes sit above the table, and the operator opens a site of page one."""
    page = lost_page_operator_page  # The separate operator, so no other journey sees the lost pages.
    open_the_site_picker(page, "mode-single-site")  # Choose the single-site mode.
    assert_both_notes_sit_above(page, "site-table")  # The notes sit above the table.
    assert_the_kept_rows(page)  # The rows of page one, with the counts of page one.
    assert save_screenshot(page, "single-site-picker.png").exists()  # The two notes above the table.
    page.get_by_test_id(f"site-open-{LOST_NORTH_ID}").click()  # Open a site that the walk kept.
    page.wait_for_url(re.compile(rf".*/select/site/{LOST_NORTH_ID}$"))  # The inventory page of the site.
    sync_api.expect(page.get_by_test_id("inventory-table")).to_be_visible()  # The device list of the site.
    assert save_screenshot(page, "single-site-inventory.png").exists()  # The inventory of a kept site.


def test_a_reload_reads_both_lists_again(lost_page_operator_page: Any) -> None:
    """A reload reads each list again, so both notes stay while the cloud still loses page two.

    Why:
        The cache keeps a whole read only. A kept short read would answer the
        reload with no partial reason. The notes would then go away, and the
        list would stay short.
    """
    page = lost_page_operator_page  # The separate operator, so no other journey sees the lost pages.
    open_the_site_picker(page, "mode-single-site")  # The first read of both lists.
    page.reload(wait_until="domcontentloaded")  # The instruction of both notes.
    assert_both_notes_sit_above(page, "site-table")  # The second read also lost page two.
    assert_the_kept_rows(page)  # The rows of page one stay.
    assert save_screenshot(page, "single-site-picker-reload.png").exists()  # The notes after the reload.


def test_the_site_list_answer_names_both_lost_reads(lost_page_operator_page: Any) -> None:
    """The site list answer holds two false fields, and the rows of page one keep their shape."""
    page = lost_page_operator_page  # The separate operator, so no other journey sees the lost pages.
    page.goto(MODE_PATH, wait_until="domcontentloaded")  # A portal page, so the read carries the session.
    logger.info("Read the site list answer in the browser")  # Record the step before the read.
    answer = page.evaluate(FETCH_SCRIPT, SITES_API_PATH)  # The same read that a script sends.
    logger.debug("The site list answer has the status %s", answer["status"])  # Record the status only.
    body = answer["body"]  # The rows and the two completeness fields.
    assert answer["status"] == OK_STATUS  # A lost page never turns the read into a refusal.
    assert body["site_list_complete"] is False  # The site read lost page two.
    assert body["device_counts_complete"] is False  # The device count read lost page two.
    assert {row["site_id"]: row["device_count"] for row in body["sites"]} == KEPT_SITES  # The rows of page one.
    assert all(set(row) == ROW_FIELDS for row in body["sites"])  # The two new fields leave each row unchanged.
