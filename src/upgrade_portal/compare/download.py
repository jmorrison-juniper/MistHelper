"""The comparison download in comma-separated value form and in JSON form.

Why:
    An operator attaches the comparison to a change record, so the download
    must open in a spreadsheet and must also feed another program. One row
    holds one difference, which lets a reader sort and filter the file without
    unpacking a nested structure.

    The download offers two scopes. The ``differences`` scope writes the rows
    that changed and keeps the file short. The ``full`` scope writes every row
    of both captures, because a file that names no device cannot prove that an
    upgrade did no harm. User Story 2, acceptance scenario 5 of the feature
    specification asks for that proof, and FR-070 asks for the file.

    The full file starts with a header block that names the two captures, the
    site, the organization, the two moments, and every statistic. A record
    keeper then reads the whole result from the file alone.

    The file never holds a credential. The row columns are fixed, and the
    builder drops any field whose name reads as a secret. A future capture
    field therefore cannot leak into a downloaded file.

    An unknown format returns the error code ``bad_format`` rather than a
    guess, and an unknown scope returns ``bad_scope``. A guess would hand the
    operator a file of the wrong type and would hide the mistake.
"""

from __future__ import annotations

import csv
import io
import json
import logging
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from src.upgrade_portal.compare import clients as client_compare
from src.upgrade_portal.compare import diff as device_compare
from src.upgrade_portal.compare import statistics as compare_statistics

logger = logging.getLogger(__name__)

FORMAT_CSV = "csv"
FORMAT_JSON = "json"
SUPPORTED_FORMATS = (FORMAT_CSV, FORMAT_JSON)

SCOPE_DIFFERENCES = "differences"
SCOPE_FULL = "full"
SUPPORTED_SCOPES = (SCOPE_DIFFERENCES, SCOPE_FULL)

ERROR_BAD_FORMAT = "bad_format"
ERROR_BAD_SCOPE = "bad_scope"

MEDIA_TYPE_CSV = "text/csv"
MEDIA_TYPE_JSON = "application/json"

FILENAME_CSV = "upgrade-comparison.csv"
FILENAME_JSON = "upgrade-comparison.json"
FILENAME_FULL_CSV = "upgrade-comparison-full.csv"
FILENAME_FULL_JSON = "upgrade-comparison-full.json"

KIND_DEVICE = "device"
KIND_CLIENT = "client"

# The two columns of the header block that opens the full comma-separated file.
SUMMARY_COLUMNS = ("detail", "value")

# The three top level names of the full JSON file.
SUMMARY_KEY = "summary"
STATISTICS_KEY = "statistics"
ROWS_KEY = "rows"

# The header block detail names. The page and the file use the same words, so
# an operator reads one term for one thing.
SITE_DETAIL = "site"
SITE_ID_DETAIL = "site_id"
ORGANIZATION_DETAIL = "organization"
SKIPPED_DETAIL = "skipped_sections"

# The two prefixes that separate the pre-check capture from the post-check
# capture inside the header block.
BEFORE_PREFIX = "before"
AFTER_PREFIX = "after"

# The capture fields that the header block reads.
_CAPTURE_ID_KEY = "capture_id"
_ROLE_KEY = "role"
_SITE_NAME_KEY = "site_name"
_SITE_ID_KEY = "site_id"
_ORG_NAME_KEY = "org_name"

# WHY: A caller that hands a value of another type asked for no known scope. A
# name that no scope carries turns that value into the ``bad_scope`` refusal,
# while an empty text still means the default scope.
_UNKNOWN_SCOPE = "unknown"

# The words that join the skipped section names in one header cell.
_SECTION_JOIN = ", "

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


