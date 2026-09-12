"""Contract tests for ``GET /api/comparisons``.

Why:
    Section 6 of ``contracts/http-api.md`` fixes the body of one comparison.
    A route lane may rename a field of the compare package without noticing
    that the endpoint prints that field, so these tests pin the wire names.

Every value below is a literal. A test that imported a name from the module
under test would agree with a rename and would prove nothing.

The statistics test uses a subset rule and never an equality rule. Section 6
states that a reader treats the object as a superset, because a later release
can add a name.
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

BEFORE_FIELD = "before"
AFTER_FIELD = "after"

OK_STATUS = 200
NOT_AUTHENTICATED_STATUS = 401
NOT_AUTHENTICATED_CODE = "not_authenticated"

CAPTURE_LOADER_KEY = "CAPTURE_LOADER"

# The eight body keys of `contracts/http-api.md:296-352`.
BODY_KEYS = frozenset(
    {
        "before",
        "after",
        "site_name",
        "org_name",
        "statistics",
        "device_deltas",
        "client_deltas",
        "skipped_sections",
    }
)

# The eleven statistic names of `data-model.md` section 7.4.
STATISTIC_NAMES = frozenset(
    {
        "devices_unchanged",
        "devices_changed",
        "devices_added",
        "devices_removed",
        "devices_version_changed",
        "clients_present",
        "clients_moved",
        "clients_added",
        "clients_missing",
        "client_return_rate",
        "elapsed_seconds",
    }
)

DEVICE_DELTA_KEYS = frozenset({"mac", "outcome", "name", "changes"})

CLIENT_DELTA_KEYS = frozenset(
    {
        "mac",
        "outcome",
        "hostname",
        "kind",
        "before_device",
        "after_device",
        "before_device_name",
        "after_device_name",
    }
)

PROBE_EMAIL = "probe.operator@example.invalid"

# ---------------------------------------------------------------------------
# The two captures
# ---------------------------------------------------------------------------

BEFORE_CAPTURE_ID = "capture-before-0001"
AFTER_CAPTURE_ID = "capture-after-0001"
SKIPPED_BEFORE_ID = "capture-before-0002"
SKIPPED_AFTER_ID = "capture-after-0002"

SITE_ID = "00000000-0000-0000-0000-0000000000bb"
SITE_NAME = "Probe site"
ORG_NAME = "Probe organization"

DEVICE_UNCHANGED_MAC = "aabbcc000001"
DEVICE_CHANGED_MAC = "aabbcc000002"
DEVICE_REMOVED_MAC = "aabbcc000003"
DEVICE_ADDED_MAC = "aabbcc000004"

CLIENT_PRESENT_MAC = "ddeeff000001"
CLIENT_MOVED_MAC = "ddeeff000002"
CLIENT_MISSING_MAC = "ddeeff000003"
CLIENT_ADDED_MAC = "ddeeff000004"

OLD_VERSION = "0.14.29644"
NEW_VERSION = "0.16.30107"

STARTED_BEFORE = "2026-08-19T10:00:00+00:00"
FINISHED_BEFORE = "2026-08-19T10:05:00+00:00"
STARTED_AFTER = "2026-08-19T10:25:00+00:00"
FINISHED_AFTER = "2026-08-19T10:30:00+00:00"

# The window runs from the start of the pre-check to the finish of the
# post-check, which is thirty minutes.
ELAPSED_SECONDS = 1800.0

# One client stayed, one client moved, and one client went missing. The rate is
# two divided by three. Rounding to three places gives 0.667, and cutting the
# digits would give 0.666.
RETURN_RATE = 0.667
TRUNCATED_RETURN_RATE = 0.666

DEVICES_SECTION = "devices"
MATCHING_DIGEST = "sha256:0000000000000000000000000000000000000000000000000000000000000001"

BEFORE_DEVICES: dict[str, dict[str, str]] = {
    DEVICE_UNCHANGED_MAC: {"name": "core-switch", "status": "connected", "version": OLD_VERSION, "model": "EX4400"},
    DEVICE_CHANGED_MAC: {"name": "access-switch", "status": "connected", "version": OLD_VERSION, "model": "EX4100"},
    DEVICE_REMOVED_MAC: {"name": "spare-switch", "status": "connected", "version": OLD_VERSION, "model": "EX2300"},
}

AFTER_DEVICES: dict[str, dict[str, str]] = {
    DEVICE_UNCHANGED_MAC: {"name": "core-switch", "status": "connected", "version": OLD_VERSION, "model": "EX4400"},
    DEVICE_CHANGED_MAC: {"name": "access-switch", "status": "connected", "version": NEW_VERSION, "model": "EX4100"},
    DEVICE_ADDED_MAC: {"name": "new-switch", "status": "connected", "version": NEW_VERSION, "model": "EX4100"},
}

BEFORE_CLIENTS: dict[str, list[dict[str, str]]] = {
    "wireless": [
        {"mac": CLIENT_PRESENT_MAC, "hostname": "desk-one", "device_mac": DEVICE_UNCHANGED_MAC},
        {"mac": CLIENT_MOVED_MAC, "hostname": "desk-two", "device_mac": DEVICE_UNCHANGED_MAC},
        {"mac": CLIENT_MISSING_MAC, "hostname": "desk-three", "device_mac": DEVICE_REMOVED_MAC},
    ]
}

AFTER_CLIENTS: dict[str, list[dict[str, str]]] = {
    "wireless": [
        {"mac": CLIENT_PRESENT_MAC, "hostname": "desk-one", "device_mac": DEVICE_UNCHANGED_MAC},
        {"mac": CLIENT_MOVED_MAC, "hostname": "desk-two", "device_mac": DEVICE_CHANGED_MAC},
        {"mac": CLIENT_ADDED_MAC, "hostname": "desk-four", "device_mac": DEVICE_ADDED_MAC},
    ]
}

BEFORE_CAPTURE: dict[str, Any] = {
    "capture_id": BEFORE_CAPTURE_ID,
    "site_id": SITE_ID,
    "site_name": SITE_NAME,
    "org_name": ORG_NAME,
    "role": "pre",
    "capture_status": "verified",
    "started_at": STARTED_BEFORE,
    "finished_at": FINISHED_BEFORE,
    "device_index": BEFORE_DEVICES,
    "clients": BEFORE_CLIENTS,
}

AFTER_CAPTURE: dict[str, Any] = {
    "capture_id": AFTER_CAPTURE_ID,
    "site_id": SITE_ID,
    "site_name": SITE_NAME,
    "org_name": ORG_NAME,
    "role": "post",
    "capture_status": "verified",
    "started_at": STARTED_AFTER,
    "finished_at": FINISHED_AFTER,
    "device_index": AFTER_DEVICES,
    "clients": AFTER_CLIENTS,
}


def with_digest(capture: Mapping[str, Any], capture_id: str) -> dict[str, Any]:
    """Return a copy of one capture that carries a device digest.

    Why:
        A matching digest proves the device section is equal, so the
        comparison skips it. The test needs a second pair that carries the
        same digest on both sides.

    Args:
        capture: The capture to copy.
        capture_id: The business key of the copy.

    Returns:
        The copy.
    """
    return {**capture, "capture_id": capture_id, "digests": {DEVICES_SECTION: MATCHING_DIGEST}}


# ---------------------------------------------------------------------------
# The stand-ins
# ---------------------------------------------------------------------------


class RecordingCaptureLoader:
    """Answers a capture read from a fixed map and records each request.

    Why:
        A contract test must reach no database. The route reads its capture
        loader from the application config, so this stand-in fills that seam
        and also proves which identifiers the route asked for.

    Attributes:
        documents: The capture of each known business key.
        requested: The business key of each read, in order.
    """

    def __init__(self, documents: Mapping[str, Any]) -> None:
        """Store the capture map and start an empty request list.

        Args:
            documents: The capture of each known business key.
        """
        self.documents = dict(documents)
        self.requested: list[str] = []

    def __call__(self, capture_id: str) -> Any:
        """Return the capture of one business key.

        Why:
            The route accepts a plain document and treats it as verified, so
            the stand-in needs no verdict record for the success tests.

        Args:
            capture_id: The business key to read.

        Returns:
            The capture, or None when the map holds no such key.
        """
        self.requested.append(capture_id)
        return self.documents.get(capture_id)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def capture_loader() -> RecordingCaptureLoader:
    """Return the capture reader that every test in this module injects.

    Returns:
        The reader, holding both capture pairs.
    """
    return RecordingCaptureLoader(
        {
            BEFORE_CAPTURE_ID: BEFORE_CAPTURE,
            AFTER_CAPTURE_ID: AFTER_CAPTURE,
            SKIPPED_BEFORE_ID: with_digest(BEFORE_CAPTURE, SKIPPED_BEFORE_ID),
            SKIPPED_AFTER_ID: with_digest(AFTER_CAPTURE, SKIPPED_AFTER_ID),
        }
    )


@pytest.fixture
def wired_app(portal_app: Flask, capture_loader: RecordingCaptureLoader) -> Flask:
    """Return the portal with the capture reader replaced.

    Why:
        The route falls back to the capture store, and the store imports the
        database driver. Injecting the reader keeps the test free of a
        database.

    Args:
        portal_app: The portal application.
        capture_loader: The capture reader to inject.

    Returns:
        The wired application.
    """
    portal_app.config[CAPTURE_LOADER_KEY] = capture_loader
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

    Why:
        The guard checks the signed session against the browser cookie. Both
        halves must agree, so this helper sets both in one place.

    Args:
        client: The test client to sign in.
        owner: The identity pair of the registered operator.
    """
    client.set_cookie(identity.BROWSER_ID_COOKIE, owner.browser_id)
    with client.session_transaction() as browser_session:
        browser_session[identity.SESSION_OWNER_KEY] = owner.key


