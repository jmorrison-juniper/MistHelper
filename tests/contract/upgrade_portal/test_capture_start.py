"""Contract test of `POST /api/sites/<site_id>/captures`.

Why:
    `contracts/http-api.md` fixes the start of a capture as one post that
    answers at once. The portal must not hold the browser open while it reads a
    whole site, so the route answers 202 and the reading runs on another thread.
    `tasks.md` T058 names two refusals for this route: `bad_tier` and
    `site_not_found`. This module pins both, pins the 202 body, and pins the
    rule that a refused request starts no work at all.

Why the tests inject a runner:
    The reading work belongs to other modules of this phase. This module tests
    the route, so it injects a stand-in runner and asserts that the route hands
    the job over. No test reaches the Mist cloud and no test opens a socket.
"""

from __future__ import annotations

import threading  # Proves that the work left the request thread.
from collections.abc import Iterator  # The return type of each generator fixture.
from typing import Any  # A portal answer and an injected seam are both free-form.

import pytest
from flask import Flask
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from src.upgrade_portal.app.routes import capture as capture_routes
from src.upgrade_portal.runtime import identity

# --------------------------------------------------------------------------
# The contract values. Each one repeats a line of the specification.
# --------------------------------------------------------------------------

# WHY: `contracts/http-api.md` fixes this path. The blueprint holds no prefix.
START_PATH_TEMPLATE = "/api/sites/{site_id}/captures"

# WHY: The endpoint name that `factory.py` registers for the start route.
START_ENDPOINT = "capture.start_capture"

# WHY: The portal answers before the reading ends, so the code is 202.
ACCEPTED_STATUS = 202
BAD_REQUEST_STATUS = 400  # The body named a tier the portal does not read.
NOT_AUTHENTICATED_STATUS = 401  # No signed-in session.
NOT_FOUND_STATUS = 404  # No such site inside the chosen organization.
CONFLICT_STATUS = 409  # Another operator holds the site lock.
METHOD_NOT_ALLOWED_STATUS = 405  # The path accepts a post only.

# WHY: `tasks.md` T058 names these two codes for this route.
BAD_TIER_CODE = "bad_tier"
SITE_NOT_FOUND_CODE = "site_not_found"

# WHY: `contracts/http-api.md` names this code when the site lock is held.
SITE_LOCKED_CODE = "site_locked"
NOT_AUTHENTICATED_CODE = "not_authenticated"  # `identity.require_session` answers this code.
CSRF_MISSING_CODE = "csrf_missing"  # `security.py` answers this code for a post with no token.

# WHY: The two tiers the portal reads. Any other value is a refusal.
TIER_STANDARD = 2
TIER_EXTRA = 3
REFUSED_TIER = 5  # A whole number outside the two tiers.
REFUSED_TIER_TEXT = "two"  # A word where the contract asks for a number.

# WHY: The seam keys. A test injects a stand-in here and reaches no network.
MIST_READER_KEY = "MIST_READER"
LOCK_READER_KEY = "SITE_LOCK_READER"
RUNNER_KEY = "CAPTURE_RUNNER"

# WHY: The session field that `select.py` writes when the operator picks an
# organization. The capture routes read the same field.
SELECTED_ORG_SESSION_KEY = "selected_org_id"

PROBE_EMAIL = "probe.operator@example.invalid"  # A reserved domain, so no real address appears.
ABSENT_SITE_ID = "00000000-0000-0000-0000-0000000000dd"  # A site the organization does not hold.
LOCK_HOLDER_EMAIL = "other.operator@example.invalid"  # The operator that holds the site lock.

WORKER_WAIT_SECONDS = 5.0  # A generous wait, so a slow machine does not fail the test.

# WHY: The two readable names that the job must carry. `ScopedCloudSession`
# holds the organization name, and the shared `listOrgSites` payload holds the
# site name. A worker thread can read neither, so the route reads both.
EXPECTED_ORG_NAME = "Test Org"
EXPECTED_SITE_NAME = "Test Site"
SITES_PAYLOAD_KEY = "listOrgSites"  # The cloud read that answers the site record.


# --------------------------------------------------------------------------
# The stand-ins. Each one records what the route asked for.
# --------------------------------------------------------------------------


