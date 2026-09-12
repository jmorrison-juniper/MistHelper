"""The view models of one comparison.

Why:
    A template must never hold a rule. The route lane builds the comparison,
    passes it here, and hands the result to the template. The page then shows
    what this module decided and nothing else.

    The view carries four sections. The header names the two captures and any
    section that the digests skipped. The device section and the client
    section hold the rows. The statistics section holds one labeled number
    for each name of the contract, with the test identifier already built.

    The outcome filter lives here as well, so the interface can show one
    outcome at a time without a second read of the captures.

    The history view sits in the same module for the same reason. The history
    page shows one row for each stored capture, and every label, link, and test
    identifier of that row comes from here.
"""

from __future__ import annotations

import logging
import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlencode

from src.upgrade_portal.compare import clients as client_compare
from src.upgrade_portal.compare import diff as device_compare
from src.upgrade_portal.compare import statistics as statistics_module

logger = logging.getLogger(__name__)

# WHY: The filter needs a value that means no filter. The word sits beside the
# four outcomes in the same query field, so it must never be an outcome name.
FILTER_ALL = "all"

DEVICE_FILTERS = (FILTER_ALL, *device_compare.DEVICE_OUTCOMES)
CLIENT_FILTERS = (FILTER_ALL, *client_compare.CLIENT_OUTCOMES)

CAPTURE_ID_KEY = "capture_id"
STARTED_AT_KEY = "started_at"
ROLE_KEY = "role"
CAPTURE_STATUS_KEY = "capture_status"
SITE_NAME_KEY = "site_name"
ORG_NAME_KEY = "org_name"

# The test identifier prefixes of contracts/ui-testids.md lines 149 to 154.
STAT_TEST_ID_PREFIX = "compare-stat-"
FILTER_TEST_ID_PREFIX = "compare-filter-"
DEVICE_ROW_TEST_ID_PREFIX = "compare-device-row-"
CLIENT_ROW_TEST_ID_PREFIX = "compare-client-row-"

# The test identifiers of contracts/ui-testids.md lines 162 to 166. The page
# holds the three fixed values, and the two prefixes build a row value.
HISTORY_TABLE_TEST_ID = "history-table"
HISTORY_ROW_TEST_ID_PREFIX = "history-row-"
HISTORY_OPEN_TEST_ID_PREFIX = "history-open-"
HISTORY_NEXT_TEST_ID = "history-page-next"
HISTORY_PREVIOUS_TEST_ID = "history-page-previous"

# WHY: contracts/http-api.md line 364 fixes the history page path, and line 178
# fixes the capture page path. A link that a view model builds must follow the
# contract, because no blueprint endpoint name is fixed.
HISTORY_PAGE_PATH = "/history"
CAPTURE_PAGE_PATH = "/captures/"

# WHY: contracts/http-api.md line 357 sets the default page size to 25. The same
# number lives in the store as DEFAULT_LIST_LIMIT, and both must agree.
DEFAULT_HISTORY_PAGE_SIZE = 25

# WHY: A capture row may name its counts directly, or it may carry the whole
# capture document with a counts map. The reader tries the direct name first.
_COUNTS_KEY = "counts"
_DEVICE_COUNT_KEY = "device_count"
_CLIENT_COUNT_KEY = "client_count"
_STORED_SIZE_KEY = "stored_size_bytes"
_DEVICES_TOTAL_KEY = "devices_total"
_CLIENT_COUNT_KEYS = ("clients_wired", "clients_wireless", "clients_guest")

# WHY: The size text uses decimal units with a step of 1000, not binary units
# with a step of 1024. A storage report and an operating system both show
# decimal units, so a decimal step keeps the portal and the disk in step.
_SIZE_UNITS = ("B", "kB", "MB", "GB", "TB")
_SIZE_STEP = 1000

_STATISTIC_LABELS = {
    "devices_unchanged": "Devices unchanged",
    "devices_changed": "Devices changed",
    "devices_added": "Devices added",
    "devices_removed": "Devices removed",
    "devices_version_changed": "Devices with a new version",
    "clients_present": "Clients present",
    "clients_moved": "Clients moved",
    "clients_added": "Clients added",
    "clients_missing": "Clients missing",
    "client_return_rate": "Client return rate",
    "elapsed_seconds": "Elapsed seconds",
}


