"""Contract tests for the join between a verified pre-check and its run.

Why:
    FR-035 refuses a start until the run names a saved pre-check, and the
    confirm page keeps its begin button shaded until then. Nothing wrote that
    field, so `POST /api/runs/<run_id>/start` answered 409 `pre_capture_missing`
    for every run and no operator could ever send an upgrade. These tests pin
    the whole journey: a capture of a run turns verified, the run then names it,
    and the start that follows reaches the run driver.

Scope:
    `POST /api/sites/<site_id>/captures` and `POST /api/runs/<run_id>/start`,
    joined through `capture.record_status`.

Fixtures:
    Every fixture lives in this file on purpose. The two seams below belong to
    these tests alone, and a shared fixture would hide the join they prove.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

import threading  # The capture reports from a worker thread, so a test waits on an event.
from collections.abc import Iterator  # The return type of each generator fixture.
from typing import Any  # A run record and a capture job are both free-form.

import pytest  # The test framework of the project.
from flask import Flask  # The application type of the portal.
from flask.testing import FlaskClient  # The client type that drives every request.
from werkzeug.test import TestResponse  # The answer type that every assertion reads.

from src.upgrade_portal.app.routes import capture as capture_routes  # The module under test.
from src.upgrade_portal.runtime import identity  # The real session guard, so the tests sign in for real.
from src.upgrade_portal.runtime.runs import RunRecordBuilder, RunSpec  # The record layer owns every field.

# --------------------------------------------------------------------------
# The contract values. Each one repeats a line of the specification.
# --------------------------------------------------------------------------

CAPTURE_PATH_TEMPLATE = "/api/sites/{site_id}/captures"  # The start of one capture.
START_PATH_TEMPLATE = "/api/runs/{run_id}/start"  # The one path that sends an upgrade.

RUN_STORE_KEY = "RUN_STORE"  # The seam that holds the run record store.
LAUNCHER_KEY = "RUN_LAUNCHER"  # The seam that hands a started run to the run driver.
RUNNER_KEY = "CAPTURE_RUNNER"  # The seam that performs the collection work.
MIST_READER_KEY = "MIST_READER"  # The seam that answers the site list.
LOCK_READER_KEY = "SITE_LOCK_READER"  # The seam that reads the site lock.

SELECTED_ORG_SESSION_KEY = "selected_org_id"  # The organization pick inside the signed session.
SELECTED_SITE_SESSION_KEY = "selected_site_id"  # The site pick inside the same signed session.

PRE_CAPTURE_FIELD = "pre_capture_id"  # The run record field that FR-035 reads before a start.
CONFIRM_WORD = "CONFIRM"  # FR-034 fixes this exact word, in these exact letters.
READY_STATE = "awaiting_confirmation"  # The state a run holds while it waits for the typed word.
VERIFIED_STATE = "verified"  # The state a capture holds once the portal read it back unchanged.

# WHY: The start refuses a plan that names no device, so every seeded run holds
# one row here and the pre-check stays the only rule under test.
PLANNED_ROW = {"mac": "5c5b350e0001", "version_target": "0.14.30075"}

ROLE_PRE = "pre"  # The half that runs before the upgrade.
ROLE_POST = "post"  # The half that the run driver owns.
TIER_STANDARD = 2  # The device state and the client lists.

ACCEPTED_STATUS = 202  # The portal took the work and answered before it ended.
CONFLICT_STATUS = 409  # The run exists and its state refuses the call.
PRE_CAPTURE_MISSING_CODE = "pre_capture_missing"  # FR-035 refuses a start with no saved pre-check.
PRE_CHECK_LOCKED_CODE = "pre_check_locked"  # A run that sent firmware keeps the reading it holds.

PROBE_EMAIL = "probe.operator@example.invalid"  # A reserved domain, so no real address appears.
UNKNOWN_RUN_ID = "run-00000000000000000000000000000000"  # A well-shaped key that no store holds.
WORKER_WAIT_SECONDS = 5.0  # A generous wait, so a slow machine does not fail the test.


class ScopedCloudSession:
    """A cloud session that may act on one organization only.

    Why:
        `identity` reads the privileges of the cloud session to decide the scope
        of the operator. A stand-in keeps the scope in the test and keeps the
        cloud out of it.
    """

    def __init__(self, org_id: str) -> None:
        """Record the one organization this session may act on.

        Args:
            org_id: The organization the operator may reach.
        """
        self.privileges = [{"scope": "org", "org_id": org_id, "name": "Test Org"}]


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
        self.writes = 0  # One count for each accepted write, so a test proves an untouched store.

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
        self.writes += 1  # The count rises only when a caller really wrote.
        return True  # The route then answers the operator.


class RecordingLauncher:
    """Counts every run the start route hands to the run driver.

    Why:
        A start that answers 202 must really reach the driver. A count is the
        only honest proof of that, because a status code alone cannot show what
        the portal did after it answered.
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


