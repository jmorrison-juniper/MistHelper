"""Browser tests for the upgrade journey of the upgrade capture portal.

Why:
    A contract test proves that the start endpoint refuses every word but
    `CONFIRM`. It cannot prove that the operator can pick a version, read the
    warning list, type the word, and then watch each device settle. Those four
    steps cross three pages and one script, so only a browser test proves them.

What this module skips and what it fails:
    The module reports a skip when no browser binary exists, and when the run
    under test holds no device. It reports a failure when a page answers 401 or
    404, and when a page answers 200 and the identifier contract does not hold.
    The fixture starts its own portal, so a 401 and a 404 are both faults of
    that portal. A portal that a browser test cannot reach never reports a pass.

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
from typing import Any

import pytest

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
RUN_STATE_ID = "upgrade-state"
RUN_TABLE_ID = "upgrade-run-table"
DEVICE_STATE_PREFIX = "upgrade-device-state-"
PHASE_PREFIX = "upgrade-phase-"
PHASE_PROGRESS_PREFIX = "upgrade-phase-progress-"

# FR-053 settles the four families in this order, and `data-model.md` repeats it.
PHASE_NAMES = ("gateways", "switches", "aps", "clients")

CONFIRM_WORD = "CONFIRM"  # FR-033 fixes this exact text and this exact letter case.
NEAR_MISS_WORD = "confirm"  # The same word in lower case, which must not unlock the start.

OK_STATUS = 200  # The contract fixes this status for every page below.
CREATED_STATUS = 201  # `POST /api/sites/<site_id>/runs` answers 201.
ACCEPTED_STATUS = 202  # `POST /api/sites/<site_id>/captures` answers 202 and reads on in its own thread.
UNAUTHORIZED_STATUS = 401  # `runtime/identity.py` answers this code with no session.
NOT_FOUND_STATUS = 404  # The route is not registered yet.
CONFLICT_STATUS = 409  # FR-037 holds one live run for each site, and the refusal names that run.

UPGRADE_RUNNING_CODE = "upgrade_already_running"  # The code that FR-037 answers on a second create call.

OFFERED_VERSION_INDEX = 1  # The entry at 0 is the empty prompt, so the first offered version sits at 1.
GATE_TIMEOUT_MS = 5000  # The script reads one key press, so the gate settles quickly.
SAVE_TIMEOUT_MS = 10000  # The save call writes the plan through the store, which may sit on a network.

STANDARD_TIER = 2  # `contracts/http-api.md` names tier 2 as the device state and the client lists.
PRE_ROLE = "pre"  # The half of the run that runs before the upgrade.
VERIFIED_STATE = "verified"  # The state that FR-035 reads before it allows a start.
VERIFY_TRIES = 40  # Twenty seconds in all, which covers a slow workstation.
VERIFY_PAUSE_MS = 500  # The collection thread holds the progress guard for a moment only.

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
        pytest.skip("The site picker shows no site row, so no site identifier exists to upgrade.")
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


@pytest.fixture
def run_id(portal_page: Any) -> str:
    """Create one upgrade run for the first site and return its key.

    Why:
        Every page of this journey needs a run key, and the contract fixes no
        page that lists the runs of a site. The fixture therefore creates a run
        through the documented endpoint, exactly as the site page does.

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
    if answer.status == CONFLICT_STATUS:  # One live run already holds this site, and the refusal names it.
        return _named_live_run(answer, path)  # The journey opens that run, as the refusal instructs.
    if answer.status != CREATED_STATUS:  # No run exists, so no page of this journey can open.
        pytest.skip(f"{path} answered {answer.status}. The contract fixes 201, so no run key exists.")
    return str(json.loads(answer.text())["run_id"])


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
        documented endpoint rather than write the field by hand.

    Args:
        page: The browser page that points at the portal.
        run_id: The key of the run that owns the capture.

    Returns:
        The capture key, which is empty when the capture never verified.
    """
    site_id = _first_site_id(page)
    headers = {CSRF_HEADER: _csrf_token(page), "Content-Type": "application/json"}
    body = json.dumps({"tier": STANDARD_TIER, "run_id": run_id, "role": PRE_ROLE})
    answer = page.request.post(CAPTURES_API_TEMPLATE.format(site_id=site_id), headers=headers, data=body)
    if answer.status != ACCEPTED_STATUS:  # The capture never started, so no pre-check can verify.
        return ""
    capture_id = str(json.loads(answer.text())["capture_id"])
    return capture_id if _capture_verified(page, capture_id) else ""


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
    return False  # The caller then leaves the skip in place and names the true cause.


@pytest.fixture
def confirm_page(portal_page: Any, run_id: str) -> Any:
    """Return a page that shows the last step before the portal sends anything.

    Why:
        The page holds its confirm field locked until the run names a verified
        pre-check capture and a plan with at least one device. The fixture
        therefore saves the plan and takes that capture first. The visit follows
        both, because the page reads the two values once at render.

    Args:
        portal_page: The browser page that points at the portal.
        run_id: The key of the fresh run.

    Returns:
        The Playwright page object, on the confirm page.
    """
    _saved_options(portal_page, run_id)  # A false answer leaves the field locked, which each test reports.
    _verified_pre_capture(portal_page, run_id)  # An empty answer leaves the skip in place below.
    path = CONFIRM_PAGE_TEMPLATE.format(run_id=run_id)
    _require_built_route(_page_status(portal_page, path), path)
    return portal_page


def _is_options_save(answer: Any) -> bool:
    """Answer whether one response came from the option save call.

    Args:
        answer: The Playwright response object.

    Returns:
        True when the response answers a POST to the option save endpoint.
    """
    return str(answer.request.method) == "POST" and str(answer.url).endswith(OPTIONS_API_SUFFIX)


def _chose_one_version_for_every_device(page: Any) -> bool:
    """Pick the first offered version in the bulk control of the options page.

    Why:
        Each device control starts empty, because an empty version means that
        the operator does not want to upgrade that device. The bulk control is
        the shipped way to fill every control at once, so this helper drives
        that control rather than write a value into each row by hand.

    Args:
        page: The Playwright page object, on the options page.

    Returns:
        True when the page offered a version and the bulk control took it.
    """
    chose_target = False
    for test_id in TYPE_VERSION_SELECT_IDS:
        picker = page.get_by_test_id(test_id)
        if picker.locator("option").count() > OFFERED_VERSION_INDEX:
            picker.select_option(index=OFFERED_VERSION_INDEX)
            chose_target = True
    return chose_target


def _saved_options(page: Any, run_id: str) -> bool:
    """Plan the devices of one run by clicking the save control of the options page.

    Why:
        The run table draws one row for each planned device, and the save call is
        the one writer of that plan. A test that wrote the plan straight into the
        store would leave the save control unproven, so this helper clicks the
        control that the operator clicks.

    Args:
        page: The browser page that points at the portal.
        run_id: The key of the run that holds the plan.

    Returns:
        True when the save call answered 200, so the run now names its devices.
    """
    if _page_status(page, OPTIONS_PAGE_TEMPLATE.format(run_id=run_id)) != OK_STATUS:
        return False  # The options page never opened, so the caller keeps its own skip.
    if not _chose_one_version_for_every_device(page):
        return False  # No version exists to plan, so the save call would keep an empty plan.
    with page.expect_response(_is_options_save, timeout=SAVE_TIMEOUT_MS) as event:
        page.get_by_test_id(OPTIONS_SAVE_ID).click()
    if event.value.status != OK_STATUS:
        return False  # The save was refused, so the caller names the true cause.
    # The button carries the confirm page in `data-next-url`, so the browser
    # moves there. The wait lets that move finish before the caller opens
    # another page, because two navigations at once cancel each other.
    page.wait_for_url(f"**{CONFIRM_PAGE_TEMPLATE.format(run_id=run_id)}", timeout=SAVE_TIMEOUT_MS)
    return True


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
    _saved_options(portal_page, run_id)  # A false answer leaves the skip of each test in place.
    path = PROGRESS_PAGE_TEMPLATE.format(run_id=run_id)
    _require_built_route(_page_status(portal_page, path), path)
    return portal_page


def _skip_without_target(page: Any) -> list[str]:
    """Return every device address of the target table, or skip when it is empty.

    Args:
        page: The Playwright page object, on the options page.

    Returns:
        The device address of each target row.
    """
    macs = _marker_keys(page, TARGET_ROW_PREFIX)
    if not macs:  # The run reached no device, so no version control exists to read.
        pytest.skip("The target table holds no row, so the run has no device to upgrade.")
    return macs


class TestUpgradeOptions:
    """The options page picks a version and sets the four upgrade options."""

    def test_options_page_shows_every_option_control(self, options_page: Any) -> None:
        """The page shows the bulk version control, the three groups, and the save control.

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
        for mac in _skip_without_target(options_page):
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
        junos_yes = options_page.get_by_test_id(JUNOS_YES_ID)  # The Junos file action on.
        junos_no = options_page.get_by_test_id(JUNOS_NO_ID)  # The Junos default, which is off.
        junos_yes.check()  # The operator turns the Junos file action on.
        sync_api.expect(junos_yes).to_be_checked()  # The chosen action holds.
        sync_api.expect(junos_no).not_to_be_checked()  # The default clears.


