"""Contract test of the lock grant in the capture start answer (#2108).

Why:
    `contracts/remaining-defects-deltas.md` Delta H1 adds a ``lock`` object to the
    202 answer of ``POST /api/sites/<site_id>/captures``. The browser reads that
    object to repaint the lock banner and to start the renewal beat, with no
    reload (FR-107, FR-110). Before this change the answer carried no grant, so
    the banner still showed the take control after a start held the site. These
    tests pin the grant on a take, the absence of a grant on a renewal and on a
    refusal, and the empty run value the record stores (FR-112).

Scope:
    ``POST /api/sites/<site_id>/captures`` alone. The grant shape matches the
    answer of the lock endpoint, because the route reuses one serializer.

No network:
    The lock reader and the lock store are the same stand-in, so a read and a
    write always agree. These tests reach no cloud, no Redis server, and no
    database.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

import threading  # The route hands each job to a worker thread, and a test waits on the count.
import time  # A short poll waits for the worker without a fixed sleep.
from collections.abc import Callable, Iterator  # Types the lock reader and each generator fixture.
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
from src.upgrade_portal.runtime import identity, lock  # The registry, the session fields, and the record.
from tests.support.lock_store_double import FakeLockStore  # The store stand-in that every test below shares.

# --------------------------------------------------------------------------
# The fixed values. Each one repeats a line of the specification.
# --------------------------------------------------------------------------

ORG_ID = "00000000-0000-0000-0000-0000000000a1"  # The organization the operator picked.
SITE_ID = "00000000-0000-0000-0000-0000000000b2"  # The site the capture reads.
SITE_KEY = f"misthelper:lock:site:{ORG_ID}:{SITE_ID}"  # The key `build_key` writes for this pair.

FIRST_EMAIL = "first.operator@example.invalid"  # A reserved domain, so no real address appears.
SECOND_EMAIL = "second.operator@example.invalid"  # The operator that arrives after the lock exists.

FAKE_SECRET = "test-secret-value-for-session-signing"  # Signs the browser session in the test only.

START_PATH = f"/api/sites/{SITE_ID}/captures"  # `contracts/http-api.md` fixes this path.
SITES_READ = "listOrgSites"  # The cloud read that answers the site record.

ACCEPTED_STATUS = 202  # The portal took the work and answered before the read ended.
CONFLICT_STATUS = 409  # Another operator holds the site lock.

TIER_STANDARD = 2  # The device state and the client lists.
WORKER_WAIT_SECONDS = 5.0  # A generous wait, so a slow machine does not fail the test.
POLL_SECONDS = 0.02  # A short pause between two reads of the job count.

ACQUIRED_STATE = "acquired"  # A free site grants this state, never a resume and never a takeover.
LOCK_FIELD = "lock"  # Delta H1 names the grant object with this key.
TOKEN_FIELD = "lock_token"  # The browser sends this value back with every beat.
LIFE_FIELD = "expires_in"  # The seconds the lock lives without a beat.
STATE_FIELD = "state"  # One of `acquired`, `resume`, or `takeover`.

SITE_RECORD: dict[str, Any] = {"id": SITE_ID, "name": "Probe site", "org_id": ORG_ID}  # The one site.


# --------------------------------------------------------------------------
# The stand-ins.
# --------------------------------------------------------------------------


class RecordingRunner:
    """A stand-in for the collection work, which records each job it received.

    Why:
        A renewal must still start the work, and a refusal must start none. This
        class counts the jobs, and a poll lets a test wait on the count instead
        of on a fixed sleep.

    Attributes:
        jobs: One entry for each start the route accepted.
        lock_guard: One guard, so the worker thread and the test never race.
    """

    def __init__(self) -> None:
        """Start with no job and with a fresh guard."""
        self.jobs: list[dict[str, Any]] = []  # One entry for each start the route accepted.
        self.lock_guard = threading.Lock()  # The worker appends under this guard.

    def __call__(self, job: dict[str, Any]) -> None:
        """Record one job under the guard.

        Args:
            job: The capture job that the start route built.
        """
        with self.lock_guard:  # The append and the later read never overlap.
            self.jobs.append(dict(job))  # A copy, so a later change in the route cannot rewrite history.

    def count(self) -> int:
        """Return how many jobs the worker holds now.

        Returns:
            The job count, read under the guard.
        """
        with self.lock_guard:  # The read never overlaps an append.
            return len(self.jobs)  # The number of accepted starts so far.

    def wait_for(self, target: int) -> bool:
        """Wait until the worker holds at least the wanted job count.

        Args:
            target: The job count the test needs.

        Returns:
            True when the count arrived before the deadline.
        """
        deadline = time.monotonic() + WORKER_WAIT_SECONDS  # A generous wait, so a slow machine still passes.
        while time.monotonic() < deadline:  # The loop ends on the count or on the deadline.
            if self.count() >= target:  # The worker ran, so no fixed sleep is needed.
                return True  # The wanted jobs arrived.
            time.sleep(POLL_SECONDS)  # A short pause keeps the loop cheap.
        return False  # The deadline passed with too few jobs.


def cloud_reader_with_one_site(name: str, **parameters: Any) -> list[dict[str, Any]]:
    """Answer the site list of the test organization, and answer nothing else.

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
    yield from register_owner(SECOND_EMAIL)  # A second address and browser, so the pair differs.


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


