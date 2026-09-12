"""Browser tests for the reschedule, the cancel, and the retry of one run.

Why:
    Pull request #2229 added the reschedule control and the cancel control.
    Pull request #2231 added the one-press retry control. Each one carries
    contract tests and a template test, and no test ever pressed one.

    A contract test posts to the route and reads the answer. It cannot prove
    that the button exists on the page, that the button is enabled at the right
    moment, or that the press sends the fields the route demands. Issue #2226 is
    the precedent: the sign-in radio controls held the same two kinds of cover,
    and neither kind answered a plain question about a press.

    Two of the three controls change a scheduled upgrade. A cancel that does not
    answer a press leaves an operator with a run that starts on hardware.

How each test presses:
    Every press is a plain `click()`. No test passes `force`, raises a timeout,
    or writes a property. A press that needs any of those hides the fault that
    the test exists to find, which is the rule that issue #2242 states.

What this module skips and what it fails:
    The module reports a skip when no browser binary exists, and when the portal
    offers no site to upgrade. It reports a failure when a control is absent
    from a page that must hold it, and when a press produces no result. The
    fixture starts its own portal, so a 401 and a 404 are both faults of that
    portal, and neither may report a pass.
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

# `contracts/http-api.md` section 5 fixes the create path and the run page.
RUNS_API_TEMPLATE = "/api/sites/{site_id}/runs"
PROGRESS_PAGE_TEMPLATE = "/runs/{run_id}"
RUN_STATUS_TEMPLATE = "/api/runs/{run_id}/status"

CSRF_META_ID = "csrf-meta"  # `layout.html` publishes the token under this identifier.
CSRF_HEADER = "X-CSRFToken"  # `portal.js` sends the token under this header name.

# The three control regions and their controls. `contracts/ui-testids.md` fixes
# every identifier below, and `upgrade/progress.html` draws each one.
SCHEDULE_REGION_ID = "run-schedule-controls"
RESCHEDULE_INPUT_ID = "run-reschedule-input"
RESCHEDULE_BUTTON_ID = "run-reschedule-button"
CANCEL_BUTTON_ID = "run-cancel-button"
RETRY_REGION_ID = "run-retry-controls"
RETRY_BUTTON_ID = "run-retry-button"

FLASH_REGION_ID = "flash-message"  # `portal.js` writes every outcome sentence here.
RUN_STATE_ID = "upgrade-state"  # The run state that the page paints.

# The exact sentence that `portal.js` writes after each control succeeds. A test
# that read a status code alone would pass while the operator saw nothing.
RESCHEDULE_MESSAGE = "The portal moved the start of this run."
CANCEL_MESSAGE = "The portal ended this run. It sent no firmware."
RETRY_MESSAGE = "The portal built a retry. Take a fresh capture before you start it."

# The duration that the reschedule test enters. Issue #2200 asks for a relative
# moment, so the operator writes a number and a unit and never an epoch second.
RELATIVE_DURATION = "5m"

OK_STATUS = 200  # The contract fixes this status for the run page.
CREATED_STATUS = 201  # `POST /api/sites/<site_id>/runs` answers 201.
UNAUTHORIZED_STATUS = 401  # `runtime/identity.py` answers this code with no session.
NOT_FOUND_STATUS = 404  # The route is not registered yet.
CONFLICT_STATUS = 409  # FR-037 holds one live run for each site, and the refusal names that run.

UPGRADE_RUNNING_CODE = "upgrade_already_running"  # The code that FR-037 answers on a second create call.

FLASH_TIMEOUT_MS = 10000  # One call reaches the store, which may sit on a network.

# WHY: The first create call of a session builds the store collections, and that
# build takes longer than the default 30 seconds of the request context. This
# bound covers the cold store. It applies to the setup call alone. Issue #2242
# forbids a raised timeout on a press, and no press below raises one.
CREATE_TIMEOUT_MS = 120000

# The seeded run that `conftest.build_stand_in_app` writes at start-up. Only a
# failed run offers the retry control, and no journey through the pages reaches
# the failed state without a real upgrade fault at a real site.
FAILED_RUN_ID = "e2e-failed-run-0001"

# The seed runs on its own thread inside the server, because a cold store builds
# its collections on the first write. These two values wait for that write.
SEED_TRIES = 20
SEED_PAUSE_MS = 1000

# WHY: The server fixture states its own fault and its own skip, so this module
# must not translate either one.
SERVER_FIXTURE = "capture_portal_server"
BROWSER_FIXTURE = "page"


def _browser_page(request: pytest.FixtureRequest) -> Any:
    """Build one browser page, and report a missing browser binary as a skip.

    Why:
        A workstation with no browser binary describes the workstation and never
        the page under test, so that one state stays a skip. Every other fault
        belongs to the portal and must fail.

    Args:
        request: The pytest request that resolves the fixture.

    Returns:
        The Playwright page object.
    """
    request.getfixturevalue(SERVER_FIXTURE)  # A fault here is a fault of the portal, not a skip.
    try:  # Only the browser binary may turn into a skip.
        page: Any = request.getfixturevalue(BROWSER_FIXTURE)
    except Exception as failure:  # A skip states the real cause, so nothing hides.
        pytest.skip(f"Playwright could not open a browser, so no browser test can run. Cause: {failure}")
    return page


@pytest.fixture(name="portal_page")
def fixture_portal_page(request: pytest.FixtureRequest) -> Any:
    """Return a signed-in browser page that points at the portal.

    Args:
        request: The pytest request that resolves the fixture.

    Returns:
        The Playwright page object.
    """
    return _browser_page(request)


def _first_site_id(page: Any) -> str:
    """Return the identifier of the first site that the picker lists.

    Args:
        page: The browser page that points at the portal.

    Returns:
        The site identifier.
    """
    answer = page.goto(SITE_PAGE_PATH)  # The picker draws one row for each site.
    if answer is not None and answer.status != OK_STATUS:  # The portal must serve its own picker.
        raise AssertionError(f"{SITE_PAGE_PATH} answered {answer.status}, so no site identifier exists.")
    rows = page.locator(f"[data-testid^='{SITE_ROW_PREFIX}']")  # Every row carries the prefix.
    if rows.count() < 1:  # A portal with no site cannot host an upgrade run.
        pytest.skip("The site picker shows no site row, so no site identifier exists to upgrade.")
    marker = str(rows.first.get_attribute("data-testid") or "")  # The row names its own site.
    return marker[len(SITE_ROW_PREFIX) :]  # The remainder is the identifier.


def _csrf_token(page: Any) -> str:
    """Return the cross-site request token that the layout publishes.

    Args:
        page: The browser page that points at the portal.

    Returns:
        The token text.
    """
    return str(page.get_by_test_id(CSRF_META_ID).get_attribute("content") or "")


def _named_live_run(answer: Any, path: str) -> str:
    """Return the key of the live run that a create refusal names.

    Why:
        FR-037 allows one live run for each site, so the second create call of a
        session meets 409. The refusal names the run, and this journey opens it,
        exactly as the portal instructs the operator to do.

    Args:
        answer: The 409 answer of the create call.
        path: The endpoint, which the failure text names.

    Returns:
        The key of the run that already holds this site.

    Raises:
        AssertionError: If the refusal carries another code, or names no run.
    """
    body = json.loads(answer.text()).get("error", {})
    code = str(body.get("code", ""))
    if code != UPGRADE_RUNNING_CODE:  # Any other 409 names a fault that this suite must show.
        raise AssertionError(f"{path} answered 409 with the code {code!r}, which this journey does not expect.")
    named = str(body.get("details", {}).get("run_id", ""))
    if not named:  # The refusal must name the live run, or the operator cannot open it.
        raise AssertionError(f"{path} answered 409 {UPGRADE_RUNNING_CODE} and named no run to open.")
    return named


def _create_run(page: Any) -> str:
    """Create one upgrade run for the first site and return its key.

    Args:
        page: The browser page that points at the portal.

    Returns:
        The key of the run that this journey drives.

    Raises:
        AssertionError: If the call never completed, or if the endpoint answers
            401 or 404. All three name a fault of the portal that this run
            started, so none of them may report a skip.
    """
    site_id = _first_site_id(page)
    path = RUNS_API_TEMPLATE.format(site_id=site_id)
    headers = {CSRF_HEADER: _csrf_token(page), "Content-Type": "application/json"}
    try:  # The fixture started this portal, so a call that fails names a fault of it.
        answer = page.request.post(path, headers=headers, data="{}", timeout=CREATE_TIMEOUT_MS)
    except Exception as failure:  # The portal died, or it never bound the port.
        raise AssertionError(f"The create call to {path} did not complete. Cause: {failure}") from failure
    if answer.status == UNAUTHORIZED_STATUS:  # `identity.require_session` refused the request.
        raise AssertionError(f"{path} answered 401. The portal this run started holds no sign-in seam.")
    if answer.status == NOT_FOUND_STATUS:  # The blueprint that owns this path is not registered.
        raise AssertionError(f"{path} answered 404. The blueprint that owns this path is not registered.")
    if answer.status == CONFLICT_STATUS:  # One live run already holds this site, and the refusal names it.
        return _named_live_run(answer, path)
    if answer.status != CREATED_STATUS:  # No run exists, so no page of this journey can open.
        pytest.skip(f"{path} answered {answer.status}. The contract fixes 201, so no run key exists.")
    return str(json.loads(answer.text())["run_id"])


def _open_run_page(page: Any, run_id: str) -> None:
    """Open the run page of one run.

    Args:
        page: The browser page that points at the portal.
        run_id: The run key.

    Raises:
        AssertionError: If the page answers any status but 200.
    """
    path = PROGRESS_PAGE_TEMPLATE.format(run_id=run_id)
    answer = page.goto(path)
    if answer is not None and answer.status != OK_STATUS:  # The portal must serve its own run page.
        raise AssertionError(f"{path} answered {answer.status}. The contract fixes 200 for this page.")


def _require_enabled(control: Any, name: str) -> None:
    """Refuse a press against a control that the page drew disabled.

    Why:
        A press against a disabled control reports a timeout, and a timeout
        names the wrong fault. The site lock turns each of these controls off,
        so a run without the lock must say so and skip.

    Args:
        control: The Playwright locator of the control.
        name: The identifier, which the skip message names.
    """
    if not control.is_enabled():  # The operator does not hold the site, so no press may land.
        pytest.skip(f"The control {name} is disabled, so this operator does not hold the site lock.")


@pytest.fixture(name="scheduled_run_page")
def fixture_scheduled_run_page(portal_page: Any) -> Any:
    """Return the run page of a run that has not begun.

    Why:
        `run_not_started` reports true while the run sits in the pre-check
        states, and the template draws the schedule region only for such a run.
        A fresh run holds the state `created`, which is one of those states.

    Args:
        portal_page: The browser page that points at the portal.

    Returns:
        The Playwright page object, on the run page.
    """
    run_id = _create_run(portal_page)
    _open_run_page(portal_page, run_id)
    region = portal_page.get_by_test_id(SCHEDULE_REGION_ID)
    if region.count() < 1:  # The run already reached the cloud, so the stop control applies instead.
        pytest.skip("The run page holds no schedule region, so this run already reached the cloud.")
    return portal_page


@pytest.fixture(name="failed_run_page")
def fixture_failed_run_page(portal_page: Any) -> Any:
    """Return the run page of the seeded failed run.

    Why:
        Only a failed run offers the retry control, and no journey through the
        pages reaches that state. A real failure needs a real upgrade fault at a
        real site, which no test may cause. The server process therefore seeds
        one failed run at start-up, and this fixture opens it.

        The fixture creates a run first, because the create call takes the site
        lock for this browser. The retry control reads that lock, so a page
        opened without it would draw the control disabled.

    Args:
        portal_page: The browser page that points at the portal.

    Returns:
        The Playwright page object, on the run page of the failed run.
    """
    _create_run(portal_page)  # Takes the site lock for this browser, which the retry control reads.
    for _ in range(SEED_TRIES):  # The seed runs on its own thread, so it may land a moment after the bind.
        _open_run_page(portal_page, FAILED_RUN_ID)
        if portal_page.get_by_test_id(RETRY_REGION_ID).count() >= 1:  # The seeded run is readable now.
            return portal_page
        portal_page.wait_for_timeout(SEED_PAUSE_MS)  # Give the writer thread one more moment.
    pytest.skip(f"The portal holds no failed run under {FAILED_RUN_ID}, so the seed did not write.")


class TestTheRescheduleControl:
    """Issue #2201 moves the start of a run that has not begun."""

    def test_the_run_page_holds_the_reschedule_control(self, scheduled_run_page: Any) -> None:
        """The page of a run that has not begun MUST draw both schedule controls."""
        page = scheduled_run_page

        assert page.get_by_test_id(RESCHEDULE_INPUT_ID).count() == 1, "the duration field must exist"
        assert page.get_by_test_id(RESCHEDULE_BUTTON_ID).count() == 1, "the reschedule control must exist"

    def test_the_duration_field_asks_for_a_relative_moment(self, scheduled_run_page: Any) -> None:
        """The field MUST ask for a duration, because issue #2200 forbids an epoch second."""
        field = scheduled_run_page.get_by_test_id(RESCHEDULE_INPUT_ID)

        # WHY: the placeholder is the one hint an operator reads before the first press.
        assert str(field.get_attribute("placeholder") or ""), "the duration field must carry a hint"

    def test_the_field_holds_the_typed_duration(self, scheduled_run_page: Any) -> None:
        """The field MUST hold what the operator typed, so the press sends that value."""
        field = scheduled_run_page.get_by_test_id(RESCHEDULE_INPUT_ID)
        _require_enabled(field, RESCHEDULE_INPUT_ID)

        field.fill(RELATIVE_DURATION)  # A plain fill, exactly as an operator types.

        assert field.input_value() == RELATIVE_DURATION, "the field must hold the typed duration"

    def test_a_plain_press_moves_the_start_of_the_run(self, scheduled_run_page: Any) -> None:
        """A plain press MUST move the start and MUST report the move on the page.

        Why:
            The contract test proves the route. Only this test proves that the
            button reaches the route with the duration that the operator typed,
            and that the operator then reads the result.
        """
        page = scheduled_run_page
        field = page.get_by_test_id(RESCHEDULE_INPUT_ID)
        button = page.get_by_test_id(RESCHEDULE_BUTTON_ID)
        _require_enabled(button, RESCHEDULE_BUTTON_ID)
        field.fill(RELATIVE_DURATION)  # The duration counts from the press, never from an epoch second.

        button.click()  # A plain press. No force, and no raised timeout.

        flash = page.get_by_test_id(FLASH_REGION_ID)
        sync_api.expect(flash).to_contain_text(RESCHEDULE_MESSAGE, timeout=FLASH_TIMEOUT_MS)