def read_body(response: TestResponse) -> dict[str, Any]:
    """Return the JSON body of one answer.

    Args:
        response: The answer to read.

    Returns:
        The body.
    """
    payload: Any = response.get_json()
    assert isinstance(payload, dict)
    return payload


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
    return str(read_body(response)["error"]["code"])


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


def outcome_of(rows: list[dict[str, Any]], mac: str) -> str:
    """Return the outcome of one row of a delta list.

    Why:
        The order of the rows is not part of the contract, so a test reads a
        row by its address rather than by its place in the list.

    Args:
        rows: The delta list.
        mac: The address to find.

    Returns:
        The outcome, or an empty string when the list holds no such address.
    """
    for row in rows:
        if row.get("mac") == mac:
            return str(row.get("outcome", ""))
    return ""


# ---------------------------------------------------------------------------
# The body shape
# ---------------------------------------------------------------------------


def test_comparison_answers_two_hundred(signed_in_client: FlaskClient) -> None:
    """The endpoint answers 200 for two verified captures of one site.

    Args:
        signed_in_client: The signed-in client.
    """
    response = fetch_comparison(signed_in_client, BEFORE_CAPTURE_ID, AFTER_CAPTURE_ID)

    assert response.status_code == OK_STATUS


def test_comparison_body_holds_every_contract_key(signed_in_client: FlaskClient) -> None:
    """The body holds the eight keys of section 6.

    Args:
        signed_in_client: The signed-in client.
    """
    body = read_body(fetch_comparison(signed_in_client, BEFORE_CAPTURE_ID, AFTER_CAPTURE_ID))

    assert BODY_KEYS <= set(body)


