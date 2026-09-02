"""Contract tests for the upgrade routes of the portal.

Why:
    `contracts/http-api.md` section 5 fixes the path, the status, and the machine
    code of every upgrade call. These tests read that contract and nothing else,
    so a later change of the route body cannot quietly change the answer that the
    browser and the operator depend on.

Scope:
    The new run, the saved options, the guarded start, the status poll, the run
    page, and the guarded stop. Each test injects a stand-in store, a stand-in
    lock reader, and a stand-in launcher, so no test reaches the Mist cloud, an
    ArangoDB server, or a Redis server.

Fixtures:
    Every fixture lives in this file on purpose. `conftest.py` is shared with
    other test modules, and a run store belongs to these tests alone.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

from collections.abc import Iterator  # The signed-in fixtures yield and then clean up.
from typing import Any  # A run record and a request body are both free-form.

import pytest  # The test framework of the project.
from flask import Flask  # The application type of the portal.
from flask.testing import FlaskClient  # The client type that drives every request.
from werkzeug.test import TestResponse  # The answer type that every assertion reads.

from src.upgrade_portal.runtime import identity  # The real session guard, so the tests sign in for real.
from src.upgrade_portal.runtime.runs import RunRecordBuilder, RunSpec  # The record layer owns every field.

RUN_STORE_KEY = "RUN_STORE"  # The seam that holds the run record store.
LOCK_READER_KEY = "SITE_LOCK_READER"  # The seam that reads the site lock, named by `select.py`.
LAUNCHER_KEY = "RUN_LAUNCHER"  # The seam that hands one prepared record to the run driver.
VERSIONS_KEY = "UPGRADE_VERSIONS"  # The seam that answers the version list of each device model.

PROBE_EMAIL = "probe.operator@example.invalid"  # A reserved domain, so no real address appears.
OTHER_EMAIL = "second.operator@example.invalid"  # The operator that holds the lock in the refusal tests.
ORG_ID = "00000000-0000-0000-0000-0000000000aa"  # Matches the shared organization of the other tests.
SITE_ID = "00000000-0000-0000-0000-0000000000bb"  # Matches the shared site of the other tests.

SELECTED_ORG_SESSION_KEY = "selected_org_id"  # The organization pick inside the signed session.
SELECTED_SITE_SESSION_KEY = "selected_site_id"  # The site pick inside the same signed session.

CREATE_PATH = f"/api/sites/{SITE_ID}/runs"  # The path that `contracts/http-api.md` section 5 names.
CREATE_ALT_PATH = "/api/runs"  # The path that `tasks.md` T151 names, which reads the session instead.
VERSIONS_PATH_TEMPLATE = "/api/runs/{run_id}/versions"  # `contracts/http-api.md` section 5 names this path.

BY_MODEL_FIELD = "by_model"  # The one answer field of the version read.
TARGETS_FIELD = "targets"  # The run record field that carries one row for each target device.
PROBE_MODEL = "AP45"  # One access point model, which the version answer groups by.
PROBE_VERSION = "0.14.30075"  # One firmware version of the model above.

# WHY: The start refuses a plan that names no device, so a run that expects a
# 202 carries one row here.
PLANNED_ROW = {"mac": "5c5b350e0001", "version_target": PROBE_VERSION}

OK_STATUS = 200  # The read or the write succeeded.
CREATED_STATUS = 201  # The portal created one run record.
ACCEPTED_STATUS = 202  # The portal took the work and answered before it ended.
BAD_REQUEST_STATUS = 400  # The portal could not read the request.
NOT_AUTHENTICATED_STATUS = 401  # No signed-in session.
NOT_FOUND_STATUS = 404  # No such run.
CONFLICT_STATUS = 409  # The site is held, the pre-check is missing, or the run cannot stop.

# The sentence that `upgrade/confirm.html` prints only while no pre-check exists.
PRE_CHECK_HINT = "The portal needs a saved pre-check capture before an upgrade starts."


class RecordingRunStore:
    """Holds every run record of one test in one dictionary.

    Why:
        `runtime/signals.RunRecordStore` asks for a reader and a writer, and
        `capture/store.py` publishes no reader today. This stand-in gives the
        routes both methods and reaches no database server.
    """

    def __init__(self) -> None:
        """Start with no run record at all."""
        self.runs: dict[str, dict[str, Any]] = {}  # One entry for each run the test seeds or creates.

    def read_run(self, run_id: str) -> dict[str, Any] | None:
        """Return one run record, or None when no run holds the identifier.

        Args:
            run_id: The run key.

        Returns:
            A copy of the record, or None.
        """
        held = self.runs.get(run_id)  # An absent key reads as None, never a fault.
        return dict(held) if held is not None else None  # A copy stops a caller edit of the stored record.

    def write_run(self, run: dict[str, Any]) -> bool:
        """Write one run record and report the true result.

        Args:
            run: The whole record, with the changed fields already in place.

        Returns:
            True, because this stand-in never refuses a write.
        """
        self.runs[str(run["run_id"])] = dict(run)  # A copy stops a later edit of the caller dictionary.
        return True  # The route then answers the operator.


class RecordingLockReader:
    """Answers the site lock read with one canned holder index.

    Why:
        T182 asks the start route to name the operator that holds the site. The
        stand-in supplies that address, so the test reads the refusal body and
        never runs a Redis server.
    """

    def __init__(self, holders: dict[str, str | None] | None = None) -> None:
        """Build the reader with a canned holder index.

        Args:
            holders: The address of the operator that holds each site lock.
        """
        self.holders = holders or {}  # An empty index means that no site has a holder.

    def __call__(self, org_id: str, site_ids: list[str]) -> dict[str, str | None]:
        """Return the holder of each asked site.

        Args:
            org_id: The organization that owns the sites.
            site_ids: The sites to ask about.

        Returns:
            One entry for each site asked about, because `runtime/lock.py`
            answers one entry for each site it can reach. A site the canned
            index does not name reads as a free site, never as an unknown one.
        """
        return {site: self.holders.get(site) for site in site_ids}  # A reachable store names every asked site.


class RecordingLauncher:
    """Records every run record that the start route hands to the driver.

    Why:
        The real driver reads the cloud and writes an upgrade. The test needs to
        know only that the start route reached the seam exactly once.
    """

    def __init__(self) -> None:
        """Start with no launched run at all."""
        self.launched: list[str] = []  # One entry for each run the route handed over.

    def __call__(self, record: dict[str, Any]) -> None:
        """Record the run that the route asked the driver to run.

        Args:
            record: The run record, already in the state `upgrade_submitting`.
        """
        self.launched.append(str(record.get("run_id", "")))  # The test asserts on the count and the key.


class RecordingVersionReader:
    """Records the scope of every version read and answers a canned map.

    Why:
        The real reader calls the Mist cloud. `list_available_versions` of
        `src/firmware/upgrade_service.py` is scoped to one site, and two
        neighbouring cloud calls are scoped to one organization instead. This
        stand-in records the identifier it received, so a test proves which of
        the two scopes the route passes on.
    """

    def __init__(self, answer: Any, fault: bool = False) -> None:
        """Build the reader with a canned answer.

        Args:
            answer: The value the reader gives back to the route.
            fault: True to act out a cloud read that never answers.
        """
        self.answer = answer  # The route turns this value into the contract map.
        self.fault = fault  # A raised fault must never reach the operator as a fault page.
        self.calls: list[tuple[str, Any]] = []  # One entry for each read, with the scope of it.

    def __call__(self, session: Any, site_id: str, devices: Any) -> Any:
        """Record one read and answer it.

        Args:
            session: The cloud session of the signed-in operator.
            site_id: The site that scopes the read.
            devices: The target rows, which name the model of each device.

        Returns:
            The canned answer.

        Raises:
            RuntimeError: While the test asked this reader to act out a fault.
        """
        self.calls.append((site_id, devices))  # The test reads the scope out of this list.
        if self.fault:  # A refused call and a timed-out call both arrive as an exception.
            raise RuntimeError("The cloud did not answer the version read.")
        return self.answer  # A mapping, and every other shape the route must survive.


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def run_store() -> RecordingRunStore:
    """Return a fresh run record store.

    Returns:
        An empty recording store.
    """
    return RecordingRunStore()  # Each test starts with no run at all.


@pytest.fixture
def lock_reader() -> RecordingLockReader:
    """Return a lock reader that reports no holder.

    Returns:
        A reader with an empty holder index.
    """
    return RecordingLockReader()  # A test that needs a holder replaces the index itself.


@pytest.fixture
def launcher() -> RecordingLauncher:
    """Return a stand-in for the run driver.

    Returns:
        A recording launcher with no launched run.
    """
    return RecordingLauncher()  # The start test asserts that the route reached this seam.


@pytest.fixture
def upgrade_app(
    portal_app: Flask,
    run_store: RecordingRunStore,
    lock_reader: RecordingLockReader,
    launcher: RecordingLauncher,
) -> Flask:
    """Return the portal application with the three upgrade seams injected.

    Why:
        The upgrade routes read a run store, a site lock, and a run driver. All
        three sit behind a seam, so a contract test replaces each one and
        reaches no server.

    Args:
        portal_app: The real application from the shared fixture.
        run_store: The stand-in run record store.
        lock_reader: The stand-in site lock read.
        launcher: The stand-in run driver.

    Returns:
        The application with the seams in place.
    """
    portal_app.config[RUN_STORE_KEY] = run_store  # No ArangoDB server runs in a contract test.
    portal_app.config[LOCK_READER_KEY] = lock_reader  # No Redis server runs in a contract test.
    portal_app.config[LAUNCHER_KEY] = launcher  # No upgrade reaches the Mist cloud.
    portal_app.config["WTF_CSRF_ENABLED"] = False  # `test_capture_start.py` already covers the token check.
    return portal_app  # Every test below drives this application.


@pytest.fixture
def registered_owner() -> Iterator[identity.SessionOwner]:
    """Register one operator and drop the record when the test ends.

    Why:
        The guard admits a request only when the signed session and the browser
        cookie both name a registered owner. The registry is a process global,
        so the fixture clears it again.

    Yields:
        The identity pair of the registered operator.
    """
    owner = identity.build_owner(PROBE_EMAIL, identity.issue_browser_id())  # The pair the guard checks.
    record = identity.OperatorSession(
        owner=owner,
        cloud_session=object(),  # A plain object states no scope, so every organization passes.
        credential_mode=identity.CredentialMode.ENVIRONMENT_TOKEN,
    )
    identity.SESSION_REGISTRY.register(record)  # The guard reads the registry on every request.
    try:  # The test body runs with the owner in place.
        yield owner  # Every signed-in test reads this pair.
    finally:  # A leaked record would sign in a later test by accident.
        identity.SESSION_REGISTRY.drop(owner.key)  # The registry outlives the test, so clear it here.


@pytest.fixture
def upgrade_client(upgrade_app: Flask, registered_owner: identity.SessionOwner) -> Iterator[FlaskClient]:
    """Return a signed-in client that already picked the organization and the site.

    Args:
        upgrade_app: The application with the seams injected.
        registered_owner: The identity pair of the registered operator.

    Yields:
        The Flask test client, with the session held open.
    """
    with upgrade_app.test_client() as client:  # The context manager holds the session across requests.
        client.set_cookie(identity.BROWSER_ID_COOKIE, registered_owner.browser_id)  # Half of the guard.
        with client.session_transaction() as browser_session:  # The other half of the guard.
            browser_session[identity.SESSION_OWNER_KEY] = registered_owner.key  # Names the registered owner.
            browser_session[SELECTED_ORG_SESSION_KEY] = ORG_ID  # The picker writes this field.
            browser_session[SELECTED_SITE_SESSION_KEY] = SITE_ID  # The picker writes this field as well.
        yield client  # Every test below drives this client.


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def seed_run(store: RecordingRunStore, state: str, **fields: Any) -> str:
    """Write one run record straight into the store and return its key.

    Why:
        A test of the start route needs a run that already passed the pre-check
        stage. Driving every earlier route first would test those routes twice
        and would hide the rule under test.

    Args:
        store: The stand-in run record store.
        state: The state the seeded run holds.
        **fields: Any further record field the test needs.

    Returns:
        The key of the seeded run.
    """
    spec = RunSpec(ORG_ID, "Probe organization", SITE_ID, "Probe site", PROBE_EMAIL, "browser-probe")
    record = RunRecordBuilder().build(spec)  # The record layer owns every field and every default.
    record["state"] = state  # The test names the stage the run already reached.
    record.update(fields)  # The pre-check identifier and the target list arrive here.
    store.write_run(record)  # The route reads this record through the seam.
    return str(record["run_id"])  # Every path below carries this key.


def read_error_code(response: TestResponse) -> str:
    """Return the `code` field of an error envelope.

    Why:
        `contracts/README.md` states that a test asserts on `code` and never on
        the message text, because the message may change with no contract change.

    Args:
        response: The answer of one refused request.

    Returns:
        The machine code, or an empty string when the body carries none.
    """
    body: Any = response.get_json()  # Every refusal of this portal answers JSON.
    return str(body.get("error", {}).get("code", "")) if isinstance(body, dict) else ""


def read_error_details(response: TestResponse) -> dict[str, Any]:
    """Return the `details` member of an error envelope.

    Args:
        response: The answer of one refused request.

    Returns:
        The details, or an empty dictionary when the body carries none.
    """
    body: Any = response.get_json()  # Every refusal of this portal answers JSON.
    details = body.get("error", {}).get("details", {}) if isinstance(body, dict) else {}
    return details if isinstance(details, dict) else {}  # A damaged body reads as no details at all.


# ---------------------------------------------------------------------------
# T151: the new run and the saved options
# ---------------------------------------------------------------------------


def test_create_run_on_the_contract_path(upgrade_client: FlaskClient) -> None:
    """`POST /api/sites/<site_id>/runs` answers 201 with the run key and the first state.

    Args:
        upgrade_client: The signed-in client.
    """
    answer = upgrade_client.post(CREATE_PATH, json={"tier": 2})  # The path of the contract carries the site.
    assert answer.status_code == CREATED_STATUS  # The contract fixes 201 for a created run.
    body: Any = answer.get_json()  # The two fields the browser reads next.
    assert body["state"] == "created"  # The first state of the run state machine.
    assert body["run_id"].startswith("run-")  # `runtime/runs.py` fixes this key prefix.


def test_create_run_on_the_task_path_reads_the_session_site(upgrade_client: FlaskClient) -> None:
    """`POST /api/runs` answers 201 and takes the site from the signed session.

    Why:
        T151 names this path and carries no site. The handler falls back to the
        pick that the selection page stored, so both documents agree.

    Args:
        upgrade_client: The signed-in client.
    """
    answer = upgrade_client.post(CREATE_ALT_PATH, json={"tier": 2})  # No site in the path at all.
    assert answer.status_code == CREATED_STATUS  # The same answer as the contract path.
    body: Any = answer.get_json()  # The created run carries the site of the session.
    assert body["state"] == "created"  # The first state of the run state machine.


def test_create_run_refuses_a_held_site(upgrade_client: FlaskClient, lock_reader: RecordingLockReader) -> None:
    """A create call on a held site answers 409 `site_locked` and names the holder.

    Args:
        upgrade_client: The signed-in client.
        lock_reader: The stand-in site lock read.
    """
    lock_reader.holders[SITE_ID] = OTHER_EMAIL  # A second operator already acts on this site.
    answer = upgrade_client.post(CREATE_PATH, json={"tier": 2})  # The same call as the passing test.
    assert answer.status_code == CONFLICT_STATUS  # The contract fixes 409 for a held site.
    assert read_error_code(answer) == "site_locked"  # A distinct word, so the browser tells the 409 cases apart.
    assert read_error_details(answer)["actor_email"] == OTHER_EMAIL  # The operator learns whom to ask.


def test_save_options_answers_the_targets_and_the_warnings(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """`POST /api/runs/<id>/options` answers 200 with the saved targets and the warnings.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, "pre_capture_done")  # The stage at which an operator picks a version.
    body = {"targets": [{"mac": "5c5b350e0001", "version_target": "0.14.29216"}], "reboot": True}
    answer = upgrade_client.post(f"/api/runs/{run_id}/options", json=body)  # The save call of the options page.
    assert answer.status_code == OK_STATUS  # The contract fixes 200 for a saved option set.
    saved: Any = answer.get_json()  # The two fields the options page reads back.
    assert saved["targets"][0]["mac"] == "5c5b350e0001"  # The record holds one row for each device.
    assert saved["warnings"] == []  # No inventory read runs, so the answer claims no warning.
    assert run_store.runs[run_id]["options"]["reboot"] is True  # The record holds the four option fields.
    assert run_store.runs[run_id]["warnings"] == []  # Issue #2003: the record itself must hold the warning list.


