"""Unit tests for the full comparison download.

Why:
    User Story 2, acceptance scenario 5 of the feature specification states
    that the download holds every row of both captures and the statistics.
    FR-070 states that the portal offers a file download of the comparison.
    The differences file alone proves nothing about a device that did not
    change, so the portal offers a second scope that writes every row.

    A digest match skips a whole section. The full download must still name
    every row of that section, because a file that names no device cannot
    prove that the upgrade did no harm.

    The full download passes through the same two guards as the differences
    download. A cell that a spreadsheet would run carries a guard character,
    and a field whose name reads as a secret never reaches the file.

    Every test feeds plain records. No test opens a socket, writes a file,
    reads the ``.env`` file, or names a real credential.
"""

from __future__ import annotations

import csv
import io
import json
from typing import Any

import pytest

from src.upgrade_portal.app.routes import review
from src.upgrade_portal.compare import clients as client_compare
from src.upgrade_portal.compare import diff as device_compare
from src.upgrade_portal.compare import download

# ---------------------------------------------------------------------------
# The test values
# ---------------------------------------------------------------------------

MASTER_MAC = "0011220000aa"
MEMBER_MAC = "0011220000bb"
CLIENT_MAC = "aabbccddeeff"
SECOND_CLIENT_MAC = "aabbccddee11"
ACCESS_POINT_ONE = "0011220000cc"
ACCESS_POINT_TWO = "0011220000dd"

OLD_VERSION = "21.4R3.15"
NEW_VERSION = "23.4R2.13"

SITE_ID = "00000000-0000-0000-0000-0000000000bb"
SITE_NAME = "Probe site"
ORG_NAME = "Probe organization"

BEFORE_CAPTURE_ID = "capture-before-0001"
AFTER_CAPTURE_ID = "capture-after-0001"

STARTED_BEFORE = "2026-08-19T10:00:00+00:00"
FINISHED_BEFORE = "2026-08-19T10:05:00+00:00"
STARTED_AFTER = "2026-08-19T10:25:00+00:00"
FINISHED_AFTER = "2026-08-19T10:30:00+00:00"

# WHY: A digest is a fixed text in these tests. The comparison only tests two
# digests for equality, so the exact characters do not matter.
DEVICE_DIGEST = "d" * 64
WIRELESS_DIGEST = "w" * 64

# The two column blocks of the full comma-separated file.
SUMMARY_COLUMNS = ["detail", "value"]
EXPORT_COLUMNS = ["kind", "mac", "name", "outcome", "field", "before", "after"]


# ---------------------------------------------------------------------------
# The capture builders
# ---------------------------------------------------------------------------


def _quiet_capture(capture_id: str, role: str, started: str, finished: str) -> dict[str, Any]:
    """Return one capture whose digests claim that nothing changed.

    Why:
        Two captures of a quiet site carry the same digests. The comparison
        then skips both sections and reports no row at all, which is the case
        that the full download must still cover.

    Args:
        capture_id: The business key of the capture.
        role: ``pre`` or ``post``.
        started: The moment the capture started.
        finished: The moment the capture finished.

    Returns:
        One capture document.
    """
    return {
        "capture_id": capture_id,
        "site_id": SITE_ID,
        "site_name": SITE_NAME,
        "org_name": ORG_NAME,
        "role": role,
        "started_at": started,
        "finished_at": finished,
        "digests": {"devices": DEVICE_DIGEST, "clients_wireless": WIRELESS_DIGEST},
        "device_index": {
            MASTER_MAC: {"name": "switch-01", "status": "connected", "version": OLD_VERSION},
            MEMBER_MAC: {"name": "switch-02", "status": "connected", "version": OLD_VERSION},
        },
        "clients": {
            "wireless": [
                {"mac": CLIENT_MAC, "hostname": "laptop-01", "device_mac": ACCESS_POINT_ONE},
                {"mac": SECOND_CLIENT_MAC, "hostname": "phone-01", "device_mac": ACCESS_POINT_ONE},
            ]
        },
    }


