"""Unit tests for the comparison download in both formats.

Why:
    The downloaded file leaves the portal. An operator attaches it to a change
    record, so a credential in that file would travel further than any other
    leak in this feature. The tests below prove that the column list is fixed
    and that a field whose name reads as a secret never reaches a row.

    An unknown format must return ``bad_format`` rather than a guess, because
    a guess hands the operator a file of the wrong type and hides the mistake.

    Every test feeds plain records. No test opens a socket, writes a file,
    reads the ``.env`` file, or names a real credential.
"""

from __future__ import annotations

import csv
import io
import json

import pytest

from src.upgrade_portal.compare import clients as client_compare
from src.upgrade_portal.compare import diff as device_compare
from src.upgrade_portal.compare import download

MASTER_MAC = "0011220000aa"
MEMBER_MAC = "0011220000bb"
CLIENT_MAC = "aabbccddeeff"
ACCESS_POINT_ONE = "0011220000cc"
ACCESS_POINT_TWO = "0011220000dd"

OLD_VERSION = "21.4R3.15"
NEW_VERSION = "23.4R2.13"


def _changed_device() -> device_compare.DeviceDelta:
    """Return one device that took a new firmware version.

    Why:
        A changed device is the only device record with two values, so most
        tests need this exact shape.

    Returns:
        One device difference record.
    """
    return device_compare.DeviceDelta(
        mac=MASTER_MAC,
        outcome=device_compare.OUTCOME_CHANGED,
        name="switch-01",
        changes=(device_compare.FieldChange(field="version", before=OLD_VERSION, after=NEW_VERSION),),
    )


def _moved_client() -> client_compare.ClientDelta:
    """Return one client that roamed to another access point.

    Why:
        A move is the only client record with two values, so it proves the
        column meaning of a client row.

    Returns:
        One client difference record.
    """
    return client_compare.ClientDelta(
        mac=CLIENT_MAC,
        outcome=client_compare.OUTCOME_MOVED,
        hostname="laptop-01",
        move=client_compare.ClientMove(before_device=ACCESS_POINT_ONE, after_device=ACCESS_POINT_TWO),
    )


def _read_csv(body: str) -> list[dict[str, str]]:
    """Return the rows of one comma-separated file.

    Why:
        Reading the file back with the standard reader proves the writer
        quoted every value. A test that split on commas would pass on a file
        that a spreadsheet cannot open.

    Args:
        body: The whole file as text.

    Returns:
        One dictionary for each row.
    """
    return list(csv.DictReader(io.StringIO(body)))


# ---------------------------------------------------------------------------
# The column list
# ---------------------------------------------------------------------------


def test_the_column_list_holds_the_seven_names() -> None:
    """The download writes the same seven columns after every run."""
    assert download.EXPORT_COLUMNS == ("kind", "mac", "name", "outcome", "field", "before", "after")
    assert download.column_names() == download.EXPORT_COLUMNS


def test_the_two_formats_write_the_same_columns() -> None:
    """A reader can join the comma-separated file to the JSON file."""
    devices = device_compare.DeviceComparison(deltas=(_changed_device(),))
    clients = client_compare.ClientComparison()

    csv_rows = _read_csv(download.export_comparison(devices, clients, "csv").body)
    json_rows = json.loads(download.export_comparison(devices, clients, "json").body)

    assert csv_rows == json_rows


# ---------------------------------------------------------------------------
# One row for each difference
# ---------------------------------------------------------------------------


def test_a_changed_device_writes_one_row_for_each_field() -> None:
    """Two differing fields write two rows, so a reader can sort by field."""
    delta = device_compare.DeviceDelta(
        mac=MASTER_MAC,
        outcome=device_compare.OUTCOME_CHANGED,
        name="switch-01",
        changes=(
            device_compare.FieldChange(field="status", before="connected", after="disconnected"),
            device_compare.FieldChange(field="version", before=OLD_VERSION, after=NEW_VERSION),
        ),
    )

    rows = download.build_rows(device_compare.DeviceComparison(deltas=(delta,)), client_compare.ClientComparison())

    assert [row.change.field for row in rows] == ["status", "version"]


