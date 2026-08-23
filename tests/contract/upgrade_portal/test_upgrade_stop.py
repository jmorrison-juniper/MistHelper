"""Contract tests for the stop control of one upgrade run.

Why:
    `tests/contract/upgrade_portal/test_upgrade_routes.py` proves the happy stop
    and three refusals. It does not prove the shape of the outcome record, nor
    the order of the checks, nor that a second stop keeps the first owner. The
    stop is the one control an operator reaches while an upgrade writes firmware
    to live hardware, so every one of those rules needs its own test.

Scope:
    `POST /api/runs/<run_id>/stop`. FR-038a to FR-038i and
    `contracts/http-api.md` section 5 fix every status and every field below.

Fixtures:
    Every fixture lives in this file on purpose. `conftest.py` is shared with
    other test modules, and a run store belongs to these tests alone.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

from collections.abc import Iterator  # The signed-in fixtures yield and then clean up.
from typing import Any  # A run record and a stop body are both free-form.

import pytest  # The test framework of the project.
from flask import Flask  # The application type of the portal.
from flask.testing import FlaskClient  # The client type that drives every request.
from werkzeug.test import TestResponse  # The answer type that every assertion reads.

from src.upgrade_portal.runtime import identity  # The real session guard, so the tests sign in for real.
from src.upgrade_portal.runtime.runs import RunRecordBuilder, RunSpec  # The record layer owns every field.
from src.upgrade_portal.runtime.signals import StopOutcome  # The shape the cancel work must answer.

# --------------------------------------------------------------------------
# The contract values. Each one repeats a line of the specification.
# --------------------------------------------------------------------------

RUN_STORE_KEY = "RUN_STORE"  # The seam that holds the run record store.
LOCK_READER_KEY = "SITE_LOCK_READER"  # The seam that reads the site lock, named by `select.py`.
STOP_RUNNER_KEY = "STOP_RUNNER"  # The seam that performs the cancel work of one stop.

PROBE_EMAIL = "probe.operator@example.invalid"  # A reserved domain, so no real address appears.
FIRST_OWNER_EMAIL = "first.operator@example.invalid"  # The operator who asked for the earlier stop.
ORG_ID = "00000000-0000-0000-0000-0000000000aa"  # Matches the shared organization of the other tests.
SITE_ID = "00000000-0000-0000-0000-0000000000bb"  # Matches the shared site of the other tests.
CANCELLED_MAC = "5c5b350e0001"  # A device the cancel work reached before it started.
WRITING_MAC = "5c5b350e0002"  # A device in mid-flash, which FR-038d never interrupts.

SELECTED_ORG_SESSION_KEY = "selected_org_id"  # The organization pick inside the signed session.
SELECTED_SITE_SESSION_KEY = "selected_site_id"  # The site pick inside the same signed session.

STOP_PATH_TEMPLATE = "/api/runs/{run_id}/stop"  # The one stop action of a run.
UNKNOWN_RUN_ID = "run-00000000000000000000000000000000"  # A well-shaped key that no store holds.

CONFIRM_FIELD = "confirm"  # The body field that carries the typed word.
STOP_WORD = "STOP"  # FR-038b fixes this exact text and this exact letter case.
RUNNING_STATE = "upgrade_running"  # A run in flight, which is the only state a stop reaches.
STOPPING_STATE = "stopping"  # The state the contract answers after a stop.
FINAL_STATES = ("complete", "stopped", "failed")  # `TERMINAL_RUN_STATES` of `runtime/signals.py`.

OK_STATUS = 200  # The stop was recorded.
BAD_REQUEST_STATUS = 400  # The portal could not read the request.
NOT_AUTHENTICATED_STATUS = 401  # No signed-in session.
NOT_FOUND_STATUS = 404  # No run holds the key of the path.
METHOD_NOT_ALLOWED_STATUS = 405  # The path accepts a write only.
CONFLICT_STATUS = 409  # The run already reached a state that a stop cannot change.
SERVER_ERROR_STATUS = 500  # The store itself refused the write.

NOT_AUTHENTICATED_CODE = "not_authenticated"  # `identity.require_session` answers this code.
CSRF_MISSING_CODE = "csrf_missing"  # `security.py` answers this code when a post carries no token.
CONFIRMATION_REQUIRED_CODE = "confirmation_required"  # The operator typed the wrong word.
RUN_NOT_FOUND_CODE = "run_not_found"  # The one code that every run path answers for an absent run.
RUN_NOT_STOPPABLE_CODE = "run_not_stoppable"  # The run already reached a final state.
SITE_LOCKED_CODE = "site_locked"  # The other 409 of this portal, which must stay a different word.
STORE_FAILED_CODE = "stop_request_failed"  # The base code of `StopRequestError`.

# WHY: `contracts/http-api.md` section 5 shows these two keys only. The stop
# panel reads both, and a third key would promise a field no contract fixed.
STOP_ANSWER_FIELDS = {"state", "outcome"}

# WHY: FR-038e splits the devices three ways and adds one plain sentence. The
# panel draws one list for each key, so every key must arrive on every stop.
OUTCOME_FIELDS = {"cancelled", "already_writing", "no_cancel_available", "message"}

# WHY: FR-038b names the exact text and the exact letter case. Each entry below
# is a word an operator may really type, and every one of them must be refused.
NEAR_MISS_WORDS = ("stop", "Stop", " STOP ", "STOP!", "CONFIRM", "")


class RecordingRunStore:
    """Holds every run record of one test in one dictionary.

    Why:
        The routes ask for a `read_run` and a `write_run` pair. This stand-in
        gives both and reaches no database server, so a contract test runs with
        no ArangoDB server and no comma-separated value fallback file.
    """

    def __init__(self) -> None:
        """Start with no run record and with writes allowed."""
        self.runs: dict[str, dict[str, Any]] = {}  # One entry for each run the test seeds.
        self.refuse_writes = False  # A test raises this flag to act out a dead store.

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
            True, or False while the test holds the refusal flag.
        """
        if self.refuse_writes:  # The store is unreachable, so the record keeps its earlier content.
            return False  # The caller answers the write failure to the operator.
        self.runs[str(run["run_id"])] = dict(run)  # A copy stops a later edit of the caller dictionary.
        return True  # The record is readable from this moment.


