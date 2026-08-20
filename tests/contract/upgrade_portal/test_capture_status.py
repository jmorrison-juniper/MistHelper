"""Contract test of `GET /api/captures/<capture_id>/status`.

Why:
    The browser polls this endpoint every 30 seconds while a capture runs. The
    portal sends no server-sent event, so this one body is the whole progress
    channel. `tasks.md` T059 names seven fields: `state`, `percent`, `sections`,
    `counts`, `partial_reasons`, `verified`, and `message`. A missing field
    stops the progress bar, the section list, or the result badge of the capture
    page, so this module pins every field and pins the six section names.

Why the tests start a real capture:
    The status of a capture only exists after a start. Each test below posts one
    start against an injected runner that records the job and does no reading.
    The capture therefore rests in its first state, which is the state the page
    paints first.
"""

from __future__ import annotations

import threading  # The runner records the thread, and the test waits on an event.
from collections.abc import Iterator  # The return type of each generator fixture.
from typing import Any  # A portal answer and an injected seam are both free-form.

import pytest
from flask import Flask
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from src.upgrade_portal.runtime import identity

# --------------------------------------------------------------------------
# The contract values. Each one repeats a line of the specification.
# --------------------------------------------------------------------------

START_PATH_TEMPLATE = "/api/sites/{site_id}/captures"  # The start of one capture.
STATUS_PATH_TEMPLATE = "/api/captures/{capture_id}/status"  # The poll target.
STATUS_ENDPOINT = "capture.capture_status"  # The endpoint name of the status route.

OK_STATUS = 200  # The status read succeeded.
NOT_FOUND_STATUS = 404  # No such capture.
ACCEPTED_STATUS = 202  # The start answered before the reading ended.

CAPTURE_NOT_FOUND_CODE = "capture_not_found"  # The refusal of an unknown identifier.

# WHY: `tasks.md` T059 names these seven fields, and the capture page paints
# each one. A missing field breaks the page and breaks the poll.
STATUS_FIELDS = ("state", "percent", "sections", "counts", "partial_reasons", "verified", "message")

# WHY: `contracts/http-api.md` lists these six section names in the status body,
# and `capture/capture.html` renders one row for each name.
SECTION_NAMES = ("devices", "clients_wired", "clients_wireless", "clients_guest", "extras", "alarms")

# WHY: `data-model.md` fixes the five states a running capture passes through,
# and fixes the three states it ends in.
KNOWN_STATES = ("pending", "collecting", "assembling", "writing", "verified", "partial", "write_failed", "failed")

SKIPPED_STATE = "skipped"  # A section that this tier does not read.
VERIFIED_STATE = "verified"  # The capture came back from the store unchanged.

TIER_STANDARD = 2  # Tier 2 reads no extra data, so `extras` is skipped.
TIER_EXTRA = 3  # Tier 3 reads the extra data as well.

LOWEST_PERCENT = 0  # The progress never falls below zero.
HIGHEST_PERCENT = 100  # The progress never passes one hundred.

MIST_READER_KEY = "MIST_READER"  # The seam for every cloud read.
LOCK_READER_KEY = "SITE_LOCK_READER"  # The seam for the site lock.
RUNNER_KEY = "CAPTURE_RUNNER"  # The seam for the collection work.
LOADER_KEY = "CAPTURE_LOADER"  # The seam for the stored capture read.

SELECTED_ORG_SESSION_KEY = "selected_org_id"  # The organization the operator picked.
PROBE_EMAIL = "probe.operator@example.invalid"  # A reserved domain, so no real address appears.
ABSENT_CAPTURE_ID = "cap-00000000-99"  # An identifier the portal never issued.

WORKER_WAIT_SECONDS = 5.0  # A generous wait, so a slow machine does not fail the test.

# WHY: The shape of one stored capture, cut down to the fields the status route
# reads. `data-model.md` fixes every name below.
STORED_CAPTURE: dict[str, Any] = {
    "capture_id": "cap-abcdef12-01",
    "schema_version": 1,
    "capture_status": VERIFIED_STATE,
    "partial_reasons": [],
    "counts": {"devices_total": 3, "clients_wireless": 7},
    "stored_size_bytes": 4096,
}


# --------------------------------------------------------------------------
# The stand-ins.
# --------------------------------------------------------------------------


class ScopedCloudSession:
    """A cloud session that may act on one organization only."""

    def __init__(self, org_ids: tuple[str, ...]) -> None:
        """Record the organizations this session may act on.

        Args:
            org_ids: The organizations the operator may reach.
        """
        self.privileges = [{"scope": "org", "org_id": org_id, "name": "Test Org"} for org_id in org_ids]