def test_comparison_names_the_site_and_the_organization(signed_in_client: FlaskClient) -> None:
    """The body repeats the site name and the organization name.

    Args:
        signed_in_client: The signed-in client.
    """
    body = read_body(fetch_comparison(signed_in_client, BEFORE_CAPTURE_ID, AFTER_CAPTURE_ID))

    assert body["site_name"] == SITE_NAME
    assert body["org_name"] == ORG_NAME


def test_comparison_names_both_captures(signed_in_client: FlaskClient) -> None:
    """The two capture summaries carry the business key of each capture.

    Args:
        signed_in_client: The signed-in client.
    """
    body = read_body(fetch_comparison(signed_in_client, BEFORE_CAPTURE_ID, AFTER_CAPTURE_ID))

    assert body["before"]["capture_id"] == BEFORE_CAPTURE_ID
    assert body["after"]["capture_id"] == AFTER_CAPTURE_ID


# ---------------------------------------------------------------------------
# The statistics
# ---------------------------------------------------------------------------


def test_statistics_hold_every_contract_name(signed_in_client: FlaskClient) -> None:
    """The statistics object holds the eleven names of the data model.

    Why:
        The test states a subset rule. Section 6 allows a later release to add
        a name, so an equality rule would fail on a release that broke nothing.

    Args:
        signed_in_client: The signed-in client.
    """
    body = read_body(fetch_comparison(signed_in_client, BEFORE_CAPTURE_ID, AFTER_CAPTURE_ID))

    assert STATISTIC_NAMES <= set(body["statistics"])