@dataclass(frozen=True, slots=True)
class ExportContext:
    """The two captures and the statistics that the full download needs.

    Why:
        The differences file needs the two comparison halves alone. The full
        file must also name the site, the organization, the two moments, and
        every statistic. One record carries that extra reading, so the export
        keeps one signature for both scopes.

    Attributes:
        before: The pre-check capture.
        after: The post-check capture.
        statistics: The flat statistics of the comparison.
    """

    before: Mapping[str, Any] = field(default_factory=dict)
    after: Mapping[str, Any] = field(default_factory=dict)
    statistics: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class FullExport:
    """Every part of one full download, ready to write.

    Why:
        The two formats write the same rows, the same header block, and the
        same statistics. Building the parts once keeps the comma-separated
        file and the JSON file in step, so a reader can join them.

    Attributes:
        rows: Every row of both captures.
        summary: The header block details, as text.
        statistics: The statistics, with each credential name dropped.
    """

    rows: tuple[ExportRow, ...] = ()
    summary: dict[str, str] = field(default_factory=dict)
    statistics: dict[str, Any] = field(default_factory=dict)


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
        A changed device writes one row for each differing field. A reader can
        then sort the file by field and see every version change together. An
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
        client that stayed on the same access point are not differences. They
        write no row, and the file stays short.

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
# The full row builders
# ---------------------------------------------------------------------------


def _skipped_sections(
    devices: device_compare.DeviceComparison,
    clients: client_compare.ClientComparison,
) -> tuple[str, ...]:
    """Return every section that a matching digest skipped.

    Why:
        A skipped section carries no delta at all. The full download must know
        about the skip, because it has to rebuild the missing rows.

    Args:
        devices: The device half of the comparison.
        clients: The client half of the comparison.

    Returns:
        The device skips followed by the client skips.
    """
    return (*devices.skipped_sections, *clients.skipped_sections)


def _without_digests(capture: Mapping[str, Any]) -> dict[str, Any]:
    """Return one capture that carries no digest.

    Why:
        The comparison compares two digests and skips the whole section when
        they match. A capture without a digest forces the comparison to read
        every record, which is what the full download needs.

    Args:
        capture: One stored capture.

    Returns:
        The same capture, without the digest map.
    """
    return {name: value for name, value in capture.items() if name != device_compare.DIGESTS_KEY}


def _rebuilt_parts(
    context: ExportContext,
) -> tuple[device_compare.DeviceComparison, client_compare.ClientComparison, dict[str, Any]]:
    """Return the whole comparison of two captures, with no section skipped.

    Why:
        A matching digest proves that every record of that section is
        unchanged. Comparing the two captures again without the digests names
        each of those records, and counting them again keeps the file in
        agreement with itself.

    Args:
        context: The two captures and the statistics.

    Returns:
        The device half, the client half, and the recounted statistics.
    """
    before = _without_digests(context.before)
    after = _without_digests(context.after)
    devices = device_compare.compare_devices(before, after)
    clients = client_compare.compare_clients(before, after)
    elapsed = compare_statistics.elapsed_seconds_between(before, after)
    return devices, clients, compare_statistics.build_statistics(devices, clients, elapsed).to_dict()


def _complete_parts(
    devices: device_compare.DeviceComparison,
    clients: client_compare.ClientComparison,
    context: ExportContext,
) -> tuple[device_compare.DeviceComparison, client_compare.ClientComparison, dict[str, Any]]:
    """Return a comparison that names every record of both captures.

    Why:
        A comparison that skipped a section holds no row for that section. The
        full download rebuilds those rows from the two captures. A caller that
        gave no capture gets the comparison it handed in, because a rebuild
        without a capture would invent rows.

    Args:
        devices: The device half of the comparison.
        clients: The client half of the comparison.
        context: The two captures and the statistics.

    Returns:
        The device half, the client half, and the statistics to write.
    """
    given = dict(context.statistics)
    if not _skipped_sections(devices, clients):
        return devices, clients, given
    if not context.before or not context.after:
        logger.warning("Upgrade portal cannot rebuild a skipped comparison, because a capture is missing")
        return devices, clients, given
    logger.info("Upgrade portal rebuilds a skipped comparison for the full download")
    rebuilt_devices, rebuilt_clients, rebuilt_statistics = _rebuilt_parts(context)
    logger.debug(
        "Upgrade portal rebuilt %s device records and %s client records",
        len(rebuilt_devices.deltas),
        len(rebuilt_clients.deltas),
    )
    return rebuilt_devices, rebuilt_clients, rebuilt_statistics