def _quiet_pair() -> tuple[dict[str, Any], dict[str, Any]]:
    """Return two captures of a site where every digest matches.

    Returns:
        The pre-check capture and the post-check capture.
    """
    before = _quiet_capture(BEFORE_CAPTURE_ID, "pre", STARTED_BEFORE, FINISHED_BEFORE)
    after = _quiet_capture(AFTER_CAPTURE_ID, "post", STARTED_AFTER, FINISHED_AFTER)
    return before, after


def _quiet_context() -> download.ExportContext:
    """Return the export context of two captures with matching digests.

    Returns:
        The context that the full download reads.
    """
    before, after = _quiet_pair()
    return download.ExportContext(before=before, after=after)


# ---------------------------------------------------------------------------
# The comparison builders
# ---------------------------------------------------------------------------


def _mixed_devices() -> device_compare.DeviceComparison:
    """Return one device that changed and one device that did not.

    Returns:
        The device half of a comparison.
    """
    changed = device_compare.DeviceDelta(
        mac=MASTER_MAC,
        outcome=device_compare.OUTCOME_CHANGED,
        name="switch-01",
        changes=(device_compare.FieldChange(field="version", before=OLD_VERSION, after=NEW_VERSION),),
    )
    unchanged = device_compare.DeviceDelta(mac=MEMBER_MAC, outcome=device_compare.OUTCOME_UNCHANGED, name="switch-02")
    return device_compare.DeviceComparison(deltas=(changed, unchanged))


def _mixed_clients() -> client_compare.ClientComparison:
    """Return one client that roamed and one client that stayed.

    Returns:
        The client half of a comparison.
    """
    moved = client_compare.ClientDelta(
        mac=CLIENT_MAC,
        outcome=client_compare.OUTCOME_MOVED,
        hostname="laptop-01",
        move=client_compare.ClientMove(before_device=ACCESS_POINT_ONE, after_device=ACCESS_POINT_TWO),
    )
    present = client_compare.ClientDelta(
        mac=SECOND_CLIENT_MAC,
        outcome=client_compare.OUTCOME_PRESENT,
        hostname="phone-01",
        move=client_compare.ClientMove(before_device=ACCESS_POINT_ONE, after_device=ACCESS_POINT_ONE),
    )
    return client_compare.ClientComparison(deltas=(moved, present))


def _statistics() -> dict[str, Any]:
    """Return one flat statistics map, as the route builds it.

    Returns:
        The eleven statistic names and their values.
    """
    return {
        "devices_unchanged": 1,
        "devices_changed": 1,
        "devices_added": 0,
        "devices_removed": 0,
        "devices_version_changed": 1,
        "clients_present": 1,
        "clients_moved": 1,
        "clients_added": 0,
        "clients_missing": 0,
        "client_return_rate": 1.0,
        "elapsed_seconds": 1800.0,
    }


def _mixed_context() -> download.ExportContext:
    """Return the export context of a comparison that skipped no section.

    Returns:
        The context that the full download reads.
    """
    before, after = _quiet_pair()
    plain_before = {name: value for name, value in before.items() if name != "digests"}
    plain_after = {name: value for name, value in after.items() if name != "digests"}
    return download.ExportContext(before=plain_before, after=plain_after, statistics=_statistics())


# ---------------------------------------------------------------------------
# The file readers
# ---------------------------------------------------------------------------


def _all_lines(body: str) -> list[list[str]]:
    """Return every line of one comma-separated file.

    Args:
        body: The whole file as text.

    Returns:
        One list of cells for each line.
    """
    return list(csv.reader(io.StringIO(body)))


def _detail_pairs(body: str) -> dict[str, str]:
    """Return the header block of one full comma-separated file.

    Why:
        The header block runs from the ``detail`` line to the first blank
        line. Reading it back with the standard reader proves that the writer
        quoted every value.

    Args:
        body: The whole file as text.

    Returns:
        One entry for each header pair.
    """
    pairs: dict[str, str] = {}
    for line in _all_lines(body)[1:]:
        if not line:
            break
        pairs[line[0]] = line[1] if len(line) > 1 else ""
    return pairs