class ScopedCloudSession:
    """A cloud session that may act on one organization only.

    Why:
        `identity` reads the privileges of the cloud session to decide the scope
        of the operator. A stand-in keeps the scope in the test and keeps the
        cloud out of it.
    """

    def __init__(self, org_ids: tuple[str, ...]) -> None:
        """Record the organizations this session may act on.

        Args:
            org_ids: The organizations the operator may reach.
        """
        self.privileges = [{"scope": "org", "org_id": org_id, "name": "Test Org"} for org_id in org_ids]


class RecordingRunner:
    """A stand-in for the collection work, which records the job it received.

    Why:
        The route must hand the job to a worker and answer at once. This class
        proves both halves: it records the job, and it records the name of the
        thread that called it, which must differ from the request thread.
    """

    def __init__(self) -> None:
        """Start with no job and with the event unset."""
        self.jobs: list[dict[str, Any]] = []  # One entry for each start the route accepted.
        self.thread_names: list[str] = []  # The thread that ran each job.
        self.started = threading.Event()  # The test waits on this event, never on a sleep.

    def __call__(self, job: dict[str, Any]) -> None:
        """Record one job and release the waiting test.

        Args:
            job: The capture job the route built.
        """
        self.jobs.append(dict(job))  # A copy, so a later change in the route cannot rewrite history.
        self.thread_names.append(threading.current_thread().name)  # Proves the work left the request thread.
        self.started.set()  # The test may continue now.


class RecordingLockReader:
    """A stand-in for the site lock reader.

    Why:
        `runtime/lock.py` reads Redis. A contract test must reach no Redis
        server, so the holders live in the test.
    """

    def __init__(self, holders: dict[str, str] | None = None) -> None:
        """Record the lock holders this reader answers with.

        Args:
            holders: The address of the holder of each held site.
        """
        self.holders = holders or {}  # An empty index means every site is free.

    def __call__(self, org_id: str, site_ids: list[str]) -> dict[str, str | None]:
        """Answer the holder of each named site.

        Args:
            org_id: The organization that owns the sites.
            site_ids: The sites the route asked about.

        Returns:
            One entry for each held site.
        """
        return {site_id: self.holders[site_id] for site_id in site_ids if site_id in self.holders}


# --------------------------------------------------------------------------
# The fixtures.
# --------------------------------------------------------------------------


@pytest.fixture
def capture_runner() -> RecordingRunner:
    """Return the stand-in that receives every capture job.

    Returns:
        The recording runner.
    """
    return RecordingRunner()


@pytest.fixture
def wired_app(portal_app: Flask, fake_mist_api: Any, capture_runner: RecordingRunner) -> Flask:
    """Return the portal with every seam of the start route injected.

    Why:
        The route reads the site list, reads the site lock, and starts the
        collection. All three arrive through the configuration, so this fixture
        is the one point where a test binds them.

    Args:
        portal_app: The portal application under test.
        fake_mist_api: The in-memory cloud reader of the shared fixtures.
        capture_runner: The stand-in that receives the capture job.

    Returns:
        The wired application.
    """
    portal_app.config[MIST_READER_KEY] = fake_mist_api.read  # No socket, no cloud account.
    portal_app.config[LOCK_READER_KEY] = RecordingLockReader()  # Every site reads as free.
    portal_app.config[RUNNER_KEY] = capture_runner  # The route hands the job here.
    portal_app.config["WTF_CSRF_ENABLED"] = False  # The token has its own test below.
    return portal_app


@pytest.fixture
def start_client(wired_app: Flask) -> Iterator[FlaskClient]:
    """Yield a browser for the wired application.

    Args:
        wired_app: The portal with every seam injected.

    Yields:
        The test browser.
    """
    with wired_app.test_client() as client:
        yield client


@pytest.fixture
def owner(fake_org_id: str) -> Iterator[identity.SessionOwner]:
    """Register one signed-in operator and drop the record afterwards.

    Why:
        `identity.SESSION_REGISTRY` lives for the whole process. A test that
        leaves a record behind changes the next test, so the record goes at the
        end of every test.

    Args:
        fake_org_id: The organization the operator may act on.

    Yields:
        The registered owner.
    """
    record = identity.OperatorSession(
        owner=identity.build_owner(PROBE_EMAIL, identity.issue_browser_id()),
        cloud_session=ScopedCloudSession((fake_org_id,)),
        credential_mode=identity.CredentialMode.ENVIRONMENT_TOKEN,
    )
    identity.SESSION_REGISTRY.register(record)
    try:
        yield record.owner
    finally:
        identity.SESSION_REGISTRY.drop(record.owner.key)


