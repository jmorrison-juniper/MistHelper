"""Contract test of `GET /api/captures/<capture_id>` and the capture page.

Why:
    The read route hands one whole capture document to the comparison work and
    to the download work. `tasks.md` T060 names the refusal `capture_not_found`.
    `contracts/http-api.md:176` names a second refusal on the same route:
    `409 capture_not_verified`, for a capture the portal never read back. Both
    refusals appear below, because a caller that receives an unverified document
    would compare data that may never have reached the store.

Why the page route sits here too:
    T086 pairs the read route with the human view at `GET /captures/<id>`. One
    module therefore pins both, so the page and the read answer for the same
    identifier and never drift apart.
"""

from __future__ import annotations

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

READ_PATH_TEMPLATE = "/api/captures/{capture_id}"  # The whole capture document.
PAGE_PATH_TEMPLATE = "/captures/{capture_id}"  # The human view of one capture.
READ_ENDPOINT = "capture.read_capture"  # The endpoint name of the read route.
PAGE_ENDPOINT = "capture.capture_page"  # The endpoint name of the page route.

OK_STATUS = 200  # The read succeeded.
NOT_AUTHENTICATED_STATUS = 401  # No signed-in session.
NOT_FOUND_STATUS = 404  # No such capture.
CONFLICT_STATUS = 409  # The portal never read the stored key back.
SERVER_ERROR_STATUS = 500  # The store did not answer at all.

# WHY: `tasks.md` T060 names the first code. `contracts/http-api.md:176` names
# the second code on the same route.
CAPTURE_NOT_FOUND_CODE = "capture_not_found"
CAPTURE_NOT_VERIFIED_CODE = "capture_not_verified"

# WHY: `capture/store.py` publishes these reasons, and each value repeats the
# error code of the route, so the route passes the reason straight on.
DATABASE_UNREACHABLE_REASON = "database_unreachable"

LOADER_KEY = "CAPTURE_LOADER"  # The seam for the stored capture read.
MIST_READER_KEY = "MIST_READER"  # The seam for every cloud read.

SELECTED_ORG_SESSION_KEY = "selected_org_id"  # The organization the operator picked.
PROBE_EMAIL = "probe.operator@example.invalid"  # A reserved domain, so no real address appears.

STORED_CAPTURE_ID = "cap-abcdef12-01"  # The identifier of the stored document below.
ABSENT_CAPTURE_ID = "cap-00000000-99"  # An identifier the portal never issued.

# WHY: The identifier of the progress region of `capture/capture.html`. The page
# always renders this region, so a test finds it before and after a capture.
PROGRESS_MARKER = 'data-testid="capture-progress"'