# ---------------------------------------------------------------------------
# The test identifiers
# ---------------------------------------------------------------------------


def stat_test_id(name: str) -> str:
    """Return the test identifier of one statistic.

    Why:
        The browser test drives ``compare-stat-clients-moved`` while the
        contract names the value ``clients_moved``. Building the identifier
        here keeps the two spellings in step.

    Args:
        name: One flat statistic name.

    Returns:
        The test identifier of that statistic.
    """
    return STAT_TEST_ID_PREFIX + name.replace("_", "-")


def filter_test_id(outcome: str) -> str:
    """Return the test identifier of one outcome filter.

    Why:
        The browser test drives ``compare-filter-missing``. One builder keeps
        the page and the test on the same name.

    Args:
        outcome: One outcome name, or ``all``.

    Returns:
        The test identifier of that filter control.
    """
    return FILTER_TEST_ID_PREFIX + outcome.replace("_", "-")


def device_row_test_id(mac: str) -> str:
    """Return the test identifier of one device row.

    Why:
        The browser test finds a device row by address. The address is already
        lower case with no separator, so it needs no further change.

    Args:
        mac: The device address.

    Returns:
        The test identifier of that row.
    """
    return DEVICE_ROW_TEST_ID_PREFIX + mac


def client_row_test_id(mac: str) -> str:
    """Return the test identifier of one client row.

    Why:
        The browser test finds a client row by address, the same way it finds
        a device row.

    Args:
        mac: The client address.

    Returns:
        The test identifier of that row.
    """
    return CLIENT_ROW_TEST_ID_PREFIX + mac


def history_row_test_id(capture_id: str) -> str:
    """Return the test identifier of one history row.

    Why:
        contracts/ui-testids.md line 163 fixes ``history-row-{capture_id}``.
        The capture identifier is already lower case with hyphens, so the
        builder joins the prefix and the key and changes nothing else.

    Args:
        capture_id: The stable identifier of one stored capture.

    Returns:
        The test identifier of that row.
    """
    return HISTORY_ROW_TEST_ID_PREFIX + capture_id


def history_open_test_id(capture_id: str) -> str:
    """Return the test identifier of the open control in one history row.

    Why:
        contracts/ui-testids.md line 164 fixes ``history-open-{capture_id}``.
        The row and the open control carry the same key. A test that found
        a row can then reach the control of that row without a second lookup.

    Args:
        capture_id: The stable identifier of one stored capture.

    Returns:
        The test identifier of the open control.
    """
    return HISTORY_OPEN_TEST_ID_PREFIX + capture_id


# ---------------------------------------------------------------------------
# The header
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CaptureSummary:
    """One capture as the header shows it.

    Why:
        The operator must be able to prove which two records the page
        compared. The identifier and the moment answer that, and the role and
        the state warn about a partial record.

    Attributes:
        capture_id: The stable identifier of the capture.
        started_at: The moment the capture started.
        role: ``pre`` or ``post``.
        capture_status: The stored state of the capture.
    """

    capture_id: str = ""
    started_at: str = ""
    role: str = ""
    capture_status: str = ""

    def to_dict(self) -> dict[str, str]:
        """Return the two values that the comparison body carries.

        Why:
            The body of ``GET /api/comparisons`` names ``capture_id`` and
            ``started_at`` alone. The page reads the role and the state from
            the record itself, so the body stays as the contract states it.

        Returns:
            A dictionary with ``capture_id`` and ``started_at``.
        """
        return {"capture_id": self.capture_id, "started_at": self.started_at}


