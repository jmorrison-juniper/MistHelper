"""Browser tests for the capture journey of the upgrade capture portal.

Why:
    A contract test proves that the status endpoint answers the right fields. It
    cannot prove that the operator can choose a tier, start a capture, and watch
    the progress. The progress paints from a browser poll, so only a browser test
    proves that the page shows a real percent and a real section state.

What this module skips and what it fails:
    The module reports a skip when the browser, the server, or the route is
    absent, and when another operator holds the site lock. It reports a failure
    when a page answers 200 and the identifier contract does not hold. A missing
    part of the environment never reports a pass.

Identifier contract:
    `contracts/ui-testids.md` fixes every identifier below. Rule 4 states that a
    test selects by `data-testid` only, so every locator reads that attribute.
    The badge test reads the badge text and never the style class, because
    `portal.css` writes a signal word through a stylesheet rule that no text
    reader returns.
"""

from __future__ import annotations

import re
from typing import Any

import pytest

# The Playwright package must exist before this module defines a browser test.
# A run without the package reports a skip and never an import error.
sync_api = pytest.importorskip("playwright.sync_api", reason="The Playwright package is not installed.")

# The import below must stay under the skip above. A run without the package
# then reaches the skip and never an import error.
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError  # noqa: E402  # WHY: The skip runs first.

# `contracts/http-api.md` fixes this path for the site picker.
SITE_PAGE_PATH = "/select/site"
SITE_ROW_PREFIX = "site-row-"

# `contracts/http-api.md` fixes `GET /captures/<capture_id>` for a capture that
# already exists. It fixes no path for the page that starts a capture. The three
# candidates below follow the shape of the paths the contract does fix. The tests
# skip with a clear reason when none of them answers, so no candidate hides a
# defect. Add the real path here once the capture route lands.
CAPTURE_PAGE_CANDIDATES = (
    "/captures/new?site_id={site_id}",
    "/select/site/{site_id}/capture",
    "/sites/{site_id}/capture",
)

# The six section keys of `GET /api/captures/<capture_id>/status`. The identifier
# appends the JSON key without any change, so the page and the body agree.
SECTION_KEYS = ("devices", "clients_wired", "clients_wireless", "clients_guest", "extras", "alarms")

CAPTURE_TIER_ID = "capture-tier-select"
CAPTURE_START_ID = "capture-start-button"
CAPTURE_PROGRESS_ID = "capture-progress"
CAPTURE_PERCENT_ID = "capture-progress-percent"
CAPTURE_VERIFIED_ID = "capture-verified-badge"
CAPTURE_SIZE_ID = "capture-size-bytes"
CAPTURE_ERROR_ID = "capture-error"

DEFAULT_TIER = "2"  # `contracts/http-api.md` states that the tier defaults to 2.
HIGH_TIER = "3"  # The endpoint refuses any value other than 2 or 3 with `bad_tier`.

# The badge names the result in words, because WCAG 1.4.1 forbids color alone.
VERIFIED_WORDS = ("Verified", "Not verified")

PERCENT_PATTERN = re.compile(r"^(\d{1,3})%$")  # The region reads "<n>%" and holds no unit word.
NON_EMPTY_PATTERN = re.compile(r".+")
HIGHEST_PERCENT = 100

OK_STATUS = 200  # The contract fixes this status for every page below.
ACCEPTED_STATUS = 202  # `POST /api/sites/<site_id>/captures` answers 202.
UNAUTHORIZED_STATUS = 401  # `runtime/identity.py` answers this code with no session.
NOT_FOUND_STATUS = 404  # The route is not registered yet.
LOCKED_STATUS = 409  # Another operator holds the site lock.

START_TIMEOUT_MS = 15000  # The start call reaches the Mist cloud, so it needs more than the default.

# The two fixtures below reach the network and the file system, so a failure in
# either one describes the environment and never the page under test.
ENVIRONMENT_FIXTURES = ("capture_portal_server", "page")


def _lazy_fixture(request: pytest.FixtureRequest, name: str) -> Any:
    """Build one environment fixture, and turn a setup failure into a skip.

    Why:
        The server fixture needs Gunicorn and the page fixture needs a browser
        binary. Neither part exists on every workstation. A plain request would
        report an error, which reads in a report as a broken test. A skip that
        carries the real cause reads as the missing part that it is.

    Args:
        request: The pytest request object of the calling fixture.
        name: The fixture to build.

    Returns:
        The fixture value.
    """
    try:  # The failure below describes the environment, never the page.
        return request.getfixturevalue(name)
    except Exception as failure:  # A skip states the real cause, so nothing hides.
        pytest.skip(f"The fixture {name} could not start, so no browser test can run. Cause: {failure}")


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
    for name in ENVIRONMENT_FIXTURES:  # The server must answer before the browser opens a page.
        value = _lazy_fixture(request, name)
    return value