# --------------------------------------------------------------------------
# The helpers.
# --------------------------------------------------------------------------


def sign_in_client(client: FlaskClient, owner: identity.SessionOwner, org_id: str) -> None:
    """Give one browser a signed-in session and a chosen organization.

    Why:
        The picker posts the organization, and a post needs a token. A contract
        test of the capture routes checks the capture routes only, so it writes
        the field and never drives the token check twice.

    Args:
        client: The test browser.
        owner: The registered owner.
        org_id: The organization the operator picked.
    """
    client.set_cookie(identity.BROWSER_ID_COOKIE, owner.browser_id)
    with client.session_transaction() as browser_session:
        browser_session[identity.SESSION_OWNER_KEY] = owner.key
        browser_session[SELECTED_ORG_SESSION_KEY] = org_id


def start_capture(client: FlaskClient, site_id: str, body: dict[str, Any] | None = None) -> TestResponse:
    """Post one capture start and return the answer.

    Args:
        client: The signed-in browser.
        site_id: The site the capture reads.
        body: The request body, or None to send no body at all.

    Returns:
        The portal answer.
    """
    path = START_PATH_TEMPLATE.format(site_id=site_id)
    return client.post(path, json=body) if body is not None else client.post(path)


def read_error_code(response: TestResponse) -> str:
    """Read the error code out of one refusal envelope.

    Args:
        response: The portal answer.

    Returns:
        The code inside the error envelope.
    """
    payload: dict[str, Any] = response.get_json()
    return str(payload["error"]["code"])


def read_paths_for_endpoint(app: Flask, endpoint: str) -> set[str]:
    """Return every path that one endpoint answers.

    Args:
        app: The portal application.
        endpoint: The endpoint name.

    Returns:
        The path rules bound to that endpoint.
    """
    return {rule.rule for rule in app.url_map.iter_rules() if rule.endpoint == endpoint}


def started_job(
    client: FlaskClient, owner: identity.SessionOwner, org_id: str, site_id: str, runner: RecordingRunner
) -> dict[str, Any]:
    """Sign in, start one capture, and return the job the worker received.

    Why:
        Three tests below read one field of the same job. One helper holds the
        sign-in, the post, and the wait, so each of those tests reads as one
        assertion about one field.

    Args:
        client: The test browser.
        owner: The registered owner.
        org_id: The organization the operator picked.
        site_id: The site the capture reads.
        runner: The stand-in that receives the job.

    Returns:
        The capture job that the route handed to the worker.
    """
    sign_in_client(client, owner, org_id)
    assert start_capture(client, site_id, {"tier": TIER_STANDARD}).status_code == ACCEPTED_STATUS
    assert runner.started.wait(WORKER_WAIT_SECONDS)
    return runner.jobs[0]


# --------------------------------------------------------------------------
# The registration of the route.
# --------------------------------------------------------------------------


def test_the_start_endpoint_is_registered(wired_app: Flask) -> None:
    """The portal binds the start endpoint to the path the contract names.

    Args:
        wired_app: The portal with every seam injected.
    """
    assert START_PATH_TEMPLATE.format(site_id="<site_id>") in read_paths_for_endpoint(wired_app, START_ENDPOINT)


def test_the_start_path_refuses_a_read(
    start_client: FlaskClient, owner: identity.SessionOwner, fake_org_id: str, fake_site_id: str
) -> None:
    """A get on the start path answers 405, because the contract names a post only.

    Args:
        start_client: The test browser.
        owner: The registered owner.
        fake_org_id: The chosen organization.
        fake_site_id: The site of that organization.
    """
    sign_in_client(start_client, owner, fake_org_id)
    answer = start_client.get(START_PATH_TEMPLATE.format(site_id=fake_site_id))
    assert answer.status_code == METHOD_NOT_ALLOWED_STATUS


# --------------------------------------------------------------------------
# The accepted start.
# --------------------------------------------------------------------------


