"""Contract tests for ``GET /api/comparisons/export``.

Why:
    Section 6 of ``contracts/http-api.md`` states that the download answers a
    file attachment or the ``bad_format`` refusal. A record keeper opens the
    comma-separated file in a spreadsheet, so the column order and the formula
    guard are part of the contract and not a detail of the writer.

Every value below is a literal. A test that imported a column name from the
module under test would agree with a rename and would prove nothing.
"""

from __future__ import annotations

import csv
import io
import json
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

EXPORT_PATH = "/api/comparisons/export"

BEFORE_FIELD = "before"
AFTER_FIELD = "after"
FORMAT_FIELD = "format"

OK_STATUS = 200
BAD_REQUEST_STATUS = 400

BAD_FORMAT_CODE = "bad_format"

CSV_FORMAT = "csv"
JSON_FORMAT = "json"

CSV_MEDIA_TYPE = "text/csv"
JSON_MEDIA_TYPE = "application/json"

CSV_FILENAME = "upgrade-comparison.csv"
JSON_FILENAME = "upgrade-comparison.json"

DISPOSITION_HEADER = "Content-Disposition"

# The seven columns of the download, in order.
EXPORT_COLUMNS = ["kind", "mac", "name", "outcome", "field", "before", "after"]

DEVICE_KIND = "device"
CLIENT_KIND = "client"

# A spreadsheet runs a cell that starts with one of these characters, so the
# writer puts a quotation mark in front of that cell.
FORMULA_NAME = "=SUM(A1:A9)"
FORMULA_GUARD = "'"

CAPTURE_LOADER_KEY = "CAPTURE_LOADER"

PROBE_EMAIL = "probe.operator@example.invalid"

# ---------------------------------------------------------------------------
# The two captures
# ---------------------------------------------------------------------------

BEFORE_CAPTURE_ID = "capture-before-0001"
AFTER_CAPTURE_ID = "capture-after-0001"

SITE_ID = "00000000-0000-0000-0000-0000000000bb"

DEVICE_CHANGED_MAC = "aabbcc000002"
DEVICE_ADDED_MAC = "aabbcc000004"
CLIENT_MOVED_MAC = "ddeeff000002"

OLD_VERSION = "0.14.29644"
NEW_VERSION = "0.16.30107"

VERSION_FIELD = "version"

STARTED_BEFORE = "2026-08-19T10:00:00+00:00"
STARTED_AFTER = "2026-08-19T10:25:00+00:00"

BEFORE_CAPTURE: dict[str, Any] = {
    "capture_id": BEFORE_CAPTURE_ID,
    "site_id": SITE_ID,
    "site_name": "Probe site",
    "org_name": "Probe organization",
    "role": "pre",
    "capture_status": "verified",
    "started_at": STARTED_BEFORE,
    "device_index": {
        DEVICE_CHANGED_MAC: {"name": "access-switch", "status": "connected", "version": OLD_VERSION},
    },
    "clients": {
        "wireless": [{"mac": CLIENT_MOVED_MAC, "hostname": "desk-two", "device_mac": DEVICE_CHANGED_MAC}],
    },
}

AFTER_CAPTURE: dict[str, Any] = {
    "capture_id": AFTER_CAPTURE_ID,
    "site_id": SITE_ID,
    "site_name": "Probe site",
    "org_name": "Probe organization",
    "role": "post",
    "capture_status": "verified",
    "started_at": STARTED_AFTER,
    "device_index": {
        DEVICE_CHANGED_MAC: {"name": "access-switch", "status": "connected", "version": NEW_VERSION},
        # WHY: The name arrives from the cloud, so the writer must guard it.
        DEVICE_ADDED_MAC: {"name": FORMULA_NAME, "status": "connected", "version": NEW_VERSION},
    },
    "clients": {
        "wireless": [{"mac": CLIENT_MOVED_MAC, "hostname": "desk-two", "device_mac": DEVICE_ADDED_MAC}],
    },
}


# ---------------------------------------------------------------------------
# The stand-in
# ---------------------------------------------------------------------------


