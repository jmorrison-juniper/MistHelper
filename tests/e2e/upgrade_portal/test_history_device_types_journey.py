"""Browser journey of issue #3492: each seed row of the history names its device types.

Why:
    Issue #3492. The seed captures held no device type count, so each seed row
    of the history read "No device type". No browser test proved the device
    type phrase of issue #2107, and no browser test measured the fit of a real
    phrase in a row. The Tier 3 seed also counted no guest client.

    This journey drives a real browser to the history with no site. It reads
    the Device types cell of each seed row and the Clients cell of each seed
    row. It measures the height of each seed row at three window widths, on
    the table with no site and on the table of one site. The two tables use
    two width sets of the stylesheet. The journey logs the width that each
    phrase needs and the width that each cell gives, and it writes those
    numbers to a JSON file beside the screenshots.

    Many journeys share the browser test server, and some of them store a
    capture. The journey therefore asks for a page of 200 rows, and it reads
    the rows of the five seed captures by their identifiers.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pytest

from tests.e2e.upgrade_portal.conftest import (
    POST_CAPTURE_ID,
    PRE_CAPTURE_ID,
    STAND_IN_SITE_ID,
    STANDALONE_PRE_CAPTURE_ID,
    STORED_POLL_CAPTURE_ID,
    TIER3_CAPTURE_ID,
)

sync_api = pytest.importorskip("playwright.sync_api", reason="Playwright is not installed.")

logger = logging.getLogger(__name__)

EVERY_SITE_PATH = "/history?limit=200"  # The history with no site. The largest page holds every seed row.
ONE_SITE_PATH = f"/history?site_id={STAND_IN_SITE_ID}&limit=200"  # The history of the site with four seeds.
TABLE_ID = "history-table"  # The Captures table.
DEVICE_TYPE_PHRASE = "1 gateway, 1 switch, 1 access point"  # Issue #2107: one device of each type.
SEED_CLIENT_TEXTS = {  # The Clients cell of each seed row. Only the Tier 3 seed holds a guest client.
    PRE_CAPTURE_ID: "3",
    STANDALONE_PRE_CAPTURE_ID: "3",
    POST_CAPTURE_ID: "3",
    STORED_POLL_CAPTURE_ID: "3",
    TIER3_CAPTURE_ID: "4",
}
HISTORY_PAGES = {  # Each table width set of portal.css, with its address and the seed rows that it shows.
    "every-site": (EVERY_SITE_PATH, tuple(SEED_CLIENT_TEXTS)),  # Ten columns. Issue #3486 added the Site column.
    "one-site": (ONE_SITE_PATH, tuple(key for key in SEED_CLIENT_TEXTS if key != STORED_POLL_CAPTURE_ID)),  # Nine.
}
CLIENTS_HEADER = "Clients"  # The header of the client count column.
SORT_ARROWS = "\u2195\u25b2\u25bc"  # The three arrows that portal.js appends to a sortable header.
ROW_CELLS = ":scope > th, :scope > td"  # The Capture cell is a row header, and the other cells are data cells.
WINDOW_WIDTHS = (1024, 1280, 1440)  # A narrow window, the common window, and a wide window.
WINDOW_HEIGHT = 900  # One height for every window, so each screenshot reads the same way.
ROW_HEIGHT_CEILING = 48  # The row height budget of issue #2106.
CELL_FIT_SCRIPT = """
cell => {
  const range = document.createRange();
  range.selectNodeContents(cell);
  const style = getComputedStyle(cell);
  const padding = parseFloat(style.paddingLeft) + parseFloat(style.paddingRight);
  return {
    need: range.getBoundingClientRect().width + padding,
    given: cell.clientWidth,
    clipped: cell.scrollWidth > cell.clientWidth,
    whiteSpace: style.whiteSpace,
    textOverflow: style.textOverflow,
  };
}
"""  # A range measures the whole phrase, and the clip of the cell does not change the measure.
SCREENSHOT_DIRECTORY = (  # The evidence folder of this journey.
    Path(__file__).parents[3] / "test-artifacts" / "upgrade-portal-journeys" / "history-device-types"
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


def open_history(page: Any, path: str = EVERY_SITE_PATH, width: int = 1280) -> None:
    """Open one history page at one window width, and log the load time.

    Args:
        page: The browser page.
        path: The address of the history page.
        width: The window width in pixels.
    """
    logger.info("Open %s at a window width of %s pixels", path, width)  # Log before the open.
    page.set_viewport_size({"width": width, "height": WINDOW_HEIGHT})  # The window of this check.
    page.goto(path, wait_until="load")  # The load event comes after portal.js prepares each header.
    sync_api.expect(page.get_by_test_id(TABLE_ID)).to_be_visible()  # The Captures table is on the page.
    duration = page.evaluate("() => performance.getEntriesByType('navigation')[0].duration")  # The load time.
    logger.debug("The history page %s loaded in %.0f milliseconds", path, duration)  # The performance record.


def column_index(page: Any, name: str) -> int:
    """Return the position of one column of the Captures table.

    Args:
        page: The browser page.
        name: The header name, with no sort arrow.

    Returns:
        The position of the column, counted from zero.
    """
    texts = page.get_by_test_id(TABLE_ID).locator("thead th").all_text_contents()  # The raw header texts.
    names = [" ".join(text.split()).strip(SORT_ARROWS).strip() for text in texts]  # No arrow, one space.
    assert name in names, f"The table holds no {name} header: {names}"  # The column exists.
    return names.index(name)  # The same position holds the cell of the column in each row.


def device_type_fit(page: Any, capture_id: str) -> dict[str, Any]:
    """Measure the Device types cell of one seed row.

    Args:
        page: The browser page.
        capture_id: The seed capture of the row.

    Returns:
        The width that the phrase needs, the width that the cell gives, the
        clip flag, and the two computed style values of the clip rule.
    """
    cell = page.get_by_test_id(f"history-device-type-{capture_id}")  # The cell of the device type phrase.
    sync_api.expect(cell).to_have_count(1)  # One cell, and the wait covers a slow page.
    fit = dict(cell.evaluate(CELL_FIT_SCRIPT))  # One browser read for the whole measure.
    need, given = fit["need"], fit["given"]  # The width that the phrase needs, and the width of the cell.
    logger.debug("%s: the phrase needs %.1f pixels, and the cell gives %s", capture_id, need, given)  # The measure.
    return fit  # The caller logs and stores the measure.


def save_fit(fits: dict[str, dict[str, Any]], name: str) -> Path:
    """Write the measure of each Device types cell beside the screenshots.

    Args:
        fits: The measure of each seed cell, by capture identifier.
        name: The page name and the window width of the measure.

    Returns:
        The path of the saved file.
    """
    path = SCREENSHOT_DIRECTORY / f"device-type-fit-{name}.json"  # One file for each page and window width.
    SCREENSHOT_DIRECTORY.mkdir(parents=True, exist_ok=True)  # Keep the evidence under the repository data tree.
    logger.info("Save the device type measure %s", name)  # Log before the file write.
    path.write_text(json.dumps(fits, indent=2), encoding="utf-8")  # A reviewer reads the numbers in the pull request.
    logger.debug("Saved the device type measure %s", path)  # Log after the file write.
    return path  # The caller proves that the file exists.


def row_height(page: Any, capture_id: str) -> float:
    """Return the painted height of one seed row.

    Args:
        page: The browser page.
        capture_id: The seed capture of the row.

    Returns:
        The row height in pixels.
    """
    row = page.get_by_test_id(f"history-row-{capture_id}")  # The whole row.
    sync_api.expect(row).to_have_count(1)  # One row, and the wait covers a slow page.
    box = row.bounding_box()  # The box that the browser painted.
    assert box is not None, f"{capture_id}: the row holds no painted box."  # A hidden row paints no box.
    return float(box["height"])  # The caller compares the height with the budget of issue #2106.


def test_each_seed_row_names_its_device_types(page: Any) -> None:
    """User Story 1 and FR-004: each seed row reads the device type phrase, and the title holds it."""
    open_history(page)  # The operator opens the history of every site.
    assert save_screenshot(page, "history-device-types.png").exists()  # The screenshot comes before the compare.
    for capture_id in SEED_CLIENT_TEXTS:  # Each seed row of the two sites.
        cell = page.get_by_test_id(f"history-device-type-{capture_id}")  # The Device types cell of the row.
        sync_api.expect(cell).to_have_text(DEVICE_TYPE_PHRASE)  # SC-001: no seed row reads "No device type".
        sync_api.expect(cell).to_have_attribute("title", DEVICE_TYPE_PHRASE)  # The title holds the whole phrase.
    logger.debug("Each seed row names one device of each type")  # Log after the compare.


def test_each_seed_row_counts_its_clients(page: Any) -> None:
    """User Story 2 and FR-003: the Clients cell of the Tier 3 row counts the guest client."""
    open_history(page)  # The operator opens the history of every site.
    index = column_index(page, CLIENTS_HEADER)  # The Clients column holds no test identifier.
    counted: dict[str, str] = {}  # The client count that each seed row paints.
    for capture_id in SEED_CLIENT_TEXTS:  # Each seed row of the two sites.
        cells = page.get_by_test_id(f"history-row-{capture_id}").locator(ROW_CELLS)  # The cells of the row.
        counted[capture_id] = cells.nth(index).inner_text().strip()  # The text that the operator reads.
    assert counted == SEED_CLIENT_TEXTS, f"The Clients cells read {counted}"  # Wired, wireless, and guest clients.
    logger.debug("Each seed row counts its clients")  # Log after the compare.


@pytest.mark.parametrize("width", WINDOW_WIDTHS)
@pytest.mark.parametrize("page_name", tuple(HISTORY_PAGES))
def test_each_row_with_the_device_type_phrase_stays_on_one_line(page: Any, page_name: str, width: int) -> None:
    """User Story 3 and SC-003: each seed row keeps the height budget of issue #2106 with the real phrase."""
    path, seed_ids = HISTORY_PAGES[page_name]  # The address of the table and the seed rows that it shows.
    open_history(page, path, width)  # The operator opens the history in a window of this width.
    name = f"{page_name}-{width}"  # One evidence name for each table and window width.
    assert save_screenshot(page, f"history-device-types-{name}.png").exists()  # The evidence of this width.
    fits = {capture_id: device_type_fit(page, capture_id) for capture_id in seed_ids}  # Each cell.
    assert save_fit(fits, name).exists()  # The measure sits beside the screenshot of this width.
    for capture_id, fit in fits.items():  # Each seed row of the two sites.
        assert (fit["whiteSpace"], fit["textOverflow"]) == ("nowrap", "ellipsis"), f"{capture_id}: {fit}"  # A clip.
        if width == 1280:  # Issue #3495: the common desktop width must show the complete phrase.
            assert not fit["clipped"], f"{capture_id}: the device type phrase clips at 1280 pixels: {fit}"
        height = row_height(page, capture_id)  # The painted height of the row.
        message = f"{capture_id}: the row is {height} pixels tall at {width} pixels"  # The failure text.
        assert height <= ROW_HEIGHT_CEILING, message  # Issue #2106: the phrase adds no second line.
    clipped = sum(1 for fit in fits.values() if fit["clipped"])  # The cells that show an ellipsis.
    logger.info("On %s, the phrase clips in %s of %s cells", name, clipped, len(fits))  # The fit record.