def test_a_start_answers_accepted(
    start_client: FlaskClient, owner: identity.SessionOwner, fake_org_id: str, fake_site_id: str
) -> None:
    """The portal answers 202 and never waits for the reading to end.

    Args:
        start_client: The test browser.
        owner: The registered owner.
        fake_org_id: The chosen organization.
        fake_site_id: The site of that organization.
    """
    sign_in_client(start_client, owner, fake_org_id)
    answer = start_capture(start_client, fake_site_id, {"tier": TIER_STANDARD, "role": "pre"})
    assert answer.status_code == ACCEPTED_STATUS


def test_the_start_answer_names_the_capture(
    start_client: FlaskClient, owner: identity.SessionOwner, fake_org_id: str, fake_site_id: str
) -> None:
    """The 202 body carries a capture identifier that is not empty.

    Args:
        start_client: The test browser.
        owner: The registered owner.
        fake_org_id: The chosen organization.
        fake_site_id: The site of that organization.
    """
    sign_in_client(start_client, owner, fake_org_id)
    payload: dict[str, Any] = start_capture(start_client, fake_site_id, {"tier": TIER_STANDARD}).get_json()
    assert payload["capture_id"]


def test_the_start_answer_names_the_status_path(
    start_client: FlaskClient, owner: identity.SessionOwner, fake_org_id: str, fake_site_id: str
) -> None:
    """The 202 body carries the status path of the new capture.

    Why:
        `contracts/http-api.md` fixes the field `status_url` and fixes the shape
        `/api/captures/<id>/status`. The browser polls the value it reads here,
        so a wrong value stops every later poll.

    Args:
        start_client: The test browser.
        owner: The registered owner.
        fake_org_id: The chosen organization.
        fake_site_id: The site of that organization.
    """
    sign_in_client(start_client, owner, fake_org_id)
    payload: dict[str, Any] = start_capture(start_client, fake_site_id, {"tier": TIER_STANDARD}).get_json()
    assert payload["status_url"] == f"/api/captures/{payload['capture_id']}/status"


def test_a_start_with_no_body_reads_tier_two(
    start_client: FlaskClient,
    owner: identity.SessionOwner,
    fake_org_id: str,
    fake_site_id: str,
    capture_runner: RecordingRunner,
) -> None:
    """A start with no body reads tier 2, which the contract names as the default.

    Args:
        start_client: The test browser.
        owner: The registered owner.
        fake_org_id: The chosen organization.
        fake_site_id: The site of that organization.
        capture_runner: The stand-in that received the job.
    """
    sign_in_client(start_client, owner, fake_org_id)
    assert start_capture(start_client, fake_site_id).status_code == ACCEPTED_STATUS
    assert capture_runner.started.wait(WORKER_WAIT_SECONDS)
    assert capture_runner.jobs[0]["tier"] == TIER_STANDARD


def test_tier_three_is_accepted(
    start_client: FlaskClient,
    owner: identity.SessionOwner,
    fake_org_id: str,
    fake_site_id: str,
    capture_runner: RecordingRunner,
) -> None:
    """Tier 3 reaches the worker unchanged.

    Args:
        start_client: The test browser.
        owner: The registered owner.
        fake_org_id: The chosen organization.
        fake_site_id: The site of that organization.
        capture_runner: The stand-in that received the job.
    """
    sign_in_client(start_client, owner, fake_org_id)
    assert start_capture(start_client, fake_site_id, {"tier": TIER_EXTRA}).status_code == ACCEPTED_STATUS
    assert capture_runner.started.wait(WORKER_WAIT_SECONDS)
    assert capture_runner.jobs[0]["tier"] == TIER_EXTRA


def test_the_job_names_the_site(
    start_client: FlaskClient,
    owner: identity.SessionOwner,
    fake_org_id: str,
    fake_site_id: str,
    capture_runner: RecordingRunner,
) -> None:
    """The job carries the site of the path and the organization of the session.

    Args:
        start_client: The test browser.
        owner: The registered owner.
        fake_org_id: The chosen organization.
        fake_site_id: The site of that organization.
        capture_runner: The stand-in that received the job.
    """
    sign_in_client(start_client, owner, fake_org_id)
    start_capture(start_client, fake_site_id, {"tier": TIER_STANDARD})
    assert capture_runner.started.wait(WORKER_WAIT_SECONDS)
    assert capture_runner.jobs[0]["site_id"] == fake_site_id
    assert capture_runner.jobs[0]["org_id"] == fake_org_id


