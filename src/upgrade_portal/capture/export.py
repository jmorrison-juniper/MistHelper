"""The capture download in comma-separated value form and in JSON form.

Why:
    FR-027 requires a file download of one completed capture, and User Story 1
    Acceptance Scenario 3 requires that the file holds every captured row. An
    operator attaches the file to a change record, so the file must open in a
    spreadsheet and must also feed another program.

    One row holds one device or one client. A flat row lets a reader sort and
    filter the file without unpacking a nested structure, and it lets the two
    formats report the same rows.

    Each chassis member writes its own row. A stack that loses a member keeps
    the same device count, so a row for each member is the only signal of the
    loss.

Why this module copies two controls of `compare/download.py`:
    `compare/clients.py` already imports `capture/clients.py`. An import of
    `compare/download.py` from this package would make the two packages read
    each other, and a later import inside `capture/clients.py` would then close
    the loop. The formula guard and the credential filter are therefore copied
    from `src/upgrade_portal/compare/download.py`, which stays the source of
    both rules. `tests/unit/upgrade_portal/test_capture_export.py` compares the
    two copies, so neither copy can change alone.

    The file never holds a credential. The row columns are fixed and the
    builder drops any field whose name reads as a secret, so a future capture
    field cannot leak into a downloaded file.
"""

from __future__ import annotations  # Every annotation stays text, so a name may appear before its class.

import csv  # The spreadsheet form of the file.
import io  # The writer needs a text buffer, because the route answers with text.
import json  # The machine form of the file.
import logging  # The portal logs with the standard library only.
import re  # Cleans the capture identifier before it reaches a response header.
from collections.abc import Iterable, Mapping, Sequence  # The read-only types of every argument below.
from dataclasses import dataclass, field  # The two small records of this module.
from typing import Any  # A stored capture document is free-form.

logger = logging.getLogger(__name__)  # One logger for each module keeps the source visible in the log.

FORMAT_CSV = "csv"  # The spreadsheet form.
FORMAT_JSON = "json"  # The machine form.
SUPPORTED_FORMATS = (FORMAT_CSV, FORMAT_JSON)  # Any other value is a refusal.

ERROR_BAD_FORMAT = "bad_format"  # `contracts/http-api.md` fixes this code for an unknown format.

MEDIA_TYPE_CSV = "text/csv"  # The browser saves the spreadsheet form under this type.
MEDIA_TYPE_JSON = "application/json"  # The browser saves the machine form under this type.

KIND_DEVICE = "device"  # One row of the device table.
KIND_CLIENT_WIRED = "client_wired"  # One row of the wired client table.
KIND_CLIENT_WIRELESS = "client_wireless"  # One row of the wireless client table.
KIND_CLIENT_GUEST = "client_guest"  # One row of the guest client table.

# The client group of the stored document, and the row kind that each one writes.
CLIENT_GROUPS: tuple[tuple[str, str], ...] = (
    ("wired", KIND_CLIENT_WIRED),
    ("wireless", KIND_CLIENT_WIRELESS),
    ("guest", KIND_CLIENT_GUEST),
)

# WHY: One column list covers a device row and a client row. A second list
# would let the two row shapes drift, and a reader could then not sort the
# whole file on one column. A column that the row does not use stays empty.
# The five naming columns lead, so every row names its own capture. A reader
# can then join two files without a separate note of where each row came from.
EXPORT_COLUMNS = (
    "org_name",
    "site_name",
    "capture_id",
    "role",
    "captured_at",
    "kind",
    "mac",
    "name",
    "hostname",
    "ip",
    "model",
    "serial",
    "version",
    "status",
    "uptime",
    "vc_role",
    "num_members",
    "parent_device",
    "parent_mac",
    "port_id",
    "vlan",
    "ssid",
    "band",
)

# The columns that a device row reads straight out of the device index entry.
DEVICE_FIELDS = ("name", "ip", "model", "serial", "version", "status", "uptime", "vc_role", "num_members")

# The columns that a client row reads straight out of the client record.
CLIENT_FIELDS = ("hostname", "ip", "port_id", "vlan", "ssid", "band")

# The two client columns whose column name and source field name differ. The
# column names read as the parent of the client, which is what the operator
# looks for. The source names come from `data-model.md` section 3.4.
CLIENT_PARENT_FIELDS = (("parent_device", "device_name"), ("parent_mac", "device_mac"))

# The five values that name the capture. FR-027 requires each one, so a reader
# of the file can tell which site it read and when. Each one is also a column,
# so a spreadsheet holds one flat table and needs no preamble.
HEADING_COLUMNS = ("org_name", "site_name", "capture_id", "role", "captured_at")