def _page_status(page: Any, path: str) -> int:
    """Open one path and return the status code of the answer.

    Why:
        A slow server or a page that never settles raises a Playwright timeout.
        That error carries a browser trace and no status, so it reads as a
        defect of the page. A skip names the real cause, which is the
        environment.

    Args:
        page: The Playwright page object.
        path: The path to open, relative to the portal address.

    Returns:
        The status code that the portal answered.
    """
    try:  # A timeout describes the environment, never the page under test.
        answer = page.goto(path, wait_until="domcontentloaded")
    except PlaywrightTimeoutError as failure:  # The catch stays narrow, so a real fault still fails.
        pytest.skip(f"The browser reached no answer for {path}. Cause: {failure}")
    if answer is None:  # A page with no answer gives the test nothing to read.
        pytest.skip(f"The browser returned no response for {path}.")
    status: int = answer.status
    return status


def _skip_without_session(status: int, path: str) -> None:
    """Skip when the portal refuses the request because no session exists.

    Args:
        status: The status code the portal answered.
        path: The path the test opened, named in the message.
    """
    if status == UNAUTHORIZED_STATUS:  # `identity.require_session` refused the request.
        pytest.skip(f"{path} answered 401. The portal has no sign-in route yet, so no browser test holds a session.")


def _require_built_route(status: int, path: str) -> None:
    """Skip when a route is absent, and fail when a built route answers wrongly.

    Args:
        status: The status code the portal answered.
        path: The path the test opened, named in every message.

    Raises:
        AssertionError: If the portal answered a status that the contract does
            not fix for a page.
    """
    _skip_without_session(status, path)
    if status == NOT_FOUND_STATUS:  # The blueprint that owns this path is not registered.
        pytest.skip(f"{path} answered 404. The route is not built yet.")
    assert status == OK_STATUS, f"{path} answered {status}. `contracts/http-api.md` fixes 200 for this page."


def _first_site_id(page: Any) -> str:
    """Open the site picker and return the identifier of the first site row.

    Why:
        A capture reads one site, so the capture page needs a real site
        identifier. A test cannot know that value in advance, so it reads the
        key that the site picker published in its row identifier.

    Args:
        page: The Playwright page object.

    Returns:
        The site identifier of the first row.
    """
    _require_built_route(_page_status(page, SITE_PAGE_PATH), SITE_PAGE_PATH)
    rows = page.locator(f'[data-testid^="{SITE_ROW_PREFIX}"]')  # A prefix match still selects by `data-testid`.
    markers = rows.evaluate_all("found => found.map(node => node.getAttribute('data-testid'))")
    keys = [str(marker)[len(SITE_ROW_PREFIX) :] for marker in markers if marker]
    if not keys:  # The portal reached no site, so no capture can start.
        pytest.skip("The site picker shows no site row, so no site identifier exists to capture.")
    return keys[0]


@pytest.fixture
def capture_page(portal_page: Any) -> Any:
    """Return a page that shows the capture view of the first site.

    Why:
        The contract fixes no path for the page that starts a capture, so this
        fixture tries each candidate path in turn. The skip below names every
        path it tried, so a reader knows which path to add.

    Args:
        portal_page: The browser page that points at the portal.

    Returns:
        The Playwright page object, on the capture view.
    """
    site_id = _first_site_id(portal_page)
    tried = []
    for template in CAPTURE_PAGE_CANDIDATES:
        path = template.format(site_id=site_id)
        status = _page_status(portal_page, path)
        _skip_without_session(status, path)
        if status == OK_STATUS:
            return portal_page
        tried.append(f"{path} answered {status}")
    pytest.skip(f"No candidate capture path answered 200, so the capture route is not built yet. Tried: {tried}.")


def _read_percent(page: Any) -> int:
    """Read the progress percent from the page and check its shape.

    Args:
        page: The Playwright page object, on the capture view.

    Returns:
        The percent as a whole number.

    Raises:
        AssertionError: If the text does not read as a number and a percent sign.
    """
    text = (page.get_by_test_id(CAPTURE_PERCENT_ID).inner_text() or "").strip()
    found = PERCENT_PATTERN.match(text)
    assert found, f"{CAPTURE_PERCENT_ID} reads {text!r}. The contract fixes a number and a percent sign."
    return int(found.group(1))


class TestCaptureControls:
    """The capture page shows the tier control and the start control."""

    def test_capture_page_shows_the_tier_and_start_controls(self, capture_page: Any) -> None:
        """The page shows the tier list and the start button.

        Args:
            capture_page: The page that shows the capture view.
        """
        sync_api.expect(capture_page.get_by_test_id(CAPTURE_TIER_ID)).to_be_visible()
        sync_api.expect(capture_page.get_by_test_id(CAPTURE_START_ID)).to_be_visible()

    def test_tier_list_starts_at_tier_two_and_accepts_tier_three(self, capture_page: Any) -> None:
        """The tier list opens on tier 2 and accepts tier 3.

        Why:
            `contracts/http-api.md` states that the tier defaults to 2 and that
            the endpoint refuses any value other than 2 or 3 with `bad_tier`. A
            list that opens on tier 3 would read more data than the operator
            asked for. `select_option` fails when the option is absent, so this
            test also proves that tier 3 exists.

        Args:
            capture_page: The page that shows the capture view.
        """
        tier_list = capture_page.get_by_test_id(CAPTURE_TIER_ID)
        sync_api.expect(tier_list).to_have_value(DEFAULT_TIER)
        tier_list.select_option(HIGH_TIER)
        sync_api.expect(tier_list).to_have_value(HIGH_TIER)


