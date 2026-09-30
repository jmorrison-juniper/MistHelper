"""Browser journey of issue #3486: the Captures table of the history with no site names the site of each row.

Why:
    Issue #3486. The history page with no site lists the stored captures of
    every site in one table, and no column named the site of a row. The
    browser fixtures put 5 captures on 2 sites, and no cell showed the
    difference. This journey drives a real browser to the page with no site.
    It reads the Site header, the site cell of each seed capture, the height
    of each row at three window widths, the fit of each header at 1280 pixels,
    and the row order after a press of the Site header. It then opens the page
    of one site and reads the nine headers of today. Each page saves a
    screenshot for a visual review.

    Many journeys share the browser test server, and some of them store a
    capture. The journey therefore asks for a page of 200 rows, and it reads
    the rows of the five seed captures by their identifiers.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pytest

from tests.e2e.upgrade_portal.conftest import (
    POST_CAPTURE_ID,
    PRE_CAPTURE_ID,
    STAND_IN_SITE_NAME,
    STANDALONE_PRE_CAPTURE_ID,
    STORED_POLL_CAPTURE_ID,
    STORED_POLL_SITE_ID,
    STORED_POLL_SITE_NAME,
    TIER3_CAPTURE_ID,
)

sync_api = pytest.importorskip("playwright.sync_api", reason="Playwright is not installed.")

logger = logging.getLogger(__name__)

EVERY_SITE_PATH = "/history?limit=200"  # The history with no site. The largest page holds every seed row.
ONE_SITE_PATH = f"/history?site_id={STORED_POLL_SITE_ID}"  # The history of the site that holds one capture.
TABLE_ID = "history-table"  # The Captures table.
SEED_SITE_NAMES = {  # The site name that each seed capture stores, in the order of the seed stamps.
    PRE_CAPTURE_ID: STAND_IN_SITE_NAME,
    STANDALONE_PRE_CAPTURE_ID: STAND_IN_SITE_NAME,
    POST_CAPTURE_ID: STAND_IN_SITE_NAME,
    STORED_POLL_CAPTURE_ID: STORED_POLL_SITE_NAME,
    TIER3_CAPTURE_ID: STAND_IN_SITE_NAME,
}
EVERY_SITE_HEADERS = [  # FR-001: the Site column follows the Capture column.
    "Capture",
    "Site",
    "Started",
    "Role",
    "State",
    "Devices",
    "Device types",
    "Clients",
    "Stored size",
    "Action",
]
ONE_SITE_HEADERS = [header for header in EVERY_SITE_HEADERS if header != "Site"]  # FR-006: the nine of today.
EVERY_SITE_CAPTION = (  # FR-005: the whole hidden caption of the page with no site.
    "The stored captures of every site. Each row holds the site, the moment, the role, the state, "
    "the device count, the device types, the client count, and the stored size."
)
SORT_ARROWS = "\u2195\u25b2\u25bc"  # The three arrows that portal.js appends to a sortable header.
SITE_HEADER_INDEX = 1  # The Site header is the second header of the table.
WINDOW_WIDTHS = (1024, 1280, 1440)  # A narrow window, the width of SC-004, and a wide window.
WINDOW_HEIGHT = 900  # One height for every window, so each screenshot reads the same way.
OPEN_HEIGHT_CEILING = 40  # tests/e2e/upgrade_portal/test_history_layout.py holds the same limit.
OPEN_WIDTH_FLOOR = 50  # A narrower control prints its word across two lines.
ROW_HEIGHT_CEILING = 48  # The row height budget of issue #2106.
HEADER_WINDOW_WIDTH = 1280  # SC-005 names this width. Each header of the table of one site fits it.
HEADER_FIT_TOLERANCE = 1  # The browser rounds the cell width to a whole pixel, and the range width is exact.
HEADER_FIT_SCRIPT = """
table => [...table.querySelectorAll('thead th')].map(header => {
  const range = document.createRange();
  range.selectNodeContents(header);
  const style = getComputedStyle(header);
  const padding = parseFloat(style.paddingLeft) + parseFloat(style.paddingRight);
  return {need: range.getBoundingClientRect().width + padding, given: header.clientWidth};
})
"""  # A range measures the header text and its sort arrow, and the cell width does not change the measure.
SCREENSHOT_DIRECTORY = (  # The evidence folder of this journey.
    Path(__file__).parents[3] / "test-artifacts" / "upgrade-portal-journeys" / "history-site-column"
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


def open_history(page: Any, path: str, width: int = 1280) -> None:
    """Open one history page at one window width, and log the load time.

    Args:
        page: The browser page.
        path: The address of the history page.
        width: The window width in pixels.
    """
    logger.info("Open %s at a window width of %s pixels", path, width)  # Log before the open.
    page.set_viewport_size({"width": width, "height": WINDOW_HEIGHT})  # The window of this check.
    page.goto(path, wait_until="load")  # The load event comes after portal.js prepares each sort header.
    sync_api.expect(page.get_by_test_id(TABLE_ID)).to_be_visible()  # The Captures table is on the page.
    duration = page.evaluate("() => performance.getEntriesByType('navigation')[0].duration")  # The load time.
    logger.debug("The history page %s loaded in %.0f milliseconds", path, duration)  # The performance record.


def header_names(page: Any) -> list[str]:
    """Return the name of each column header of the Captures table.

    Why:
        portal.js appends an arrow to each sortable header. The arrow names
        the sort state, and it is not a part of the column name.

    Args:
        page: The browser page.

    Returns:
        The header names, in column order.
    """
    texts = page.get_by_test_id(TABLE_ID).locator("thead th").all_text_contents()  # The raw header texts.
    return [" ".join(text.split()).strip(SORT_ARROWS).strip() for text in texts]  # No arrow, one space.


def row_order(page: Any) -> list[str]:
    """Return the test identifier of each row of the Captures table, in page order.

    Args:
        page: The browser page.

    Returns:
        The row test identifiers.
    """
    rows = page.get_by_test_id(TABLE_ID).locator("tbody tr")  # The rows of the Captures table.
    script = "rows => rows.map(row => row.getAttribute('data-testid') || '')"  # One read for every row.
    return list(rows.evaluate_all(script))  # The identifiers, in the order that the browser shows.


def box_of(locator: Any) -> dict[str, float]:
    """Return the painted box of one element.

    Args:
        locator: The element to measure.

    Returns:
        The box, with the keys x, y, width, and height.
    """
    sync_api.expect(locator).to_have_count(1)  # One element, and the wait covers a slow page.
    box = locator.bounding_box()  # The box that the browser painted.
    assert box is not None, "The element holds no painted box."  # A hidden element paints no box.
    return dict(box)  # A plain copy, so the caller reads the keys by name.


def header_fits(page: Any) -> dict[str, bool]:
    """Return, for each header of the Captures table, whether the header shows its whole text and arrow.

    Why:
        A header does not wrap. If the text and the sort arrow need more room
        than the column gives, the next header covers the arrow, and the
        operator cannot see the sort order.

    Args:
        page: The browser page.

    Returns:
        One flag for each header name. True means that the header fits.
    """
    logger.info("Measure each header of the Captures table")  # Log before the browser read.
    measures = page.get_by_test_id(TABLE_ID).evaluate(HEADER_FIT_SCRIPT)  # One read for every header.
    names = header_names(page)  # The header names, in the same column order.
    logger.debug("The header measures are %s", list(zip(names, measures, strict=True)))  # The raw evidence.
    return {  # Each header name and its fit.
        name: measure["need"] <= measure["given"] + HEADER_FIT_TOLERANCE
        for name, measure in zip(names, measures, strict=True)
    }


def seed_positions(page: Any) -> tuple[list[int], int]:
    """Return the page positions of the seed rows of the two sites.

    Args:
        page: The browser page.

    Returns:
        The positions of the four rows of the stand-in site, and the position
        of the one row of the stored poll site.
    """
    order = row_order(page)  # The rows in page order.
    stand_in_ids = [key for key, name in SEED_SITE_NAMES.items() if name == STAND_IN_SITE_NAME]  # Four rows.
    stand_in = [order.index(f"history-row-{capture_id}") for capture_id in stand_in_ids]  # Their positions.
    return stand_in, order.index(f"history-row-{STORED_POLL_CAPTURE_ID}")  # The one row of the other site.


def test_the_history_with_no_site_names_the_site_of_each_row(page: Any) -> None:
    """User Stories 1 and 3: the Site header, the site cell of each seed capture, and the caption."""
    open_history(page, EVERY_SITE_PATH)  # The operator opens the history of every site.
    assert save_screenshot(page, "history-every-site.png").exists()  # The screenshot comes before the compare.
    assert header_names(page) == EVERY_SITE_HEADERS  # FR-001: ten headers, with Site second.
    for capture_id, site_name in SEED_SITE_NAMES.items():  # Each seed row of the two sites.
        cell = page.get_by_test_id(f"history-site-{capture_id}")  # FR-004: the test identifier of the cell.
        sync_api.expect(cell).to_have_text(site_name)  # FR-002: the cell names the site of the row.
        sync_api.expect(cell).to_have_attribute("title", site_name)  # FR-003: the title holds the whole name.
    raw_caption = page.get_by_test_id(TABLE_ID).locator("caption").text_content() or ""  # The hidden caption.
    caption = " ".join(raw_caption.split())  # The template wraps the caption across lines.
    assert caption == EVERY_SITE_CAPTION, f"The caption of every site is wrong: {caption}"  # FR-005.
    logger.debug("The history with no site names the site of each seed row")  # Log after the compare.


@pytest.mark.parametrize("width", WINDOW_WIDTHS)
def test_each_row_with_the_site_column_stays_on_one_line(page: Any, width: int) -> None:
    """SC-004: each seed row keeps the height budget of issue #2106, and the Open control stays in the window."""
    open_history(page, EVERY_SITE_PATH, width)  # The operator opens the history in a window of this width.
    assert save_screenshot(page, f"history-every-site-{width}.png").exists()  # The evidence of this width.
    for capture_id in SEED_SITE_NAMES:  # Each seed row of the two sites.
        control = box_of(page.get_by_test_id(f"history-open-{capture_id}"))  # The Open control of the row.
        row = box_of(page.get_by_test_id(f"history-row-{capture_id}"))  # The whole row.
        logger.debug("%s at %s pixels: control %s, row %s", capture_id, width, control, row)  # The measured boxes.
        assert control["height"] <= OPEN_HEIGHT_CEILING, f"{capture_id}: the Open control wraps"  # One line.
        assert control["width"] >= OPEN_WIDTH_FLOOR, f"{capture_id}: the Open control is too narrow"  # One word.
        assert control["x"] + control["width"] <= width, f"{capture_id}: Open sits past the window edge"  # Visible.
        assert row["height"] <= ROW_HEIGHT_CEILING, f"{capture_id}: the row is too tall"  # Issue #2106.
    logger.debug("Each seed row stays on one line at %s pixels", width)  # Log after the measure.