class RecordingStopRunner:
    """Answers one fixed result for the cancel work of a stop.

    Why:
        The cancel work reaches the cloud in production. This stand-in lets a
        test fix the three device lists and then read them back out of the
        answer, which proves that the route repeats the work and invents none.
    """

    def __init__(self, answer: Any) -> None:
        """Hold the answer this runner gives.

        Args:
            answer: The value the route receives, of any type.
        """
        self.answer = answer  # A `StopOutcome`, or a value of the wrong shape.
        self.calls: list[str] = []  # One entry for each stop that reached the cancel work.

    def __call__(self, run_id: str) -> Any:
        """Return the fixed answer and record the call.

        Args:
            run_id: The run key.

        Returns:
            The held answer.
        """
        self.calls.append(run_id)  # A test counts these entries.
        return self.answer


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

    Why:
        The `STOP_RUNNER` seam stays empty. The shared `portal_app` fixture
        empties the seam that `wiring.install_seams` fills. FR-038f forbids a
        claim of a cancel that never happened, so the tests must be able to
        drive the portal with no cancel work wired at all.

    Args:
        portal_app: The real application from the shared fixture.
        run_store: The stand-in run record store.

    Returns:
        The application with the seams in place.
    """
    portal_app.config[RUN_STORE_KEY] = run_store  # No ArangoDB server runs in a contract test.
    portal_app.config[LOCK_READER_KEY] = lambda org, sites: dict.fromkeys(sites)  # Every site reads free.
    portal_app.config["WTF_CSRF_ENABLED"] = False  # One test drives the untouched portal to prove the check.
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


def sign_in_client(client: FlaskClient, owner: identity.SessionOwner) -> None:
    """Write the cookie and the session values that the guard reads.

    Args:
        client: The Flask test client.
        owner: The identity pair of the registered operator.
    """
    client.set_cookie(identity.BROWSER_ID_COOKIE, owner.browser_id)  # Half of the guard.
    with client.session_transaction() as browser_session:  # The other half of the guard.
        browser_session[identity.SESSION_OWNER_KEY] = owner.key  # Names the registered owner.
        browser_session[SELECTED_ORG_SESSION_KEY] = ORG_ID  # The scope of every later read.
        browser_session[SELECTED_SITE_SESSION_KEY] = SITE_ID  # The site the run belongs to.


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
        sign_in_client(client, registered_owner)
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
    record.update(fields)  # A seeded stop request arrives here.
    store.write_run(record)  # The route reads this record through the seam.
    return str(record["run_id"])  # Every path below carries this key.


def stop_run(client: FlaskClient, run_id: str, word: str | None) -> TestResponse:
    """Ask the portal to stop one run.

    Args:
        client: The Flask test client.
        run_id: The run key.
        word: The typed word, or None for a body that carries no confirm field.

    Returns:
        The portal answer.
    """
    body: dict[str, Any] = {} if word is None else {CONFIRM_FIELD: word}
    return client.post(STOP_PATH_TEMPLATE.format(run_id=run_id), json=body)


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

    Why:
        `contracts/http-api.md` section 3 carries the address of a lock holder in
        `details.actor_email` and nowhere else. A test of FR-038i must read that
        address, so the code alone is not enough.

    Args:
        response: The answer of one refused request.

    Returns:
        The details, or an empty dictionary when the body carries none.
    """
    body: Any = response.get_json()  # Every refusal of this portal answers JSON.
    details = body.get("error", {}).get("details", {}) if isinstance(body, dict) else {}
    return details if isinstance(details, dict) else {}  # A damaged body reads as no details at all.


