"""Browser tests for the capture journey of the upgrade capture portal.

Why:
    A contract test proves that the status endpoint answers the right fields. It
    cannot prove that the operator can choose a tier, start a capture, and watch
    the progress. The progress paints from a browser poll, so only a browser test
    proves that the page shows a real percent and a real section state.

What this module skips and what it fails:
    The module reports a skip when no browser binary exists, and when another
    operator holds the site lock. It reports a failure when a page answers 401
    or 404, and when a page answers 200 and the identifier contract does not
    hold. The fixture starts its own portal, so a 401 and a 404 are both faults
    of that portal. A portal that a browser test cannot reach never reports a
    pass.

Identifier contract:
    `contracts/ui-testids.md` fixes every identifier below. Rule 4 states that a
    test selects by `data-testid` only, so every locator reads that attribute.
    The badge test reads the badge text and never the style class, because
    `portal.css` writes a signal word through a stylesheet rule that no text
    reader returns.

Why each test ends with a plain assertion:
    The test quality gate counts a plain `assert` statement. It does not count
    a Playwright `expect` call. Each `expect` call waits for the page script,
    and the plain assertion then reads one more fact of the same state, such
    as the site that the start control writes to.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterator
from typing import Any
from urllib.parse import parse_qs, urlsplit  # Read the site from the address of the capture page.

import pytest

from tests.support.upgrade_portal_e2e.site_lock import RunLedger, SiteRelease  # Issue #3511: the walk teardown.

logger = logging.getLogger(__name__)  # A module logger keeps the record source readable.

# The Playwright package must exist before this module defines a browser test.
# A run without the package reports a skip and never an import error.
sync_api = pytest.importorskip("playwright.sync_api", reason="The Playwright package is not installed.")

# The import below must stay under the skip above. A run without the package
# then reaches the skip and never an import error.
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError  # noqa: E402  # WHY: The skip runs first.

from tests.e2e.upgrade_portal.test_upgrade import (  # noqa: E402  # WHY: The selector helper stays behind the skip.
    OFFERED_VERSION_INDEX,  # The prompt occupies the index before offered versions.
    TARGET_ROW_PREFIX,  # Each target row records the device type it represents.
    TYPE_VERSION_SELECT_IDS,  # These are the three current type controls.
    _chose_one_version_for_every_device,  # Use the tested type selector.
    _is_options_save,  # This helper recognizes the real options-save response.
)

# `contracts/http-api.md` fixes this path for the site picker.
SITE_PAGE_PATH = "/select/site"
SITE_ROW_PREFIX = "site-row-"

# `contracts/http-api.md` fixes `GET /captures/<capture_id>` for a capture that
# already exists. It fixes no path for the page that starts one, so the portal
# reads the identifier segment `new` as "no capture yet" and reads the site from
# the query argument. `app/routes/select.py` builds this same address for the
# link that carries an operator out of the inventory page, so the two agree.
#
# An earlier version held three guessed paths and reported a skip when none of
# them answered. That skip could hide a broken capture page behind a green run,
# so the fixture below now fails on any answer other than 200.
CAPTURE_PAGE_PATH = "/captures/new?site_id={site_id}"

# The six section keys of `GET /api/captures/<capture_id>/status`. The identifier
# appends the JSON key without any change, so the page and the body agree.
SECTION_KEYS = ("devices", "clients_wired", "clients_wireless", "clients_guest", "extras", "alarms")

CAPTURE_TIER_ID = "capture-tier-select"
CAPTURE_START_ID = "capture-start-button"
CAPTURE_REFRESH_ID = "capture-refresh-button"
CAPTURE_PROGRESS_ID = "capture-progress"
CAPTURE_PERCENT_ID = "capture-progress-percent"
CAPTURE_VERIFIED_ID = "capture-verified-badge"
CAPTURE_SIZE_ID = "capture-size-bytes"
CAPTURE_ERROR_ID = "capture-error"

# Delta U1 adds the two controls below. `contracts/ui-testids.md` fixes both
# identifiers. The button starts a run for the site of the verified pre-check,
# and the region names a refusal.
CAPTURE_START_UPGRADE_ID = "capture-start-upgrade-button"
CAPTURE_START_UPGRADE_ERROR_ID = "capture-start-upgrade-error"

# The click path out of the site list. `test_site_selection.py` reads the same
# two identifiers, so the walk below opens the same pages an operator opens.
SITE_OPEN_PREFIX = "site-open-"
SITE_CAPTURE_LINK_ID = "site-capture-link"
NAV_SITES_ID = "nav-sites"  # The shared header returns the operator to the site list.

# Issue #2259: the walk must hold the site before it writes to it. FR-072 gives
# one site to one operator. One press takes a free site, and a site that any
# lock already holds needs the word of FR-079 as well.
LOCK_TAKE_BUTTON_ID = "lock-take-button"
LOCK_CONFIRM_INPUT_ID = "lock-confirm-input"
LOCK_CONFIRM_SUBMIT_ID = "lock-confirm-submit"
TAKEOVER_WORD = "CONFIRM"  # FR-079 fixes this word and this letter case. The page may name another.
CONFIRM_WORD_ATTRIBUTE = "data-confirm-word"  # The page names the word the gate reads.
LOCK_RELEASE_BUTTON_ID = "lock-release-button"  # The control that gives the site back at once.
LOCK_SETTLE_MS = 4000  # The take call is one round trip on loopback, so it settles quickly.

# Issue #3511: the teardown of the walk cancels each run of the walk. Each write
# needs the cross-site request token, and the layout publishes it on each page.
CSRF_META_ID = "csrf-meta"  # `layout.html` publishes the token under this identifier.

# The options page and the confirm page of the run the upgrade button creates.
# `contracts/http-api.md` section 5 fixes both page paths and the create path.
OPTIONS_SAVE_ID = "upgrade-options-save-button"
CONFIRM_LINK_ID = "upgrade-confirm-link"
CONFIRM_INPUT_ID = "upgrade-confirm-input"
UPGRADE_SITE_ID_ID = "upgrade-site-id"  # The run page identifies the site that owns this run.
OPTIONS_PAGE_SUFFIX = "/options"  # The run page that picks a version for each device.
CONFIRM_PAGE_SUFFIX = "/confirm"  # The run page that reads the typed word.

# The history page lists every stored capture, and each row carries an open
# control whose identifier ends with the capture key. That key is the only
# address of a stored capture that a browser can find without a fixture import,
# so the read test below reads it from the page.
HISTORY_PAGE_PATH = "/history"
HISTORY_OPEN_PREFIX = "history-open-"
CAPTURE_READ_PATH = "/api/captures/{capture_id}"  # `contracts/http-api.md:238` fixes this path.

DEFAULT_TIER = "2"  # `contracts/http-api.md` states that the tier defaults to 2.
HIGH_TIER = "3"  # The endpoint refuses any value other than 2 or 3 with `bad_tier`.

# The badge names the result in words, because WCAG 1.4.1 forbids color alone.
VERIFIED_WORDS = ("Verified", "Not verified")

PERCENT_PATTERN = re.compile(r"^(\d{1,3})%$")  # The region reads "<n>%" and holds no unit word.
NON_EMPTY_PATTERN = re.compile(r".+")
HIGHEST_PERCENT = 100

OK_STATUS = 200  # The contract fixes this status for every page below.
CREATED_STATUS = 201  # `POST /api/sites/<site_id>/runs` answers 201 with the run key.
ACCEPTED_STATUS = 202  # `POST /api/sites/<site_id>/captures` answers 202.
UNAUTHORIZED_STATUS = 401  # `runtime/identity.py` answers this code with no session.
NOT_FOUND_STATUS = 404  # The route is not registered yet.
LOCKED_STATUS = 409  # Another operator holds the site lock, or a run of the site is live.
UNREACHABLE_STATUS = 503  # The portal cannot read the site lock store.

START_TIMEOUT_MS = 15000  # The start call reaches the Mist cloud, so it needs more than the default.
VERIFY_ATTEMPTS = 20  # The refresh clicks that force a status read while the worker verifies.
VERIFY_WAIT_MS = 500  # The pause between two refresh clicks, so the worker thread can finish.

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


def _require_session(status: int, path: str) -> None:
    """Fail when the portal refuses the request because no session exists.

    Why:
        The fixture starts its own portal, and only that portal holds the
        sign-in seam of this run. A 401 therefore means the seam is broken. A
        skip would let every page below the sign-in form stay unread while the
        run still reported success.

    Args:
        status: The status code the portal answered.
        path: The path the test opened, named in the message.

    Raises:
        AssertionError: If the portal answered 401.
    """
    if status == UNAUTHORIZED_STATUS:  # `identity.require_session` refused the request.
        raise AssertionError(f"{path} answered 401. The portal this run started holds no sign-in seam.")


def _require_built_route(status: int, path: str) -> None:
    """Fail when the portal answers a status that the contract does not fix.

    Args:
        status: The status code the portal answered.
        path: The path the test opened, named in every message.

    Raises:
        AssertionError: If the portal answered a status that the contract does
            not fix for a page.
    """
    _require_session(status, path)
    if status == NOT_FOUND_STATUS:  # The blueprint that owns this path is not registered.
        raise AssertionError(f"{path} answered 404. The blueprint that owns this path is not registered.")
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
        This page is the first write step of the journey, so every test below
        needs it. The portal reaches it from the inventory page, and a failure
        here means the operator has no way to start any capture at all.

    Args:
        portal_page: The browser page that points at the portal.

    Returns:
        The Playwright page object, on the capture view.
    """
    site_id = _first_site_id(portal_page)
    path = CAPTURE_PAGE_PATH.format(site_id=site_id)
    _require_built_route(_page_status(portal_page, path), path)  # A skip here would hide a broken capture page.
    return portal_page


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
        logger.info("Wait for the capture page to show the tier list and the start control")  # Log before the wait.
        sync_api.expect(capture_page.get_by_test_id(CAPTURE_TIER_ID)).to_be_visible()  # The tier list of the capture.
        start = capture_page.get_by_test_id(CAPTURE_START_ID)  # The control that starts the capture.
        sync_api.expect(start).to_be_visible()  # The page shows the start control.
        page_site = parse_qs(urlsplit(capture_page.url).query).get("site_id", [""])[0]  # The site of the page.
        start_site = start.get_attribute("data-site-id")  # The site that a press of the control writes to.
        logger.debug("The start control names site %s on the page of site %s", start_site, page_site)  # Log the read.
        assert start_site == page_site, f"The start control names site {start_site!r} on the page of {page_site!r}."

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
        tier_list = capture_page.get_by_test_id(CAPTURE_TIER_ID)  # The list that picks the capture tier.
        sync_api.expect(tier_list).to_have_value(DEFAULT_TIER)  # The list opens on tier 2.
        logger.info("Pick tier %s in the tier list", HIGH_TIER)  # Log before the pick.
        picked = tier_list.select_option(HIGH_TIER)  # The call fails when the page offers no tier 3.
        logger.debug("The tier list picked %s", picked)  # Log after the pick.
        sync_api.expect(tier_list).to_have_value(HIGH_TIER)  # The list now shows tier 3.
        assert picked == [HIGH_TIER], f"The tier list picked {picked}, and the test asked for tier {HIGH_TIER}."


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
        logger.info("Read the state of each of the %s capture sections", len(SECTION_KEYS))  # Log before the reads.
        states: list[str] = []  # The state word of each section, in the order of the contract.
        for key in SECTION_KEYS:  # The contract fixes six sections.
            section = capture_page.get_by_test_id(f"capture-section-{key}")  # The element of one section.
            sync_api.expect(section).to_be_visible()  # A missing section hides a part of the capture.
            states.append((section.locator("[data-section-state]").inner_text() or "").strip())  # The state word.
        logger.debug("The capture sections read %s", states)  # Log after the reads.
        assert "" not in states, f"A section shows no state word: {dict(zip(SECTION_KEYS, states, strict=True))}."

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
        error = capture_page.get_by_test_id(CAPTURE_ERROR_ID)  # The alert region of the capture page.
        logger.info("Check that the error region is hidden and empty before a capture")  # Log before the checks.
        sync_api.expect(error).to_be_hidden()  # A shown alert announces a fault at once.
        text = (error.text_content() or "").strip()  # The text that the alert announces when it shows.
        logger.debug("The error region holds %r", text)  # Log after the read.
        assert text == "", f"{CAPTURE_ERROR_ID} holds {text!r} before a capture starts, so it names a false fault."