class RecordingRunner:
    """A stand-in for the collection work, which reads nothing at all.

    Why:
        The status route must answer while the reading still runs. A runner that
        records the job and returns leaves the capture in its first state, which
        is the state the page paints first.
    """

    def __init__(self) -> None:
        """Start with no job and with the event unset."""
        self.jobs: list[dict[str, Any]] = []  # One entry for each start the route accepted.
        self.started = threading.Event()  # The test waits on this event, never on a sleep.

    def __call__(self, job: dict[str, Any]) -> None:
        """Record one job and release the waiting test.

        Args:
            job: The capture job the route built.
        """
        self.jobs.append(dict(job))
        self.started.set()


class StoredLoad:
    """The answer of the stored capture reader.

    Why:
        `capture/store.py` answers with a record that holds the document, a flag
        that reports whether the document is fit to compare, and a reason. This
        stand-in holds the same three names, so the route needs no second shape.
    """

    def __init__(self, capture: dict[str, Any] | None, comparable: bool, reason: str) -> None:
        """Record one stored capture read.

        Args:
            capture: The stored document, or None when no document exists.
            comparable: True when the portal read the key back unchanged.
            reason: The refusal code, or an empty string after a clean read.
        """
        self.capture = capture
        self.comparable = comparable
        self.reason = reason


class RecordingLoader:
    """A stand-in for the stored capture reader.

    Why:
        A worker restart empties the progress store. The status route then reads
        the stored capture instead, so the operator still sees the result of a
        capture that ended before the restart.
    """

    def __init__(self, load: StoredLoad) -> None:
        """Record the answer this reader gives.

        Args:
            load: The answer for every identifier.
        """
        self.load = load
        self.asked: list[str] = []  # The identifiers the route asked about.

    def __call__(self, capture_id: str) -> StoredLoad:
        """Answer one stored capture read.

        Args:
            capture_id: The capture the route asked about.

        Returns:
            The recorded answer.
        """
        self.asked.append(capture_id)
        return self.load


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
    """Return the portal with every seam of the capture routes injected.

    Args:
        portal_app: The portal application under test.
        fake_mist_api: The in-memory cloud reader of the shared fixtures.
        capture_runner: The stand-in that receives the capture job.

    Returns:
        The wired application.
    """
    portal_app.config[MIST_READER_KEY] = fake_mist_api.read
    portal_app.config[LOCK_READER_KEY] = lambda org_id, site_ids: {}  # Every site reads as free.
    portal_app.config[RUNNER_KEY] = capture_runner
    # WHY: without this seam the route falls back to the real store, which opens
    # a database connection. A contract test must reach no server, so the empty
    # store answers here and each test that needs a document injects its own.
    portal_app.config[LOADER_KEY] = RecordingLoader(StoredLoad(None, False, CAPTURE_NOT_FOUND_CODE))
    portal_app.config["WTF_CSRF_ENABLED"] = False  # The token check has its own contract test.
    return portal_app