def hold_the_site(app: Flask, address: str) -> None:
    """Name one operator as the holder of the site lock of every run below.

    Why:
        The `upgrade_app` fixture injects a reader that names no holder, and that
        reader is a plain function with no state. A test of FR-038i replaces the
        whole seam, because it needs a held site and no Redis server.

    Args:
        app: The application that holds the lock reader seam.
        address: The address of the operator that holds the site.
    """
    held = {SITE_ID: address}  # One run acts on one site, so the route asks about one site only.
    app.config[LOCK_READER_KEY] = lambda org_id, site_ids: held  # No Redis server runs in a contract test.


def seeded_stop_request(address: str) -> dict[str, Any]:
    """Build the stop request record of an earlier operator.

    Args:
        address: The address of the operator who asked first.

    Returns:
        The `stop_request` member of a run record.
    """
    return {
        "requested_by": address,  # FR-047 keeps this owner through every later click.
        "requested_at": "2026-08-19T00:00:00Z",  # A fixed time, so a test can compare it.
        "confirmation_text": STOP_WORD,  # Proof that the first operator typed the word.
        "scope": "run",  # The whole run, which is the only scope of the first release.
        "outcome": None,  # The cancels had not reported when the record was written.
    }


# ---------------------------------------------------------------------------
# T131: the guard in front of the stop path
# ---------------------------------------------------------------------------


def test_the_stop_path_refuses_a_read(upgrade_client: FlaskClient, run_store: RecordingRunStore) -> None:
    """A read of the stop path answers 405, because a stop changes a live run.

    Why:
        A stop must never ride on a link or on a page load. A read that stopped
        a run would let a browser prefetch end an upgrade of a whole site.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, RUNNING_STATE)  # A run that a stop could really reach.
    path = STOP_PATH_TEMPLATE.format(run_id=run_id)
    assert upgrade_client.get(path).status_code == METHOD_NOT_ALLOWED_STATUS


def test_a_stop_with_no_session_is_refused(
    signed_out_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """A stop with no signed-in session answers 401 `not_authenticated`.

    Args:
        signed_out_client: A client that never signed in.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, RUNNING_STATE)  # The run exists, so only the guard can refuse.
    answer = stop_run(signed_out_client, run_id, STOP_WORD)
    assert answer.status_code == NOT_AUTHENTICATED_STATUS  # The guard refused before the handler ran.
    assert read_error_code(answer) == NOT_AUTHENTICATED_CODE  # One code for every unsigned request.
    assert run_store.runs[run_id].get("stop_request") is None  # No refused request reached the record.


def test_a_stop_with_no_token_is_refused(portal_app: Flask, registered_owner: identity.SessionOwner) -> None:
    """A stop post with no token answers 400 `csrf_missing`.

    Why:
        `security.py` registers the token check for every post, and `TESTING`
        does not switch it off. This test runs against the untouched portal, so
        it proves that the one path that ends an upgrade sits behind the check.

    Args:
        portal_app: The portal application, with the token check still on.
        registered_owner: The identity pair of the registered operator.
    """
    with portal_app.test_client() as client:  # This application never saw the fixture that clears the check.
        sign_in_client(client, registered_owner)
        answer = stop_run(client, UNKNOWN_RUN_ID, STOP_WORD)
    assert answer.status_code == BAD_REQUEST_STATUS  # The check refuses before the handler runs.
    assert read_error_code(answer) == CSRF_MISSING_CODE  # The browser reads this code and fetches a token.