def test_the_site_column_hides_no_sort_arrow(page: Any) -> None:
    """SC-005: at 1280 pixels, each header that fits on the page of one site also fits with the Site column.

    Why:
        The font of the browser sets the header widths, and the Linux font of
        the test runner is wider than the Windows font. The check therefore
        compares the two tables in one browser, and it does not name a fixed
        pixel count.
    """
    open_history(page, ONE_SITE_PATH, HEADER_WINDOW_WIDTH)  # The table of one site is the baseline.
    one_site = header_fits(page)  # The fit of each of the nine headers.
    open_history(page, EVERY_SITE_PATH, HEADER_WINDOW_WIDTH)  # The table with the Site column.
    assert save_screenshot(page, f"history-every-site-headers-{HEADER_WINDOW_WIDTH}.png").exists()  # Evidence.
    every_site = header_fits(page)  # The fit of each of the ten headers.
    assert every_site["Site"], "The Site header hides its sort arrow"  # The new header shows its arrow.
    hidden = [name for name, fits in one_site.items() if fits and not every_site[name]]  # A lost arrow.
    assert not hidden, f"The Site column hides the sort arrow of {hidden}"  # SC-005: the nine arrows stay.
    logger.debug("The Site column hides no sort arrow at %s pixels", HEADER_WINDOW_WIDTH)  # Log after the compare.