# WHY: The export must never write a credential. This list is a copy of
# `compare.download.CREDENTIAL_WORDS`. That module stays the source of the
# rule, and a unit test compares the two lists.
CREDENTIAL_WORDS = ("password", "secret", "token", "credential", "authorization", "api_key", "apikey", "passphrase")

# WHY: A spreadsheet runs a cell that starts with one of these characters. A
# device name comes from the cloud, so the writer disarms the cell. The minus
# sign belongs in the list, because `-1+cmd|' /c calc'!A0` is a formula that
# starts with a minus sign. A tab and a carriage return lead the same way.
# This list is a copy of `compare.download._FORMULA_LEADERS`.
FORMULA_LEADERS = ("=", "+", "@", "-", "\t", "\r")
FORMULA_GUARD = "'"  # The character that stops a spreadsheet from running a cell.

HEADER_MARKER = ",".join(EXPORT_COLUMNS)  # The header line. It opens the file.

FILENAME_STEM = "capture-"  # The download name opens with this word.
FALLBACK_STEM = "capture"  # The download name for a capture that names no identifier.
_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]")  # Every other character leaves the download name.

_JSON_INDENT = 2  # A reader opens the machine form as well, so the file stays readable.
_LINE_BREAKS = ("\r\n", "\n", "\r")  # A value that held one of these would split one row in two.


# ---------------------------------------------------------------------------
# The two safety controls. Both are copies of `compare/download.py`.
# ---------------------------------------------------------------------------


def is_credential_field(name: str) -> bool:
    """Return whether one field name reads as a secret.

    Why:
        The capture writes a downloaded file that an operator attaches to a
        change record. A secret in that file would travel further than the
        portal. The test runs on the name, so a new capture field is refused
        before anybody notices it.

    Args:
        name: The field name to test.

    Returns:
        True when the name holds a word of `CREDENTIAL_WORDS`.
    """
    lowered = name.lower()  # The cloud may send a name in any letter case.
    return any(word in lowered for word in CREDENTIAL_WORDS)  # One match is enough to drop the field.


def _reads_as_a_number(value: str) -> bool:
    """Return whether the whole cell reads as one number.

    Why:
        A minus sign starts a negative number and it also starts a formula. A
        cell that reads as a number holds no formula, so the writer leaves it
        alone and a spreadsheet still sums the column.

    Args:
        value: The raw cell text.

    Returns:
        True when the text is a plain number.
    """
    try:  # A word, an empty value, and a formula all land in the refusal below.
        float(value)
    except ValueError:  # The cell is not a number, so the guard applies.
        return False
    return True  # The cell is a number, so a spreadsheet cannot run it.


def disarm_cell(value: str) -> str:
    """Return one cell that a spreadsheet cannot run.

    Why:
        A cell that starts with an equals sign runs as a formula when the
        operator opens the file. A device name comes from the cloud, so the
        writer puts a quotation mark in front of that cell.

    Args:
        value: The raw cell text.

    Returns:
        The cell text, with a guard character when the cell would run.
    """
    if value.startswith(FORMULA_LEADERS) and not _reads_as_a_number(value):  # A number keeps its own form.
        return FORMULA_GUARD + value  # The quotation mark makes a spreadsheet read the cell as text.
    return value  # The cell holds no formula, so it passes through unchanged.


# ---------------------------------------------------------------------------
# The row record
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ExportRow:
    """One device or one client of one capture, ready to write.

    Why:
        The two formats write the same rows. Building the row once keeps the
        comma-separated file and the JSON file in step, so a reader can join
        them.

    Attributes:
        kind: The row kind. One of the four `KIND_` values.
        mac: The address of the device or of the client.
        values: The cell of every column of `EXPORT_COLUMNS`.
    """

    kind: str = ""
    mac: str = ""
    values: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, str]:
        """Return the row under the fixed column names.

        Why:
            Both writers read the same columns. One converter keeps the column
            order and the column names in a single place.

        Returns:
            A dictionary with every name of `EXPORT_COLUMNS`.
        """
        return {name: self.values.get(name, "") for name in EXPORT_COLUMNS}  # A missing column reads as empty.


# ---------------------------------------------------------------------------
# The row builders
# ---------------------------------------------------------------------------


def _as_text(value: Any) -> str:
    """Return one captured value as text.

    Why:
        A comma-separated file holds text alone, and the JSON file must match
        it column for column. An absent value becomes an empty cell rather than
        the word `None`.

    Args:
        value: The captured value.

    Returns:
        The value as text, or an empty string.
    """
    if value is None:  # The cloud sends a null value for a field it never read.
        return ""  # An empty cell reads better than the word None.
    return _one_line(str(value))  # A number, a flag, and a word all read the same way.


