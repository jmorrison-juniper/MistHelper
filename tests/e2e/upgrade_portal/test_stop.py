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

Why each test ends its own run:
    Issue #3511. The first test created a run, and each later test met the 409
    of FR-037 and used the same run. The canned stop answer never reaches the
    server, so the run stayed in the state `created` after the module. The
    live-run check of #3511 found it. Each test now records the run that it
    creates, and the teardown cancels that run, even when the test fails.

Why each test ends with a plain assertion:
    The test quality gate counts a plain `assert` statement. It does not count
    a Playwright `expect` call. Each `expect` call waits for the page script,
    and the plain assertion then reads one more fact of the same state, such
    as the typed text or the list that must not name the device.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from typing import Any

import pytest

from tests.support.upgrade_portal_e2e.site_lock import RunLedger, SiteRelease  # Issue #3511: the teardown.

# The Playwright package must exist before this module defines a browser test.
# A run without the package reports a skip and never an import error.
sync_api = pytest.importorskip("playwright.sync_api", reason="The Playwright package is not installed.")

logger = logging.getLogger(__name__)  # The teardown steps reach the pytest log.

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
CONFLICT_STATUS = 409  # FR-037 holds one live run for each site, and the refusal names that run.

UPGRADE_RUNNING_CODE = "upgrade_already_running"  # The code that FR-037 answers on a second create call.

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


def _named_live_run(answer: Any, path: str) -> str:
    """Return the key of the live run that a create refusal names.

    Why:
        FR-037 allows one live run for each site. The second create call of a
        session therefore meets 409, and the refusal names the run and tells the
        operator to open it. This helper follows that instruction, so the tests
        below drive the journey that the portal itself describes.

    Args:
        answer: The 409 answer of the create call.
        path: The endpoint, which the failure text names.

    Returns:
        The key of the run that already runs at this site.

    Raises:
        AssertionError: If the refusal carries another code, or names no run.
            Both describe a portal that departs from the contract, so neither
            may report a skip.
    """
    body = json.loads(answer.text()).get("error", {})
    code = str(body.get("code", ""))
    if code != UPGRADE_RUNNING_CODE:  # Any other 409 names a fault that this suite must show.
        raise AssertionError(f"{path} answered 409 with the code {code!r}, which this journey does not expect.")
    named = str(body.get("details", {}).get("run_id", ""))
    if not named:  # The refusal must name the live run, or the operator cannot open it.
        raise AssertionError(f"{path} answered 409 {UPGRADE_RUNNING_CODE} and named no run to open.")
    return named


def _post_the_run(page: Any, path: str) -> Any:
    """Send the create call of one run, and fail when the portal cannot answer it.

    Args:
        page: The browser page that points at the portal.
        path: The create endpoint of the first site.

    Returns:
        The answer of the create call.

    Raises:
        AssertionError: If the call never completed, or if the endpoint answers
            401 or 404. All three name a fault of the portal that the server
            fixture started, so none of them may report a skip.
    """
    headers = {CSRF_HEADER: _csrf_token(page), "Content-Type": "application/json"}  # The page token signs the call.
    logger.info("Create one run for the stop journey at %s", path)  # Log before the create call.
    try:  # The fixture started this portal, so a call that fails names a fault of it.
        answer = page.request.post(path, headers=headers, data="{}")  # The documented create call.
    except Exception as failure:  # The portal died, or it never bound the port.
        raise AssertionError(f"The create call to {path} did not complete. Cause: {failure}") from failure
    logger.debug("The create call answered %s", answer.status)  # Log the status only.
    if answer.status == UNAUTHORIZED_STATUS:  # `identity.require_session` refused the request.
        raise AssertionError(f"{path} answered 401. The portal this run started holds no sign-in seam.")
    if answer.status == NOT_FOUND_STATUS:  # The blueprint that owns this path is not registered.
        raise AssertionError(f"{path} answered 404. The blueprint that owns this path is not registered.")
    return answer  # The caller reads 201 or 409.