def start_capture(client: FlaskClient, body: dict[str, Any] | None = None) -> TestResponse:
    """Post one capture start of the test site and return the answer.

    Args:
        client: The signed-in browser.
        body: The request body, or None for the default tier body.

    Returns:
        The portal answer.
    """
    payload = body if body is not None else {"tier": TIER_STANDARD}  # The default tier of the contract.
    return client.post(START_PATH, json=payload)  # The one start of the test site.


def answer_body(answer: TestResponse) -> dict[str, Any]:
    """Read the JSON body of one answer as a dictionary.

    Args:
        answer: The portal answer.

    Returns:
        The body, or an empty index when the body carries another shape.
    """
    body: Any = answer.get_json(silent=True) or {}  # A body of another shape reads as an empty index.
    return dict(body)  # A copy keeps a caller edit out of the framework buffer.


# --------------------------------------------------------------------------
# The grant. This is the defect of issue #2108.
# --------------------------------------------------------------------------


def test_a_capture_start_answer_carries_the_lock_grant(
    client: FlaskClient,
    capture_runner: RecordingRunner,
    first_owner: identity.SessionOwner,
) -> None:
    """A capture start on a free site answers 202 with the lock grant.

    Why:
        Delta H1 adds the grant so the browser repaints the banner and starts the
        beat with no reload. FR-109 asks for the grant on a start that took the
        lock.

    Args:
        client: The signed-in test client of the first operator.
        capture_runner: The stand-in that receives the capture job.
        first_owner: The identity pair of the first operator.
    """
    answer = start_capture(client)  # The site is free, so the start takes the lock.
    assert answer.status_code == ACCEPTED_STATUS  # The route took the work.
    assert capture_runner.wait_for(1)  # The worker ran, so no sleep is needed.
    body = answer_body(answer)  # The grant lives inside the 202 body.
    grant: Any = body.get(LOCK_FIELD) or {}  # Delta H1 nests the grant under this one key.
    assert grant.get(TOKEN_FIELD)  # The browser needs a token for every later beat.
    assert isinstance(grant.get(LIFE_FIELD), int)  # The countdown needs the seconds left as a number.
    assert grant.get(STATE_FIELD) == ACQUIRED_STATE  # A free site grants the acquired state.


def test_a_second_start_by_the_holder_carries_no_grant(
    client: FlaskClient,
    capture_runner: RecordingRunner,
    first_owner: identity.SessionOwner,
) -> None:
    """The holder starts a second capture, and the answer carries no grant.

    Why:
        Delta H1 adds the grant only when the start took the lock on this call. A
        renewal keeps a lock the browser already holds, so the answer holds no
        grant and the browser needs no repaint.

    Args:
        client: The signed-in test client of the first operator.
        capture_runner: The stand-in that receives the capture job.
        first_owner: The identity pair of the first operator.
    """
    first = start_capture(client)  # The first start takes the lock.
    assert first.status_code == ACCEPTED_STATUS  # The take answered 202.
    assert capture_runner.wait_for(1)  # The first worker ran.
    second = start_capture(client)  # The same browser starts again, so the lock only renews.
    assert second.status_code == ACCEPTED_STATUS  # The renewal still starts the work.
    assert capture_runner.wait_for(2)  # The second worker ran too.
    assert LOCK_FIELD not in answer_body(second)  # A renewal took no lock, so it carries no grant.


def test_a_refused_start_carries_no_grant(
    portal_app: Flask,
    client: FlaskClient,
    capture_runner: RecordingRunner,
    first_owner: identity.SessionOwner,
    second_owner: identity.SessionOwner,
) -> None:
    """A second operator reads 409, and the refusal carries no grant.

    Why:
        Delta H1 changes the success answer alone. A refusal must leave the site
        exactly as it found it and must name no false hold, so it carries no
        grant object.

    Args:
        portal_app: The application with every seam injected.
        client: The signed-in test client of the first operator.
        capture_runner: The stand-in that receives the capture job.
        first_owner: The identity pair of the first operator.
        second_owner: The identity pair of the second operator.
    """
    assert start_capture(client).status_code == ACCEPTED_STATUS  # The first operator takes the site.
    assert capture_runner.wait_for(1)  # The first worker ran.
    with signed_client(portal_app, second_owner) as rival:  # The second operator arrives after the lock exists.
        refusal = start_capture(rival)  # The site is held, so the second start stops.
    assert refusal.status_code == CONFLICT_STATUS  # The holder must end first.
    assert LOCK_FIELD not in answer_body(refusal)  # A refusal carries no grant object.


def test_a_start_with_a_null_run_stores_an_empty_run(
    client: FlaskClient,
    capture_runner: RecordingRunner,
    lock_store: FakeLockStore,
    first_owner: identity.SessionOwner,
) -> None:
    """A start with a null run stores a lock record that holds an empty run.

    Why:
        FR-112 forbids the text ``None`` in a stored record. A body with a JSON
        null run once reached the record as that word, so the site list showed it
        to the next operator. The record must store an empty run instead.

    Args:
        client: The signed-in test client of the first operator.
        capture_runner: The stand-in that receives the capture job.
        lock_store: The stand-in store that both lock seams share.
        first_owner: The identity pair of the first operator.
    """
    answer = start_capture(client, {"tier": TIER_STANDARD, "run_id": None})  # A null run reaches the record.
    assert answer.status_code == ACCEPTED_STATUS  # The start still takes the lock.
    assert capture_runner.wait_for(1)  # The worker ran.
    record = lock.LockRecord.from_json(lock_store.values[SITE_KEY])  # The value the store now holds.
    assert record is not None  # A well-shaped record reads back, never None.
    assert record.run_id == ""  # FR-112 forbids the word None, so the record holds an empty run.
