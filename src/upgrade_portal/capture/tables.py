"""The rows that the capture page paints as tables.

Why:
    FR-026 requires that the portal shows a completed capture as tables. The
    page held the counts alone before this module, so an operator read that a
    site holds eight devices and could not read which eight. User Story 1 names
    the fields of each table, and this module builds exactly those fields.

    The page and the download read the same capture, so both must agree. This
    module therefore reads the device list through `export.device_entries`, and
    it drops a credential field through `export.is_credential_field`. Neither
    rule lives twice.

Row shape:
    Each builder answers a list of plain dictionaries. A dictionary reads well
    in a template, and it holds no method that a template could call by
    accident. Every value is text, so the template needs no filter and an
    absent value paints as an empty cell.
"""

from __future__ import annotations  # Every annotation stays text, so a name may appear before its class.

import logging  # The portal logs with the standard library only.
from collections.abc import Mapping  # Types each read-only record that arrives from the store.
from typing import Any  # A stored capture document is free-form.

from .export import device_entries, is_credential_field  # The two rules that the download owns as well.

logger = logging.getLogger(__name__)  # One logger for each module keeps the source visible in the log.

# The columns of the device table. User Story 1 names the version, the status,
# the uptime, the model, and the serial number. The name, the address, and the
# chassis fields sit beside them, because an operator finds a device by name and
# must tell one chassis member from another.
DEVICE_COLUMNS = (
    "name",
    "mac",
    "type",
    "model",
    "serial",
    "version",
    "status",
    "uptime",
    "vc_role",
    "num_members",
    "ip",
)

# The columns of the wired client table identify the client and its attachment.
# The manufacturer helps an operator identify unmanaged equipment. The VLAN
# number does not identify the client and therefore stays out of this table.
WIRED_COLUMNS = ("hostname", "mac", "ip", "manufacture", "parent_device", "port_id")

# The columns of the wireless client table. The same five fields of the story,
# and then the network name and the band. A wireless client has no port.
WIRELESS_COLUMNS = ("hostname", "mac", "ip", "vlan", "parent_device", "ssid", "band")

WIRED_GROUP = "wired"  # The key of the wired client list in the stored document.
WIRELESS_GROUP = "wireless"  # The key of the wireless client list in the stored document.

# The two client columns whose column name and source field name differ.
# `data-model.md` section 3.4 names the source fields.
PARENT_SOURCE = "device_name"  # The name of the switch or the access point that holds the client.

_LINE_BREAKS = ("\r\n", "\n", "\r")  # A value that held one of these would break the table layout.


def cell_text(value: Any) -> str:
    """Return one captured value as one line of text.

    Why:
        A template paints text. A null value would paint as the word `None`,
        which an operator would read as a firmware version. A line break inside
        a cell would push the rest of the row out of its column.

    Args:
        value: The captured value.

    Returns:
        The value as text on one line, or an empty string.
    """
    if value is None:  # The cloud sends a null value for a field it never read.
        return ""  # An empty cell reads better than the word None.
    text = str(value)  # A number, a flag, and a word all paint the same way.
    for marker in _LINE_BREAKS:  # The cloud may send any of the three forms.
        text = text.replace(marker, " ")  # A space keeps the words apart.
    return text.strip()  # A leading space or a trailing space carries no meaning.


def readable(record: Mapping[str, Any]) -> dict[str, Any]:
    """Return one captured record with every credential field removed.

    Why:
        A page is a file that a browser caches and that an operator screenshots.
        A token must never reach it. `export.is_credential_field` owns the rule,
        so the page and the download drop the same fields.

    Args:
        record: One captured record.

    Returns:
        The record, without any field whose name reads as a secret.
    """
    return {name: value for name, value in record.items() if not is_credential_field(str(name))}


def _row(columns: tuple[str, ...], source: Mapping[str, Any]) -> dict[str, str]:
    """Return one table row over a fixed column list.

    Args:
        columns: The column names of the table.
        source: The record that holds the values.

    Returns:
        One value for each column, as text.
    """
    return {name: cell_text(source.get(name)) for name in columns}  # A column the record misses paints empty.


