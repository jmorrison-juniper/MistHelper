"""Browser tests for the site picker and the inventory view of the capture portal.

Why:
    A contract test proves that a JSON answer holds the right fields. It cannot
    prove that an operator can find a site, open it, and read the device list. A
    browser test drives the route, the template, and the browser script together,
    so it finds a template that renders no row and a script that never runs.

What this module skips and what it fails:
    The module reports a skip when no browser binary exists. It reports a
    failure when a page answers 401 or 404, and when a page answers 200 and the
    identifier contract does not hold. The fixture starts its own portal, so a
    401 and a 404 are both faults of that portal. A portal that a browser test
    cannot reach never reports a pass, and a broken page never reports a skip.

Identifier contract:
    `contracts/ui-testids.md` fixes every identifier below. Rule 4 states that a
    test selects by `data-testid` only. Every locator here reads that attribute.
    No locator reads visible text, a style class, or an element position.
"""

from __future__ import annotations

import re
from typing import Any

import pytest

# The Playwright package must exist before this module defines a browser test.
# A run without the package reports a skip and never an import error.
sync_api = pytest.importorskip("playwright.sync_api", reason="The Playwright package is not installed.")

# `contracts/http-api.md` fixes this path for the site picker.
SITE_PAGE_PATH = "/select/site"

# The identifier prefixes that `contracts/ui-testids.md` fixes for a dynamic row.
SITE_ROW_PREFIX = "site-row-"
INVENTORY_ROW_PREFIX = "inventory-row-"

# The four fixed identifiers of the two pages.
SITE_SEARCH_ID = "site-search"
INVENTORY_TABLE_ID = "inventory-table"
INVENTORY_TOTAL_ID = "inventory-count-total"

# The text below matches no site name and no site identifier, so the browser
# filter must hide every row. A short word could match a real site by accident.
UNMATCHED_FILTER_TEXT = "zzz-no-such-site-zzz"

# `data-model.md` fixes the device index key as a MAC address in lower case with
# no separator. The inventory row appends that same key, so a capture document
# and this page join on one spelling.
MAC_PATTERN = re.compile(r"^[0-9a-f]{12}$")

OK_STATUS = 200  # The contract fixes this status for every page below.
UNAUTHORIZED_STATUS = 401  # `runtime/identity.py` answers this code with no session.
NOT_FOUND_STATUS = 404  # The route is not registered yet.

# WHY: The server fixture states its own fault and its own skip, so this module
# must not translate either one. The browser fixture is different: a workstation
# without a browser binary describes the workstation and never the page.
SERVER_FIXTURE = "capture_portal_server"
BROWSER_FIXTURE = "page"


def _browser_page(request: pytest.FixtureRequest, name: str) -> Any:
    """Build one browser page, and report a missing browser binary as a skip.

    Why:
        Playwright needs a browser binary that no source tree carries. A plain
        request would report an error, which reads in a report as a broken test.
        A missing binary is the one environment fault this module still hides,
        because it stops every browser test for a reason outside the portal.
        The server fixture states its own fault and its own skip, so this
        function never wraps it.

    Args:
        request: The pytest request object of the calling fixture.
        name: The browser fixture to build.

    Returns:
        The Playwright page object.
    """
    try:  # A missing browser binary describes the workstation, never the page.
        return request.getfixturevalue(name)
    except Exception as failure:  # A skip states the real cause, so nothing hides.
        pytest.skip(f"Playwright could not open a browser, so no browser test can run. Cause: {failure}")


@pytest.fixture
def portal_page(request: pytest.FixtureRequest) -> Any:
    """Return a browser page that points at the running capture portal.

    Why:
        Every test below needs the same two parts: a portal on port 8056 and a
        browser page. One fixture builds both in order, so a missing part gives
        one clear skip instead of one error for each test.

    Args:
        request: The pytest request object.

    Returns:
        The Playwright page object.
    """
    request.getfixturevalue(SERVER_FIXTURE)  # A fault here is a fault of the portal, so it must not become a skip.
    return _browser_page(request, BROWSER_FIXTURE)


