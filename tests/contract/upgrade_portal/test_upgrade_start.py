"""Contract tests for the start call of one upgrade run.

Why:
    `tests/contract/upgrade_portal/test_upgrade_routes.py` proves that the word
    `CONFIRM` starts a run and that one wrong word refuses it. It does not prove
    the edge of the typed word, the order of the three refusal rules, or the
    promise that a refused start sends nothing at all. FR-034 makes the typed
    word the last guard in front of a whole site of hardware, so every near miss
    of that word needs its own test.

Scope:
    `POST /api/runs/<run_id>/start`. `contracts/http-api.md` section 5 fixes
    every status and every machine code below.

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

# --------------------------------------------------------------------------
# The contract values. Each one repeats a line of the specification.
# --------------------------------------------------------------------------

RUN_STORE_KEY = "RUN_STORE"  # The seam that holds the run record store.
LOCK_READER_KEY = "SITE_LOCK_READER"  # The seam that reads the site lock, named by `select.py`.
LAUNCHER_KEY = "RUN_LAUNCHER"  # The seam that hands a started run to the run driver.

PROBE_EMAIL = "probe.operator@example.invalid"  # A reserved domain, so no real address appears.
ORG_ID = "00000000-0000-0000-0000-0000000000aa"  # Matches the shared organization of the other tests.
SITE_ID = "00000000-0000-0000-0000-0000000000bb"  # Matches the shared site of the other tests.
PROBE_CAPTURE_ID = "cap-probe-pre-check"  # Stands for a saved pre-check, which FR-035 demands.

# WHY: The start refuses a plan that names no device, so every run that expects
# a 202 carries one planned device. The seven names match the target row that
# `contracts/http-api.md` section 5 fixes.
PROBE_TARGET = {
    "mac": "00000000aabb",
    "name": "Probe switch",
    "device_type": "switch",
    "state": "pending",
    "version_before": "21.4R3-S5",
    "version_target": "23.4R2-S3",
    "version_after": None,
}

SELECTED_ORG_SESSION_KEY = "selected_org_id"  # The organization pick inside the signed session.
SELECTED_SITE_SESSION_KEY = "selected_site_id"  # The site pick inside the same signed session.

START_PATH_TEMPLATE = "/api/runs/{run_id}/start"  # The one path that sends an upgrade.
UNKNOWN_RUN_ID = "run-00000000000000000000000000000000"  # A well-shaped key that no store holds.

CONFIRM_WORD = "CONFIRM"  # FR-034 fixes this exact word, in these exact letters.
READY_STATE = "awaiting_confirmation"  # The state a run holds while it waits for the typed word.
SUBMITTING_STATE = "upgrade_submitting"  # The state a started run holds at once.
RUNNING_STATE = "upgrade_running"  # The state a run holds once the cloud accepted the work.
COMPLETE_STATE = "complete"  # A run that already finished, which no start may restart.

ACCEPTED_STATUS = 202  # The portal took the start and the driver now owns the run.
BAD_REQUEST_STATUS = 400  # The portal could not read the request.
NOT_AUTHENTICATED_STATUS = 401  # No signed-in session.
NOT_FOUND_STATUS = 404  # No run holds the key.
CONFLICT_STATUS = 409  # The run exists and its state refuses the call.
METHOD_NOT_ALLOWED_STATUS = 405  # The path accepts a post only.

NOT_AUTHENTICATED_CODE = "not_authenticated"  # `identity.require_session` answers this code.
CSRF_MISSING_CODE = "csrf_missing"  # `security.py` answers this code for a post with no token.
RUN_NOT_FOUND_CODE = "run_not_found"  # One code for every run path with an unknown key.
CONFIRMATION_REQUIRED_CODE = "confirmation_required"  # FR-034 refuses any word but `CONFIRM`.
PRE_CAPTURE_MISSING_CODE = "pre_capture_missing"  # FR-035 refuses a start with no saved pre-check.
TARGETS_MISSING_CODE = "upgrade_targets_missing"  # The start refuses a saved plan that names no device.

# WHY: `contracts/http-api.md` section 5 fixes exactly this one answer field for
# a start. The browser reads the state and then polls, so a second field would
# promise the reader something the contract never fixed.
START_ANSWER_FIELDS = {"state"}

# WHY: Each of these near misses is a word an operator may really type. FR-034
# accepts one word only, so each one must reach the same refusal.
NEAR_MISS_WORDS = ("confirm", "Confirm", " CONFIRM ", "CONFIRM!", "YES", "")


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


class RecordingLauncher:
    """Counts every run the start route hands to the run driver.

    Why:
        A refused start must send nothing at all. A count is the only honest
        proof of that, because a status code alone cannot show what the portal
        did after it answered.
    """

    def __init__(self) -> None:
        """Start with no launched run at all."""
        self.launched: list[str] = []  # One entry for each run the route handed over.

    def __call__(self, record: dict[str, Any]) -> None:
        """Take one prepared run record.

        Args:
            record: The run record, already in the state `upgrade_submitting`.
        """
        self.launched.append(str(record.get("run_id", "")))  # The test then counts the entries.


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
    """Return the portal application with the run store injected and no launcher.

    Why:
        The launcher seam stays empty. The shared `portal_app` fixture empties
        the seam that `wiring.install_seams` fills. One test below proves that
        the portal still answers when the driver wiring is absent, and every
        other test asks for the `launcher` fixture, which fills the seam.

    Args:
        portal_app: The real application from the shared fixture.
        run_store: The stand-in run record store.

    Returns:
        The application with the seams in place.
    """
    portal_app.config[RUN_STORE_KEY] = run_store  # No ArangoDB server runs in a contract test.
    portal_app.config[LOCK_READER_KEY] = lambda org_id, site_ids: {}  # No Redis server runs in a contract test.
    portal_app.config["WTF_CSRF_ENABLED"] = False  # One test below reads the untouched application instead.
    return portal_app  # Every test below drives this application.


@pytest.fixture
def launcher(upgrade_app: Flask) -> RecordingLauncher:
    """Fill the launcher seam and return the recorder.

    Args:
        upgrade_app: The application with the other seams injected.

    Returns:
        The recorder that counts every launched run.
    """
    recorder = RecordingLauncher()  # No run driver thread starts in a contract test.
    upgrade_app.config[LAUNCHER_KEY] = recorder  # The route reads this seam at request time.
    return recorder


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
    """Give one client a signed session, an organization pick, and a site pick.

    Args:
        client: The Flask test client.
        owner: The registered operator.
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
        sign_in_client(client, registered_owner)  # The state that every passing test needs.
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
    record.update(fields)  # The saved pre-check key arrives here.
    store.write_run(record)  # The route reads this record through the seam.
    return str(record["run_id"])  # Every path below carries this key.