def _one_line(value: str) -> str:
    """Return one value with every line break replaced by a space.

    Why:
        A cloud value can hold a line break. A line break inside a cell splits
        one row into two rows for a reader that does not honor the quoting, so
        the writer removes it before the cell reaches the file.

    Args:
        value: The raw value.

    Returns:
        The value on one line.
    """
    for marker in _LINE_BREAKS:  # The cloud may send any of the three forms.
        value = value.replace(marker, " ")  # A space keeps the words apart.
    return value.strip()  # A leading space or a trailing space carries no meaning.


def _readable(record: Mapping[str, Any]) -> dict[str, Any]:
    """Return one captured record with every credential field removed.

    Why:
        The column list names no credential today. This filter guards the day
        somebody adds one, and it guards a cloud field that arrives under a
        name the column list already holds.

    Args:
        record: One device index entry or one client record.

    Returns:
        The record, without any field whose name reads as a secret.
    """
    return {name: value for name, value in record.items() if not is_credential_field(str(name))}


def _blank_values(heading: Mapping[str, str]) -> dict[str, str]:
    """Return one cell for every column, with the naming columns already filled.

    Why:
        A device row uses no client column and a client row uses no device
        column. An empty cell keeps both row shapes on the same column list.
        The five naming columns hold the same value on every row, so a reader
        of one row alone can still tell which capture wrote it.

    Args:
        heading: The five values that name the capture.

    Returns:
        A map from each column name to its starting value.
    """
    values = dict.fromkeys(EXPORT_COLUMNS, "")  # Every column exists, so no row is short.
    values.update({name: heading.get(name, "") for name in HEADING_COLUMNS})  # Every row names its capture.
    return values


def _device_row(mac: str, entry: Mapping[str, Any], heading: Mapping[str, str]) -> ExportRow:
    """Return the export row of one device.

    Args:
        mac: The address of the device, which is the index key.
        entry: One device index entry.
        heading: The five values that name the capture.

    Returns:
        The row of that device.
    """
    readable = _readable(entry)  # No credential field reaches a cell.
    values = _blank_values(heading)  # Every client column stays empty on a device row.
    values.update({name: _as_text(readable.get(name)) for name in DEVICE_FIELDS})  # The nine device columns.
    values["kind"] = KIND_DEVICE  # A reader filters the file on this column.
    values["mac"] = mac  # The index key names the member, so a chassis member keeps its own row.
    return ExportRow(kind=KIND_DEVICE, mac=mac, values=values)


def _client_row(kind: str, record: Mapping[str, Any], heading: Mapping[str, str]) -> ExportRow:
    """Return the export row of one client.

    Args:
        kind: The row kind of the client group.
        record: One client record.
        heading: The five values that name the capture.

    Returns:
        The row of that client.
    """
    readable = _readable(record)  # No credential field reaches a cell.
    values = _blank_values(heading)  # Every device column stays empty on a client row.
    values.update({name: _as_text(readable.get(name)) for name in CLIENT_FIELDS})  # The six client columns.
    values.update({name: _as_text(readable.get(source)) for name, source in CLIENT_PARENT_FIELDS})  # The parent.
    values["kind"] = kind  # A reader filters the wired rows apart from the wireless rows.
    values["mac"] = _as_text(readable.get("mac"))  # The match key of the client.
    return ExportRow(kind=kind, mac=values["mac"], values=values)


def device_entries(capture: Mapping[str, Any]) -> list[tuple[str, Mapping[str, Any]]]:
    """Return one address and one record for each device of one capture.

    Why:
        `data-model.md` section 3.3 fills the device index from the physical
        view, so every chassis member holds its own entry. That map also holds
        the firmware version, the status, and the uptime, which the raw device
        list does not. The raw list is the fallback for an older document that
        holds no index.

    Args:
        capture: The stored capture document.

    Returns:
        One pair for each device, in the order the capture stored them.
    """
    index: Any = capture.get("device_index")  # The map that the comparison reads.
    if isinstance(index, Mapping) and index:  # The normal path for every capture of this release.
        return [(str(key), entry) for key, entry in index.items() if isinstance(entry, Mapping)]
    records: Any = capture.get("devices") or []  # An older document holds the raw list alone.
    return [(str(row.get("mac", "")), row) for row in records if isinstance(row, Mapping)]