def test_statistics_count_every_device_outcome(signed_in_client: FlaskClient) -> None:
    """The device counts match the four devices of the two captures.

    Args:
        signed_in_client: The signed-in client.
    """
    statistics = read_body(fetch_comparison(signed_in_client, BEFORE_CAPTURE_ID, AFTER_CAPTURE_ID))["statistics"]

    assert statistics["devices_unchanged"] == 1
    assert statistics["devices_changed"] == 1
    assert statistics["devices_added"] == 1
    assert statistics["devices_removed"] == 1


def test_statistics_count_the_version_change(signed_in_client: FlaskClient) -> None:
    """One device reports a new firmware version.

    Args:
        signed_in_client: The signed-in client.
    """
    statistics = read_body(fetch_comparison(signed_in_client, BEFORE_CAPTURE_ID, AFTER_CAPTURE_ID))["statistics"]

    assert statistics["devices_version_changed"] == 1


def test_statistics_count_every_client_outcome(signed_in_client: FlaskClient) -> None:
    """The client counts match the four clients of the two captures.

    Args:
        signed_in_client: The signed-in client.
    """
    statistics = read_body(fetch_comparison(signed_in_client, BEFORE_CAPTURE_ID, AFTER_CAPTURE_ID))["statistics"]

    assert statistics["clients_present"] == 1
    assert statistics["clients_moved"] == 1
    assert statistics["clients_added"] == 1
    assert statistics["clients_missing"] == 1


def test_return_rate_rounds_and_does_not_cut(signed_in_client: FlaskClient) -> None:
    """The return rate rounds to three places rather than cutting the digits.

    Why:
        Section 6 records that an earlier example printed the cut value. Two
        divided by three shows the difference at the third place.

    Args:
        signed_in_client: The signed-in client.
    """
    statistics = read_body(fetch_comparison(signed_in_client, BEFORE_CAPTURE_ID, AFTER_CAPTURE_ID))["statistics"]

    assert statistics["client_return_rate"] == RETURN_RATE
    assert statistics["client_return_rate"] != TRUNCATED_RETURN_RATE


def test_elapsed_seconds_spans_the_whole_window(signed_in_client: FlaskClient) -> None:
    """The elapsed time runs from the pre-check start to the post-check finish.

    Args:
        signed_in_client: The signed-in client.
    """
    statistics = read_body(fetch_comparison(signed_in_client, BEFORE_CAPTURE_ID, AFTER_CAPTURE_ID))["statistics"]

    assert statistics["elapsed_seconds"] == pytest.approx(ELAPSED_SECONDS)


# ---------------------------------------------------------------------------
# The two delta lists
# ---------------------------------------------------------------------------


def test_device_deltas_hold_every_contract_key(signed_in_client: FlaskClient) -> None:
    """Each device row holds the address, the outcome, the name, and the changes.

    Args:
        signed_in_client: The signed-in client.
    """
    rows = read_body(fetch_comparison(signed_in_client, BEFORE_CAPTURE_ID, AFTER_CAPTURE_ID))["device_deltas"]

    assert rows
    for row in rows:
        assert DEVICE_DELTA_KEYS <= set(row)


