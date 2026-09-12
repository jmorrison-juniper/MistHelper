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

import json  # Structured Tier 3 values stay valid JSON inside one table cell.
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
GUEST_GROUP = "guest"  # The key of the guest client list in the stored document.
GUEST_COLUMNS = ("hostname", "mac", "username", "parent_device", "ssid", "random_mac")  # Guest identity and attachment.

# Each Tier 3 section has preferred columns. A new safe field appends after them.
EXTRA_TABLE_SPECS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("switch_ports", "Switch ports", ("mac", "port_id", "up", "speed", "full_duplex", "port_usage", "mac_count")),
    (
        "poe",
        "Power over Ethernet",
        ("mac", "port_id", "poe_on", "poe_disabled", "poe_mode", "poe_priority", "power_draw"),
    ),
    ("radios", "Radios", ("mac", "band", "channel", "bandwidth", "power", "noise_floor", "num_clients", "num_wlans")),
    ("tunnels", "Gateway tunnels", ("mac", "tunnel_name", "type", "protocol", "status")),
    ("bgp_peers", "BGP peers", ("mac", "neighbor_mac", "neighbor_ip", "vrf_name", "state", "up")),
    ("alarms", "Alarms", ("id", "severity", "type", "group", "timestamp", "last_seen", "count")),
)

# The two client columns whose column name and source field name differ.
# `data-model.md` section 3.4 names the source fields.
PARENT_SOURCE = "device_name"  # The name of the switch or the access point that holds the client.

_LINE_BREAKS = ("\r\n", "\n", "\r")  # A value that held one of these would break the table layout.

# The largest count of rows that one table of the capture page paints. A capture
# of a large site holds thousands of client rows, and a page that painted every
# one would render slowly and sort slowly. Issue #2075 asks for the cap. The
# whole document still reaches the operator through the download control, so the
# cap hides no record from the evidence.
TABLE_ROW_CAP = 500


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


def safe_value(value: Any) -> Any:
    """Return one value with credential fields removed from nested maps."""
    if isinstance(value, Mapping):  # A nested cloud object can hold a credential field.
        return {  # Keep every safe field for the operator.
            str(name): safe_value(item)  # Apply the same rule at every map depth.
            for name, item in value.items()  # Read each stored field once.
            if not is_credential_field(str(name))  # Remove credentials before the template sees them.
        }
    if isinstance(value, list | tuple):  # A list can hold nested cloud objects.
        return [safe_value(item) for item in value]  # Preserve the source order.
    return value  # A scalar has no field name to inspect.


def readable(record: Mapping[str, Any]) -> dict[str, Any]:
    """Return one captured record with every credential field removed."""
    safe = safe_value(record)  # Remove credentials before the page builds columns.
    return dict(safe) if isinstance(safe, Mapping) else {}  # The caller always receives a map.


def display_text(value: Any) -> str:
    """Return a readable cell value for a scalar or a structured value."""
    if isinstance(value, Mapping | list | tuple):  # Keep a nested cloud value valid and unambiguous.
        return json.dumps(safe_value(value), sort_keys=True, separators=(",", ":"), default=str)  # Compact JSON.
    return cell_text(value)  # Use the existing one-line rule for scalar values.


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


def _section_records(capture: Mapping[str, Any], section: str) -> list[Mapping[str, Any]]:
    """Return the stored records of one Tier 3 section."""
    extras: Any = capture.get("extras") or {}  # A Tier 2 capture holds no extra map.
    if not isinstance(extras, Mapping):  # A damaged extra section must not stop the page.
        logger.warning("capture tables: the extra section is not a map, so %s stays empty", section)
        return []  # The page still shows the explicit empty state.
    records: Any = extras.get(section) or []  # A successful empty read contains no row.
    return [record for record in records if isinstance(record, Mapping)]  # Drop a stray non-record value.


def _section_columns(records: list[Mapping[str, Any]], preferred: tuple[str, ...]) -> list[str]:
    """Return preferred columns followed by new safe source columns."""
    found = {str(name) for record in records for name in readable(record)}  # Find every safe stored field.
    ordered = [name for name in preferred if name in found or not records]  # Keep stable headings for empty data.
    ordered.extend(sorted(found.difference(ordered)))  # Append future fields without hiding them.
    return ordered  # The template uses this same order for the heading and each row.