class VerifyingRunner:
    """A stand-in collector that reports one verified capture for each job.

    Why:
        The real collector reads a whole site. These tests prove what happens
        when a capture turns verified, so this stand-in reports that one state
        change through the same reporter the collector uses, and reads nothing.
        The counter holds one permit for each report, so a test that starts two
        captures waits for each one in turn and never reads a stale list.
    """

    def __init__(self) -> None:
        """Start with no job and with no report counted."""
        self.capture_ids: list[str] = []  # One entry for each job this runner received.
        self.reports = threading.Semaphore(0)  # One permit for each report, so no test ever sleeps.

    def __call__(self, job: dict[str, Any]) -> None:
        """Report one verified capture, then release the waiting test.

        Args:
            job: The capture job that the start route built.
        """
        capture_id = str(job["capture_id"])  # The identifier that the run must end up naming.
        self.capture_ids.append(capture_id)  # The test reads this list after it takes a permit.
        capture_routes.record_status(capture_id, state=VERIFIED_STATE, verified=True)  # The one change.
        self.reports.release()  # Every write of this thread is done, so the test may continue.


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
def runner() -> VerifyingRunner:
    """Return the stand-in that reports one verified capture.

    Returns:
        The verifying runner.
    """
    return VerifyingRunner()  # Each test starts with no capture at all.


@pytest.fixture
def launcher() -> RecordingLauncher:
    """Return the stand-in that counts every launched run.

    Returns:
        The recording launcher.
    """
    return RecordingLauncher()  # No run driver thread starts in a contract test.


@pytest.fixture
def joined_app(
    portal_app: Flask,
    fake_mist_api: Any,
    run_store: RecordingRunStore,
    runner: VerifyingRunner,
    launcher: RecordingLauncher,
) -> Flask:
    """Return the portal with both halves of the journey injected.

    Why:
        These tests join the capture routes to the run routes, so one fixture
        binds the seams of both. No test reaches the cloud, Redis, or ArangoDB.

    Args:
        portal_app: The real application from the shared fixture.
        fake_mist_api: The in-memory cloud reader of the shared fixtures.
        run_store: The stand-in run record store.
        runner: The stand-in that reports one verified capture.
        launcher: The stand-in that counts every launched run.

    Returns:
        The wired application.
    """
    portal_app.config[MIST_READER_KEY] = fake_mist_api.read  # No socket, no cloud account.
    portal_app.config[LOCK_READER_KEY] = lambda org_id, site_ids: {}  # Every site reads as free.
    portal_app.config[RUN_STORE_KEY] = run_store  # Both route modules read this one store.
    portal_app.config[RUNNER_KEY] = runner  # The capture route hands the job here.
    portal_app.config[LAUNCHER_KEY] = launcher  # The start route hands the run here.
    portal_app.config["WTF_CSRF_ENABLED"] = False  # The token has its own tests elsewhere.
    return portal_app  # Every test below drives this application.


@pytest.fixture
def registered_owner(fake_org_id: str) -> Iterator[identity.SessionOwner]:
    """Register one operator and drop the record when the test ends.

    Why:
        `identity.SESSION_REGISTRY` lives for the whole process. A test that
        leaves a record behind signs in a later test by accident.

    Args:
        fake_org_id: The organization the operator may act on.

    Yields:
        The identity pair of the registered operator.
    """
    owner = identity.build_owner(PROBE_EMAIL, identity.issue_browser_id())  # The pair the guard checks.
    record = identity.OperatorSession(
        owner=owner,
        cloud_session=ScopedCloudSession(fake_org_id),
        credential_mode=identity.CredentialMode.ENVIRONMENT_TOKEN,
    )
    identity.SESSION_REGISTRY.register(record)  # The guard reads the registry on every request.
    try:  # The test body runs with the owner in place.
        yield owner  # Every signed-in test reads this pair.
    finally:  # A leaked record would sign in a later test by accident.
        identity.SESSION_REGISTRY.drop(owner.key)  # The registry outlives the test, so clear it here.


