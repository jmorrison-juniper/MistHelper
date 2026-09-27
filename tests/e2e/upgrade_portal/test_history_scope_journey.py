"""Browser journey of issue #3482: the capture history with no site names every site.

Why:
    Issue #3482. The history page with no site read the site name of its first
    row. For the captures of two sites, the note said "The list shows the
    stored captures of E2E Stand-In Site. The site holds 5 captures." The
    hidden caption of the table said "The stored captures of the site." This
    journey drives a real browser to the page with no site and to the page of
    one site. It reads each whole note and each caption, and it saves a
    screenshot of each page for a visual review.

    Many journeys share the browser test server, and some of them store a
    capture. The count of the page with no site therefore depends on the order
    of the tests, so the journey reads that count as a pattern.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import pytest

from tests.e2e.upgrade_portal.conftest import (
    SECOND_SITE_NAME,
    STAND_IN_SITE_NAME,
    STORED_POLL_SITE_ID,
    STORED_POLL_SITE_NAME,
)

sync_api = pytest.importorskip("playwright.sync_api", reason="Playwright is not installed.")

logger = logging.getLogger(__name__)

EVERY_SITE_PATH = "/history"  # The history with no site, which lists the captures of every site.
ONE_SITE_PATH = f"/history?site_id={STORED_POLL_SITE_ID}"  # The history of the site that holds one capture.
NOTE_ID = "history-count-note"  # Issue #3449 added this test identifier to the note.
TABLE_ID = "history-table"  # The capture table, which holds the hidden caption.
EVERY_SITE_NOTE = re.compile(  # The whole note of the page with no site, for any count of captures.
    r"The list shows the stored captures of every site\. The portal holds (?:1 capture|\d+ captures)\. "
    r"This page starts after 0 captures, and one page holds 25 rows\."
)
ONE_SITE_NOTE = (  # The whole note of the page of one site, which does not change.
    f"The list shows the stored captures of {STORED_POLL_SITE_NAME}. The site holds 1 capture. "
    "This page starts after 0 captures, and one page holds 25 rows."
)
EVERY_SITE_CAPTION = "The stored captures of every site. "  # The first sentence of the caption with no site.
ONE_SITE_CAPTION = "The stored captures of the site. "  # The first sentence of the caption of one site.
SCREENSHOT_DIRECTORY = (  # The evidence folder of this journey.
    Path(__file__).parents[3] / "data" / "test-artifacts" / "upgrade-portal-journeys" / "history-scope"
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


def folded_text(locator: Any) -> str:
    """Return the text of one element with one space between each word.

    Why:
        Playwright folds the white space of the text only when the expected
        value is a string. A pattern compare reads the raw text, and the
        template wraps each sentence across lines.

    Args:
        locator: The element to read.

    Returns:
        The folded text.
    """
    sync_api.expect(locator).to_have_count(1)  # One element, and the wait covers a slow page.
    return " ".join((locator.text_content() or "").split())  # One space between each word.


def test_the_history_with_no_site_names_every_site(page: Any) -> None:
    """The note and the caption of the page with no site name every site."""
    logger.info("Open the capture history with no site")  # Log before the open.
    page.goto(EVERY_SITE_PATH, wait_until="domcontentloaded")  # The operator opens the history of every site.
    assert save_screenshot(page, "history-every-site.png").exists()  # The screenshot comes before the compare.
    note = folded_text(page.get_by_test_id(NOTE_ID))  # The whole note of the Captures card.
    for site_name in (STAND_IN_SITE_NAME, SECOND_SITE_NAME, STORED_POLL_SITE_NAME):  # Each seeded site name.
        assert site_name not in note, f"The note of every site names one site: {note}"  # The report of #3482.
    assert EVERY_SITE_NOTE.fullmatch(note), f"The note of every site is wrong: {note}"  # Every word of the note.
    caption = folded_text(page.get_by_test_id(TABLE_ID).locator("caption"))  # The hidden caption of the table.
    assert caption.startswith(EVERY_SITE_CAPTION), f"The caption of every site is wrong: {caption}"  # FR-004.
    logger.debug("The history with no site names every site")  # Log after the compare.


def test_the_history_of_one_site_names_the_site(page: Any) -> None:
    """The note and the caption of the page of one site keep the site name."""
    logger.info("Open the history of the site %s", STORED_POLL_SITE_ID)  # Log before the open.
    page.goto(ONE_SITE_PATH, wait_until="domcontentloaded")  # The operator opens the history of one site.
    assert save_screenshot(page, "history-one-site.png").exists()  # The screenshot comes before the compare.
    sync_api.expect(page.get_by_test_id(NOTE_ID)).to_have_text(ONE_SITE_NOTE)  # The whole note does not change.
    caption = folded_text(page.get_by_test_id(TABLE_ID).locator("caption"))  # The hidden caption of the table.
    assert caption.startswith(ONE_SITE_CAPTION), f"The caption of one site is wrong: {caption}"  # No change.
    logger.debug("The history of one site names the site")  # Log after the compare.