# ---------------------------------------------------------------------------
# T131: the typed word
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("word", NEAR_MISS_WORDS)
def test_a_stop_refuses_every_near_miss_of_the_word(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
    word: str,
) -> None:
    """Only the exact text `STOP` stops a run.

    Why:
        FR-038b names the letter case, so the check trims nothing and changes no
        letter. The word of the start control must not stop a run either, so
        `CONFIRM` sits in this list beside the case and spacing near misses.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
        word: The near miss under test.
    """
    run_id = seed_run(run_store, RUNNING_STATE)  # A run a correct word would really stop.
    answer = stop_run(upgrade_client, run_id, word)
    assert answer.status_code == BAD_REQUEST_STATUS  # The portal refused before it recorded anything.
    assert read_error_code(answer) == CONFIRMATION_REQUIRED_CODE  # The panel shows the word again.


def test_a_stop_with_no_confirm_field_is_refused(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """A stop body with no confirm field at all answers 400 `confirmation_required`.

    Why:
        A script that posts an empty body must meet the same guard as an
        operator who types the wrong word. An absent field is not a special case.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, RUNNING_STATE)  # A run a correct word would really stop.
    answer = stop_run(upgrade_client, run_id, None)  # A body with no confirm field.
    assert answer.status_code == BAD_REQUEST_STATUS
    assert read_error_code(answer) == CONFIRMATION_REQUIRED_CODE  # The same code as a wrong word.


def test_the_wrong_word_is_refused_before_the_unknown_run(upgrade_client: FlaskClient) -> None:
    """A wrong word on an unknown run answers the word refusal, not the run refusal.

    Why:
        The word check runs before the store read. A caller who guesses run keys
        therefore learns nothing about which keys exist while the word is wrong.

    Args:
        upgrade_client: The signed-in client.
    """
    answer = stop_run(upgrade_client, UNKNOWN_RUN_ID, "stop")  # Wrong case, and a run nobody holds.
    assert answer.status_code == BAD_REQUEST_STATUS  # The word check answered first.
    assert read_error_code(answer) == CONFIRMATION_REQUIRED_CODE  # No hint about the missing run.


def test_a_refused_stop_writes_no_request_into_the_record(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """A refused stop leaves the run record exactly as it was.

    Why:
        The run driver reads `stop_request` from the record. A refused click
        that still wrote the field would stop the upgrade the operator kept.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, RUNNING_STATE)  # A run in flight.
    before = dict(run_store.runs[run_id])  # The record before the refused click.
    stop_run(upgrade_client, run_id, "Stop")  # The wrong letter case.
    assert run_store.runs[run_id] == before  # Not one field moved.


# ---------------------------------------------------------------------------
# T131: the state of the run
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("state", FINAL_STATES)
def test_every_final_state_refuses_a_stop_with_the_same_code(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
    state: str,
) -> None:
    """A run in any final state answers 409 `run_not_stoppable`.

    Why:
        The portal answers 409 for a held site as well. The two carry different
        codes on purpose, so the panel can tell the operator to wait for another
        operator, or tell the operator that the run already ended.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
        state: The final state under test.
    """
    run_id = seed_run(run_store, state)  # A run that already ended.
    answer = stop_run(upgrade_client, run_id, STOP_WORD)
    assert answer.status_code == CONFLICT_STATUS
    assert read_error_code(answer) == RUN_NOT_STOPPABLE_CODE  # Never the code of a held site.
    assert read_error_code(answer) != SITE_LOCKED_CODE  # The two 409 answers stay two different words.


def test_a_second_stop_keeps_the_first_owner(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """A stop of a run that already holds a request keeps the earlier owner.

    Why:
        FR-047 gives one stop one owner. A second click from a second operator
        must not rewrite the record of who ended the upgrade, because that
        record is the audit answer after the event.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    held = seeded_stop_request(FIRST_OWNER_EMAIL)  # An earlier operator already asked.
    run_id = seed_run(run_store, STOPPING_STATE, stop_request=held)
    assert stop_run(upgrade_client, run_id, STOP_WORD).status_code == OK_STATUS  # The second click passes.
    stored = run_store.runs[run_id]["stop_request"]
    assert stored["requested_by"] == FIRST_OWNER_EMAIL  # The first operator still owns the stop.
    assert stored["requested_at"] == held["requested_at"]  # The time of the first ask still stands.


# ---------------------------------------------------------------------------
# T131: the answer of a recorded stop
# ---------------------------------------------------------------------------


def test_the_stop_answers_only_the_two_contract_fields(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """A recorded stop answers the state and the outcome, and no other key.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, RUNNING_STATE)  # A run in flight, which a stop reaches.
    answer = stop_run(upgrade_client, run_id, STOP_WORD)
    assert answer.status_code == OK_STATUS
    body: Any = answer.get_json()
    assert set(body) == STOP_ANSWER_FIELDS  # Exactly the two keys of the contract.
    assert body["state"] == STOPPING_STATE  # The run moved, and the panel reads the new state.


