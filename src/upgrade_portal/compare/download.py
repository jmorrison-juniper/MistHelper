"""The comparison download in comma-separated value form and in JSON form.

Why:
    An operator attaches the comparison to a change record, so the download
    must open in a spreadsheet and must also feed another program. One row
    holds one difference, which lets a reader sort and filter the file without
    unpacking a nested structure.

    The file never holds a credential. The row columns are fixed and the
    builder drops any field whose name reads as a secret, so a future capture
    field cannot leak into a downloaded file.

    An unknown format returns the error code ``bad_format`` rather than a
    guess. A guess would hand the operator a file of the wrong type and would
    hide the mistake.
"""

from __future__ import annotations

import csv
import io
import json
import logging
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any

from src.upgrade_portal.compare import clients as client_compare
from src.upgrade_portal.compare import diff as device_compare

logger = logging.getLogger(__name__)

FORMAT_CSV = "csv"
FORMAT_JSON = "json"
SUPPORTED_FORMATS = (FORMAT_CSV, FORMAT_JSON)

ERROR_BAD_FORMAT = "bad_format"

MEDIA_TYPE_CSV = "text/csv"
MEDIA_TYPE_JSON = "application/json"

FILENAME_CSV = "upgrade-comparison.csv"
FILENAME_JSON = "upgrade-comparison.json"

KIND_DEVICE = "device"
KIND_CLIENT = "client"

# The one client field that a move changes. A move is the only client
# difference that carries a value before and a value after.
CLIENT_MOVE_FIELD = "device_mac"

EXPORT_COLUMNS = ("kind", "mac", "name", "outcome", "field", "before", "after")

# WHY: The export must never write a credential. The comparison reads no
# credential field today, so this list guards a future capture field rather
# than a present one.
CREDENTIAL_WORDS = ("password", "secret", "token", "credential", "authorization", "api_key", "apikey", "passphrase")

# WHY: A spreadsheet runs a cell that starts with one of these characters. A
# device name comes from the cloud, so the writer disarms the cell. The minus
# sign belongs in the list, because `-1+cmd|' /c calc'!A0` is a formula that
# starts with a minus sign. A tab and a carriage return lead the same way.
_FORMULA_LEADERS = ("=", "+", "@", "-", "\t", "\r")
_FORMULA_GUARD = "'"

_JSON_INDENT = 2


# ---------------------------------------------------------------------------
# The row records
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RowChange:
    """The changed field of one export row.

    Why:
        An added device and a removed device carry no field, while a changed
        device carries one field for each row. One record covers both, so the
        column list never changes between rows.

    Attributes:
        field: The name of the changed field, or an empty string.
        before: The value in the pre-check capture, as text.
        after: The value in the post-check capture, as text.
    """

    field: str = ""
    before: str = ""
    after: str = ""


@dataclass(frozen=True, slots=True)
class ExportRow:
    """One difference of one comparison, ready to write.

    Why:
        The two formats write the same rows. Building the row once keeps the
        comma-separated file and the JSON file in step, so a reader can join
        them.

    Attributes:
        kind: ``device`` or ``client``.
        mac: The address of the device or the client.
        name: The device name or the client name.
        outcome: The outcome of the record.
        change: The changed field, when the outcome carries one.
    """

    kind: str = ""
    mac: str = ""
    name: str = ""
    outcome: str = ""
    change: RowChange = field(default_factory=RowChange)

    def to_dict(self) -> dict[str, str]:
        """Return the row under the fixed column names.

        Why:
            Both writers read the same seven columns. One converter keeps the
            column order and the column names in a single place.

        Returns:
            A dictionary with every name of ``EXPORT_COLUMNS``.
        """
        return {
            "kind": self.kind,
            "mac": self.mac,
            "name": self.name,
            "outcome": self.outcome,
            "field": self.change.field,
            "before": self.change.before,
            "after": self.change.after,
        }


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


# ---------------------------------------------------------------------------
# The row builders
# ---------------------------------------------------------------------------