@dataclass(frozen=True, slots=True)
class ComparisonHeader:
    """The header of one comparison.

    Why:
        The skipped section list belongs at the top of the page. A reader who
        sees an empty device table must learn at once that the digests proved
        the section equal.

    Attributes:
        before: The pre-check capture.
        after: The post-check capture.
        site_name: The site that both captures name.
        org_name: The organization that both captures name.
        skipped_sections: Each section whose digest matched.
    """

    before: CaptureSummary = field(default_factory=CaptureSummary)
    after: CaptureSummary = field(default_factory=CaptureSummary)
    site_name: str = ""
    org_name: str = ""
    skipped_sections: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Return the header as a plain dictionary.

        Why:
            The route lane merges these keys into the comparison body, and
            the template reads the same names.

        Returns:
            A dictionary with both captures, both names, and the skipped
            section list.
        """
        return {
            "before": self.before.to_dict(),
            "after": self.after.to_dict(),
            "site_name": self.site_name,
            "org_name": self.org_name,
            "skipped_sections": list(self.skipped_sections),
        }


def _text_field(capture: Mapping[str, Any], name: str) -> str:
    """Return one text field of one capture document.

    Why:
        A partial capture drops a field, and the header must still render. A
        reader that returns an empty string keeps the type tests out of the
        header builder.

    Args:
        capture: One capture document.
        name: The field name.

    Returns:
        The field value as text, or an empty string.
    """
    value = capture.get(name)
    return value if isinstance(value, str) else ""


def build_capture_summary(capture: Mapping[str, Any]) -> CaptureSummary:
    """Return the header record of one capture.

    Why:
        The header reads four fields of a large document. Pulling them here
        keeps the template free of document keys.

    Args:
        capture: One capture document.

    Returns:
        The header record of that capture.
    """
    return CaptureSummary(
        capture_id=_text_field(capture, CAPTURE_ID_KEY),
        started_at=_text_field(capture, STARTED_AT_KEY),
        role=_text_field(capture, ROLE_KEY),
        capture_status=_text_field(capture, CAPTURE_STATUS_KEY),
    )


def build_header(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    skipped_sections: Iterable[str] = (),
) -> ComparisonHeader:
    """Return the header of one comparison.

    Why:
        The site name comes from the post-check capture first, because that
        record is the later truth. The pre-check capture answers when a
        partial post-check dropped the name.

    Args:
        before: The pre-check capture.
        after: The post-check capture.
        skipped_sections: Each section whose digest matched.

    Returns:
        The header record.
    """
    return ComparisonHeader(
        before=build_capture_summary(before),
        after=build_capture_summary(after),
        site_name=_text_field(after, SITE_NAME_KEY) or _text_field(before, SITE_NAME_KEY),
        org_name=_text_field(after, ORG_NAME_KEY) or _text_field(before, ORG_NAME_KEY),
        skipped_sections=tuple(skipped_sections),
    )


# ---------------------------------------------------------------------------
# The outcome filter
# ---------------------------------------------------------------------------


def normalize_filter(outcome: object, allowed: Sequence[str]) -> str:
    """Return one filter value that the page can use.

    Why:
        The filter arrives in the address bar, so any text can reach it. An
        unknown value shows every row rather than an empty table, because an
        empty table would read as a site with no devices.

    Args:
        outcome: The raw filter value.
        allowed: The filter values of this table.

    Returns:
        The matching filter value, or ``all``.
    """
    if isinstance(outcome, str) and outcome in allowed:
        return outcome
    if outcome not in (None, "", FILTER_ALL):
        logger.warning("Upgrade portal ignored an unknown comparison filter value")
    return FILTER_ALL


def filter_devices(
    deltas: Iterable[device_compare.DeviceDelta],
    outcome: str,
) -> tuple[device_compare.DeviceDelta, ...]:
    """Return the device rows of one outcome.

    Why:
        A site with 200 devices and 8 changes hides the 8 changes in the
        table. The filter lets the operator read one outcome at a time.

    Args:
        deltas: The device difference records.
        outcome: One device outcome, or ``all``.

    Returns:
        The matching rows, in their original order.
    """
    chosen = normalize_filter(outcome, DEVICE_FILTERS)
    if chosen == FILTER_ALL:
        return tuple(deltas)
    return tuple(delta for delta in deltas if delta.outcome == chosen)


def filter_clients(
    deltas: Iterable[client_compare.ClientDelta],
    outcome: str,
) -> tuple[client_compare.ClientDelta, ...]:
    """Return the client rows of one outcome.

    Why:
        The operator opens a comparison to read the missing clients. The
        filter takes that list to the top of the page in one click.

    Args:
        deltas: The client difference records.
        outcome: One client outcome, or ``all``.

    Returns:
        The matching rows, in their original order.
    """
    chosen = normalize_filter(outcome, CLIENT_FILTERS)
    if chosen == FILTER_ALL:
        return tuple(deltas)
    return tuple(delta for delta in deltas if delta.outcome == chosen)


# ---------------------------------------------------------------------------
# The table sections
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DeviceSection:
    """The device table of one comparison.

    Why:
        The row count before the filter belongs beside the rows. Without it a
        reader cannot tell a filter that matched nothing from a comparison
        that found nothing.

    Attributes:
        rows: The device rows after the filter.
        outcome: The filter in force.
        total: The row count before the filter.
        skipped: True when the digests proved the section equal.
    """

    rows: tuple[device_compare.DeviceDelta, ...] = ()
    outcome: str = FILTER_ALL
    total: int = 0
    skipped: bool = False


@dataclass(frozen=True, slots=True)
class ClientSection:
    """The client table of one comparison.

    Why:
        The client table needs the same three facts as the device table. A
        skipped client section is common, because a quiet site changes no
        wired client at all.

    Attributes:
        rows: The client rows after the filter.
        outcome: The filter in force.
        total: The row count before the filter.
        skipped: True when every client digest matched.
    """

    rows: tuple[client_compare.ClientDelta, ...] = ()
    outcome: str = FILTER_ALL
    total: int = 0
    skipped: bool = False


@dataclass(frozen=True, slots=True)
class StatisticView:
    """One number of the statistics section.

    Why:
        The template must not build a label or a test identifier, because a
        template that builds a name drifts from the browser test. The record
        carries both, ready to print.

    Attributes:
        name: The flat contract name.
        label: The words that the page shows.
        value: The number itself.
        test_id: The test identifier of this number.
    """

    name: str
    label: str
    value: Any
    test_id: str


@dataclass(frozen=True, slots=True)
class StatisticsSection:
    """The statistics region of one comparison.

    Why:
        The region prints in the order of the contract, so the same number
        sits in the same place on every page.

    Attributes:
        values: One record for each name of the contract, in report order.
    """

    values: tuple[StatisticView, ...] = ()


def build_device_section(
    comparison: device_compare.DeviceComparison,
    outcome: str = FILTER_ALL,
) -> DeviceSection:
    """Return the device table of one comparison.

    Why:
        The section reports the skip as a fact of its own. An empty table
        after a digest skip is not a table with no differences.

    Args:
        comparison: The device half of the comparison.
        outcome: The filter to apply.

    Returns:
        The device table record.
    """
    chosen = normalize_filter(outcome, DEVICE_FILTERS)
    rows = filter_devices(comparison.deltas, chosen)
    skipped = device_compare.SECTION_DEVICES in comparison.skipped_sections
    return DeviceSection(rows=rows, outcome=chosen, total=len(comparison.deltas), skipped=skipped)


def build_client_section(
    comparison: client_compare.ClientComparison,
    outcome: str = FILTER_ALL,
) -> ClientSection:
    """Return the client table of one comparison.

    Why:
        The client section holds three digests, so it counts as skipped only
        when all three matched. One matching digest still leaves work.

    Args:
        comparison: The client half of the comparison.
        outcome: The filter to apply.

    Returns:
        The client table record.
    """
    chosen = normalize_filter(outcome, CLIENT_FILTERS)
    rows = filter_clients(comparison.deltas, chosen)
    skipped = set(client_compare.CLIENT_SECTIONS) <= set(comparison.skipped_sections)
    return ClientSection(rows=rows, outcome=chosen, total=len(comparison.deltas), skipped=skipped)


def build_statistics_section(statistics: statistics_module.ComparisonStatistics) -> StatisticsSection:
    """Return the statistics region of one comparison.

    Why:
        The region walks the contract name list rather than the dictionary
        keys, so a new key never reaches the page until somebody names it.

    Args:
        statistics: The statistics roll-up.

    Returns:
        The statistics region record.
    """
    flat = statistics.to_dict()
    views = tuple(
        StatisticView(
            name=name,
            label=_STATISTIC_LABELS.get(name, name),
            value=flat.get(name, 0),
            test_id=stat_test_id(name),
        )
        for name in statistics_module.STATISTIC_NAMES
    )
    return StatisticsSection(values=views)


# ---------------------------------------------------------------------------
# The whole view
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ComparisonView:
    """Everything that the comparison page shows.

    Why:
        One record travels from the route to the template, so the template
        needs no second call and holds no rule of its own.

    Attributes:
        header: The two captures and the skipped section list.
        devices: The device table.
        clients: The client table.
        statistics: The statistics region.
    """

    header: ComparisonHeader = field(default_factory=ComparisonHeader)
    devices: DeviceSection = field(default_factory=DeviceSection)
    clients: ClientSection = field(default_factory=ClientSection)
    statistics: StatisticsSection = field(default_factory=StatisticsSection)

    def to_dict(self) -> dict[str, Any]:
        """Return the comparison body of the contract.

        Why:
            The endpoint and the page show the same comparison. Building the
            body from the view keeps the two from drifting apart.

        Returns:
            A dictionary with the header keys, the statistics, and both
            delta lists.
        """
        body = self.header.to_dict()
        body["statistics"] = {view.name: view.value for view in self.statistics.values}
        body["device_deltas"] = [row.to_dict() for row in self.devices.rows]
        body["client_deltas"] = [row.to_dict() for row in self.clients.rows]
        return body


def build_view(
    captures: tuple[Mapping[str, Any], Mapping[str, Any]],
    devices: device_compare.DeviceComparison,
    clients: client_compare.ClientComparison,
    statistics: statistics_module.ComparisonStatistics,
    outcome: str = FILTER_ALL,
) -> ComparisonView:
    """Return the whole comparison view.

    Why:
        The route lane calls one function and passes the result to the
        template. The skipped section list joins both halves here, so the
        header reports every skip once.

    Args:
        captures: The pre-check capture and the post-check capture, in order.
        devices: The device half of the comparison.
        clients: The client half of the comparison.
        statistics: The statistics roll-up.
        outcome: The filter to apply to both tables.

    Returns:
        The comparison view record.
    """
    before, after = captures
    skipped = (*devices.skipped_sections, *clients.skipped_sections)
    return ComparisonView(
        header=build_header(before, after, skipped),
        devices=build_device_section(devices, outcome),
        clients=build_client_section(clients, outcome),
        statistics=build_statistics_section(statistics),
    )


# ---------------------------------------------------------------------------
# The history view
# ---------------------------------------------------------------------------


def _whole_number(value: object) -> int:
    """Return one stored value as a whole number that is never negative.

    Why:
        A count and a size reach this module from a stored document. The
        value may be absent, a text, or a floating point number. A reader that
        answers zero for every other shape keeps the type tests out of the row
        builder. A negative size can never reach the page.

    Args:
        value: One stored value of any shape.

    Returns:
        The value as a whole number, or zero.
    """
    if isinstance(value, bool):  # A boolean is an integer in Python, and True is not a count.
        return 0
    if isinstance(value, int):  # The normal shape of a count and of a byte size.
        return max(value, 0)
    if isinstance(value, float):  # A number that arrived through JSON may be a float.
        return max(int(value), 0) if math.isfinite(value) else 0  # int() drops the fraction.
    return 0  # A text, a None, or any other shape counts as nothing.


def format_stored_size(size_bytes: object) -> str:
    """Return one stored size in a form a person reads, such as ``1.2 MB``.

    Why:
        FR-032b asks the portal to record the stored size of a capture, and the
        customer asked to see that size in a readable form. The rule is one
        rule, and the page never repeats it.

        The rule: decimal units with a step of 1000, named ``B``, ``kB``,
        ``MB``, ``GB``, and ``TB``. A size below 1000 bytes shows whole bytes
        with no decimal. Every larger size shows one decimal place, and that
        decimal is cut, never rounded up. Whole number arithmetic produces the
        decimal, so no floating point artifact can appear. The text therefore
        never states a size larger than the stored size.

    Args:
        size_bytes: The stored size in bytes.

    Returns:
        The size as text, such as ``999 B``, ``1.0 kB``, or ``1.2 MB``.
    """
    count = _whole_number(size_bytes)  # Reject every shape that is not a size.
    divisor = 1  # The byte count of the current unit. The first unit is the byte.
    unit_index = 0  # The position of the current unit in the unit names.
    while unit_index + 1 < len(_SIZE_UNITS) and count >= divisor * _SIZE_STEP:  # Stop at the last name.
        divisor *= _SIZE_STEP  # Step up one unit.
        unit_index += 1  # Move to the name of that unit.
    if unit_index == 0:  # A byte has no fraction, so a byte count shows no decimal.
        return f"{count} {_SIZE_UNITS[0]}"
    tenths = count * 10 // divisor  # Whole number division cuts the size, so it never overstates.
    return f"{tenths // 10}.{tenths % 10} {_SIZE_UNITS[unit_index]}"  # One decimal place, always.


def _int_field(row: Mapping[str, Any], name: str) -> int:
    """Return one field of one record as a whole number.

    Why:
        The row builder reads four numbers, and each one may be absent. One
        reader keeps that test in one place.

    Args:
        row: One record.
        name: The field name.

    Returns:
        The field value as a whole number, or zero.
    """
    return _whole_number(row.get(name))


def _counts_map(row: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return the counts map of one capture document.

    Why:
        The store projection of contracts/http-api.md line 361 holds no device
        count and no client count. A caller that passes a whole capture
        document instead carries those numbers under the ``counts`` key. The
        page then shows a real number for both shapes.

    Args:
        row: One history record, or one whole capture document.

    Returns:
        The counts map, or an empty map.
    """
    counts = row.get(_COUNTS_KEY)  # Present on a whole capture document only.
    return counts if isinstance(counts, Mapping) else {}  # Any other shape counts as no map.