def _row_dicts(body: str) -> list[dict[str, str]]:
    """Return the export rows of one full comma-separated file.

    Args:
        body: The whole file as text.

    Returns:
        One dictionary for each export row.
    """
    lines = _all_lines(body)
    start = lines.index(EXPORT_COLUMNS)
    return [dict(zip(EXPORT_COLUMNS, line, strict=False)) for line in lines[start + 1 :] if line]


def _full_csv(devices: Any, clients: Any, context: download.ExportContext) -> str:
    """Return the full comma-separated download of one comparison.

    Args:
        devices: The device half of the comparison.
        clients: The client half of the comparison.
        context: The two captures and the statistics.

    Returns:
        The whole file as text.
    """
    return download.export_comparison(devices, clients, "csv", download.SCOPE_FULL, context).body


# ---------------------------------------------------------------------------
# Every row of both captures
# ---------------------------------------------------------------------------


def test_the_full_scope_writes_a_row_for_an_unchanged_device() -> None:
    """A device that did not change reaches the full file."""
    delta = device_compare.DeviceDelta(mac=MASTER_MAC, outcome=device_compare.OUTCOME_UNCHANGED, name="switch-01")

    rows = download.build_full_rows(device_compare.DeviceComparison(deltas=(delta,)), client_compare.ClientComparison())

    assert len(rows) == 1
    assert rows[0].mac == MASTER_MAC
    assert rows[0].outcome == device_compare.OUTCOME_UNCHANGED


def test_the_full_scope_writes_a_row_for_a_present_client() -> None:
    """A client that stayed on the same access point reaches the full file."""
    delta = client_compare.ClientDelta(mac=CLIENT_MAC, outcome=client_compare.OUTCOME_PRESENT, hostname="laptop-01")

    rows = download.build_full_rows(device_compare.DeviceComparison(), client_compare.ClientComparison(deltas=(delta,)))

    assert len(rows) == 1
    assert rows[0].mac == CLIENT_MAC
    assert rows[0].outcome == client_compare.OUTCOME_PRESENT


def test_the_full_scope_writes_every_device_and_every_client() -> None:
    """The full file names both halves of the comparison, quiet rows included."""
    body = _full_csv(_mixed_devices(), _mixed_clients(), _mixed_context())
    addresses = {row["mac"] for row in _row_dicts(body)}

    assert addresses == {MASTER_MAC, MEMBER_MAC, CLIENT_MAC, SECOND_CLIENT_MAC}


def test_the_full_scope_keeps_the_device_rows_before_the_client_rows() -> None:
    """The file reads devices first, so the firmware result comes first."""
    rows = download.build_full_rows(_mixed_devices(), _mixed_clients())

    kinds = [row.kind for row in rows]

    assert kinds == [download.KIND_DEVICE, download.KIND_DEVICE, download.KIND_CLIENT, download.KIND_CLIENT]


# ---------------------------------------------------------------------------
# A skipped section still writes every row
# ---------------------------------------------------------------------------


def test_a_skipped_device_section_still_writes_every_device() -> None:
    """A digest match proves every device is unchanged, so every device reaches the file."""
    before, after = _quiet_pair()
    devices = device_compare.compare_devices(before, after)

    rows = download.build_full_rows(devices, client_compare.compare_clients(before, after), _quiet_context())
    device_rows = [row for row in rows if row.kind == download.KIND_DEVICE]

    assert devices.skipped_sections == (device_compare.SECTION_DEVICES,)
    assert {row.mac for row in device_rows} == {MASTER_MAC, MEMBER_MAC}
    assert {row.outcome for row in device_rows} == {device_compare.OUTCOME_UNCHANGED}


def test_a_skipped_client_section_still_writes_every_client() -> None:
    """A digest match proves every client returned, so every client reaches the file."""
    before, after = _quiet_pair()
    clients = client_compare.compare_clients(before, after)

    rows = download.build_full_rows(device_compare.compare_devices(before, after), clients, _quiet_context())
    client_rows = [row for row in rows if row.kind == download.KIND_CLIENT]

    assert clients.skipped_sections == (client_compare.SECTION_CLIENTS_WIRELESS,)
    assert {row.mac for row in client_rows} == {CLIENT_MAC, SECOND_CLIENT_MAC}
    assert {row.outcome for row in client_rows} == {client_compare.OUTCOME_PRESENT}