# WHY: The shape of one stored capture, cut down to the fields the read route
# hands on. `data-model.md` fixes every name below, and fixes the schema version
# as the whole number 1.
STORED_CAPTURE: dict[str, Any] = {
    "_key": STORED_CAPTURE_ID,
    "capture_id": STORED_CAPTURE_ID,
    "schema_version": 1,
    "run_id": "run-abcdef12",
    "ordinal": 1,
    "role": "pre",
    "tier": 2,
    "capture_status": "verified",
    "partial_reasons": [],
    "counts": {"devices_total": 3},
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
        The real reader reaches ArangoDB. A contract test must reach no database
        server, so the answer lives in the test and the route stays honest about
        the seam it calls.
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
def verified_loader() -> RecordingLoader:
    """Return a reader that answers with one verified capture.

    Returns:
        The recording reader.
    """
    return RecordingLoader(StoredLoad(dict(STORED_CAPTURE), True, ""))


@pytest.fixture
def wired_app(portal_app: Flask, fake_mist_api: Any, verified_loader: RecordingLoader) -> Flask:
    """Return the portal with the stored capture reader injected.

    Args:
        portal_app: The portal application under test.
        fake_mist_api: The in-memory cloud reader of the shared fixtures.
        verified_loader: The reader that answers with one verified capture.

    Returns:
        The wired application.
    """
    portal_app.config[MIST_READER_KEY] = fake_mist_api.read
    portal_app.config[LOADER_KEY] = verified_loader
    return portal_app


@pytest.fixture
def read_client(wired_app: Flask) -> Iterator[FlaskClient]:
    """Yield a browser for the wired application.

    Args:
        wired_app: The portal with the stored capture reader injected.

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


def read_capture(client: FlaskClient, capture_id: str) -> TestResponse:
    """Read one whole capture document.

    Args:
        client: The signed-in browser.
        capture_id: The capture to read.

    Returns:
        The portal answer.
    """
    return client.get(READ_PATH_TEMPLATE.format(capture_id=capture_id))


def open_page(client: FlaskClient, capture_id: str) -> TestResponse:
    """Open the human view of one capture.

    Args:
        client: The signed-in browser.
        capture_id: The capture to show.

    Returns:
        The portal answer.
    """
    return client.get(PAGE_PATH_TEMPLATE.format(capture_id=capture_id))


def read_error_code(response: TestResponse) -> str:
    """Read the error code out of one refusal envelope.

    Args:
        response: The portal answer.

    Returns:
        The code inside the error envelope.
    """
    payload: dict[str, Any] = response.get_json()
    return str(payload["error"]["code"])


def signed_in_client(app: Flask, owner: identity.SessionOwner, org_id: str) -> FlaskClient:
    """Return a browser that already carries a signed-in session.

    Args:
        app: The portal application.
        owner: The registered owner.
        org_id: The organization the operator picked.

    Returns:
        The signed-in browser.
    """
    client = app.test_client()
    sign_in_client(client, owner, org_id)
    return client


# --------------------------------------------------------------------------
# The registration of the two routes.
# --------------------------------------------------------------------------


def test_the_read_endpoint_is_registered(wired_app: Flask) -> None:
    """The portal binds the read endpoint to the path the contract names.

    Args:
        wired_app: The portal with the stored capture reader injected.
    """
    paths = {rule.rule for rule in wired_app.url_map.iter_rules() if rule.endpoint == READ_ENDPOINT}
    assert READ_PATH_TEMPLATE.format(capture_id="<capture_id>") in paths


def test_the_page_endpoint_is_registered(wired_app: Flask) -> None:
    """The portal binds the page endpoint to the path the contract names.

    Args:
        wired_app: The portal with the stored capture reader injected.
    """
    paths = {rule.rule for rule in wired_app.url_map.iter_rules() if rule.endpoint == PAGE_ENDPOINT}
    assert PAGE_PATH_TEMPLATE.format(capture_id="<capture_id>") in paths


# --------------------------------------------------------------------------
# The successful read.
# --------------------------------------------------------------------------


def test_a_verified_capture_reads_back(
    read_client: FlaskClient, owner: identity.SessionOwner, fake_org_id: str
) -> None:
    """A verified capture answers 200.

    Args:
        read_client: The test browser.
        owner: The registered owner.
        fake_org_id: The chosen organization.
    """
    sign_in_client(read_client, owner, fake_org_id)
    assert read_capture(read_client, STORED_CAPTURE_ID).status_code == OK_STATUS


def test_the_read_answers_the_whole_document(
    read_client: FlaskClient, owner: identity.SessionOwner, fake_org_id: str
) -> None:
    """The body carries the stored document, and not a summary of it.

    Why:
        The comparison work and the download work both read this body. A summary
        would force a second read for every field the summary dropped.

    Args:
        read_client: The test browser.
        owner: The registered owner.
        fake_org_id: The chosen organization.
    """
    sign_in_client(read_client, owner, fake_org_id)
    payload: dict[str, Any] = read_capture(read_client, STORED_CAPTURE_ID).get_json()
    assert payload["capture_id"] == STORED_CAPTURE_ID
    assert payload["schema_version"] == STORED_CAPTURE["schema_version"]
    assert payload["counts"] == STORED_CAPTURE["counts"]


def test_the_read_asks_the_store_for_the_named_capture(
    read_client: FlaskClient, owner: identity.SessionOwner, fake_org_id: str, verified_loader: RecordingLoader
) -> None:
    """The route asks the store for the identifier the path named.

    Args:
        read_client: The test browser.
        owner: The registered owner.
        fake_org_id: The chosen organization.
        verified_loader: The reader that recorded the question.
    """
    sign_in_client(read_client, owner, fake_org_id)
    read_capture(read_client, STORED_CAPTURE_ID)
    assert verified_loader.asked == [STORED_CAPTURE_ID]


# --------------------------------------------------------------------------
# The two refusals.
# --------------------------------------------------------------------------


def test_an_unknown_capture_is_refused(wired_app: Flask, owner: identity.SessionOwner, fake_org_id: str) -> None:
    """An identifier the store does not hold answers 404 `capture_not_found`.

    Args:
        wired_app: The portal with the stored capture reader injected.
        owner: The registered owner.
        fake_org_id: The chosen organization.
    """
    wired_app.config[LOADER_KEY] = RecordingLoader(StoredLoad(None, False, CAPTURE_NOT_FOUND_CODE))
    answer = read_capture(signed_in_client(wired_app, owner, fake_org_id), ABSENT_CAPTURE_ID)
    assert answer.status_code == NOT_FOUND_STATUS
    assert read_error_code(answer) == CAPTURE_NOT_FOUND_CODE


def test_an_unverified_capture_is_refused(wired_app: Flask, owner: identity.SessionOwner, fake_org_id: str) -> None:
    """A capture the portal never read back answers 409 `capture_not_verified`.

    Why:
        `contracts/http-api.md:176` fixes this refusal. A caller that received
        the document anyway would compare data that may never have reached the
        store, and the comparison would then report a change that never happened.

    Args:
        wired_app: The portal with the stored capture reader injected.
        owner: The registered owner.
        fake_org_id: The chosen organization.
    """
    wired_app.config[LOADER_KEY] = RecordingLoader(StoredLoad(dict(STORED_CAPTURE), False, CAPTURE_NOT_VERIFIED_CODE))
    answer = read_capture(signed_in_client(wired_app, owner, fake_org_id), STORED_CAPTURE_ID)
    assert answer.status_code == CONFLICT_STATUS
    assert read_error_code(answer) == CAPTURE_NOT_VERIFIED_CODE


def test_an_unverified_capture_hands_over_no_document(
    wired_app: Flask, owner: identity.SessionOwner, fake_org_id: str
) -> None:
    """The 409 answer carries the error envelope only, and no capture field.

    Args:
        wired_app: The portal with the stored capture reader injected.
        owner: The registered owner.
        fake_org_id: The chosen organization.
    """
    wired_app.config[LOADER_KEY] = RecordingLoader(StoredLoad(dict(STORED_CAPTURE), False, CAPTURE_NOT_VERIFIED_CODE))
    payload: dict[str, Any] = read_capture(
        signed_in_client(wired_app, owner, fake_org_id), STORED_CAPTURE_ID
    ).get_json()
    assert set(payload) == {"error"}


def test_an_unreachable_store_is_a_fault(wired_app: Flask, owner: identity.SessionOwner, fake_org_id: str) -> None:
    """A store that does not answer is a fault of the portal, not of the caller.

    Why:
        `capture/store.py` reports an unreachable database under its own reason.
        A 404 there would tell the operator that the capture is gone, and the
        operator would then start the whole capture again for nothing.

    Args:
        wired_app: The portal with the stored capture reader injected.
        owner: The registered owner.
        fake_org_id: The chosen organization.
    """
    wired_app.config[LOADER_KEY] = RecordingLoader(StoredLoad(None, False, DATABASE_UNREACHABLE_REASON))
    answer = read_capture(signed_in_client(wired_app, owner, fake_org_id), STORED_CAPTURE_ID)
    assert answer.status_code == SERVER_ERROR_STATUS


def test_a_read_with_no_session_is_refused(read_client: FlaskClient) -> None:
    """A read with no signed-in session answers 401.

    Args:
        read_client: A browser that never signed in.
    """
    assert read_capture(read_client, STORED_CAPTURE_ID).status_code == NOT_AUTHENTICATED_STATUS


# --------------------------------------------------------------------------
# The human view.
# --------------------------------------------------------------------------


def test_the_page_renders(read_client: FlaskClient, owner: identity.SessionOwner, fake_org_id: str) -> None:
    """The capture page answers 200 and carries the progress region.

    Args:
        read_client: The test browser.
        owner: The registered owner.
        fake_org_id: The chosen organization.
    """
    sign_in_client(read_client, owner, fake_org_id)
    answer = open_page(read_client, STORED_CAPTURE_ID)
    assert answer.status_code == OK_STATUS
    assert PROGRESS_MARKER in answer.get_data(as_text=True)


def test_the_page_names_the_capture(read_client: FlaskClient, owner: identity.SessionOwner, fake_org_id: str) -> None:
    """The page carries the capture identifier, which the poll script reads.

    Why:
        `portal.js` reads `data-capture-id` from the progress region and polls
        the status of that capture. An empty value stops the poll before it
        starts.

    Args:
        read_client: The test browser.
        owner: The registered owner.
        fake_org_id: The chosen organization.
    """
    sign_in_client(read_client, owner, fake_org_id)
    assert STORED_CAPTURE_ID in open_page(read_client, STORED_CAPTURE_ID).get_data(as_text=True)


def test_the_page_with_no_session_is_refused(read_client: FlaskClient) -> None:
    """The page with no signed-in session answers 401.

    Args:
        read_client: A browser that never signed in.
    """
    assert open_page(read_client, STORED_CAPTURE_ID).status_code == NOT_AUTHENTICATED_STATUS