def seed_ready_run(store: RecordingRunStore) -> str:
    """Write one run that passes every start rule but the typed word.

    Why:
        Most tests below change one thing only: the word the operator types. A
        shared starting point keeps each test about that one word. The run holds
        a saved pre-check and one planned device, because the start refuses both
        a missing pre-check and an empty plan.

    Args:
        store: The stand-in run record store.

    Returns:
        The key of the seeded run.
    """
    # FR-035 asks for the saved pre-check, and the plan must name a device.
    return seed_run(store, READY_STATE, pre_capture_id=PROBE_CAPTURE_ID, targets=[dict(PROBE_TARGET)])


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


def start_run(client: FlaskClient, run_id: str, word: str | None) -> TestResponse:
    """Ask the portal to start one run with one typed word.

    Args:
        client: The Flask test client.
        run_id: The run key.
        word: The typed word, or None to send a body with no confirm field.

    Returns:
        The portal answer.
    """
    body: dict[str, Any] = {} if word is None else {"confirm": word}  # None stands for a body with no field.
    return client.post(START_PATH_TEMPLATE.format(run_id=run_id), json=body)


# ---------------------------------------------------------------------------
# T129: the guard in front of the start path
# ---------------------------------------------------------------------------


def test_the_start_path_refuses_a_read(upgrade_client: FlaskClient, run_store: RecordingRunStore) -> None:
    """A get on the start path answers 405, because the contract names a post only.

    Why:
        A start changes a whole site of hardware. A path that answered a get
        would let a link, a browser prefetch, or a crawler send an upgrade.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_ready_run(run_store)  # A run that a post could really start.
    assert upgrade_client.get(START_PATH_TEMPLATE.format(run_id=run_id)).status_code == METHOD_NOT_ALLOWED_STATUS


def test_a_start_with_no_session_is_refused(
    signed_out_client: FlaskClient,
    run_store: RecordingRunStore,
    launcher: RecordingLauncher,
) -> None:
    """A start with no signed-in session answers 401 and sends no upgrade.

    Args:
        signed_out_client: A client that never signed in.
        run_store: The stand-in run record store.
        launcher: The recorder that counts every launched run.
    """
    run_id = seed_ready_run(run_store)  # The run exists, so only the guard can refuse.
    answer = start_run(signed_out_client, run_id, CONFIRM_WORD)  # Even the right word must not pass the guard.
    assert answer.status_code == NOT_AUTHENTICATED_STATUS  # The guard refused before the handler ran.
    assert read_error_code(answer) == NOT_AUTHENTICATED_CODE  # One code for every unsigned request.
    assert launcher.launched == []  # No upgrade left the portal.


def test_a_start_with_no_token_is_refused(portal_app: Flask, registered_owner: identity.SessionOwner) -> None:
    """A start post with no token answers 400 `csrf_missing`.

    Why:
        `security.py` registers the token check for every post, and `TESTING`
        does not switch it off. This test runs against the untouched portal, so
        it proves that the one path that sends an upgrade sits behind the check.

    Args:
        portal_app: The portal application, with the token check still on.
        registered_owner: The identity pair of the registered operator.
    """
    with portal_app.test_client() as client:  # This application never saw the fixture that clears the check.
        sign_in_client(client, registered_owner)
        answer = start_run(client, UNKNOWN_RUN_ID, CONFIRM_WORD)
    assert answer.status_code == BAD_REQUEST_STATUS  # The check refuses before the handler runs.
    assert read_error_code(answer) == CSRF_MISSING_CODE  # The browser reads this code and fetches a token.


def test_a_start_of_an_unknown_run_is_refused(
    upgrade_client: FlaskClient,
    launcher: RecordingLauncher,
) -> None:
    """A start for a key that no store holds answers 404 `run_not_found`.

    Why:
        A stale browser tab and a hand-typed path both reach this route. The
        portal must name the missing run and must not read the typed word at
        all, because there is no run for that word to start.

    Args:
        upgrade_client: The signed-in client.
        launcher: The recorder that counts every launched run.
    """
    answer = start_run(upgrade_client, UNKNOWN_RUN_ID, CONFIRM_WORD)  # A well-shaped key that no store holds.
    assert answer.status_code == NOT_FOUND_STATUS  # The run is absent, so no state can change.
    assert read_error_code(answer) == RUN_NOT_FOUND_CODE  # One code for every run path.
    assert launcher.launched == []  # No upgrade left the portal.


# ---------------------------------------------------------------------------
# T129: the typed word
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("word", NEAR_MISS_WORDS)
def test_a_start_refuses_every_near_miss_of_the_word(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
    launcher: RecordingLauncher,
    word: str,
) -> None:
    """Every near miss of the word `CONFIRM` answers 400 and sends no upgrade.

    Why:
        FR-034 fixes one word, in one letter case, with no space around it. A
        route that trimmed the text or folded the letter case would accept a
        word the operator typed by habit, and a whole site would then upgrade.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
        launcher: The recorder that counts every launched run.
        word: The near miss the operator typed.
    """
    run_id = seed_ready_run(run_store)  # A run that the right word would start at once.
    answer = start_run(upgrade_client, run_id, word)  # Only the word differs from the passing case.
    assert answer.status_code == BAD_REQUEST_STATUS  # A wrong word is a caller defect, not a state conflict.
    assert read_error_code(answer) == CONFIRMATION_REQUIRED_CODE  # The page then shows the word to type.
    assert launcher.launched == []  # No upgrade left the portal.


def test_a_start_with_no_confirm_field_is_refused(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
    launcher: RecordingLauncher,
) -> None:
    """A start body with no confirm field at all answers 400 `confirmation_required`.

    Why:
        A script that posts to this path carries no form field. An absent field
        must read as an empty word, and never as a silent pass.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
        launcher: The recorder that counts every launched run.
    """
    run_id = seed_ready_run(run_store)  # A run that the right word would start at once.
    answer = start_run(upgrade_client, run_id, None)  # An empty body, with no confirm field at all.
    assert answer.status_code == BAD_REQUEST_STATUS  # The portal read no word, so it starts nothing.
    assert read_error_code(answer) == CONFIRMATION_REQUIRED_CODE  # The page then shows the word to type.
    assert launcher.launched == []  # No upgrade left the portal.


def test_a_refused_start_leaves_the_run_in_its_saved_state(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """A refused start writes nothing at all into the run record.

    Why:
        The 30-second poll reads the same record. A refused start that still
        moved the state would show the operator a run in flight that nothing
        drives, and the page would then wait for ever.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_ready_run(run_store)  # A run that the right word would start at once.
    start_run(upgrade_client, run_id, "confirm")  # The lowercase word, which FR-034 refuses.
    assert run_store.runs[run_id]["state"] == READY_STATE  # The run still waits for the typed word.