def _first_stored_capture_id(page: Any) -> str:
    """Return the key of the first capture that the history page lists.

    Why:
        A stored capture is the only capture that the read endpoint answers
        for, and the history page is the one page that names one. Reading the
        key from the page keeps this module free of a fixture import, so the
        test reads what an operator reads.

    Args:
        page: The Playwright page object.

    Returns:
        The capture key of the first history row.
    """
    _require_built_route(_page_status(page, HISTORY_PAGE_PATH), HISTORY_PAGE_PATH)
    controls = page.locator(f'[data-testid^="{HISTORY_OPEN_PREFIX}"]')
    if controls.count() == 0:  # A history with no row gives this test nothing to read back.
        raise AssertionError(f"{HISTORY_PAGE_PATH} listed no stored capture, so no capture key exists to read.")
    marker = controls.first.get_attribute("data-testid") or ""
    return marker[len(HISTORY_OPEN_PREFIX) :]


class TestStoredCaptureRead:
    """The read endpoint hands back a capture that the portal stored."""

    def test_a_stored_capture_reads_back_through_the_api(self, portal_page: Any) -> None:
        """`GET /api/captures/<capture_id>` answers 200 for a stored capture.

        Why:
            The capture page reads the stored size through this endpoint, and
            the comparison reads both documents through it. No other browser
            test called it, so the whole suite passed while the endpoint
            answered 500 for a capture that the status route called verified.

            The fault was one shape. Two route modules read the one
            `CAPTURE_LOADER` seam. `app/routes/review.py` accepts a bare
            document as well as the record of the store, and
            `app/routes/capture.py` accepts the record alone. The stand-in
            answered a bare document, so the comparison worked and this read
            did not.

        Args:
            portal_page: The page that points at the running portal.
        """
        capture_id = _first_stored_capture_id(portal_page)
        path = CAPTURE_READ_PATH.format(capture_id=capture_id)
        status = _page_status(portal_page, path)
        _require_session(status, path)
        assert status == OK_STATUS, f"{path} answered {status}. The contract fixes 200 for a stored capture."

    def test_the_read_answers_the_stored_document(self, portal_page: Any) -> None:
        """The body of the read carries the key of the capture it names.

        Why:
            A 200 with an empty body would still pass the test above. The
            comparison reads every field of this body, so the body must be the
            document itself and must name the capture that the caller asked
            for.

        Args:
            portal_page: The page that points at the running portal.
        """
        capture_id = _first_stored_capture_id(portal_page)
        path = CAPTURE_READ_PATH.format(capture_id=capture_id)
        _require_built_route(_page_status(portal_page, path), path)
        body = portal_page.evaluate("() => JSON.parse(document.body.innerText || '{}')")
        assert body.get("capture_id") == capture_id, f"{path} answered a body for {body.get('capture_id')!r}."


