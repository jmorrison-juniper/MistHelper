"""Browser tests for the capture history page of the upgrade capture portal.

Why:
    A contract test proves that the history endpoint shapes eight names and
    holds the page window inside its bounds. It cannot prove that the operator
    opens the page, reads a stored capture, and steps to the earlier page. That
    path crosses one template and one view builder, so only a browser test
    proves it.

Why the paging proof reads the earlier page control:
    `compare/render.py` sets `has_previous` from the offset alone, so the
    earlier page control becomes a live link on every page but the first, even
    when the store holds no row. The address of that link carries the limit and
    the offset that the route settled. The tests below read those two values
    back, so they prove the default limit, both limit bounds, and the offset
    bound on a workstation that holds no database.

Why a row test may skip:
    A stored capture reaches the page from the capture store. A workstation
    with no database driver reads an empty list, which is correct behavior and
    not a failure. The row tests therefore read the count first and skip with
    the real cause when the store holds nothing.

Why the module reaches no cloud:
    Every call below is a read of the portal itself. No test starts a capture,
    creates a run, or writes a firmware version, so nothing reaches live
    hardware and nothing opens a socket to the Mist cloud.

Why the helpers repeat `test_stop.py`:
    The shared `conftest.py` of this directory belongs to every browser module,
    and a helper for one journey does not belong in it.
"""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest

# The Playwright package must exist before this module defines a browser test.
# A run without the package reports a skip and never an import error.
sync_api = pytest.importorskip("playwright.sync_api", reason="The Playwright package is not installed.")

# `contracts/http-api.md` fixes these paths.
HISTORY_PAGE_PATH = "/history"
SITE_PAGE_PATH = "/select/site"
HISTORY_API_TEMPLATE = "/api/sites/{site_id}/history"
RUN_HISTORY_API_TEMPLATE = "/api/sites/{site_id}/runs/history"

SITE_ROW_PREFIX = "site-row-"  # `contracts/ui-testids.md` line 68.

# The history controls, all fixed by `contracts/ui-testids.md` lines 198 to 202.
HISTORY_TABLE_ID = "history-table"
HISTORY_ROW_PREFIX = "history-row-"
HISTORY_OPEN_PREFIX = "history-open-"
HISTORY_NEXT_ID = "history-page-next"
HISTORY_PREVIOUS_ID = "history-page-previous"

# `contracts/http-api.md:466` names these two query values and their defaults.
LIMIT_FIELD = "limit"
OFFSET_FIELD = "offset"
DEFAULT_LIMIT = 25
SMALLEST_LIMIT = 1
LARGEST_LIMIT = 200
FIRST_OFFSET = 0

# `contracts/http-api.md:476` holds the offset between zero and this value.
LARGEST_OFFSET = 1_000_000

# `contracts/http-api.md:467` fixes the two envelope names of the two endpoints.
CAPTURES_FIELD = "captures"
RUNS_FIELD = "runs"
TOTAL_FIELD = "total"

# `contracts/http-api.md:469` fixes these eight names on every capture row.
ROW_NAMES = (
    "capture_id",
    "role",
    "started_at",
    "capture_status",
    "actor_email",
    "stored_size_bytes",
    "device_count",
    "client_count",
)

OK_STATUS = 200  # The contract fixes this status for the page and for both endpoints.
UNAUTHORIZED_STATUS = 401  # `runtime/identity.py` answers this code with no session.
NOT_FOUND_STATUS = 404  # The route is not registered yet.

GATE_TIMEOUT_MS = 5000  # The page is server rendered, so every control is present at once.

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
    """Return a browser page that points at the running portal.

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

    Args:
        status: The status code the portal answered.
        path: The path the test opened, named in every message.

    Raises:
        AssertionError: If the portal answered a status that the contract does
            not fix for a page.
    """
    if status == UNAUTHORIZED_STATUS:  # `identity.require_session` refused the request.
        raise AssertionError(f"{path} answered 401. The portal this run started holds no sign-in seam.")
    if status == NOT_FOUND_STATUS:  # The blueprint that owns this path is not registered.
        raise AssertionError(f"{path} answered 404. The blueprint that owns this path is not registered.")
    assert status == OK_STATUS, f"{path} answered {status}. `contracts/http-api.md` fixes 200 for this page."


def _marker_keys(page: Any, prefix: str) -> list[str]:
    """Return the tail of every identifier on the page that starts with a prefix.

    Args:
        page: The Playwright page object.
        prefix: The identifier prefix, such as `history-row-`.

    Returns:
        The tail of each matching identifier, in page order.
    """
    found = page.locator(f'[data-testid^="{prefix}"]')  # A prefix match still selects by `data-testid`.
    markers = found.evaluate_all("nodes => nodes.map(node => node.getAttribute('data-testid'))")
    return [str(marker)[len(prefix) :] for marker in markers if marker]


