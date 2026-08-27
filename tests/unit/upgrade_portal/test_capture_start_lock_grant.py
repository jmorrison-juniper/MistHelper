"""The capture start must take the site lock.

Why:
    `spec.md` User Story 4 Acceptance Scenario 1 states that a capture start on a
    free site grants the site lock to that session owner. Success Criterion 6
    then asks the portal to block a second operator in every attempt. A start
    that only reads the lock leaves the site free, so two operators can capture
    one site at the same moment. Issue #2092 records that defect.

The unreachable lock store:
    `contracts/site-lock.md` states that an unreachable lock store still lets a
    capture start, because only an upgrade writes firmware. The last test below
    pins that choice, so a later change cannot make a capture need Redis.

No network:
    Every seam arrives through the application configuration. The lock reader and
    the lock store are the same stand-in, so a read and a write always agree.
    These tests reach no cloud, no Redis server, and no database.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

import threading  # The route hands each job to a worker thread, and the test waits on an event.
from collections.abc import Callable, Iterator  # Types the lock reader and each fixture that yields.
from contextlib import contextmanager  # The second operator needs a signed session inside one test body.
from typing import Any  # A cloud payload, a capture job, and an injected seam are all free-form.

import pytest  # The test framework.
from flask import Flask  # The smallest application that can hold the blueprint.
from flask.testing import FlaskClient  # Drives a route with no server and no browser.
from werkzeug.test import TestResponse  # The answer that the test client returns.

from src.upgrade_portal.app.routes import capture  # The module under test.
from src.upgrade_portal.app.routes.select import (  # The real seam and session names.
    LOCK_CLIENT_KEY,
    LOCK_READER_KEY,
    MIST_READER_KEY,
    SELECTED_ORG_KEY,
)
from src.upgrade_portal.runtime import identity, lock  # The registry, the session fields, and the lock rules.
from tests.support.lock_store_double import FakeLockStore  # The store stand-in that every test below shares.

# --------------------------------------------------------------------------
# The fixed values. Each one repeats a line of the specification.
# --------------------------------------------------------------------------

ORG_ID = "00000000-0000-0000-0000-0000000000c3"  # The organization the operator picked.
SITE_ID = "00000000-0000-0000-0000-0000000000d4"  # The site the capture reads.
SITE_KEY = f"misthelper:lock:site:{ORG_ID}:{SITE_ID}"  # The key `build_key` writes for this pair.

FIRST_EMAIL = "first.operator@example.invalid"  # A reserved domain, so no real address appears.
SECOND_EMAIL = "second.operator@example.invalid"  # The operator that arrives after the lock exists.

FAKE_SECRET = "test-secret-value-for-session-signing"  # Signs the browser session in the test only.

START_PATH = f"/api/sites/{SITE_ID}/captures"  # `contracts/http-api.md` fixes this path.
SITES_READ = "listOrgSites"  # The cloud read that answers the site record.

ACCEPTED_STATUS = 202  # The portal took the work and answered before the read ended.
CONFLICT_STATUS = 409  # Another operator holds the site lock.
SITE_LOCKED_CODE = "site_locked"  # `contracts/http-api.md:138` fixes this code for the capture start.

TIER_STANDARD = 2  # The device state and the client lists.
WORKER_WAIT_SECONDS = 5.0  # A generous wait, so a slow machine does not fail the test.

SITE_RECORD: dict[str, Any] = {"id": SITE_ID, "name": "Probe site", "org_id": ORG_ID}  # The one site.


# --------------------------------------------------------------------------
# The stand-ins.
# --------------------------------------------------------------------------


class RecordingRunner:
    """A stand-in for the collection work, which records the job it received.

    Why:
        A refusal must start no work at all. This class proves that half by
        counting the jobs, and the event lets a test wait on the worker instead
        of on a sleep.

    Attributes:
        jobs: One entry for each start the route accepted.
        started: The event that the worker sets when it takes a job.
    """

    def __init__(self) -> None:
        """Start with no job and with the event unset."""
        self.jobs: list[dict[str, Any]] = []  # One entry for each start the route accepted.
        self.started = threading.Event()  # The test waits on this event, never on a sleep.

    def __call__(self, job: dict[str, Any]) -> None:
        """Record one job and release the waiting test.

        Args:
            job: The capture job that the start route built.
        """
        self.jobs.append(dict(job))  # A copy, so a later change in the route cannot rewrite history.
        self.started.set()  # The test may continue now.


def cloud_reader_with_one_site(name: str, **parameters: Any) -> list[dict[str, Any]]:
    """Answer the site list of the test organization, and answer nothing else.

    Why:
        `select.find_site` reads the site list to prove that the organization
        holds the site. The route refuses with 404 before it reaches the lock
        step when that read answers nothing.

    Args:
        name: The cloud read the route asked for.
        **parameters: The call parameters, which this stand-in does not read.

    Returns:
        One site record for the site list read, or an empty list.
    """
    del parameters  # The stand-in answers the same list for every call shape.
    if name == SITES_READ:  # The one read that the start route performs.
        return [dict(SITE_RECORD)]  # A copy, so no test can change the shared record.
    return []  # Every other read answers nothing, because this route makes no other.


def reader_backed_by(store: FakeLockStore) -> Callable[[str, list[str]], dict[str, str | None]]:
    """Build a site lock reader that reads the same store the route writes.

    Why:
        The refusal reads the lock through the `SITE_LOCK_READER` seam, and the
        grant writes through the `LOCK_STORE_CLIENT` seam. A test that backs both
        with one store proves that a grant is visible to the next operator.

    Args:
        store: The stand-in store that both seams share.

    Returns:
        The reader callable that the seam accepts.
    """

    def read(org_id: str, site_ids: list[str]) -> dict[str, str | None]:
        """Return the holder of each site named.

        Args:
            org_id: The organization that owns the sites.
            site_ids: The sites to ask about.

        Returns:
            One entry for each site, holding the address or None.
        """
        return lock.read_site_locks(org_id, site_ids, client=store)  # The real reader, on the shared store.

    return read  # The test writes this callable into the application configuration.


# --------------------------------------------------------------------------
# The fixtures.
# --------------------------------------------------------------------------


@pytest.fixture
def lock_store() -> FakeLockStore:
    """Return the stand-in lock store that the reader and the writer share.

    Returns:
        A fresh store, so no lock survives from an earlier test.
    """
    return FakeLockStore()  # One store for each test keeps every test independent.


@pytest.fixture
def capture_runner() -> RecordingRunner:
    """Return the stand-in that receives every capture job.

    Returns:
        A fresh recording runner, so no job survives from an earlier test.
    """
    return RecordingRunner()  # One runner for each test keeps every test independent.


@pytest.fixture
def portal_app(capture_runner: RecordingRunner, lock_store: FakeLockStore) -> Flask:
    """Return a bare application that holds the capture blueprint alone.

    Why:
        A bare application holds no sibling blueprint and no request forgery
        guard, so no other route can change an answer.

    Args:
        capture_runner: The stand-in that receives the capture job.
        lock_store: The stand-in store that both lock seams share.

    Returns:
        The application, ready for a test client.
    """
    app = Flask(__name__)  # The smallest application that can hold the blueprint.
    app.config.update(TESTING=True, SECRET_KEY=FAKE_SECRET, WTF_CSRF_ENABLED=False)  # Test settings alone.
    app.config[MIST_READER_KEY] = cloud_reader_with_one_site  # No socket, and no cloud account.
    app.config[LOCK_READER_KEY] = reader_backed_by(lock_store)  # The read sees every grant of the write.
    app.config[LOCK_CLIENT_KEY] = lock_store  # The grant writes here instead of a Redis server.
    app.config[capture.RUNNER_KEY] = capture_runner  # The route hands the job here instead of the cloud.
    app.register_blueprint(capture.capture_bp)  # The routes under test.
    return app  # Each test drives this application through a client.


@pytest.fixture
def first_owner() -> Iterator[identity.SessionOwner]:
    """Register the first operator and drop the record when the test ends.

    Yields:
        The identity pair of the first operator.
    """
    yield from register_owner(FIRST_EMAIL)  # The helper holds the shared registration steps.


@pytest.fixture
def second_owner() -> Iterator[identity.SessionOwner]:
    """Register the second operator and drop the record when the test ends.

    Yields:
        The identity pair of the second operator.
    """
    yield from register_owner(SECOND_EMAIL)  # A second address and a second browser, so the pair differs.


@pytest.fixture
def client(portal_app: Flask, first_owner: identity.SessionOwner) -> Iterator[FlaskClient]:
    """Return a signed-in client of the first operator.

    Args:
        portal_app: The application with every seam injected.
        first_owner: The identity pair of the first operator.

    Yields:
        The Flask test client, with the session held open.
    """
    with signed_client(portal_app, first_owner) as opened:  # The helper holds the shared sign-in steps.
        yield opened  # Every test below drives this client.


# --------------------------------------------------------------------------
# The helpers.
# --------------------------------------------------------------------------


def register_owner(address: str) -> Iterator[identity.SessionOwner]:
    """Register one operator and drop the record when the test ends.

    Why:
        The session guard reads the registry on every request, and the registry
        lives for the whole process. A leaked record would sign in a later test
        by accident, so the helper clears it.

    Args:
        address: The work email address of the operator.

    Yields:
        The identity pair of the registered operator.
    """
    owner = identity.build_owner(address, identity.issue_browser_id())  # The pair the guard checks.
    record = identity.OperatorSession(
        owner=owner,  # The pair that the browser cookie and the session field name.
        cloud_session=object(),  # A plain object states no scope, so every organization passes.
        credential_mode=identity.CredentialMode.ENVIRONMENT_TOKEN,  # No password takes part in these tests.
    )
    identity.SESSION_REGISTRY.register(record)  # The guard reads the registry on every request.
    try:  # The test body runs with the owner in place.
        yield owner  # Every signed-in test reads this pair.
    finally:  # A leaked record would sign in a later test by accident.
        identity.SESSION_REGISTRY.drop(owner.key)  # The registry outlives the test, so clear it here.


@contextmanager
def signed_client(portal_app: Flask, owner: identity.SessionOwner) -> Iterator[FlaskClient]:
    """Return a client that is signed in and that already picked the organization.

    Args:
        portal_app: The application with every seam injected.
        owner: The identity pair the session names.

    Yields:
        The Flask test client, with the session held open.
    """
    with portal_app.test_client() as opened:  # The context manager holds the session across requests.
        opened.set_cookie(identity.BROWSER_ID_COOKIE, owner.browser_id)  # Half of the guard.
        with opened.session_transaction() as browser_session:  # The other half of the guard.
            browser_session[identity.SESSION_OWNER_KEY] = owner.key  # Names the registered owner.
            browser_session[SELECTED_ORG_KEY] = ORG_ID  # The picker writes this field.
        yield opened  # The test drives this client.


def start_capture(client: FlaskClient) -> TestResponse:
    """Post one capture start of the test site and return the answer.

    Args:
        client: The signed-in browser.

    Returns:
        The portal answer.
    """
    return client.post(START_PATH, json={"tier": TIER_STANDARD})  # The default tier of the contract.


def error_code(response: TestResponse) -> str:
    """Read the machine code out of one refusal envelope.

    Args:
        response: The portal answer.

    Returns:
        The code, or an empty string when the body carries none.
    """
    body: Any = response.get_json(silent=True) or {}  # A body of another shape reads as an empty index.
    error: Any = body.get("error") or {}  # The envelope nests the code under this one key.
    return str(error.get("code", ""))  # An envelope with no code reads as an empty string.


def assert_capture_started(answer: TestResponse, runner: RecordingRunner, count: int) -> None:
    """Assert that a start answered 202 and that the worker holds the wanted jobs.

    Args:
        answer: The portal answer.
        runner: The stand-in that receives every capture job.
        count: How many jobs the worker must hold by now.
    """
    assert answer.status_code == ACCEPTED_STATUS  # The route took the work.
    assert runner.started.wait(WORKER_WAIT_SECONDS)  # The worker thread ran, so no sleep is needed.
    assert len(runner.jobs) == count  # No start may run twice, and none may go missing.


# --------------------------------------------------------------------------
# The grant. This is the defect of issue #2092.
# --------------------------------------------------------------------------


def test_a_capture_start_on_a_free_site_takes_the_site_lock(
    client: FlaskClient,
    capture_runner: RecordingRunner,
    lock_store: FakeLockStore,
    first_owner: identity.SessionOwner,
) -> None:
    """A capture start on a free site grants the site lock to that operator.

    Why:
        `spec.md` User Story 4 Acceptance Scenario 1 asks for this grant. Before
        issue #2092 the route only refused, so the store held no key at all and a
        second operator read the site as free.

    Args:
        client: The signed-in test client of the first operator.
        capture_runner: The stand-in that receives the capture job.
        lock_store: The stand-in store that both lock seams share.
        first_owner: The identity pair of the first operator.
    """
    answer = start_capture(client)  # The site is free, so the start must take the lock.
    assert_capture_started(answer, capture_runner, 1)  # The capture still runs.
    assert SITE_KEY in lock_store.values  # The store now holds one lock for this site.
    assert lock_store.holder_email(SITE_KEY) == first_owner.actor_email  # The starter holds it.


def test_a_second_operator_then_reads_site_locked(
    portal_app: Flask,
    client: FlaskClient,
    capture_runner: RecordingRunner,
    second_owner: identity.SessionOwner,
) -> None:
    """A second operator cannot capture a site that the first operator started.

    Why:
        Success Criterion 6 asks the portal to block the second operator in every
        attempt. The block needs the grant above, because a free site refuses
        nobody.

    Args:
        portal_app: The application with every seam injected.
        client: The signed-in test client of the first operator.
        capture_runner: The stand-in that receives the capture job.
        second_owner: The identity pair of the second operator.
    """
    assert_capture_started(start_capture(client), capture_runner, 1)  # The first operator holds the site.
    with signed_client(portal_app, second_owner) as rival:  # A second browser, with a second address.
        answer = start_capture(rival)  # The second operator asks for the same site.
        assert answer.status_code == CONFLICT_STATUS  # The portal refuses.
        assert error_code(answer) == SITE_LOCKED_CODE  # The refusal names the lock, not another fault.
    assert len(capture_runner.jobs) == 1  # The refusal started no second capture.


def test_the_lock_holder_starts_a_second_capture(
    client: FlaskClient,
    capture_runner: RecordingRunner,
    lock_store: FakeLockStore,
    first_owner: identity.SessionOwner,
) -> None:
    """The operator that holds the lock starts another capture on the same site.

    Why:
        The documented journey asks one operator for a pre-check capture and a
        post-check capture on one site. A grant that refused the holder would
        break that journey at the second capture.

    Args:
        client: The signed-in test client of the first operator.
        capture_runner: The stand-in that receives the capture job.
        lock_store: The stand-in store that both lock seams share.
        first_owner: The identity pair of the first operator.
    """
    assert_capture_started(start_capture(client), capture_runner, 1)  # The first capture takes the lock.
    assert_capture_started(start_capture(client), capture_runner, 2)  # The second capture renews the hold.
    assert lock_store.holder_email(SITE_KEY) == first_owner.actor_email  # The same operator still holds it.


def test_an_unreachable_lock_store_still_starts_the_capture(
    client: FlaskClient, capture_runner: RecordingRunner, lock_store: FakeLockStore
) -> None:
    """A capture starts while the lock store answers nothing.

    Why:
        `contracts/site-lock.md` states that an unreachable lock store still lets
        a capture start, because only an upgrade writes firmware. The fail-closed
        503 belongs to the upgrade path alone.

    Args:
        client: The signed-in test client of the first operator.
        capture_runner: The stand-in that receives the capture job.
        lock_store: The stand-in store that both lock seams share.
    """
    lock_store.fail = True  # Every command of the store now raises.
    answer = start_capture(client)  # The read and the grant both fail, and the start continues.
    assert_capture_started(answer, capture_runner, 1)  # The capture still runs.
