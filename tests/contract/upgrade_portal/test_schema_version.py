"""Contract test of the `schema_version_too_new` refusal on the two read endpoints.

Why:
    `contracts/http-api.md:236` promises `409 schema_version_too_new` from
    `GET /api/captures/<capture_id>`. `contracts/http-api.md:414` promises the
    same answer from `GET /api/comparisons`. The only test that covered this
    refusal called the mapping helper of the review module and drove no route,
    so it proved the table and proved nothing about the two endpoints. A route
    that dropped the code would still pass it. Every test below drives a real
    route through the Flask test client instead.

Why the message matters:
    `app/routes/review.py:181` names the code and the sentence at the call site,
    because `factory.ERROR_CODES[409]` gives the bare word `conflict` and
    `factory.ERROR_MESSAGES[409]` gives the site lock sentence. A portal that
    fell back to those two defaults would send the operator to wait for a lock
    that nobody holds, and the true cure, a portal upgrade, would stay hidden.
    The tests below therefore prove that neither default reaches the caller.
    They read the shape of the sentence and never its wording, because
    `contracts/README.md:43` reserves the exact text for the writer.

Why no server runs:
    Both routes read the stored capture through one injected seam in the
    application config. Every test fills that seam, so no test opens a socket,
    reaches the cloud, imports a database driver, or reads the `.env` file.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from src.upgrade_portal.app.factory import ERROR_CODES, ERROR_MESSAGES
from src.upgrade_portal.runtime import identity

# ---------------------------------------------------------------------------
# The contract values. Each one repeats a line of the specification.
# ---------------------------------------------------------------------------

READ_PATH_TEMPLATE = "/api/captures/{capture_id}"  # `contracts/http-api.md:229`.
COMPARISONS_PATH = "/api/comparisons"  # `contracts/http-api.md:406`.

BEFORE_FIELD = "before"  # The query field that names the pre-check capture.
AFTER_FIELD = "after"  # The query field that names the post-check capture.

OK_STATUS = 200  # The read succeeded.
CONFLICT_STATUS = 409  # The record is present, and this release cannot render it.

ERROR_FIELD = "error"  # The one envelope name of `contracts/README.md:29`.
CODE_FIELD = "code"  # The fixed lower-case word inside the envelope.
MESSAGE_FIELD = "message"  # The plain sentence for the operator.

SCHEMA_TOO_NEW_CODE = "schema_version_too_new"  # `capture/store.py:66` publishes this reason.

# The two answers that `json_error` gives when a route names no code and no
# sentence of its own. Neither value may reach the caller of these two routes.
GENERIC_CONFLICT_CODE = ERROR_CODES[CONFLICT_STATUS]
GENERIC_CONFLICT_MESSAGE = ERROR_MESSAGES[CONFLICT_STATUS]

# WHY: `app/routes/capture.py:67` and `app/routes/review.py:196` read this one
# config key, so a single injected reader serves both endpoints.
CAPTURE_LOADER_KEY = "CAPTURE_LOADER"

SELECTED_ORG_SESSION_KEY = "selected_org_id"  # The organization the operator picked.
PROBE_EMAIL = "probe.operator@example.invalid"  # A reserved domain, so no real address appears.

READABLE_SCHEMA_VERSION = 1  # `capture/store.py:45` fixes the version of this release.
LATER_SCHEMA_VERSION = 2  # One version above this release, so the reader must refuse it.

SITE_ID = "00000000-0000-0000-0000-0000000000bb"  # One site, so no comparison meets the site rule.

READABLE_BEFORE_ID = "cap-abcdef12-01"
READABLE_AFTER_ID = "cap-abcdef12-02"
LATER_BEFORE_ID = "cap-fedcba98-01"
LATER_AFTER_ID = "cap-fedcba98-02"

SENTENCE_END = "."  # A sentence for the operator closes with a period.
WORD_GAP = " "  # A sentence holds more than one word.

# WHY: The shape of one stored capture, cut down to the fields that the read
# route hands on and the comparison route reads. `data-model.md` fixes each name.
READABLE_BEFORE: dict[str, Any] = {
    "capture_id": READABLE_BEFORE_ID,
    "schema_version": READABLE_SCHEMA_VERSION,
    "site_id": SITE_ID,
    "site_name": "Probe site",
    "org_name": "Probe organization",
    "role": "pre",
    "capture_status": "verified",
    "started_at": "2026-08-19T10:00:00+00:00",
    "device_index": {},
    "clients": {},
}

READABLE_AFTER: dict[str, Any] = {
    **READABLE_BEFORE,
    "capture_id": READABLE_AFTER_ID,
    "role": "post",
    "started_at": "2026-08-19T10:25:00+00:00",
}

# WHY: The same two captures, written by a later release. Only the schema
# version differs, so the refusal can come from that one field and no other.
LATER_BEFORE: dict[str, Any] = {
    **READABLE_BEFORE,
    "capture_id": LATER_BEFORE_ID,
    "schema_version": LATER_SCHEMA_VERSION,
}

LATER_AFTER: dict[str, Any] = {
    **READABLE_AFTER,
    "capture_id": LATER_AFTER_ID,
    "schema_version": LATER_SCHEMA_VERSION,
}


# ---------------------------------------------------------------------------
# The stand-ins
# ---------------------------------------------------------------------------


class ScopedCloudSession:
    """A cloud session that may act on one organization only.

    Why:
        The session guard reads the privilege list off the cloud session. A
        plain list keeps the whole test free of the cloud and free of a token.
    """

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
        that reports whether this release may render it, and the reason for a
        refusal. Both routes read those three names, so this stand-in carries
        the same three names and needs no database.

    Attributes:
        capture: The stored document, which travels beside a refusal too.
        comparable: True when this release may render the document.
        reason: The refusal code, or an empty string after a clean read.
    """

    def __init__(self, capture: Mapping[str, Any], comparable: bool, reason: str) -> None:
        """Record one stored capture read.

        Args:
            capture: The stored document.
            comparable: True when this release may render the document.
            reason: The refusal code, or an empty string after a clean read.
        """
        self.capture = capture
        self.comparable = comparable
        self.reason = reason


