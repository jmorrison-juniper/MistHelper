"""Browser tests for the upgrade journey of the upgrade capture portal.

Why:
    A contract test proves that the start endpoint refuses every word but
    `CONFIRM`. It cannot prove that the operator can pick a version, read the
    warning list, type the word, and then watch each device settle. Those four
    steps cross three pages and one script, so only a browser test proves them.

What this module skips and what it fails:
    The module reports a skip only when no browser binary exists. It reports a
    failure when a page answers 401 or 404, and when a page answers 200 and the
    identifier contract does not hold. It also reports a failure when a step of
    the journey does not complete, such as the plan save or the pre-check
    capture. The fixture starts its own portal and its own stand-in cloud, so
    each of those faults belongs to that portal. Issue #3377 records three
    tests that skipped on every run and proved nothing. A portal that a browser
    test cannot reach never reports a pass.

Identifier contract:
    `contracts/ui-testids.md` fixes every identifier below. Rule 4 states that a
    test selects by `data-testid` only, so every locator reads that attribute.
    The contract also states that the target table and the run table are two
    different tables, so the progress tests select `upgrade-run-table`.

Why the helpers repeat `test_capture.py`:
    The shared `conftest.py` of this directory belongs to every browser module,
    and a helper for one journey does not belong in it. The four helpers below
    therefore live in this module, beside the tests that read them.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pytest

from tests.e2e.upgrade_portal.conftest import (  # Issue #3377: the stand-in facts that this journey reads.
    JOURNEY_SITE_ID,  # The site that only this journey uses.
    STAND_IN_DEVICE_TYPES,  # The stand-in cloud offers one device of each of these types.
)

# The Playwright package must exist before this module defines a browser test.
# A run without the package reports a skip and never an import error.
sync_api = pytest.importorskip("playwright.sync_api", reason="The Playwright package is not installed.")

# `contracts/http-api.md` fixes this path for the site picker.
SITE_PAGE_PATH = "/select/site"
SITE_ROW_PREFIX = "site-row-"

# `contracts/http-api.md` section 5 fixes the create path and the three pages.
RUNS_API_TEMPLATE = "/api/sites/{site_id}/runs"
CAPTURES_API_TEMPLATE = "/api/sites/{site_id}/captures"
CAPTURE_STATUS_TEMPLATE = "/api/captures/{capture_id}/status"
LOCK_API_TEMPLATE = "/api/sites/{site_id}/lock"  # `contracts/site-lock.md` fixes this path for the release.
OPTIONS_PAGE_TEMPLATE = "/runs/{run_id}/options"
CONFIRM_PAGE_TEMPLATE = "/runs/{run_id}/confirm"
PROGRESS_PAGE_TEMPLATE = "/runs/{run_id}"
OPTIONS_API_SUFFIX = "/options"  # `POST /api/runs/<run_id>/options` is the one writer of the device plan.

CSRF_META_ID = "csrf-meta"  # `layout.html` publishes the token under this identifier.
CSRF_HEADER = "X-CSRFToken"  # `portal.js` sends the token under this header name.

# The options page controls.
TYPE_VERSION_SELECT_IDS = (
    "upgrade-version-select-ap",
    "upgrade-version-select-switch",
    "upgrade-version-select-gateway",
)
REBOOT_GROUP_ID = "upgrade-reboot-group"
REBOOT_YES_ID = "upgrade-reboot-yes"
REBOOT_NO_ID = "upgrade-reboot-no"
STRATEGY_GROUP_ID = "upgrade-strategy-group"
STRATEGY_BIG_BANG_ID = "upgrade-strategy-big-bang"
STRATEGY_CANARY_ID = "upgrade-strategy-canary"
JUNOS_GROUP_ID = "upgrade-junos-file-action-group"
JUNOS_YES_ID = "upgrade-junos-file-action-yes"
JUNOS_NO_ID = "upgrade-junos-file-action-no"
OPTIONS_SAVE_ID = "upgrade-options-save-button"
TARGET_TABLE_ID = "upgrade-target-table"
TARGET_ROW_PREFIX = "upgrade-target-row-"
VERSION_SELECT_PREFIX = "upgrade-version-select-"

# The confirm page controls.
WARNING_LIST_ID = "upgrade-warning-list"
CONFIRM_INPUT_ID = "upgrade-confirm-input"
START_BUTTON_ID = "upgrade-start-button"

# The progress page controls.
CONFIRM_LINK_ID = "upgrade-confirm-link"
RUN_STATE_ID = "upgrade-state"
RUN_TABLE_ID = "upgrade-run-table"
DEVICE_STATE_PREFIX = "upgrade-device-state-"
PHASE_PREFIX = "upgrade-phase-"
PHASE_PROGRESS_PREFIX = "upgrade-phase-progress-"

# FR-053 settles the four families in this order, and `data-model.md` repeats it.
PHASE_NAMES = ("gateways", "switches", "aps", "clients")

logger = logging.getLogger(__name__)  # Use this module name in browser start proof logs.

CONFIRM_WORD = "CONFIRM"  # FR-033 fixes this exact text and this exact letter case.
NEAR_MISS_WORD = "confirm"  # The same word in lower case, which must not unlock the start.

OK_STATUS = 200  # The contract fixes this status for every page below.
CREATED_STATUS = 201  # `POST /api/sites/<site_id>/runs` answers 201.
ACCEPTED_STATUS = 202  # `POST /api/sites/<site_id>/captures` answers 202 and reads on in its own thread.
UNAUTHORIZED_STATUS = 401  # `runtime/identity.py` answers this code with no session.
NOT_FOUND_STATUS = 404  # The route is not registered yet.
CONFLICT_STATUS = 409  # FR-037 holds one live run for each site, and the refusal names that run.

UPGRADE_RUNNING_CODE = "upgrade_already_running"  # The code that FR-037 answers on a second create call.
LOCK_BANNER_ID = "lock-banner"  # `partials/lock_banner.html` publishes the lock token of this browser here.
LOCK_TOKEN_ATTRIBUTE = "data-lock-token"  # `portal.js` reads this attribute for the beat and the release.
LOCK_TOKEN_FIELD = "lock_token"  # `contracts/http-api.md` section 3 names this body field for a release.

OFFERED_VERSION_INDEX = 1  # The entry at 0 is the empty prompt, so the first offered version sits at 1.
GATE_TIMEOUT_MS = 5000  # The script reads one key press, so the gate settles quickly.
SAVE_TIMEOUT_MS = 10000  # The save call writes the plan through the store, which may sit on a network.

STANDARD_TIER = 2  # `contracts/http-api.md` names tier 2 as the device state and the client lists.
PRE_ROLE = "pre"  # The half of the run that runs before the upgrade.
VERIFIED_STATE = "verified"  # The state that FR-035 reads before it allows a start.
VERIFY_TRIES = 40  # Twenty seconds in all, which covers a slow workstation.
VERIFY_PAUSE_MS = 500  # The collection thread holds the progress guard for a moment only.
PREPARED_RUN_ID = "e2e-prepared-run-0001"  # `conftest.py` seeds this awaiting-confirmation run.
START_READY_RUN_ID = "e2e-start-ready-run-0001"  # `conftest.py` seeds this run for the start proof.
SEED_TIMEOUT_MS = 30000  # A cold store can take several seconds to write the seeded browser fixture.

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

    Raises:
        AssertionError: If the browser returned no response. A navigation to a
            portal path always carries one, so its absence is a fault.
    """
    answer = page.goto(path, wait_until="domcontentloaded")  # Open the page the way an operator does.
    assert answer is not None, f"The browser returned no response for {path}, so the test has nothing to read."
    status: int = answer.status  # The status that the portal answered.
    return status  # The caller decides which status the contract fixes.


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

    Why:
        A test cannot know a site key or a device address in advance. The page
        publishes both inside its identifiers, so the test reads them from the
        one attribute that Rule 4 allows.

    Args:
        page: The Playwright page object.
        prefix: The identifier prefix, such as `upgrade-target-row-`.

    Returns:
        The tail of each matching identifier, in page order.
    """
    found = page.locator(f'[data-testid^="{prefix}"]')  # A prefix match still selects by `data-testid`.
    markers = found.evaluate_all("nodes => nodes.map(node => node.getAttribute('data-testid'))")
    return [str(marker)[len(prefix) :] for marker in markers if marker]


def _journey_site_id(page: Any) -> str:
    """Open the site picker, and return the site that only this journey uses.

    Why:
        Issue #3377. Seeded live runs hold the first site of the picker, and
        FR-037 allows one live run for each site. The create call then opened a
        seeded run that another module also reads. The journey site holds no
        seeded run, so every run on it belongs to this module. The picker opens
        first, because the calls below read the token that the page publishes.

    Args:
        page: The Playwright page object.

    Returns:
        The site identifier of the journey site.

    Raises:
        AssertionError: If the picker does not show the journey site as a row.
    """
    _require_built_route(_page_status(page, SITE_PAGE_PATH), SITE_PAGE_PATH)  # The picker must answer 200.
    keys = _marker_keys(page, SITE_ROW_PREFIX)  # The page publishes each site key in a row identifier.
    assert JOURNEY_SITE_ID in keys, f"The site picker shows no row for the journey site {JOURNEY_SITE_ID}."
    return JOURNEY_SITE_ID  # The run and the pre-check capture both use this site.


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


@pytest.fixture
def run_id(portal_page: Any) -> str:
    """Create one upgrade run for the journey site and return its key.

    Why:
        Every page of this journey needs a run key, and the contract fixes no
        page that lists the runs of a site. The fixture therefore creates a run
        through the documented endpoint, exactly as the site page does. The
        first test of the module gets a new run. Each later test meets the 409
        of FR-037, and the refusal names that same run.

    Args:
        portal_page: The browser page that points at the portal.

    Returns:
        The key of the fresh run.

    Raises:
        AssertionError: If the call never completed, or if the endpoint answers
            401, 404, or any other status than 201 and 409. Each one names a
            fault of the portal that the server fixture started, so none of
            them may report a skip.
    """
    site_id = _journey_site_id(portal_page)  # Issue #3377: no seeded run holds this site.
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
    if answer.status == CONFLICT_STATUS:  # One live run already holds this site, and the refusal names it.
        return _named_live_run(answer, path)  # The journey opens that run, as the refusal instructs.
    assert answer.status == CREATED_STATUS, f"{path} answered {answer.status}. The contract fixes 201 for a new run."
    return str(json.loads(answer.text())["run_id"])  # The key of the run that this call created.


@pytest.fixture
def options_page(portal_page: Any, run_id: str) -> Any:
    """Return a page that shows the version picker of one run.

    Args:
        portal_page: The browser page that points at the portal.
        run_id: The key of the fresh run.

    Returns:
        The Playwright page object, on the options page.
    """
    path = OPTIONS_PAGE_TEMPLATE.format(run_id=run_id)
    _require_built_route(_page_status(portal_page, path), path)
    return portal_page


def _verified_pre_capture(page: Any, run_id: str) -> str:
    """Take the pre-check capture of one run and wait for it to verify.

    Why:
        FR-035 refuses a start until the run names a verified pre-check, and the
        confirm page holds its own field locked until then. The operator reaches
        that state by taking the pre-check, so this helper takes it through the
        documented endpoint rather than write the field by hand. Issue #3377: a
        capture that does not verify is a fault of the portal that the fixture
        started, so the helper fails and names the cause.

    Args:
        page: The browser page that points at the portal.
        run_id: The key of the run that owns the capture.

    Returns:
        The key of the verified capture.

    Raises:
        AssertionError: If the capture does not start, or if it does not verify
            inside the wait.
    """
    path = CAPTURES_API_TEMPLATE.format(site_id=JOURNEY_SITE_ID)  # The run of this journey lives on this site.
    headers = {CSRF_HEADER: _csrf_token(page), "Content-Type": "application/json"}  # The page token signs the call.
    body = json.dumps({"tier": STANDARD_TIER, "run_id": run_id, "role": PRE_ROLE})  # The pre-check of this run.
    logger.info("Take the pre-check capture of the run %s", run_id)  # Record the capture call before it starts.
    answer = page.request.post(path, headers=headers, data=body)  # The documented start call of a capture.
    assert answer.status == ACCEPTED_STATUS, f"{path} answered {answer.status}, so no pre-check started."
    capture_id = str(json.loads(answer.text())["capture_id"])  # The key that the status path reads.
    assert _capture_verified(page, capture_id), f"The pre-check capture {capture_id} did not verify inside the wait."
    logger.debug("The pre-check capture %s of the run %s verified", capture_id, run_id)  # Record the result.
    return capture_id  # The run now names this capture, so the confirm field can open.


def _capture_verified(page: Any, capture_id: str) -> bool:
    """Poll one capture until it verifies, or until the wait runs out.

    Why:
        The start route answers 202 and the collection runs in its own thread,
        so the field of the confirm page opens a moment after the call returns.
        A test that read the page at once would meet the locked field and would
        report a fault that the portal does not hold.

    Args:
        page: The browser page that points at the portal.
        capture_id: The key of the capture to watch.

    Returns:
        True when the capture reported the verified state inside the wait.
    """
    path = CAPTURE_STATUS_TEMPLATE.format(capture_id=capture_id)
    for _ in range(VERIFY_TRIES):  # A bounded wait, so a stuck capture never holds the suite open.
        answer = page.request.get(path)
        if answer.status == OK_STATUS and json.loads(answer.text()).get("state") == VERIFIED_STATE:
            return True  # The run now names this capture, so the confirm field opens.
        page.wait_for_timeout(VERIFY_PAUSE_MS)  # The collection thread holds the guard for a moment.
    return False  # The caller then fails and names the capture that did not verify.


def _release_the_site(page: Any, run_id: str) -> None:
    """Give up the site lock that the pre-check capture of this browser took.

    Why:
        Issue #3377. The pre-check capture takes the site lock for this browser.
        The lock names one operator and one browser, and each test opens a new
        browser. FR-080 lets the same operator take the site back only after the
        first browser goes quiet. Without this step, the next test met a save
        control that the page held off. An operator at the end of a journey
        frees the site, so this step sends the release call of the lock banner.

        The confirm page shows no lock banner, so the step opens the options
        page. A fresh render publishes the token that the session holds now.

    Args:
        page: The browser page that took the pre-check capture.
        run_id: The key of the run, which names the options page.

    Raises:
        AssertionError: If the options page does not open, or if the release of
            a published token answers a status other than 200.
    """
    options_path = OPTIONS_PAGE_TEMPLATE.format(run_id=run_id)  # A page that shows the lock banner of the site.
    _require_built_route(_page_status(page, options_path), options_path)  # The render reads the session lock.
    banner = page.get_by_test_id(LOCK_BANNER_ID)  # The banner holds the token of this browser.
    token = str(banner.get_attribute(LOCK_TOKEN_ATTRIBUTE) or "")  # Empty means that this browser holds no lock.
    if not token:  # The setup stopped before the capture, so this browser took no lock.
        logger.debug("This browser holds no lock on the journey site")  # Record the empty result.
        return  # The next test finds the site as this test found it.
    path = LOCK_API_TEMPLATE.format(site_id=JOURNEY_SITE_ID)  # The release path of the journey site.
    headers = {CSRF_HEADER: _csrf_token(page), "Content-Type": "application/json"}  # The page token signs the call.
    body = json.dumps({LOCK_TOKEN_FIELD: token})  # The release proves that this browser holds the lock.
    logger.info("Release the site lock of the journey site")  # Record the release before the call.
    answer = page.request.delete(path, headers=headers, data=body)  # The same call that `releaseSiteLock` sends.
    assert answer.status == OK_STATUS, f"{path} answered {answer.status}: {answer.text()}. The site stays locked."
    logger.debug("The journey site is free again")  # Record the result after the release.


@pytest.fixture
def confirm_page(request: pytest.FixtureRequest, portal_page: Any, run_id: str) -> Any:
    """Return a page that shows the last step before the portal sends anything.

    Why:
        The page holds its confirm field locked until the run names a verified
        pre-check capture and a plan with at least one device. The fixture
        therefore saves the plan and takes that capture first. The visit follows
        both, because the page reads the two values once at render.

        Issue #3377: the capture takes the site lock for this browser, and the
        next test opens a new browser. The fixture therefore releases the lock
        when the test ends.

    Args:
        request: The pytest request object, which holds the release step.
        portal_page: The browser page that points at the portal.
        run_id: The key of the fresh run.

    Returns:
        The Playwright page object, on the confirm page.
    """
    _save_the_plan(portal_page, run_id)  # A plan that does not save fails here and names the cause.
    request.addfinalizer(lambda: _release_the_site(portal_page, run_id))  # The release runs when a later step fails.
    _verified_pre_capture(portal_page, run_id)  # A capture that does not verify fails here and names the cause.
    path = CONFIRM_PAGE_TEMPLATE.format(run_id=run_id)  # The page that the two steps above unlock.
    _require_built_route(_page_status(portal_page, path), path)  # The page itself must answer 200.
    return portal_page  # Each test reads the confirm page from here.


def _is_options_save(answer: Any) -> bool:
    """Answer whether one response came from the option save call.

    Args:
        answer: The Playwright response object.

    Returns:
        True when the response answers a POST to the option save endpoint.
    """
    return str(answer.request.method) == "POST" and str(answer.url).endswith(OPTIONS_API_SUFFIX)


def _chose_one_version_for_every_device(page: Any) -> bool:
    """Pick the first offered version in each type control of the options page.

    Why:
        The options page holds one version control for each device type. A pick
        in a type control fills the version of each device of that type, so this
        helper drives those three controls rather than write a value into each
        row by hand.

    Args:
        page: The Playwright page object, on the options page.

    Returns:
        True when at least one type control offered a version and took it.
    """
    chose_target = False  # No control has offered a version yet.
    for test_id in TYPE_VERSION_SELECT_IDS:  # One control for each device type.
        picker = page.get_by_test_id(test_id)  # The contract fixes this identifier.
        if picker.locator("option").count() > OFFERED_VERSION_INDEX:  # The empty prompt, then each version.
            picker.select_option(index=OFFERED_VERSION_INDEX)  # The first offered version is the newest one.
            chose_target = True  # At least one device type now holds a version.
    return chose_target  # False means the page offered no version at all.


def _save_the_plan(page: Any, run_id: str) -> None:
    """Plan the devices of one run by clicking the save control of the options page.

    Why:
        The run table draws one row for each planned device, and the save call is
        the one writer of that plan. A test that wrote the plan straight into the
        store would leave the save control unproven, so this helper clicks the
        control that the operator clicks. Issue #3377: the fixture starts its own
        portal and its own stand-in cloud, so a plan that does not save is a
        fault of that portal. The helper therefore fails and names the cause.

    Args:
        page: The browser page that points at the portal.
        run_id: The key of the run that holds the plan.

    Raises:
        AssertionError: If the options page does not open, if no type control
            offers a version, or if the save call does not answer 200.
    """
    path = OPTIONS_PAGE_TEMPLATE.format(run_id=run_id)  # The page that holds the save control.
    _require_built_route(_page_status(page, path), path)  # A page that does not open fails with its status.
    assert _chose_one_version_for_every_device(page), f"No type control of {path} offers a version to plan."
    logger.info("Save the plan of the run %s", run_id)  # Record the save call before the click.
    with page.expect_response(_is_options_save, timeout=SAVE_TIMEOUT_MS) as event:  # Catch the save answer.
        page.get_by_test_id(OPTIONS_SAVE_ID).click()  # The control that the operator clicks.
    status = event.value.status  # The answer of the one writer of the plan.
    assert status == OK_STATUS, f"The options save of the run {run_id} answered {status}. The contract fixes 200."
    # The button carries the confirm page in `data-next-url`, so the browser
    # moves there. The wait lets that move finish before the caller opens
    # another page, because two navigations at once cancel each other.
    page.wait_for_url(f"**{CONFIRM_PAGE_TEMPLATE.format(run_id=run_id)}", timeout=SAVE_TIMEOUT_MS)
    logger.debug("The run %s holds a saved plan", run_id)  # Record the result after the move ends.


@pytest.fixture
def progress_page(portal_page: Any, run_id: str) -> Any:
    """Return a page that shows the live view of one run.

    Why:
        The run table holds one row for each device that the run plans, and the
        options page is where the operator picks those devices. The fixture
        therefore saves the options first, so the live view has a device to show.

    Args:
        portal_page: The browser page that points at the portal.
        run_id: The key of the fresh run.

    Returns:
        The Playwright page object, on the progress page.
    """
    _save_the_plan(portal_page, run_id)  # A plan that does not save fails here and names the cause.
    path = PROGRESS_PAGE_TEMPLATE.format(run_id=run_id)  # The live view of the run.
    _require_built_route(_page_status(portal_page, path), path)  # The page itself must answer 200.
    return portal_page  # Each test reads the progress page from here.


def _target_macs(page: Any) -> list[str]:
    """Return every device address of the target table, and fail when it is empty.

    Why:
        Issue #3377. The stand-in cloud offers one device of each type, so an
        empty target table is a fault of the portal that the fixture started.
        A skip here would report a pass for a page that shows no device.

    Args:
        page: The Playwright page object, on the options page.

    Returns:
        The device address of each target row.

    Raises:
        AssertionError: If the target table holds no row.
    """
    macs = _marker_keys(page, TARGET_ROW_PREFIX)  # The page publishes each address in a row identifier.
    assert macs, "The target table holds no row, although the stand-in cloud offers one device of each type."
    return macs  # One address for each target row, in page order.


def _checked_choices(page: Any, group_id: str) -> int:
    """Count the checked choices of one radio group on the options page.

    Why:
        A radio group must hold exactly one choice. A count of zero sends the
        default with no consent, and a count of two sends a choice that the
        operator cannot read back.

    Args:
        page: The Playwright page object, on the options page.
        group_id: The identifier of the group, such as `upgrade-reboot-group`.

    Returns:
        The count of checked radio inputs inside the group.
    """
    return int(page.get_by_test_id(group_id).locator("input[type=radio]:checked").count())  # The live state.


class TestUpgradeOptions:
    """The options page picks a version and sets the four upgrade options."""

    def test_options_page_shows_every_option_control(self, options_page: Any) -> None:
        """The page shows the three type controls, the three groups, and the save control.

        Why:
            FR-121 turns the reboot option, the strategy option, and the Junos
            file action into radio groups. An operator who cannot see one of them
            cannot choose it, and the portal would then send the default to live
            hardware with no consent.

        Args:
            options_page: The page that shows the version picker.
        """
        for test_id in TYPE_VERSION_SELECT_IDS:
            sync_api.expect(options_page.get_by_test_id(test_id)).to_be_visible()
        assert options_page.get_by_test_id("upgrade-version-select-all").count() == 0
        sync_api.expect(options_page.get_by_test_id(REBOOT_GROUP_ID)).to_be_visible()
        sync_api.expect(options_page.get_by_test_id(STRATEGY_GROUP_ID)).to_be_visible()
        sync_api.expect(options_page.get_by_test_id(JUNOS_GROUP_ID)).to_be_visible()
        sync_api.expect(options_page.get_by_test_id(OPTIONS_SAVE_ID)).to_be_visible()

    def test_options_page_offers_a_version_in_each_type_control(self, options_page: Any, tmp_path: Path) -> None:
        """Each type control offers at least one version to pick.

        Why:
            Issue #3377. Each type control draws its versions from the
            `type_selections` field of the options view. A control that holds
            only the empty prompt gives the operator no way to plan that device
            type, and the save control then keeps an empty plan.

        Args:
            options_page: The page that shows the version picker.
            tmp_path: The folder that keeps the screenshot of this test.
        """
        for test_id in TYPE_VERSION_SELECT_IDS:  # The stand-in site holds one device of each type.
            offered = options_page.get_by_test_id(test_id).locator("option").count()  # The prompt and each version.
            assert offered > OFFERED_VERSION_INDEX, f"{test_id} offers no version, so no device of its type can plan."
        shot = tmp_path / "options-type-controls.png"  # The evidence that an engineer compares with the page.
        options_page.screenshot(path=str(shot), full_page=True)  # Keep the page that offered each version.
        assert shot.exists(), f"The screenshot {shot} was not written."  # A missing file is missing evidence.

    def test_options_page_gives_one_version_control_to_each_device(self, options_page: Any) -> None:
        """Every target row carries its own version control.

        Why:
            FR-026 lets an operator hold one device back on its current version.
            A page with one control for the whole table would force every device
            onto the same version, which removes that choice.

        Args:
            options_page: The page that shows the version picker.
        """
        sync_api.expect(options_page.get_by_test_id(TARGET_TABLE_ID)).to_be_visible()
        macs = _target_macs(options_page)  # One address for each target row.
        expected = len(STAND_IN_DEVICE_TYPES)  # The stand-in cloud offers one device of each type.
        assert len(macs) == expected, f"The target table shows {len(macs)} rows for {expected} devices."
        for mac in macs:
            sync_api.expect(options_page.get_by_test_id(f"{VERSION_SELECT_PREFIX}{mac}")).to_be_visible()

    def test_options_page_keeps_the_chosen_reboot_state(self, options_page: Any) -> None:
        """The reboot group holds the state the operator sets.

        Why:
            The reboot option decides whether the site drops traffic at the end
            of the upgrade. A radio group that snapped back to its default would
            send a reboot the operator cleared.

        Args:
            options_page: The page that shows the version picker.
        """
        reboot_no = options_page.get_by_test_id(REBOOT_NO_ID)  # The choice that holds the reboot back.
        reboot_yes = options_page.get_by_test_id(REBOOT_YES_ID)  # The default choice, which reboots.
        reboot_no.check()  # The operator clears the reboot.
        sync_api.expect(reboot_no).to_be_checked()  # The cleared choice holds.
        sync_api.expect(reboot_yes).not_to_be_checked()  # A radio group keeps exactly one choice.
        reboot_yes.check()  # The operator restores the reboot.
        sync_api.expect(reboot_yes).to_be_checked()  # The restored choice holds.
        sync_api.expect(reboot_no).not_to_be_checked()  # The other choice clears.
        checked = _checked_choices(options_page, REBOOT_GROUP_ID)  # The group state after two changes.
        assert checked == 1, f"The reboot group holds {checked} choices instead of exactly one."

    def test_options_page_holds_the_chosen_strategy_and_junos_action(self, options_page: Any) -> None:
        """The strategy group and the Junos group hold the choice the operator sets.

        Why:
            FR-121 turns each single choice into a radio group. A group that lost
            the choice would run a strategy or a Junos action the operator never
            picked.

        Args:
            options_page: The page that shows the version picker.
        """
        canary = options_page.get_by_test_id(STRATEGY_CANARY_ID)  # The staged strategy.
        big_bang = options_page.get_by_test_id(STRATEGY_BIG_BANG_ID)  # The default strategy.
        canary.check()  # The operator picks the staged rollout.
        sync_api.expect(canary).to_be_checked()  # The staged choice holds.
        sync_api.expect(big_bang).not_to_be_checked()  # The default clears.
        strategies = _checked_choices(options_page, STRATEGY_GROUP_ID)  # The strategy group state after the pick.
        assert strategies == 1, f"The strategy group holds {strategies} choices instead of exactly one."
        junos_yes = options_page.get_by_test_id(JUNOS_YES_ID)  # The default completes the Junos file action.
        junos_no = options_page.get_by_test_id(JUNOS_NO_ID)  # The operator can skip the Junos file action.
        sync_api.expect(junos_yes).to_be_checked()  # The safe default is on.
        sync_api.expect(junos_no).not_to_be_checked()  # A radio group keeps one default.
        junos_no.check()  # The operator turns the Junos file action off.
        sync_api.expect(junos_no).to_be_checked()  # The changed choice holds.
        sync_api.expect(junos_yes).not_to_be_checked()  # The default clears.
        junos_yes.check()  # The operator restores the default.
        sync_api.expect(junos_yes).to_be_checked()  # The restored choice holds.
        actions = _checked_choices(options_page, JUNOS_GROUP_ID)  # The Junos group state after two changes.
        assert actions == 1, f"The Junos group holds {actions} choices instead of exactly one."


class TestUpgradeConfirm:
    """The confirm page holds the start behind the typed word `CONFIRM`."""

    def test_prepared_run_links_to_the_confirmation_page(self, page: Any) -> None:
        """A prepared run exposes and follows the final-review action.

        Args:
            page: The signed-in browser page.
        """
        path = PROGRESS_PAGE_TEMPLATE.format(run_id=PREPARED_RUN_ID)
        link = page.get_by_test_id(CONFIRM_LINK_ID)
        for _ in range(SEED_TIMEOUT_MS // 1000):
            answer = page.goto(path)
            assert answer is not None and answer.status == OK_STATUS, f"{path} did not answer {OK_STATUS}."
            if link.count() == 1:
                break
            page.wait_for_timeout(1000)
        sync_api.expect(link).to_be_visible()
        link.click()
        sync_api.expect(page.get_by_test_id(CONFIRM_INPUT_ID)).to_be_visible()
        assert page.url.endswith(CONFIRM_PAGE_TEMPLATE.format(run_id=PREPARED_RUN_ID))

    def test_confirm_page_shows_the_warning_list(self, confirm_page: Any) -> None:
        """The page shows the warning list that the plan produced.

        Why:
            FR-031 asks the operator to read every warning before the start. A
            page that hid the list would send an upgrade that the operator never
            agreed to in full.

        Args:
            confirm_page: The page that shows the last step.
        """
        warning_list = confirm_page.get_by_test_id(WARNING_LIST_ID)  # The list that FR-031 asks the operator to read.
        sync_api.expect(warning_list).to_be_visible()
        lines = warning_list.locator("li").count()  # A plan with no warning still states that fact in one line.
        assert lines >= 1, "The warning list holds no line, so the operator reads nothing before the start."

    def test_confirm_page_locks_the_start_before_any_word(self, confirm_page: Any) -> None:
        """The start control is locked while the field holds nothing.

        Why:
            FR-033 holds the start behind typed text. The markup itself carries
            the locked state, so a browser that fails to load the script leaves
            the start locked instead of unlocked.

        Args:
            confirm_page: The page that shows the last step.
        """
        field = confirm_page.get_by_test_id(CONFIRM_INPUT_ID)  # The field that holds the typed word.
        button = confirm_page.get_by_test_id(START_BUTTON_ID)  # The control that sends the upgrade.
        sync_api.expect(field).to_be_visible()
        sync_api.expect(button).to_be_disabled()
        assert field.input_value() == "", "The confirm field holds text before the operator types."
        # The native attribute blocks a click even when the script never loads. A bare attribute reads as "".
        disabled = button.get_attribute("disabled")  # None means that the page renders no attribute.
        assert disabled == "", f"The start control carries the disabled value {disabled!r} instead of a bare attribute."

    def test_confirm_page_keeps_the_start_locked_for_the_wrong_letter_case(self, confirm_page: Any) -> None:
        """The word in lower case does not unlock the start control.

        Why:
            FR-033 names the letter case. The stylesheet shows the typed text in
            capital letters, so an operator who types lower case sees capital
            letters. The gate must still refuse that text.

        Args:
            confirm_page: The page that shows the last step.
        """
        field = confirm_page.get_by_test_id(CONFIRM_INPUT_ID)  # The field that holds the typed word.
        assert field.is_enabled(), "The confirm field is disabled after a saved plan and a verified pre-check."
        field.fill(NEAR_MISS_WORD)
        sync_api.expect(confirm_page.get_by_test_id(START_BUTTON_ID)).to_be_disabled()

    def test_confirm_page_unlocks_the_start_after_the_exact_word(self, confirm_page: Any, tmp_path: Path) -> None:
        """The exact word unlocks the start control.

        Args:
            confirm_page: The page that shows the last step.
            tmp_path: The folder that keeps the screenshot of this test.
        """
        field = confirm_page.get_by_test_id(CONFIRM_INPUT_ID)  # The field that holds the typed word.
        assert field.is_enabled(), "The confirm field is disabled after a saved plan and a verified pre-check."
        field.fill(CONFIRM_WORD)
        button = confirm_page.get_by_test_id(START_BUTTON_ID)
        sync_api.expect(button).to_be_enabled(timeout=GATE_TIMEOUT_MS)
        shot = tmp_path / "confirm-start-unlocked.png"  # The evidence that an engineer compares with the page.
        confirm_page.screenshot(path=str(shot), full_page=True)  # Keep the page with the unlocked start control.
        assert shot.exists(), f"The screenshot {shot} was not written."  # A missing file is missing evidence.


class TestUpgradeStart:
    """The firmware operator can complete the start journey."""

    def test_firmware_operator_starts_a_prepared_run(self, firmware_operator_page: Any) -> None:
        """The reachable test operator reaches the start route and the run page."""
        logger.info("Open the prepared browser upgrade run with the firmware operator")  # Record the proof start.
        run_id = START_READY_RUN_ID  # Use a seeded ready run that only this test mutates.
        prepared_path = PROGRESS_PAGE_TEMPLATE.format(run_id=run_id)  # Poll the run page that reveals the seed.
        confirm_link = firmware_operator_page.get_by_test_id(CONFIRM_LINK_ID)  # The link proves the run is ready.
        for _ in range(SEED_TIMEOUT_MS // 1000):  # The seed thread can finish after the server starts listening.
            answer = firmware_operator_page.goto(prepared_path)  # Open the run page through the browser.
            assert answer is not None and answer.status == OK_STATUS, f"{prepared_path} did not answer {OK_STATUS}."
            if confirm_link.count() == 1:  # The page now shows the route to the confirm step.
                break  # Stop waiting as soon as the prepared run is visible.
            firmware_operator_page.wait_for_timeout(1000)  # Wait before the next seed check.
        sync_api.expect(confirm_link).to_be_visible()  # Fail if the seed never produced a prepared run.
        logger.debug("Opened prepared browser upgrade run %s for the firmware operator", run_id)  # Record the key.
        confirm_path = CONFIRM_PAGE_TEMPLATE.format(run_id=run_id)  # Open the page that owns the typed word.
        _require_built_route(_page_status(firmware_operator_page, confirm_path), confirm_path)  # Fail on route gaps.
        field = firmware_operator_page.get_by_test_id(CONFIRM_INPUT_ID)  # Select the confirmation control by contract.
        assert not field.is_disabled(), "The confirm field is disabled, so the start path was not measured."
        field.fill(CONFIRM_WORD)  # Type the exact word that the server also checks.
        button = firmware_operator_page.get_by_test_id(START_BUTTON_ID)  # Select the start control by contract.
        sync_api.expect(button).to_be_enabled(timeout=GATE_TIMEOUT_MS)  # Prove the browser gate accepted the word.
        start_suffix = f"/api/runs/{run_id}/start"  # Match the endpoint without binding to the dynamic port.
        logger.info("Start the browser upgrade run %s", run_id)  # Record the measured start call.
        with firmware_operator_page.expect_response(lambda response: response.url.endswith(start_suffix)) as event:
            button.click()  # Click the same control an operator clicks.
        assert event.value.status == ACCEPTED_STATUS, "The start call did not answer the accepted status."
        progress_path = PROGRESS_PAGE_TEMPLATE.format(run_id=run_id)  # The script moves to this page after success.
        firmware_operator_page.wait_for_url(f"**{progress_path}", timeout=SAVE_TIMEOUT_MS)  # Prove navigation ended.
        sync_api.expect(firmware_operator_page.get_by_test_id(RUN_STATE_ID)).to_have_text(
            "upgrade_submitting"
        )  # Prove the run page shows the state that only the start route writes.
        logger.debug("The browser upgrade run %s reached the run page after start", run_id)  # Record success.


class TestUpgradeProgress:
    """The progress page shows the run state, the four phases, and each device."""

    def test_progress_page_shows_the_run_state(self, progress_page: Any) -> None:
        """The page names the run state in words.

        Why:
            The page refreshes itself every 30 seconds and holds no server-sent
            event. The state value is the one field that tells the operator
            whether the poll is still watching a live run.

        Args:
            progress_page: The page that shows the live run view.
        """
        state = progress_page.get_by_test_id(RUN_STATE_ID)
        sync_api.expect(state).to_be_visible()
        assert (state.inner_text() or "").strip(), f"{RUN_STATE_ID} reads no text, so the state is not shown."

    def test_progress_page_shows_the_four_cascade_phases(self, progress_page: Any) -> None:
        """The page shows one phase block and one settled count for each family.

        Why:
            FR-053 settles gateways, then switches, then access points, then
            wireless clients. A missing block would hide a family that never
            settled, so the operator would call the upgrade done too early.

        Args:
            progress_page: The page that shows the live run view.
        """
        for name in PHASE_NAMES:
            sync_api.expect(progress_page.get_by_test_id(f"{PHASE_PREFIX}{name}")).to_be_visible()
            sync_api.expect(progress_page.get_by_test_id(f"{PHASE_PROGRESS_PREFIX}{name}")).to_be_visible()
        blocks = [progress_page.get_by_test_id(f"{PHASE_PREFIX}{name}").count() for name in PHASE_NAMES]  # Each family.
        assert blocks == [1] * len(PHASE_NAMES), f"The phase blocks appear {blocks} times, not once for each family."

    def test_progress_page_gives_one_state_cell_to_each_device(self, progress_page: Any) -> None:
        """The run table shows the state of each device on its own row.

        Why:
            FR-041 asks for one line for each device. `contracts/ui-testids.md`
            states that a test which watches progress selects the run table, and
            never the target table of the options page.

        Args:
            progress_page: The page that shows the live run view.
        """
        sync_api.expect(progress_page.get_by_test_id(RUN_TABLE_ID)).to_be_visible()
        macs = _marker_keys(progress_page, DEVICE_STATE_PREFIX)  # One state cell for each planned device.
        expected = len(STAND_IN_DEVICE_TYPES)  # The plan save named one device of each type.
        assert len(macs) == expected, f"The run table holds {len(macs)} device rows, but the plan names {expected}."
        for mac in macs:
            sync_api.expect(progress_page.get_by_test_id(f"{DEVICE_STATE_PREFIX}{mac}")).to_be_visible()