def test_the_wrong_word_is_refused_before_the_missing_pre_check(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """A run that breaks two start rules answers the word rule first.

    Why:
        FR-034 and FR-035 both refuse this run. The order is fixed on purpose,
        so the page always shows one cure at a time. The word is the cure the
        operator can act on right there, so the portal names it first.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, READY_STATE)  # No saved pre-check, so FR-035 also refuses this run.
    answer = start_run(upgrade_client, run_id, "yes")  # A wrong word, so FR-034 refuses it as well.
    assert read_error_code(answer) == CONFIRMATION_REQUIRED_CODE  # The word rule runs first.
    assert read_error_code(answer) != PRE_CAPTURE_MISSING_CODE  # The pre-check rule never ran.


def test_a_start_with_no_pre_check_names_a_state_conflict(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """A run with no saved pre-check answers 409, and never 400.

    Why:
        The two refusals of a start carry two different statuses on purpose. A
        wrong word is a caller defect, which the operator fixes by typing again.
        A missing pre-check is a state conflict, which the operator fixes by
        running the pre-check page first.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, READY_STATE)  # The right state, and no saved pre-check at all.
    answer = start_run(upgrade_client, run_id, CONFIRM_WORD)  # The right word, so only FR-035 can refuse.
    assert answer.status_code == CONFLICT_STATUS  # A state conflict, and never a caller defect.
    assert read_error_code(answer) == PRE_CAPTURE_MISSING_CODE  # The page then sends the operator to the pre-check.