def _section_view(capture: Mapping[str, Any], section: str, label: str, preferred: tuple[str, ...]) -> dict[str, Any]:
    """Return one bounded Tier 3 table description."""
    logger.info("capture tables: build the %s rows", section)  # Log before the page transformation.
    records = _section_records(capture, section)  # Read every stored record of the section.
    columns = _section_columns(records, preferred)  # Preserve stable fields and append future fields.
    rows = [{name: display_text(readable(record).get(name)) for name in columns} for record in records]  # Text cells.
    visible, held = capped(rows, section.replace("_", " "))  # Apply the same bound as the base tables.
    logger.debug("capture tables: built %s visible %s rows from %s stored rows", len(visible), section, held)
    return {"key": section.replace("_", "-"), "label": label, "columns": columns, "rows": visible, "held": held}


def _guest_view(capture: Mapping[str, Any]) -> dict[str, Any]:
    """Return the bounded guest-client table description."""
    logger.info("capture tables: build the guest client rows")  # Log before the page transformation.
    records = _client_records(capture, GUEST_GROUP)  # Read the guest group through the existing client rule.
    columns = list(GUEST_COLUMNS)  # The stable fields keep an empty guest table readable.
    rows = [_client_row(GUEST_COLUMNS, record) for record in records]  # Reuse the client name and parent mapping.
    visible, held = capped(rows, "guest client")  # Apply the same bound as the other client tables.
    logger.debug("capture tables: built %s visible guest client rows from %s stored rows", len(visible), held)
    return {"key": "clients-guest", "label": "Guest clients", "columns": columns, "rows": visible, "held": held}


def additional_tables(capture: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return the guest table and each requested Tier 3 table."""
    tables = [_guest_view(capture)]  # Guest clients belong to both data tiers.
    if int(capture.get("tier") or 2) != 3:  # Tier 2 did not request any extra section.
        return tables  # The template shows one explicit Tier 2 note after the guest table.
    tables.extend(_section_view(capture, key, label, columns) for key, label, columns in EXTRA_TABLE_SPECS)
    return tables  # Tier 3 always shows all six sections, including empty ones.


def capped(rows: list[dict[str, str]], name: str) -> tuple[list[dict[str, str]], int]:
    """Return one table cut to the row cap, with the count it held before.

    Why:
        A capture of a large site holds thousands of client rows. One page that
        painted every row would take a long time to render, and the browser
        would then sort that whole table on every header press.

        Issue #2075 asks each table to carry a cap and to state what the cap
        removed. A silent cut is worse than no cut, because the operator would
        read a short table as the whole site.

    Args:
        rows: Every row that the capture holds for one table.
        name: The table name, for the log record.

    Returns:
        The rows to paint, and the count that the capture held. A count equal to
        the row count means the cap removed nothing.
    """
    held = len(rows)  # The count before the cap, which the page states.
    if held <= TABLE_ROW_CAP:  # The common site fits inside the cap.
        return rows, held
    logger.info("Upgrade portal caps the %s table at %s of %s row(s)", name, TABLE_ROW_CAP, held)
    return rows[:TABLE_ROW_CAP], held  # The page states both numbers, so no reader mistakes the cut.


def page_tables(capture: Mapping[str, Any]) -> dict[str, Any]:
    """Return the three row lists that the capture page paints.

    Why:
        The page reads one name for each table. Building all three here keeps
        the route short and keeps the column lists in one module.

        Each table also carries the count that the capture holds. A capped table
        must state what it removed, so the operator never reads a cut table as
        the whole site.

    Args:
        capture: The stored capture document, or an empty map.

    Returns:
        The device rows, the wired client rows, the wireless client rows, the
        held count of each table, and the cap itself.
    """
    devices, device_held = capped(device_table(capture), "device")  # Acceptance Scenario 1.
    wired, wired_held = capped(client_table(capture, WIRED_GROUP, WIRED_COLUMNS), "wired client")
    wireless, wireless_held = capped(client_table(capture, WIRELESS_GROUP, WIRELESS_COLUMNS), "wireless client")
    return {
        "device_rows": devices,
        "wired_rows": wired,
        "wireless_rows": wireless,
        "additional_tables": additional_tables(capture),  # Guest and Tier 3 tables use one generic template.
        "tier3_requested": int(capture.get("tier") or 2) == 3,  # The page explains why Tier 3 tables are absent.
        # The page reads each held count beside its table, so a capped table
        # states both numbers and an uncapped table states nothing at all.
        "device_rows_held": device_held,
        "wired_rows_held": wired_held,
        "wireless_rows_held": wireless_held,
        "table_row_cap": TABLE_ROW_CAP,
    }


__all__ = [
    "DEVICE_COLUMNS",
    "TABLE_ROW_CAP",
    "WIRED_COLUMNS",
    "WIRELESS_COLUMNS",
    "capped",
    "cell_text",
    "client_table",
    "device_table",
    "page_tables",
    "readable",
]
