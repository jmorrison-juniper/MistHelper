"""The browser proof that each action label stays on one line on a narrow screen.

Why:
    Issue #3278 reports that at a width of 390 pixels the Choose, Open, and
    Select labels break into groups of letters. The unit test in
    ``tests/unit/upgrade_portal/test_select_action_cells.py`` reads the markup
    and the rule text. Only a browser paints the label, so only a browser
    proves the repair.

What each test measures:
    Each test opens a real page of the stand-in portal at 390 by 844 pixels. It
    counts the painted lines of the label text of one control. A label that
    breaks into letter groups paints more than one line. Each test also proves
    that the page itself does not scroll sideways, because a label that never
    wraps must push the scroll box of the table and not the page.

    Each test saves a screenshot of the whole page into the pytest folder of
    the test, so an engineer can compare the painted page with the count.

Identifier contract:
    Every locator reads a ``data-testid`` attribute, as rule 4 of
    ``contracts/ui-testids.md`` states. The multi-site label has no identifier
    of its own, so the script reaches it through the ``labels`` list of the
    check box that the identifier names.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

# The Playwright package must exist before this module defines a browser test.
sync_api = pytest.importorskip("playwright.sync_api", reason="The Playwright package is not installed.")

# The screen size that issue #3278 names. A common phone reports this size.
NARROW_SCREEN = {"width": 390, "height": 844}

# The three pages of the operator journey that hold an action column.
ORG_PAGE_PATH = "/select/org"
MODE_PAGE_PATH = "/select/mode"
SITE_PAGE_PATH = "/select/site"

OK_STATUS = 200  # The contract fixes this status for every page below.

# The server fixture states its own fault and its own skip. The browser
# fixture is different, because a missing browser describes the workstation.
SERVER_FIXTURE = "capture_portal_server"
BROWSER_FIXTURE = "page"

# The script counts the painted lines of the label text of one control. It
# reads only the direct text of the label. The visually hidden name of a row
# sits in a child element one pixel wide, so its words paint on many lines and
# must not count. A check box has no text, so the script reads its label.
LINE_COUNT_SCRIPT = """
(node) => {
  const target = node.labels && node.labels.length ? node.labels[0] : node;
  const tops = new Set();
  for (const child of target.childNodes) {
    if (child.nodeType !== Node.TEXT_NODE || !child.textContent.trim()) {
      continue;
    }
    const range = document.createRange();
    range.selectNodeContents(child);
    for (const rect of range.getClientRects()) {
      if (rect.width > 1 && rect.height > 1) {
        tops.add(Math.round(rect.top));
      }
    }
  }
  return tops.size;
}
"""

# The script returns the number of pixels by which the page is wider than the
# screen. A page that does not scroll sideways returns zero or less.
PAGE_OVERFLOW_SCRIPT = "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"


@pytest.fixture
def narrow_page(request: pytest.FixtureRequest) -> Any:
    """Return a signed-in browser page with the screen size of a phone.

    Args:
        request: The pytest request object.

    Returns:
        The Playwright page object.
    """
    request.getfixturevalue(SERVER_FIXTURE)  # A fault here is a fault of the portal, so it must not become a skip.
    try:  # A missing browser binary describes the workstation, never the page.
        page = request.getfixturevalue(BROWSER_FIXTURE)
    except Exception as failure:  # A skip states the real cause, so nothing hides.
        pytest.skip(f"Playwright could not open a browser, so no browser test can run. Cause: {failure}")
    page.set_viewport_size(NARROW_SCREEN)  # Every page below opens at the size that issue #3278 names.
    return page


def _open(page: Any, path: str) -> None:
    """Open one portal page, and fail when the portal answers another status.

    Args:
        page: The Playwright page object.
        path: The path to open, relative to the portal address.
    """
    answer = page.goto(path, wait_until="domcontentloaded")
    assert answer is not None and answer.status == OK_STATUS, f"{path} did not answer {OK_STATUS}"


def _first_key(page: Any, prefix: str) -> str:
    """Return the key of the first row that carries one identifier prefix.

    Args:
        page: The Playwright page object.
        prefix: The identifier prefix of a row, such as ``site-row-``.

    Returns:
        The key of the first row.
    """
    marker = page.locator(f'[data-testid^="{prefix}"]').first.get_attribute("data-testid")
    assert marker, f"The page shows no row with the identifier prefix {prefix}"
    return str(marker)[len(prefix) :]


def _measure(page: Any, test_id: str, screenshot: Path) -> tuple[int, int]:
    """Save a screenshot, then return the label line count and the page overflow.

    Args:
        page: The Playwright page object.
        test_id: The test identifier of the control.
        screenshot: The file that receives the screenshot of the whole page.

    Returns:
        The number of painted label lines, and the page overflow in pixels.
    """
    control = page.get_by_test_id(test_id)
    sync_api.expect(control).to_be_attached()  # The control must exist before the script reads it.
    page.screenshot(path=str(screenshot), full_page=True)  # The evidence that an engineer compares with the count.
    return int(control.evaluate(LINE_COUNT_SCRIPT)), int(page.evaluate(PAGE_OVERFLOW_SCRIPT))


def test_the_choose_label_stays_on_one_line(narrow_page: Any, tmp_path: Path) -> None:
    """Prove the Choose label of the organization table paints one line.

    Args:
        narrow_page: The signed-in page at the size of a phone.
        tmp_path: The pytest folder of this test.
    """
    _open(narrow_page, ORG_PAGE_PATH)
    key = _first_key(narrow_page, "org-row-")
    lines, overflow = _measure(narrow_page, f"org-select-{key}", tmp_path / "org-390x844.png")
    assert (lines, overflow <= 0) == (1, True), f"Choose paints {lines} lines, and the page overflows by {overflow}"


def test_the_open_label_stays_on_one_line(narrow_page: Any, tmp_path: Path) -> None:
    """Prove the Open label of the single-site table paints one line.

    Args:
        narrow_page: The signed-in page at the size of a phone.
        tmp_path: The pytest folder of this test.
    """
    _open(narrow_page, SITE_PAGE_PATH)
    key = _first_key(narrow_page, "site-row-")
    lines, overflow = _measure(narrow_page, f"site-open-{key}", tmp_path / "sites-single-390x844.png")
    assert (lines, overflow <= 0) == (1, True), f"Open paints {lines} lines, and the page overflows by {overflow}"


def test_the_select_label_stays_on_one_line(narrow_page: Any, tmp_path: Path) -> None:
    """Prove the Select label of the multi-site table paints one line.

    Why:
        The multi-site mode shows a check box and a label in the same action
        column. The mode must hold the same layout as the single-site mode.

    Args:
        narrow_page: The signed-in page at the size of a phone.
        tmp_path: The pytest folder of this test.
    """
    _open(narrow_page, MODE_PAGE_PATH)
    narrow_page.get_by_test_id("mode-multi-site").check()  # The operator chooses the multi-site mode.
    narrow_page.get_by_test_id("mode-continue").click()  # The portal then opens the site table.
    narrow_page.wait_for_url(re.compile(r".*/select/site$"))
    key = _first_key(narrow_page, "site-row-")
    lines, overflow = _measure(narrow_page, f"site-select-{key}", tmp_path / "sites-multi-390x844.png")
    assert (lines, overflow <= 0) == (1, True), f"Select paints {lines} lines, and the page overflows by {overflow}"
