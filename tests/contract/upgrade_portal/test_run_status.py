"""Contract tests for the status poll of one upgrade run.

Why:
    `tests/contract/upgrade_portal/test_upgrade_routes.py` proves that the poll
    answers every field the contract names and that an unknown run is refused.
    It does not prove the shape inside those fields. The browser polls this body
    every 30 seconds and draws a table from it with no server-sent events, so a
    missing key inside a phase entry or a target row breaks the page with no
    server error at all. These tests read the body key by key.

Scope:
    `GET /api/runs/<run_id>/status`. `contracts/http-api.md` section 5 fixes
    every status and every field below.

Fixtures:
    Every fixture lives in this file on purpose. `conftest.py` is shared with
    other test modules, and a run store belongs to these tests alone.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

from collections.abc import Iterator  # The signed-in fixtures yield and then clean up.
from typing import Any  # A run record and a status body are both free-form.

import pytest  # The test framework of the project.
from flask import Flask  # The application type of the portal.
from flask.testing import FlaskClient  # The client type that drives every request.
from werkzeug.test import TestResponse  # The answer type that every assertion reads.

from src.upgrade_portal.runtime import identity  # The real session guard, so the tests sign in for real.
from src.upgrade_portal.runtime.runs import RunRecordBuilder, RunSpec  # The record layer owns every field.

# --------------------------------------------------------------------------
# The contract values. Each one repeats a line of the specification.
# --------------------------------------------------------------------------

RUN_STORE_KEY = "RUN_STORE"  # The seam that holds the run record store.
LOCK_READER_KEY = "SITE_LOCK_READER"  # The seam that reads the site lock, named by `select.py`.

PROBE_EMAIL = "probe.operator@example.invalid"  # A reserved domain, so no real address appears.
ORG_ID = "00000000-0000-0000-0000-0000000000aa"  # Matches the shared organization of the other tests.
SITE_ID = "00000000-0000-0000-0000-0000000000bb"  # Matches the shared site of the other tests.
PROBE_MAC = "5c5b350e0001"  # The device of the shared inventory payload.
PRE_CAPTURE_ID = "cap-probe-pre-check"  # Stands for the saved pre-check of one run.
POST_CAPTURE_ID = "cap-probe-post-check"  # Stands for the saved post-check of the same run.

SELECTED_ORG_SESSION_KEY = "selected_org_id"  # The organization pick inside the signed session.
SELECTED_SITE_SESSION_KEY = "selected_site_id"  # The site pick inside the same signed session.

STATUS_PATH_TEMPLATE = "/api/runs/{run_id}/status"  # The path the browser polls every 30 seconds.
UNKNOWN_RUN_ID = "run-00000000000000000000000000000000"  # A well-shaped key that no store holds.

RUNNING_STATE = "upgrade_running"  # A run in flight, which is the state the page polls most.
SETTLING_STATE = "settling_switches"  # A run in the second cascade phase.
UNKNOWN_STATE = "banana"  # A state name outside the model, which a stale record may hold.

OK_STATUS = 200  # The poll answered.
NOT_AUTHENTICATED_STATUS = 401  # No signed-in session.
METHOD_NOT_ALLOWED_STATUS = 405  # The path accepts a read only.

NOT_AUTHENTICATED_CODE = "not_authenticated"  # `identity.require_session` answers this code.

# WHY: `contracts/http-api.md` section 5 shows exactly these nine keys. The page
# reads each one on every poll, so an extra key would tell a reader that the
# portal promises a field the contract never fixed.
STATUS_FIELDS = {
    "run_id",
    "state",
    "phase_order",
    "phases",
    "targets",
    "stop_request",
    "pre_capture_id",
    "post_capture_id",
    "message",
}

# WHY: `data-model.md` section 4.2 fixes this order, and the page draws the four
# phases in it. A sorted order or a stored order would move the columns.
PHASE_ORDER = ["gateways", "switches", "aps", "clients"]

# WHY: The contract shows a settled phase with a settle time and a waiting phase
# with two counts. Every phase carries all six keys, so the page reads one shape.
# The sixth key names what the gate could not read, and it holds text, never null.
PHASE_FIELDS = {"name", "state", "settled", "total", "settled_at", "note"}

# WHY: The contract shows these seven keys on a target row. A row that dropped a
# key would leave a blank column with no reason a reader could see.
TARGET_FIELDS = {"mac", "name", "device_type", "state", "version_before", "version_target", "version_after"}

# WHY: `data-model.md` section 4.3 fixes these five keys on a stop request.
STOP_REQUEST_FIELDS = {"requested_by", "requested_at", "confirmation_text", "scope", "outcome"}


class RecordingRunStore:
    """Holds every run record of one test in one dictionary.

    Why:
        The routes ask for a `read_run` and a `write_run` pair. This stand-in
        gives both and reaches no database server, so a contract test runs with
        no ArangoDB server and no comma-separated value fallback file.
    """

    def __init__(self) -> None:
        """Start with no run record at all."""
        self.runs: dict[str, dict[str, Any]] = {}  # One entry for each run the test seeds.
        self.reads: list[str] = []  # One entry for each read, so a test can count the polls.

    def read_run(self, run_id: str) -> dict[str, Any] | None:
        """Return one run record, or None when no run holds the identifier.

        Args:
            run_id: The run key.

        Returns:
            A copy of the record, or None.
        """
        self.reads.append(run_id)  # The poll test counts these entries.
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
def upgrade_app(portal_app: Flask, run_store: RecordingRunStore) -> Flask:
    """Return the portal application with the run store injected.

    Args:
        portal_app: The real application from the shared fixture.
        run_store: The stand-in run record store.

    Returns:
        The application with the seams in place.
    """
    portal_app.config[RUN_STORE_KEY] = run_store  # No ArangoDB server runs in a contract test.
    portal_app.config[LOCK_READER_KEY] = lambda org_id, site_ids: {}  # No Redis server runs in a contract test.
    portal_app.config["WTF_CSRF_ENABLED"] = False  # A read carries no token, but the fixture keeps one rule.
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
            browser_session[SELECTED_ORG_SESSION_KEY] = ORG_ID  # The scope of every later read.
            browser_session[SELECTED_SITE_SESSION_KEY] = SITE_ID  # The site the run belongs to.
        yield client  # Every test below drives this client.


@pytest.fixture
def signed_out_client(upgrade_app: Flask) -> Iterator[FlaskClient]:
    """Return a client that never signed in.

    Args:
        upgrade_app: The application with the seams injected.

    Yields:
        The Flask test client, with no session owner at all.
    """
    with upgrade_app.test_client() as client:  # The guard must refuse every request from this client.
        yield client


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def seed_run(store: RecordingRunStore, state: str, **fields: Any) -> str:
    """Write one run record straight into the store and return its key.

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
    record.update(fields)  # The stored phases, targets, and capture keys arrive here.
    store.write_run(record)  # The route reads this record through the seam.
    return str(record["run_id"])  # Every path below carries this key.