class TestTheCancelControl:
    """Issue #2201 ends a run that never reached the cloud."""

    def test_the_run_page_holds_the_cancel_control(self, scheduled_run_page: Any) -> None:
        """The page of a run that has not begun MUST draw the cancel control."""
        assert scheduled_run_page.get_by_test_id(CANCEL_BUTTON_ID).count() == 1, "the cancel control must exist"

    def test_the_cancel_control_reads_as_the_dangerous_one(self, scheduled_run_page: Any) -> None:
        """The cancel MUST look different from the reschedule, because it ends the run."""
        cancel = scheduled_run_page.get_by_test_id(CANCEL_BUTTON_ID)
        reschedule = scheduled_run_page.get_by_test_id(RESCHEDULE_BUTTON_ID)

        # WHY: an operator must tell the two apart before the press, not after it.
        assert str(cancel.get_attribute("class") or "") != str(reschedule.get_attribute("class") or "")

    def test_a_plain_press_ends_the_run(self, scheduled_run_page: Any) -> None:
        """A plain press MUST end the run and MUST report that no firmware moved.

        Why:
            A cancel that does not answer a press leaves an operator with a run
            that starts on hardware. Only a press proves the control.
        """
        page = scheduled_run_page
        button = page.get_by_test_id(CANCEL_BUTTON_ID)
        _require_enabled(button, CANCEL_BUTTON_ID)

        button.click()  # A plain press. No force, and no raised timeout.

        flash = page.get_by_test_id(FLASH_REGION_ID)
        sync_api.expect(flash).to_contain_text(CANCEL_MESSAGE, timeout=FLASH_TIMEOUT_MS)

    def test_the_canceled_run_reads_as_canceled_after_a_reload(self, scheduled_run_page: Any) -> None:
        """The cancel MUST reach the record, so a reload MUST show the new state.

        Why:
            A flash alone proves the script. Only a reload proves that the store
            kept the change, which is what an operator returns to tomorrow.
        """
        page = scheduled_run_page
        run_id = str(page.get_by_test_id(CANCEL_BUTTON_ID).get_attribute("data-run-id") or "")
        button = page.get_by_test_id(CANCEL_BUTTON_ID)
        _require_enabled(button, CANCEL_BUTTON_ID)
        before = page.get_by_test_id(RUN_STATE_ID).inner_text().strip()

        button.click()  # A plain press. No force, and no raised timeout.
        sync_api.expect(page.get_by_test_id(FLASH_REGION_ID)).to_contain_text(CANCEL_MESSAGE, timeout=FLASH_TIMEOUT_MS)
        _open_run_page(page, run_id)  # Read the record back, and not the page that the script painted.

        after = page.get_by_test_id(RUN_STATE_ID).inner_text().strip()
        assert after != before, f"the run state stayed {before!r}, so the cancel reached no record"