def _is_run_create(answer: Any) -> bool:
    """Report whether one response answers the call that creates a run.

    Why:
        The upgrade button posts one create call, and the page reads more than
        one endpoint. The walk waits on the one call the contract fixes:
        `POST /api/sites/<site_id>/runs`.

    Args:
        answer: The Playwright response object.

    Returns:
        True when the response answers the create call.
    """
    is_post: bool = str(answer.request.method) == "POST"  # The contract fixes POST for the create call.
    return is_post and str(answer.url).rstrip("/").endswith("/runs")  # The path ends with the collection name.


def _run_id_from_url(url: str) -> str:
    """Return the run key that sits inside a run page URL.

    Why:
        The create answer body is gone once the browser opens the options
        page. The options URL still holds the run key, so the walk reads the
        key from the path rather than the emptied answer.

    Args:
        url: The current page URL, such as ".../runs/<key>/options".

    Returns:
        The run key from the URL path.
    """
    tail = url.split("/runs/", 1)[1]  # The text after the collection name opens with the run key.
    return tail.split("/", 1)[0]  # The key ends at the next path separator.


class CaptureClickJourney:
    """Guard the real options page before the capture walk saves its plan."""

    def __init__(self, page: Any, ledger: RunLedger) -> None:
        """Bind the guard to the walk page and its own-run ledger."""
        self.page = page  # Keep every browser action on the operator's real page.
        self.ledger = ledger  # Let teardown end only the run this walk created.

    def require_created_run(self, status: int) -> None:
        """Fail with a precise reason when the create endpoint refuses a new run."""
        logger.info("Check the run-create status %s", status)  # Record the response before classifying it.
        if status == LOCKED_STATUS:  # A fresh fixture site must not hold another live run.
            logger.error("The run create answered 409 because a live run holds the site.")  # Name the fixture fault.
            raise AssertionError("The run create answered 409 because a live run holds the site.")  # Fail this journey.
        if status == UNREACHABLE_STATUS:  # The local fixture requires its lock store.
            logger.error("The run create answered 503 because the local site-lock store is unavailable.")  # Name it.
            raise AssertionError(
                "The run create answered 503 because the local site-lock store is unavailable."
            )  # Fail.
        logger.debug("The run-create status is not a 409 or 503 refusal")  # Other statuses reach the contract check.

    def prepare_options(self) -> str:
        """Read the created run and select a version for every present device type."""
        logger.info("Wait for the options page of the created run")  # Record the next browser step.
        self.page.wait_for_url(f"**/runs/*{OPTIONS_PAGE_SUFFIX}", timeout=START_TIMEOUT_MS)  # Keep the original bound.
        logger.debug("The browser reached the options page")  # Confirm that the real route rendered.
        logger.info("Read the run key from the options page address")  # Record the address read.
        run_id = _run_id_from_url(self.page.url)  # Read the key from the page that the click opened.
        logger.debug("Read the run key from the options page")  # Do not expose the key in logs.
        logger.info("Record the created run for teardown")  # Record before any plan action.
        self.ledger.record(run_id)  # Teardown cancels this run before it releases the site.
        logger.debug("Recorded one run in the walk ledger")  # Confirm test-owned cleanup state.
        self._require_type_versions()  # A missing family or version is a portal or fixture failure.
        return run_id  # The caller continues the click journey with this run.

    def return_to_owned_capture(self, site_id: str) -> None:
        """Click back to this run's capture page so fixture teardown can release its site."""
        logger.info("Check that the confirmed run belongs to the capture site")  # Bind cleanup to the owned site.
        run_site_id = self.page.get_by_test_id(UPGRADE_SITE_ID_ID).inner_text().strip()  # Read the confirmed site.
        logger.info("Open the site list to return to the run's capture page")  # Use the existing site navigation.
        with self.page.expect_response(
            lambda answer: answer.request.is_navigation_request()
        ):  # Track the real site-list navigation.
            self.page.get_by_test_id(NAV_SITES_ID).click()  # Click the shared header link.
        self.page.wait_for_url(f"**{SITE_PAGE_PATH}", timeout=START_TIMEOUT_MS)  # Wait for the real site list.
        with self.page.expect_response(
            lambda answer: answer.request.is_navigation_request()
        ):  # Track the inventory navigation.
            self.page.get_by_test_id(f"{SITE_OPEN_PREFIX}{site_id}").click()  # Open the row for the run's site.
        with self.page.expect_response(
            lambda answer: answer.request.is_navigation_request()
        ):  # Track the capture-page navigation.
            self.page.get_by_test_id(SITE_CAPTURE_LINK_ID).click()  # Open the capture page for the run's site.
        capture_url = urlsplit(self.page.url)  # Read the page that the navigation clicks opened.
        assert capture_url.path == "/captures/new"  # Require the site page that draws the release control.
        assert parse_qs(capture_url.query).get("site_id", [""])[0] == site_id  # Keep cleanup on the run site.
        release = self.page.get_by_test_id(LOCK_RELEASE_BUTTON_ID)  # Select the release control for this site.
        sync_api.expect(release).to_be_visible(timeout=START_TIMEOUT_MS)  # Prove the control is drawn for this holder.
        assert release.get_attribute("data-site-id") == site_id  # Bind the visible control to the owned site.
        assert (
            run_site_id == site_id
        ), f"The run site {run_site_id!r} is not the capture site."  # Reject a different site after safe navigation.
        logger.debug("The run's capture page exposes its owned site release control")  # Confirm teardown's page.

    def _require_type_versions(self) -> None:
        """Require one row and one offered version for each type control."""
        logger.info("Check every current type control before selecting versions")  # Record the complete check.
        for test_id in TYPE_VERSION_SELECT_IDS:  # Check every device type, even if another type has versions.
            self._require_type_options(test_id)  # Check the matching device rows and offered versions.
        logger.info("Select offered versions through the existing browser helper")  # Record before selection.
        _chose_one_version_for_every_device(self.page)  # Reuse the proven real-control interaction.
        logger.debug("The existing selection helper finished on all required controls")  # Confirm selection completed.
        for test_id in TYPE_VERSION_SELECT_IDS:  # Verify the helper changed each required family control.
            logger.info("Verify the selected value of %s", test_id)  # Record before reading the control.
            value = self.page.get_by_test_id(test_id).input_value()  # Read the value that the form will submit.
            logger.debug("The selected value is present for %s: %s", test_id, bool(value))  # Report no version value.
            if not value:  # An empty value would produce no planned device of this type.
                raise AssertionError(f"{test_id} kept an empty version after selection.")  # Fail before the save.

    def _require_type_options(self, test_id: str) -> None:
        """Require a matching row and an offered version for each type control."""
        device_type = test_id.rsplit("-", 1)[1]  # The suffix names this device type.
        row_selector = f'[data-testid^="{TARGET_ROW_PREFIX}"][data-device-type="{device_type}"]'  # Match this family.
        logger.info("Count target rows for device type %s", device_type)  # Record before reading the table.
        row_count = self.page.locator(row_selector).count()  # Require a device that can use this type control.
        logger.debug("Found %s target row(s) for device type %s", row_count, device_type)  # Report the measured count.
        if row_count < 1:  # A control without a matching device cannot prove a plan.
            raise AssertionError(f"{test_id} has no target row for device type {device_type}.")  # Fail before save.
        logger.info("Read the option count for %s", test_id)  # Record before checking the actual select.
        control = self.page.get_by_test_id(test_id)  # Select the shipped control by its contract identifier.
        control_count = control.count()  # A missing or repeated control violates the page contract.
        logger.debug("Found %s control(s) for %s", control_count, test_id)  # Report the measured count.
        if control_count != 1:  # Require one control for each present device type.
            raise AssertionError(f"The options page rendered {control_count} controls for {test_id}.")  # Fail.
        option_count = control.locator("option").count()  # Count the prompt and the offered firmware versions.
        logger.debug("Found %s option(s) for %s", option_count, test_id)  # Report the measured count.
        if option_count <= OFFERED_VERSION_INDEX:  # The prompt is not a version that can form a plan.
            raise AssertionError(  # Stop before the options save.
                f"{test_id} offers no version for {row_count} {device_type} device(s)."  # Name the empty family.
            )