class MapLoader:
    """A stored capture reader that answers from one fixed map.

    Why:
        The real reader reaches ArangoDB. A contract test must reach no database
        server, so every answer lives in the test. Both routes read one seam
        key, so one map serves the capture read and the comparison, and the two
        endpoints can never answer from two different stores.

    Attributes:
        answers: One answer for each capture identifier.
        asked: The identifiers the routes asked about, in order.
    """

    def __init__(self, answers: Mapping[str, StoredLoad]) -> None:
        """Record the answer map and start an empty question list.

        Args:
            answers: One answer for each capture identifier.
        """
        self.answers = dict(answers)
        self.asked: list[str] = []

    def __call__(self, capture_id: str) -> StoredLoad | None:
        """Answer one stored capture read.

        Args:
            capture_id: The capture that a route asked about.

        Returns:
            The recorded answer, or None for an identifier the map does not hold.
        """
        self.asked.append(capture_id)
        return self.answers.get(capture_id)


# ---------------------------------------------------------------------------
# The fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def capture_loader() -> MapLoader:
    """Return the stored capture reader that every test injects.

    Why:
        The map holds one readable pair and one later pair. The readable pair
        proves that the gate reads the schema version and does not refuse every
        request, so a rule that always refused could not pass this module.

    Returns:
        The reader, holding four answers.
    """
    return MapLoader(
        {
            READABLE_BEFORE_ID: StoredLoad(READABLE_BEFORE, True, ""),
            READABLE_AFTER_ID: StoredLoad(READABLE_AFTER, True, ""),
            LATER_BEFORE_ID: StoredLoad(LATER_BEFORE, False, SCHEMA_TOO_NEW_CODE),
            LATER_AFTER_ID: StoredLoad(LATER_AFTER, False, SCHEMA_TOO_NEW_CODE),
        }
    )


@pytest.fixture
def wired_app(portal_app: Flask, capture_loader: MapLoader) -> Flask:
    """Return the portal with the stored capture reader injected.

    Why:
        The injected seam wins over the capture store, so no test in this module
        imports a database driver and no test opens a socket.

    Args:
        portal_app: The portal application under test.
        capture_loader: The reader to inject.

    Returns:
        The wired application.
    """
    portal_app.config[CAPTURE_LOADER_KEY] = capture_loader
    return portal_app