@pytest.fixture
def site_id(portal_page: Any) -> str:
    """Open the site picker and return the key of the first site row.

    Why:
        Both history endpoints name the site in the path, and the contract fixes
        no page that lists a site key as text. The picker is the one documented
        source of a real key.

    Args:
        portal_page: The browser page that points at the portal.

    Returns:
        The site key of the first row.
    """
    _require_built_route(_page_status(portal_page, SITE_PAGE_PATH), SITE_PAGE_PATH)
    keys = _marker_keys(portal_page, SITE_ROW_PREFIX)
    if not keys:  # The portal reached no site, so no history path can be built.
        pytest.skip("The site picker shows no site row, so no site key exists to read a history for.")
    return keys[0]


def _read_json(page: Any, path: str) -> dict[str, Any]:
    """Read one portal endpoint and return the answer body.

    Args:
        page: The Playwright page object, which carries the portal session.
        path: The endpoint to read, relative to the portal address.

    Returns:
        The answer body.

    Raises:
        AssertionError: If a built endpoint answers a status the contract does
            not fix.
    """
    try:  # The fixture started this portal, so a call that fails names a fault of it.
        answer = page.request.get(path)
    except Exception as failure:  # The portal died, or it never bound the port.
        raise AssertionError(f"The read of {path} did not complete. Cause: {failure}") from failure
    if answer.status == UNAUTHORIZED_STATUS:  # `identity.require_session` refused the request.
        raise AssertionError(f"{path} answered 401. The portal this run started holds no sign-in seam.")
    if answer.status == NOT_FOUND_STATUS:  # The blueprint that owns this path is not registered.
        raise AssertionError(f"{path} answered 404. The blueprint that owns this path is not registered.")
    assert answer.status == OK_STATUS, f"{path} answered {answer.status}. `contracts/http-api.md` fixes 200."
    return dict(json.loads(answer.text()))


def _stored_rows(page: Any, site: str) -> list[dict[str, Any]]:
    """Return the stored capture rows of one site, or skip when none exist.

    Why:
        A workstation with no database driver reads an empty history. That is
        correct behavior, so a row test states the cause and skips rather than
        reporting a failure that names the wrong part.

    Args:
        page: The Playwright page object.
        site: The site key that the path names.

    Returns:
        The stored capture rows.
    """
    body = _read_json(page, HISTORY_API_TEMPLATE.format(site_id=site))
    rows = body.get(CAPTURES_FIELD) or []
    if not rows:  # The store holds no capture, so no row can reach the page.
        pytest.skip("The capture store holds no stored capture, so no history row exists to read.")
    return [dict(row) for row in rows]


def _window_values(href: str) -> dict[str, str]:
    """Return the query values of one paging address.

    Args:
        href: The address that a paging control carries.

    Returns:
        The first value of each query name.
    """
    parsed = urlsplit(href)  # A relative address and a whole address both parse here.
    found = parse_qs(parsed.query)
    return {name: values[0] for name, values in found.items() if values}


def _earlier_page_window(page: Any, query: str) -> dict[str, str]:
    """Open one history page and read the window of its earlier page link.

    Why:
        The route settles the limit and the offset before it builds this
        address, so the address states what the route decided. That makes the
        bounds readable without a stored row.

    Args:
        page: The Playwright page object.
        query: The query text of the page to open, with no leading question mark.

    Returns:
        The query values of the earlier page address.
    """
    path = f"{HISTORY_PAGE_PATH}?{query}"
    _require_built_route(_page_status(page, path), path)
    control = page.get_by_test_id(HISTORY_PREVIOUS_ID)
    sync_api.expect(control).to_be_visible(timeout=GATE_TIMEOUT_MS)
    href = control.get_attribute("href")
    if not href:  # The control is the locked button, so this page holds no earlier page.
        pytest.skip(f"{path} shows no earlier page link, so the page window cannot be read.")
    return _window_values(href)