def test_device_deltas_name_each_outcome(signed_in_client: FlaskClient) -> None:
    """The device list reports one device for each of the four outcomes.

    Args:
        signed_in_client: The signed-in client.
    """
    rows = read_body(fetch_comparison(signed_in_client, BEFORE_CAPTURE_ID, AFTER_CAPTURE_ID))["device_deltas"]

    assert outcome_of(rows, DEVICE_UNCHANGED_MAC) == "unchanged"
    assert outcome_of(rows, DEVICE_CHANGED_MAC) == "changed"
    assert outcome_of(rows, DEVICE_ADDED_MAC) == "added"
    assert outcome_of(rows, DEVICE_REMOVED_MAC) == "removed"


def test_client_deltas_hold_every_contract_key(signed_in_client: FlaskClient) -> None:
    """Each client row holds the address, the outcome, and both serving devices.

    Args:
        signed_in_client: The signed-in client.
    """
    rows = read_body(fetch_comparison(signed_in_client, BEFORE_CAPTURE_ID, AFTER_CAPTURE_ID))["client_deltas"]

    assert rows
    for row in rows:
        assert CLIENT_DELTA_KEYS <= set(row)


def test_client_deltas_name_each_outcome(signed_in_client: FlaskClient) -> None:
    """The client list reports one client for each of the four outcomes.

    Why:
        A moved client is on the network, so the report must separate ``moved``
        from ``missing``.

    Args:
        signed_in_client: The signed-in client.
    """
    rows = read_body(fetch_comparison(signed_in_client, BEFORE_CAPTURE_ID, AFTER_CAPTURE_ID))["client_deltas"]

    assert outcome_of(rows, CLIENT_PRESENT_MAC) == "present"
    assert outcome_of(rows, CLIENT_MOVED_MAC) == "moved"
    assert outcome_of(rows, CLIENT_ADDED_MAC) == "added"
    assert outcome_of(rows, CLIENT_MISSING_MAC) == "missing"


def test_moved_client_names_both_serving_devices(signed_in_client: FlaskClient) -> None:
    """The moved client names the device before the move and the device after it.

    Args:
        signed_in_client: The signed-in client.
    """
    rows = read_body(fetch_comparison(signed_in_client, BEFORE_CAPTURE_ID, AFTER_CAPTURE_ID))["client_deltas"]
    moved = [row for row in rows if row["mac"] == CLIENT_MOVED_MAC]

    assert moved[0]["before_device"] == DEVICE_UNCHANGED_MAC
    assert moved[0]["after_device"] == DEVICE_CHANGED_MAC


# ---------------------------------------------------------------------------
# The skipped sections
# ---------------------------------------------------------------------------


def test_skipped_sections_is_a_list(signed_in_client: FlaskClient) -> None:
    """The body always carries a skipped section list, even an empty one.

    Args:
        signed_in_client: The signed-in client.
    """
    body = read_body(fetch_comparison(signed_in_client, BEFORE_CAPTURE_ID, AFTER_CAPTURE_ID))

    assert body["skipped_sections"] == []


def test_matching_digest_skips_the_device_section(signed_in_client: FlaskClient) -> None:
    """A matching device digest names the section and empties the device list.

    Why:
        An empty device table must read as a proof of no change. The name in
        the skipped list is the only signal that separates that case from a
        capture that held no device at all.

    Args:
        signed_in_client: The signed-in client.
    """
    body = read_body(fetch_comparison(signed_in_client, SKIPPED_BEFORE_ID, SKIPPED_AFTER_ID))

    assert DEVICES_SECTION in body["skipped_sections"]
    assert body["device_deltas"] == []


# ---------------------------------------------------------------------------
# The session guard
# ---------------------------------------------------------------------------


def test_comparison_refuses_a_request_with_no_session(wired_app: Flask) -> None:
    """The endpoint refuses a caller that holds no session.

    Args:
        wired_app: The wired application.
    """
    with wired_app.test_client() as client:
        response = fetch_comparison(client, BEFORE_CAPTURE_ID, AFTER_CAPTURE_ID)

    assert response.status_code == NOT_AUTHENTICATED_STATUS
    assert read_error_code(response) == NOT_AUTHENTICATED_CODE