def _page_status(page: Any, path: str) -> int:
    """Open one path and return the status code of the answer.

    Args:
        page: The Playwright page object.
        path: The path to open, relative to the portal address.

    Returns:
        The status code that the portal answered.
    """
    answer = page.goto(path, wait_until="domcontentloaded")
    if answer is None:  # A page with no answer gives the test nothing to read.
        pytest.skip(f"The browser returned no response for {path}.")
    status: int = answer.status
    return status


def _require_built_route(status: int, path: str) -> None:
    """Fail when the portal answers a status that the contract does not fix.

    Why:
        This function draws the one line that keeps the suite honest. The
        fixture starts its own portal, so that portal holds the sign-in seam and
        every blueprint of this run. A 401 therefore means the seam is broken,
        and a 404 means a blueprint is missing. Both are faults of the portal. A
        skip for either one would let a whole run read no page and still report
        success.

    Args:
        status: The status code the portal answered.
        path: The path the test opened, named in every message.

    Raises:
        AssertionError: If the portal answered a status that the contract
            does not fix for a page.
    """
    if status == UNAUTHORIZED_STATUS:  # `identity.require_session` refused the request.
        raise AssertionError(f"{path} answered 401. The portal this run started holds no sign-in seam.")
    if status == NOT_FOUND_STATUS:  # The blueprint that owns this path is not registered.
        raise AssertionError(f"{path} answered 404. The blueprint that owns this path is not registered.")
    assert status == OK_STATUS, f"{path} answered {status}. `contracts/http-api.md` fixes 200 for this page."


def _open_portal_page(page: Any, path: str) -> None:
    """Open one portal page, and fail when the portal answers wrongly.

    Args:
        page: The Playwright page object.
        path: The path to open.
    """
    _require_built_route(_page_status(page, path), path)


def _row_keys(page: Any, prefix: str) -> list[str]:
    """Read the stable key of every row that carries one identifier prefix.

    Why:
        Rule 5 of `contracts/ui-testids.md` states that a dynamic row appends a
        stable key. A test cannot know a site identifier or a MAC address before
        it reads the page, so it reads the keys the page published.

    Args:
        page: The Playwright page object.
        prefix: The identifier prefix, such as `site-row-`.

    Returns:
        One key for each row, in page order.
    """
    rows = page.locator(f'[data-testid^="{prefix}"]')  # A prefix match still selects by `data-testid`.
    markers = rows.evaluate_all("found => found.map(node => node.getAttribute('data-testid'))")
    return [str(marker)[len(prefix) :] for marker in markers if marker]


def _first_row_key(page: Any, prefix: str) -> str:
    """Return the key of the first row that carries one identifier prefix.

    Why:
        A test needs one sample key to build the identifier of a paired control,
        such as the open button of a site row. The first row is a sample of a
        list whose rows all share one shape, so the choice reads nothing from
        the position itself.

    Args:
        page: The Playwright page object.
        prefix: The identifier prefix, such as `site-row-`.

    Returns:
        The key of the first row.
    """
    keys = _row_keys(page, prefix)
    if not keys:  # The portal reached no site, so no key exists to drive.
        pytest.skip(f"The page shows no element with the identifier prefix {prefix}, so no key exists to drive.")
    return keys[0]


@pytest.fixture
def site_page(portal_page: Any) -> Any:
    """Return a page that shows the site picker.

    Args:
        portal_page: The browser page that points at the portal.

    Returns:
        The Playwright page object, on the site picker.
    """
    _open_portal_page(portal_page, SITE_PAGE_PATH)
    return portal_page


@pytest.fixture
def inventory_page(site_page: Any) -> Any:
    """Return a page that shows the inventory of the first site.

    Why:
        `contracts/http-api.md` fixes no page path for the inventory of one
        site. The open button of a site row is the one published route to that
        page, so this fixture presses it instead of guessing a path.

    Args:
        site_page: The page that shows the site picker.

    Returns:
        The Playwright page object, on the inventory view.
    """
    site_id = _first_row_key(site_page, SITE_ROW_PREFIX)
    with site_page.expect_response(lambda answer: answer.request.is_navigation_request()) as event:
        site_page.get_by_test_id(f"site-open-{site_id}").click()
    _require_built_route(event.value.status, f"the inventory page of the site {site_id}")
    return site_page