def test_save_options_refuses_an_unknown_run(upgrade_client: FlaskClient) -> None:
    """A save call for a run that does not exist answers 404 `run_not_found`.

    Args:
        upgrade_client: The signed-in client.
    """
    answer = upgrade_client.post("/api/runs/run-absent/options", json={"targets": []})  # A stale link.
    assert answer.status_code == NOT_FOUND_STATUS  # The contract fixes 404 for every unknown run.
    assert read_error_code(answer) == "run_not_found"  # One code for every run path.


# ---------------------------------------------------------------------------
# T152 and T182: the guarded start
# ---------------------------------------------------------------------------


def test_start_refuses_any_word_but_confirm(upgrade_client: FlaskClient, run_store: RecordingRunStore) -> None:
    """A start call with the wrong text answers 400 `confirmation_required`.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, "awaiting_confirmation", pre_capture_id="capture-1")  # Every other rule passes.
    answer = upgrade_client.post(f"/api/runs/{run_id}/start", json={"confirm": "confirm"})  # The wrong case.
    assert answer.status_code == BAD_REQUEST_STATUS  # The contract fixes 400 for the wrong word.
    assert read_error_code(answer) == "confirmation_required"  # FR-034 names the exact text and the case.


def test_start_refuses_a_run_with_no_pre_capture(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """A start call with no saved pre-check answers 409 `pre_capture_missing`.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, "awaiting_confirmation")  # The record holds no pre-check identifier.
    answer = upgrade_client.post(f"/api/runs/{run_id}/start", json={"confirm": "CONFIRM"})  # The right word.
    assert answer.status_code == CONFLICT_STATUS  # The contract fixes 409 for this refusal.
    assert read_error_code(answer) == "pre_capture_missing"  # FR-035 guards the whole start on this field.