class RecordingCaptureLoader:
    """Answers a capture read from a fixed map and records each request.

    Why:
        A contract test must reach no database. The route reads its capture
        loader from the application config, so this stand-in fills that seam.

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
def wired_app(portal_app: Flask) -> Flask:
    """Return the portal with the capture reader replaced.

    Args:
        portal_app: The portal application.

    Returns:
        The wired application.
    """
    loader = RecordingCaptureLoader({BEFORE_CAPTURE_ID: BEFORE_CAPTURE, AFTER_CAPTURE_ID: AFTER_CAPTURE})
    portal_app.config[CAPTURE_LOADER_KEY] = loader
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


def fetch_download(client: FlaskClient, export_format: str) -> TestResponse:
    """Ask the portal for one comparison download.

    Args:
        client: The signed-in client.
        export_format: The format value to send.

    Returns:
        The answer.
    """
    values = {BEFORE_FIELD: BEFORE_CAPTURE_ID, AFTER_FIELD: AFTER_CAPTURE_ID, FORMAT_FIELD: export_format}
    return client.get(EXPORT_PATH, query_string=values)


def read_csv_rows(response: TestResponse) -> list[list[str]]:
    """Return every line of a comma-separated download.

    Args:
        response: The answer to read.

    Returns:
        The header line and each data line, as lists of cells.
    """
    return list(csv.reader(io.StringIO(response.get_data(as_text=True))))


def read_json_rows(response: TestResponse) -> list[dict[str, Any]]:
    """Return every row of a JSON download.

    Why:
        The reader parses the body text rather than the response helper,
        because the answer is a file and not an ordinary JSON reply.

    Args:
        response: The answer to read.

    Returns:
        The rows.
    """
    rows: Any = json.loads(response.get_data(as_text=True))
    assert isinstance(rows, list)
    return rows


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


# ---------------------------------------------------------------------------
# The comma-separated download
# ---------------------------------------------------------------------------


def test_csv_download_answers_two_hundred(signed_in_client: FlaskClient) -> None:
    """The comma-separated download answers 200.

    Args:
        signed_in_client: The signed-in client.
    """
    response = fetch_download(signed_in_client, CSV_FORMAT)

    assert response.status_code == OK_STATUS


def test_csv_download_names_the_media_type(signed_in_client: FlaskClient) -> None:
    """The comma-separated download carries the comma-separated media type.

    Args:
        signed_in_client: The signed-in client.
    """
    response = fetch_download(signed_in_client, CSV_FORMAT)

    assert response.mimetype == CSV_MEDIA_TYPE


def test_csv_download_arrives_as_an_attachment(signed_in_client: FlaskClient) -> None:
    """The browser saves the comma-separated file rather than showing it.

    Args:
        signed_in_client: The signed-in client.
    """
    response = fetch_download(signed_in_client, CSV_FORMAT)
    disposition = response.headers.get(DISPOSITION_HEADER, "")

    assert disposition.startswith("attachment")
    assert CSV_FILENAME in disposition


def test_csv_download_starts_with_the_column_names(signed_in_client: FlaskClient) -> None:
    """The first line of the file names the seven columns, in order.

    Why:
        The record keeper reads the file with a script that reads the columns
        by place. A new order would break every stored script.

    Args:
        signed_in_client: The signed-in client.
    """
    lines = read_csv_rows(fetch_download(signed_in_client, CSV_FORMAT))

    assert lines[0] == EXPORT_COLUMNS


def test_csv_download_holds_the_device_and_the_client(signed_in_client: FlaskClient) -> None:
    """The file reports both halves of the comparison.

    Args:
        signed_in_client: The signed-in client.
    """
    lines = read_csv_rows(fetch_download(signed_in_client, CSV_FORMAT))
    kinds = {line[0] for line in lines[1:] if line}

    assert DEVICE_KIND in kinds
    assert CLIENT_KIND in kinds


def test_csv_download_reports_the_version_change(signed_in_client: FlaskClient) -> None:
    """The changed device reports the old version and the new version.

    Args:
        signed_in_client: The signed-in client.
    """
    lines = read_csv_rows(fetch_download(signed_in_client, CSV_FORMAT))
    versions = [line for line in lines[1:] if line and line[1] == DEVICE_CHANGED_MAC and line[4] == VERSION_FIELD]

    assert versions
    assert versions[0][5] == OLD_VERSION
    assert versions[0][6] == NEW_VERSION


def test_csv_download_guards_a_formula_cell(signed_in_client: FlaskClient) -> None:
    """A device name that would run as a formula carries a guard character.

    Why:
        The name arrives from the cloud. A spreadsheet runs a cell that starts
        with an equals sign, so an unguarded cell would run code on the
        computer of the record keeper.

    Args:
        signed_in_client: The signed-in client.
    """
    lines = read_csv_rows(fetch_download(signed_in_client, CSV_FORMAT))
    guarded = [line for line in lines[1:] if line and line[1] == DEVICE_ADDED_MAC]

    assert guarded
    assert guarded[0][2] == FORMULA_GUARD + FORMULA_NAME


# ---------------------------------------------------------------------------
# The JSON download
# ---------------------------------------------------------------------------


def test_json_download_answers_two_hundred(signed_in_client: FlaskClient) -> None:
    """The JSON download answers 200.

    Args:
        signed_in_client: The signed-in client.
    """
    response = fetch_download(signed_in_client, JSON_FORMAT)

    assert response.status_code == OK_STATUS


def test_json_download_names_the_media_type(signed_in_client: FlaskClient) -> None:
    """The JSON download carries the JSON media type.

    Args:
        signed_in_client: The signed-in client.
    """
    response = fetch_download(signed_in_client, JSON_FORMAT)

    assert response.mimetype == JSON_MEDIA_TYPE


def test_json_download_arrives_as_an_attachment(signed_in_client: FlaskClient) -> None:
    """The browser saves the JSON file rather than showing it.

    Args:
        signed_in_client: The signed-in client.
    """
    response = fetch_download(signed_in_client, JSON_FORMAT)
    disposition = response.headers.get(DISPOSITION_HEADER, "")

    assert disposition.startswith("attachment")
    assert JSON_FILENAME in disposition


def test_json_download_holds_the_same_seven_columns(signed_in_client: FlaskClient) -> None:
    """Each JSON row holds the same seven names as a comma-separated line.

    Why:
        A program that reads one format must read the other without a second
        mapping table.

    Args:
        signed_in_client: The signed-in client.
    """
    rows = read_json_rows(fetch_download(signed_in_client, JSON_FORMAT))

    assert rows
    for row in rows:
        assert set(EXPORT_COLUMNS) <= set(row)


def test_json_download_reports_the_same_row_count(signed_in_client: FlaskClient) -> None:
    """The two formats report the same number of rows.

    Args:
        signed_in_client: The signed-in client.
    """
    lines = read_csv_rows(fetch_download(signed_in_client, CSV_FORMAT))
    rows = read_json_rows(fetch_download(signed_in_client, JSON_FORMAT))

    assert len(rows) == len(lines) - 1  # WHY: The first line of the file names the columns.


# ---------------------------------------------------------------------------
# The format refusal
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("wanted", ["xml", "text", "csvv", "comma"])
def test_an_unknown_format_answers_bad_format(signed_in_client: FlaskClient, wanted: str) -> None:
    """The portal refuses a format that it does not write.

    Args:
        signed_in_client: The signed-in client.
        wanted: The format value to send.
    """
    response = fetch_download(signed_in_client, wanted)

    assert response.status_code == BAD_REQUEST_STATUS
    assert read_error_code(response) == BAD_FORMAT_CODE


def test_a_request_with_no_format_answers_bad_format(signed_in_client: FlaskClient) -> None:
    """A request that names no format reads as a mistake and not as a default.

    Why:
        A default format would send one file to a caller who asked for the
        other. The refusal makes the caller state the format.

    Args:
        signed_in_client: The signed-in client.
    """
    values = {BEFORE_FIELD: BEFORE_CAPTURE_ID, AFTER_FIELD: AFTER_CAPTURE_ID}
    response = signed_in_client.get(EXPORT_PATH, query_string=values)

    assert response.status_code == BAD_REQUEST_STATUS
    assert read_error_code(response) == BAD_FORMAT_CODE


@pytest.mark.parametrize("wanted", ["CSV", " csv", "Json "])
def test_the_format_ignores_case_and_spaces(signed_in_client: FlaskClient, wanted: str) -> None:
    """A format value with capital letters or spaces still names a file.

    Why:
        The value arrives in the address bar, where a stray space is common.
        The refusal must fire for a real mistake only.

    Args:
        signed_in_client: The signed-in client.
        wanted: The format value to send.
    """
    response = fetch_download(signed_in_client, wanted)

    assert response.status_code == OK_STATUS