def _rows_without_a_filter(
    devices: device_compare.DeviceComparison,
    clients: client_compare.ClientComparison,
) -> list[ExportRow]:
    """Return one row for every record of both halves.

    Why:
        The full download keeps the unchanged device and the client that
        stayed. Those rows are the proof that the upgrade did no harm, so the
        builder applies no outcome filter.

    Args:
        devices: The device half of the comparison.
        clients: The client half of the comparison.

    Returns:
        The device rows first, then the client rows.
    """
    rows: list[ExportRow] = []
    for device_delta in devices.deltas:
        rows.extend(_device_rows_of(device_delta))
    for client_delta in clients.deltas:
        rows.append(_client_row_of(client_delta))
    return rows


def _capture_details(capture: Mapping[str, Any], prefix: str) -> dict[str, str]:
    """Return the header block details of one capture.

    Why:
        The reader must tell the pre-check capture from the post-check capture
        at a glance. A prefix on each name keeps the two sets apart without a
        nested structure that a spreadsheet cannot show.

    Args:
        capture: One stored capture.
        prefix: ``before`` or ``after``.

    Returns:
        Four details, named under the prefix.
    """
    return {
        prefix + "_" + _CAPTURE_ID_KEY: _as_text(capture.get(_CAPTURE_ID_KEY, "")),
        prefix + "_" + _ROLE_KEY: _as_text(capture.get(_ROLE_KEY, "")),
        prefix + "_" + compare_statistics.STARTED_AT_KEY: _as_text(capture.get(compare_statistics.STARTED_AT_KEY, "")),
        prefix
        + "_"
        + compare_statistics.FINISHED_AT_KEY: _as_text(capture.get(compare_statistics.FINISHED_AT_KEY, "")),
    }


def build_summary(context: ExportContext, skipped: tuple[str, ...] = ()) -> dict[str, str]:
    """Return the header block details of one comparison.

    Why:
        The operator attaches the file to a change record. That record must name
        the site and the two captures without the portal beside it.
        Both captures name the same site, so either one answers.

    Args:
        context: The two captures and the statistics.
        skipped: Every section that a matching digest skipped.

    Returns:
        One entry for each header block detail, as text.
    """
    named = context.after or context.before
    summary = {
        SITE_DETAIL: _as_text(named.get(_SITE_NAME_KEY, "")),
        SITE_ID_DETAIL: _as_text(named.get(_SITE_ID_KEY, "")),
        ORGANIZATION_DETAIL: _as_text(named.get(_ORG_NAME_KEY, "")),
        SKIPPED_DETAIL: _SECTION_JOIN.join(skipped),
    }
    summary.update(_capture_details(context.before, BEFORE_PREFIX))
    summary.update(_capture_details(context.after, AFTER_PREFIX))
    return summary


def safe_statistics(statistics: Mapping[str, Any]) -> dict[str, Any]:
    """Return the statistics without any name that reads as a secret.

    Why:
        The statistics reach the file from the caller. The same rule that
        guards a capture field must guard a statistic name, so a caller cannot
        put a secret into the header block.

    Args:
        statistics: The flat statistics of the comparison.

    Returns:
        The statistics that the file may hold.
    """
    return {name: value for name, value in statistics.items() if not is_credential_field(name)}


def build_full_export(
    devices: device_compare.DeviceComparison,
    clients: client_compare.ClientComparison,
    context: ExportContext | None = None,
) -> FullExport:
    """Return every part of the full download of one comparison.

    Why:
        The comma-separated file and the JSON file hold the same rows and the
        same header block. Building both parts once stops the two files from
        disagreeing.

    Args:
        devices: The device half of the comparison.
        clients: The client half of the comparison.
        context: The two captures and the statistics.

    Returns:
        The rows, the header block, and the statistics.
    """
    reading = context or ExportContext()
    skipped = _skipped_sections(devices, clients)
    whole_devices, whole_clients, statistics = _complete_parts(devices, clients, reading)
    rows = tuple(_rows_without_a_filter(whole_devices, whole_clients))
    logger.info("Upgrade portal built %s full comparison download rows", len(rows))
    return FullExport(rows=rows, summary=build_summary(reading, skipped), statistics=safe_statistics(statistics))


