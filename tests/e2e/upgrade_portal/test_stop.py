"""Browser tests for the stop journey of the upgrade capture portal.

Why:
    A contract test proves that the stop endpoint refuses every word but `STOP`.
    It cannot prove that the operator finds the control, opens the box, types the
    word, and then reads which device the portal cancelled. That path crosses one
    partial template and one script, so only a browser test proves it.

Why the stop answer is a canned answer:
    A real stop reaches live hardware. The tests below therefore answer the stop
    call inside the browser, so the outcome region paints from a known answer and
    no device receives a cancel. The gate tests send no call at all. This keeps
    the whole module safe against a portal that points at a production
    organization.

Where the stop control lives:
    `upgrade/stop.html` is a partial. `upgrade/progress.html` includes it, and
    `contracts/http-api.md` names `/runs/<run_id>` as the live run view. The
    tests therefore open the run page and never a separate stop page.

Why the helpers repeat `test_capture.py`:
    The shared `conftest.py` of this directory belongs to every browser module,
    and a helper for one journey does not belong in it.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

# The Playwright package must exist before this module defines a browser test.
# A run without the package reports a skip and never an import error.
sync_api = pytest.importorskip("playwright.sync_api", reason="The Playwright package is not installed.")

# `contracts/http-api.md` fixes this path for the site picker.
SITE_PAGE_PATH = "/select/site"
SITE_ROW_PREFIX = "site-row-"

RUNS_API_TEMPLATE = "/api/sites/{site_id}/runs"
PROGRESS_PAGE_TEMPLATE = "/runs/{run_id}"
STOP_ROUTE_GLOB = "**/api/runs/*/stop"  # The one call this module answers itself.

CSRF_META_ID = "csrf-meta"  # `layout.html` publishes the token under this identifier.
CSRF_HEADER = "X-CSRFToken"  # `portal.js` sends the token under this header name.

# The stop controls, all fixed by `contracts/ui-testids.md`.
STOP_BUTTON_ID = "stop-button"
STOP_INPUT_ID = "stop-confirm-input"
STOP_SUBMIT_ID = "stop-confirm-submit"
STOP_OUTCOME_ID = "stop-outcome"
STOP_MESSAGE_ID = "stop-outcome-message"
STOP_CANCELLED_ID = "stop-outcome-cancelled"
STOP_WRITING_ID = "stop-outcome-writing"
STOP_NO_CANCEL_ID = "stop-outcome-no-cancel"
RUN_STATE_ID = "upgrade-state"  # The answer writes the new state into this region.

STOP_WORD = "STOP"  # FR-038b fixes this exact text and this exact letter case.
# Each word below is one key press away from the real word. None may unlock the stop.
NEAR_MISS_WORDS = ("stop", "Stop", " STOP", "STOP ", "STOPP", "CONFIRM")

CANCELLED_MAC = "5c5b350e0001"
WRITING_MAC = "5c5b350e0002"
NO_CANCEL_MAC = "5c5b350e0003"
STOPPING_STATE = "stopping"

# The answer of a stop that cancelled one device, met one write, and missed one.
FULL_STOP_ANSWER = {
    "state": STOPPING_STATE,
    "outcome": {
        "cancelled": [CANCELLED_MAC],
        "already_writing": [WRITING_MAC],
        "no_cancel_available": [NO_CANCEL_MAC],
        "message": "The portal cancelled one device.",
    },
}

# The answer of a stop that reached no device at all.
EMPTY_STOP_ANSWER = {
    "state": STOPPING_STATE,
    "outcome": {
        "cancelled": [],
        "already_writing": [],
        "no_cancel_available": [],
        "message": "The portal recorded the stop request.",
    },
}

OK_STATUS = 200  # The contract fixes this status for the run page and for the stop.
CREATED_STATUS = 201  # `POST /api/sites/<site_id>/runs` answers 201.
UNAUTHORIZED_STATUS = 401  # `runtime/identity.py` answers this code with no session.
NOT_FOUND_STATUS = 404  # The route is not registered yet.

GATE_TIMEOUT_MS = 5000  # The script reads one key press, so the gate settles quickly.

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
        prefix: The identifier prefix, such as `site-row-`.

    Returns:
        The tail of each matching identifier, in page order.
    """
    found = page.locator(f'[data-testid^="{prefix}"]')  # A prefix match still selects by `data-testid`.
    markers = found.evaluate_all("nodes => nodes.map(node => node.getAttribute('data-testid'))")
    return [str(marker)[len(prefix) :] for marker in markers if marker]