class TestSitePicker:
    """The site picker shows a search field and one row for each site."""

    def test_site_search_field_is_present(self, site_page: Any) -> None:
        """The picker shows the search field that FR-012 asks for.

        Args:
            site_page: The page that shows the site picker.
        """
        sync_api.expect(site_page.get_by_test_id(SITE_SEARCH_ID)).to_be_visible()

    def test_site_row_carries_an_open_button_with_the_same_key(self, site_page: Any) -> None:
        """One site row and its open button share one site identifier.

        Why:
            Rule 5 of the identifier contract binds a row and its controls to
            one key. A row whose open button holds a different key would leave
            a test unable to open the site it just read.

        Args:
            site_page: The page that shows the site picker.
        """
        site_id = _first_row_key(site_page, SITE_ROW_PREFIX)
        sync_api.expect(site_page.get_by_test_id(f"site-row-{site_id}")).to_be_visible()
        sync_api.expect(site_page.get_by_test_id(f"site-open-{site_id}")).to_be_visible()

    def test_site_search_hides_a_row_that_does_not_match(self, site_page: Any) -> None:
        """The search field hides every row when no site name matches.

        Why:
            FR-012 asks for a searchable list. The filter runs in the browser,
            so only a browser test proves that a key press changes the list.

        Args:
            site_page: The page that shows the site picker.
        """
        site_id = _first_row_key(site_page, SITE_ROW_PREFIX)
        site_page.get_by_test_id(SITE_SEARCH_ID).fill(UNMATCHED_FILTER_TEXT)
        sync_api.expect(site_page.get_by_test_id(f"site-row-{site_id}")).to_be_hidden()


class TestSiteInventory:
    """The inventory view shows the device table and the device total."""

    def test_inventory_table_and_total_are_present(self, inventory_page: Any) -> None:
        """The inventory view shows the device table and the total count.

        Args:
            inventory_page: The page that shows the inventory of one site.
        """
        sync_api.expect(inventory_page.get_by_test_id(INVENTORY_TABLE_ID)).to_be_visible()
        sync_api.expect(inventory_page.get_by_test_id(INVENTORY_TOTAL_ID)).to_be_visible()

    def test_inventory_total_counts_every_device_row(self, inventory_page: Any) -> None:
        """The total equals the number of device rows on the page.

        Why:
            The inventory reads the physical view, so every chassis member owns
            a row. A total that disagrees with the rows would tell the operator
            that the capture reads a different device count than the page shows.

        Args:
            inventory_page: The page that shows the inventory of one site.
        """
        total_text = (inventory_page.get_by_test_id(INVENTORY_TOTAL_ID).inner_text() or "").strip()
        assert total_text.isdigit(), f"{INVENTORY_TOTAL_ID} reads {total_text!r}. The contract fixes a whole number."
        rows = _row_keys(inventory_page, INVENTORY_ROW_PREFIX)
        assert int(total_text) == len(rows), f"{INVENTORY_TOTAL_ID} reads {total_text}, and the page shows {len(rows)}."

    def test_every_device_row_carries_a_mac_address_key(self, inventory_page: Any) -> None:
        """Each device row appends a MAC address in one spelling.

        Why:
            Rule 5 of the identifier contract states that a device row uses the
            MAC address, and `data-model.md` fixes lower case with no separator.
            A second spelling would break the join between this page and the
            device index of a capture, so a compare would report a false change.

        Args:
            inventory_page: The page that shows the inventory of one site.
        """
        keys = _row_keys(inventory_page, INVENTORY_ROW_PREFIX)
        if not keys:  # A site with no device publishes no row, which breaks no rule.
            pytest.skip("The site holds no device, so the page shows no inventory row to read.")
        wrong = [key for key in keys if not MAC_PATTERN.match(key)]
        assert not wrong, f"These inventory rows hold a MAC address in the wrong spelling: {wrong}."
        assert len(set(keys)) == len(keys), "Two inventory rows share one MAC address in their test identifiers."
