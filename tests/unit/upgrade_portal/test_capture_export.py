"""Unit tests for the capture download in both formats.

Why:
    FR-027 requires a file download of a completed capture, and User Story 1
    Acceptance Scenario 3 requires that the file holds every captured row. The
    tests below prove that every device row and every client row reaches the
    file, and that the two safety controls of the comparison download hold here
    as well.

    The downloaded file leaves the portal. An operator attaches it to a change
    record, so a credential in that file would travel further than any other
    leak of this feature. A spreadsheet also runs a cell that starts with an
    equals sign, so the writer disarms every cell.

    Every test feeds plain records. No test opens a socket, writes a file,
    reads the `.env` file, or names a real credential.
"""

from __future__ import annotations

import csv
import io
import json
from typing import Any

import pytest

from src.upgrade_portal.capture import export
from src.upgrade_portal.compare import download as compare_download

MASTER_MAC = "0011220000aa"  # The master member of the one virtual chassis below.
MEMBER_MAC = "0011220000bb"  # The second member of the same virtual chassis.
ACCESS_POINT_MAC = "0011220000cc"  # The access point that serves the wireless client.
WIRED_CLIENT_MAC = "aabbccddeeff"  # The wired client of the capture below.
WIRELESS_CLIENT_MAC = "aabbccdd0011"  # The wireless client of the capture below.

CAPTURE_ID = "cap-abcdef12-01"  # The identifier of the capture below.
RUN_ID = "run-abcdef12"  # The run that owns the capture below.
ORG_NAME = "Test Org"  # The organization name that the file must carry.
SITE_NAME = "Test Site"  # The site name that the file must carry.
STARTED_AT = "2026-08-27T10:00:00+00:00"  # The moment of the capture, in UTC.

RUNNING_VERSION = "23.4R2.13"  # The firmware version of the master member.