def test_start_refuses_a_held_site_and_names_the_holder(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
    lock_reader: RecordingLockReader,
) -> None:
    """A start call on a held site answers 409 `site_locked` and names the holder.

    Why:
        T182 asks the refusal to name the holder, so the second operator knows
        whom to ask before the two of them act on one site.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
        lock_reader: The stand-in site lock read.
    """
    run_id = seed_run(run_store, "awaiting_confirmation", pre_capture_id="capture-1")  # Every other rule passes.
    lock_reader.holders[SITE_ID] = OTHER_EMAIL  # A second operator already acts on this site.
    answer = upgrade_client.post(f"/api/runs/{run_id}/start", json={"confirm": "CONFIRM"})  # The right word.
    assert answer.status_code == CONFLICT_STATUS  # The same status as `run_not_stoppable`, so the code matters.
    assert read_error_code(answer) == "site_locked"  # A distinct word, so the browser tells the 409 cases apart.
    assert read_error_details(answer)["actor_email"] == OTHER_EMAIL  # The operator learns whom to ask.


def test_start_sends_the_upgrade_after_the_typed_word(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
    launcher: RecordingLauncher,
) -> None:
    """A start call with the exact word answers 202 `upgrade_submitting` and reaches the driver.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
        launcher: The stand-in run driver.
    """
    # Every start rule passes: the saved pre-check, the free site, and one planned device.
    run_id = seed_run(run_store, "awaiting_confirmation", pre_capture_id="capture-1", targets=[PLANNED_ROW])
    answer = upgrade_client.post(f"/api/runs/{run_id}/start", json={"confirm": "CONFIRM"})  # The exact word.
    assert answer.status_code == ACCEPTED_STATUS  # The contract fixes 202, because the work outlives the call.
    assert answer.get_json()["state"] == "upgrade_submitting"  # The contract fixes this state name.
    assert launcher.launched == [run_id]  # The route reached the driver exactly once.


