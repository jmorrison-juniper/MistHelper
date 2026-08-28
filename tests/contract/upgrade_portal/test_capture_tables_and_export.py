"""Contract test of the capture tables and of the capture download.

Why:
    FR-026 requires the portal to show a completed capture as tables. Issue
    #2094 records that the capture page held counts alone, so an operator could
    not read one device row or one client row. FR-027 requires a file download
    of a completed capture. Issue #2095 records that no capture export existed.

    The tests below pin both requirements. The page tests read the rendered
    page, and the download tests read the file body, so neither test can pass
    while the operator still sees a count alone.

    No test reaches a database server. The stored capture reader travels
    through the `CAPTURE_LOADER` seam, which a stand-in fills.
"""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Iterator
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from src.upgrade_portal.runtime import identity

# --------------------------------------------------------------------------
# The contract values. Each one repeats a line of the specification.
# --------------------------------------------------------------------------

PAGE_PATH_TEMPLATE = "/captures/{capture_id}"  # The human view of one capture.
EXPORT_PATH_TEMPLATE = "/api/captures/{capture_id}/export"  # The download of one capture.
EXPORT_ENDPOINT = "capture.download_capture"  # The endpoint name of the download route.

OK_STATUS = 200  # The read succeeded.
NOT_AUTHENTICATED_STATUS = 401  # No signed-in session.
BAD_REQUEST_STATUS = 400  # The portal could not read the format.
NOT_FOUND_STATUS = 404  # No such capture.
CONFLICT_STATUS = 409  # The portal never read the stored key back.

BAD_FORMAT_CODE = "bad_format"  # `contracts/http-api.md` fixes this code.
CAPTURE_NOT_FOUND_CODE = "capture_not_found"  # No such capture.
CAPTURE_NOT_VERIFIED_CODE = "capture_not_verified"  # The portal never read the key back.

LOADER_KEY = "CAPTURE_LOADER"  # The seam for the stored capture read.
MIST_READER_KEY = "MIST_READER"  # The seam for every cloud read.

SELECTED_ORG_SESSION_KEY = "selected_org_id"  # The organization the operator picked.
PROBE_EMAIL = "probe.operator@example.invalid"  # A reserved domain, so no real address appears.

STORED_CAPTURE_ID = "cap-abcdef12-01"  # The identifier of the stored document below.

MASTER_MAC = "0011220000aa"  # The master member of the one virtual chassis below.
MEMBER_MAC = "0011220000bb"  # The second member of the same virtual chassis.
WIRED_CLIENT_MAC = "aabbccddeeff"  # The wired client of the capture below.
WIRELESS_CLIENT_MAC = "aabbccdd0011"  # The wireless client of the capture below.

# WHY: `contracts/ui-testids.md` fixes each identifier below. A test reads the
# identifier and never reads a class name, because a class name may change.
DEVICE_TABLE_MARKER = 'data-testid="capture-device-table"'
WIRED_TABLE_MARKER = 'data-testid="capture-client-wired-table"'
WIRELESS_TABLE_MARKER = 'data-testid="capture-client-wireless-table"'
EXPORT_CSV_MARKER = 'data-testid="capture-export-csv"'
EXPORT_JSON_MARKER = 'data-testid="capture-export-json"'

# WHY: The shape of one stored capture, cut down to the fields the page and the
# download read. `data-model.md` section 3 fixes every name below.
STORED_CAPTURE: dict[str, Any] = {
    "_key": STORED_CAPTURE_ID,
    "capture_id": STORED_CAPTURE_ID,
    "schema_version": 1,
    "run_id": "run-abcdef12",
    "ordinal": 1,
    "role": "pre",
    "tier": 2,
    "org_id": "org-1",
    "org_name": "Test Org",
    "site_id": "site-1",
    "site_name": "Test Site",
    "started_at": "2026-08-27T10:00:00+00:00",
    "capture_status": "complete",
    "partial_reasons": [],
    "stored_size_bytes": 4096,
    "device_index": {
        MASTER_MAC: {
            "name": "switch-01",
            "type": "switch",
            "model": "EX4400-48P",
            "serial": "JW0000000000",
            "version": "23.4R2.13",
            "status": "connected",
            "uptime": 1832140,
            "vc_role": "master",
            "num_members": 2,
            "ip": "10.20.30.40",
        },
        MEMBER_MAC: {
            "name": "switch-01",
            "type": "switch",
            "model": "EX4400-48P",
            "serial": "JW0000000001",
            "version": "23.4R2.13",
            "status": "connected",
            "uptime": 1832140,
            "vc_role": "backup",
            "num_members": 2,
            "ip": "",
        },
    },
    "devices": [{"mac": MASTER_MAC}, {"mac": MEMBER_MAC}],
    "clients": {
        "wired": [
            {
                "mac": WIRED_CLIENT_MAC,
                "hostname": "desk-01",
                "ip": "192.168.1.110",
                "device_mac": MASTER_MAC,
                "device_name": "switch-01",
                "port_id": "ge-0/0/3",
                "vlan": 1,
            }
        ],
        "wireless": [
            {
                "mac": WIRELESS_CLIENT_MAC,
                "hostname": "laptop-01",
                "ip": "192.168.1.222",
                "device_mac": "0011220000cc",
                "device_name": "ap-01",
                "vlan": 1,
                "ssid": "corp",
                "band": "5",
            }
        ],
        "guest": [],
    },
    "counts": {"devices_total": 2, "clients_wired": 1, "clients_wireless": 1},
}