@pytest.fixture
def joined_client(
    joined_app: Flask, registered_owner: identity.SessionOwner, fake_org_id: str, fake_site_id: str
) -> Iterator[FlaskClient]:
    """Return a signed-in client that already picked the organization and the site.

    Args:
        joined_app: The application with every seam injected.
        registered_owner: The identity pair of the registered operator.
        fake_org_id: The organization the operator picked.
        fake_site_id: The site the operator picked.

    Yields:
        The Flask test client, with the session held open.
    """
    with joined_app.test_client() as client:  # The context manager holds the session across requests.
        client.set_cookie(identity.BROWSER_ID_COOKIE, registered_owner.browser_id)  # Half of the guard.
        with client.session_transaction() as browser_session:  # The other half of the guard.
            browser_session[identity.SESSION_OWNER_KEY] = registered_owner.key  # Names the registered owner.
            browser_session[SELECTED_ORG_SESSION_KEY] = fake_org_id  # The scope of every later read.
            browser_session[SELECTED_SITE_SESSION_KEY] = fake_site_id  # The site the run belongs to.
        yield client  # Every test below drives this client.


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def seed_run(store: RecordingRunStore, org_id: str, site_id: str) -> str:
    """Write one run that waits for the typed word and return its key.

    Why:
        Every test below starts from a run that passes each start rule but the
        saved pre-check, so the pre-check is the only thing under test. The run
        therefore names one planned device, because the start also refuses a
        plan that names no device.

    Args:
        store: The stand-in run record store.
        org_id: The organization that holds the site.
        site_id: The site the run acts on.

    Returns:
        The key of the seeded run.
    """
    spec = RunSpec(org_id, "Probe organization", site_id, "Probe site", PROBE_EMAIL, "browser-probe")
    record = RunRecordBuilder().build(spec)  # The record layer owns every field and every default.
    record["state"] = READY_STATE  # The run waits for the word that FR-034 fixes.
    record["targets"] = [dict(PLANNED_ROW)]  # A copy, so no test can edit the shared row.
    store.write_run(record)  # Both route modules read this record through the seam.
    return str(record["run_id"])  # Every path below carries this key.


def take_capture(client: FlaskClient, site_id: str, run_id: str, role: str = ROLE_PRE) -> TestResponse:
    """Start one capture of one site through the real route.

    Args:
        client: The signed-in test browser.
        site_id: The site the capture reads.
        run_id: The run that owns the capture.
        role: The half of the run, which is the pre-check by default.

    Returns:
        The answer of the start route.
    """
    body = {"tier": TIER_STANDARD, "run_id": run_id, "role": role}  # The three fields the browser posts.
    return client.post(CAPTURE_PATH_TEMPLATE.format(site_id=site_id), json=body)


def await_capture(runner: VerifyingRunner, ordinal: int = 1) -> str:
    """Wait for the next worker report and return the capture it reported on.

    Why:
        The reading runs on another thread, so an assertion that ran at once
        would read the store before the worker wrote it. The counter makes the
        wait exact for each report in turn, and no test ever sleeps for a fixed
        time. A test that starts two captures therefore waits twice.

    Args:
        runner: The stand-in that reports one verified capture for each job.
        ordinal: The report to wait for, counting from one.

    Returns:
        The identifier of the capture the worker reported on.
    """
    assert runner.reports.acquire(timeout=WORKER_WAIT_SECONDS), "The capture worker never reported."
    return runner.capture_ids[ordinal - 1]  # The reports arrive in the order the tests start them.


def send_start(client: FlaskClient, run_id: str) -> TestResponse:
    """Type the word `CONFIRM` and post the start of one run.

    Args:
        client: The signed-in test browser.
        run_id: The run to start.

    Returns:
        The answer of the start route.
    """
    return client.post(START_PATH_TEMPLATE.format(run_id=run_id), json={"confirm": CONFIRM_WORD})


# ---------------------------------------------------------------------------
# The pure rule that picks the run.
# ---------------------------------------------------------------------------


def test_a_verified_pre_check_names_the_run_that_owns_it() -> None:
    """A progress record of the pre-check half answers its run key."""
    record = {"role": ROLE_PRE, "run_id": "run-abc"}  # The shape that `opening_record` builds.
    assert capture_routes.pre_check_run(record) == "run-abc"


def test_a_verified_post_check_names_no_run() -> None:
    """The run driver owns the post half, so this module must leave it alone.

    Why:
        `upgrade/driver.py` writes `post_capture_id` when the upgrade ends. A
        second writer here would race that one.
    """
    record = {"role": ROLE_POST, "run_id": "run-abc"}  # A post-check of the very same run.
    assert capture_routes.pre_check_run(record) == ""


def test_a_capture_outside_a_run_names_no_run() -> None:
    """A capture that names no run opens no start."""
    assert capture_routes.pre_check_run({"role": ROLE_PRE, "run_id": ""}) == ""