def test_start_twice_sends_one_upgrade_only(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
    launcher: RecordingLauncher,
) -> None:
    """A second start call changes nothing and reports the state the run already holds.

    Why:
        FR-038 accepts one begin action for each run, even when the operator has
        the confirmation page open in two browser tabs.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
        launcher: The stand-in run driver.
    """
    # Every start rule passes: the saved pre-check, the free site, and one planned device.
    run_id = seed_run(run_store, "awaiting_confirmation", pre_capture_id="capture-1", targets=[PLANNED_ROW])
    upgrade_client.post(f"/api/runs/{run_id}/start", json={"confirm": "CONFIRM"})  # The first tab.
    answer = upgrade_client.post(f"/api/runs/{run_id}/start", json={"confirm": "CONFIRM"})  # The second tab.
    assert answer.status_code == ACCEPTED_STATUS  # The second call is not an error, because nothing went wrong.
    assert launcher.launched == [run_id]  # One upgrade only, which is the whole rule of FR-038.


# ---------------------------------------------------------------------------
# T153: the status poll and the run page
# ---------------------------------------------------------------------------


def test_status_answers_every_contract_field(upgrade_client: FlaskClient, run_store: RecordingRunStore) -> None:
    """`GET /api/runs/<id>/status` answers 200 with every field the contract names.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, "settling_switches", pre_capture_id="capture-1")  # A run in mid-cascade.
    answer = upgrade_client.get(f"/api/runs/{run_id}/status")  # The call the browser repeats every 30 seconds.
    assert answer.status_code == OK_STATUS  # The contract fixes 200 for a run that exists.
    body: Any = answer.get_json()  # Every field below appears in `contracts/http-api.md` section 5.
    expected = {"run_id", "state", "phase_order", "phases", "targets", "stop_request", "message"}
    assert expected <= set(body)  # A missing field would break the run page with no browser error.
    assert body["phase_order"] == ["gateways", "switches", "aps", "clients"]  # The fixed cascade order.


def test_status_refuses_an_unknown_run(upgrade_client: FlaskClient) -> None:
    """A poll for a run that does not exist answers 404 `run_not_found`.

    Args:
        upgrade_client: The signed-in client.
    """
    answer = upgrade_client.get("/api/runs/run-absent/status")  # A poll may outlive the run it watches.
    assert answer.status_code == NOT_FOUND_STATUS  # The contract fixes 404 for every unknown run.
    assert read_error_code(answer) == "run_not_found"  # One code for every run path.


def test_run_page_renders_the_live_view(upgrade_client: FlaskClient, run_store: RecordingRunStore) -> None:
    """`GET /runs/<id>` answers 200 with the run page and the stop partial.

    Why:
        `render_page` falls back to the plain layout when a template is absent,
        so the test reads a control identifier of the real page. A fallback would
        answer 200 with none of them.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, "upgrade_running", pre_capture_id="capture-1")  # A run the operator watches.
    answer = upgrade_client.get(f"/runs/{run_id}")  # The page that the browser refreshes every 30 seconds.
    assert answer.status_code == OK_STATUS  # A page read never refuses a run that exists.
    page = answer.get_data(as_text=True)  # The whole rendered page.
    assert run_id in page  # The page names the run it shows.
    assert 'data-testid="upgrade-run-table"' in page  # `progress.html` rendered, and not the fallback layout.
    assert 'data-testid="stop-button"' in page  # The included `stop.html` read the two values the route passed.