def build_full_rows(
    devices: device_compare.DeviceComparison,
    clients: client_compare.ClientComparison,
    context: ExportContext | None = None,
) -> tuple[ExportRow, ...]:
    """Return one row for every record of both captures.

    Why:
        A caller that wants the rows alone should not unpack the whole export
        record. The rebuild of a skipped section happens here as well, so both
        callers read the same rows.

    Args:
        devices: The device half of the comparison.
        clients: The client half of the comparison.
        context: The two captures and the statistics.

    Returns:
        The device rows first, then the client rows.
    """
    return build_full_export(devices, clients, context).rows


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


def build_details(export: FullExport) -> dict[str, str]:
    """Return the header block of one full file, as text.

    Why:
        A comma-separated cell holds text alone. Turning each statistic into
        text here keeps the writer free of a type test.

    Args:
        export: The parts of the full download.

    Returns:
        The header block details, in file order.
    """
    details = dict(export.summary)
    details.update({name: _as_text(value) for name, value in export.statistics.items()})
    return details


def _render_detail_block(details: Mapping[str, str]) -> str:
    """Return the header block of one full comma-separated file.

    Why:
        A spreadsheet reads two tables from one file when a blank line stands
        between them. The block therefore ends with a blank line, and the row
        columns follow it.

        Both cells pass the formula guard. A site name comes from the cloud,
        so a name that starts with an equals sign must not run.

    Args:
        details: The header block details.

    Returns:
        The header block, with a blank line at its end.
    """
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(list(SUMMARY_COLUMNS))
    for name, value in details.items():
        writer.writerow([_disarm(name), _disarm(value)])
    writer.writerow([])
    return buffer.getvalue()


def render_full_csv(export: FullExport) -> str:
    """Return the full download in comma-separated value form.

    Why:
        The header block proves which two captures the rows came from. The
        rows follow through the same writer as the differences file, so every
        cell keeps the formula guard.

    Args:
        export: The parts of the full download.

    Returns:
        The whole file as text.
    """
    return _render_detail_block(build_details(export)) + render_csv(export.rows)


def render_full_json(export: FullExport) -> str:
    """Return the full download in JSON form.

    Why:
        Another program reads this file. Three named parts let that program
        read the statistics without counting the rows itself. The rows keep the
        same seven column names as the comma-separated file.

    Args:
        export: The parts of the full download.

    Returns:
        The whole file as text.
    """
    document = {
        SUMMARY_KEY: dict(export.summary),
        STATISTICS_KEY: dict(export.statistics),
        ROWS_KEY: [row.to_dict() for row in export.rows],
    }
    return json.dumps(document, indent=_JSON_INDENT)


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


def _chosen_scope(scope: object) -> str:
    """Return one requested scope name in its stored spelling.

    Why:
        The scope arrives in the address bar, so it may hold spaces or capital
        letters. An empty value means that the caller named no scope, which is
        the differences scope. A value of another type names no known scope,
        so it reaches the refusal.

    Args:
        scope: The raw scope value.

    Returns:
        The trimmed lower case name, or ``unknown``.
    """
    if not isinstance(scope, str):
        return _UNKNOWN_SCOPE
    trimmed = scope.strip().lower()
    return trimmed or SCOPE_DIFFERENCES