class TestHistoryPage:
    """The history page shows the stored captures and both paging controls."""

    def test_the_history_page_shows_the_capture_table(self, portal_page: Any) -> None:
        """The page carries the history table.

        Why:
            `contracts/http-api.md:496` names this page as the human view of the
            stored captures. An operator who finds no table cannot find an
            earlier capture to compare against.

        Args:
            portal_page: The browser page that points at the portal.
        """
        _require_built_route(_page_status(portal_page, HISTORY_PAGE_PATH), HISTORY_PAGE_PATH)
        sync_api.expect(portal_page.get_by_test_id(HISTORY_TABLE_ID)).to_be_visible(timeout=GATE_TIMEOUT_MS)

    def test_the_history_page_carries_both_paging_controls(self, portal_page: Any) -> None:
        """Both paging controls sit on the page in every state.

        Why:
            `review/history.html` keeps the test identifier on the control when
            the neighbor page is absent, and shows a locked button instead of a
            dead link. A test therefore finds the control on the first page and
            on the last page.

        Args:
            portal_page: The browser page that points at the portal.
        """
        _require_built_route(_page_status(portal_page, HISTORY_PAGE_PATH), HISTORY_PAGE_PATH)
        sync_api.expect(portal_page.get_by_test_id(HISTORY_PREVIOUS_ID)).to_be_visible(timeout=GATE_TIMEOUT_MS)
        sync_api.expect(portal_page.get_by_test_id(HISTORY_NEXT_ID)).to_be_visible(timeout=GATE_TIMEOUT_MS)

    def test_a_stored_capture_appears_as_a_history_row(self, portal_page: Any, site_id: str) -> None:
        """Every stored capture of the site reaches the page as one row.

        Why:
            The endpoint and the page must agree. A page that drops a row hides
            a capture that the operator needs before an upgrade.

        Args:
            portal_page: The browser page that points at the portal.
            site_id: The site key that the endpoint path names.
        """
        stored = _stored_rows(portal_page, site_id)
        path = f"{HISTORY_PAGE_PATH}?site_id={site_id}"
        _require_built_route(_page_status(portal_page, path), path)
        shown = set(_marker_keys(portal_page, HISTORY_ROW_PREFIX))
        assert {str(row["capture_id"]) for row in stored} <= shown, "The page dropped a stored capture."

    def test_each_history_row_offers_an_open_control(self, portal_page: Any, site_id: str) -> None:
        """Each row carries the control that opens that capture.

        Why:
            A row with no open control states that a capture exists and gives no
            way to read it, so the history would answer half the question.

        Args:
            portal_page: The browser page that points at the portal.
            site_id: The site key that the endpoint path names.
        """
        _stored_rows(portal_page, site_id)
        path = f"{HISTORY_PAGE_PATH}?site_id={site_id}"
        _require_built_route(_page_status(portal_page, path), path)
        rows = set(_marker_keys(portal_page, HISTORY_ROW_PREFIX))
        assert rows <= set(_marker_keys(portal_page, HISTORY_OPEN_PREFIX)), "A row carries no open control."


class TestHistoryPaging:
    """The route settles the page window and the earlier page link states it."""

    def test_the_first_page_locks_the_earlier_control(self, portal_page: Any) -> None:
        """The earlier page control is a locked button on the first page.

        Why:
            `contracts/http-api.md:466` starts the page at offset zero, so no
            earlier page exists. A link with no target still takes a press, and a
            locked button takes none.

        Args:
            portal_page: The browser page that points at the portal.
        """
        _require_built_route(_page_status(portal_page, HISTORY_PAGE_PATH), HISTORY_PAGE_PATH)
        control = portal_page.get_by_test_id(HISTORY_PREVIOUS_ID)
        assert control.get_attribute("href") is None, "The first page offered an earlier page link."
        sync_api.expect(control).to_be_disabled(timeout=GATE_TIMEOUT_MS)

    def test_the_second_page_offers_an_earlier_page_link(self, portal_page: Any) -> None:
        """A page after the first offers a live link back to the first page.

        Why:
            An operator who steps forward must be able to step back. The address
            states the page the operator returns to.

        Args:
            portal_page: The browser page that points at the portal.
        """
        window = _earlier_page_window(portal_page, f"{OFFSET_FIELD}={DEFAULT_LIMIT}")
        assert window[OFFSET_FIELD] == str(FIRST_OFFSET), "The earlier page did not return to the first page."

    def test_an_absent_limit_reads_the_default_of_twenty_five(self, portal_page: Any) -> None:
        """The route reads 25 rows for one page when the address names no limit.

        Why:
            `contracts/http-api.md:466` fixes this default. The earlier page link
            carries the limit onward, so the address states what the route read.

        Args:
            portal_page: The browser page that points at the portal.
        """
        window = _earlier_page_window(portal_page, f"{OFFSET_FIELD}={DEFAULT_LIMIT}")
        assert window[LIMIT_FIELD] == str(DEFAULT_LIMIT), "The route did not read the default limit."

    def test_a_limit_above_the_bound_reads_two_hundred(self, portal_page: Any) -> None:
        """A limit above 200 reads 200.

        Why:
            `contracts/http-api.md:476` holds the limit at 200, because retention
            is unlimited and an unbounded limit lets one request read the whole
            store.

        Args:
            portal_page: The browser page that points at the portal.
        """
        window = _earlier_page_window(portal_page, f"{LIMIT_FIELD}=5000&{OFFSET_FIELD}=5000")
        assert window[LIMIT_FIELD] == str(LARGEST_LIMIT), "The route did not hold the limit at the upper bound."

    def test_a_limit_below_the_bound_reads_one(self, portal_page: Any) -> None:
        """A limit below 1 reads 1.

        Why:
            `contracts/http-api.md:476` holds the limit at 1. A page of zero rows
            would show nothing and would never reach the end of the store.

        Args:
            portal_page: The browser page that points at the portal.
        """
        window = _earlier_page_window(portal_page, f"{LIMIT_FIELD}=0&{OFFSET_FIELD}=10")
        assert window[LIMIT_FIELD] == str(SMALLEST_LIMIT), "The route did not hold the limit at the lower bound."

    def test_a_word_in_the_limit_reads_the_default(self, portal_page: Any) -> None:
        """Text that is not a number reads the default limit.

        Why:
            An address reaches the route from a browser and from a link, so a
            damaged value must not raise. The route falls back to the default.

        Args:
            portal_page: The browser page that points at the portal.
        """
        window = _earlier_page_window(portal_page, f"{LIMIT_FIELD}=every&{OFFSET_FIELD}={DEFAULT_LIMIT}")
        assert window[LIMIT_FIELD] == str(DEFAULT_LIMIT), "A word in the limit did not read the default."

    def test_an_offset_above_the_bound_reads_one_million(self, portal_page: Any) -> None:
        """An offset above 1000000 reads 1000000.

        Why:
            `contracts/http-api.md:476` holds the offset at this value. The
            earlier page then starts one page below the bound.

        Args:
            portal_page: The browser page that points at the portal.
        """
        window = _earlier_page_window(portal_page, f"{LIMIT_FIELD}={DEFAULT_LIMIT}&{OFFSET_FIELD}=99000000")
        assert window[OFFSET_FIELD] == str(LARGEST_OFFSET - DEFAULT_LIMIT), "The route did not hold the offset."