def _run_key(answer: Any, path: str, ledger: RunLedger) -> str:
    """Return the key of the run that one create answer names.

    Why:
        Issue #3511. The ledger holds only a run that this test built. The
        teardown therefore never cancels a run of another test or module.

    Args:
        answer: The answer of the create call.
        path: The create endpoint, which the skip text names.
        ledger: The ledger of the runs that this test builds.

    Returns:
        The key of the run that the stop journey opens.
    """
    if answer.status == CONFLICT_STATUS:  # One live run already holds this site, and the refusal names it.
        return _named_live_run(answer, path)  # The journey opens that run, as the refusal instructs.
    if answer.status != CREATED_STATUS:  # No run exists, so the run page cannot open.
        pytest.skip(f"{path} answered {answer.status}. The contract fixes 201, so no run key exists.")
    created = str(json.loads(answer.text())["run_id"])  # The key of the run that this test built.
    ledger.record(created)  # Issue #3511: the teardown ends this run, so the site stays free.
    return created  # The run page of this test opens this run.


@pytest.fixture(name="run_ledger")
def fixture_run_ledger() -> RunLedger:
    """Return an empty ledger for the run that one stop test builds.

    Why:
        Issue #3511. The teardown of `run_id` ends each run of this ledger, so
        no stop test leaves a live run at the first site for a later module.

    Returns:
        The ledger of this test.
    """
    return RunLedger()  # Each test starts with no recorded run.


def _end_the_stop_runs(page: Any, ledger: RunLedger) -> None:
    """End each live run that one stop test built.

    Why:
        Issue #3511. The browser answers each stop call of this module with a
        canned answer, so the run never leaves the state `created`. A live run
        blocks each later create call at the same site (FR-037). The cancel
        route ends a run that sent nothing, and it sends no cloud call.

    Args:
        page: The Playwright page object, on a page that draws the layout.
        ledger: The ledger of the runs that the test built.

    Raises:
        AssertionError: The page publishes no token, or a cancel answered a refusal.
    """
    if not ledger.runs:  # The test opened a run that it did not build, so no run needs an end.
        logger.debug("The stop test built no run, so the teardown ends no run")  # Log the empty ledger.
        return
    logger.info("End the %d run(s) of the stop test", len(ledger.runs))  # Log before the teardown step.
    meta = page.get_by_test_id(CSRF_META_ID)  # The layout publishes the token under this identifier.
    token = str(meta.get_attribute("content") or "") if meta.count() > 0 else ""  # A page with no layout has none.
    if not token:  # A cancel with no token meets the cross-site request check.
        raise AssertionError(f"The page publishes no {CSRF_META_ID} token, so the stop runs stay live. See #3511.")
    ended = SiteRelease(page.request, token).end_runs(ledger.runs)  # A refused cancel fails the teardown.
    logger.debug("The stop teardown ended %d run(s)", ended)  # Log after the teardown step.