def is_credential_field(name: str) -> bool:
    """Return whether one field name reads as a secret.

    Why:
        The comparison writes a downloaded file that an operator attaches to
        a change record. A secret in that file would travel further than the
        portal. The test runs on the name, so a new capture field is refused
        before anybody notices it.

    Args:
        name: The field name to test.

    Returns:
        True when the name holds a word of ``CREDENTIAL_WORDS``.
    """
    lowered = name.lower()
    return any(word in lowered for word in CREDENTIAL_WORDS)


def _as_text(value: Any) -> str:
    """Return one compared value as text.

    Why:
        A comma-separated file holds text alone, and the JSON file must match
        it column for column. An absent value becomes an empty cell rather
        than the word ``None``.

    Args:
        value: The compared value.

    Returns:
        The value as text, or an empty string.
    """
    if value is None:
        return ""
    return str(value)


def _device_rows_of(delta: device_compare.DeviceDelta) -> list[ExportRow]:
    """Return every export row of one device difference.

    Why:
        A changed device writes one row for each differing field, so a reader
        can sort the file by field and see every version change together. An
        added device and a removed device write one row with no field.

        A device whose every change is a credential field still changed. It
        keeps one row that names no field, because a device that vanished from
        the file would tell the reader that nothing happened to it.

    Args:
        delta: One device difference record.

    Returns:
        The rows of that device. Always at least one row.
    """
    base = ExportRow(kind=KIND_DEVICE, mac=delta.mac, name=delta.name, outcome=delta.outcome)
    if delta.outcome != device_compare.OUTCOME_CHANGED:
        return [base]
    rows = [
        ExportRow(
            kind=KIND_DEVICE,
            mac=delta.mac,
            name=delta.name,
            outcome=delta.outcome,
            change=RowChange(field=change.field, before=_as_text(change.before), after=_as_text(change.after)),
        )
        for change in delta.changes
        if not is_credential_field(change.field)
    ]
    return rows or [base]


def _client_row_of(delta: client_compare.ClientDelta) -> ExportRow:
    """Return the export row of one client difference.

    Why:
        A move is the only client difference with two values, and the two
        values are the serving devices. Naming the field keeps the column
        meaning the same as a device row.

    Args:
        delta: One client difference record.

    Returns:
        The row of that client.
    """
    change = RowChange()
    if delta.outcome == client_compare.OUTCOME_MOVED:
        change = RowChange(
            field=CLIENT_MOVE_FIELD,
            before=delta.move.before_device,
            after=delta.move.after_device,
        )
    return ExportRow(
        kind=KIND_CLIENT,
        mac=delta.mac,
        name=delta.hostname,
        outcome=delta.outcome,
        change=change,
    )


def build_rows(
    devices: device_compare.DeviceComparison,
    clients: client_compare.ClientComparison,
) -> tuple[ExportRow, ...]:
    """Return one row for each difference of one comparison.

    Why:
        The download reports differences. A device that did not change and a
        client that stayed on the same access point are not differences, so
        they write no row and keep the file short.

    Args:
        devices: The device half of the comparison.
        clients: The client half of the comparison.

    Returns:
        The device rows first, then the client rows.
    """
    rows: list[ExportRow] = []
    for device_delta in devices.deltas:
        if device_delta.outcome != device_compare.OUTCOME_UNCHANGED:
            rows.extend(_device_rows_of(device_delta))
    for client_delta in clients.deltas:
        if client_delta.outcome != client_compare.OUTCOME_PRESENT:
            rows.append(_client_row_of(client_delta))
    logger.info("Upgrade portal built %s comparison download rows", len(rows))
    return tuple(rows)


# ---------------------------------------------------------------------------
# The writers
# ---------------------------------------------------------------------------


def _reads_as_a_number(value: str) -> bool:
    """Return whether the whole cell reads as one number.

    Why:
        A minus sign starts a negative number and it also starts a formula.
        A cell that reads as a number holds no formula, so the writer leaves
        it alone and a spreadsheet still sums the column.

    Args:
        value: The raw cell text.

    Returns:
        True when the text is a plain number.
    """
    try:
        float(value)
    except ValueError:
        return False
    return True