@pytest.fixture
def status_client(wired_app: Flask) -> Iterator[FlaskClient]:
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

    Args:
        client: The test browser.
        owner: The registered owner.
        org_id: The organization the operator picked.
    """
    client.set_cookie(identity.BROWSER_ID_COOKIE, owner.browser_id)
    with client.session_transaction() as browser_session:
        browser_session[identity.SESSION_OWNER_KEY] = owner.key
        browser_session[SELECTED_ORG_SESSION_KEY] = org_id


def start_capture(client: FlaskClient, site_id: str, tier: int = TIER_STANDARD) -> str:
    """Start one capture and return its identifier.

    Args:
        client: The signed-in browser.
        site_id: The site the capture reads.
        tier: The data tier of the capture.

    Returns:
        The identifier of the new capture.
    """
    answer = client.post(START_PATH_TEMPLATE.format(site_id=site_id), json={"tier": tier})
    assert answer.status_code == ACCEPTED_STATUS
    payload: dict[str, Any] = answer.get_json()
    return str(payload["capture_id"])


def read_status(client: FlaskClient, capture_id: str) -> TestResponse:
    """Read the status of one capture.

    Args:
        client: The signed-in browser.
        capture_id: The capture to read.

    Returns:
        The portal answer.
    """
    return client.get(STATUS_PATH_TEMPLATE.format(capture_id=capture_id))


def status_body(client: FlaskClient, capture_id: str) -> dict[str, Any]:
    """Read the status body of one capture.

    Args:
        client: The signed-in browser.
        capture_id: The capture to read.

    Returns:
        The decoded status body.
    """
    answer = read_status(client, capture_id)
    assert answer.status_code == OK_STATUS
    payload: dict[str, Any] = answer.get_json()
    return payload


def started_status(client: FlaskClient, owner: identity.SessionOwner, org_id: str, site_id: str) -> dict[str, Any]:
    """Start one capture and read its first status body.

    Args:
        client: The test browser.
        owner: The registered owner.
        org_id: The organization the operator picked.
        site_id: The site the capture reads.

    Returns:
        The decoded status body.
    """
    sign_in_client(client, owner, org_id)
    return status_body(client, start_capture(client, site_id))


def read_error_code(response: TestResponse) -> str:
    """Read the error code out of one refusal envelope.

    Args:
        response: The portal answer.

    Returns:
        The code inside the error envelope.
    """
    payload: dict[str, Any] = response.get_json()
    return str(payload["error"]["code"])


# --------------------------------------------------------------------------
# The registration of the route.
# --------------------------------------------------------------------------


def test_the_status_endpoint_is_registered(wired_app: Flask) -> None:
    """The portal binds the status endpoint to the path the contract names.

    Args:
        wired_app: The portal with every seam injected.
    """
    paths = {rule.rule for rule in wired_app.url_map.iter_rules() if rule.endpoint == STATUS_ENDPOINT}
    assert STATUS_PATH_TEMPLATE.format(capture_id="<capture_id>") in paths


# --------------------------------------------------------------------------
# The seven fields.
# --------------------------------------------------------------------------


def test_the_status_body_holds_every_field(
    status_client: FlaskClient, owner: identity.SessionOwner, fake_org_id: str, fake_site_id: str
) -> None:
    """The body carries all seven fields that `tasks.md` T059 names.

    Args:
        status_client: The test browser.
        owner: The registered owner.
        fake_org_id: The chosen organization.
        fake_site_id: The site of that organization.
    """
    body = started_status(status_client, owner, fake_org_id, fake_site_id)
    assert set(STATUS_FIELDS) <= set(body)


def test_the_status_body_names_the_capture(
    status_client: FlaskClient, owner: identity.SessionOwner, fake_org_id: str, fake_site_id: str
) -> None:
    """The body names the capture it describes, as the contract sample shows.

    Args:
        status_client: The test browser.
        owner: The registered owner.
        fake_org_id: The chosen organization.
        fake_site_id: The site of that organization.
    """
    sign_in_client(status_client, owner, fake_org_id)
    capture_id = start_capture(status_client, fake_site_id)
    assert status_body(status_client, capture_id)["capture_id"] == capture_id


def test_the_state_is_a_known_state(
    status_client: FlaskClient, owner: identity.SessionOwner, fake_org_id: str, fake_site_id: str
) -> None:
    """The state holds one of the names that `data-model.md` fixes.

    Args:
        status_client: The test browser.
        owner: The registered owner.
        fake_org_id: The chosen organization.
        fake_site_id: The site of that organization.
    """
    assert started_status(status_client, owner, fake_org_id, fake_site_id)["state"] in KNOWN_STATES


def test_the_percent_stays_inside_the_scale(
    status_client: FlaskClient, owner: identity.SessionOwner, fake_org_id: str, fake_site_id: str
) -> None:
    """The percent is a whole number between zero and one hundred.

    Why:
        The progress bar of the capture page writes this value into an ARIA
        value that names zero and one hundred as its limits. A value outside the
        scale paints a bar that runs past the track.

    Args:
        status_client: The test browser.
        owner: The registered owner.
        fake_org_id: The chosen organization.
        fake_site_id: The site of that organization.
    """
    percent = started_status(status_client, owner, fake_org_id, fake_site_id)["percent"]
    assert isinstance(percent, int)
    assert LOWEST_PERCENT <= percent <= HIGHEST_PERCENT


def test_the_sections_map_holds_every_section(
    status_client: FlaskClient, owner: identity.SessionOwner, fake_org_id: str, fake_site_id: str
) -> None:
    """The sections map holds one entry for each of the six section names.

    Why:
        The capture page renders one row for each name. A missing key paints an
        empty row, and the operator then cannot tell a pending section from a
        section the portal forgot.

    Args:
        status_client: The test browser.
        owner: The registered owner.
        fake_org_id: The chosen organization.
        fake_site_id: The site of that organization.
    """
    sections = started_status(status_client, owner, fake_org_id, fake_site_id)["sections"]
    assert set(SECTION_NAMES) <= set(sections)


def test_tier_two_skips_the_extra_sections(
    status_client: FlaskClient, owner: identity.SessionOwner, fake_org_id: str, fake_site_id: str
) -> None:
    """Tier 2 marks the extra sections as skipped, as the contract sample shows.

    Args:
        status_client: The test browser.
        owner: The registered owner.
        fake_org_id: The chosen organization.
        fake_site_id: The site of that organization.
    """
    sign_in_client(status_client, owner, fake_org_id)
    sections = status_body(status_client, start_capture(status_client, fake_site_id, TIER_STANDARD))["sections"]
    assert sections["extras"] == SKIPPED_STATE


def test_tier_three_does_not_skip_the_extra_sections(
    status_client: FlaskClient, owner: identity.SessionOwner, fake_org_id: str, fake_site_id: str
) -> None:
    """Tier 3 reads the extra sections, so it never marks them skipped.

    Args:
        status_client: The test browser.
        owner: The registered owner.
        fake_org_id: The chosen organization.
        fake_site_id: The site of that organization.
    """
    sign_in_client(status_client, owner, fake_org_id)
    sections = status_body(status_client, start_capture(status_client, fake_site_id, TIER_EXTRA))["sections"]
    assert sections["extras"] != SKIPPED_STATE


def test_the_counts_are_whole_numbers(
    status_client: FlaskClient, owner: identity.SessionOwner, fake_org_id: str, fake_site_id: str
) -> None:
    """The counts map holds a whole number under every key.

    Args:
        status_client: The test browser.
        owner: The registered owner.
        fake_org_id: The chosen organization.
        fake_site_id: The site of that organization.
    """
    counts = started_status(status_client, owner, fake_org_id, fake_site_id)["counts"]
    assert isinstance(counts, dict)
    assert all(isinstance(value, int) for value in counts.values())


def test_the_partial_reasons_are_a_list(
    status_client: FlaskClient, owner: identity.SessionOwner, fake_org_id: str, fake_site_id: str
) -> None:
    """A capture that lost no section carries an empty reason list.

    Args:
        status_client: The test browser.
        owner: The registered owner.
        fake_org_id: The chosen organization.
        fake_site_id: The site of that organization.
    """
    assert started_status(status_client, owner, fake_org_id, fake_site_id)["partial_reasons"] == []


def test_a_running_capture_is_not_verified(
    status_client: FlaskClient, owner: identity.SessionOwner, fake_org_id: str, fake_site_id: str
) -> None:
    """The verified flag holds false until the portal reads the key back.

    Why:
        FR-030 states that a capture counts as verified only after the portal
        reads the stored key back and compares it. A flag that reads true too
        early would let a comparison run on data that never reached the store.

    Args:
        status_client: The test browser.
        owner: The registered owner.
        fake_org_id: The chosen organization.
        fake_site_id: The site of that organization.
    """
    assert started_status(status_client, owner, fake_org_id, fake_site_id)["verified"] is False


def test_the_message_is_text(
    status_client: FlaskClient, owner: identity.SessionOwner, fake_org_id: str, fake_site_id: str
) -> None:
    """The message holds text, because the page prints it without a change.

    Args:
        status_client: The test browser.
        owner: The registered owner.
        fake_org_id: The chosen organization.
        fake_site_id: The site of that organization.
    """
    assert isinstance(started_status(status_client, owner, fake_org_id, fake_site_id)["message"], str)


# --------------------------------------------------------------------------
# The stored capture, and the unknown capture.
# --------------------------------------------------------------------------


def test_a_stored_capture_reads_as_verified(wired_app: Flask, owner: identity.SessionOwner, fake_org_id: str) -> None:
    """A capture that ended before a restart still reports its result.

    Why:
        The progress store lives in the worker process only. After a restart the
        status route reads the stored capture instead, so the operator sees the
        result of a capture the portal already finished.

    Args:
        wired_app: The portal with every seam injected.
        owner: The registered owner.
        fake_org_id: The chosen organization.
    """
    wired_app.config[LOADER_KEY] = RecordingLoader(StoredLoad(dict(STORED_CAPTURE), True, ""))
    with wired_app.test_client() as client:
        sign_in_client(client, owner, fake_org_id)
        body = status_body(client, str(STORED_CAPTURE["capture_id"]))
    assert body["state"] == VERIFIED_STATE
    assert body["verified"] is True


def test_an_unknown_capture_is_refused(
    status_client: FlaskClient, owner: identity.SessionOwner, fake_org_id: str
) -> None:
    """An identifier the portal never issued answers 404 `capture_not_found`.

    Args:
        status_client: The test browser.
        owner: The registered owner.
        fake_org_id: The chosen organization.
    """
    sign_in_client(status_client, owner, fake_org_id)
    answer = read_status(status_client, ABSENT_CAPTURE_ID)
    assert answer.status_code == NOT_FOUND_STATUS
    assert read_error_code(answer) == CAPTURE_NOT_FOUND_CODE


def test_a_status_read_with_no_session_is_refused(status_client: FlaskClient) -> None:
    """A poll with no signed-in session answers 401 `not_authenticated`.

    Args:
        status_client: A browser that never signed in.
    """
    assert read_status(status_client, ABSENT_CAPTURE_ID).status_code == 401