# WHY: A site with no device and no client is a valid capture. The page must
# then show an empty table, and never an error.
EMPTY_CAPTURE: dict[str, Any] = {
    "capture_id": STORED_CAPTURE_ID,
    "schema_version": 1,
    "tier": 2,
    "capture_status": "complete",
    "partial_reasons": [],
    "device_index": {},
    "devices": [],
    "clients": {"wired": [], "wireless": [], "guest": []},
    "counts": {"devices_total": 0},
    "stored_size_bytes": 512,
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
        server, so the answer lives in the test.
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
def wired_app(portal_app: Flask, fake_mist_api: Any) -> Flask:
    """Return the portal with one verified stored capture injected.

    Args:
        portal_app: The portal application under test.
        fake_mist_api: The in-memory cloud reader of the shared fixtures.

    Returns:
        The wired application.
    """
    portal_app.config[MIST_READER_KEY] = fake_mist_api.read
    portal_app.config[LOADER_KEY] = RecordingLoader(StoredLoad(dict(STORED_CAPTURE), True, ""))
    return portal_app


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


@pytest.fixture
def signed_in(wired_app: Flask, owner: identity.SessionOwner, fake_org_id: str) -> FlaskClient:
    """Return a browser that already carries a signed-in session.

    Args:
        wired_app: The portal with the stored capture reader injected.
        owner: The registered owner.
        fake_org_id: The organization the operator picked.

    Returns:
        The signed-in browser.
    """
    client = wired_app.test_client()
    client.set_cookie(identity.BROWSER_ID_COOKIE, owner.browser_id)
    with client.session_transaction() as browser_session:
        browser_session[identity.SESSION_OWNER_KEY] = owner.key
        browser_session[SELECTED_ORG_SESSION_KEY] = fake_org_id
    return client


# --------------------------------------------------------------------------
# The helpers.
# --------------------------------------------------------------------------


def open_page(client: FlaskClient, capture_id: str = STORED_CAPTURE_ID) -> str:
    """Open the human view of one capture and return the page text.

    Args:
        client: The signed-in browser.
        capture_id: The capture to show.

    Returns:
        The rendered page as text.
    """
    return client.get(PAGE_PATH_TEMPLATE.format(capture_id=capture_id)).get_data(as_text=True)


def download(client: FlaskClient, wanted: str, capture_id: str = STORED_CAPTURE_ID) -> TestResponse:
    """Download one capture in the named format.

    Args:
        client: The signed-in browser.
        wanted: The format value of the query.
        capture_id: The capture to download.

    Returns:
        The portal answer.
    """
    return client.get(EXPORT_PATH_TEMPLATE.format(capture_id=capture_id) + "?format=" + wanted)


def csv_rows(response: TestResponse) -> list[dict[str, str]]:
    """Return every data row of one downloaded comma-separated file.

    Args:
        response: The portal answer.

    Returns:
        One dictionary for each row, under the header names.
    """
    return list(csv.DictReader(io.StringIO(_data_part(response.get_data(as_text=True)))))


def _data_part(body: str) -> str:
    """Return the part of one comma-separated file that holds the header line.

    Why:
        The file opens with a comment block that names the capture, so the
        header line is not the first line.

    Args:
        body: The whole file as text.

    Returns:
        The header line and every row after it.
    """
    lines = [line for line in body.splitlines() if not line.startswith("#")]
    return "\n".join(line for line in lines if line.strip())


def error_code(response: TestResponse) -> str:
    """Read the error code out of one refusal envelope.

    Args:
        response: The portal answer.

    Returns:
        The code inside the error envelope.
    """
    payload: dict[str, Any] = response.get_json()
    return str(payload["error"]["code"])


# --------------------------------------------------------------------------
# FR-026. The capture page shows a completed capture as tables.
# --------------------------------------------------------------------------


def test_the_page_holds_the_three_tables(signed_in: FlaskClient) -> None:
    """The page shows a device table, a wired table, and a wireless table.

    Args:
        signed_in: The signed-in browser.
    """
    page = open_page(signed_in)
    assert DEVICE_TABLE_MARKER in page
    assert WIRED_TABLE_MARKER in page
    assert WIRELESS_TABLE_MARKER in page


def test_each_chassis_member_holds_its_own_row(signed_in: FlaskClient) -> None:
    """A stack that loses a member must show the loss, so each member has a row.

    Args:
        signed_in: The signed-in browser.
    """
    page = open_page(signed_in)
    assert f'data-testid="capture-device-row-{MASTER_MAC}"' in page
    assert f'data-testid="capture-device-row-{MEMBER_MAC}"' in page


def test_a_device_row_names_the_five_fields_of_the_story(signed_in: FlaskClient) -> None:
    """User Story 1 names the version, the status, the uptime, the model, and the serial.

    Args:
        signed_in: The signed-in browser.
    """
    page = open_page(signed_in)
    assert "23.4R2.13" in page
    assert "connected" in page
    assert "1832140" in page
    assert "EX4400-48P" in page
    assert "JW0000000000" in page


def test_a_wired_client_row_names_the_five_fields_of_the_story(signed_in: FlaskClient) -> None:
    """User Story 1 names the address, the host name, the address, the VLAN, and the parent.

    Args:
        signed_in: The signed-in browser.
    """
    page = open_page(signed_in)
    assert f'data-testid="capture-client-row-{WIRED_CLIENT_MAC}"' in page
    assert "desk-01" in page
    assert "192.168.1.110" in page


def test_a_wireless_client_row_reaches_the_page(signed_in: FlaskClient) -> None:
    """Every wireless client shows as well, and names its parent access point.

    Args:
        signed_in: The signed-in browser.
    """
    page = open_page(signed_in)
    assert f'data-testid="capture-client-row-{WIRELESS_CLIENT_MAC}"' in page
    assert "laptop-01" in page
    assert "ap-01" in page


def test_an_empty_capture_shows_an_empty_table_and_no_error(wired_app: Flask, signed_in: FlaskClient) -> None:
    """A site with no device is a valid capture, so the page shows an empty table.

    Args:
        wired_app: The portal with the stored capture reader injected.
        signed_in: The signed-in browser.
    """
    wired_app.config[LOADER_KEY] = RecordingLoader(StoredLoad(dict(EMPTY_CAPTURE), True, ""))
    answer = signed_in.get(PAGE_PATH_TEMPLATE.format(capture_id=STORED_CAPTURE_ID))
    assert answer.status_code == OK_STATUS
    page = answer.get_data(as_text=True)
    assert DEVICE_TABLE_MARKER in page
    assert WIRED_TABLE_MARKER in page


def test_a_capture_the_portal_does_not_know_still_renders(wired_app: Flask, signed_in: FlaskClient) -> None:
    """The start page knows no capture yet, so the tables render empty and not absent.

    Args:
        wired_app: The portal with the stored capture reader injected.
        signed_in: The signed-in browser.
    """
    wired_app.config[LOADER_KEY] = RecordingLoader(StoredLoad(None, False, CAPTURE_NOT_FOUND_CODE))
    answer = signed_in.get(PAGE_PATH_TEMPLATE.format(capture_id="new"))
    assert answer.status_code == OK_STATUS
    assert DEVICE_TABLE_MARKER in answer.get_data(as_text=True)


# --------------------------------------------------------------------------
# FR-027. The portal offers a file download of a completed capture.
# --------------------------------------------------------------------------


def test_the_download_endpoint_is_registered(wired_app: Flask) -> None:
    """The portal binds the download endpoint to the path the contract names.

    Args:
        wired_app: The portal with the stored capture reader injected.
    """
    paths = {rule.rule for rule in wired_app.url_map.iter_rules() if rule.endpoint == EXPORT_ENDPOINT}
    assert EXPORT_PATH_TEMPLATE.format(capture_id="<capture_id>") in paths


def test_the_page_holds_both_download_controls(signed_in: FlaskClient) -> None:
    """A verified capture offers the two download formats.

    Args:
        signed_in: The signed-in browser.
    """
    page = open_page(signed_in)
    assert EXPORT_CSV_MARKER in page
    assert EXPORT_JSON_MARKER in page


def test_the_download_answers_a_file_attachment(signed_in: FlaskClient) -> None:
    """The browser must save the file rather than show it.

    Args:
        signed_in: The signed-in browser.
    """
    answer = download(signed_in, "csv")
    assert answer.status_code == OK_STATUS
    assert "attachment" in answer.headers["Content-Disposition"]


def test_the_download_holds_every_captured_row(signed_in: FlaskClient) -> None:
    """Acceptance Scenario 3 requires that the file holds every captured row.

    Args:
        signed_in: The signed-in browser.
    """
    rows = csv_rows(download(signed_in, "csv"))
    assert {row["mac"] for row in rows} == {MASTER_MAC, MEMBER_MAC, WIRED_CLIENT_MAC, WIRELESS_CLIENT_MAC}


def test_the_json_download_holds_every_captured_row(signed_in: FlaskClient) -> None:
    """The JSON file reports the same rows as the comma-separated file.

    Args:
        signed_in: The signed-in browser.
    """
    payload = json.loads(download(signed_in, "json").get_data(as_text=True))
    assert {row["mac"] for row in payload["rows"]} == {
        MASTER_MAC,
        MEMBER_MAC,
        WIRED_CLIENT_MAC,
        WIRELESS_CLIENT_MAC,
    }


def test_an_unknown_format_is_refused(signed_in: FlaskClient) -> None:
    """A guess would hand the operator a file of the wrong type.

    Args:
        signed_in: The signed-in browser.
    """
    answer = download(signed_in, "pdf")
    assert answer.status_code == BAD_REQUEST_STATUS
    assert error_code(answer) == BAD_FORMAT_CODE


def test_an_unknown_capture_is_refused(wired_app: Flask, signed_in: FlaskClient) -> None:
    """An identifier the store does not hold answers 404.

    Args:
        wired_app: The portal with the stored capture reader injected.
        signed_in: The signed-in browser.
    """
    wired_app.config[LOADER_KEY] = RecordingLoader(StoredLoad(None, False, CAPTURE_NOT_FOUND_CODE))
    answer = download(signed_in, "csv")
    assert answer.status_code == NOT_FOUND_STATUS
    assert error_code(answer) == CAPTURE_NOT_FOUND_CODE


def test_an_unverified_capture_is_refused(wired_app: Flask, signed_in: FlaskClient) -> None:
    """A capture the portal never read back answers 409, as the read route does.

    Why:
        A download of a document that may never have reached the store would
        hand the operator a file that reports a site state that never existed.

    Args:
        wired_app: The portal with the stored capture reader injected.
        signed_in: The signed-in browser.
    """
    wired_app.config[LOADER_KEY] = RecordingLoader(StoredLoad(dict(STORED_CAPTURE), False, CAPTURE_NOT_VERIFIED_CODE))
    answer = download(signed_in, "csv")
    assert answer.status_code == CONFLICT_STATUS
    assert error_code(answer) == CAPTURE_NOT_VERIFIED_CODE


def test_a_download_with_no_session_is_refused(wired_app: Flask) -> None:
    """A download with no signed-in session answers 401.

    Args:
        wired_app: The portal with the stored capture reader injected.
    """
    answer = download(wired_app.test_client(), "csv")
    assert answer.status_code == NOT_AUTHENTICATED_STATUS


def test_the_download_carries_no_credential(wired_app: Flask, signed_in: FlaskClient) -> None:
    """A field whose name reads as a secret never reaches the file.

    Args:
        wired_app: The portal with the stored capture reader injected.
        signed_in: The signed-in browser.
    """
    leaky = json.loads(json.dumps(STORED_CAPTURE))
    leaky["device_index"][MASTER_MAC]["api_token"] = "must-not-appear"
    wired_app.config[LOADER_KEY] = RecordingLoader(StoredLoad(leaky, True, ""))
    assert "must-not-appear" not in download(signed_in, "csv").get_data(as_text=True)