def test_the_collection_leaves_the_request_thread(
    start_client: FlaskClient,
    owner: identity.SessionOwner,
    fake_org_id: str,
    fake_site_id: str,
    capture_runner: RecordingRunner,
) -> None:
    """The reading runs on another thread, so the browser never waits for it.

    Why:
        FR-021 to FR-028 describe a read of a whole site. A site with many
        devices takes minutes, and a request that waits that long times out at
        the proxy. The 202 answer only holds when the work runs elsewhere.

    Args:
        start_client: The test browser.
        owner: The registered owner.
        fake_org_id: The chosen organization.
        fake_site_id: The site of that organization.
        capture_runner: The stand-in that received the job.
    """
    sign_in_client(start_client, owner, fake_org_id)
    start_capture(start_client, fake_site_id, {"tier": TIER_STANDARD})
    assert capture_runner.started.wait(WORKER_WAIT_SECONDS)
    assert capture_runner.thread_names[0] != threading.current_thread().name


# --------------------------------------------------------------------------
# The `bad_tier` refusal.
# --------------------------------------------------------------------------


def test_an_unknown_tier_is_refused(
    start_client: FlaskClient, owner: identity.SessionOwner, fake_org_id: str, fake_site_id: str
) -> None:
    """A tier outside 2 and 3 answers 400 `bad_tier`.

    Args:
        start_client: The test browser.
        owner: The registered owner.
        fake_org_id: The chosen organization.
        fake_site_id: The site of that organization.
    """
    sign_in_client(start_client, owner, fake_org_id)
    answer = start_capture(start_client, fake_site_id, {"tier": REFUSED_TIER})
    assert answer.status_code == BAD_REQUEST_STATUS
    assert read_error_code(answer) == BAD_TIER_CODE


def test_a_word_tier_is_refused(
    start_client: FlaskClient, owner: identity.SessionOwner, fake_org_id: str, fake_site_id: str
) -> None:
    """A tier that holds a word answers 400 `bad_tier` and never a fault page.

    Args:
        start_client: The test browser.
        owner: The registered owner.
        fake_org_id: The chosen organization.
        fake_site_id: The site of that organization.
    """
    sign_in_client(start_client, owner, fake_org_id)
    answer = start_capture(start_client, fake_site_id, {"tier": REFUSED_TIER_TEXT})
    assert answer.status_code == BAD_REQUEST_STATUS
    assert read_error_code(answer) == BAD_TIER_CODE


def test_a_refused_tier_starts_no_work(
    start_client: FlaskClient,
    owner: identity.SessionOwner,
    fake_org_id: str,
    fake_site_id: str,
    capture_runner: RecordingRunner,
) -> None:
    """A refused start hands no job to the worker.

    Why:
        A refusal that still starts the reading would take the site lock and
        would write a capture the operator never asked for.

    Args:
        start_client: The test browser.
        owner: The registered owner.
        fake_org_id: The chosen organization.
        fake_site_id: The site of that organization.
        capture_runner: The stand-in that received no job.
    """
    sign_in_client(start_client, owner, fake_org_id)
    start_capture(start_client, fake_site_id, {"tier": REFUSED_TIER})
    assert capture_runner.jobs == []


# --------------------------------------------------------------------------
# The `site_not_found` refusal.
# --------------------------------------------------------------------------


def test_a_site_outside_the_organization_is_refused(
    start_client: FlaskClient, owner: identity.SessionOwner, fake_org_id: str
) -> None:
    """A site the organization does not hold answers 404 `site_not_found`.

    Why:
        A stale link and a hand-typed path both reach this route. The check runs
        before the reading, so an operator cannot capture a site of another
        organization through a guessed identifier.

    Args:
        start_client: The test browser.
        owner: The registered owner.
        fake_org_id: The chosen organization.
    """
    sign_in_client(start_client, owner, fake_org_id)
    answer = start_capture(start_client, ABSENT_SITE_ID, {"tier": TIER_STANDARD})
    assert answer.status_code == NOT_FOUND_STATUS
    assert read_error_code(answer) == SITE_NOT_FOUND_CODE