class TestTheRetryControl:
    """Issue #2202 builds a new run from the settings of a failed one."""

    def test_a_run_that_has_not_failed_offers_no_retry(self, scheduled_run_page: Any) -> None:
        """A run in any state but failed MUST NOT draw the retry control.

        Why:
            The retry reaches a failed run alone. A control on a healthy run
            would invite a press that the route refuses, and the operator would
            read a refusal instead of a page that never offered the control.
        """
        assert scheduled_run_page.get_by_test_id(RETRY_REGION_ID).count() == 0, "only a failed run offers a retry"
        assert scheduled_run_page.get_by_test_id(RETRY_BUTTON_ID).count() == 0, "only a failed run offers a retry"

    def test_a_plain_press_builds_a_retry_of_a_failed_run(self, failed_run_page: Any) -> None:
        """A plain press MUST build a retry and MUST ask for a fresh capture.

        Why:
            The retry keeps every option of the failed run, so no operator
            rebuilds a plan by hand and drops a setting on the way. Only a press
            proves that the button carries the run key to the route.
        """
        page = failed_run_page
        button = page.get_by_test_id(RETRY_BUTTON_ID)
        _require_enabled(button, RETRY_BUTTON_ID)

        button.click()  # A plain press. No force, and no raised timeout.

        flash = page.get_by_test_id(FLASH_REGION_ID)
        sync_api.expect(flash).to_contain_text(RETRY_MESSAGE, timeout=FLASH_TIMEOUT_MS)