def test_a_skipped_comparison_reports_the_statistics_of_every_row() -> None:
    """The rebuilt file counts the rows that it holds, so the file agrees with itself."""
    before, after = _quiet_pair()
    devices = device_compare.compare_devices(before, after)
    clients = client_compare.compare_clients(before, after)

    pairs = _detail_pairs(_full_csv(devices, clients, _quiet_context()))

    assert pairs["devices_unchanged"] == "2"
    assert pairs["clients_present"] == "2"


def test_the_header_block_names_each_skipped_section() -> None:
    """The header block says which section the digests skipped."""
    before, after = _quiet_pair()
    devices = device_compare.compare_devices(before, after)
    clients = client_compare.compare_clients(before, after)

    pairs = _detail_pairs(_full_csv(devices, clients, _quiet_context()))

    assert device_compare.SECTION_DEVICES in pairs["skipped_sections"]
    assert client_compare.SECTION_CLIENTS_WIRELESS in pairs["skipped_sections"]


# ---------------------------------------------------------------------------
# The header block
# ---------------------------------------------------------------------------


def test_the_full_file_starts_with_the_header_block_names() -> None:
    """The first line names the two header block columns."""
    body = _full_csv(_mixed_devices(), _mixed_clients(), _mixed_context())

    assert _all_lines(body)[0] == SUMMARY_COLUMNS


def test_the_header_block_names_the_site_and_the_organization() -> None:
    """The record keeper reads the site and the organization from the file alone."""
    pairs = _detail_pairs(_full_csv(_mixed_devices(), _mixed_clients(), _mixed_context()))

    assert pairs["site"] == SITE_NAME
    assert pairs["site_id"] == SITE_ID
    assert pairs["organization"] == ORG_NAME


def test_the_header_block_names_the_two_captures() -> None:
    """The header block names the business key and the role of each capture."""
    pairs = _detail_pairs(_full_csv(_mixed_devices(), _mixed_clients(), _mixed_context()))

    assert pairs["before_capture_id"] == BEFORE_CAPTURE_ID
    assert pairs["after_capture_id"] == AFTER_CAPTURE_ID
    assert pairs["before_role"] == "pre"
    assert pairs["after_role"] == "post"


def test_the_header_block_names_the_two_moments() -> None:
    """The header block names when each capture started and finished."""
    pairs = _detail_pairs(_full_csv(_mixed_devices(), _mixed_clients(), _mixed_context()))

    assert pairs["before_started_at"] == STARTED_BEFORE
    assert pairs["before_finished_at"] == FINISHED_BEFORE
    assert pairs["after_started_at"] == STARTED_AFTER
    assert pairs["after_finished_at"] == FINISHED_AFTER


@pytest.mark.parametrize(
    "name",
    [
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
    ],
)
def test_the_header_block_names_every_statistic(name: str) -> None:
    """Every statistic of the comparison reaches the full file.

    Args:
        name: One flat statistic name.
    """
    pairs = _detail_pairs(_full_csv(_mixed_devices(), _mixed_clients(), _mixed_context()))

    assert name in pairs


def test_the_header_block_reports_the_statistic_values() -> None:
    """The statistics in the file hold the numbers that the page shows."""
    pairs = _detail_pairs(_full_csv(_mixed_devices(), _mixed_clients(), _mixed_context()))

    assert pairs["devices_version_changed"] == "1"
    assert pairs["clients_moved"] == "1"


def test_the_column_line_follows_a_blank_line() -> None:
    """A blank line ends the header block, so a spreadsheet reads two tables."""
    lines = _all_lines(_full_csv(_mixed_devices(), _mixed_clients(), _mixed_context()))
    column_line = lines.index(EXPORT_COLUMNS)

    assert lines[column_line - 1] == []


# ---------------------------------------------------------------------------
# The JSON file
# ---------------------------------------------------------------------------