def test_a_start_of_an_empty_plan_names_a_state_conflict(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
    launcher: RecordingLauncher,
) -> None:
    """A run whose plan names no device answers 409 and sends nothing.

    Why:
        An operator can open the options page and save it with no chosen
        version, which saves an empty plan. A start of that plan would send
        nothing and would still report a complete run, so the operator would
        read a site that never changed as an upgraded site.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
        launcher: The recorder that counts every launched run.
    """
    # A saved pre-check, so only the empty plan can refuse this start.
    run_id = seed_run(run_store, READY_STATE, pre_capture_id=PROBE_CAPTURE_ID, targets=[])
    answer = start_run(upgrade_client, run_id, CONFIRM_WORD)  # The right word, and nothing else to refuse it.
    assert answer.status_code == CONFLICT_STATUS  # A state conflict, which the options page fixes.
    assert read_error_code(answer) == TARGETS_MISSING_CODE  # The page then sends the operator to the options.
    assert launcher.launched == []  # No upgrade left the portal.


# ---------------------------------------------------------------------------
# T129: the accepted start
# ---------------------------------------------------------------------------


def test_a_start_reads_the_word_from_a_form_body(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
    launcher: RecordingLauncher,
) -> None:
    """A form post carries the typed word as well as a JSON post does.

    Why:
        The confirmation page posts a real form, and a script posts JSON. Both
        reach one route, so both must read the same field. A route that read
        JSON only would refuse every operator who has no script.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
        launcher: The recorder that counts every launched run.
    """
    run_id = seed_ready_run(run_store)  # A run that the right word starts at once.
    path = START_PATH_TEMPLATE.format(run_id=run_id)
    answer = upgrade_client.post(path, data={"confirm": CONFIRM_WORD})  # A form body, and no JSON at all.
    assert answer.status_code == ACCEPTED_STATUS  # The portal read the word from the form.
    assert launcher.launched == [run_id]  # Exactly one upgrade left the portal.