def _capture() -> dict[str, Any]:
    """Return one stored capture with two devices and two clients.

    Why:
        Every test below reads the same capture, so one builder keeps the row
        counts and the field values in a single place.

    Returns:
        One stored capture document.
    """
    return {
        "capture_id": CAPTURE_ID,
        "run_id": RUN_ID,
        "role": "pre",
        "org_id": "org-1",
        "org_name": ORG_NAME,
        "site_id": "site-1",
        "site_name": SITE_NAME,
        "started_at": STARTED_AT,
        "device_index": {
            MASTER_MAC: {
                "name": "switch-01",
                "type": "switch",
                "model": "EX4400-48P",
                "serial": "JW0000000000",
                "version": RUNNING_VERSION,
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
                "version": RUNNING_VERSION,
                "status": "connected",
                "uptime": 1832140,
                "vc_role": "backup",
                "num_members": 2,
                "ip": "",
            },
        },
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
                    "device_mac": ACCESS_POINT_MAC,
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


def _csv_rows(body: str) -> list[dict[str, str]]:
    """Return every data row of one comma-separated file.

    Args:
        body: The whole file as text.

    Returns:
        One dictionary for each row, under the header names.
    """
    return list(csv.DictReader(io.StringIO(body)))


# --------------------------------------------------------------------------
# Every captured row reaches the file.
# --------------------------------------------------------------------------


def test_the_file_holds_every_device_row() -> None:
    """Each chassis member writes its own row, so a lost member shows."""
    rows = export.build_rows(_capture())
    devices = [row for row in rows if row.kind == export.KIND_DEVICE]
    assert {row.mac for row in devices} == {MASTER_MAC, MEMBER_MAC}


def test_the_file_holds_every_client_row() -> None:
    """The wired client and the wireless client both write a row."""
    rows = export.build_rows(_capture())
    clients = [row for row in rows if row.kind != export.KIND_DEVICE]
    assert {row.mac for row in clients} == {WIRED_CLIENT_MAC, WIRELESS_CLIENT_MAC}


def test_a_device_row_names_the_five_fields_of_the_story() -> None:
    """User Story 1 names the version, the status, the uptime, the model, and the serial."""
    rows = _csv_rows(export.export_capture(_capture(), export.FORMAT_CSV).body)
    master = next(row for row in rows if row["mac"] == MASTER_MAC)
    assert master["version"] == RUNNING_VERSION
    assert master["status"] == "connected"
    assert master["uptime"] == "1832140"
    assert master["model"] == "EX4400-48P"
    assert master["serial"] == "JW0000000000"


def test_a_client_row_names_the_five_fields_of_the_story() -> None:
    """User Story 1 names the address, the host name, the address, the VLAN, and the parent."""
    rows = _csv_rows(export.export_capture(_capture(), export.FORMAT_CSV).body)
    client = next(row for row in rows if row["mac"] == WIRED_CLIENT_MAC)
    assert client["hostname"] == "desk-01"
    assert client["ip"] == "192.168.1.110"
    assert client["vlan"] == "1"
    assert client["parent_device"] == "switch-01"
    assert client["kind"] == export.KIND_CLIENT_WIRED


def test_an_empty_capture_writes_a_header_and_no_row() -> None:
    """A site with no device and no client is a valid capture, not a fault."""
    result = export.export_capture({"capture_id": CAPTURE_ID}, export.FORMAT_CSV)
    assert result.ok
    assert _csv_rows(result.body) == []


# --------------------------------------------------------------------------
# Issue #2443. The tier 3 rows.
# --------------------------------------------------------------------------


def _tier3_capture() -> dict[str, Any]:
    """Return one stored capture that also holds a tier 3 `extras` map.

    Returns:
        One stored capture document.
    """
    capture = _capture()
    capture["extras"] = {
        "switch_ports": [{"mac": MASTER_MAC, "port_id": "ge-0/0/1", "up": True}],
        "poe": [{"mac": MASTER_MAC, "port_id": "ge-0/0/1", "poe_on": True}],
        "radios": [{"mac": ACCESS_POINT_MAC, "band": "5", "channel": 36}],
        "tunnels": [{"mac": MASTER_MAC, "tunnel_name": "vpn-01", "up": True}],
        "bgp_peers": [{"mac": MASTER_MAC, "neighbor": "10.0.0.1", "state": "Established"}],
        "alarms": [{"type": "device_down", "severity": "critical", "hostnames": ["switch-01"]}],
    }
    return capture


def test_the_file_holds_a_row_for_every_tier3_section() -> None:
    """A tier 3 capture must export every section that Issue #2443 reports missing."""
    rows = export.build_rows(_tier3_capture())
    kinds = {row.kind for row in rows}
    assert export.KIND_SWITCH_PORT in kinds
    assert export.KIND_POE in kinds
    assert export.KIND_RADIO in kinds
    assert export.KIND_TUNNEL in kinds
    assert export.KIND_BGP_PEER in kinds
    assert export.KIND_ALARM in kinds


def test_a_tier2_capture_writes_no_tier3_row() -> None:
    """A tier 2 capture holds no `extras` key, so the file must carry none of those rows."""
    rows = export.build_rows(_capture())
    kinds = {row.kind for row in rows}
    assert not kinds & {
        export.KIND_SWITCH_PORT,
        export.KIND_POE,
        export.KIND_RADIO,
        export.KIND_TUNNEL,
        export.KIND_BGP_PEER,
        export.KIND_ALARM,
    }


def test_a_tier3_section_with_no_row_writes_no_row() -> None:
    """A section that read zero records still writes zero rows, and no error."""
    capture = _tier3_capture()
    capture["extras"]["tunnels"] = []
    rows = export.build_rows(capture)
    assert not any(row.kind == export.KIND_TUNNEL for row in rows)


def test_an_alarm_row_joins_a_list_field_into_one_cell() -> None:
    """The alarm `hostnames` field is a list, and the cell must read as one line of text."""
    rows = _csv_rows(export.export_capture(_tier3_capture(), export.FORMAT_CSV).body)
    alarm = next(row for row in rows if row["kind"] == export.KIND_ALARM)
    assert alarm["hostnames"] == "switch-01"


def test_a_tier3_row_still_names_the_capture() -> None:
    """A tier 3 row is a row of the same file, so it carries the same five naming values."""
    rows = _csv_rows(export.export_capture(_tier3_capture(), export.FORMAT_CSV).body)
    switch_port = next(row for row in rows if row["kind"] == export.KIND_SWITCH_PORT)
    assert switch_port["org_name"] == ORG_NAME
    assert switch_port["capture_id"] == CAPTURE_ID


def test_a_credential_tier3_field_never_reaches_a_row() -> None:
    """The same credential filter that guards a device row guards a tier 3 row."""
    capture = _tier3_capture()
    capture["extras"]["radios"][0]["api_token"] = "must-not-appear"
    body = export.export_capture(capture, export.FORMAT_JSON).body
    assert "must-not-appear" not in body


# --------------------------------------------------------------------------
# The file names the capture.
# --------------------------------------------------------------------------


def test_the_json_file_names_the_capture() -> None:
    """FR-027 requires the organization, the site, the capture, the role, and the moment."""
    payload = json.loads(export.export_capture(_capture(), export.FORMAT_JSON).body)
    assert payload["capture"]["org_name"] == ORG_NAME
    assert payload["capture"]["site_name"] == SITE_NAME
    assert payload["capture"]["capture_id"] == CAPTURE_ID
    assert payload["capture"]["role"] == "pre"
    assert payload["capture"]["captured_at"] == STARTED_AT


def test_the_csv_file_names_the_capture_on_every_row() -> None:
    """The comma-separated file carries the same five values as leading columns."""
    body = export.export_capture(_capture(), export.FORMAT_CSV).body
    assert body.startswith(export.HEADER_MARKER)  # The header line opens the file, with no preamble.
    rows = _csv_rows(body)
    assert rows, "the capture holds rows, so the file must hold rows"
    for row in rows:  # Every row names its own capture, so one row alone is still traceable.
        assert row["org_name"] == ORG_NAME
        assert row["site_name"] == SITE_NAME
        assert row["capture_id"] == CAPTURE_ID
        assert row["role"] == "pre"
        assert row["captured_at"] == STARTED_AT


def test_the_json_file_holds_every_row() -> None:
    """The JSON file and the comma-separated file report the same row count."""
    payload = json.loads(export.export_capture(_capture(), export.FORMAT_JSON).body)
    assert len(payload["rows"]) == len(_csv_rows(export.export_capture(_capture(), export.FORMAT_CSV).body))


def test_the_file_name_carries_the_capture_identifier() -> None:
    """An operator downloads two captures of one run, so the names must differ."""
    result = export.export_capture(_capture(), export.FORMAT_CSV)
    assert CAPTURE_ID in result.filename


# --------------------------------------------------------------------------
# The two safety controls.
# --------------------------------------------------------------------------


def test_a_cell_that_reads_as_a_formula_is_disarmed() -> None:
    """A spreadsheet must never run a device name that came from the cloud."""
    capture = _capture()
    capture["device_index"][MASTER_MAC]["name"] = "=cmd|' /c calc'!A0"
    rows = _csv_rows(export.export_capture(capture, export.FORMAT_CSV).body)
    master = next(row for row in rows if row["mac"] == MASTER_MAC)
    assert master["name"].startswith("'")


@pytest.mark.parametrize("leader", ["=", "+", "-", "@"])
def test_every_formula_leader_is_disarmed(leader: str) -> None:
    """The guard covers each of the four characters that start a formula.

    Args:
        leader: One character that starts a formula.
    """
    assert export.disarm_cell(leader + "danger").startswith("'")


def test_a_negative_number_stays_a_number() -> None:
    """A minus sign starts a negative number as well, so a number keeps its form."""
    assert export.disarm_cell("-12") == "-12"


def test_a_credential_field_never_reaches_a_row() -> None:
    """A field whose name reads as a secret drops out of the file."""
    capture = _capture()
    capture["device_index"][MASTER_MAC]["api_token"] = "must-not-appear"
    body = export.export_capture(capture, export.FORMAT_JSON).body
    assert "must-not-appear" not in body


def test_a_credential_client_field_never_reaches_a_row() -> None:
    """The same rule holds for a client field."""
    capture = _capture()
    capture["clients"]["wired"][0]["password"] = "must-not-appear"
    body = export.export_capture(capture, export.FORMAT_JSON).body
    assert "must-not-appear" not in body


def test_the_credential_word_list_matches_the_comparison_download() -> None:
    """The two downloads guard the same words, so neither can drift alone.

    Why:
        This module copies the two controls of `compare/download.py`, because
        an import would point the capture package at the comparison package
        that already reads it. This test fails when either copy changes alone.
    """
    assert export.CREDENTIAL_WORDS == compare_download.CREDENTIAL_WORDS


def test_the_credential_test_matches_the_comparison_download() -> None:
    """The two downloads answer the same way for the same field name."""
    for name in ("mac", "api_token", "PASSWORD", "vlan", "secret_key"):
        assert export.is_credential_field(name) == compare_download.is_credential_field(name)


# --------------------------------------------------------------------------
# The format rule.
# --------------------------------------------------------------------------


def test_an_unknown_format_is_refused() -> None:
    """A guess would hand the operator a file of the wrong type."""
    result = export.export_capture(_capture(), "pdf")
    assert not result.ok
    assert result.error == export.ERROR_BAD_FORMAT


def test_a_format_with_stray_spaces_still_works() -> None:
    """The value arrives in the address bar, so a stray space is not a mistake."""
    assert export.export_capture(_capture(), "  CSV  ").ok


def test_each_format_carries_its_own_media_type() -> None:
    """The browser saves the file under the type the portal names."""
    assert export.export_capture(_capture(), export.FORMAT_CSV).media_type == export.MEDIA_TYPE_CSV
    assert export.export_capture(_capture(), export.FORMAT_JSON).media_type == export.MEDIA_TYPE_JSON