def test_the_full_json_holds_the_summary_the_statistics_and_the_rows() -> None:
    """The JSON file carries the header block beside the rows."""
    body = download.export_comparison(
        _mixed_devices(), _mixed_clients(), "json", download.SCOPE_FULL, _mixed_context()
    ).body

    document = json.loads(body)

    assert set(document) == {"summary", "statistics", "rows"}
    assert document["summary"]["site"] == SITE_NAME
    assert document["statistics"]["devices_version_changed"] == 1
    assert len(document["rows"]) == 4


def test_the_two_full_formats_report_the_same_rows() -> None:
    """A reader can join the full comma-separated file to the full JSON file."""
    devices, clients, context = _mixed_devices(), _mixed_clients(), _mixed_context()

    csv_rows = _row_dicts(_full_csv(devices, clients, context))
    json_rows = json.loads(download.export_comparison(devices, clients, "json", download.SCOPE_FULL, context).body)[
        "rows"
    ]

    assert csv_rows == json_rows


def test_the_full_download_names_its_own_file() -> None:
    """The full file carries its own name, so it never overwrites the differences file."""
    devices, clients, context = _mixed_devices(), _mixed_clients(), _mixed_context()

    as_csv = download.export_comparison(devices, clients, "csv", download.SCOPE_FULL, context)
    as_json = download.export_comparison(devices, clients, "json", download.SCOPE_FULL, context)

    assert as_csv.filename == "upgrade-comparison-full.csv"
    assert as_json.filename == "upgrade-comparison-full.json"
    assert as_csv.media_type == download.MEDIA_TYPE_CSV
    assert as_json.media_type == download.MEDIA_TYPE_JSON


# ---------------------------------------------------------------------------
# The two guards still hold
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("leader", ["=", "+", "@", "-", "\t", "\r"])
def test_a_full_file_cell_that_would_run_gets_a_guard(leader: str) -> None:
    """A spreadsheet never runs a device name that came from the cloud.

    Args:
        leader: The character that would start a formula.
    """
    delta = device_compare.DeviceDelta(
        mac=MASTER_MAC,
        outcome=device_compare.OUTCOME_UNCHANGED,
        name=leader + "cmd|' /c calc'!A1",
    )
    devices = device_compare.DeviceComparison(deltas=(delta,))

    cell = _row_dicts(_full_csv(devices, client_compare.ClientComparison(), _mixed_context()))[0]["name"]

    assert cell.startswith("'")
    assert not cell.startswith(leader)


def test_a_header_block_value_that_would_run_gets_a_guard() -> None:
    """A site name that came from the cloud never runs in a spreadsheet."""
    before, after = _quiet_pair()
    before["site_name"] = "=SUM(A1:A9)"
    after["site_name"] = "=SUM(A1:A9)"
    context = download.ExportContext(before=before, after=after, statistics=_statistics())

    pairs = _detail_pairs(_full_csv(_mixed_devices(), _mixed_clients(), context))

    assert pairs["site"] == "'=SUM(A1:A9)"


def test_the_full_file_never_writes_a_credential_value() -> None:
    """A future capture field named as a secret never reaches the full file."""
    delta = device_compare.DeviceDelta(
        mac=MASTER_MAC,
        outcome=device_compare.OUTCOME_CHANGED,
        changes=(
            device_compare.FieldChange(field="api_token", before="old-secret", after="new-secret"),
            device_compare.FieldChange(field="version", before=OLD_VERSION, after=NEW_VERSION),
        ),
    )
    devices = device_compare.DeviceComparison(deltas=(delta,))

    body = _full_csv(devices, client_compare.ClientComparison(), _mixed_context())

    assert "old-secret" not in body
    assert "new-secret" not in body
    assert NEW_VERSION in body


def test_a_statistic_that_reads_as_a_secret_never_reaches_the_file() -> None:
    """A caller cannot smuggle a secret into the header block through the statistics."""
    statistics = {**_statistics(), "cloud_api_token": "fake-token-value"}
    before, after = _quiet_pair()
    context = download.ExportContext(before=before, after=after, statistics=statistics)

    body = _full_csv(_mixed_devices(), _mixed_clients(), context)

    assert "fake-token-value" not in body
    assert "cloud_api_token" not in body


# ---------------------------------------------------------------------------
# The default scope never changes
# ---------------------------------------------------------------------------