def test_the_stop_outcome_names_all_four_of_its_fields(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """The outcome record holds the three device lists and the message.

    Why:
        The stop panel draws one list for each key. A missing key would leave a
        blank panel with no server error, so the operator would not know whether
        a device was cancelled or not.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, RUNNING_STATE)  # A run in flight, which a stop reaches.
    body: Any = stop_run(upgrade_client, run_id, STOP_WORD).get_json()
    assert set(body["outcome"]) == OUTCOME_FIELDS  # Every key of FR-038e arrives.


def test_a_stop_with_no_cancel_work_claims_no_cancelled_device(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """A stop with no cancel work wired names no cancelled device at all.

    Why:
        FR-038f forbids a claim of a cancel that never happened. While the
        cancel work is not wired, the honest answer is three empty lists and one
        sentence that states only what the portal did do.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, RUNNING_STATE)  # The `STOP_RUNNER` seam stays unset in this test.
    outcome: Any = stop_run(upgrade_client, run_id, STOP_WORD).get_json()["outcome"]
    assert outcome["cancelled"] == []  # No device was cancelled, and the portal claims none.
    assert outcome["already_writing"] == []  # The portal names no device it did not read.
    assert outcome["message"]  # One true sentence still reaches the operator.


def test_the_stop_names_the_devices_the_cancel_work_reports(
    upgrade_app: Flask,
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """The outcome repeats the device lists that the cancel work answered.

    Why:
        FR-038c cancels a device that has not started, and FR-038d leaves a
        device in mid-flash alone. The route owns neither rule, so it must
        repeat the answer of the cancel work and change nothing in it.

    Args:
        upgrade_app: The application, so the test can wire the cancel work.
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    reported = StopOutcome(cancelled=(CANCELLED_MAC,), already_writing=(WRITING_MAC,), message="Two devices read.")
    upgrade_app.config[STOP_RUNNER_KEY] = RecordingStopRunner(reported)  # The cancel work of this test.
    run_id = seed_run(run_store, RUNNING_STATE)
    outcome: Any = stop_run(upgrade_client, run_id, STOP_WORD).get_json()["outcome"]
    assert outcome["cancelled"] == [CANCELLED_MAC]  # The device the portal stopped in time.
    assert outcome["already_writing"] == [WRITING_MAC]  # The device that keeps writing firmware.


def test_a_cancel_answer_of_the_wrong_shape_claims_no_cancel(
    upgrade_app: Flask,
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """A cancel answer of the wrong type still answers an honest empty outcome.

    Why:
        The cancel work arrives from another module on a later day. A wrong
        answer must not become a claim that the portal cancelled devices, and it
        must not fault, because the operator still needs the stop recorded.

    Args:
        upgrade_app: The application, so the test can wire the cancel work.
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    upgrade_app.config[STOP_RUNNER_KEY] = RecordingStopRunner({"cancelled": [CANCELLED_MAC]})  # Not an outcome.
    run_id = seed_run(run_store, RUNNING_STATE)
    answer = stop_run(upgrade_client, run_id, STOP_WORD)
    assert answer.status_code == OK_STATUS  # The stop was still recorded.
    body: Any = answer.get_json()
    assert body["outcome"]["cancelled"] == []  # The portal claims no cancel it cannot prove.


def test_the_stop_reads_the_word_from_a_form_body(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """A form post of the word stops the run, as a page without a script does.

    Why:
        `contracts/ui-testids.md` shows a stop dialog with a text field. A
        browser with no script posts that field as a form, so the route must
        read the word from a form body as well as from a JSON body.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, RUNNING_STATE)  # A run in flight, which a stop reaches.
    path = STOP_PATH_TEMPLATE.format(run_id=run_id)
    answer = upgrade_client.post(path, data={CONFIRM_FIELD: STOP_WORD})  # A form body, and no JSON at all.
    assert answer.status_code == OK_STATUS  # The form field met the same guard as a JSON field.


def test_a_stop_the_store_cannot_write_names_the_store_failure(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """A store that refuses the write answers 500 `stop_request_failed`.

    Why:
        The stop is only real once the record holds it, because the run driver
        reads the record. A portal that answered success on a failed write would
        tell the operator that the upgrade stops while it keeps running.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, RUNNING_STATE)  # The seeding write happens before the refusal starts.
    run_store.refuse_writes = True  # From this line, the store acts out an unreachable database.
    answer = stop_run(upgrade_client, run_id, STOP_WORD)
    assert answer.status_code == SERVER_ERROR_STATUS  # The portal reports the failure it met.
    assert read_error_code(answer) == STORE_FAILED_CODE  # The operator learns to try the stop again.


# ---------------------------------------------------------------------------
# FR-038i: the site lock guards the stop control
# ---------------------------------------------------------------------------


def test_a_stop_from_a_second_operator_is_refused_with_site_locked(
    upgrade_app: Flask,
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """A stop from an operator without the site lock answers 409 `site_locked`.

    Why:
        FR-038i binds this control to the operator that holds the site. Without
        the guard, any signed-in operator cancels the upgrade of any other
        operator, and the second operator learns of it only from the run page.

    Args:
        upgrade_app: The application, so the test names the holder of the site.
        upgrade_client: The signed-in client of the operator without the lock.
        run_store: The stand-in run record store.
    """
    hold_the_site(upgrade_app, FIRST_OWNER_EMAIL)  # Another operator already holds the site of the run below.
    run_id = seed_run(run_store, RUNNING_STATE)  # A run in flight, which a stop would otherwise reach.
    answer = stop_run(upgrade_client, run_id, STOP_WORD)  # The exact word, so only the lock refuses this call.
    assert answer.status_code == CONFLICT_STATUS  # The contract fixes 409 for a site that another operator holds.
    assert read_error_code(answer) == SITE_LOCKED_CODE  # A distinct word, so the browser tells the two 409s apart.
    assert read_error_details(answer)["actor_email"] == FIRST_OWNER_EMAIL  # The operator learns whom to ask.
    assert run_store.runs[run_id].get("stop_request") is None  # The refused stop wrote no request at all.
    assert run_store.runs[run_id]["state"] == RUNNING_STATE  # The upgrade of the first operator keeps running.


def test_the_operator_who_holds_the_site_still_stops_the_run(
    upgrade_app: Flask,
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """The operator that holds the site lock reaches the stop control.

    Why:
        A guard that refused every operator would leave a live upgrade with no
        stop at all. FR-038i names one operator, so the same guard must pass
        that one operator through to the cancel work.

    Args:
        upgrade_app: The application, so the test names the holder of the site.
        upgrade_client: The signed-in client of the operator that holds the site.
        run_store: The stand-in run record store.
    """
    hold_the_site(upgrade_app, PROBE_EMAIL)  # The signed-in operator of this test holds the site of the run.
    run_id = seed_run(run_store, RUNNING_STATE)
    answer = stop_run(upgrade_client, run_id, STOP_WORD)
    assert answer.status_code == OK_STATUS  # The holder of the lock met no refusal.
    assert run_store.runs[run_id]["stop_request"]["requested_by"] == PROBE_EMAIL  # FR-038h names the owner.


def test_a_held_site_still_answers_the_unknown_run_first(
    upgrade_app: Flask,
    upgrade_client: FlaskClient,
) -> None:
    """A stop for an absent run answers `run_not_found` even while the site is held.

    Why:
        The lock check reads the organization and the site out of the run record,
        and an absent run names neither. The check must pass that case on, so a
        stale link keeps its own honest code instead of a refusal about a lock.

    Args:
        upgrade_app: The application, so the test names the holder of the site.
        upgrade_client: The signed-in client.
    """
    hold_the_site(upgrade_app, FIRST_OWNER_EMAIL)  # Another operator holds the site the session picked.
    answer = stop_run(upgrade_client, UNKNOWN_RUN_ID, STOP_WORD)  # A well-shaped key that no store holds.
    assert answer.status_code == NOT_FOUND_STATUS  # The contract fixes 404 for every unknown run.
    assert read_error_code(answer) == RUN_NOT_FOUND_CODE  # One code for every run path of the portal.