def read_status(client: FlaskClient, run_id: str) -> TestResponse:
    """Poll the status of one run.

    Args:
        client: The Flask test client.
        run_id: The run key.

    Returns:
        The portal answer.
    """
    return client.get(STATUS_PATH_TEMPLATE.format(run_id=run_id))


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


def status_body(client: FlaskClient, run_id: str) -> dict[str, Any]:
    """Poll one run and return the status body.

    Args:
        client: The Flask test client.
        run_id: The run key.

    Returns:
        The whole status body.
    """
    body: Any = read_status(client, run_id).get_json()  # Every passing poll answers a JSON record.
    return dict(body)


# ---------------------------------------------------------------------------
# T130: the guard in front of the status path
# ---------------------------------------------------------------------------


def test_the_status_path_refuses_a_write(upgrade_client: FlaskClient, run_store: RecordingRunStore) -> None:
    """A post on the status path answers 405, because the contract names a read only.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, RUNNING_STATE)  # A run that a read could really poll.
    path = STATUS_PATH_TEMPLATE.format(run_id=run_id)
    assert upgrade_client.post(path, json={}).status_code == METHOD_NOT_ALLOWED_STATUS


def test_a_status_read_with_no_session_is_refused(
    signed_out_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """A poll with no signed-in session answers 401 `not_authenticated`.

    Why:
        The status body names every device of a site and the address of the
        operator who started the run. An unsigned poll must read none of it.

    Args:
        signed_out_client: A client that never signed in.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, RUNNING_STATE)  # The run exists, so only the guard can refuse.
    answer = read_status(signed_out_client, run_id)
    assert answer.status_code == NOT_AUTHENTICATED_STATUS  # The guard refused before the handler ran.
    assert read_error_code(answer) == NOT_AUTHENTICATED_CODE  # One code for every unsigned request.


