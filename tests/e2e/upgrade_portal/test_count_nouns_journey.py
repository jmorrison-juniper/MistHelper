"""Browser journey of issue #3449: the picker note and the history note agree with each count.

Why:
    Issue #3449. The organization picker note said "The filter matches 1
    organizations." The history note said "The site holds 1 captures." Each
    second sentence said "This page starts after 0 of them", and the words "of
    them" cannot refer to one item. This journey drives a real browser to the
    picker and to the history page. It reads each whole note, and it saves a
    screenshot of each page for a visual review. The stand-in cloud reaches one
    organization, and the stored-poll seed is the one capture of its site.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import pytest

from tests.e2e.upgrade_portal.conftest import STAND_IN_ORG_NAME, STORED_POLL_SITE_ID, STORED_POLL_SITE_NAME

sync_api = pytest.importorskip("playwright.sync_api", reason="Playwright is not installed.")

logger = logging.getLogger(__name__)

PICKER_PATH = "/select/org"  # The organization picker.
HISTORY_PATH = f"/history?site_id={STORED_POLL_SITE_ID}"  # The history of the site that holds one capture.
PICKER_NOTE_ID = "org-search-note"  # Issue #3449 adds this test identifier to the picker note.
HISTORY_NOTE_ID = "history-count-note"  # Issue #3449 adds this test identifier to the history note.
PICKER_NOTE = (  # The whole picker note for one match.
    "The filter reads the organization name and the organization identifier. The portal filters every "
    "organization that this sign-in may act on, and then shows one page of the matches. The filter matches "
    "1 organization. This page starts after 0 organizations, and one page holds 25 rows."
)
HISTORY_START = f"The list shows the stored captures of {STORED_POLL_SITE_NAME}."  # The fixed first sentence.
HISTORY_NOTE = (  # The whole history note for one capture and the default page size.
    f"{HISTORY_START} The site holds 1 capture. This page starts after 0 captures, and one page holds 25 rows."
)
ONE_ROW_NOTE = (  # The whole history note for one capture and a page size of one row.
    f"{HISTORY_START} The site holds 1 capture. This page starts after 0 captures, and one page holds 1 row."
)
SCREENSHOT_DIRECTORY = (  # The evidence folder of this journey.
    Path(__file__).parents[3] / "test-artifacts" / "upgrade-portal-journeys" / "count-nouns"
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
    logger.info("Save the journey screenshot %s", name)  # Log before the file write.
    page.screenshot(path=str(path), full_page=True)  # Capture the full page for the visual review.
    logger.debug("Saved the journey screenshot %s", path)  # Log after the file write.
    return path  # The caller proves that the file exists.


def test_the_picker_note_names_one_matching_organization(page: Any) -> None:
    """A filter that keeps the one stand-in organization says "1 organization"."""
    logger.info("Open the organization picker")  # Log before the open.
    page.goto(PICKER_PATH, wait_until="domcontentloaded")  # The signed-in operator opens the picker.
    page.get_by_test_id("org-search").fill(STAND_IN_ORG_NAME)  # The operator types the whole organization name.
    page.get_by_test_id("org-search-submit").click()  # The portal filters every page.
    page.wait_for_url(re.compile(r".*/select/org\?q=.*"))  # The filter reached the portal.
    assert save_screenshot(page, "picker-one-match.png").exists()  # The screenshot comes before the compare.
    sync_api.expect(page.get_by_test_id(PICKER_NOTE_ID)).to_have_text(PICKER_NOTE)  # The whole note.
    logger.debug("The picker note agrees with one match")  # Log after the compare.


def test_the_history_note_names_one_capture(page: Any) -> None:
    """The history of a site that holds one capture says "1 capture"."""
    logger.info("Open the history of the site %s", STORED_POLL_SITE_ID)  # Log before the open.
    page.goto(HISTORY_PATH, wait_until="domcontentloaded")  # The operator opens the history of the site.
    assert save_screenshot(page, "history-one-capture.png").exists()  # The screenshot comes before the compare.
    sync_api.expect(page.get_by_test_id(HISTORY_NOTE_ID)).to_have_text(HISTORY_NOTE)  # The whole note.
    logger.debug("The history note agrees with one capture")  # Log after the compare.


def test_the_history_note_names_a_page_of_one_row(page: Any) -> None:
    """A page size of one says "1 row"."""
    logger.info("Open the history of the site %s with a page of one row", STORED_POLL_SITE_ID)  # Log first.
    page.goto(f"{HISTORY_PATH}&limit=1", wait_until="domcontentloaded")  # A hand-edited link asks for one row.
    assert save_screenshot(page, "history-one-row.png").exists()  # The screenshot comes before the compare.
    sync_api.expect(page.get_by_test_id(HISTORY_NOTE_ID)).to_have_text(ONE_ROW_NOTE)  # The whole note.
    logger.debug("The history note agrees with a page of one row")  # Log after the compare.