def test_an_absent_site_starts_no_work(
    start_client: FlaskClient, owner: identity.SessionOwner, fake_org_id: str, capture_runner: RecordingRunner
) -> None:
    """A refused site hands no job to the worker.

    Args:
        start_client: The test browser.
        owner: The registered owner.
        fake_org_id: The chosen organization.
        capture_runner: The stand-in that received no job.
    """
    sign_in_client(start_client, owner, fake_org_id)
    start_capture(start_client, ABSENT_SITE_ID, {"tier": TIER_STANDARD})
    assert capture_runner.jobs == []


def test_a_start_with_no_chosen_organization_is_refused(
    start_client: FlaskClient, owner: identity.SessionOwner, fake_site_id: str
) -> None:
    """A session that picked no organization answers 404 `site_not_found`.

    Why:
        With no organization the portal cannot prove that the site belongs to
        the operator. The safe answer is the same refusal as an unknown site,
        because a different answer would tell the caller that the site exists.

    Args:
        start_client: The test browser.
        owner: The registered owner.
        fake_site_id: A site the session may not prove ownership of.
    """
    start_client.set_cookie(identity.BROWSER_ID_COOKIE, owner.browser_id)
    with start_client.session_transaction() as browser_session:
        browser_session[identity.SESSION_OWNER_KEY] = owner.key
    answer = start_capture(start_client, fake_site_id, {"tier": TIER_STANDARD})
    assert answer.status_code == NOT_FOUND_STATUS
    assert read_error_code(answer) == SITE_NOT_FOUND_CODE


# --------------------------------------------------------------------------
# The site lock and the session guard.
# --------------------------------------------------------------------------


def test_a_held_site_answers_site_locked(
    wired_app: Flask, owner: identity.SessionOwner, fake_org_id: str, fake_site_id: str, capture_runner: RecordingRunner
) -> None:
    """A site another operator holds answers 409 `site_locked` and starts no work.

    Args:
        wired_app: The portal with every seam injected.
        owner: The registered owner.
        fake_org_id: The chosen organization.
        fake_site_id: The site of that organization.
        capture_runner: The stand-in that received no job.
    """
    wired_app.config[LOCK_READER_KEY] = RecordingLockReader({fake_site_id: LOCK_HOLDER_EMAIL})
    with wired_app.test_client() as client:
        sign_in_client(client, owner, fake_org_id)
        answer = start_capture(client, fake_site_id, {"tier": TIER_STANDARD})
    assert answer.status_code == CONFLICT_STATUS
    assert read_error_code(answer) == SITE_LOCKED_CODE
    assert capture_runner.jobs == []


def test_a_start_with_no_session_is_refused(start_client: FlaskClient, fake_site_id: str) -> None:
    """A request with no signed-in session answers 401 `not_authenticated`.

    Args:
        start_client: A browser that never signed in.
        fake_site_id: The site of the path.
    """
    answer = start_capture(start_client, fake_site_id, {"tier": TIER_STANDARD})
    assert answer.status_code == NOT_AUTHENTICATED_STATUS
    assert read_error_code(answer) == NOT_AUTHENTICATED_CODE


def test_a_start_with_no_token_is_refused(
    portal_app: Flask, fake_mist_api: Any, owner: identity.SessionOwner, fake_org_id: str, fake_site_id: str
) -> None:
    """A post with no token answers 400 `csrf_missing`.

    Why:
        `security.py` registers the token check for every post, and `TESTING`
        does not switch it off. This test runs against the untouched portal, so
        it proves that the start route sits behind the check.

    Args:
        portal_app: The portal application, with the token check still on.
        fake_mist_api: The in-memory cloud reader.
        owner: The registered owner.
        fake_org_id: The chosen organization.
        fake_site_id: The site of that organization.
    """
    portal_app.config[MIST_READER_KEY] = fake_mist_api.read
    with portal_app.test_client() as client:
        sign_in_client(client, owner, fake_org_id)
        answer = start_capture(client, fake_site_id, {"tier": TIER_STANDARD})
    assert answer.status_code == BAD_REQUEST_STATUS
    assert read_error_code(answer) == CSRF_MISSING_CODE