# ---------------------------------------------------------------------------
# T130: the shape of the status body
# ---------------------------------------------------------------------------


def test_the_status_adds_no_key_the_contract_never_named(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """The status body holds the nine contract keys, and no other key.

    Why:
        A reader of the contract looks for these nine keys only. A tenth key
        would become a promise that no contract fixed, and a later removal of
        it would then read as a breaking change.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, RUNNING_STATE)  # A run in flight, which is the state the page polls most.
    assert set(status_body(upgrade_client, run_id)) == STATUS_FIELDS  # Exactly the nine keys of the contract.


def test_the_status_names_the_four_phases_in_the_fixed_order(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """The status body names the four cascade phases in the documented order.

    Why:
        FR-053 settles the families in one order: gateways, then switches, then
        access points, then wireless clients. The page draws the columns in the
        order this field gives, so a sorted order would move every column.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, SETTLING_STATE)  # A run inside the cascade, so every phase matters.
    body = status_body(upgrade_client, run_id)
    assert body["phase_order"] == PHASE_ORDER  # The order of the data model, and never a sorted order.
    assert [entry["name"] for entry in body["phases"]] == PHASE_ORDER  # The entries follow the same order.


def test_the_status_fills_every_phase_the_record_never_wrote(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """A record that stored one phase still answers four phase entries.

    Why:
        The driver writes a phase entry only when that phase starts. The page
        draws four rows from the first poll onward, so the view fills the gap
        instead of leaving the page to guess.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    stored = [{"name": "gateways", "state": "settled", "settled": 2, "total": 2, "settled_at": "2026-08-19T00:00:00Z"}]
    run_id = seed_run(run_store, SETTLING_STATE, phases=stored)  # One stored phase, and three that never started.
    entries = status_body(upgrade_client, run_id)["phases"]
    assert len(entries) == len(PHASE_ORDER)  # Four rows, whatever the record holds.
    assert all(set(entry) == PHASE_FIELDS for entry in entries)  # Every row carries all six keys.
    # A record written before the note existed still answers text. The page prints the value as it stands.
    assert all(entry["note"] == "" for entry in entries)


def test_every_target_row_carries_the_seven_contract_keys(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """A target row that stored one field still answers all seven fields.

    Why:
        The driver fills the version after the upgrade only at the end. The row
        carries the key with a null value from the first poll, so the table
        draws the same columns at every poll.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, RUNNING_STATE, targets=[{"mac": PROBE_MAC}])  # One field only.
    rows = status_body(upgrade_client, run_id)["targets"]
    assert set(rows[0]) == TARGET_FIELDS  # Every contract key is present.
    assert rows[0]["version_after"] is None  # The unfilled key reads as null, and never as absent.


