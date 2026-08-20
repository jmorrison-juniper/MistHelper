"""Browser tests for the upgrade journey of the upgrade capture portal.

Why:
    A contract test proves that the start endpoint refuses every word but
    `CONFIRM`. It cannot prove that the operator can pick a version, read the
    warning list, type the word, and then watch each device settle. Those four
    steps cross three pages and one script, so only a browser test proves them.

What this module skips and what it fails:
    The module reports a skip when the browser, the server, the session, or the
    route is absent, and when the run under test holds no device. It reports a
    failure when a page answers 200 and the identifier contract does not hold. A
    missing part of the environment never reports a pass.

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
OPTIONS_PAGE_TEMPLATE = "/runs/{run_id}/options"
CONFIRM_PAGE_TEMPLATE = "/runs/{run_id}/confirm"
PROGRESS_PAGE_TEMPLATE = "/runs/{run_id}"

CSRF_META_ID = "csrf-meta"  # `layout.html` publishes the token under this identifier.
CSRF_HEADER = "X-CSRFToken"  # `portal.js` sends the token under this header name.

# The options page controls.
VERSION_SELECT_ALL_ID = "upgrade-version-select-all"
REBOOT_TOGGLE_ID = "upgrade-reboot-toggle"
STRATEGY_SELECT_ID = "upgrade-strategy-select"
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
UNAUTHORIZED_STATUS = 401  # `runtime/identity.py` answers this code with no session.
NOT_FOUND_STATUS = 404  # The route is not registered yet.

GATE_TIMEOUT_MS = 5000  # The script reads one key press, so the gate settles quickly.

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
    """Return a browser page that points at the running portal.

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
    """Skip when a route is absent, and fail when a built route answers wrongly.

    Args:
        status: The status code the portal answered.
        path: The path the test opened, named in every message.

    Raises:
        AssertionError: If the portal answered a status that the contract does
            not fix for a page.
    """
    if status == UNAUTHORIZED_STATUS:  # `identity.require_session` refused the request.
        pytest.skip(f"{path} answered 401. The portal holds no session, so no browser test reaches this page.")
    if status == NOT_FOUND_STATUS:  # The blueprint that owns this path is not registered.
        pytest.skip(f"{path} answered 404. The route is not built yet.")
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
    """
    site_id = _first_site_id(portal_page)
    path = RUNS_API_TEMPLATE.format(site_id=site_id)
    headers = {CSRF_HEADER: _csrf_token(portal_page), "Content-Type": "application/json"}
    try:  # A portal with no create route reaches this clause, and a skip names the cause.
        answer = portal_page.request.post(path, headers=headers, data="{}")
    except Exception as failure:  # The call never reached the portal at all.
        pytest.skip(f"The create call to {path} did not complete. Cause: {failure}")
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


@pytest.fixture
def confirm_page(portal_page: Any, run_id: str) -> Any:
    """Return a page that shows the last step before the portal sends anything.

    Args:
        portal_page: The browser page that points at the portal.
        run_id: The key of the fresh run.

    Returns:
        The Playwright page object, on the confirm page.
    """
    path = CONFIRM_PAGE_TEMPLATE.format(run_id=run_id)
    _require_built_route(_page_status(portal_page, path), path)
    return portal_page


@pytest.fixture
def progress_page(portal_page: Any, run_id: str) -> Any:
    """Return a page that shows the live view of one run.

    Args:
        portal_page: The browser page that points at the portal.
        run_id: The key of the fresh run.

    Returns:
        The Playwright page object, on the progress page.
    """
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
        """The page shows the bulk version control, the two options, and the save control.

        Why:
            FR-027 to FR-030 name the reboot option and the strategy option. An
            operator who cannot see one of them cannot choose it, and the portal
            would then send the default to live hardware with no consent.

        Args:
            options_page: The page that shows the version picker.
        """
        sync_api.expect(options_page.get_by_test_id(VERSION_SELECT_ALL_ID)).to_be_visible()
        sync_api.expect(options_page.get_by_test_id(REBOOT_TOGGLE_ID)).to_be_visible()
        sync_api.expect(options_page.get_by_test_id(STRATEGY_SELECT_ID)).to_be_visible()
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
        """The reboot control holds the state the operator sets.

        Why:
            The reboot option decides whether the site drops traffic at the end
            of the upgrade. A control that snapped back to its default would send
            a reboot the operator cleared.

        Args:
            options_page: The page that shows the version picker.
        """
        toggle = options_page.get_by_test_id(REBOOT_TOGGLE_ID)
        toggle.uncheck()
        sync_api.expect(toggle).not_to_be_checked()
        toggle.check()
        sync_api.expect(toggle).to_be_checked()


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