# --------------------------------------------------------------------------
# The four job fields that only the request thread can read.
# --------------------------------------------------------------------------


def test_the_job_carries_the_signed_in_cloud_session(
    start_client: FlaskClient,
    owner: identity.SessionOwner,
    fake_org_id: str,
    fake_site_id: str,
    capture_runner: RecordingRunner,
) -> None:
    """The job holds the same cloud session object that the signed-in record holds.

    Why:
        A worker thread holds no request, so `identity` answers nothing there.
        Without this field every capture fails before it reads one device. The
        check compares identity, because the worker needs the live session.

    Args:
        start_client: The test browser.
        owner: The registered owner.
        fake_org_id: The chosen organization.
        fake_site_id: The site of that organization.
        capture_runner: The stand-in that received the job.
    """
    job = started_job(start_client, owner, fake_org_id, fake_site_id, capture_runner)
    record = identity.SESSION_REGISTRY.get(owner.key)  # The record that the `owner` fixture registered.
    assert record is not None  # The fixture registered it, so this record exists.
    assert job["cloud_session"] is record.cloud_session  # The live object, and never a copy of it.


def test_the_job_carries_both_readable_names(
    start_client: FlaskClient,
    owner: identity.SessionOwner,
    fake_org_id: str,
    fake_site_id: str,
    capture_runner: RecordingRunner,
) -> None:
    """The job carries the organization name and the site name.

    Why:
        The stored capture keeps both names for the later comparison. A worker
        thread can read neither name, so the route reads both and carries them.
        Without them a reader of a stored capture shows an identifier instead.

    Args:
        start_client: The test browser.
        owner: The registered owner.
        fake_org_id: The chosen organization.
        fake_site_id: The site of that organization.
        capture_runner: The stand-in that received the job.
    """
    job = started_job(start_client, owner, fake_org_id, fake_site_id, capture_runner)
    assert job["org_name"] == EXPECTED_ORG_NAME  # The name inside the privilege list of the session.
    assert job["site_name"] == EXPECTED_SITE_NAME  # The name inside the site record of the cloud read.


def test_the_job_falls_back_to_the_site_identifier(
    start_client: FlaskClient,
    owner: identity.SessionOwner,
    fake_mist_api: Any,
    fake_site_id: str,
    capture_runner: RecordingRunner,
) -> None:
    """A site record with no name leaves the identifier in the name field.

    Why:
        A site of the cloud may carry no name at all. The job must still hold a
        value there, because an empty name reads as a defect of the portal.

    Args:
        start_client: The test browser.
        owner: The registered owner.
        fake_mist_api: The in-memory cloud reader of the shared fixtures.
        fake_site_id: The site of that organization.
        capture_runner: The stand-in that received the job.
    """
    org_id = str(fake_mist_api.payloads[SITES_PAYLOAD_KEY][0]["org_id"])  # The organization of the canned record.
    fake_mist_api.payloads[SITES_PAYLOAD_KEY] = [{"id": fake_site_id, "org_id": org_id}]  # A record with no name.
    job = started_job(start_client, owner, org_id, fake_site_id, capture_runner)
    assert job["site_name"] == fake_site_id  # The identifier fills in when the record carries no name.


def test_a_job_with_no_signed_in_record_still_builds(wired_app: Flask, fake_org_id: str, fake_site_id: str) -> None:
    """`build_job` answers a whole job when no operator signed in.

    Why:
        The route guard refuses such a request, so this path never runs in the
        portal. A direct call must still answer, because a raise here would
        turn a plain refusal into a fault of the portal.

    Args:
        wired_app: The portal with every seam injected.
        fake_org_id: The organization of the canned record.
        fake_site_id: The site of the canned record.
    """
    site = {"id": fake_site_id, "name": EXPECTED_SITE_NAME}  # The record that `find_site` answers with.
    with wired_app.test_request_context():  # A request that carries no signed-in operator.
        job = capture_routes.build_job(site, fake_org_id, TIER_STANDARD, {})
    assert job["cloud_session"] is None  # No record, so the job carries no session.
    assert job["actor_email"] == ""  # No record, so the job carries no address.
    assert job["org_name"] == fake_org_id  # An empty privilege list leaves the identifier in place.