@pytest.fixture
def owner(fake_org_id: str) -> Iterator[identity.SessionOwner]:
    """Register one signed-in operator, then drop the record.

    Why:
        The session registry is a process global that outlives one test, so the
        cleanup runs in a finally block and runs even when a test fails.

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


@pytest.fixture
def signed_in_client(wired_app: Flask, owner: identity.SessionOwner, fake_org_id: str) -> Iterator[FlaskClient]:
    """Yield a browser that already carries a signed-in session.

    Args:
        wired_app: The portal with the stored capture reader injected.
        owner: The registered owner.
        fake_org_id: The organization the operator picked.

    Yields:
        The signed-in browser.
    """
    with wired_app.test_client() as client:  # WHY: The context manager holds the session across the requests.
        client.set_cookie(identity.BROWSER_ID_COOKIE, owner.browser_id)
        with client.session_transaction() as browser_session:
            browser_session[identity.SESSION_OWNER_KEY] = owner.key
            browser_session[SELECTED_ORG_SESSION_KEY] = fake_org_id
        yield client


# ---------------------------------------------------------------------------
# The helpers
# ---------------------------------------------------------------------------


def read_capture(client: FlaskClient, capture_id: str) -> TestResponse:
    """Ask the portal for one whole capture document.

    Args:
        client: The signed-in browser.
        capture_id: The capture to read.

    Returns:
        The portal answer.
    """
    return client.get(READ_PATH_TEMPLATE.format(capture_id=capture_id))


def fetch_comparison(client: FlaskClient, before_id: str, after_id: str) -> TestResponse:
    """Ask the portal for one comparison of two captures.

    Args:
        client: The signed-in browser.
        before_id: The identifier of the pre-check capture.
        after_id: The identifier of the post-check capture.

    Returns:
        The portal answer.
    """
    return client.get(COMPARISONS_PATH, query_string={BEFORE_FIELD: before_id, AFTER_FIELD: after_id})


def error_field(response: TestResponse, name: str) -> str:
    """Read one field out of the error envelope of a refusal.

    Args:
        response: The portal answer.
        name: The field to read, either `code` or `message`.

    Returns:
        The field value as text.
    """
    payload: Any = response.get_json()
    return str(payload[ERROR_FIELD][name])


def reads_as_a_sentence(text: str) -> bool:
    """Report whether one refusal message reads as a sentence for the operator.

    Why:
        `contracts/README.md:43` reserves the exact wording for the writer, so
        this rule reads the shape and never the words. A bare code word such as
        `conflict` holds no space and closes with no period, so this rule
        catches a fall back to the default answer without pinning one sentence.

    Args:
        text: The message field of the error envelope.

    Returns:
        True when the text holds more than one word and closes with a period.
    """
    trimmed = text.strip()
    return WORD_GAP in trimmed and trimmed.endswith(SENTENCE_END)


# ---------------------------------------------------------------------------
# `GET /api/captures/<capture_id>`
# ---------------------------------------------------------------------------


def test_a_capture_of_a_later_release_answers_a_conflict(signed_in_client: FlaskClient) -> None:
    """The read of a capture from a later release answers 409.

    Why:
        `contracts/http-api.md:236` fixes this status. The record is present, so
        the request is sound and the answer must not read as a missing record.

    Args:
        signed_in_client: The signed-in browser.
    """
    response = read_capture(signed_in_client, LATER_BEFORE_ID)

    assert response.status_code == CONFLICT_STATUS


def test_the_capture_read_names_the_schema_version_code(signed_in_client: FlaskClient) -> None:
    """The read refusal carries the `schema_version_too_new` code.

    Args:
        signed_in_client: The signed-in browser.
    """
    response = read_capture(signed_in_client, LATER_BEFORE_ID)

    assert error_field(response, CODE_FIELD) == SCHEMA_TOO_NEW_CODE


def test_the_capture_read_avoids_the_bare_conflict_code(signed_in_client: FlaskClient) -> None:
    """The read refusal never falls back to the default code of the status.

    Why:
        The default code of 409 is one word, and that word cannot tell a locked
        site from a record of a later release. An operator who read it would
        wait for a lock that nobody holds.

    Args:
        signed_in_client: The signed-in browser.
    """
    response = read_capture(signed_in_client, LATER_BEFORE_ID)

    assert error_field(response, CODE_FIELD) != GENERIC_CONFLICT_CODE


def test_the_capture_read_avoids_the_site_lock_sentence(signed_in_client: FlaskClient) -> None:
    """The read refusal never falls back to the default sentence of the status.

    Why:
        The default sentence of 409 names the site lock. That sentence names the
        wrong fault here, and it hides the one cure, a portal upgrade.

    Args:
        signed_in_client: The signed-in browser.
    """
    response = read_capture(signed_in_client, LATER_BEFORE_ID)

    assert error_field(response, MESSAGE_FIELD) != GENERIC_CONFLICT_MESSAGE


def test_the_capture_read_message_reads_as_a_sentence(signed_in_client: FlaskClient) -> None:
    """The read refusal carries a plain sentence, and not a bare code word.

    Args:
        signed_in_client: The signed-in browser.
    """
    response = read_capture(signed_in_client, LATER_BEFORE_ID)

    assert reads_as_a_sentence(error_field(response, MESSAGE_FIELD))


def test_the_capture_read_hands_over_no_document(signed_in_client: FlaskClient) -> None:
    """The read refusal carries the error envelope only, and no capture field.

    Why:
        This release cannot read a field that a later release wrote, so a
        partial document would invite a caller to guess at a meaning.

    Args:
        signed_in_client: The signed-in browser.
    """
    payload: Any = read_capture(signed_in_client, LATER_BEFORE_ID).get_json()

    assert set(payload) == {ERROR_FIELD}


def test_a_readable_capture_still_reads_back(signed_in_client: FlaskClient) -> None:
    """A capture of this release still answers 200.

    Why:
        A gate that refused every read would pass every test above. This test
        proves the gate reads the schema version of the record.

    Args:
        signed_in_client: The signed-in browser.
    """
    response = read_capture(signed_in_client, READABLE_BEFORE_ID)

    assert response.status_code == OK_STATUS


# ---------------------------------------------------------------------------
# `GET /api/comparisons`
# ---------------------------------------------------------------------------


def test_a_later_pre_check_capture_answers_a_conflict(signed_in_client: FlaskClient) -> None:
    """A comparison whose pre-check capture is too new answers 409 with the code.

    Why:
        `contracts/http-api.md:414` fixes this status and this code for either
        capture of the pair.

    Args:
        signed_in_client: The signed-in browser.
    """
    response = fetch_comparison(signed_in_client, LATER_BEFORE_ID, READABLE_AFTER_ID)

    assert response.status_code == CONFLICT_STATUS
    assert error_field(response, CODE_FIELD) == SCHEMA_TOO_NEW_CODE


def test_a_later_post_check_capture_answers_a_conflict(signed_in_client: FlaskClient) -> None:
    """A comparison whose post-check capture is too new answers 409 with the code.

    Why:
        The route reads the pre-check capture first. A rule that tested only the
        first capture would still pass the test above.

    Args:
        signed_in_client: The signed-in browser.
    """
    response = fetch_comparison(signed_in_client, READABLE_BEFORE_ID, LATER_AFTER_ID)

    assert response.status_code == CONFLICT_STATUS
    assert error_field(response, CODE_FIELD) == SCHEMA_TOO_NEW_CODE


def test_the_comparison_avoids_the_bare_conflict_code(signed_in_client: FlaskClient) -> None:
    """The comparison refusal never falls back to the default code of the status.

    Args:
        signed_in_client: The signed-in browser.
    """
    response = fetch_comparison(signed_in_client, LATER_BEFORE_ID, READABLE_AFTER_ID)

    assert error_field(response, CODE_FIELD) != GENERIC_CONFLICT_CODE


def test_the_comparison_avoids_the_site_lock_sentence(signed_in_client: FlaskClient) -> None:
    """The comparison refusal never falls back to the default sentence of the status.

    Why:
        The default sentence of 409 names the site lock. Two captures of a later
        release name no lock at all, so that sentence would send the operator to
        the wrong cure.

    Args:
        signed_in_client: The signed-in browser.
    """
    response = fetch_comparison(signed_in_client, LATER_BEFORE_ID, READABLE_AFTER_ID)

    assert error_field(response, MESSAGE_FIELD) != GENERIC_CONFLICT_MESSAGE


def test_the_comparison_message_reads_as_a_sentence(signed_in_client: FlaskClient) -> None:
    """The comparison refusal carries a plain sentence, and not a bare code word.

    Args:
        signed_in_client: The signed-in browser.
    """
    response = fetch_comparison(signed_in_client, LATER_BEFORE_ID, READABLE_AFTER_ID)

    assert reads_as_a_sentence(error_field(response, MESSAGE_FIELD))


def test_the_comparison_hands_over_no_capture(signed_in_client: FlaskClient) -> None:
    """The comparison refusal carries the error envelope only, and no capture.

    Args:
        signed_in_client: The signed-in browser.
    """
    payload: Any = fetch_comparison(signed_in_client, LATER_BEFORE_ID, READABLE_AFTER_ID).get_json()

    assert set(payload) == {ERROR_FIELD}


def test_the_comparison_stops_at_the_first_refused_capture(
    signed_in_client: FlaskClient, capture_loader: MapLoader
) -> None:
    """The route stops after the pre-check capture that it cannot render.

    Why:
        A route that read both captures anyway would report the fault of the
        second capture, and the operator would then upgrade for the wrong
        record.

    Args:
        signed_in_client: The signed-in browser.
        capture_loader: The reader that recorded each question.
    """
    fetch_comparison(signed_in_client, LATER_BEFORE_ID, READABLE_AFTER_ID)

    assert capture_loader.asked == [LATER_BEFORE_ID]


def test_two_readable_captures_still_compare(signed_in_client: FlaskClient) -> None:
    """Two captures of this release still answer 200.

    Why:
        A gate that refused every pair would pass every comparison test above.
        This test proves the gate reads the schema version of each record.

    Args:
        signed_in_client: The signed-in browser.
    """
    response = fetch_comparison(signed_in_client, READABLE_BEFORE_ID, READABLE_AFTER_ID)

    assert response.status_code == OK_STATUS