def _device_count(row: Mapping[str, Any]) -> int:
    """Return the device count of one history record.

    Why:
        The record may name the count directly, and a whole capture document
        names it ``devices_total`` inside the counts map. The direct name wins,
        because a route that already counted the devices must not be overruled.

    Args:
        row: One history record, or one whole capture document.

    Returns:
        The device count, or zero.
    """
    direct = _int_field(row, _DEVICE_COUNT_KEY)  # The name the view model asks for.
    if direct:  # A real count answers at once.
        return direct
    return _int_field(_counts_map(row), _DEVICES_TOTAL_KEY)  # The whole document names it here.


def _client_count(row: Mapping[str, Any]) -> int:
    """Return the client count of one history record.

    Why:
        A whole capture document counts the clients in three groups, and the
        page shows one number. Adding the three here keeps the sum out of the
        page, because a template must never hold a rule.

    Args:
        row: One history record, or one whole capture document.

    Returns:
        The client count, or zero.
    """
    direct = _int_field(row, _CLIENT_COUNT_KEY)  # The name the view model asks for.
    if direct:  # A real count answers at once.
        return direct
    counts = _counts_map(row)  # The whole document splits the clients in three groups.
    return sum(_int_field(counts, name) for name in _CLIENT_COUNT_KEYS)  # Wired, wireless, and guest.