# ---------------------------------------------------------------------------
# The join.
# ---------------------------------------------------------------------------


def test_a_verified_pre_check_reaches_the_run_record(
    joined_client: FlaskClient,
    run_store: RecordingRunStore,
    runner: VerifyingRunner,
    fake_org_id: str,
    fake_site_id: str,
) -> None:
    """The run names the pre-check as soon as the portal verifies the capture.

    Why:
        FR-035 reads this one field before it allows a start. No line wrote it,
        so every start answered 409 and the feature could not be used at all.

    Args:
        joined_client: The signed-in test browser.
        run_store: The stand-in run record store.
        runner: The stand-in that reports one verified capture.
        fake_org_id: The organization that holds the site.
        fake_site_id: The site the capture reads.
    """
    run_id = seed_run(run_store, fake_org_id, fake_site_id)
    answer = take_capture(joined_client, fake_site_id, run_id)
    assert answer.status_code == ACCEPTED_STATUS
    capture_id = await_capture(runner)
    stored = run_store.read_run(run_id) or {}
    assert stored.get(PRE_CAPTURE_FIELD) == capture_id


def test_a_verified_post_check_leaves_the_pre_check_field_alone(
    joined_client: FlaskClient,
    run_store: RecordingRunStore,
    runner: VerifyingRunner,
    fake_org_id: str,
    fake_site_id: str,
) -> None:
    """A post-check writes nothing here, because the run driver owns that half.

    Args:
        joined_client: The signed-in test browser.
        run_store: The stand-in run record store.
        runner: The stand-in that reports one verified capture.
        fake_org_id: The organization that holds the site.
        fake_site_id: The site the capture reads.
    """
    run_id = seed_run(run_store, fake_org_id, fake_site_id)
    writes_before = run_store.writes  # The seed wrote once, and nothing else may write.
    take_capture(joined_client, fake_site_id, run_id, role=ROLE_POST)
    await_capture(runner)
    assert not (run_store.read_run(run_id) or {}).get(PRE_CAPTURE_FIELD)
    assert run_store.writes == writes_before


def test_a_capture_of_an_unknown_run_writes_nothing(
    joined_client: FlaskClient, run_store: RecordingRunStore, runner: VerifyingRunner, fake_site_id: str
) -> None:
    """A capture may name a run that this process never held, and must not fail.

    Why:
        A restarted portal holds no run record of an earlier process. The
        capture must still finish, and the operator must still meet the start
        refusal, which is the truthful answer.

    Args:
        joined_client: The signed-in test browser.
        run_store: The stand-in run record store.
        runner: The stand-in that reports one verified capture.
        fake_site_id: The site the capture reads.
    """
    take_capture(joined_client, fake_site_id, UNKNOWN_RUN_ID)
    await_capture(runner)
    assert run_store.writes == 0
    assert run_store.read_run(UNKNOWN_RUN_ID) is None


# ---------------------------------------------------------------------------
# The payoff: the start that the join unlocks.
# ---------------------------------------------------------------------------


def test_a_start_before_the_pre_check_still_refuses(
    joined_client: FlaskClient,
    run_store: RecordingRunStore,
    launcher: RecordingLauncher,
    fake_org_id: str,
    fake_site_id: str,
) -> None:
    """FR-035 keeps its refusal for a run that holds no verified pre-check.

    Args:
        joined_client: The signed-in test browser.
        run_store: The stand-in run record store.
        launcher: The stand-in that counts every launched run.
        fake_org_id: The organization that holds the site.
        fake_site_id: The site the run acts on.
    """
    run_id = seed_run(run_store, fake_org_id, fake_site_id)
    answer = send_start(joined_client, run_id)
    assert answer.status_code == CONFLICT_STATUS
    assert (answer.get_json() or {}).get("error", {}).get("code") == PRE_CAPTURE_MISSING_CODE
    assert launcher.launched == []


def test_a_start_after_the_pre_check_reaches_the_run_driver(
    joined_client: FlaskClient,
    run_store: RecordingRunStore,
    runner: VerifyingRunner,
    launcher: RecordingLauncher,
    fake_org_id: str,
    fake_site_id: str,
) -> None:
    """The whole journey works: capture the site, then send the upgrade.

    Why:
        This is the test that the feature exists for. It fails on the code as it
        stood before this change, because no line wrote the pre-check field.

    Args:
        joined_client: The signed-in test browser.
        run_store: The stand-in run record store.
        runner: The stand-in that reports one verified capture.
        launcher: The stand-in that counts every launched run.
        fake_org_id: The organization that holds the site.
        fake_site_id: The site the run acts on.
    """
    run_id = seed_run(run_store, fake_org_id, fake_site_id)
    take_capture(joined_client, fake_site_id, run_id)
    await_capture(runner)
    answer = send_start(joined_client, run_id)
    assert answer.status_code == ACCEPTED_STATUS
    assert launcher.launched == [run_id]