def test_a_device_row_carries_the_value_before_and_after() -> None:
    """A version row names the old version and the new version."""
    devices = device_compare.DeviceComparison(deltas=(_changed_device(),))

    row = download.build_rows(devices, client_compare.ClientComparison())[0]

    assert row.kind == download.KIND_DEVICE
    assert row.mac == MASTER_MAC
    assert row.change.before == OLD_VERSION
    assert row.change.after == NEW_VERSION


def test_an_unchanged_device_writes_no_row() -> None:
    """The download reports differences, so a quiet device stays out."""
    delta = device_compare.DeviceDelta(mac=MASTER_MAC, outcome=device_compare.OUTCOME_UNCHANGED)

    rows = download.build_rows(device_compare.DeviceComparison(deltas=(delta,)), client_compare.ClientComparison())

    assert rows == ()


def test_a_present_client_writes_no_row() -> None:
    """A client that stayed on the same access point is not a difference."""
    delta = client_compare.ClientDelta(mac=CLIENT_MAC, outcome=client_compare.OUTCOME_PRESENT)

    rows = download.build_rows(device_compare.DeviceComparison(), client_compare.ClientComparison(deltas=(delta,)))

    assert rows == ()


def test_an_added_device_writes_one_row_with_no_field() -> None:
    """A device with no field difference still reaches the file."""
    delta = device_compare.DeviceDelta(mac=MEMBER_MAC, outcome=device_compare.OUTCOME_ADDED, name="new-switch")

    rows = download.build_rows(device_compare.DeviceComparison(deltas=(delta,)), client_compare.ClientComparison())

    assert len(rows) == 1
    assert rows[0].outcome == "added"
    assert rows[0].change.field == ""


def test_a_moved_client_names_the_two_serving_devices() -> None:
    """A move row names the access point before and the access point after."""
    clients = client_compare.ClientComparison(deltas=(_moved_client(),))

    row = download.build_rows(device_compare.DeviceComparison(), clients)[0]

    assert row.kind == download.KIND_CLIENT
    assert row.change.field == download.CLIENT_MOVE_FIELD
    assert row.change.before == ACCESS_POINT_ONE
    assert row.change.after == ACCESS_POINT_TWO


def test_a_missing_client_writes_a_row_with_no_field() -> None:
    """A client that never came back reaches the file."""
    delta = client_compare.ClientDelta(mac=CLIENT_MAC, outcome=client_compare.OUTCOME_MISSING)

    rows = download.build_rows(device_compare.DeviceComparison(), client_compare.ClientComparison(deltas=(delta,)))

    assert rows[0].outcome == "missing"
    assert rows[0].change.field == ""


def test_the_device_rows_come_before_the_client_rows() -> None:
    """The file reads devices first, so the firmware result comes first."""
    devices = device_compare.DeviceComparison(deltas=(_changed_device(),))
    clients = client_compare.ClientComparison(deltas=(_moved_client(),))

    rows = download.build_rows(devices, clients)

    assert [row.kind for row in rows] == [download.KIND_DEVICE, download.KIND_CLIENT]


def test_a_number_reaches_the_file_as_text() -> None:
    """A member count writes a cell rather than the word ``None``."""
    delta = device_compare.DeviceDelta(
        mac=MASTER_MAC,
        outcome=device_compare.OUTCOME_CHANGED,
        changes=(device_compare.FieldChange(field="num_members", before=2, after=None),),
    )

    row = download.build_rows(device_compare.DeviceComparison(deltas=(delta,)), client_compare.ClientComparison())[0]

    assert row.change.before == "2"
    assert row.change.after == ""


# ---------------------------------------------------------------------------
# No credential in the file
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name",
    ["password", "API_TOKEN", "client_secret", "Authorization", "api_key", "passphrase", "cloud_credential"],
)
def test_a_field_that_reads_as_a_secret_is_refused(name: str) -> None:
    """A field name that holds a secret word never reaches a row.

    Args:
        name: The field name to test.
    """
    assert download.is_credential_field(name) is True