@dataclass(frozen=True, slots=True)
class HistoryRow:
    """One stored capture as the history table shows it.

    Why:
        The history page lists the stored captures of one site. Every label,
        every number, every link, and every test identifier of one row is
        settled here, so the page prints values and holds no rule.

    Attributes:
        capture_id: The stable identifier of the capture.
        started_at: The moment the capture started.
        role: ``pre`` or ``post``.
        capture_status: The stored state of the capture.
        device_count: The number of devices the capture holds.
        client_count: The number of clients the capture holds.
        stored_size_bytes: The stored size in bytes, for a sort or a test.
        stored_size_text: The same size in a form a person reads.
        row_test_id: The test identifier of the row.
        open_test_id: The test identifier of the open control.
        open_url: The path of the capture page.
    """

    capture_id: str = ""
    started_at: str = ""
    role: str = ""
    capture_status: str = ""
    device_count: int = 0
    client_count: int = 0
    stored_size_bytes: int = 0
    stored_size_text: str = "0 B"
    row_test_id: str = ""
    open_test_id: str = ""
    open_url: str = ""


@dataclass(frozen=True, slots=True)
class HistoryView:
    """The history page as the template shows it.

    Why:
        The template must do no arithmetic. The two boolean values and the two
        links answer every question the paging controls ask. The page shows
        a control or hides it and never compares a number.

    Attributes:
        rows: One record for each stored capture on this page.
        total: The number of stored captures the site holds.
        page_size: The number of rows one page holds.
        offset: The number of rows the earlier pages hold.
        has_next: True when a later page exists.
        has_previous: True when an earlier page exists.
        next_url: The path of the later page. Empty when none exists.
        previous_url: The path of the earlier page. Empty when none exists.
    """

    rows: tuple[HistoryRow, ...] = ()
    total: int = 0
    page_size: int = DEFAULT_HISTORY_PAGE_SIZE
    offset: int = 0
    has_next: bool = False
    has_previous: bool = False
    next_url: str = ""
    previous_url: str = ""