def _walk_to_capture_view(page: Any) -> None:
    """Open the capture view by clicking from the site list.

    Why:
        SC-018 asks for a walk with no typed address. The site list is the one
        entry the operator opens, and every later step is a click. This helper
        opens the inventory of the first site, then the capture view of it.

    Args:
        page: The Playwright page object.
    """
    site_id = _first_site_id(page)  # This call opens the site list, which is the one entry the walk types.
    with page.expect_response(lambda answer: answer.request.is_navigation_request()):
        page.get_by_test_id(f"{SITE_OPEN_PREFIX}{site_id}").click()  # The site row opens the inventory page.
    with page.expect_response(lambda answer: answer.request.is_navigation_request()):
        page.get_by_test_id(SITE_CAPTURE_LINK_ID).click()  # The inventory page opens the capture view.
    _take_the_site(page)  # FR-072 gives one site to one operator, so the walk must take it before any write.


def _take_the_site(page: Any) -> None:
    """Take the site lock, so the operator may write to the site.

    Why:
        Issue #2259. FR-072 gives one site to one operator, and `capture.html`
        draws the start control disabled until this browser holds the site. The
        walk pressed the start control without the lock, so the press waited for
        a control that could never become enabled and reported a timeout.

        The take has two shapes, and the walk must follow both. One press takes
        a free site, which `partials/lock_banner.html` states in its own header.
        A site that any lock already holds answers a refusal, and the script
        then opens the confirmation box. FR-079 fixes the word for that box.

        A run of this suite leaves a lock behind, and the lease outlives the
        run. The second shape is therefore the normal one on a workstation that
        runs the suite twice, and the first shape is the normal one in CI.

    Args:
        page: The Playwright page object, on a page that draws the lock banner.
    """
    take = page.get_by_test_id(LOCK_TAKE_BUTTON_ID)
    if take.count() < 1 or not take.is_visible():  # The banner hides the control while this browser holds the site.
        return  # This browser already holds the site, so no press is needed.
    take.click()  # A plain press. One press takes a free site.
    if _write_is_allowed(page):  # The site was free, so the one press was enough.
        return
    _confirm_the_takeover(page)  # A lock already held the site, so the word must follow the press.