def test_run_page_gives_a_recovery_link_for_an_unprepared_run(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """A stalled run tells the operator how to restore the confirmation path."""
    run_id = seed_run(run_store, "created", pre_capture_id="capture-1", targets=[PLANNED_ROW])
    answer = upgrade_client.get(f"/runs/{run_id}")  # The run page must expose the recovery action.
    page = answer.get_data(as_text=True)  # The rendered page that the operator reads.
    assert answer.status_code == OK_STATUS  # A recoverable run still has a readable page.
    assert 'data-testid="upgrade-recovery-options-link"' in page  # The page names the recovery control.
    assert f'href="/runs/{run_id}/options"' in page  # The control opens the correct saved plan.


def test_options_page_renders_the_version_picker(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """`GET /runs/<id>/options` answers 200 with the version picker.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, "pre_capture_done", targets=[{"mac": "5c5b350e0001", "model": "AP45"}])
    answer = upgrade_client.get(f"/runs/{run_id}/options")  # The page that picks a version for each device.
    assert answer.status_code == OK_STATUS  # A page read never refuses a run that exists.
    assert 'data-testid="upgrade-target-table"' in answer.get_data(as_text=True)  # The real template rendered.


def test_confirm_page_locks_the_start_without_a_pre_check(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """`GET /runs/<id>/confirm` answers 200 and keeps the start control locked.

    Why:
        FR-035 forbids a start with no verified pre-check. The template defaults
        the flag to false, so this test proves the route agrees with it.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, "pre_capture_done")  # The record holds no pre-check identifier.
    answer = upgrade_client.get(f"/runs/{run_id}/confirm")  # The last page before the portal sends anything.
    assert answer.status_code == OK_STATUS  # A page read never refuses a run that exists.
    page = answer.get_data(as_text=True)  # The whole rendered page.
    assert 'data-testid="upgrade-start-button"' in page  # The real template rendered, and not the fallback.
    assert PRE_CHECK_HINT in page  # The page tells the operator why the start control stays locked.
    ready_id = seed_run(run_store, "pre_capture_done", pre_capture_id="capture-1")  # A run with a saved pre-check.
    ready_page = upgrade_client.get(f"/runs/{ready_id}/confirm").get_data(as_text=True)  # The same page, unlocked.
    assert PRE_CHECK_HINT not in ready_page  # A saved pre-check clears the hint, so the route reads the record.


def test_confirm_page_shows_the_warning_list_the_options_call_saved(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """`GET /runs/<id>/confirm` shows the same warning list the options save stored.

    Why:
        Issue #2003: the options page shows a plan warning after a save, but the
        operator can move straight to the confirm page without reading it. The
        confirm page is the last page before firmware moves, so it must repeat
        the same warning list, and never the empty-list fallback text.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    warning_text = "3 access points always reboot with this build, no matter the reboot choice."
    run_id = seed_run(run_store, "pre_capture_done", warnings=[warning_text])  # Mirrors a saved options call.
    page = upgrade_client.get(f"/runs/{run_id}/confirm").get_data(as_text=True)  # The last page before the upgrade.
    assert warning_text in page  # The confirm page must repeat the saved warning list.
    assert "The plan found no warning." not in page  # The empty-list fallback text must not show beside it.


def test_confirm_page_names_every_advanced_control_that_the_run_submits(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """`GET /runs/<id>/confirm` names each advanced control that the operator set.

    Why:
        Issue #2156 asks the confirmation page to show the exact submitted
        fields. This is the last page before firmware moves, so an operator who
        cannot read the phase list or the force flag confirms a plan they never
        reviewed.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    stored = {
        "reboot": True,
        "strategy": "canary",
        "force": True,
        "stable_version": True,
        "canary": {"canary_phases": [25, 50, 100], "max_failures": None, "max_failure_percentage": 12},
        "peer_to_peer": {"enable_p2p": True, "p2p_cluster_size": 12, "p2p_parallelism": None},
    }
    run_id = seed_run(run_store, "pre_capture_done", options=stored)
    page = upgrade_client.get(f"/runs/{run_id}/confirm").get_data(as_text=True)
    assert "25,50,100" in page  # The phase list reaches the page as the operator wrote it.
    assert "12" in page  # The failure percentage and the download group both reach the page.
    assert 'data-testid="upgrade-summary-force"' in page  # The force row always shows its own answer.
    assert "vendor stable build" in page  # The stable choice overrides every picked version.


def test_confirm_page_names_no_advanced_control_that_keeps_the_cloud_default(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """The advanced summary hides a control that the operator never set.

    Why:
        A page of eleven "cloud default" rows hides the one row that the
        operator changed. The summary therefore lists the changed controls
        alone, and one note states the rule for the rest.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, "pre_capture_done", options={"reboot": True, "strategy": "big_bang"})
    page = upgrade_client.get(f"/runs/{run_id}/confirm").get_data(as_text=True)
    assert 'data-testid="upgrade-advanced-summary"' in page  # The card renders for every run.
    assert 'data-testid="upgrade-summary-canary-phases"' not in page  # An untouched control draws no row.
    assert "keeps the cloud default" in page  # One note states the rule for every hidden control.


def test_confirm_page_reports_the_release_train_and_the_schedule(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """`GET /runs/<id>/confirm` names the router train and both schedule moments.

    Why:
        Issue #2157 asks the confirmation page to report the channel and the
        download and reboot schedule. This is the last page before firmware
        moves. An operator who cannot read the release train may send a router
        onto an alpha build and drop the wide area network of the site.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    stored = {
        "reboot": True,
        "strategy": "serial",
        "ssr": {"channel": "beta"},
        "schedule": {"start_time_after": 3600, "reboot_at_after": 28800},
    }
    run_id = seed_run(run_store, "pre_capture_done", options=stored)
    page = upgrade_client.get(f"/runs/{run_id}/confirm").get_data(as_text=True)
    assert "beta" in page  # The release train reaches the last page before the firmware moves.
    assert "1h" in page  # The download duration reads back in the unit that fits it.
    assert "8h" in page  # The reboot duration reads back the same way.
    assert "if you start now" in page  # Each duration carries the moment that it names.
    assert "Release train" in page  # The row carries a label that an operator reads.


def test_confirm_page_names_no_release_train_when_the_run_holds_no_router(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """A run that picked no train draws no train row at all.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, "pre_capture_done", options={"reboot": True, "strategy": "big_bang"})
    page = upgrade_client.get(f"/runs/{run_id}/confirm").get_data(as_text=True)
    assert 'data-testid="upgrade-summary-channel"' not in page  # An untouched control draws no row.


# ---------------------------------------------------------------------------
# T154: the guarded stop
# ---------------------------------------------------------------------------


def test_stop_refuses_any_word_but_stop(upgrade_client: FlaskClient, run_store: RecordingRunStore) -> None:
    """A stop call with the wrong text answers 400 `confirmation_required`.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, "upgrade_running", pre_capture_id="capture-1")  # A run that a stop can change.
    answer = upgrade_client.post(f"/api/runs/{run_id}/stop", json={"confirm": "stop"})  # The wrong case.
    assert answer.status_code == BAD_REQUEST_STATUS  # The contract fixes 400 for the wrong word.
    assert read_error_code(answer) == "confirmation_required"  # FR-038b names the exact text and the case.
    assert run_store.runs[run_id]["state"] == "upgrade_running"  # The refused call left the run untouched.


def test_stop_refuses_a_run_that_already_finished(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """A stop call on a final run answers 409 `run_not_stoppable`.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, "complete", pre_capture_id="capture-1")  # A run that a stop cannot change.
    answer = upgrade_client.post(f"/api/runs/{run_id}/stop", json={"confirm": "STOP"})  # The exact word.
    assert answer.status_code == CONFLICT_STATUS  # The same status as `site_locked`, so the code matters.
    assert read_error_code(answer) == "run_not_stoppable"  # A distinct word, so the browser tells the cases apart.


def test_stop_refuses_an_unknown_run(upgrade_client: FlaskClient) -> None:
    """A stop call for a run that does not exist answers 404 `run_not_found`.

    Args:
        upgrade_client: The signed-in client.
    """
    answer = upgrade_client.post("/api/runs/run-absent/stop", json={"confirm": "STOP"})  # A stale link.
    assert answer.status_code == NOT_FOUND_STATUS  # The contract fixes 404 for every unknown run.
    assert read_error_code(answer) == "run_not_found"  # One code for every run path.


def test_stop_records_the_request_and_moves_the_run(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """A stop call with the exact word answers 200 `stopping` with an outcome.

    Why:
        FR-038f forbids a claim of a cancel that never happened, so the outcome
        of an unwired cancel names no cancelled device at all.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, "upgrade_running", pre_capture_id="capture-1")  # A run a stop can change.
    answer = upgrade_client.post(f"/api/runs/{run_id}/stop", json={"confirm": "STOP"})  # The exact word.
    assert answer.status_code == OK_STATUS  # The contract fixes 200 for a recorded stop.
    body: Any = answer.get_json()  # The two fields the run page reads next.
    assert body["state"] == "stopping"  # The contract fixes this state name.
    assert body["outcome"]["cancelled"] == []  # No cancel call went out, so the answer claims none.
    assert run_store.runs[run_id]["stop_request"]["requested_by"] == PROBE_EMAIL  # FR-038h names the owner.


# ---------------------------------------------------------------------------
# The version list of each model
# ---------------------------------------------------------------------------


def read_versions(client: FlaskClient, run_id: str) -> TestResponse:
    """Ask the portal for the version list of each model of one run.

    Args:
        client: The Flask test client.
        run_id: The run key.

    Returns:
        The portal answer.
    """
    return client.get(VERSIONS_PATH_TEMPLATE.format(run_id=run_id))  # A read, so the path takes no token.


def test_the_version_read_refuses_an_unknown_run(upgrade_client: FlaskClient) -> None:
    """A version read for a run that does not exist answers 404 `run_not_found`.

    Args:
        upgrade_client: The signed-in client.
    """
    answer = read_versions(upgrade_client, "run-absent")  # A stale link, and a hand-typed path.
    assert answer.status_code == NOT_FOUND_STATUS  # The contract fixes 404 for every unknown run.
    assert read_error_code(answer) == "run_not_found"  # One code for every run path of the portal.


def test_the_version_read_answers_one_list_for_each_model(
    upgrade_app: Flask,
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """`GET /api/runs/<run_id>/versions` answers 200 with the `by_model` map.

    Why:
        `contracts/http-api.md` section 5 fixes this one field. The options page
        refills its version picker from this path, so a changed field name would
        leave the operator with an empty picker and no fault at all.

    Args:
        upgrade_app: The application, so the test can inject the version seam.
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    upgrade_app.config[VERSIONS_KEY] = {PROBE_MODEL: (PROBE_VERSION,)}  # A ready map, which needs no cloud.
    run_id = seed_run(run_store, "created")
    answer = read_versions(upgrade_client, run_id)
    assert answer.status_code == OK_STATUS  # The contract fixes 200 for a run that exists.
    body: Any = answer.get_json()  # The one field that the picker reads.
    assert body[BY_MODEL_FIELD] == {PROBE_MODEL: [PROBE_VERSION]}  # A tuple arrives as a list of text.


def test_the_version_read_is_scoped_to_the_site_of_the_run(
    upgrade_app: Flask,
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """The route passes the site of the run, and never the organization.

    Why:
        `list_available_versions` of `src/firmware/upgrade_service.py` reads one
        site. Two neighbouring cloud calls read one organization instead. An
        organization identifier in this call would name firmware for hardware
        that the run never touches.

    Args:
        upgrade_app: The application, so the test can inject the version seam.
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    reader = RecordingVersionReader({PROBE_MODEL: [PROBE_VERSION]})  # Records the scope of the one read below.
    upgrade_app.config[VERSIONS_KEY] = reader
    rows = [{"mac": "5c5b350e0001", "model": PROBE_MODEL}]  # One target row, which names the model.
    run_id = seed_run(run_store, "created", **{TARGETS_FIELD: rows})
    answer = read_versions(upgrade_client, run_id)
    assert answer.status_code == OK_STATUS  # The reader answered, so the route answers too.
    assert reader.calls == [(SITE_ID, rows)]  # One read, scoped to the site, with the target rows of the run.
    assert reader.calls[0][0] != ORG_ID  # The trap of this read, stated as its own assertion.


def test_a_version_read_that_fails_answers_an_empty_map(
    upgrade_app: Flask,
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """A cloud read that raises answers 200 with an empty map, and no fault page.

    Why:
        The version list is a convenience of the options page. A picker with no
        version lets the operator retry the page and keeps every earlier choice.
        A fault page would end the run preparation over a read that may pass on
        the next click.

    Args:
        upgrade_app: The application, so the test can inject the version seam.
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    upgrade_app.config[VERSIONS_KEY] = RecordingVersionReader(None, fault=True)  # The cloud never answers.
    run_id = seed_run(run_store, "created")
    answer = read_versions(upgrade_client, run_id)
    assert answer.status_code == OK_STATUS  # The operator meets a page, and never a fault.
    body: Any = answer.get_json()
    assert body[BY_MODEL_FIELD] == {}  # The portal names no version it cannot prove.


def test_a_version_read_with_no_session_is_refused(run_store: RecordingRunStore, upgrade_app: Flask) -> None:
    """A version read without a signed-in session answers 401 `not_authenticated`.

    Why:
        The read reaches the Mist cloud with the session of the operator. An
        unsigned request must stop at the guard, and never at the cloud.

    Args:
        run_store: The stand-in run record store.
        upgrade_app: The application with the seams injected.
    """
    run_id = seed_run(run_store, "created")  # The run exists, so only the guard can refuse the read.
    with upgrade_app.test_client() as client:  # This client never signed in at all.
        answer = read_versions(client, run_id)
    assert answer.status_code == NOT_AUTHENTICATED_STATUS  # The guard refuses before the handler runs.
    assert read_error_code(answer) == "not_authenticated"  # One code for every unsigned request.


# ---------------------------------------------------------------------------
# Issue #2194: the confirmation page names every warning of the plan
# ---------------------------------------------------------------------------


def seed_mixed_run(run_store: RecordingRunStore) -> str:
    """Seed a run that triggers three warnings of the plan.

    Why:
        The selection holds two versions, a radio strategy that reaches an
        access point alone, and six access points that reboot on their own.

    Args:
        run_store: The stand-in run record store.

    Returns:
        The run identifier.
    """
    targets = [
        {
            "mac": "209339051780",
            "name": "sw",
            "device_type": "switch",
            "model": "EX4100-F-12P",
            "version_before": "25.4R1",
            "version_target": "25.4R2",
            "gateway_family": None,
            "scope": "site",
        }
    ]
    targets += [
        {
            "mac": f"7cb68d9269{index:02d}",
            "name": f"ap{index}",
            "device_type": "ap",
            "model": "AP37",
            "version_before": "0.15.1",
            "version_target": "0.15.2",
            "gateway_family": None,
            "scope": "site",
        }
        for index in range(6)
    ]
    options = {"strategy": "rrm", "reboot": True, "schedule": {"start_time_after": 7200}}
    return seed_run(run_store, "pre_capture_done", targets=targets, options=options)


def test_the_confirm_page_names_the_reboot_of_each_access_point(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """An operator plans a window from the reboot control, and an access point ignores it.

    Why:
        Issue #2003 reported that the no-reboot choice never reaches an access
        point and the page never says so. Issue #2194 found that the sentence
        exists and never reached this page.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_mixed_run(run_store)
    page = upgrade_client.get(f"/runs/{run_id}/confirm").get_data(as_text=True)
    assert "reboots each of the 6 access point" in page  # The count names the devices to plan for.


def test_the_confirm_page_names_the_strategy_that_the_run_drops(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """The radio strategy reaches an access point alone.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_mixed_run(run_store)
    page = upgrade_client.get(f"/runs/{run_id}/confirm").get_data(as_text=True)
    assert "radio strategy reaches an access point only" in page


def test_the_confirm_page_names_the_count_of_cloud_calls(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """One selection can send several calls, and the page named one plan.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_mixed_run(run_store)
    page = upgrade_client.get(f"/runs/{run_id}/confirm").get_data(as_text=True)
    assert 'data-testid="upgrade-summary-call-count"' in page  # The row renders.
    assert "one call for each device type" in page  # The note names the reason for the split.


def test_the_confirm_page_keeps_the_saved_warning_list(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """The plan warnings join the saved list, and they replace none of it.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    saved = "One device already runs the version that you chose. The portal still sends the upgrade."
    run_id = seed_run(run_store, "pre_capture_done", warnings=[saved])
    page = upgrade_client.get(f"/runs/{run_id}/confirm").get_data(as_text=True)
    assert saved in page  # The sentence of the option save still shows.