# ---------------------------------------------------------------------------
# The repeat pre-check.
# ---------------------------------------------------------------------------


def test_a_repeat_pre_check_would_carry_the_identifier_of_the_first() -> None:
    """The capture key derives from the run alone, so a repeat names the first.

    Why:
        This one property is the reason the route refuses a repeat. The capture
        collection keys on the identifier, so a second reading of the same run
        does not join the first one. It replaces that stored document in place.
    """
    first = capture_routes.build_capture_id("run-abc")  # The identifier the first pre-check carries.
    assert capture_routes.build_capture_id("run-abc") == first


def test_a_repeat_pre_check_before_the_start_is_accepted(
    joined_client: FlaskClient,
    run_store: RecordingRunStore,
    runner: VerifyingRunner,
    fake_org_id: str,
    fake_site_id: str,
) -> None:
    """An operator who wants a different tier may take the pre-check again.

    Why:
        The run has sent no firmware, so the site still holds the versions the
        first reading described. The replacement is what the operator asked for,
        and the newer reading is the better one.

    Args:
        joined_client: The signed-in test browser.
        run_store: The stand-in run record store.
        runner: The stand-in that reports one verified capture.
        fake_org_id: The organization that holds the site.
        fake_site_id: The site the run acts on.
    """
    run_id = seed_run(run_store, fake_org_id, fake_site_id)
    take_capture(joined_client, fake_site_id, run_id)
    first = await_capture(runner)
    answer = take_capture(joined_client, fake_site_id, run_id)
    assert answer.status_code == ACCEPTED_STATUS
    assert await_capture(runner, ordinal=2) == first
    assert (run_store.read_run(run_id) or {}).get(PRE_CAPTURE_FIELD) == first


def test_a_repeat_pre_check_after_the_start_is_refused(
    joined_client: FlaskClient,
    run_store: RecordingRunStore,
    runner: VerifyingRunner,
    fake_org_id: str,
    fake_site_id: str,
) -> None:
    """A run that sent firmware keeps the only reading of the site before it.

    Why:
        The brief asks the portal to lock the first capture, so that no later
        capture corrupts the reading the comparison depends on. A reading taken
        after the start describes upgraded devices, so the comparison would
        measure the upgraded site against itself and report no change. The route
        refuses, so no worker starts and no store write ever opens.

    Args:
        joined_client: The signed-in test browser.
        run_store: The stand-in run record store.
        runner: The stand-in that reports one verified capture.
        fake_org_id: The organization that holds the site.
        fake_site_id: The site the run acts on.
    """
    run_id = seed_run(run_store, fake_org_id, fake_site_id)
    take_capture(joined_client, fake_site_id, run_id)
    first = await_capture(runner)
    assert send_start(joined_client, run_id).status_code == ACCEPTED_STATUS
    answer = take_capture(joined_client, fake_site_id, run_id)
    assert answer.status_code == CONFLICT_STATUS
    assert (answer.get_json() or {}).get("error", {}).get("code") == PRE_CHECK_LOCKED_CODE
    assert runner.capture_ids == [first]  # The refusal ran before the route built any job.
    assert (run_store.read_run(run_id) or {}).get(PRE_CAPTURE_FIELD) == first


def test_a_post_check_after_the_start_is_never_refused(
    joined_client: FlaskClient,
    run_store: RecordingRunStore,
    runner: VerifyingRunner,
    fake_org_id: str,
    fake_site_id: str,
) -> None:
    """The rule guards the pre-check half alone.

    Why:
        The run driver owns the post half and gives it the second ordinal, so a
        post-check writes its own document and collides with nothing. A refusal
        there would stop every upgrade from ever reading the site afterwards.

    Args:
        joined_client: The signed-in test browser.
        run_store: The stand-in run record store.
        runner: The stand-in that reports one verified capture.
        fake_org_id: The organization that holds the site.
        fake_site_id: The site the run acts on.
    """
    run_id = seed_run(run_store, fake_org_id, fake_site_id)
    take_capture(joined_client, fake_site_id, run_id)
    await_capture(runner)
    assert send_start(joined_client, run_id).status_code == ACCEPTED_STATUS
    answer = take_capture(joined_client, fake_site_id, run_id, role=ROLE_POST)
    assert answer.status_code == ACCEPTED_STATUS
    assert await_capture(runner, ordinal=2)  # The worker really ran, and it finished before the test ends.