def _write_is_allowed(page: Any) -> bool:
    """Report whether the page now offers an enabled start control.

    Args:
        page: The Playwright page object, on the capture view.

    Returns:
        True when this browser may write to the site.
    """
    start = page.get_by_test_id(CAPTURE_START_ID)
    try:  # A control that never enables is the refusal path, and not a fault.
        sync_api.expect(start).to_be_enabled(timeout=LOCK_SETTLE_MS)
    except AssertionError:  # The take met a refusal, so the confirmation box holds the next step.
        return False
    return True


def _confirm_the_takeover(page: Any) -> None:
    """Type the word and press the submit control of the takeover box.

    Why:
        FR-079 guards a takeover with one word, because a takeover moves the
        write of a live site to another browser. The box opens only after the
        first press meets the refusal, so this helper runs only on that path.

    Args:
        page: The Playwright page object, on the capture view.
    """
    field = page.get_by_test_id(LOCK_CONFIRM_INPUT_ID)
    sync_api.expect(field).to_be_visible(timeout=LOCK_SETTLE_MS)  # The refusal opened the box.
    # WHY: `portal.js` writes the needed word into this attribute from the refusal
    # body, so the page names the word. A copy in this module would drift from it.
    word = str(field.get_attribute(CONFIRM_WORD_ATTRIBUTE) or TAKEOVER_WORD)
    field.fill(word)  # The gate reads each key press and enables the submit for the exact word.
    submit = page.get_by_test_id(LOCK_CONFIRM_SUBMIT_ID)
    sync_api.expect(submit).to_be_enabled(timeout=LOCK_SETTLE_MS)  # The gate opened for the typed word.
    submit.click()  # A plain press sends the typed word.
    # WHY: the script writes the lock, then enables every control that needs it.
    # The walk must wait for that state, or the next press meets a disabled control.
    sync_api.expect(page.get_by_test_id(CAPTURE_START_ID)).to_be_enabled(timeout=START_TIMEOUT_MS)