@pytest.mark.parametrize("name", ["version", "status", "model", "name", "ip", "vc_role", "num_members"])
def test_every_compared_field_reaches_the_file(name: str) -> None:
    """No compared field of the data model reads as a secret.

    Args:
        name: One compared device field.
    """
    assert download.is_credential_field(name) is False


def test_a_credential_field_never_writes_a_row() -> None:
    """A future capture field named as a secret is dropped from the file."""
    delta = device_compare.DeviceDelta(
        mac=MASTER_MAC,
        outcome=device_compare.OUTCOME_CHANGED,
        changes=(
            device_compare.FieldChange(field="api_token", before="old-secret", after="new-secret"),
            device_compare.FieldChange(field="version", before=OLD_VERSION, after=NEW_VERSION),
        ),
    )
    devices = device_compare.DeviceComparison(deltas=(delta,))

    body = download.export_comparison(devices, client_compare.ClientComparison(), "csv").body

    assert "old-secret" not in body
    assert "new-secret" not in body
    assert NEW_VERSION in body


def test_a_device_with_only_credential_changes_keeps_one_row() -> None:
    """A device whose every change reads as a secret still reports that it changed."""
    delta = device_compare.DeviceDelta(
        mac=MASTER_MAC,
        outcome=device_compare.OUTCOME_CHANGED,
        changes=(device_compare.FieldChange(field="api_token", before="old-secret", after="new-secret"),),
    )

    rows = download.build_rows(device_compare.DeviceComparison(deltas=(delta,)), client_compare.ClientComparison())

    assert len(rows) == 1
    assert rows[0].mac == MASTER_MAC
    assert rows[0].outcome == device_compare.OUTCOME_CHANGED
    assert rows[0].change.field == ""
    assert "secret" not in download.render_csv(rows)


# ---------------------------------------------------------------------------
# The comma-separated file
# ---------------------------------------------------------------------------


def test_the_file_starts_with_a_header_line() -> None:
    """The header line names the columns, so a spreadsheet labels them."""
    body = download.render_csv(())

    assert body.splitlines()[0] == ",".join(download.EXPORT_COLUMNS)


def test_a_name_with_a_comma_reads_back_whole() -> None:
    """A device name with a comma never splits into two cells."""
    delta = device_compare.DeviceDelta(
        mac=MASTER_MAC,
        outcome=device_compare.OUTCOME_ADDED,
        name="switch-01, floor 2",
    )

    rows = download.build_rows(device_compare.DeviceComparison(deltas=(delta,)), client_compare.ClientComparison())

    assert _read_csv(download.render_csv(rows))[0]["name"] == "switch-01, floor 2"


@pytest.mark.parametrize("leader", ["=", "+", "@", "-"])
def test_a_cell_that_would_run_gets_a_guard(leader: str) -> None:
    """A spreadsheet never runs a device name that came from the cloud.

    Args:
        leader: The character that would start a formula.
    """
    delta = device_compare.DeviceDelta(
        mac=MASTER_MAC,
        outcome=device_compare.OUTCOME_ADDED,
        name=leader + "cmd|' /c calc'!A1",
    )
    rows = download.build_rows(device_compare.DeviceComparison(deltas=(delta,)), client_compare.ClientComparison())

    cell = _read_csv(download.render_csv(rows))[0]["name"]

    assert cell.startswith("'")
    assert not cell.startswith(leader)


def test_a_negative_number_stays_a_number() -> None:
    """A negative count keeps its minus sign, so a spreadsheet sums the column."""
    delta = device_compare.DeviceDelta(
        mac=MASTER_MAC,
        outcome=device_compare.OUTCOME_CHANGED,
        changes=(device_compare.FieldChange(field="num_members", before=-1, after=2),),
    )
    rows = download.build_rows(device_compare.DeviceComparison(deltas=(delta,)), client_compare.ClientComparison())

    assert _read_csv(download.render_csv(rows))[0]["before"] == "-1"


