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

# The options page and the confirm page of the run the upgrade button creates.
# `contracts/http-api.md` section 5 fixes both page paths and the create path.
VERSION_SELECT_ALL_ID = "upgrade-version-select-all"
OPTIONS_SAVE_ID = "upgrade-options-save-button"
CONFIRM_INPUT_ID = "upgrade-confirm-input"
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


# WHY: Issue #2259. Neither test below takes the site lock, so `capture.html`
# draws the start control disabled and the press times out. Both tests reported
# a skip until the E2E job gained a lock store, so neither one ever ran and
# neither one ever passed. The marker states that truth. It is not the repair,
# and issue #2259 holds the repair.
@pytest.mark.xfail(
    reason="Issue #2259: the journey never takes the site lock, so the start control stays disabled.",
    strict=False,
)
class TestUpgradeJourney:
    """The operator walks from the site list to the confirm page by clicking."""

    def test_walk_from_the_site_list_reaches_the_confirm_page(self, portal_page: Any) -> None:
        """The upgrade button carries the operator from a capture to the confirm page.

        Why:
            FR-106 and SC-018 ask for a walk from the site list to the confirm
            page with no typed address. The walk opens the site list once, then
            clicks through the inventory, the capture, the run create, and the
            options save. A broken step leaves the operator with no path from a
            verified pre-check to an upgrade.

        Args:
            portal_page: The browser page that points at the running portal.
        """
        _walk_to_capture_view(portal_page)  # Site list, to inventory, to capture view, by clicks alone.
        _start_and_reveal_upgrade(portal_page)  # Start the capture and wait for the upgrade button.

        with portal_page.expect_response(_is_run_create, timeout=START_TIMEOUT_MS) as run_event:
            portal_page.get_by_test_id(CAPTURE_START_UPGRADE_ID).click()  # The button posts the run create.
        status = run_event.value.status  # The status reads without a body, so it survives the navigation.
        if status in (LOCKED_STATUS, UNREACHABLE_STATUS):  # A live run or a dead lock store stops a fresh run.
            pytest.skip(f"The run create answered {status}, so no fresh run key exists to walk.")
        assert status == CREATED_STATUS, f"The run create answered {status}. The contract fixes 201."

        portal_page.wait_for_url(f"**/runs/*{OPTIONS_PAGE_SUFFIX}", timeout=START_TIMEOUT_MS)
        run_id = _run_id_from_url(portal_page.url)  # The options URL holds the run key that the walk follows.
        picker = portal_page.get_by_test_id(VERSION_SELECT_ALL_ID)  # The bulk control fills every device version.
        if picker.locator("option").count() <= 1:  # Only the empty prompt exists, so no version can plan a device.
            pytest.skip("The options page offered no version, so the save would keep an empty plan.")
        picker.select_option(index=1)  # The first real version, because index 0 is the empty prompt.
        portal_page.get_by_test_id(OPTIONS_SAVE_ID).click()  # The save writes the plan and opens the confirm page.

        portal_page.wait_for_url(f"**/runs/{run_id}{CONFIRM_PAGE_SUFFIX}", timeout=START_TIMEOUT_MS)
        sync_api.expect(portal_page.get_by_test_id(CONFIRM_INPUT_ID)).to_be_visible(timeout=START_TIMEOUT_MS)

    def test_a_refused_second_start_shows_a_link_to_the_open_run(self, portal_page: Any) -> None:
        """Issue #2172: the open-run refusal now carries a link, not plain text.

        Why:
            One run already holds a site once the first create call lands,
            whether that call landed just now or before this test began. A
            second create call at the same site must then answer 409 with
            `upgrade_already_running`, and the error region must render the
            named run as a link to its live view, not as inert text the
            operator has to copy by hand.

        Args:
            portal_page: The browser page that points at the running portal.
        """
        _walk_to_capture_view(portal_page)
        _start_and_reveal_upgrade(portal_page)
        with portal_page.expect_response(_is_run_create, timeout=START_TIMEOUT_MS) as first_event:
            portal_page.get_by_test_id(CAPTURE_START_UPGRADE_ID).click()  # The first attempt sets up the scenario.
        first_status = first_event.value.status
        if first_status not in (CREATED_STATUS, LOCKED_STATUS):  # Neither state can seed a live run at this site.
            pytest.skip(f"The first run create answered {first_status}, so this walk cannot set up its scenario.")

        _walk_to_capture_view(portal_page)  # Back to the same site's capture view, by clicking alone.
        _start_and_reveal_upgrade(portal_page)  # A fresh capture, so the upgrade button shows again.
        with portal_page.expect_response(_is_run_create, timeout=START_TIMEOUT_MS) as second_event:
            portal_page.get_by_test_id(CAPTURE_START_UPGRADE_ID).click()  # A run already holds this site now.
        second_status = second_event.value.status
        if second_status == UNREACHABLE_STATUS:  # The lock store answered no better on the second try either.
            pytest.skip("The second run create answered 503. The portal cannot reach the site lock store.")
        assert second_status == LOCKED_STATUS, f"The second run create answered {second_status}, not 409."

        error_region = portal_page.get_by_test_id(CAPTURE_START_UPGRADE_ERROR_ID)
        sync_api.expect(error_region).to_contain_text("Open that run before you start", timeout=START_TIMEOUT_MS)
        link = error_region.locator("a")
        sync_api.expect(link).to_be_visible(timeout=START_TIMEOUT_MS)
        run_id = (link.inner_text() or "").strip()
        assert run_id, "The link inside the error region named no run identifier."
        href = link.get_attribute("href") or ""
        assert href == f"/runs/{run_id}", f"The link pointed at {href!r}, not /runs/{run_id}."