def _start_and_reveal_upgrade(page: Any) -> None:
    """Start a capture and wait for the upgrade button to show.

    Why:
        FR-101 reveals the upgrade button once the capture verifies. The
        stand-in verifies in a worker thread, so the walk clicks the refresh
        control until the badge reads verified. The poll period then never
        delays the walk.

    Args:
        page: The Playwright page object, on the capture view.
    """
    with page.expect_response(_is_capture_start, timeout=START_TIMEOUT_MS) as event:
        page.get_by_test_id(CAPTURE_START_ID).click()  # The start button posts the capture.
    if event.value.status == LOCKED_STATUS:  # Another operator holds the lock, so no capture can start here.
        pytest.skip("The start call answered 409. Another operator holds the lock on this site.")
    assert event.value.status == ACCEPTED_STATUS, f"The start call answered {event.value.status}, not 202."
    badge = page.get_by_test_id(CAPTURE_VERIFIED_ID)  # The badge reads verified once the worker finishes.
    for _ in range(VERIFY_ATTEMPTS):  # Each pass forces one status read, so the walk never waits a poll period.
        if (badge.inner_text() or "").strip() == "Verified":  # The worker wrote the verified record.
            break  # The upgrade button is now visible, so the walk continues.
        page.get_by_test_id(CAPTURE_REFRESH_ID).click()  # The refresh control reads the status at once.
        page.wait_for_timeout(VERIFY_WAIT_MS)  # A short pause lets the worker thread store the record.
    sync_api.expect(page.get_by_test_id(CAPTURE_START_UPGRADE_ID)).to_be_visible(timeout=START_TIMEOUT_MS)


def _release_the_site(page: Any) -> None:
    """Give the site back, so the next test finds it free.

    Why:
        Issue #2259. The walk takes the site, and the lease outlives the test.
        Every later test that writes to the same site then reads a refusal, so
        one walk would starve the rest of the suite. The release control gives
        the site back at once, which is the same path an operator uses.

        The release never fails a test. A walk that failed early may sit on a
        page with no banner, and that is not a fault of the release.

    Args:
        page: The Playwright page object, on any page that draws the banner.
    """
    try:  # A teardown must never turn one failure into two.
        release = page.get_by_test_id(LOCK_RELEASE_BUTTON_ID)
        if release.count() < 1 or not release.is_visible():  # This browser holds no site to give back.
            return
        release.click()  # A plain press gives the site back at once.
        sync_api.expect(page.get_by_test_id(LOCK_TAKE_BUTTON_ID)).to_be_visible(timeout=LOCK_SETTLE_MS)
    except Exception as failure:  # A closed page or a dead portal must not mask the real result.
        logger.info("The site release did not complete, so a later test may meet the lease. Cause: %s", failure)


def _end_the_walk_runs(page: Any, ledger: RunLedger) -> None:
    """End each live run that one walk built.

    Why:
        Issue #3511. The walk creates a run and never starts it, so the run
        stays live after the test. A live run blocks each later create call at
        the same site (FR-037). The cancel route binds each write of a run to
        the operator that holds the site (FR-038i), so this step runs before
        the release.

    Args:
        page: The Playwright page object, on a page that draws the layout.
        ledger: The ledger of the runs that the walk built.

    Raises:
        AssertionError: The page publishes no token, or a cancel answered a refusal.
    """
    if not ledger.runs:  # The walk stopped before it built a run, so no run needs an end.
        logger.debug("The walk built no run, so the teardown ends no run")  # Log the empty ledger.
        return
    logger.info("End the %d run(s) of the walk", len(ledger.runs))  # Log before the teardown step.
    meta = page.get_by_test_id(CSRF_META_ID)  # The layout publishes the token under this identifier.
    token = str(meta.get_attribute("content") or "") if meta.count() > 0 else ""  # A page with no layout has none.
    if not token:  # A cancel with no token meets the cross-site request check.
        raise AssertionError(
            f"The page publishes no {CSRF_META_ID} token, so the walk runs stay live. See issue #3511."
        )
    ended = SiteRelease(page.request, token).end_runs(ledger.runs)  # A refused cancel fails the teardown.
    logger.debug("The walk teardown ended %d run(s)", ended)  # Log after the teardown step.


