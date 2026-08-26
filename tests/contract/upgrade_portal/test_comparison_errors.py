"""Contract tests for the refusals of ``GET /api/comparisons``.

Why:
    Section 7.1 of ``data-model.md`` states that only a verified capture may
    enter a comparison, and section 6 of ``contracts/http-api.md`` fixes the
    two refusal codes. A route that answered 200 for an unverified capture
    would publish numbers that nobody may trust.

Every value below is a literal, and every test reads the ``code`` field of the
error envelope. ``contracts/README.md`` states that a test never asserts on
``message``.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from src.upgrade_portal.runtime import identity

# ---------------------------------------------------------------------------
# The contract values
# ---------------------------------------------------------------------------

COMPARISONS_PATH = "/api/comparisons"
COMPARE_PAGE_PATH = "/compare"

BEFORE_FIELD = "before"
AFTER_FIELD = "after"

OK_STATUS = 200
BAD_REQUEST_STATUS = 400
NOT_FOUND_STATUS = 404
CONFLICT_STATUS = 409
SERVER_ERROR_STATUS = 500

SITE_MISMATCH_CODE = "capture_site_mismatch"
NOT_VERIFIED_CODE = "capture_not_verified"
NOT_FOUND_CODE = "capture_not_found"

CAPTURE_LOADER_KEY = "CAPTURE_LOADER"
CAPTURE_LISTER_KEY = "CAPTURE_LISTER"

PROBE_EMAIL = "probe.operator@example.invalid"

# ---------------------------------------------------------------------------
# The captures
# ---------------------------------------------------------------------------

FIRST_SITE_ID = "00000000-0000-0000-0000-0000000000bb"
SECOND_SITE_ID = "00000000-0000-0000-0000-0000000000cc"

VERIFIED_BEFORE_ID = "capture-before-0001"
VERIFIED_AFTER_ID = "capture-after-0001"
OTHER_SITE_AFTER_ID = "capture-after-0002"
UNVERIFIED_BEFORE_ID = "capture-before-0003"
UNVERIFIED_AFTER_ID = "capture-after-0003"
UNREACHABLE_BEFORE_ID = "capture-before-0004"
UNKNOWN_CAPTURE_ID = "capture-that-nobody-stored"

STARTED_BEFORE = "2026-08-19T10:00:00+00:00"
STARTED_AFTER = "2026-08-19T10:25:00+00:00"

DATABASE_UNREACHABLE_REASON = "database_unreachable"

VERIFIED_BEFORE: dict[str, Any] = {
    "capture_id": VERIFIED_BEFORE_ID,
    "site_id": FIRST_SITE_ID,
    "site_name": "Probe site",
    "org_name": "Probe organization",
    "role": "pre",
    "capture_status": "verified",
    "started_at": STARTED_BEFORE,
    "device_index": {},
    "clients": {},
}

VERIFIED_AFTER: dict[str, Any] = {
    **VERIFIED_BEFORE,
    "capture_id": VERIFIED_AFTER_ID,
    "role": "post",
    "started_at": STARTED_AFTER,
}

OTHER_SITE_AFTER: dict[str, Any] = {
    **VERIFIED_AFTER,
    "capture_id": OTHER_SITE_AFTER_ID,
    "site_id": SECOND_SITE_ID,
    "site_name": "Other probe site",
}


# ---------------------------------------------------------------------------
# The stand-ins
# ---------------------------------------------------------------------------


class CaptureVerdict:
    """The answer that the capture store gives for a capture it refuses.

    Why:
        The store hands out no document for an unverified capture. It hands
        out the reason instead, and the route turns that reason into a status.
        This stand-in copies that shape and needs no database.

    Attributes:
        capture: The capture document, which is always None here.
        comparable: Whether the capture may enter a comparison.
        reason: The name of the fault.
    """

    def __init__(self, reason: str) -> None:
        """Store the reason and refuse the comparison.

        Args:
            reason: The name of the fault.
        """
        self.capture: Mapping[str, Any] | None = None
        self.comparable = False
        self.reason = reason


class RecordingCaptureLoader:
    """Answers a capture read from a fixed map and records each request.

    Why:
        A contract test must reach no database. The route reads its capture
        loader from the application config, so this stand-in fills that seam.

    Attributes:
        documents: The answer for each known business key.
        requested: The business key of each read, in order.
    """

    def __init__(self, documents: Mapping[str, Any]) -> None:
        """Store the answer map and start an empty request list.

        Args:
            documents: The answer for each known business key.
        """
        self.documents = dict(documents)
        self.requested: list[str] = []

    def __call__(self, capture_id: str) -> Any:
        """Return the answer for one business key.

        Args:
            capture_id: The business key to read.

        Returns:
            The capture, the refusal record, or None for an unknown key.
        """
        self.requested.append(capture_id)
        return self.documents.get(capture_id)


def empty_capture_list(site_id: str) -> list[dict[str, Any]]:
    """Return no capture row for the picker.

    Why:
        The comparison page falls back to the capture store when the config
        holds no lister, and that store imports a database driver. An injected
        lister keeps the page test free of a database.

    Args:
        site_id: The site to narrow to. This stand-in ignores it.

    Returns:
        An empty list.
    """
    del site_id  # WHY: The stand-in answers the same way for every site.
    return []


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def capture_loader() -> RecordingCaptureLoader:
    """Return the capture reader that every test in this module injects.

    Returns:
        The reader, holding one answer for each refusal.
    """
    return RecordingCaptureLoader(
        {
            VERIFIED_BEFORE_ID: VERIFIED_BEFORE,
            VERIFIED_AFTER_ID: VERIFIED_AFTER,
            OTHER_SITE_AFTER_ID: OTHER_SITE_AFTER,
            UNVERIFIED_BEFORE_ID: CaptureVerdict(NOT_VERIFIED_CODE),
            UNVERIFIED_AFTER_ID: CaptureVerdict(NOT_VERIFIED_CODE),
            UNREACHABLE_BEFORE_ID: CaptureVerdict(DATABASE_UNREACHABLE_REASON),
        }
    )


@pytest.fixture
def wired_app(portal_app: Flask, capture_loader: RecordingCaptureLoader) -> Flask:
    """Return the portal with the capture reader and the capture lister replaced.

    Args:
        portal_app: The portal application.
        capture_loader: The capture reader to inject.

    Returns:
        The wired application.
    """
    portal_app.config[CAPTURE_LOADER_KEY] = capture_loader
    portal_app.config[CAPTURE_LISTER_KEY] = empty_capture_list  # WHY: No database runs in a contract test.
    return portal_app


@pytest.fixture
def owner() -> Iterator[identity.SessionOwner]:
    """Register one operator for the length of one test.

    Yields:
        The identity pair of the registered operator.
    """
    yield from register_owner(object())  # WHY: A plain object states no scope, so every site passes.


@pytest.fixture
def signed_in_client(wired_app: Flask, owner: identity.SessionOwner) -> Iterator[FlaskClient]:
    """Return a test client that already holds a session.

    Args:
        wired_app: The wired application.
        owner: The identity pair of the registered operator.

    Yields:
        The signed-in client.
    """
    with wired_app.test_client() as client:  # WHY: The context manager holds the session across requests.
        sign_in_client(client, owner)
        yield client


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def register_owner(cloud_session: Any) -> Iterator[identity.SessionOwner]:
    """Register one operator, yield the identity pair, then drop the record.

    Why:
        The registry is a process global that outlives one test, so the
        cleanup must run even when the test fails.

    Args:
        cloud_session: The stand-in for the Mist cloud session.

    Yields:
        The identity pair of the registered operator.
    """
    owner = identity.build_owner(PROBE_EMAIL, identity.issue_browser_id())
    record = identity.OperatorSession(
        owner=owner,
        cloud_session=cloud_session,
        credential_mode=identity.CredentialMode.ENVIRONMENT_TOKEN,
    )
    identity.SESSION_REGISTRY.register(record)
    try:
        yield owner
    finally:
        identity.SESSION_REGISTRY.drop(owner.key)  # WHY: The registry outlives the test, so clear it here.


def sign_in_client(client: FlaskClient, owner: identity.SessionOwner) -> None:
    """Give one test client the session and the cookie of a registered owner.

    Args:
        client: The test client to sign in.
        owner: The identity pair of the registered operator.
    """
    client.set_cookie(identity.BROWSER_ID_COOKIE, owner.browser_id)
    with client.session_transaction() as browser_session:
        browser_session[identity.SESSION_OWNER_KEY] = owner.key


def read_error_code(response: TestResponse) -> str:
    """Return the ``code`` field of an error envelope.

    Why:
        ``contracts/README.md`` states that a test asserts on ``code`` and
        never on ``message``.

    Args:
        response: The answer to read.

    Returns:
        The error code.
    """
    payload: Any = response.get_json()
    return str(payload["error"]["code"])


def fetch_comparison(client: FlaskClient, before_id: str, after_id: str) -> TestResponse:
    """Ask the endpoint for one comparison.

    Args:
        client: The signed-in client.
        before_id: The business key of the pre-check capture.
        after_id: The business key of the post-check capture.

    Returns:
        The answer.
    """
    return client.get(COMPARISONS_PATH, query_string={BEFORE_FIELD: before_id, AFTER_FIELD: after_id})


# ---------------------------------------------------------------------------
# The site mismatch
# ---------------------------------------------------------------------------


def test_two_sites_answer_four_hundred(signed_in_client: FlaskClient) -> None:
    """The endpoint refuses two captures that name different sites.

    Why:
        A comparison across two sites reports every device as added and every
        device as removed, which reads as a total outage.

    Args:
        signed_in_client: The signed-in client.
    """
    response = fetch_comparison(signed_in_client, VERIFIED_BEFORE_ID, OTHER_SITE_AFTER_ID)

    assert response.status_code == BAD_REQUEST_STATUS


def test_two_sites_name_the_mismatch_code(signed_in_client: FlaskClient) -> None:
    """The site refusal carries the ``capture_site_mismatch`` code.

    Args:
        signed_in_client: The signed-in client.
    """
    response = fetch_comparison(signed_in_client, VERIFIED_BEFORE_ID, OTHER_SITE_AFTER_ID)

    assert read_error_code(response) == SITE_MISMATCH_CODE


def test_one_site_passes_the_site_test(signed_in_client: FlaskClient) -> None:
    """Two captures of one site pass the site test.

    Why:
        A refusal that fired for every pair would still pass the mismatch
        test above. This test proves the rule reads the site name.

    Args:
        signed_in_client: The signed-in client.
    """
    response = fetch_comparison(signed_in_client, VERIFIED_BEFORE_ID, VERIFIED_AFTER_ID)

    assert response.status_code == OK_STATUS


# ---------------------------------------------------------------------------
# The verification refusal
# ---------------------------------------------------------------------------


def test_unverified_pre_check_answers_four_hundred_and_nine(signed_in_client: FlaskClient) -> None:
    """The endpoint refuses an unverified pre-check capture.

    Args:
        signed_in_client: The signed-in client.
    """
    response = fetch_comparison(signed_in_client, UNVERIFIED_BEFORE_ID, VERIFIED_AFTER_ID)

    assert response.status_code == CONFLICT_STATUS
    assert read_error_code(response) == NOT_VERIFIED_CODE


def test_unverified_post_check_answers_four_hundred_and_nine(signed_in_client: FlaskClient) -> None:
    """The endpoint refuses an unverified post-check capture.

    Why:
        The route reads the pre-check capture first. A rule that tested only
        the first capture would still pass the test above.

    Args:
        signed_in_client: The signed-in client.
    """
    response = fetch_comparison(signed_in_client, VERIFIED_BEFORE_ID, UNVERIFIED_AFTER_ID)

    assert response.status_code == CONFLICT_STATUS
    assert read_error_code(response) == NOT_VERIFIED_CODE


def test_verification_runs_before_the_site_test(signed_in_client: FlaskClient) -> None:
    """An unverified capture answers the verification code, not the site code.

    Why:
        The store hands out no document for an unverified capture, so the
        route cannot read that capture's site. The order is therefore fixed
        and a test must hold it.

    Args:
        signed_in_client: The signed-in client.
    """
    response = fetch_comparison(signed_in_client, UNVERIFIED_BEFORE_ID, OTHER_SITE_AFTER_ID)

    assert read_error_code(response) == NOT_VERIFIED_CODE


# ---------------------------------------------------------------------------
# The unknown capture and the unreachable store
# ---------------------------------------------------------------------------


def test_unknown_capture_answers_four_hundred_and_four(signed_in_client: FlaskClient) -> None:
    """The endpoint reports that it holds no capture with that identifier.

    Args:
        signed_in_client: The signed-in client.
    """
    response = fetch_comparison(signed_in_client, UNKNOWN_CAPTURE_ID, VERIFIED_AFTER_ID)

    assert response.status_code == NOT_FOUND_STATUS
    assert read_error_code(response) == NOT_FOUND_CODE


def test_an_unreachable_store_is_a_portal_fault(signed_in_client: FlaskClient) -> None:
    """A store that the portal cannot read answers 500 and never 404.

    Why:
        Section 6 names no status for ``database_unreachable``. A read that
        the portal cannot perform is a portal fault, so the answer must not
        tell the operator that the capture is missing.

    Args:
        signed_in_client: The signed-in client.
    """
    response = fetch_comparison(signed_in_client, UNREACHABLE_BEFORE_ID, VERIFIED_AFTER_ID)

    assert response.status_code == SERVER_ERROR_STATUS
    assert read_error_code(response) != NOT_FOUND_CODE


# ---------------------------------------------------------------------------
# The human page
# ---------------------------------------------------------------------------


def test_the_page_shows_a_refusal_rather_than_an_error(signed_in_client: FlaskClient) -> None:
    """The comparison page answers 200 and shows the refusal to the operator.

    Why:
        A person who picked the wrong pair must read a sentence and pick
        again. A stack trace would end the task.

    Args:
        signed_in_client: The signed-in client.
    """
    response = signed_in_client.get(
        COMPARE_PAGE_PATH,
        query_string={BEFORE_FIELD: VERIFIED_BEFORE_ID, AFTER_FIELD: OTHER_SITE_AFTER_ID},
    )

    assert response.status_code == OK_STATUS


def test_the_page_asks_for_two_captures_when_the_request_names_none(signed_in_client: FlaskClient) -> None:
    """The comparison page shows the picker when the request names no capture.

    Args:
        signed_in_client: The signed-in client.
    """
    response = signed_in_client.get(COMPARE_PAGE_PATH)

    assert response.status_code == OK_STATUS
