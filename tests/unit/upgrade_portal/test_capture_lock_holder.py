"""The site lock rule of the capture start route.

Why:
    `capture.held_by_other` decides whether one capture may start while a site
    lock exists. The rule has two halves, and a test must hold both. The
    operator that holds the lock must take their own pre-check capture, because
    the documented journey asks that operator to take the lock first. A second
    operator must still read 409 `site_locked`. A presence-only test passes the
    second half and fails the first, so it blocks the primary journey.

The unreachable lock store:
    `contracts/site-lock.md:130` asks a read to continue when the lock store is
    unreachable. `contracts/site-lock.md:139` states that the lock does not gate
    a capture on its own, because a capture reads only. The tests below pin that
    choice, so a later change cannot make a capture need Redis by accident.

No network:
    Every seam of the start route arrives through the application configuration,
    so these tests reach no cloud, no Redis server, and no database.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

import threading  # The route hands each job to a worker thread, and the test waits on an event.
from collections.abc import Callable, Iterator  # Types the lock reader and each fixture that yields.
from contextlib import contextmanager  # Builds the request that a direct read of the rule needs.
from typing import Any  # A cloud payload, a capture job, and an injected seam are all free-form.

import pytest  # The test framework.
from flask import Flask, session  # The smallest application, and the signed session the rule reads.
from flask.testing import FlaskClient  # Drives a route with no server and no browser.
from werkzeug.test import TestResponse  # The answer that the test client returns.

from src.upgrade_portal.app.routes import capture  # The module under test.
from src.upgrade_portal.app.routes.select import (  # The real seam and session names.
    LOCK_READER_KEY,
    MIST_READER_KEY,
    SELECTED_ORG_KEY,
)
from src.upgrade_portal.runtime import identity  # The registry, the cookie name, and the session fields.

# --------------------------------------------------------------------------
# The fixed values. Each one repeats a line of the specification.
# --------------------------------------------------------------------------

ORG_ID = "00000000-0000-0000-0000-0000000000a1"  # The organization the operator picked.
SITE_ID = "00000000-0000-0000-0000-0000000000b2"  # The site the capture reads.

PROBE_EMAIL = "probe.operator@example.invalid"  # A reserved domain, so no real address appears.
OTHER_EMAIL = "other.operator@example.invalid"  # The second operator, who holds no session here.

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
# The stand-ins. Each one records what the route asked for.
# --------------------------------------------------------------------------


class RecordingRunner:
    """A stand-in for the collection work, which records the job it received.

    Why:
        A refusal must start no work at all. This class proves that half by
        holding an empty job list, and proves the accepted half by holding one
        job. The event lets the test wait on the worker instead of on a sleep.
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
        check when that read answers nothing, so this reader is what lets every
        test below reach the rule it means to test.

    Args:
        name: The cloud read the route asked for.
        **parameters: The call parameters, which this stand-in does not read.

    Returns:
        One site record for the site list read, or an empty list.
    """
    if name == SITES_READ:  # The one read that the start route performs.
        return [dict(SITE_RECORD)]  # A copy, so no test can change the shared record.
    return []  # Every other read answers nothing, because this route makes no other.


def lock_reader_that_names(holder: str) -> Callable[[str, list[str]], dict[str, str]]:
    """Build a site lock reader that names one holder for every site.

    Why:
        `capture.held_by_other` reads the lock through the `SITE_LOCK_READER`
        seam. A reader that names the current operator reproduces the exact gap
        that the primary journey hits, and a reader that names a second operator
        proves the refusal still stands.

    Args:
        holder: The address that the lock store reports for each site.

    Returns:
        The reader callable that the seam accepts.
    """

    def read(org_id: str, site_ids: list[str]) -> dict[str, str]:
        """Return the same holder for each site asked about.

        Args:
            org_id: The organization that owns the sites.
            site_ids: The sites to ask about.

        Returns:
            One entry for each site, all naming the same holder.
        """
        return dict.fromkeys(site_ids, holder)  # The organization plays no part in this stand-in.

    return read  # The test writes this callable into the application configuration.


def unreachable_lock_reader(org_id: str, site_ids: list[str]) -> dict[str, str]:
    """Act as a lock store that no request can reach.

    Why:
        `select.read_site_locks` absorbs the fault and answers an empty index.
        The tests below pin the behavior that follows that empty index, so a
        later change cannot make a capture need Redis by accident.

    Args:
        org_id: The organization that owns the sites.
        site_ids: The sites to ask about.

    Returns:
        Nothing, because this reader always raises.

    Raises:
        RuntimeError: Always, because the lock store cannot answer.
    """
    raise RuntimeError(f"the lock store cannot answer for {len(site_ids)} sites")  # The fault the reader absorbs.


# --------------------------------------------------------------------------
# The fixtures.
# --------------------------------------------------------------------------


@pytest.fixture
def capture_runner() -> RecordingRunner:
    """Return the stand-in that receives every capture job.

    Returns:
        A fresh recording runner, so no job survives from an earlier test.
    """
    return RecordingRunner()  # One runner for each test keeps every test independent.


@pytest.fixture
def portal_app(capture_runner: RecordingRunner) -> Flask:
    """Return a bare application that holds the capture blueprint alone.

    Why:
        A bare application holds no sibling blueprint and no request forgery
        guard, so no other route can change an answer. Every seam arrives
        through the same configuration the built portal reads.

    Args:
        capture_runner: The stand-in that receives the capture job.

    Returns:
        The application, ready for a test client.
    """
    app = Flask(__name__)  # The smallest application that can hold the blueprint.
    app.config.update(TESTING=True, SECRET_KEY=FAKE_SECRET, WTF_CSRF_ENABLED=False)  # Test settings alone.
    app.config[MIST_READER_KEY] = cloud_reader_with_one_site  # No socket, and no cloud account.
    app.config[LOCK_READER_KEY] = lock_reader_that_names("")  # Every site reads as free by default.
    app.config[capture.RUNNER_KEY] = capture_runner  # The route hands the job here instead of the cloud.
    app.register_blueprint(capture.capture_bp)  # The routes under test.
    return app  # Each test drives this application through a client.


@pytest.fixture
def registered_owner() -> Iterator[identity.SessionOwner]:
    """Register one operator and drop the record when the test ends.

    Why:
        The session guard reads the registry on every request, and the registry
        lives for the whole process. A leaked record would sign in a later test
        by accident, so the fixture clears it.

    Yields:
        The identity pair of the registered operator.
    """
    owner = identity.build_owner(PROBE_EMAIL, identity.issue_browser_id())  # The pair the guard checks.
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


@pytest.fixture
def client(portal_app: Flask, registered_owner: identity.SessionOwner) -> Iterator[FlaskClient]:
    """Return a signed-in client that already picked the organization.

    Args:
        portal_app: The application with every seam injected.
        registered_owner: The identity pair of the registered operator.

    Yields:
        The Flask test client, with the session held open.
    """
    with portal_app.test_client() as opened:  # The context manager holds the session across requests.
        opened.set_cookie(identity.BROWSER_ID_COOKIE, registered_owner.browser_id)  # Half of the guard.
        with opened.session_transaction() as browser_session:  # The other half of the guard.
            browser_session[identity.SESSION_OWNER_KEY] = registered_owner.key  # Names the registered owner.
            browser_session[SELECTED_ORG_KEY] = ORG_ID  # The picker writes this field.
        yield opened  # Every test below drives this client.


# --------------------------------------------------------------------------
# The helpers.
# --------------------------------------------------------------------------


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


def assert_capture_started(answer: TestResponse, runner: RecordingRunner) -> None:
    """Assert that one start answered 202 and handed exactly one job to a worker.

    Why:
        Both halves matter. A 202 with no job would mean the route answered and
        started nothing, so the operator would watch a bar that never moves.

    Args:
        answer: The portal answer.
        runner: The stand-in that receives every capture job.
    """
    assert answer.status_code == ACCEPTED_STATUS  # The route took the work.
    assert runner.started.wait(WORKER_WAIT_SECONDS)  # The worker thread ran, so no sleep is needed.
    assert len(runner.jobs) == 1  # Exactly one capture started, and never a second one.


# --------------------------------------------------------------------------
# The lock holder takes their own capture. This is the primary journey.
# --------------------------------------------------------------------------


def test_the_lock_holder_takes_their_own_capture(
    portal_app: Flask, client: FlaskClient, capture_runner: RecordingRunner, registered_owner: identity.SessionOwner
) -> None:
    """The operator that holds the site lock starts their own pre-check capture.

    Why:
        The documented journey asks one operator to take the site lock and then
        take the pre-check capture. A presence-only lock test refuses that
        operator their own capture with 409 `site_locked`, so the journey cannot
        finish. This test is the whole reason `held_by_other` exists here.

    Args:
        portal_app: The application that holds the lock reader seam.
        client: The signed-in test client.
        capture_runner: The stand-in that receives the capture job.
        registered_owner: The identity pair of the registered operator.
    """
    portal_app.config[LOCK_READER_KEY] = lock_reader_that_names(registered_owner.actor_email)  # The same operator.
    answer = start_capture(client)  # The lock exists, and this operator holds it.
    assert_capture_started(answer, capture_runner)  # The capture runs, so the journey finishes.


def test_the_lock_holder_reads_no_refusal_code(
    portal_app: Flask, client: FlaskClient, registered_owner: identity.SessionOwner
) -> None:
    """The lock holder never reads the code `site_locked` for their own site.

    Why:
        A status assertion alone would pass if a later change answered 202 with
        a refusal body. The operator reads the code, so the code is part of the
        journey and needs its own assertion.

    Args:
        portal_app: The application that holds the lock reader seam.
        client: The signed-in test client.
        registered_owner: The identity pair of the registered operator.
    """
    portal_app.config[LOCK_READER_KEY] = lock_reader_that_names(registered_owner.actor_email)  # The same operator.
    answer = start_capture(client)  # The lock exists, and this operator holds it.
    assert error_code(answer) != SITE_LOCKED_CODE  # The holder is the one operator the lock protects.


# --------------------------------------------------------------------------
# A second operator still reads the refusal. The fix corrects no more than it must.
# --------------------------------------------------------------------------


def test_a_second_operator_is_refused(portal_app: Flask, client: FlaskClient, capture_runner: RecordingRunner) -> None:
    """A site that another operator holds answers 409 `site_locked`.

    Why:
        The repair of the primary journey must not open the site to everybody.
        This test holds the half of the rule that already worked, so an
        over-correction that let every operator pass would fail here.

    Args:
        portal_app: The application that holds the lock reader seam.
        client: The signed-in test client.
        capture_runner: The stand-in that received no job.
    """
    portal_app.config[LOCK_READER_KEY] = lock_reader_that_names(OTHER_EMAIL)  # A different operator holds it.
    answer = start_capture(client)  # The lock check refuses this start.
    assert answer.status_code == CONFLICT_STATUS  # `contracts/http-api.md:138` fixes this status.
    assert error_code(answer) == SITE_LOCKED_CODE  # The same line fixes this code.
    assert capture_runner.jobs == []  # A refusal starts no work at all.


def test_a_free_site_starts_the_capture(client: FlaskClient, capture_runner: RecordingRunner) -> None:
    """A site that no operator holds starts the capture.

    Why:
        The default fixture names no holder. This test proves the plain path
        still works, so a failure in a test above points at the lock rule and
        never at the wiring.

    Args:
        client: The signed-in test client.
        capture_runner: The stand-in that receives the capture job.
    """
    answer = start_capture(client)  # No holder exists, so no refusal applies.
    assert_capture_started(answer, capture_runner)  # The capture runs.


# --------------------------------------------------------------------------
# The unreachable lock store. `contracts/site-lock.md:130` and `:139`.
# --------------------------------------------------------------------------


def test_an_unreachable_lock_store_still_starts_the_capture(
    portal_app: Flask, client: FlaskClient, capture_runner: RecordingRunner
) -> None:
    """A lock store that cannot answer does not stop a capture.

    Why:
        `contracts/site-lock.md:130` asks a read to continue when the store is
        unreachable, and `contracts/site-lock.md:139` states that the lock does
        not gate a capture on its own. A capture reads only. This test records
        that choice, so a later change cannot make a capture need Redis without
        first failing here and reading the reason.

    Args:
        portal_app: The application that holds the lock reader seam.
        client: The signed-in test client.
        capture_runner: The stand-in that receives the capture job.
    """
    portal_app.config[LOCK_READER_KEY] = unreachable_lock_reader  # Every read of the lock store raises.
    answer = start_capture(client)  # The reader absorbs the fault and answers an empty index.
    assert_capture_started(answer, capture_runner)  # A capture reads only, so it continues.


def test_a_missing_lock_module_still_starts_the_capture(
    portal_app: Flask, client: FlaskClient, capture_runner: RecordingRunner
) -> None:
    """A portal with no lock reader at all still starts a capture.

    Why:
        `select.read_site_locks` answers an empty index when no reader exists.
        The answer must match the unreachable store above, because both states
        mean the same thing: the portal knows no holder.

    Args:
        portal_app: The application that holds the lock reader seam.
        client: The signed-in test client.
        capture_runner: The stand-in that receives the capture job.
    """
    portal_app.config[LOCK_READER_KEY] = None  # An unset seam reads as no reader at all.
    answer = start_capture(client)  # No reader means no known holder.
    assert_capture_started(answer, capture_runner)  # The capture runs.


# --------------------------------------------------------------------------
# The rule itself, read directly.
# --------------------------------------------------------------------------


def test_held_by_other_names_the_second_operator(portal_app: Flask, registered_owner: identity.SessionOwner) -> None:
    """`held_by_other` answers the address of an operator that is not this one.

    Why:
        The route needs the address to decide, and a later change may want to
        show it. A direct read of the rule states the return value plainly, so
        the shape of the answer is pinned beside the status code.

    Args:
        portal_app: The application that holds the lock reader seam.
        registered_owner: The identity pair of the registered operator.
    """
    portal_app.config[LOCK_READER_KEY] = lock_reader_that_names(OTHER_EMAIL)  # A different operator holds it.
    with signed_request(portal_app, registered_owner):  # A request the rule can read the session in.
        assert capture.held_by_other(ORG_ID, SITE_ID) == OTHER_EMAIL  # The address of the other operator.


def test_held_by_other_passes_the_current_operator(portal_app: Flask, registered_owner: identity.SessionOwner) -> None:
    """`held_by_other` answers None when the current operator holds the lock.

    Why:
        None is the value that lets the route continue. A direct read states
        that plainly, so a reader of this rule needs no trip through the route
        to learn what the holder gets.

    Args:
        portal_app: The application that holds the lock reader seam.
        registered_owner: The identity pair of the registered operator.
    """
    portal_app.config[LOCK_READER_KEY] = lock_reader_that_names(registered_owner.actor_email)  # The same operator.
    with signed_request(portal_app, registered_owner):  # A request the rule can read the session in.
        assert capture.held_by_other(ORG_ID, SITE_ID) is None  # The holder passes the check.


def test_held_by_other_passes_an_unreachable_store(portal_app: Flask, registered_owner: identity.SessionOwner) -> None:
    """`held_by_other` answers None when the lock store cannot answer.

    Why:
        This is the documented fail-open choice, read at the rule itself. An
        unreachable store names no holder, so the capture continues. The
        docstring of `held_by_other` carries the reasoning and the two contract
        lines that ask for it.

    Args:
        portal_app: The application that holds the lock reader seam.
        registered_owner: The identity pair of the registered operator.
    """
    portal_app.config[LOCK_READER_KEY] = unreachable_lock_reader  # Every read of the lock store raises.
    with signed_request(portal_app, registered_owner):  # A request the rule can read the session in.
        assert capture.held_by_other(ORG_ID, SITE_ID) is None  # An unknown holder never refuses a read.


@contextmanager
def signed_request(app: Flask, owner: identity.SessionOwner) -> Iterator[None]:
    """Open one request that carries the signed session and the browser cookie.

    Why:
        `identity.current_owner` reads the session field and compares the stored
        browser identifier against the cookie of the request. A request context
        built by hand carries neither, so the rule would find no owner and a
        direct test would prove nothing.

    Args:
        app: The application under test.
        owner: The identity pair of the registered operator.

    Yields:
        Nothing. The body runs inside the request.
    """
    cookie = f"{identity.BROWSER_ID_COOKIE}={owner.browser_id}"  # The half of the guard that rides in a header.
    with app.test_request_context("/", environ_base={"HTTP_COOKIE": cookie}):  # The request the rule reads.
        session[identity.SESSION_OWNER_KEY] = owner.key  # The other half of the guard.
        session[SELECTED_ORG_KEY] = ORG_ID  # The organization the picker stored.
        yield  # The test body reads the rule here.