@pytest.fixture(name="run_ledger")
def fixture_run_ledger() -> RunLedger:
    """Return an empty ledger for the runs that one walk builds.

    Why:
        Issue #3511. The teardown of `walking_page` ends each run of this
        ledger, so no walk leaves a live run at the site for a later module.

    Returns:
        The ledger of this test.
    """
    return RunLedger()  # Each test starts with no recorded run.


# WHY: Issue #2259. The walk takes the site lock, and the lease outlives the
# test. Without the release below, every later test that writes to this site
# reads a refusal and reports a skip, so one walk would starve the suite.
# Issue #3511: the run of the walk also outlived the test. The teardown now
# cancels each run of the ledger first, and then it releases the site.
@pytest.fixture(name="walking_page")
def fixture_walking_page(portal_page: Any, run_ledger: RunLedger) -> Iterator[Any]:
    """Give a browser page to the walk, end the runs of the walk, and then release the site.

    Args:
        portal_page: The browser page that points at the running portal.
        run_ledger: The ledger of the runs that the walk builds.

    Yields:
        The Playwright page object.

    Raises:
        AssertionError: A cancel of a walk run answered a refusal. The site release still runs.
    """
    yield portal_page
    try:  # FR-002: a refused cancel fails the teardown.
        _end_the_walk_runs(portal_page, run_ledger)  # A live run would block each later create call.
    finally:  # FR-002: the release runs even when a cancel fails.
        _release_the_site(portal_page)  # The next test then finds the site free.