def build_history_row(row: Mapping[str, Any], capture_path: str = CAPTURE_PAGE_PATH) -> HistoryRow:
    """Return the view record of one stored capture.

    Why:
        The row builder reads the record once and settles the size text, the
        two test identifiers, and the open link together. A second reader would
        be a second chance to spell an identifier a different way.

    Args:
        row: One history record from the store.
        capture_path: The path prefix of the capture page.

    Returns:
        The view record of that capture.
    """
    capture_id = _text_field(row, CAPTURE_ID_KEY)  # The key of the row, the control, and the link.
    size_bytes = _int_field(row, _STORED_SIZE_KEY)  # FR-032b asks the portal to record this size.
    return HistoryRow(
        capture_id=capture_id,
        started_at=_text_field(row, STARTED_AT_KEY),
        role=_text_field(row, ROLE_KEY),
        capture_status=_text_field(row, CAPTURE_STATUS_KEY),
        device_count=_device_count(row),
        client_count=_client_count(row),
        stored_size_bytes=size_bytes,
        stored_size_text=format_stored_size(size_bytes),
        row_test_id=history_row_test_id(capture_id),
        open_test_id=history_open_test_id(capture_id),
        open_url=capture_path + capture_id,
    )


def _row_records(page: object) -> tuple[Mapping[str, Any], ...]:
    """Return the capture records of one history page.

    Why:
        The store answers with a page record that holds the rows under
        ``captures``, and a route may pass the rows alone. Reading both shapes
        here keeps this module free of an import of the store, which would pull
        the database driver into every page render.

    Args:
        page: A store page record, or the capture records alone.

    Returns:
        The capture records, or an empty tuple.
    """
    records = getattr(page, "captures", page)  # A page record answers. A plain list is itself.
    if not isinstance(records, Sequence) or isinstance(records, str | bytes):  # A text is not a row list.
        return ()
    return tuple(record for record in records if isinstance(record, Mapping))  # Drop every other shape.