def test_a_start_answers_only_the_state_field(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
    launcher: RecordingLauncher,
) -> None:
    """An accepted start answers the new state, and nothing else.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
        launcher: The recorder that counts every launched run.
    """
    run_id = seed_ready_run(run_store)  # A run that the right word starts at once.
    body: Any = start_run(upgrade_client, run_id, CONFIRM_WORD).get_json()
    assert set(body) == START_ANSWER_FIELDS  # Exactly the one field of the contract.
    assert body["state"] == SUBMITTING_STATE  # The browser then polls until the driver moves the run.


def test_a_start_with_no_driver_still_answers_and_saves_the_state(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """A start with no run driver wired answers 202 and saves the new state.

    Why:
        The driver sits behind a seam that a deployment may leave unset. The
        portal must still answer the operator and must still record what it
        did, so the poll shows a run held at `upgrade_submitting` instead of a
        page that never loads.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_ready_run(run_store)  # The `launcher` fixture is absent, so the seam stays unset.
    answer = start_run(upgrade_client, run_id, CONFIRM_WORD)  # The right word, and no driver behind it.
    assert answer.status_code == ACCEPTED_STATUS  # The operator still reads an answer.
    assert run_store.runs[run_id]["state"] == SUBMITTING_STATE  # The record still tells the truth.


def test_a_start_of_a_run_already_in_flight_sends_nothing(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
    launcher: RecordingLauncher,
) -> None:
    """A start for a run that the driver already owns answers the live state.

    Why:
        FR-038 accepts one begin action for each run, even across several
        browser tabs. A second tab that reloads the confirmation page must not
        send a second upgrade to the same hardware.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
        launcher: The recorder that counts every launched run.
    """
    # The driver already owns this run, so the record holds the plan it started.
    run_id = seed_run(run_store, RUNNING_STATE, pre_capture_id=PROBE_CAPTURE_ID, targets=[dict(PROBE_TARGET)])
    answer = start_run(upgrade_client, run_id, CONFIRM_WORD)  # A second tab typed the word again.
    assert answer.status_code == ACCEPTED_STATUS  # A repeat is not a fault, so the portal answers plainly.
    assert answer.get_json()["state"] == RUNNING_STATE  # The live state, and never the state of a new start.
    assert launcher.launched == []  # No second upgrade left the portal.


def test_a_start_of_a_finished_run_sends_nothing(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
    launcher: RecordingLauncher,
) -> None:
    """A start for a run that already finished answers the finished state.

    Why:
        A finished run holds a saved pre-check and a saved post-check. Nothing
        in the start rules refuses it, so the state model is the only guard. A
        restart would overwrite the record of an upgrade that already ran.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
        launcher: The recorder that counts every launched run.
    """
    # A run that already finished, so the record still holds the plan it ran.
    run_id = seed_run(run_store, COMPLETE_STATE, pre_capture_id=PROBE_CAPTURE_ID, targets=[dict(PROBE_TARGET)])
    answer = start_run(upgrade_client, run_id, CONFIRM_WORD)  # A stale tab typed the word again.
    assert answer.get_json()["state"] == COMPLETE_STATE  # The finished state, and never a new start.
    assert run_store.runs[run_id]["state"] == COMPLETE_STATE  # The record of the finished run stands.
    assert launcher.launched == []  # No upgrade left the portal.