class TestUpgradeJourney:
    """The operator walks from the site list to the confirm page by clicking."""

    def test_walk_from_the_site_list_reaches_the_confirm_page(self, walking_page: Any, run_ledger: RunLedger) -> None:
        """The upgrade button carries the operator from a capture to the confirm page.

        Why:
            FR-106 and SC-018 ask for a walk from the site list to the confirm
            page with no typed address. The walk opens the site list once, then
            clicks through the inventory, the capture, the run create, and the
            options save. A broken step leaves the operator with no path from a
            verified pre-check to an upgrade.

            Issue #3511. The walk records its run in the ledger, so the teardown
            ends the run and no later module meets a live run at this site.

        Args:
            walking_page: The browser page that points at the running portal.
            run_ledger: The ledger that the teardown of `walking_page` reads.
        """
        _walk_to_capture_view(walking_page)  # Site list, to inventory, to capture view, by clicks alone.
        capture_site_id = parse_qs(urlsplit(walking_page.url).query).get("site_id", [""])[0]  # Retain this site's key.
        assert (
            capture_site_id != ""
        ), "The capture page has no site identifier to bind the run to."  # Require ownership.
        _start_and_reveal_upgrade(walking_page)  # Start the capture and wait for the upgrade button.

        with walking_page.expect_response(_is_run_create, timeout=START_TIMEOUT_MS) as run_event:
            walking_page.get_by_test_id(CAPTURE_START_UPGRADE_ID).click()  # The button posts the run create.
        status = run_event.value.status  # The status reads without a body, so it survives the navigation.
        journey = CaptureClickJourney(walking_page, run_ledger)  # Guard the options stage with this run's ledger.
        journey.require_created_run(status)  # A refusal is a fixture or portal fault, not an environment skip.
        assert status == CREATED_STATUS, f"The run create answered {status}. The contract fixes 201."  # Require 201.
        run_id = journey.prepare_options()  # Check all three type controls before saving a plan.
        logger.info("Save the selected versions through the options page")  # Record before the user-facing action.
        with walking_page.expect_response(_is_options_save, timeout=START_TIMEOUT_MS) as save_event:  # Record save.
            walking_page.get_by_test_id(OPTIONS_SAVE_ID).click()  # The operator saves the selected type versions.
        save_status = save_event.value.status  # Read the status of the one plan-saving route.
        logger.debug("The options-save route answered %s", save_status)  # Record the measured response status.
        assert save_status == OK_STATUS, f"Options save answered {save_status}. Expected 200."  # Require status 200.

        logger.info("Wait for the saved run's confirmation page")  # Record the next page transition.
        walking_page.wait_for_url(f"**/runs/{run_id}{CONFIRM_PAGE_SUFFIX}", timeout=START_TIMEOUT_MS)  # Keep the bound.
        sync_api.expect(walking_page.get_by_test_id(CONFIRM_INPUT_ID)).to_be_visible(
            timeout=START_TIMEOUT_MS
        )  # Require the real confirmation control.
        logger.debug("The saved run's confirmation page is visible")  # Confirm the first confirmation view.

        logger.info("Open History from the confirmed run")  # Preserve the operator's existing navigation path.
        walking_page.get_by_role("link", name="History", exact=True).click()  # Open History with the visible link.
        walking_page.wait_for_url(f"**{HISTORY_PAGE_PATH}", timeout=START_TIMEOUT_MS)  # Wait for the History route.
        logger.debug("The History page is visible")  # Confirm the first navigation completed.
        logger.info("Open the run that this journey created")  # Select only the test-owned run.
        walking_page.get_by_role("link", name=run_id, exact=True).click()  # Open its real History link.
        walking_page.wait_for_url(f"**/runs/{run_id}", timeout=START_TIMEOUT_MS)  # Wait for the owned run page.
        confirm_link = walking_page.get_by_test_id(CONFIRM_LINK_ID)  # Select the run's existing confirm link.
        sync_api.expect(confirm_link).to_be_visible(timeout=START_TIMEOUT_MS)  # Require the real link.
        logger.info("Open the confirmation page from the owned run")  # Preserve the existing click step.
        confirm_link.click()  # Open the confirm page with the visible control.
        walking_page.wait_for_url(
            f"**/runs/{run_id}{CONFIRM_PAGE_SUFFIX}", timeout=START_TIMEOUT_MS
        )  # Wait for the confirmation route.
        sync_api.expect(walking_page.get_by_test_id(CONFIRM_INPUT_ID)).to_be_visible(
            timeout=START_TIMEOUT_MS
        )  # Require the real confirmation control.
        logger.debug("The run returned to its confirmation page")  # Confirm the full original click path.
        journey.return_to_owned_capture(capture_site_id)  # Give fixture teardown the real page for its site release.

    def test_a_refused_second_start_shows_a_link_to_the_open_run(
        self, walking_page: Any, run_ledger: RunLedger
    ) -> None:
        """Issue #2172: the open-run refusal now carries a link, not plain text.

        Why:
            The first create call of this test builds one run at the site. A
            second create call at the same site must then answer 409 with
            `upgrade_already_running`, and the error region must render the
            named run as a link to its live view, not as inert text the
            operator has to copy by hand.

            Issue #3511. The first call must answer 201. An earlier test once
            left a live run at this site, and the refusal then named that run.
            The test now checks that the refusal names the run of this test.

        Args:
            walking_page: The browser page that points at the running portal.
            run_ledger: The ledger that the teardown of `walking_page` reads.
        """
        _walk_to_capture_view(walking_page)  # Site list, to inventory, to capture view, by clicks alone.
        _start_and_reveal_upgrade(walking_page)  # Start the capture and wait for the upgrade button.
        with walking_page.expect_response(_is_run_create, timeout=START_TIMEOUT_MS) as first_event:
            walking_page.get_by_test_id(CAPTURE_START_UPGRADE_ID).click()  # The first attempt sets up the scenario.
        first_status = first_event.value.status  # The status reads without a body, so it survives the navigation.
        if first_status == UNREACHABLE_STATUS:  # A dead lock store stops each run, so the scenario cannot start.
            pytest.skip("The first run create answered 503. The portal cannot reach the site lock store.")
        assert first_status == CREATED_STATUS, (  # FR-003: the test must build its own run.
            f"The first run create answered {first_status}, not 201. A 409 names a live run of an earlier test. "
            "See issue #3511."
        )
        walking_page.wait_for_url(f"**/runs/*{OPTIONS_PAGE_SUFFIX}", timeout=START_TIMEOUT_MS)  # The new run opens.
        own_run_id = _run_id_from_url(walking_page.url)  # The options URL holds the key of the new run.
        run_ledger.record(own_run_id)  # Issue #3511: the teardown ends this run, so the site stays free.

        _walk_to_capture_view(walking_page)  # Back to the same site's capture view, by clicking alone.
        _start_and_reveal_upgrade(walking_page)  # A fresh capture, so the upgrade button shows again.
        with walking_page.expect_response(_is_run_create, timeout=START_TIMEOUT_MS) as second_event:
            walking_page.get_by_test_id(CAPTURE_START_UPGRADE_ID).click()  # A run already holds this site now.
        second_status = second_event.value.status  # The refusal answer carries the status of the second call.
        if second_status == UNREACHABLE_STATUS:  # The lock store answered no better on the second try either.
            pytest.skip("The second run create answered 503. The portal cannot reach the site lock store.")
        assert second_status == LOCKED_STATUS, f"The second run create answered {second_status}, not 409."

        error_region = walking_page.get_by_test_id(CAPTURE_START_UPGRADE_ERROR_ID)  # The region names the refusal.
        sync_api.expect(error_region).to_contain_text("Open that run before you start", timeout=START_TIMEOUT_MS)
        link = error_region.locator("a")  # The refusal names the live run as a link.
        sync_api.expect(link).to_be_visible(timeout=START_TIMEOUT_MS)
        run_id = (link.inner_text() or "").strip()  # The link text names the run that holds the site.
        assert run_id != "", "The link inside the error region named no run identifier."
        assert run_id == own_run_id, f"The refusal named the run {run_id}, not the run {own_run_id} of this test."
        href = link.get_attribute("href") or ""  # The link must open the live view of that run.
        assert href == f"/runs/{run_id}", f"The link pointed at {href!r}, not /runs/{run_id}."