def _first_site_id(page: Any) -> str:
    """Open the site picker and return the identifier of the first site row.

    Args:
        page: The Playwright page object.

    Returns:
        The site identifier of the first row.
    """
    _require_built_route(_page_status(page, SITE_PAGE_PATH), SITE_PAGE_PATH)
    keys = _marker_keys(page, SITE_ROW_PREFIX)
    if not keys:  # The portal reached no site, so no run can open.
        pytest.skip("The site picker shows no site row, so no site identifier exists to stop.")
    return keys[0]


def _csrf_token(page: Any) -> str:
    """Read the token that `layout.html` publishes in the head of every page.

    Args:
        page: The Playwright page object, on any portal page.

    Returns:
        The token text, which is empty when the portal published none.
    """
    return str(page.get_by_test_id(CSRF_META_ID).get_attribute("content") or "")


@pytest.fixture
def run_id(portal_page: Any) -> str:
    """Create one upgrade run for the first site and return its key.

    Why:
        The run page needs a run key, and the contract fixes no page that lists
        the runs of a site. The fixture therefore creates a run through the
        documented endpoint. The run never starts, so nothing reaches hardware.

    Args:
        portal_page: The browser page that points at the portal.

    Returns:
        The key of the fresh run.

    Raises:
        AssertionError: If the call never completed, or if the endpoint answers
            401 or 404. All three name a fault of the portal that the server
            fixture started, so none of them may report a skip.
    """
    site_id = _first_site_id(portal_page)
    path = RUNS_API_TEMPLATE.format(site_id=site_id)
    headers = {CSRF_HEADER: _csrf_token(portal_page), "Content-Type": "application/json"}
    try:  # The fixture started this portal, so a call that fails names a fault of it.
        answer = portal_page.request.post(path, headers=headers, data="{}")
    except Exception as failure:  # The portal died, or it never bound the port.
        raise AssertionError(f"The create call to {path} did not complete. Cause: {failure}") from failure
    if answer.status == UNAUTHORIZED_STATUS:  # `identity.require_session` refused the request.
        raise AssertionError(f"{path} answered 401. The portal this run started holds no sign-in seam.")
    if answer.status == NOT_FOUND_STATUS:  # The blueprint that owns this path is not registered.
        raise AssertionError(f"{path} answered 404. The blueprint that owns this path is not registered.")
    if answer.status != CREATED_STATUS:  # No run exists, so the run page cannot open.
        pytest.skip(f"{path} answered {answer.status}. The contract fixes 201, so no run key exists.")
    return str(json.loads(answer.text())["run_id"])


@pytest.fixture
def run_page(portal_page: Any, run_id: str) -> Any:
    """Return a run page that carries a stop control the operator can press.

    Why:
        A run that already finished renders the stop control locked, and no test
        below can then open the box. The fixture skips that state, because a
        locked control is correct behavior and not a failure.

    Args:
        portal_page: The browser page that points at the portal.
        run_id: The key of the fresh run.

    Returns:
        The Playwright page object, on the run page.
    """
    path = PROGRESS_PAGE_TEMPLATE.format(run_id=run_id)
    _require_built_route(_page_status(portal_page, path), path)
    if portal_page.get_by_test_id(STOP_BUTTON_ID).is_disabled():  # The run already reached a final state.
        pytest.skip("The stop control is locked, because the run under test already finished.")
    return portal_page


def _open_stop_box(page: Any) -> Any:
    """Press the stop control and return the field that reads the typed word.

    Args:
        page: The Playwright page object, on the run page.

    Returns:
        The locator of the confirmation field.
    """
    page.get_by_test_id(STOP_BUTTON_ID).click()
    field = page.get_by_test_id(STOP_INPUT_ID)
    sync_api.expect(field).to_be_visible(timeout=GATE_TIMEOUT_MS)
    return field


def _answer_the_stop(page: Any, answer: dict[str, Any]) -> None:
    """Answer the next stop call inside the browser, so no device is cancelled.

    Why:
        The portal under test can point at a production organization. A canned
        answer proves that the outcome region paints, and it reaches no cloud.

    Args:
        page: The Playwright page object.
        answer: The body the browser reads instead of the server answer.
    """

    def handle(route: Any) -> None:
        """Fulfill one stop call with the canned answer.

        Args:
            route: The intercepted route.
        """
        route.fulfill(status=OK_STATUS, content_type="application/json", body=json.dumps(answer))

    page.route(STOP_ROUTE_GLOB, handle)