def test_the_status_answers_a_run_that_upgrades_no_device(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """A run with no target answers an empty list and still names four phases.

    Why:
        An operator may open a run before choosing a version. The page must
        draw its frame from the first poll, so an empty target list is a normal
        answer and never a fault.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, RUNNING_STATE, targets=[])  # A run that upgrades nothing yet.
    body = status_body(upgrade_client, run_id)
    assert body["targets"] == []  # An empty list, and never a null value.
    assert len(body["phases"]) == len(PHASE_ORDER)  # The frame of the page still stands.


# ---------------------------------------------------------------------------
# T130: the outcome fields
# ---------------------------------------------------------------------------


def test_the_status_holds_no_stop_request_before_a_stop(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """A run that nobody stopped answers a null stop request.

    Why:
        The page hides the stop panel while this field is null. A field that
        held an empty record instead would show an empty panel on every run.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, RUNNING_STATE)  # A fresh run, which nobody asked to stop.
    assert status_body(upgrade_client, run_id)["stop_request"] is None  # Null, and never an empty record.


def test_the_status_names_the_stop_request_after_one(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """A run with a stored stop request answers all five of its fields.

    Why:
        The stop panel names the operator who asked and the time of the ask.
        FR-047 keeps the first owner of a stop, so the page must be able to
        show that owner on every later poll.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    stored = {
        "requested_by": PROBE_EMAIL,
        "requested_at": "2026-08-19T00:00:00Z",
        "confirmation_text": "STOP",
        "scope": "run",
        "outcome": None,  # The cancels have not reported yet.
    }
    run_id = seed_run(run_store, "stopping", stop_request=stored)  # A run that an operator asked to stop.
    assert set(status_body(upgrade_client, run_id)["stop_request"]) == STOP_REQUEST_FIELDS


def test_the_status_names_both_capture_keys(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """A finished run answers the pre-check key and the post-check key.

    Why:
        FR-060 asks the page to link both captures once the run ends. The page
        builds each link from these two fields alone, so it reads no second
        endpoint to find them.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, "complete", pre_capture_id=PRE_CAPTURE_ID, post_capture_id=POST_CAPTURE_ID)
    body = status_body(upgrade_client, run_id)
    assert body["pre_capture_id"] == PRE_CAPTURE_ID  # The link to the state of the site before the upgrade.
    assert body["post_capture_id"] == POST_CAPTURE_ID  # The link to the state of the site after the upgrade.


# ---------------------------------------------------------------------------
# T130: the poll itself
# ---------------------------------------------------------------------------


def test_two_polls_change_nothing_in_the_run_record(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """The status poll reads the run record and never writes it.

    Why:
        The page polls every 30 seconds for the whole life of a run, which is
        often an hour. A poll that wrote the record would race the run driver
        and could roll a phase back to an earlier count.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, RUNNING_STATE, targets=[{"mac": PROBE_MAC}])  # A run the page would poll.
    before = dict(run_store.runs[run_id])  # The record as the driver last wrote it.
    first = status_body(upgrade_client, run_id)
    assert status_body(upgrade_client, run_id) == first  # The second poll answers the same body.
    assert run_store.runs[run_id] == before  # Neither poll changed one field of the record.


def test_a_poll_reads_the_record_once(upgrade_client: FlaskClient, run_store: RecordingRunStore) -> None:
    """One poll reads the run record exactly once.

    Why:
        A busy site polls one run from several tabs at the same time. Each read
        reaches ArangoDB in production, so a route that read the record twice
        would double the load of every open page for no gain.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, RUNNING_STATE)  # A run in flight, which is the state the page polls most.
    run_store.reads.clear()  # The seeding wrote the record, and this test counts reads only.
    read_status(upgrade_client, run_id)
    assert run_store.reads == [run_id]  # One read for one poll.


def test_a_poll_answers_a_state_outside_the_model_without_a_fault(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """A record that holds an unknown state still answers 200.

    Why:
        A record written by an older build may hold a state name this build
        does not know. A poll that faulted would leave the operator with a
        blank page and no way to read the run at all.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, UNKNOWN_STATE)  # A state name outside the model of this build.
    answer = read_status(upgrade_client, run_id)
    assert answer.status_code == OK_STATUS  # The page still loads.
    body: Any = answer.get_json()
    assert body["state"] == UNKNOWN_STATE  # The poll reports the truth of the record.
    assert body["message"]  # The page still has one sentence to show the operator.