def _number_attribute(source: object, name: str, fallback: int) -> int:
    """Return one whole number of a page record or of a page window.

    Why:
        The store page record and the window record of the route lane both name
        ``limit``, ``offset``, and ``total``. One reader serves both, and a
        third caller may pass a plain dictionary.

    Args:
        source: The page record, the window record, or a dictionary.
        name: The field name.
        fallback: The value to return when the field is absent.

    Returns:
        The field value as a whole number, or the fallback.
    """
    value = getattr(source, name, None)  # A record answers through an attribute.
    if value is None and isinstance(source, Mapping):  # A dictionary answers through a key.
        value = source.get(name)
    if isinstance(value, bool) or not isinstance(value, int):  # A boolean is never a count.
        return fallback
    return value


def _step_url(source: object, name: str, offset: int, page_size: int, path: str) -> str:
    """Return the path of one earlier or later history page.

    Why:
        The template must hold no arithmetic, so the link arrives complete. The
        route lane may already hold the link in its window record. That
        value wins, because the route owns the real path of the page.

    Args:
        source: The page record or the window record.
        name: The window field that may already hold the link.
        offset: The row offset of the wanted page.
        page_size: The number of rows one page holds.
        path: The path of the history page.

    Returns:
        The path of that page, with the query arguments.
    """
    given = getattr(source, name, "")  # The window record of the route lane may hold the link.
    if isinstance(given, str) and given:  # A real link wins over a built one.
        return given
    query = urlencode({"limit": page_size, "offset": max(offset, 0)})  # Never ask for a negative offset.
    return f"{path}?{query}"