def test_a_formula_that_starts_with_a_minus_sign_gets_a_guard() -> None:
    """A minus sign starts a formula as well as a number, so the writer reads the whole cell."""
    delta = device_compare.DeviceDelta(
        mac=MASTER_MAC,
        outcome=device_compare.OUTCOME_ADDED,
        name="-1+cmd|' /c calc'!A0",
    )
    rows = download.build_rows(device_compare.DeviceComparison(deltas=(delta,)), client_compare.ClientComparison())

    assert _read_csv(download.render_csv(rows))[0]["name"].startswith("'")


@pytest.mark.parametrize("leader", ["\t", "\r"])
def test_a_control_character_leader_gets_a_guard(leader: str) -> None:
    """A tab and a carriage return also start a formula in a spreadsheet.

    Args:
        leader: The control character that would start a formula.
    """
    delta = device_compare.DeviceDelta(
        mac=MASTER_MAC,
        outcome=device_compare.OUTCOME_ADDED,
        name=leader + "cmd|' /c calc'!A1",
    )
    rows = download.build_rows(device_compare.DeviceComparison(deltas=(delta,)), client_compare.ClientComparison())

    assert "'" + leader in download.render_csv(rows)


def test_an_empty_comparison_writes_the_header_alone() -> None:
    """A run with no difference writes a file the operator can still open."""
    result = download.export_comparison(device_compare.DeviceComparison(), client_compare.ClientComparison(), "csv")

    assert _read_csv(result.body) == []
    assert result.ok is True


# ---------------------------------------------------------------------------
# The JSON file
# ---------------------------------------------------------------------------


def test_the_json_file_holds_one_object_for_each_row() -> None:
    """The JSON file is a list of flat objects, one for each difference."""
    devices = device_compare.DeviceComparison(deltas=(_changed_device(),))
    clients = client_compare.ClientComparison(deltas=(_moved_client(),))

    rows = json.loads(download.render_json(download.build_rows(devices, clients)))

    assert len(rows) == 2
    assert set(rows[0]) == set(download.EXPORT_COLUMNS)


def test_the_json_file_reads_back_as_a_list() -> None:
    """An empty comparison writes an empty list rather than nothing."""
    assert json.loads(download.render_json(())) == []


# ---------------------------------------------------------------------------
# The format refusal
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("chosen", ["csv", "json", "CSV", " json "])
def test_a_known_format_returns_a_file(chosen: str) -> None:
    """A known format returns the file, whatever its spelling.

    Args:
        chosen: The requested format.
    """
    result = download.export_comparison(device_compare.DeviceComparison(), client_compare.ClientComparison(), chosen)

    assert result.ok is True
    assert result.error == ""
    assert result.body


@pytest.mark.parametrize("chosen", ["xlsx", "", "pdf", None, 12345, "cs v", ["csv"]])
def test_an_unknown_format_returns_the_refusal(chosen: object) -> None:
    """An unknown format refuses with ``bad_format`` rather than a guess.

    Args:
        chosen: The requested format.
    """
    result = download.export_comparison(device_compare.DeviceComparison(), client_compare.ClientComparison(), chosen)

    assert result.ok is False
    assert result.error == download.ERROR_BAD_FORMAT
    assert result.body == ""


def test_the_refusal_never_names_the_bad_value_in_the_log(caplog: pytest.LogCaptureFixture) -> None:
    """A format value from the address bar never reaches a log record.

    Args:
        caplog: The captured log records.
    """
    attack = "csv\nWARNING The upgrade succeeded"

    with caplog.at_level("WARNING"):
        download.export_comparison(device_compare.DeviceComparison(), client_compare.ClientComparison(), attack)

    assert "The upgrade succeeded" not in caplog.text


def test_each_format_names_its_media_type_and_file() -> None:
    """The browser learns the media type and the file name of the download."""
    devices = device_compare.DeviceComparison()
    clients = client_compare.ClientComparison()

    as_csv = download.export_comparison(devices, clients, "csv")
    as_json = download.export_comparison(devices, clients, "json")

    assert (as_csv.media_type, as_csv.filename) == ("text/csv", "upgrade-comparison.csv")
    assert (as_json.media_type, as_json.filename) == ("application/json", "upgrade-comparison.json")