def _send_the_stop(page: Any, answer: dict[str, Any]) -> None:
    """Drive the whole stop journey and wait for the outcome region to open.

    Args:
        page: The Playwright page object, on the run page.
        answer: The body the browser reads instead of the server answer.
    """
    _answer_the_stop(page, answer)
    _open_stop_box(page).fill(STOP_WORD)
    submit = page.get_by_test_id(STOP_SUBMIT_ID)
    sync_api.expect(submit).to_be_enabled(timeout=GATE_TIMEOUT_MS)
    submit.click()
    sync_api.expect(page.get_by_test_id(STOP_OUTCOME_ID)).to_be_visible(timeout=GATE_TIMEOUT_MS)


class TestStopGate:
    """The stop stays locked until the operator types the word `STOP`."""

    def test_the_run_page_shows_the_stop_control(self, run_page: Any) -> None:
        """The run page carries the stop control beside the phase list.

        Why:
            FR-038a asks for a stop while the run is live. An operator who must
            leave the page to stop a run loses the view of what is still running.

        Args:
            run_page: The page that shows the live run view.
        """
        sync_api.expect(run_page.get_by_test_id(STOP_BUTTON_ID)).to_be_visible()

    def test_the_typed_word_box_stays_closed_until_the_stop_press(self, run_page: Any) -> None:
        """The confirmation field is hidden before the operator presses stop.

        Why:
            FR-038b makes the stop a two-step action. A field that is open from
            the start turns the stop into one press and one key press.

        Args:
            run_page: The page that shows the live run view.
        """
        sync_api.expect(run_page.get_by_test_id(STOP_INPUT_ID)).to_be_hidden()

    def test_the_stop_press_opens_the_box_and_leaves_the_stop_locked(self, run_page: Any) -> None:
        """The first press only opens the box, so it starts no work.

        Why:
            The submit control carries the locked state in the markup itself. A
            browser that fails to load the script therefore leaves the stop
            locked and never sends a stop by accident.

        Args:
            run_page: The page that shows the live run view.
        """
        _open_stop_box(run_page)
        sync_api.expect(run_page.get_by_test_id(STOP_SUBMIT_ID)).to_be_disabled()

    @pytest.mark.parametrize("typed", NEAR_MISS_WORDS)
    def test_a_near_miss_of_the_word_keeps_the_stop_locked(self, run_page: Any, typed: str) -> None:
        """Text that is one key press from the word does not unlock the stop.

        Why:
            The field shows the typed text in capital letters, so an operator who
            types lower case sees capital letters. The gate must still refuse it.

        Args:
            run_page: The page that shows the live run view.
            typed: The near miss the test types into the field.
        """
        _open_stop_box(run_page).fill(typed)
        sync_api.expect(run_page.get_by_test_id(STOP_SUBMIT_ID)).to_be_disabled()

    def test_the_exact_word_unlocks_the_stop(self, run_page: Any) -> None:
        """The exact word in capital letters unlocks the stop control.

        Args:
            run_page: The page that shows the live run view.
        """
        _open_stop_box(run_page).fill(STOP_WORD)
        sync_api.expect(run_page.get_by_test_id(STOP_SUBMIT_ID)).to_be_enabled(timeout=GATE_TIMEOUT_MS)

    def test_a_cleared_field_locks_the_stop_again(self, run_page: Any) -> None:
        """The stop locks again after the operator clears the word.

        Why:
            An operator who types the word and then changes their mind must not
            leave a live stop control behind. The gate reads every key press, so
            it must also read the key press that removes a letter.

        Args:
            run_page: The page that shows the live run view.
        """
        field = _open_stop_box(run_page)
        field.fill(STOP_WORD)
        submit = run_page.get_by_test_id(STOP_SUBMIT_ID)
        sync_api.expect(submit).to_be_enabled(timeout=GATE_TIMEOUT_MS)
        field.fill("")
        sync_api.expect(submit).to_be_disabled(timeout=GATE_TIMEOUT_MS)