def build_history_view(
    page: object,
    window: object = None,
    capture_path: str = CAPTURE_PAGE_PATH,
    history_path: str = HISTORY_PAGE_PATH,
) -> HistoryView:
    """Return the view model of the history page.

    Why:
        The route lane reads the store and hands the result here. This builder
        settles the paging. The template shows a control or hides it and
        never compares a number. The ``has_next`` flag is true when the rows of
        this page and the rows of the earlier pages do not reach the total.

    Args:
        page: A store page record, or the capture records alone.
        window: The paging record of the route lane. The page record answers
            when this value is absent.
        capture_path: The path prefix of the capture page.
        history_path: The path of the history page.

    Returns:
        The view model of the history page.
    """
    rows = tuple(build_history_row(record, capture_path) for record in _row_records(page))
    source = window if window is not None else page  # The window wins, because the route owns the paging.
    total = max(_number_attribute(source, "total", len(rows)), 0)  # A missing total counts the rows.
    page_size = max(_number_attribute(source, "limit", DEFAULT_HISTORY_PAGE_SIZE), 1)  # Never divide by zero.
    offset = max(_number_attribute(source, "offset", 0), 0)  # The first page starts at zero.
    seen = offset + len(rows)  # The rows of this page and of every earlier page.
    return HistoryView(
        rows=rows,
        total=total,
        page_size=page_size,
        offset=offset,
        has_next=seen < total,
        has_previous=offset > 0,
        next_url=_step_url(source, "next_href", seen, page_size, history_path) if seen < total else "",
        previous_url=_step_url(source, "previous_href", offset - page_size, page_size, history_path) if offset else "",
    )


__all__ = [
    "CAPTURE_ID_KEY",
    "CAPTURE_PAGE_PATH",
    "CAPTURE_STATUS_KEY",
    "CLIENT_FILTERS",
    "CLIENT_ROW_TEST_ID_PREFIX",
    "DEFAULT_HISTORY_PAGE_SIZE",
    "DEVICE_FILTERS",
    "DEVICE_ROW_TEST_ID_PREFIX",
    "FILTER_ALL",
    "FILTER_TEST_ID_PREFIX",
    "HISTORY_NEXT_TEST_ID",
    "HISTORY_OPEN_TEST_ID_PREFIX",
    "HISTORY_PAGE_PATH",
    "HISTORY_PREVIOUS_TEST_ID",
    "HISTORY_ROW_TEST_ID_PREFIX",
    "HISTORY_TABLE_TEST_ID",
    "ORG_NAME_KEY",
    "ROLE_KEY",
    "SITE_NAME_KEY",
    "STARTED_AT_KEY",
    "STAT_TEST_ID_PREFIX",
    "CaptureSummary",
    "ClientSection",
    "ComparisonHeader",
    "ComparisonView",
    "DeviceSection",
    "HistoryRow",
    "HistoryView",
    "StatisticView",
    "StatisticsSection",
    "build_capture_summary",
    "build_client_section",
    "build_device_section",
    "build_header",
    "build_history_row",
    "build_history_view",
    "build_statistics_section",
    "build_view",
    "client_row_test_id",
    "device_row_test_id",
    "filter_clients",
    "filter_devices",
    "filter_test_id",
    "format_stored_size",
    "history_open_test_id",
    "history_row_test_id",
    "normalize_filter",
    "stat_test_id",
]