def test_the_default_scope_still_writes_the_differences_alone() -> None:
    """A caller that names no scope gets the same file as before."""
    devices, clients = _mixed_devices(), _mixed_clients()

    body = download.export_comparison(devices, clients, "csv").body

    assert _all_lines(body)[0] == EXPORT_COLUMNS
    assert {row["mac"] for row in _row_dicts(body)} == {MASTER_MAC, CLIENT_MAC}


@pytest.mark.parametrize("wanted", ["", " ", "differences", "DIFFERENCES", " Differences "])
def test_the_differences_scope_holds_the_differences_alone(wanted: str) -> None:
    """The differences scope answers the same file, whatever its spelling.

    Args:
        wanted: The requested scope.
    """
    result = download.export_comparison(_mixed_devices(), _mixed_clients(), "csv", wanted, _mixed_context())

    assert result.ok is True
    assert result.filename == download.FILENAME_CSV
    assert {row["mac"] for row in _row_dicts(result.body)} == {MASTER_MAC, CLIENT_MAC}


@pytest.mark.parametrize("wanted", ["everything", "all", "partial", None, 12345, ["full"]])
def test_an_unknown_scope_returns_the_refusal(wanted: object) -> None:
    """An unknown scope refuses rather than sending the wrong file.

    Args:
        wanted: The requested scope.
    """
    result = download.export_comparison(_mixed_devices(), _mixed_clients(), "csv", wanted, _mixed_context())

    assert result.ok is False
    assert result.error == download.ERROR_BAD_SCOPE
    assert result.body == ""


def test_an_unknown_format_still_refuses_before_the_scope() -> None:
    """A bad format reports the format fault, so the operator reads one cause."""
    result = download.export_comparison(_mixed_devices(), _mixed_clients(), "xlsx", download.SCOPE_FULL)

    assert result.error == download.ERROR_BAD_FORMAT


def test_the_scope_refusal_never_names_the_bad_value_in_the_log(caplog: pytest.LogCaptureFixture) -> None:
    """A scope value from the address bar never reaches a log record.

    Args:
        caplog: The captured log records.
    """
    attack = "full\nWARNING The upgrade succeeded"

    with caplog.at_level("WARNING"):
        download.export_comparison(_mixed_devices(), _mixed_clients(), "csv", attack)

    assert "The upgrade succeeded" not in caplog.text


# ---------------------------------------------------------------------------
# The page offers both downloads
# ---------------------------------------------------------------------------


def test_the_page_offers_four_download_addresses() -> None:
    """The page offers the differences file and the full file in both formats."""
    links = review.build_download_links({"before": BEFORE_CAPTURE_ID, "after": AFTER_CAPTURE_ID})

    assert set(links) == {"csv_href", "json_href", "full_csv_href", "full_json_href"}


@pytest.mark.parametrize("name", ["full_csv_href", "full_json_href"])
def test_each_full_address_names_the_full_scope(name: str) -> None:
    """A full download link asks the endpoint for every row.

    Args:
        name: The name of the link to read.
    """
    links = review.build_download_links({"before": BEFORE_CAPTURE_ID, "after": AFTER_CAPTURE_ID})

    assert "scope=full" in links[name]
    assert links[name].startswith(review.COMPARISONS_EXPORT_API_PATH)


@pytest.mark.parametrize(("name", "wanted"), [("csv_href", "format=csv"), ("json_href", "format=json")])
def test_each_differences_address_keeps_its_format(name: str, wanted: str) -> None:
    """The two older links still name the export path and their own format.

    Args:
        name: The name of the link to read.
        wanted: The query text that the link must carry.
    """
    links = review.build_download_links({"before": BEFORE_CAPTURE_ID, "after": AFTER_CAPTURE_ID})

    assert links[name].startswith(review.COMPARISONS_EXPORT_API_PATH)
    assert wanted in links[name]


def test_the_export_context_carries_the_captures_and_the_statistics() -> None:
    """The route hands the download the two captures and the counted statistics."""
    before, after = _quiet_pair()
    parts = review.build_parts(before, after)

    context = review.build_export_context(parts)

    assert context.before is before
    assert context.after is after
    assert context.statistics == parts.statistics.to_dict()