def export_comparison(
    devices: device_compare.DeviceComparison,
    clients: client_compare.ClientComparison,
    export_format: object,
    scope: object = SCOPE_DIFFERENCES,
    context: ExportContext | None = None,
) -> ExportResult:
    """Return the download of one comparison in the requested format and scope.

    Why:
        The route asks for one file and gets either the file or the refusal
        in the same record. The refusal names ``bad_format`` or ``bad_scope``,
        which the route returns with status 400.

        The format check runs first, so a request that names two faults
        reports the format fault alone. An operator then reads one cause.

    Args:
        devices: The device half of the comparison.
        clients: The client half of the comparison.
        export_format: ``csv`` or ``json``.
        scope: ``differences`` or ``full``. An empty value means the default.
        context: The two captures and the statistics, for the full scope.

    Returns:
        The file and its media type, or the refusal.
    """
    chosen_format = _chosen_format(export_format)
    if chosen_format not in SUPPORTED_FORMATS:
        # WHY: The raw value never reaches the log. It arrives from the
        # address bar and could carry a line break that fakes a log line.
        logger.warning("Upgrade portal refused a comparison download, because the format is not known")
        return ExportResult(error=ERROR_BAD_FORMAT)
    chosen_scope = _chosen_scope(scope)
    if chosen_scope not in SUPPORTED_SCOPES:
        # WHY: The scope arrives in the address bar as well, so the log names
        # the fault and never the value.
        logger.warning("Upgrade portal refused a comparison download, because the scope is not known")
        return ExportResult(error=ERROR_BAD_SCOPE)
    if chosen_scope == SCOPE_FULL:
        return _full_result(devices, clients, chosen_format, context)
    return _differences_result(devices, clients, chosen_format)


def _differences_result(
    devices: device_compare.DeviceComparison,
    clients: client_compare.ClientComparison,
    export_format: str,
) -> ExportResult:
    """Return the file that holds the differences alone.

    Why:
        This file keeps its old shape. An operator who saved a link before the
        full scope arrived still gets the same bytes.

    Args:
        devices: The device half of the comparison.
        clients: The client half of the comparison.
        export_format: ``csv`` or ``json``.

    Returns:
        The file and its media type.
    """
    rows = build_rows(devices, clients)
    if export_format == FORMAT_CSV:
        return ExportResult(body=render_csv(rows), media_type=MEDIA_TYPE_CSV, filename=FILENAME_CSV)
    return ExportResult(body=render_json(rows), media_type=MEDIA_TYPE_JSON, filename=FILENAME_JSON)


def _full_result(
    devices: device_compare.DeviceComparison,
    clients: client_compare.ClientComparison,
    export_format: str,
    context: ExportContext | None,
) -> ExportResult:
    """Return the file that holds every row and the statistics.

    Why:
        The full file carries its own name. An operator can then keep both
        files in one folder, because neither file overwrites the other.

    Args:
        devices: The device half of the comparison.
        clients: The client half of the comparison.
        export_format: ``csv`` or ``json``.
        context: The two captures and the statistics.

    Returns:
        The file and its media type.
    """
    export = build_full_export(devices, clients, context)
    if export_format == FORMAT_CSV:
        return ExportResult(body=render_full_csv(export), media_type=MEDIA_TYPE_CSV, filename=FILENAME_FULL_CSV)
    return ExportResult(body=render_full_json(export), media_type=MEDIA_TYPE_JSON, filename=FILENAME_FULL_JSON)


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
    "AFTER_PREFIX",
    "BEFORE_PREFIX",
    "CLIENT_MOVE_FIELD",
    "CREDENTIAL_WORDS",
    "ERROR_BAD_FORMAT",
    "ERROR_BAD_SCOPE",
    "EXPORT_COLUMNS",
    "FILENAME_CSV",
    "FILENAME_FULL_CSV",
    "FILENAME_FULL_JSON",
    "FILENAME_JSON",
    "FORMAT_CSV",
    "FORMAT_JSON",
    "KIND_CLIENT",
    "KIND_DEVICE",
    "MEDIA_TYPE_CSV",
    "MEDIA_TYPE_JSON",
    "ORGANIZATION_DETAIL",
    "ROWS_KEY",
    "SCOPE_DIFFERENCES",
    "SCOPE_FULL",
    "SITE_DETAIL",
    "SITE_ID_DETAIL",
    "SKIPPED_DETAIL",
    "STATISTICS_KEY",
    "SUMMARY_COLUMNS",
    "SUMMARY_KEY",
    "SUPPORTED_FORMATS",
    "SUPPORTED_SCOPES",
    "ExportContext",
    "ExportResult",
    "ExportRow",
    "FullExport",
    "RowChange",
    "build_details",
    "build_full_export",
    "build_full_rows",
    "build_rows",
    "build_summary",
    "column_names",
    "export_comparison",
    "is_credential_field",
    "render_csv",
    "render_full_csv",
    "render_full_json",
    "render_json",
    "safe_statistics",
]