def device_table(capture: Mapping[str, Any]) -> list[dict[str, str]]:
    """Return one row for every device of one capture.

    Why:
        Acceptance Scenario 1 requires a table of switches with the firmware
        version, the status, the uptime, the model, and the serial number.
        `data-model.md` section 3.3 holds those three state fields in the device
        index alone, so the row reads the index and not the raw device list.

        Every chassis member holds its own index entry, so a stack that loses a
        member shows the loss as a missing row.

    Args:
        capture: The stored capture document.

    Returns:
        One row for each device, in the order the capture stored them.
    """
    logger.info("capture tables: build the device rows of the capture %s", cell_text(capture.get("capture_id")))
    rows: list[dict[str, str]] = []  # A capture that read no device answers an empty list, and no error.
    for mac, entry in device_entries(capture):  # The index key names the member, so each member holds a row.
        row = _row(DEVICE_COLUMNS, readable(entry))  # No credential field reaches a cell.
        row["mac"] = cell_text(mac)  # The index key wins, because an entry may hold no address field.
        rows.append(row)  # The order of the index is the order of the table.
    logger.debug("capture tables: built %s device rows", len(rows))  # The count proves that no member was dropped.
    return rows


def _client_row(columns: tuple[str, ...], record: Mapping[str, Any]) -> dict[str, str]:
    """Return one client row.

    Args:
        columns: The column names of that table.
        record: One stored client record.

    Returns:
        One value for each column, as text.
    """
    source = readable(record)  # No credential field reaches a cell.
    row = _row(columns, source)  # Every column of the table, in order.
    row["hostname"] = client_hostname(source)  # Old wired captures can hold the name in either field.
    row["parent_device"] = cell_text(source.get(PARENT_SOURCE))  # The column name differs from the source name.
    return row


def client_hostname(source: Mapping[str, Any]) -> str:
    """Return the usable host name from one client record.

    Why:
        Current and older wired-client responses use different host name fields.
        Some current responses put one name in a list. The table needs one
        readable value and must not show a Python list representation.

    Args:
        source: One credential-free client record.

    Returns:
        The host name, or an empty string when neither source names the client.
    """
    for field in ("hostname", "last_hostname"):  # Prefer the current field before the older fallback.
        value = source.get(field)  # A source can omit either field.
        if isinstance(value, (list, tuple)):  # Mist can return one or more observed names.
            value = next((item for item in value if cell_text(item)), None)  # Use the first usable observed name.
        name = cell_text(value)  # All field shapes become one display value.
        if name:  # An empty value must not hide the fallback field.
            return name  # The first usable field identifies the client.
    return ""  # The template shows its existing unnamed-client text.


def client_table(capture: Mapping[str, Any], group: str, columns: tuple[str, ...]) -> list[dict[str, str]]:
    """Return one row for every client of one group of one capture.

    Why:
        Acceptance Scenario 2 requires every wired client and every wireless
        client. Each row names the address, the host name, the VLAN, and the
        parent device. One builder covers both groups, because the two tables
        differ by their column list alone.

    Args:
        capture: The stored capture document.
        group: `wired` or `wireless`.
        columns: The column names of that table.

    Returns:
        One row for each client of that group.
    """
    logger.info("capture tables: build the %s client rows", group)  # The group name reads in the log.
    rows = [_client_row(columns, record) for record in _client_records(capture, group)]  # One pass over the group.
    logger.debug("capture tables: built %s %s client rows", len(rows), group)  # The count proves the whole group.
    return rows


def _client_records(capture: Mapping[str, Any], group: str) -> list[Mapping[str, Any]]:
    """Return the stored client records of one group.

    Args:
        capture: The stored capture document.
        group: `wired` or `wireless`.

    Returns:
        The records of that group, or an empty list.
    """
    groups: Any = capture.get("clients") or {}  # A capture that read no client holds an empty map.
    if not isinstance(groups, Mapping):  # A document of a later release may hold another shape.
        logger.warning("capture tables: the client section is not a map, so the %s table stays empty", group)
        return []  # An empty table is a valid answer, and never an error.
    records: Any = groups.get(group) or []  # A group the capture did not read holds no record.
    return [record for record in records if isinstance(record, Mapping)]  # A stray value never reaches a row.


def page_tables(capture: Mapping[str, Any]) -> dict[str, list[dict[str, str]]]:
    """Return the three row lists that the capture page paints.

    Why:
        The page reads one name for each table. Building all three here keeps
        the route short and keeps the column lists in one module.

    Args:
        capture: The stored capture document, or an empty map.

    Returns:
        The device rows, the wired client rows, and the wireless client rows.
    """
    return {
        "device_rows": device_table(capture),  # Acceptance Scenario 1.
        "wired_rows": client_table(capture, WIRED_GROUP, WIRED_COLUMNS),  # Acceptance Scenario 2, first half.
        "wireless_rows": client_table(capture, WIRELESS_GROUP, WIRELESS_COLUMNS),  # The second half.
    }


__all__ = [
    "DEVICE_COLUMNS",
    "WIRED_COLUMNS",
    "WIRELESS_COLUMNS",
    "cell_text",
    "client_table",
    "device_table",
    "page_tables",
    "readable",
]