class TestHistoryNeedsNoLock:
    """No history route reads the site lock, so a read never waits."""

    def test_the_capture_history_answers_a_session_that_holds_no_lock(self, portal_page: Any, site_id: str) -> None:
        """The capture history endpoint answers a session that holds no lock.

        Why:
            `contracts/http-api.md:493` states that no history route reads the
            lock, because a read that waited for a lock would hide the record
            from the operator who watches another upgrade.

        Args:
            portal_page: The browser page that points at the portal.
            site_id: The site key that the endpoint path names.
        """
        body = _read_json(portal_page, HISTORY_API_TEMPLATE.format(site_id=site_id))
        assert isinstance(body.get(CAPTURES_FIELD), list), "The answer carries no capture list."
        assert isinstance(body.get(TOTAL_FIELD), int), "The answer carries no row total."

    def test_the_run_history_answers_a_session_that_holds_no_lock(self, portal_page: Any, site_id: str) -> None:
        """The run history endpoint answers a session that holds no lock.

        Why:
            `contracts/http-api.md:485` fixes the two names of this answer, and
            line 493 states that this read needs no lock either.

        Args:
            portal_page: The browser page that points at the portal.
            site_id: The site key that the endpoint path names.
        """
        body = _read_json(portal_page, RUN_HISTORY_API_TEMPLATE.format(site_id=site_id))
        assert isinstance(body.get(RUNS_FIELD), list), "The answer carries no run list."
        assert isinstance(body.get(TOTAL_FIELD), int), "The answer carries no row total."

    def test_the_history_page_answers_a_session_that_holds_no_lock(self, portal_page: Any) -> None:
        """The human history page opens for a session that holds no lock.

        Why:
            The page reads the same list as the endpoint. A page that asked for
            the lock would refuse the second operator the record they need.

        Args:
            portal_page: The browser page that points at the portal.
        """
        _require_built_route(_page_status(portal_page, HISTORY_PAGE_PATH), HISTORY_PAGE_PATH)
        sync_api.expect(portal_page.get_by_test_id(HISTORY_TABLE_ID)).to_be_visible(timeout=GATE_TIMEOUT_MS)

    def test_each_history_row_carries_the_eight_contract_names(self, portal_page: Any, site_id: str) -> None:
        """Every capture row of the answer carries the eight fixed names.

        Why:
            `contracts/http-api.md:469` fixes these eight names. The size
            satisfies FR-032b, and the two counts tell the operator what the
            capture holds.

        Args:
            portal_page: The browser page that points at the portal.
            site_id: The site key that the endpoint path names.
        """
        for row in _stored_rows(portal_page, site_id):
            missing = [name for name in ROW_NAMES if name not in row]
            assert not missing, f"A capture row carries none of these names: {missing}."