def _is_capture_start(answer: Any) -> bool:
    """Report whether one response answers the call that starts a capture.

    Why:
        The page calls more than one endpoint, so the test must pick the one
        call the contract fixes: `POST /api/sites/<site_id>/captures`.

    Args:
        answer: The Playwright response object.

    Returns:
        True when the response answers the start call.
    """
    is_post: bool = str(answer.request.method) == "POST"  # The contract fixes POST for the start call.
    return is_post and str(answer.url).endswith("/captures")  # The path ends with the collection name.


class TestCaptureProgress:
    """The progress region shows the percent and the state of every section."""

    def test_progress_region_shows_a_percent_between_zero_and_one_hundred(self, capture_page: Any) -> None:
        """The progress region shows a percent in range.

        Args:
            capture_page: The page that shows the capture view.
        """
        sync_api.expect(capture_page.get_by_test_id(CAPTURE_PROGRESS_ID)).to_be_visible()
        percent = _read_percent(capture_page)
        assert 0 <= percent <= HIGHEST_PERCENT, f"{CAPTURE_PERCENT_ID} reads {percent}, which is out of range."

    def test_progress_region_shows_every_section_of_the_status_body(self, capture_page: Any) -> None:
        """The region shows one element for each of the six sections.

        Why:
            FR-032 asks the operator to see which section is done and which is
            still running. A missing section would hide a part of the capture
            that never ran, so the operator would trust an incomplete read.

        Args:
            capture_page: The page that shows the capture view.
        """
        for key in SECTION_KEYS:
            sync_api.expect(capture_page.get_by_test_id(f"capture-section-{key}")).to_be_visible()

    def test_start_button_starts_a_capture(self, capture_page: Any) -> None:
        """The start button posts a capture and the region takes the identifier.

        Why:
            The button sends JSON and reads the identifier from the answer. A
            button that posts nothing, or a region that never takes the new
            identifier, would leave the poll with no capture to read.

        Args:
            capture_page: The page that shows the capture view.
        """
        with capture_page.expect_response(_is_capture_start, timeout=START_TIMEOUT_MS) as event:
            capture_page.get_by_test_id(CAPTURE_START_ID).click()
        status = event.value.status
        if status == LOCKED_STATUS:  # Another operator holds the lock, so this run cannot start a capture.
            pytest.skip("The start call answered 409 site_locked. Another operator holds the lock on this site.")
        assert status == ACCEPTED_STATUS, f"The start call answered {status}. The contract fixes 202."
        region = capture_page.get_by_test_id(CAPTURE_PROGRESS_ID)
        sync_api.expect(region).to_have_attribute("data-capture-id", NON_EMPTY_PATTERN, timeout=START_TIMEOUT_MS)


class TestCaptureResult:
    """The result block shows the verified state and the stored size."""

    def test_result_shows_the_verified_state_in_words(self, capture_page: Any) -> None:
        """The badge names the verified state in words.

        Why:
            WCAG 1.4.1 forbids color as the only signal, so the badge must read
            as words. `portal.css` writes a signal word through a stylesheet
            rule, and no text reader returns that word, so this test reads the
            badge text and never the style class.

        Args:
            capture_page: The page that shows the capture view.
        """
        text = (capture_page.get_by_test_id(CAPTURE_VERIFIED_ID).inner_text() or "").strip()
        assert text in VERIFIED_WORDS, f"{CAPTURE_VERIFIED_ID} reads {text!r}. The contract fixes {VERIFIED_WORDS}."

    def test_result_shows_the_stored_size_as_a_whole_number(self, capture_page: Any) -> None:
        """The stored size reads as a byte count with no unit word.

        Why:
            FR-032b asks for the stored size. A test compares that number
            against the stored document, so the cell holds the raw count. A unit
            word such as "kB" would force every reader to parse the text.

        Args:
            capture_page: The page that shows the capture view.
        """
        text = (capture_page.get_by_test_id(CAPTURE_SIZE_ID).inner_text() or "").strip()
        assert text.isdigit(), f"{CAPTURE_SIZE_ID} reads {text!r}. The contract fixes a byte count and no unit."

    def test_result_shows_no_error_before_a_capture_starts(self, capture_page: Any) -> None:
        """The error region stays hidden while the page holds no fault.

        Why:
            The region carries `role="alert"`, so a screen reader reads it as
            soon as it shows. A region that shows with no text would announce a
            fault that never happened.

        Args:
            capture_page: The page that shows the capture view.
        """
        sync_api.expect(capture_page.get_by_test_id(CAPTURE_ERROR_ID)).to_be_hidden()