def test_the_site_header_sorts_the_rows_by_site(page: Any) -> None:
    """User Story 3 and FR-007: a press of the Site header orders the rows by the site text."""
    open_history(page, EVERY_SITE_PATH)  # The operator opens the history of every site.
    header = page.get_by_test_id(TABLE_ID).locator("thead th").nth(SITE_HEADER_INDEX)  # The Site header.
    sync_api.expect(header).to_have_attribute("aria-sort", "none")  # portal.js made the header a sort control.
    header.click()  # The first press orders the rows from A to Z.
    sync_api.expect(header).to_have_attribute("aria-sort", "ascending")  # The screen reader hears the order.
    assert save_screenshot(page, "history-sorted-by-site.png").exists()  # The evidence of the ascending order.
    stand_in, stored_poll = seed_positions(page)  # "E2E Stand-In Site" sorts before "E2E Stored Poll Site".
    assert max(stand_in) < stored_poll, f"The ascending order is wrong: {row_order(page)}"
    header.click()  # The second press reverses the order.
    sync_api.expect(header).to_have_attribute("aria-sort", "descending")  # The screen reader hears the change.
    stand_in, stored_poll = seed_positions(page)  # The positions after the second press.
    assert stored_poll < min(stand_in), f"The descending order is wrong: {row_order(page)}"
    logger.debug("The Site header sorts the rows in both directions")  # Log after the compare.


def test_the_history_of_one_site_shows_no_site_column(page: Any) -> None:
    """User Story 2 and User Story 3: the page of one site keeps the nine columns of today."""
    open_history(page, ONE_SITE_PATH)  # The operator opens the history of one site.
    assert save_screenshot(page, "history-one-site.png").exists()  # The screenshot comes before the compare.
    assert header_names(page) == ONE_SITE_HEADERS  # FR-006: no Site header.
    sync_api.expect(page.locator('[data-testid^="history-site-"]')).to_have_count(0)  # No row holds a site cell.
    sync_api.expect(page.get_by_test_id(f"history-row-{STORED_POLL_CAPTURE_ID}")).to_be_visible()  # The one row.
    logger.debug("The history of one site shows no Site column")  # Log after the compare.