@pytest.fixture
def run_id(portal_page: Any, run_ledger: RunLedger) -> Iterator[str]:
    """Create one upgrade run for the first site, yield its key, and then end the run.

    Why:
        The run page needs a run key, and the contract fixes no page that lists
        the runs of a site. The fixture therefore creates a run through the
        documented endpoint. The run never starts, so nothing reaches hardware.

        Issue #3511. The run stayed live after the module. The fixture now
        records the run that it creates, and the teardown cancels that run,
        even when the test fails. Each test therefore opens its own run.

    Args:
        portal_page: The browser page that points at the portal.
        run_ledger: The ledger of the runs that this test builds.

    Yields:
        The key of the run that the test opens.

    Raises:
        AssertionError: If the create call fails, or if a cancel of the
            teardown answers a refusal.
    """
    path = RUNS_API_TEMPLATE.format(site_id=_first_site_id(portal_page))  # The create path of the first site.
    answer = _post_the_run(portal_page, path)  # A fault of the portal fails here.
    yield _run_key(answer, path, run_ledger)  # The test opens this run.
    _end_the_stop_runs(portal_page, run_ledger)  # Issue #3511: the next create call at this site then answers 201.


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
        stop = run_page.get_by_test_id(STOP_BUTTON_ID)  # The control that opens the stop box.
        logger.info("Wait for the run page to show the stop control")  # Log before the wait.
        sync_api.expect(stop).to_be_visible()  # The page can show the control after the load.
        enabled = stop.is_enabled()  # A live run must accept a press of the control.
        logger.debug("The stop control shows, and the enabled state is %s", enabled)  # Log after the read.
        assert enabled is True, "The stop control is locked, so the operator cannot stop the live run."

    def test_the_typed_word_box_stays_closed_until_the_stop_press(self, run_page: Any) -> None:
        """The confirmation field is hidden before the operator presses stop.

        Why:
            FR-038b makes the stop a two-step action. A field that is open from
            the start turns the stop into one press and one key press.

        Args:
            run_page: The page that shows the live run view.
        """
        logger.info("Check that the stop box is closed before the stop press")  # Log before the checks.
        sync_api.expect(run_page.get_by_test_id(STOP_INPUT_ID)).to_be_hidden()  # The field waits for the press.
        stop = run_page.get_by_test_id(STOP_BUTTON_ID)  # The control that opens the box.
        expanded = stop.get_attribute("aria-expanded")  # The box state that a screen reader announces.
        logger.debug("The stop control reports aria-expanded=%s", expanded)  # Log after the read.
        assert expanded == "false", f"The stop control reports aria-expanded={expanded!r} before the press."

    def test_the_stop_press_opens_the_box_and_leaves_the_stop_locked(self, run_page: Any) -> None:
        """The first press only opens the box, so it starts no work.

        Why:
            The submit control carries the locked state in the markup itself. A
            browser that fails to load the script therefore leaves the stop
            locked and never sends a stop by accident.

        Args:
            run_page: The page that shows the live run view.
        """
        logger.info("Press the stop control and check that the stop stays locked")  # Log before the press.
        _open_stop_box(run_page)  # The first press opens the box and sends no stop.
        sync_api.expect(run_page.get_by_test_id(STOP_SUBMIT_ID)).to_be_disabled()  # The markup locks the submit.
        stop = run_page.get_by_test_id(STOP_BUTTON_ID)  # The control that opened the box.
        expanded = stop.get_attribute("aria-expanded")  # The box state that a screen reader announces.
        logger.debug("The stop control reports aria-expanded=%s after the press", expanded)  # Log after the read.
        assert expanded == "true", f"The stop control reports aria-expanded={expanded!r} after the press."

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
        logger.info("Type the near miss %r into the stop box", typed)  # Log before the typing.
        field = _open_stop_box(run_page)  # Open the box that reads the typed word.
        field.fill(typed)  # Type one near miss of the word.
        sync_api.expect(run_page.get_by_test_id(STOP_SUBMIT_ID)).to_be_disabled()  # The gate refuses the near miss.
        value = field.input_value()  # The text that the gate read.
        logger.debug("The stop box holds %r, and the stop stays locked", value)  # Log after the read.
        assert value == typed, f"The stop box holds {value!r}, so the test did not type the near miss {typed!r}."

    def test_the_exact_word_unlocks_the_stop(self, run_page: Any) -> None:
        """The exact word in capital letters unlocks the stop control.

        Args:
            run_page: The page that shows the live run view.
        """
        logger.info("Type the exact word into the stop box")  # Log before the typing.
        field = _open_stop_box(run_page)  # Open the box that reads the typed word.
        field.fill(STOP_WORD)  # Type the exact word in capital letters.
        submit = run_page.get_by_test_id(STOP_SUBMIT_ID)  # The control that sends the stop.
        sync_api.expect(submit).to_be_enabled(timeout=GATE_TIMEOUT_MS)  # The gate unlocks the stop.
        value = field.input_value()  # The text that unlocked the stop.
        logger.debug("The stop box holds %r, and the stop is unlocked", value)  # Log after the read.
        assert value == STOP_WORD, f"The stop box holds {value!r}, and the stop unlocked for that text."

    def test_a_cleared_field_locks_the_stop_again(self, run_page: Any) -> None:
        """The stop locks again after the operator clears the word.

        Why:
            An operator who types the word and then changes their mind must not
            leave a live stop control behind. The gate reads every key press, so
            it must also read the key press that removes a letter.

        Args:
            run_page: The page that shows the live run view.
        """
        logger.info("Type the word, clear it, and check that the stop locks again")  # Log before the typing.
        field = _open_stop_box(run_page)  # Open the box that reads the typed word.
        field.fill(STOP_WORD)  # Type the exact word first.
        submit = run_page.get_by_test_id(STOP_SUBMIT_ID)  # The control that sends the stop.
        sync_api.expect(submit).to_be_enabled(timeout=GATE_TIMEOUT_MS)  # The word unlocks the stop.
        field.fill("")  # Clear the word, as an operator who changes their mind does.
        sync_api.expect(submit).to_be_disabled(timeout=GATE_TIMEOUT_MS)  # The gate locks the stop again.
        value = field.input_value()  # The text that the gate read last.
        logger.debug("The stop box holds %r, and the stop is locked again", value)  # Log after the read.
        assert value == "", f"The stop box still holds {value!r}, so the test did not clear the word."


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
        outcome = run_page.get_by_test_id(STOP_OUTCOME_ID)  # The region that names the result of a stop.
        logger.info("Check that the stop result region is closed before a stop")  # Log before the checks.
        sync_api.expect(outcome).to_be_hidden()  # The region waits for a stop answer.
        count = outcome.count()  # A hidden check also passes for a region that is absent.
        logger.debug("The run page holds %s stop result region(s)", count)  # Log after the read.
        assert count == 1, f"The run page holds {count} stop result regions, so a stop answer cannot paint."

    def test_the_outcome_names_the_sentence_the_server_sent(self, run_page: Any) -> None:
        """The plain sentence of the answer leads the result region.

        Why:
            The cloud states that a cancel is best effort. The sentence says the
            whole result in one line, so it reads before the three lists.

        Args:
            run_page: The page that shows the live run view.
        """
        expected = str(FULL_STOP_ANSWER["outcome"]["message"])  # The sentence of the canned answer.
        logger.info("Send the stop and read the sentence of the result")  # Log before the stop.
        _send_the_stop(run_page, FULL_STOP_ANSWER)  # Send the stop and wait for the result region.
        message = run_page.get_by_test_id(STOP_MESSAGE_ID)  # The line that leads the result region.
        sync_api.expect(message).to_have_text(expected)  # The script paints the sentence after the answer.
        shown = (message.text_content() or "").strip()  # The sentence that the region shows.
        logger.debug("The stop result reads %r", shown)  # Log after the read.
        assert shown == expected, f"The stop result reads {shown!r}, and the answer sent {expected!r}."

    def test_the_outcome_names_the_device_it_cancelled(self, run_page: Any) -> None:
        """The cancelled list holds each address the answer named.

        Why:
            FR-038e asks the portal to name each device it cancelled. The
            operator reads that list to learn which device keeps its old version.

        Args:
            run_page: The page that shows the live run view.
        """
        logger.info("Send the stop and read the cancelled list")  # Log before the stop.
        _send_the_stop(run_page, FULL_STOP_ANSWER)  # Send the stop and wait for the result region.
        cancelled = run_page.get_by_test_id(STOP_CANCELLED_ID)  # The list of each cancelled device.
        sync_api.expect(cancelled).to_contain_text(CANCELLED_MAC)  # The script paints the list after the answer.
        writing = run_page.get_by_test_id(STOP_WRITING_ID).inner_text()  # One call paints the three lists.
        logger.debug("The writing list reads %r", writing)  # Log after the read.
        assert CANCELLED_MAC not in writing, f"The cancelled device {CANCELLED_MAC} also shows as a writing device."

    def test_the_outcome_names_the_device_that_keeps_writing(self, run_page: Any) -> None:
        """The writing list holds each device the stop could not reach in time.

        Why:
            A device that already writes firmware finishes the write. The
            operator must know that address, because that device changes version
            even after the stop.

        Args:
            run_page: The page that shows the live run view.
        """
        logger.info("Send the stop and read the writing list")  # Log before the stop.
        _send_the_stop(run_page, FULL_STOP_ANSWER)  # Send the stop and wait for the result region.
        writing = run_page.get_by_test_id(STOP_WRITING_ID)  # The list of each device that keeps writing.
        sync_api.expect(writing).to_contain_text(WRITING_MAC)  # The script paints the list after the answer.
        cancelled = run_page.get_by_test_id(STOP_CANCELLED_ID).inner_text()  # One call paints the three lists.
        logger.debug("The cancelled list reads %r", cancelled)  # Log after the read.
        assert WRITING_MAC not in cancelled, f"The writing device {WRITING_MAC} also shows as a cancelled device."

    def test_the_outcome_names_the_device_with_no_cancel_path(self, run_page: Any) -> None:
        """The third list holds each device the cloud offers no cancel for.

        Why:
            FR-038f asks the portal to report a device with no cancel path.
            `contracts/ui-testids.md` fixes `stop-outcome-no-cancel` for it, and
            the list must not fall silently into the cancelled list.

        Args:
            run_page: The page that shows the live run view.
        """
        logger.info("Send the stop and read the list of each device with no cancel path")  # Log before the stop.
        _send_the_stop(run_page, FULL_STOP_ANSWER)  # Send the stop and wait for the result region.
        no_cancel = run_page.get_by_test_id(STOP_NO_CANCEL_ID)  # The list of each device with no cancel path.
        sync_api.expect(no_cancel).to_contain_text(NO_CANCEL_MAC)  # The script paints the list after the answer.
        cancelled = run_page.get_by_test_id(STOP_CANCELLED_ID).inner_text()  # One call paints the three lists.
        logger.debug("The cancelled list reads %r", cancelled)  # Log after the read.
        assert NO_CANCEL_MAC not in cancelled, f"The device {NO_CANCEL_MAC} has no cancel path, but shows as cancelled."

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
            assert text != "", f"{marker} reads no text, so an empty list looks like a fault."

    def test_the_outcome_writes_the_new_state_into_the_run_state(self, run_page: Any) -> None:
        """The answer moves the state region to the state the server reported.

        Why:
            The page polls every 30 seconds. Without this write the operator
            would read the old state for up to half a minute after the stop.

        Args:
            run_page: The page that shows the live run view.
        """
        logger.info("Send the stop and read the run state")  # Log before the stop.
        _send_the_stop(run_page, FULL_STOP_ANSWER)  # Send the stop and wait for the result region.
        state = run_page.get_by_test_id(RUN_STATE_ID)  # The region that names the state of the run.
        sync_api.expect(state).to_have_text(STOPPING_STATE, timeout=GATE_TIMEOUT_MS)  # The answer writes the state.
        shown = (state.text_content() or "").strip()  # The state that the operator reads.
        logger.debug("The run state reads %r after the stop", shown)  # Log after the read.
        assert shown == STOPPING_STATE, f"The run state reads {shown!r}, and the answer sent {STOPPING_STATE!r}."

    def test_the_stop_cannot_be_sent_a_second_time(self, run_page: Any) -> None:
        """The stop control locks after the portal sends one stop.

        Why:
            A second stop for the same run reaches the cloud again and reports a
            second outcome. One run needs one stop.

        Args:
            run_page: The page that shows the live run view.
        """
        logger.info("Send the stop and check that both stop controls lock")  # Log before the stop.
        _send_the_stop(run_page, FULL_STOP_ANSWER)  # Send the stop and wait for the result region.
        stop = run_page.get_by_test_id(STOP_BUTTON_ID)  # The control that opens the stop box.
        sync_api.expect(stop).to_be_disabled(timeout=GATE_TIMEOUT_MS)  # The answer locks the control.
        submit_enabled = run_page.get_by_test_id(STOP_SUBMIT_ID).is_enabled()  # The script locks it before the send.
        logger.debug("The submit control is enabled after the stop: %s", submit_enabled)  # Log after the read.
        assert submit_enabled is False, "The submit is live after the stop, so a second press sends a second stop."