class TestStopOutcome:
    """The outcome region names every device the stop reached."""

    def test_the_outcome_region_stays_closed_before_a_stop(self, run_page: Any) -> None:
        """The run page shows no stop result until a stop returns an answer.

        Why:
            An open and empty result region reads as a stop that already ran and
            cancelled nothing. That is the opposite of the true state.

        Args:
            run_page: The page that shows the live run view.
        """
        sync_api.expect(run_page.get_by_test_id(STOP_OUTCOME_ID)).to_be_hidden()

    def test_the_outcome_names_the_sentence_the_server_sent(self, run_page: Any) -> None:
        """The plain sentence of the answer leads the result region.

        Why:
            The cloud states that a cancel is best effort. The sentence says the
            whole result in one line, so it reads before the three lists.

        Args:
            run_page: The page that shows the live run view.
        """
        _send_the_stop(run_page, FULL_STOP_ANSWER)
        message = run_page.get_by_test_id(STOP_MESSAGE_ID)
        sync_api.expect(message).to_have_text(str(FULL_STOP_ANSWER["outcome"]["message"]))

    def test_the_outcome_names_the_device_it_cancelled(self, run_page: Any) -> None:
        """The cancelled list holds each address the answer named.

        Why:
            FR-038e asks the portal to name each device it cancelled. The
            operator reads that list to learn which device keeps its old version.

        Args:
            run_page: The page that shows the live run view.
        """
        _send_the_stop(run_page, FULL_STOP_ANSWER)
        sync_api.expect(run_page.get_by_test_id(STOP_CANCELLED_ID)).to_contain_text(CANCELLED_MAC)

    def test_the_outcome_names_the_device_that_keeps_writing(self, run_page: Any) -> None:
        """The writing list holds each device the stop could not reach in time.

        Why:
            A device that already writes firmware finishes the write. The
            operator must know that address, because that device changes version
            even after the stop.

        Args:
            run_page: The page that shows the live run view.
        """
        _send_the_stop(run_page, FULL_STOP_ANSWER)
        sync_api.expect(run_page.get_by_test_id(STOP_WRITING_ID)).to_contain_text(WRITING_MAC)

    def test_the_outcome_names_the_device_with_no_cancel_path(self, run_page: Any) -> None:
        """The third list holds each device the cloud offers no cancel for.

        Why:
            FR-038f asks the portal to report a device with no cancel path.
            `contracts/ui-testids.md` fixes `stop-outcome-no-cancel` for it, and
            the list must not fall silently into the cancelled list.

        Args:
            run_page: The page that shows the live run view.
        """
        _send_the_stop(run_page, FULL_STOP_ANSWER)
        sync_api.expect(run_page.get_by_test_id(STOP_NO_CANCEL_ID)).to_contain_text(NO_CANCEL_MAC)

    def test_an_empty_list_reads_as_a_sentence_and_never_as_a_blank(self, run_page: Any) -> None:
        """Each empty list carries a sentence, so a blank never reads as a fault.

        Why:
            An empty list with no text looks like a page that failed to load. A
            sentence states that the list is empty on purpose.

        Args:
            run_page: The page that shows the live run view.
        """
        _send_the_stop(run_page, EMPTY_STOP_ANSWER)
        for marker in (STOP_CANCELLED_ID, STOP_WRITING_ID, STOP_NO_CANCEL_ID):
            text = (run_page.get_by_test_id(marker).inner_text() or "").strip()
            assert text, f"{marker} reads no text, so an empty list looks like a fault."

    def test_the_outcome_writes_the_new_state_into_the_run_state(self, run_page: Any) -> None:
        """The answer moves the state region to the state the server reported.

        Why:
            The page polls every 30 seconds. Without this write the operator
            would read the old state for up to half a minute after the stop.

        Args:
            run_page: The page that shows the live run view.
        """
        _send_the_stop(run_page, FULL_STOP_ANSWER)
        sync_api.expect(run_page.get_by_test_id(RUN_STATE_ID)).to_have_text(STOPPING_STATE, timeout=GATE_TIMEOUT_MS)

    def test_the_stop_cannot_be_sent_a_second_time(self, run_page: Any) -> None:
        """The stop control locks after the portal sends one stop.

        Why:
            A second stop for the same run reaches the cloud again and reports a
            second outcome. One run needs one stop.

        Args:
            run_page: The page that shows the live run view.
        """
        _send_the_stop(run_page, FULL_STOP_ANSWER)
        sync_api.expect(run_page.get_by_test_id(STOP_BUTTON_ID)).to_be_disabled(timeout=GATE_TIMEOUT_MS)
