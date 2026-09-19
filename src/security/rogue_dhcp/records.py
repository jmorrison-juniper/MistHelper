"""One row shape for every rogue DHCP server finding, and the rules that build it.

Why:
    The scan reads three record shapes. An alarm names its switches in a list.
    A switch event names one MAC address in a scalar field. A Marvis config
    action names the port and the operation but carries no severity. A single
    table needs one column set, so this module converts all three into one
    frozen record.

Merge rule:
    Two sources often report one real event. The alarm and the switch event
    both fire when a rogue DHCP server appears on a port. The merge key groups
    those two records into one row, and the row names both sources. Without the
    merge, an operator would count one rogue server twice.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on the annotations in this module.

import hashlib  # WHY: build a short stable merge key from the grouping fields.
import logging  # WHY: report how many records the merge collapsed.
from dataclasses import dataclass, fields, replace  # WHY: declare the columns once, and rebuild a frozen row.
from datetime import UTC, datetime  # WHY: render a Mist epoch stamp as an ISO 8601 string in UTC.
from typing import Any  # WHY: a Mist record is an untyped dict that the SDK returns.

from src.security.rogue_dhcp.signals import (
    MARVIS_REMEDIATION_FAMILY,  # WHY: a Marvis repair keeps its own merge family.
    RogueDhcpSignalMatcher,  # WHY: the matcher owns the family rule, so this module never repeats it.
)

logger = logging.getLogger(__name__)  # Name the logger for this module so a reader filters by source.

SOURCE_ORG_ALARM = "org_alarm"  # WHY: name the organization alarm search as a source value.
SOURCE_SITE_ALARM = "site_alarm"  # WHY: name the site alarm search as a source value.
SOURCE_ORG_EVENT = "org_device_event"  # WHY: name the organization device event search as a source value.
SOURCE_SITE_EVENT = "site_device_event"  # WHY: name the site device event search as a source value.
SOURCE_MARVIS_ACTION = "marvis_config_action"  # WHY: name the Marvis config action search as a source value.

STATE_ACTIVE = "active"  # WHY: the source still reports the finding open.
STATE_HISTORICAL = "historical"  # WHY: the window holds the finding, but the source closed it.

# WHY: a finding whose last seen time falls inside this trailing span still counts as active.
ACTIVE_WINDOW_SECONDS = 86400

# WHY: Mist states the resolution in the alarm `status` field. A `reoccured` value means the
# fault returned, so it is absent here on purpose. Issue #2996 records the defect this closes.
RESOLVED_STATUSES = frozenset({"resolved", "closed"})

UNKNOWN_SITE_NAME = "unknown"  # WHY: a result can name a site identifier that the site list does not hold.


@dataclass(frozen=True)
class RogueDhcpFinding:
    """One rogue DHCP server finding about one switch port at one site.

    Every source produces this same shape, so one table holds an alarm, a
    switch event, and a Marvis config action together.
    """

    record_id: str  # WHY: the merge key, so a repeat run rewrites the same database row.
    org_id: str  # WHY: name the organization that the scan covered.
    site_id: str  # WHY: name the site that reported the finding.
    site_name: str  # WHY: an engineer reads a name faster than an identifier.
    device_name: str  # WHY: name the switch that saw the rogue server.
    device_mac: str  # WHY: the MAC address identifies the switch when the name is absent.
    device_model: str  # WHY: the model guides the remediation step.
    device_type: str  # WHY: record the device class, which is a switch for every rogue DHCP signal.
    port_id: str  # WHY: the port is where an engineer disconnects the rogue server.
    vlan: str  # WHY: the VLAN scopes the blast radius of the rogue server.
    source: str  # WHY: name every search that reported the finding.
    signal_type: str  # WHY: keep the literal Mist type string for an audit.
    signal_family: str  # WHY: name the canonical group, because two catalogs spell one signal two ways.
    state: str  # WHY: tell an engineer whether the finding is open now.
    severity: str  # WHY: Mist rates the finding, and the rating guides the priority.
    first_seen: str  # WHY: the first occurrence bounds how long the rogue server ran.
    last_seen: str  # WHY: the last occurrence decides the active state.
    occurrence_count: int  # WHY: a repeated finding is a standing fault, not a single packet.
    details: str  # WHY: the raw Mist text names the addresses and the interface.
    scan_started_at: str  # WHY: record when the scan ran, so two exports never look identical.

    @classmethod
    def column_names(cls) -> list[str]:
        """Return the column names in declaration order.

        Returns:
            One list that the CSV writer and the database writer both read.
        """
        return [field.name for field in fields(cls)]  # WHY: the dataclass declares the order one time.

    def as_row(self) -> dict[str, Any]:
        """Return the finding as a flat dict for the export writer.

        Returns:
            One dict whose keys match ``column_names`` exactly.
        """
        return {field.name: getattr(self, field.name) for field in fields(self)}  # WHY: keep the declared order.


class RogueDhcpRecordNormalizer:
    """Convert a raw Mist record into a ``RogueDhcpFinding``.

    Why:
        The three source shapes name the switch, the time, and the detail text
        in different fields. This class holds every one of those differences,
        so the scanner never reads a raw Mist field name.
    """

    def __init__(self, org_id: str, scan_started_at: str, window_end: float) -> None:
        """Store the values that every finding of one run shares.

        Args:
            org_id: The organization the scan covered.
            scan_started_at: The scan start time as an ISO 8601 string.
            window_end: The scan window end as epoch seconds, which decides the state.
        """
        self._org_id = org_id  # WHY: every row names the organization, and the value never changes in one run.
        self._scan_started_at = scan_started_at  # WHY: stamp every row with one run time.
        self._window_end = window_end  # WHY: the active rule measures backward from the window end.

    @staticmethod
    def _first_text(value: Any) -> str:
        """Return one readable string from a scalar, a list, or a missing value.

        Args:
            value: A Mist field that can hold a string, a list, or nothing.

        Returns:
            The scalar as a string, the joined list, or an empty string.
        """
        if value is None:  # WHY: a missing field is normal across the three record shapes.
            return ""
        if isinstance(value, list):  # WHY: an alarm carries switches and reasons as lists.
            return "; ".join(str(item) for item in value if item is not None)  # WHY: keep every entry readable.
        return str(value)  # WHY: a scalar needs only a string conversion.

    @staticmethod
    def _first_item(value: Any) -> str:
        """Return the first entry of a list, or the scalar itself.

        Args:
            value: A Mist field that can hold a string, a list, or nothing.

        Returns:
            The first list entry as a string, the scalar as a string, or an empty string.
        """
        if isinstance(value, list):  # WHY: an alarm names its switches in a list, newest first.
            return str(value[0]) if value else ""  # WHY: an empty list names no switch.
        return "" if value is None else str(value)  # WHY: a scalar needs only a string conversion.

    @staticmethod
    def _epoch(value: Any) -> float:
        """Return a Mist timestamp as epoch seconds.

        Args:
            value: A Mist timestamp, which arrives as a number or a numeric string.

        Returns:
            The value as a float, or 0.0 when the field holds nothing readable.
        """
        try:  # WHY: a malformed timestamp must not end the scan.
            return float(value)  # WHY: Mist sends epoch seconds, sometimes with a fractional part.
        except (TypeError, ValueError):  # WHY: the field can be absent or hold text.
            return 0.0  # WHY: a zero sorts first and marks the value as unknown.

    @staticmethod
    def _iso(epoch_seconds: float) -> str:
        """Return an epoch second value as an ISO 8601 string in UTC.

        Args:
            epoch_seconds: The time as epoch seconds.

        Returns:
            The ISO 8601 string, or an empty string when the input is zero.
        """
        if not epoch_seconds:  # WHY: a zero means the record named no time.
            return ""
        return datetime.fromtimestamp(epoch_seconds, tz=UTC).isoformat()  # WHY: UTC avoids a local offset.

    @staticmethod
    def is_closed(record: dict[str, Any]) -> bool:
        """Report whether Mist already closed this record.

        Why:
            A time window alone cannot tell an open fault from a fault that Mist
            resolved two hours ago. Both fall inside the trailing window. The
            alarm record carries the answer directly, in ``status`` and in
            ``resolved_time``, so this method reads the cloud verdict instead of
            guessing from the clock.

        Warning: a ``status`` of ``reoccured`` means the fault returned. That
        value must never read as closed, or the scan would hide a live rogue
        DHCP server.

        Args:
            record: One raw Mist alarm, event, or Marvis config action.

        Returns:
            True when an operator acknowledged the record, or Mist resolved it.
        """
        if record.get("acked") is True:  # WHY: an operator closed the alarm by hand.
            return True
        if record.get("resolved_time"):  # WHY: the cloud stamped the moment it resolved the alarm.
            return True
        return str(record.get("status") or "").strip().lower() in RESOLVED_STATUSES  # WHY: the cloud verdict.

    def resolve_state(self, last_seen_epoch: float, record: dict[str, Any] | None = None) -> str:
        """Report whether a finding is open now or closed inside the window.

        A finding reads ``historical`` when Mist closed it. Otherwise it reads
        ``active`` when its last occurrence falls inside the trailing active
        window. Every other finding reads ``historical``.

        Args:
            last_seen_epoch: The last occurrence as epoch seconds.
            record: The raw Mist record. An event carries no resolution field,
                so the caller may leave it unset.

        Returns:
            The literal ``active`` or the literal ``historical``.
        """
        if record is not None and self.is_closed(record):  # WHY: the cloud verdict outranks the clock.
            return STATE_HISTORICAL
        age = self._window_end - last_seen_epoch  # WHY: measure backward from the window end, not from now.
        if last_seen_epoch and age <= ACTIVE_WINDOW_SECONDS:  # WHY: a recent occurrence means the fault stands.
            return STATE_ACTIVE
        return STATE_HISTORICAL  # WHY: an old occurrence or a missing time reads as history.

    @staticmethod
    def build_record_id(site_id: str, device_mac: str, port_id: str, signal_family: str, last_seen: float) -> str:
        """Return the merge key for one finding.

        Two records that name one site, one switch, one port, one signal family,
        and one minute describe one real event. The key rounds the time to the
        minute, because an alarm and an event rarely carry the identical second.

        Warning: the key reads the signal family, not the literal Mist type. The
        alarm catalog spells the detection in lower case and the event catalog
        spells it in upper case, so a key built on the literal string would
        report one rogue DHCP server twice.

        Args:
            site_id: The site identifier.
            device_mac: The switch MAC address.
            port_id: The switch port identifier.
            signal_family: The canonical family from ``RogueDhcpSignalMatcher``.
            last_seen: The last occurrence as epoch seconds.

        Returns:
            A short hexadecimal digest that identifies the merged finding.
        """
        minute = int(last_seen // 60)  # WHY: round to the minute so two sources of one event agree.
        raw = f"{site_id}|{device_mac}|{port_id}|{signal_family}|{minute}"  # WHY: one readable key before hashing.
        # WHY: sha256 gives a stable short key. The value identifies a row, so it guards no secret.
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]

    def _build(self, parts: dict[str, Any]) -> RogueDhcpFinding:
        """Assemble one finding from the fields a source method already resolved.

        Args:
            parts: The resolved values, keyed by the finding column name.

        Returns:
            One frozen finding.
        """
        last_seen = float(parts["last_seen_epoch"])  # WHY: the merge key and the state both read this value.
        record_id = self.build_record_id(  # WHY: compute the merge key from the grouping fields.
            parts["site_id"], parts["device_mac"], parts["port_id"], parts["signal_family"], last_seen
        )
        return RogueDhcpFinding(  # WHY: one construction point keeps every source on the same column order.
            record_id=record_id,
            org_id=self._org_id,
            site_id=parts["site_id"],
            site_name=parts.get("site_name", UNKNOWN_SITE_NAME),
            device_name=parts["device_name"],
            device_mac=parts["device_mac"],
            device_model=parts["device_model"],
            device_type=parts.get("device_type", "switch"),
            port_id=parts["port_id"],
            vlan=parts["vlan"],
            source=parts["source"],
            signal_type=parts["signal_type"],
            signal_family=parts["signal_family"],
            state=parts["state"],
            severity=parts["severity"],
            first_seen=self._iso(parts["first_seen_epoch"]),
            last_seen=self._iso(last_seen),
            occurrence_count=parts["occurrence_count"],
            details=parts["details"],
            scan_started_at=self._scan_started_at,
        )

    def from_alarm(self, record: dict[str, Any], source: str) -> RogueDhcpFinding:
        """Convert one Mist alarm into a finding.

        Args:
            record: The raw alarm from an alarm search.
            source: The source name, which states which search returned it.

        Returns:
            One frozen finding.
        """
        last_seen = self._epoch(record.get("last_seen") or record.get("timestamp"))  # WHY: prefer the later field.
        first_seen = self._epoch(record.get("timestamp") or record.get("last_seen"))  # WHY: prefer the earlier field.
        return self._build(
            {
                "site_id": self._first_text(record.get("site_id")),
                "device_name": self._first_item(record.get("hostnames")),
                "device_mac": self._first_item(record.get("switches")),
                "device_model": self._first_item(record.get("models")),
                "port_id": self._first_text(record.get("port_id")),
                "vlan": self._first_text(record.get("vlan") or record.get("vlans")),
                "source": source,
                "signal_type": self._first_text(record.get("type")),
                "signal_family": RogueDhcpSignalMatcher.signal_family(record),
                "state": self.resolve_state(last_seen, record),  # WHY: an alarm states its own resolution.
                "severity": self._first_text(record.get("severity")),
                "first_seen_epoch": min(first_seen, last_seen) if first_seen and last_seen else last_seen,
                "last_seen_epoch": last_seen,
                "occurrence_count": int(self._epoch(record.get("count")) or 1),
                "details": self._first_text(record.get("reasons") or record.get("text")),
            }
        )

    def from_device_event(self, record: dict[str, Any], source: str) -> RogueDhcpFinding:
        """Convert one Mist switch event into a finding.

        Args:
            record: The raw event from a device event search.
            source: The source name, which states which search returned it.

        Returns:
            One frozen finding.
        """
        last_seen = self._epoch(record.get("timestamp"))  # WHY: an event stamps its own occurrence time.
        first_seen = self._epoch(record.get("first_seen")) or last_seen  # WHY: a repeated event names both ends.
        details = self._first_text(record.get("text"))  # WHY: the event text names the addresses and the interface.
        reason = self._first_text(record.get("reason"))  # WHY: the Marvis event carries its cause here.
        return self._build(
            {
                "site_id": self._first_text(record.get("site_id")),
                "device_name": self._first_text(record.get("hostname") or record.get("device_name")),
                "device_mac": self._first_text(record.get("mac") or record.get("chassis_mac")),
                "device_model": self._first_text(record.get("model")),
                "device_type": self._first_text(record.get("device_type")) or "switch",
                "port_id": self._first_text(record.get("port_id")),
                "vlan": self._first_text(record.get("vlan_id") or record.get("vlan")),
                "source": source,
                "signal_type": self._first_text(record.get("type")),
                "signal_family": RogueDhcpSignalMatcher.signal_family(record),
                "state": self.resolve_state(last_seen, record),  # WHY: honor a resolution field if Mist adds one.
                "severity": self._first_text(record.get("severity")),
                "first_seen_epoch": first_seen,
                "last_seen_epoch": last_seen,
                "occurrence_count": int(self._epoch(record.get("count")) or 1),
                "details": "; ".join(part for part in (details, reason) if part),
            }
        )

    def from_marvis_action(self, record: dict[str, Any], site_id: str) -> RogueDhcpFinding:
        """Convert one Marvis config action into a finding.

        Args:
            record: The raw action from the Marvis config action search.
            site_id: The site the scan queried, because the record may omit it.

        Returns:
            One frozen finding.
        """
        last_seen = self._epoch(record.get("timestamp"))  # WHY: the action stamps when Marvis acted.
        operation = self._first_text(record.get("op"))  # WHY: name what Marvis did, such as disable the port.
        reason = self._first_text(record.get("reason"))  # WHY: the reason proves the rogue DHCP cause.
        return self._build(
            {
                "site_id": self._first_text(record.get("site_id")) or site_id,
                "device_name": self._first_text(record.get("hostname")),
                "device_mac": self._first_text(record.get("mac")),
                "device_model": self._first_text(record.get("model")),
                "port_id": self._first_text(record.get("port_id")),
                "vlan": self._first_text(record.get("vlan_ids") or record.get("vlan_id")),
                "source": SOURCE_MARVIS_ACTION,
                "signal_type": self._first_text(record.get("type")) or reason,
                "signal_family": MARVIS_REMEDIATION_FAMILY,
                "state": self.resolve_state(last_seen, record),  # WHY: honor a resolution field if Mist adds one.
                "severity": self._first_text(record.get("severity")),
                "first_seen_epoch": last_seen,
                "last_seen_epoch": last_seen,
                "occurrence_count": 1,
                "details": f"Marvis ran {operation} because of {reason}" if operation else reason,
            }
        )


class RogueDhcpFindingMerger:
    """Collapse the findings that describe one real event into one row.

    Why:
        An alarm and a switch event both fire when a rogue DHCP server appears
        on a port. Without a merge, one rogue server produces two rows, and an
        operator counts the fault twice.
    """

    # WHY: on these columns the held row wins, and the new row fills only a blank. One list
    # replaces nineteen `or` expressions, which kept the merge above the complexity limit.
    _FILLABLE_FIELDS = (
        "site_name",
        "device_name",
        "device_mac",
        "device_model",
        "device_type",
        "port_id",
        "vlan",
        "signal_type",
        "signal_family",
        "severity",
        "details",
    )

    @classmethod
    def _fill_blanks(cls, existing: RogueDhcpFinding, addition: RogueDhcpFinding) -> dict[str, Any]:
        """Return each fillable column, preferring the held value over the new one.

        Args:
            existing: The finding already held for the key.
            addition: The finding that shares the key.

        Returns:
            One override dict for the fillable columns only.
        """
        return {name: getattr(existing, name) or getattr(addition, name) for name in cls._FILLABLE_FIELDS}

    @staticmethod
    def _merge_span(existing: RogueDhcpFinding, addition: RogueDhcpFinding) -> tuple[str, str]:
        """Return the widest time span the two findings cover.

        Args:
            existing: The finding already held for the key.
            addition: The finding that shares the key.

        Returns:
            The earliest first seen value and the latest last seen value.
        """
        first = [value for value in (existing.first_seen, addition.first_seen) if value]  # WHY: drop a blank.
        last = [value for value in (existing.last_seen, addition.last_seen) if value]  # WHY: drop a blank.
        # WHY: every stamp is an ISO 8601 string in UTC, so a text compare orders them correctly.
        return (min(first) if first else "", max(last) if last else "")

    @classmethod
    def _combine(cls, existing: RogueDhcpFinding, addition: RogueDhcpFinding) -> RogueDhcpFinding:
        """Fold one finding into another that shares its merge key.

        Args:
            existing: The finding already held for the key.
            addition: The finding that shares the key.

        Returns:
            One finding that names both sources and spans both times.
        """
        sources = sorted({*existing.source.split(", "), *addition.source.split(", ")})  # WHY: name every search once.
        first_seen, last_seen = cls._merge_span(existing, addition)  # WHY: the row must cover the whole span.
        # WHY: one open report outranks a closed one, because the fault still stands.
        state = STATE_ACTIVE if STATE_ACTIVE in (existing.state, addition.state) else STATE_HISTORICAL
        return replace(  # WHY: rebuild the frozen row, keeping the key and the run stamp of the held row.
            existing,
            **cls._fill_blanks(existing, addition),
            source=", ".join(sources),
            state=state,
            first_seen=first_seen,
            last_seen=last_seen,
            occurrence_count=existing.occurrence_count + addition.occurrence_count,
        )

    @classmethod
    def merge(cls, findings: list[RogueDhcpFinding]) -> list[RogueDhcpFinding]:
        """Collapse every duplicate and return the rows in a stable order.

        Args:
            findings: Every finding the scan collected, in any order.

        Returns:
            One list with no duplicate merge key, sorted newest first.
        """
        logger.info("Merging rogue DHCP findings count=%d", len(findings))  # WHY: entry audit for the merge step.
        merged: dict[str, RogueDhcpFinding] = {}  # WHY: one entry for each merge key.
        for finding in findings:  # WHY: fold each finding into the entry that shares its key.
            held = merged.get(finding.record_id)  # WHY: a missing entry means this key is new.
            merged[finding.record_id] = cls._combine(held, finding) if held else finding  # WHY: fold or store.
        # WHY: newest first puts the standing fault at the top of the operator table.
        ordered = sorted(merged.values(), key=lambda row: (row.last_seen, row.site_id, row.port_id), reverse=True)
        logger.debug("Merged rogue DHCP findings input=%d output=%d", len(findings), len(ordered))
        return ordered