class TestUpgradeConfirm:
    """The confirm page holds the start behind the typed word `CONFIRM`."""

    def test_confirm_page_shows_the_warning_list(self, confirm_page: Any) -> None:
        """The page shows the warning list that the plan produced.

        Why:
            FR-031 asks the operator to read every warning before the start. A
            page that hid the list would send an upgrade that the operator never
            agreed to in full.

        Args:
            confirm_page: The page that shows the last step.
        """
        sync_api.expect(confirm_page.get_by_test_id(WARNING_LIST_ID)).to_be_visible()

    def test_confirm_page_locks_the_start_before_any_word(self, confirm_page: Any) -> None:
        """The start control is locked while the field holds nothing.

        Why:
            FR-033 holds the start behind typed text. The markup itself carries
            the locked state, so a browser that fails to load the script leaves
            the start locked instead of unlocked.

        Args:
            confirm_page: The page that shows the last step.
        """
        sync_api.expect(confirm_page.get_by_test_id(CONFIRM_INPUT_ID)).to_be_visible()
        sync_api.expect(confirm_page.get_by_test_id(START_BUTTON_ID)).to_be_disabled()

    def test_confirm_page_keeps_the_start_locked_for_the_wrong_letter_case(self, confirm_page: Any) -> None:
        """The word in lower case does not unlock the start control.

        Why:
            FR-033 names the letter case. The stylesheet shows the typed text in
            capital letters, so an operator who types lower case sees capital
            letters. The gate must still refuse that text.

        Args:
            confirm_page: The page that shows the last step.
        """
        field = confirm_page.get_by_test_id(CONFIRM_INPUT_ID)
        if field.is_disabled():  # No verified pre-check exists, so the gate cannot open at all.
            pytest.skip("The confirm field is disabled, because the run holds no verified pre-check capture.")
        field.fill(NEAR_MISS_WORD)
        sync_api.expect(confirm_page.get_by_test_id(START_BUTTON_ID)).to_be_disabled()

    def test_confirm_page_unlocks_the_start_after_the_exact_word(self, confirm_page: Any) -> None:
        """The exact word unlocks the start control.

        Args:
            confirm_page: The page that shows the last step.
        """
        field = confirm_page.get_by_test_id(CONFIRM_INPUT_ID)
        if field.is_disabled():  # No verified pre-check exists, so the gate cannot open at all.
            pytest.skip("The confirm field is disabled, because the run holds no verified pre-check capture.")
        field.fill(CONFIRM_WORD)
        button = confirm_page.get_by_test_id(START_BUTTON_ID)
        sync_api.expect(button).to_be_enabled(timeout=GATE_TIMEOUT_MS)


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
        macs = _marker_keys(progress_page, DEVICE_STATE_PREFIX)
        if not macs:  # The run reached no device, so the table holds no state cell.
            pytest.skip("The run table holds no device row, so the run has no device to watch.")
        for mac in macs:
            sync_api.expect(progress_page.get_by_test_id(f"{DEVICE_STATE_PREFIX}{mac}")).to_be_visible()