def device_rows(capture: Mapping[str, Any]) -> list[ExportRow]:
    """Return one export row for each device of one capture.

    Args:
        capture: The stored capture document.

    Returns:
        The device rows.
    """
    heading = capture_heading(capture)  # Every row names the same capture, so the writer reads it one time.
    return [_device_row(mac, entry, heading) for mac, entry in device_entries(capture)]


def client_rows(capture: Mapping[str, Any]) -> list[ExportRow]:
    """Return one export row for each client of one capture.

    Why:
        The three groups write into one list, and the kind column keeps them
        apart. A reader then sorts the whole file on one column.

    Args:
        capture: The stored capture document.

    Returns:
        The wired rows, then the wireless rows, then the guest rows.
    """
    groups: Any = capture.get("clients") or {}  # A capture that read no client holds an empty map.
    if not isinstance(groups, Mapping):  # A document of a later release may hold another shape.
        logger.warning("capture export: the client section is not a map, so the file holds no client row")
        return []
    heading = capture_heading(capture)  # Every row names the same capture, so the writer reads it one time.
    rows: list[ExportRow] = []  # The three groups write into one list.
    for group, kind in CLIENT_GROUPS:  # The order of `CLIENT_GROUPS` fixes the row order.
        records: Any = groups.get(group) or []  # A group the capture did not read holds no record.
        rows.extend(_client_row(kind, record, heading) for record in records if isinstance(record, Mapping))
    return rows


def build_rows(capture: Mapping[str, Any]) -> tuple[ExportRow, ...]:
    """Return one row for every device and every client of one capture.

    Why:
        Acceptance Scenario 3 requires that the file holds every captured row.
        The download therefore reports the whole capture, and not the changed
        part of it.

    Args:
        capture: The stored capture document.

    Returns:
        The device rows first, then the client rows.
    """
    logger.info("capture export: build the rows of the capture %s", _as_text(capture.get("capture_id")) or "unnamed")
    rows = tuple(device_rows(capture) + client_rows(capture))  # The device rows read first, as the page shows them.
    logger.debug("capture export: built %s rows", len(rows))  # The count proves that no row was dropped.
    return rows


# ---------------------------------------------------------------------------
# The writers
# ---------------------------------------------------------------------------


def capture_heading(capture: Mapping[str, Any]) -> dict[str, str]:
    """Return the five values that name one capture.

    Why:
        FR-027 requires the organization, the site, the capture identifier, the
        role, and the moment of the capture. A file without them cannot be
        matched to a change record.

    Args:
        capture: The stored capture document.

    Returns:
        The five values, as text.
    """
    return {
        "org_name": _as_text(capture.get("org_name")),  # The organization that holds the site.
        "site_name": _as_text(capture.get("site_name")),  # The site that the capture read.
        "capture_id": _as_text(capture.get("capture_id")),  # The natural business key of the capture.
        "role": _as_text(capture.get("role")),  # `pre` before the upgrade, `post` after it.
        "captured_at": _as_text(capture.get("started_at") or capture.get("finished_at")),  # The moment, in UTC.
    }


def render_csv(rows: Iterable[ExportRow]) -> str:
    """Return the capture in comma-separated value form.

    Why:
        The operator opens this file in a spreadsheet. The header line names
        the fixed columns, so the file reads the same after every capture. The
        five naming columns sit on every row, so the file needs no preamble and
        a spreadsheet reads the whole file as one table.

    Args:
        rows: The export rows.

    Returns:
        The whole file as text, with the header line first.
    """
    buffer = io.StringIO()  # The route answers with text, so the writer needs no file.
    writer = csv.DictWriter(buffer, fieldnames=list(EXPORT_COLUMNS))  # The column order never changes.
    writer.writeheader()  # The header line opens the file.
    for row in rows:  # Each row writes one device or one client.
        writer.writerow({name: disarm_cell(value) for name, value in row.to_dict().items()})  # No cell may run.
    return buffer.getvalue()


def render_json(heading: Mapping[str, str], rows: Iterable[ExportRow]) -> str:
    """Return the capture in JSON form.

    Why:
        Another program reads this file, so the rows keep the same column names
        as the comma-separated file. The heading sits beside the rows, so one
        read names the capture and holds its data.

    Args:
        heading: The five values that name the capture.
        rows: The export rows.

    Returns:
        The whole file as text.
    """
    payload = {"capture": dict(heading), "rows": [row.to_dict() for row in rows]}  # One object holds both parts.
    return json.dumps(payload, indent=_JSON_INDENT)  # The indent keeps the file readable for a person as well.