def _disarm(value: str) -> str:
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
    if value.startswith(_FORMULA_LEADERS) and not _reads_as_a_number(value):
        return _FORMULA_GUARD + value
    return value


def render_csv(rows: Iterable[ExportRow]) -> str:
    """Return the rows in comma-separated value form.

    Why:
        The operator opens this file in a spreadsheet. The header line names
        the fixed columns, so the file reads the same after every run.

    Args:
        rows: The export rows.

    Returns:
        The whole file as text, with a header line first.
    """
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(EXPORT_COLUMNS))
    writer.writeheader()
    for row in rows:
        writer.writerow({name: _disarm(value) for name, value in row.to_dict().items()})
    return buffer.getvalue()


def render_json(rows: Iterable[ExportRow]) -> str:
    """Return the rows in JSON form.

    Why:
        Another program reads this file, so the rows keep the same seven
        column names as the comma-separated file. The text stays inside the
        ASCII range, which keeps every reader in agreement.

    Args:
        rows: The export rows.

    Returns:
        The whole file as text.
    """
    return json.dumps([row.to_dict() for row in rows], indent=_JSON_INDENT)


def _chosen_format(export_format: object) -> str:
    """Return one requested format name in its stored spelling.

    Why:
        The format arrives in the address bar, so it may hold spaces or
        capital letters. Trimming the value here keeps the refusal for a real
        mistake rather than a stray space.

    Args:
        export_format: The raw format value.

    Returns:
        The trimmed lower case name, or an empty string.
    """
    if not isinstance(export_format, str):
        return ""
    return export_format.strip().lower()


def export_comparison(
    devices: device_compare.DeviceComparison,
    clients: client_compare.ClientComparison,
    export_format: object,
) -> ExportResult:
    """Return the download of one comparison in the requested format.

    Why:
        The route asks for one file and gets either the file or the refusal
        in the same record. The refusal names ``bad_format``, which the route
        returns with status 400.

    Args:
        devices: The device half of the comparison.
        clients: The client half of the comparison.
        export_format: ``csv`` or ``json``.

    Returns:
        The file and its media type, or the ``bad_format`` refusal.
    """
    chosen = _chosen_format(export_format)
    if chosen not in SUPPORTED_FORMATS:
        # WHY: The raw value never reaches the log. It arrives from the
        # address bar and could carry a line break that fakes a log line.
        logger.warning("Upgrade portal refused a comparison download, because the format is not known")
        return ExportResult(error=ERROR_BAD_FORMAT)
    rows = build_rows(devices, clients)
    if chosen == FORMAT_CSV:
        return ExportResult(body=render_csv(rows), media_type=MEDIA_TYPE_CSV, filename=FILENAME_CSV)
    return ExportResult(body=render_json(rows), media_type=MEDIA_TYPE_JSON, filename=FILENAME_JSON)


def column_names() -> Sequence[str]:
    """Return the fixed column names of the download.

    Why:
        The contract test reads the header line of the file. Naming the
        columns through one function keeps the test from repeating the list.

    Returns:
        The column names, in file order.
    """
    return EXPORT_COLUMNS


__all__ = [
    "CLIENT_MOVE_FIELD",
    "CREDENTIAL_WORDS",
    "ERROR_BAD_FORMAT",
    "EXPORT_COLUMNS",
    "FILENAME_CSV",
    "FILENAME_JSON",
    "FORMAT_CSV",
    "FORMAT_JSON",
    "KIND_CLIENT",
    "KIND_DEVICE",
    "MEDIA_TYPE_CSV",
    "MEDIA_TYPE_JSON",
    "SUPPORTED_FORMATS",
    "ExportResult",
    "ExportRow",
    "RowChange",
    "build_rows",
    "column_names",
    "export_comparison",
    "is_credential_field",
    "render_csv",
    "render_json",
]