# ---------------------------------------------------------------------------
# The result record and the entry point
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ExportResult:
    """The result of one download request.

    Why:
        The route needs the body, the media type, and the file name together,
        and it needs the refusal in the same shape. One record answers both
        outcomes, so the route holds no branch of its own.

    Attributes:
        body: The file content. Empty on a refusal.
        media_type: The media type of the file. Empty on a refusal.
        filename: The name to offer the browser. Empty on a refusal.
        error: The error code, or an empty string on success.
    """

    body: str = ""
    media_type: str = ""
    filename: str = ""
    error: str = ""

    @property
    def ok(self) -> bool:
        """Return whether the export succeeded.

        Why:
            The route tests one value rather than comparing the error code
            against an empty string in two places.

        Returns:
            True when the result holds no error code.
        """
        return not self.error


def _chosen_format(export_format: object) -> str:
    """Return one requested format name in its stored spelling.

    Why:
        The format arrives in the address bar, so it may hold spaces or capital
        letters. Trimming the value here keeps the refusal for a real mistake
        rather than a stray space.

    Args:
        export_format: The raw format value.

    Returns:
        The trimmed lower case name, or an empty string.
    """
    if not isinstance(export_format, str):  # A caller may hand over any object.
        return ""  # An unreadable value falls into the refusal below.
    return export_format.strip().lower()  # `  CSV  ` and `csv` name the same format.


def download_name(capture: Mapping[str, Any], extension: str) -> str:
    """Return the file name to offer the browser.

    Why:
        An operator downloads the pre-check capture and the post-check capture
        of one run, so the two names must differ. The identifier reaches a
        response header, so every character outside the safe set leaves it.

    Args:
        capture: The stored capture document.
        extension: The file extension, with no leading dot.

    Returns:
        The download name.
    """
    stem = _SAFE_NAME.sub("", _as_text(capture.get("capture_id")))  # A quotation mark would break the header.
    return FILENAME_STEM + stem + "." + extension if stem else FALLBACK_STEM + "." + extension


def export_capture(capture: Mapping[str, Any], export_format: object) -> ExportResult:
    """Return the download of one capture in the requested format.

    Why:
        The route asks for one file and gets either the file or the refusal in
        the same record. The refusal names `bad_format`, which the route returns
        with status 400.

    Args:
        capture: The stored capture document.
        export_format: `csv` or `json`.

    Returns:
        The file and its media type, or the `bad_format` refusal.
    """
    chosen = _chosen_format(export_format)  # An empty value falls into the refusal below.
    if chosen not in SUPPORTED_FORMATS:  # A guess would hand the operator a file of the wrong type.
        # WHY: The raw value never reaches the log. It arrives from the address
        # bar and could carry a line break that fakes a log line.
        logger.warning("capture export: the portal refused a download, because the format is not known")
        return ExportResult(error=ERROR_BAD_FORMAT)  # The route answers 400 with this code.
    rows = build_rows(capture)  # Every device row and every client row. Each one names the capture.
    if chosen == FORMAT_CSV:  # The spreadsheet form.
        return ExportResult(render_csv(rows), MEDIA_TYPE_CSV, download_name(capture, FORMAT_CSV))
    heading = capture_heading(capture)  # The machine form repeats the five values in one object.
    return ExportResult(render_json(heading, rows), MEDIA_TYPE_JSON, download_name(capture, FORMAT_JSON))


def column_names() -> Sequence[str]:
    """Return the fixed column names of the download.

    Why:
        A contract test reads the header line of the file. Naming the columns
        through one function keeps the test from repeating the list.

    Returns:
        The column names, in file order.
    """
    return EXPORT_COLUMNS


__all__ = [
    "CLIENT_FIELDS",
    "CLIENT_GROUPS",
    "CLIENT_PARENT_FIELDS",
    "CREDENTIAL_WORDS",
    "DEVICE_FIELDS",
    "ERROR_BAD_FORMAT",
    "EXPORT_COLUMNS",
    "FORMAT_CSV",
    "FORMAT_JSON",
    "FORMULA_GUARD",
    "FORMULA_LEADERS",
    "HEADER_MARKER",
    "HEADING_COLUMNS",
    "KIND_CLIENT_GUEST",
    "KIND_CLIENT_WIRED",
    "KIND_CLIENT_WIRELESS",
    "KIND_DEVICE",
    "MEDIA_TYPE_CSV",
    "MEDIA_TYPE_JSON",
    "SUPPORTED_FORMATS",
    "ExportResult",
    "ExportRow",
    "build_rows",
    "capture_heading",
    "client_rows",
    "column_names",
    "device_entries",
    "device_rows",
    "disarm_cell",
    "download_name",
    "export_capture",
    "is_credential_field",
    "render_csv",
    "render_json",
]
