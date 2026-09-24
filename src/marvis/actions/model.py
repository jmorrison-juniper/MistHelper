"""Catalogs and record shapes for menu 270, the Marvis Actions export and bulk resolve.

Why:
    The Mist API calls one Marvis Action a "suggestion", and it returns each
    action as a nested row. A NOC engineer needs one flat row with readable
    names. This module holds the name catalogs that the Mist UI shows, the
    readers that turn a raw value into a safe column value, and the builder
    that turns one raw row into one CSV record and one database document.

Evidence:
    The names come from the Mist UI bundle ``admin2.21.1765-hotfix``, read on
    2026-09-23. Research R8 in ``specs/3299-marvis-actions-bulk-resolve`` holds
    the list. The built-in topic names win over the schema names, because the
    schema swaps the names of two gateway topics.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions in the annotations of this module.

import json  # WHY: a nested field reaches the CSV file as sorted JSON text.
import math  # WHY: reject an infinite or NaN number before it becomes a count.
import uuid  # WHY: derive the Mist action key when a row holds no uuid.
from collections.abc import Iterable, Mapping  # WHY: type the reader inputs without a concrete class.
from dataclasses import dataclass, fields  # WHY: the record declares its column order one time.
from datetime import UTC, datetime  # WHY: an epoch millisecond value becomes readable UTC text.
from typing import Any  # WHY: a raw Mist row holds values of any JSON type.

OPEN_STATUSES = frozenset({"open", "inprogress", "reoccured"})  # WHY: the Open tab of the Mist UI. Mist writes one r.

STATUS_NAMES = {  # WHY: the status names that the Mist UI shows, so the CSV reads like the portal.
    "open": "Open",  # WHY: a new action that nobody changed.
    "inprogress": "In Progress",  # WHY: an operator marked the action as in progress.
    "resolved": "Resolved By User",  # WHY: an operator resolved the action with a resolution code.
    "validated": "AI Validated",  # WHY: Marvis saw the problem stop and closed the action.
    "marvis_self_driven": "Marvis Self Driven",  # WHY: Marvis fixed the problem by itself.
    "reoccured": "Reoccurred",  # WHY: the problem came back after a close.
    "expired action": "Expired Action",  # WHY: the action aged out without a close.
}

CATEGORY_NAMES = {  # WHY: the super category names of the Mist UI, keyed by the API category value.
    "ap": "Wireless",  # WHY: access point topics.
    "application": "Data Center/Application",  # WHY: application reachability topics.
    "client": "Clients",  # WHY: client topics.
    "connectivity": "Connectivity",  # WHY: DHCP, DNS, ARP, and authentication topics.
    "gateway": "WAN",  # WHY: WAN edge topics.
    "layer_1": "Layer 1",  # WHY: cable and optic topics.
    "security": "Security",  # WHY: security topics.
    "switch": "Wired",  # WHY: switch topics.
}

TOPIC_NAMES: dict[tuple[str, str], str] = {  # WHY: the subcategory names of the Mist UI.
    # Wireless (ap) topics.
    ("ap", "ap_disconnect"): "AP Offline",
    ("ap", "health_check"): "Health Check Failed",
    ("ap", "insufficient_capacity"): "Insufficient Capacity",
    ("ap", "insufficient_coverage"): "Coverage Hole",
    ("ap", "non_compliant"): "Non-compliant",
    ("ap", "ap_loop"): "AP Loop Detected",
    ("ap", "site_down_isp_issue"): "ISP Offline",
    ("ap", "mxedge_failure"): "Mist Edge Anomaly",
    ("ap", "site_radar_channel_punishment"): "DFS Optimization",
    ("ap", "headroom_insufficient"): "Dynamic Capacity Optimization",
    # Data Center/Application (application) topics.
    ("application", "reachability_failure"): "Reachability Failure",
    # Clients (client) topics.
    ("client", "persistently_failing"): "Persistently Failing Clients",
    # Connectivity (connectivity) topics.
    ("connectivity", "arp_failure"): "ARP Failure",
    ("connectivity", "auth_failure"): "Authentication Failure",
    ("connectivity", "dhcp_failure"): "DHCP Failure",
    ("connectivity", "dns_failure"): "DNS Failure",
    # WAN (gateway) topics. The schema swaps the first and the last name, so these names win.
    ("gateway", "bad_wan_link"): "Bad WAN Uplink",
    ("gateway", "gw_mtu_mismatch"): "WAN Edge MTU Mismatch",
    ("gateway", "vpn_path_down"): "VPN Path Down",
    ("gateway", "non_compliant"): "Non-compliant",
    ("gateway", "gw_negotiation_incomplete"): "WAN Edge Negotiation Incomplete",
    ("gateway", "intermittent_wan_connectivity"): "Intermittent WAN Connectivity",
    # Layer 1 (layer_1) topics.
    ("layer_1", "bad_cable"): "Bad Cable",
    ("layer_1", "bad_fiber_optics"): "Bad Fiber Optics",
    # Wired (switch) topics.
    ("switch", "high_cpu"): "High CPU",
    ("switch", "missing_vlan"): "Missing VLAN",
    ("switch", "mtu_mismatch"): "Switch MTU Mismatch",
    ("switch", "negotiation_incomplete"): "Switch Negotiation Incomplete",
    ("switch", "port_flap"): "Network Port Flap",
    ("switch", "port_stuck"): "Port Stuck",
    ("switch", "stp_loop"): "Loop Detected",
    ("switch", "traffic_anomaly"): "Traffic Anomaly",
    ("switch", "misconfig_port"): "Misconfigured Port",
    ("switch", "sw_offline"): "Switch Offline",
    ("switch", "rogue_dhcp_server_detected"): "Rogue DHCP Server Detected",
    ("switch", "access_port_flap"): "Access Port Flap",
}

# The impacted_tuple items name a device under other keys for each topic. The first key that holds text wins.
NAME_KEYS = ("entity_name", "ap_name", "switch_hostname", "switch_name", "hostname")  # WHY: the device name keys.
MAC_KEYS = ("entity_mac", "ap_id", "switch_mac", "gateway_id", "mac")  # WHY: ap_id holds the AP MAC, so it is 2nd.
PORT_KEYS = ("port_id",)  # WHY: the wired and WAN topics name the impacted port under this key.
REASON_KEYS = (  # WHY: the details object states the cause under other keys for each topic.
    "disconnect_reason",
    "failure_reason",
    "reason",
    "sub_symptom",
    "event_name",
    "details_msg_in_ui",
)


@dataclass(frozen=True, slots=True)
class ResolutionCode:
    """One resolution code that the Mist UI offers when an operator resolves an action.

    Attributes:
        key: The value that the API stores in the ``label`` field.
        name: The text that the Mist UI shows for the code.
        needs_comment: True when the operator must explain the fix in a comment.
    """

    key: str  # WHY: the API value, such as "suggested".
    name: str  # WHY: the text that the operator reads.
    needs_comment: bool  # WHY: the code nonsuggested needs an explanation.


RESOLUTION_CODES = (  # WHY: the four codes in the order of the Mist UI, so the numbers match the portal.
    ResolutionCode("suggested", "Solved using the Mist suggested action", needs_comment=False),
    ResolutionCode("nonsuggested", "Solved using another method (please comment below)", needs_comment=True),
    ResolutionCode("known", "A known issue and should be ignored in the future", needs_comment=False),
    ResolutionCode("invalid", "Incorrectly listed as an issue", needs_comment=False),
)
RESOLUTION_ALIASES = {"other": "nonsuggested"}  # WHY: the operator thinks of code 2 as the "other method" code.
RESOLUTION_NAMES = {code.key: code.name for code in RESOLUTION_CODES}  # WHY: turn a stored label into its text.


class MarvisFieldReader:
    """Turn one raw JSON value into one safe column value.

    Why:
        A Mist row can hold null, a number, a string, a list, or an object in
        the same field. Each reader returns one fixed type, so the CSV file and
        the database always receive the same shape.
    """

    @staticmethod
    def text(value: Any) -> str:
        """Return a value as trimmed text.

        Args:
            value: Any JSON value.

        Returns:
            An empty string for None, sorted JSON for a list or a dict, and text for the rest.
        """
        if value is None:  # WHY: a null field becomes an empty cell, not the word None.
            return ""  # WHY: an empty cell is the CSV form of a missing value.
        if isinstance(value, (dict, list)):  # WHY: a nested value needs a stable text form.
            return json.dumps(value, sort_keys=True, default=str)  # WHY: sorted keys give the same text each run.
        return str(value).strip()  # WHY: trim the stray spaces that a free-text field can hold.

    @staticmethod
    def integer(value: Any) -> int | None:
        """Return a value as a whole number.

        Args:
            value: Any JSON value.

        Returns:
            The whole number, or None when the value holds no finite whole number.
        """
        if isinstance(value, bool):  # WHY: JSON true and false are not counts, although Python treats them as ints.
            return None  # WHY: a flag must not become the count 1 or 0.
        if isinstance(value, int):  # WHY: a JSON integer needs no conversion.
            return value  # WHY: keep the exact value, also for a very large number.
        if not isinstance(value, (float, str)):  # WHY: a list, a dict, or None holds no number.
            return None  # WHY: tell the caller that no number exists.
        try:  # WHY: a string can hold any text.
            number = float(value)  # WHY: accept "12", "12.0", and 12.0 alike.
        except ValueError:  # WHY: the text holds no number.
            return None  # WHY: tell the caller that no number exists.
        return int(number) if math.isfinite(number) and number.is_integer() else None  # WHY: reject 1.5, inf, NaN.

    @staticmethod
    def flag(value: Any) -> bool | None:
        """Return a value as a boolean flag.

        Args:
            value: Any JSON value.

        Returns:
            The boolean, or None when the value is not a JSON boolean.
        """
        return value if isinstance(value, bool) else None  # WHY: never guess a flag from text or a number.

    @staticmethod
    def iso(value: Any) -> str:
        """Return an epoch millisecond value as ISO 8601 UTC text.

        Args:
            value: An epoch time in milliseconds.

        Returns:
            The UTC time as text, or an empty string when the value holds no valid time.
        """
        epoch_ms = MarvisFieldReader.integer(value)  # WHY: the Mist times are whole milliseconds.
        if epoch_ms is None or epoch_ms <= 0:  # WHY: Mist writes 0 or null for a time that did not occur.
            return ""  # WHY: an empty cell tells the reader that no time exists.
        try:  # WHY: a very large value is outside the range that datetime accepts.
            return datetime.fromtimestamp(epoch_ms / 1000, tz=UTC).isoformat(timespec="seconds")  # WHY: UTC text.
        except (OverflowError, OSError, ValueError):  # WHY: each platform reports an out-of-range year differently.
            return ""  # WHY: an invalid time must not stop the export.

    @staticmethod
    def first_text(mapping: Mapping[str, Any], keys: Iterable[str]) -> str:
        """Return the first value that holds text, in the order of the keys.

        Args:
            mapping: The object to read.
            keys: The keys to try, in order of preference.

        Returns:
            The first text that is not empty, or an empty string.
        """
        for key in keys:  # WHY: the first key in the list is the most specific name.
            value = MarvisFieldReader.text(mapping.get(key))  # WHY: turn the raw value into trimmed text.
            if value:  # WHY: an empty value must not hide a later key that holds text.
                return value  # WHY: stop at the first match.
        return ""  # WHY: no key held text.


class MarvisCatalog:
    """Name the topics of the Marvis Actions, and give their recommended actions.

    Why:
        The API returns keys such as ``switch`` and ``sw_offline``. The NOC
        engineer knows the names that the Mist UI shows, such as ``Wired`` and
        ``Switch Offline``. This class joins the built-in names with the live
        topic schema, so a new Mist topic still receives a name.
    """

    def __init__(self, schema_rows: Iterable[Mapping[str, Any]]) -> None:
        """Keep the schema entries keyed by their category and symptom pair.

        Args:
            schema_rows: The entries of the ``suggestions_schema`` response. An empty list is valid.
        """
        self._schema: dict[tuple[str, str], Mapping[str, Any]] = {}  # WHY: one schema entry for each topic pair.
        for row in schema_rows:  # WHY: index each entry so a lookup costs one step.
            category = MarvisFieldReader.text(row.get("category"))  # WHY: the first half of the topic pair.
            symptom = MarvisFieldReader.text(row.get("symptom"))  # WHY: the second half of the topic pair.
            if category and symptom:  # WHY: an entry without a category or a symptom cannot name a topic.
                self._schema[(category, symptom)] = row  # WHY: the last entry wins when the schema repeats a pair.

    def topic_name(self, category: str, symptom: str) -> str:
        """Return the Mist UI name of a topic.

        Args:
            category: The API category value.
            symptom: The API symptom value.

        Returns:
            The built-in name, then the schema name, then the symptom key.
        """
        entry = self._schema.get((category, symptom), {})  # WHY: a topic can be absent from the schema.
        schema_name = MarvisFieldReader.text(entry.get("display_name"))  # WHY: the schema names a new topic.
        return TOPIC_NAMES.get((category, symptom)) or schema_name or symptom  # WHY: built-in, schema, then key.

    def recommended_action(self, category: str, symptom: str) -> str:
        """Return the recommended action text of a topic.

        Args:
            category: The API category value.
            symptom: The API symptom value.

        Returns:
            The schema text, or an empty string when the schema holds no entry.
        """
        entry = self._schema.get((category, symptom), {})  # WHY: a topic can be absent from the schema.
        return MarvisFieldReader.text(entry.get("recommended_action"))  # WHY: only the schema holds this text.

    def known_pairs(self) -> frozenset[tuple[str, str]]:
        """Return every topic pair that the catalog or the schema holds.

        Returns:
            The category and symptom pairs.
        """
        return frozenset(TOPIC_NAMES) | frozenset(self._schema)  # WHY: a filter accepts a topic from both sources.


@dataclass(frozen=True, slots=True)
class MarvisActionRecord:
    """One Marvis Action as one flat CSV row.

    Why:
        The field order is the column order of ``OrgMarvisActions.csv``. The
        record holds readable times only. The database document keeps the raw
        epoch values, so no precision is lost.
    """

    uuid: str  # WHY: the stable key of the action, the same as in the Mist UI.
    row_key: str  # WHY: the key that a resolve request names.
    suggestion_id: str  # WHY: the short ID that the Mist UI shows, such as swoff-291.
    org_id: str  # WHY: the organization of the action.
    site_id: str  # WHY: the site of the action.
    site_name: str  # WHY: the site name, for a human reader.
    category: str  # WHY: the super category key, such as switch.
    category_name: str  # WHY: the super category name, such as Wired.
    symptom: str  # WHY: the subcategory key, such as sw_offline.
    symptom_name: str  # WHY: the subcategory name, such as Switch Offline.
    topic: str  # WHY: the pair key, such as switch/sw_offline.
    suggestion: str  # WHY: the Mist code of the recommended fix.
    recommended_action: str  # WHY: the recommended fix as text.
    impact_scope: str  # WHY: the scope of the impact, such as site or device.
    status: str  # WHY: the status key, such as open or validated.
    status_name: str  # WHY: the status name, such as AI Validated.
    is_open: bool  # WHY: True when the action can take a resolve.
    severity: int | None  # WHY: the severity number that Mist assigns.
    label: str  # WHY: the resolution code of a closed action.
    label_name: str  # WHY: the text of the resolution code.
    comment: str  # WHY: the comment of the last resolve.
    assignee: str  # WHY: the person who owns the action.
    entity_type: str  # WHY: the kind of impacted entity, such as switch or ap.
    entity_id: str  # WHY: the identifier of the impacted entity.
    entity_names: str  # WHY: the names of the impacted devices.
    entity_macs: str  # WHY: the MAC addresses of the impacted devices.
    entity_ports: str  # WHY: the impacted ports.
    impacted_entity_count: int  # WHY: the number of impacted devices or ports.
    detail_reason: str  # WHY: the cause of the action, when Mist states one.
    start_time_iso: str  # WHY: when the problem started.
    end_time_iso: str  # WHY: when the problem stopped.
    suggestion_time_iso: str  # WHY: when Marvis wrote the action.
    resolve_time_iso: str  # WHY: when the action closed.
    validation_time_iso: str  # WHY: when Marvis checked the fix.
    reoccur_time_iso: str  # WHY: when the problem came back.
    duration: int | None  # WHY: the length of the problem.
    reoccur_count: int | None  # WHY: how often the problem came back.
    batch_count: int | None  # WHY: the number of grouped entities.
    self_drivable: bool | None  # WHY: True when Marvis can fix the problem alone.
    self_driven: bool | None  # WHY: True when Marvis did fix the problem alone.
    zendesk_ticket: str  # WHY: the support case of the action.
    details_json: str  # WHY: every topic value, for an audit.
    exported_at: str  # WHY: the time of the export run.

    @classmethod
    def column_names(cls) -> list[str]:
        """Return the CSV column names in field order.

        Returns:
            The column names.
        """
        return [field.name for field in fields(cls)]  # WHY: the dataclass is the one source of the column order.

    def as_row(self) -> dict[str, Any]:
        """Return the record as one CSV row.

        Returns:
            The column name and value pairs, in field order.
        """
        return {field.name: getattr(self, field.name) for field in fields(self)}  # WHY: keep the column order.


class MarvisActionRecordBuilder:
    """Build one flat record and one database document from one raw Mist row.

    Why:
        Each topic stores its device names, MACs, ports, and cause under other
        keys. The builder reads all of those keys in one place, so every CSV
        row has the same columns.
    """

    def __init__(self, catalog: MarvisCatalog, site_names: Mapping[str, str], exported_at: str) -> None:
        """Keep the shared lookups for every row of one run.

        Args:
            catalog: The topic names and the recommended actions.
            site_names: The site name for each site identifier. An empty map is valid.
            exported_at: The ISO time of this run, stored on each row.
        """
        self._catalog = catalog  # WHY: every row reads the same names.
        self._site_names = site_names  # WHY: every row reads the same site names.
        self._exported_at = exported_at  # WHY: one run time lets a reader group the rows of one export.

    @staticmethod
    def action_key(raw: Mapping[str, Any]) -> str:
        """Return the stable key of one action.

        Args:
            raw: One raw row of the suggestion list.

        Returns:
            The Mist uuid. Without a uuid, the key is the same UUID3 value that the Mist UI derives.
        """
        given = MarvisFieldReader.text(raw.get("uuid"))  # WHY: the API sets this key on every current row.
        if given:  # WHY: prefer the key that the API supplies.
            return given  # WHY: the key matches the Mist UI and the database document.
        row_key = MarvisFieldReader.text(raw.get("row_key"))  # WHY: the Mist UI derives the uuid from this value.
        seed = row_key or json.dumps(raw, sort_keys=True, default=str)  # WHY: the last fallback is the row text.
        return str(uuid.uuid3(uuid.NAMESPACE_X500, seed))  # WHY: the same seed always gives the same key.

    def build(self, raw: Mapping[str, Any]) -> MarvisActionRecord:
        """Return the flat record of one raw row.

        Args:
            raw: One raw row of the suggestion list.

        Returns:
            The record, with a value in every column.
        """
        details = self._details(raw)  # WHY: most topic-specific values live inside the details object.
        parts: dict[str, Any] = {}  # WHY: each helper fills one group of columns.
        parts.update(self._identity_part(raw))  # WHY: the keys that identify the action and its site.
        parts.update(self._topic_part(raw))  # WHY: the category and the subcategory columns.
        parts.update(self._status_part(raw))  # WHY: the status and the resolution columns.
        parts.update(self._entity_part(raw, details))  # WHY: the device, MAC, port, and cause columns.
        parts.update(self._time_part(raw))  # WHY: the readable time and the count columns.
        parts.update(self._audit_part(raw, details))  # WHY: the self-drive and the audit columns.
        return MarvisActionRecord(**parts)  # WHY: the dataclass rejects a missing or an extra column.

    @staticmethod
    def document(raw: Mapping[str, Any], record: MarvisActionRecord) -> dict[str, Any]:
        """Return the database document of one action.

        Args:
            raw: One raw row of the suggestion list.
            record: The flat record of the same row.

        Returns:
            The raw row with the readable columns added. The raw epoch values stay.
        """
        row = record.as_row()  # WHY: the readable columns help a database query.
        row.pop("details_json")  # WHY: the raw details object is already in the document.
        return {**raw, **row}  # WHY: the record uuid wins, so every document holds its primary key.

    @staticmethod
    def _details(raw: Mapping[str, Any]) -> Mapping[str, Any]:
        """Return the details object of a row, or an empty map."""
        details = raw.get("details")  # WHY: a row can hold null or a list here.
        return details if isinstance(details, Mapping) else {}  # WHY: the readers need a map.

    def _identity_part(self, raw: Mapping[str, Any]) -> dict[str, Any]:
        """Return the identity columns of a row."""
        site_id = MarvisFieldReader.text(raw.get("site_id"))  # WHY: the site name lookup needs the identifier.
        return {
            "uuid": self.action_key(raw),  # WHY: the natural primary key of the database collection.
            "row_key": MarvisFieldReader.text(raw.get("row_key")),  # WHY: the resolve request names this key.
            "suggestion_id": MarvisFieldReader.text(raw.get("suggestion_id")),  # WHY: the ID that the UI shows.
            "org_id": MarvisFieldReader.text(raw.get("org_id")),  # WHY: the organization of the action.
            "site_id": site_id,  # WHY: the site of the action.
            "site_name": self._site_names.get(site_id, ""),  # WHY: the engineer knows the site by name.
        }

    def _topic_part(self, raw: Mapping[str, Any]) -> dict[str, Any]:
        """Return the category and the subcategory columns of a row."""
        category = MarvisFieldReader.text(raw.get("category"))  # WHY: the super category key.
        symptom = MarvisFieldReader.text(raw.get("symptom"))  # WHY: the subcategory key.
        return {
            "category": category,  # WHY: the key that a filter accepts.
            "category_name": CATEGORY_NAMES.get(category, category),  # WHY: the name of the Mist UI, or the key.
            "symptom": symptom,  # WHY: the key that a filter accepts.
            "symptom_name": self._catalog.topic_name(category, symptom),  # WHY: the name of the Mist UI.
            "topic": f"{category}/{symptom}",  # WHY: one column that names the topic pair.
            "suggestion": MarvisFieldReader.text(raw.get("suggestion")),  # WHY: the Mist code of the advice.
            "recommended_action": self._catalog.recommended_action(category, symptom),  # WHY: the advice text.
            "impact_scope": MarvisFieldReader.text(raw.get("impact_scope")),  # WHY: the scope of the impact.
        }

    def _status_part(self, raw: Mapping[str, Any]) -> dict[str, Any]:
        """Return the status and the resolution columns of a row."""
        status = MarvisFieldReader.text(raw.get("status"))  # WHY: the status key decides the open flag.
        label = MarvisFieldReader.text(raw.get("label"))  # WHY: the resolution code of a closed action.
        return {
            "status": status,  # WHY: the key that the API returns.
            "status_name": STATUS_NAMES.get(status, status),  # WHY: the name of the Mist UI, or the key.
            "is_open": status in OPEN_STATUSES,  # WHY: only an open action can take a resolve.
            "severity": MarvisFieldReader.integer(raw.get("severity")),  # WHY: the severity number.
            "label": label,  # WHY: the stored resolution code key.
            "label_name": RESOLUTION_NAMES.get(label, label),  # WHY: the text of the resolution code.
            "comment": MarvisFieldReader.text(raw.get("comment")),  # WHY: the comment of the last resolve.
            "assignee": MarvisFieldReader.text(raw.get("assignee")),  # WHY: the person who owns the action.
        }

    def _entity_part(self, raw: Mapping[str, Any], details: Mapping[str, Any]) -> dict[str, Any]:
        """Return the device, MAC, port, and cause columns of a row."""
        items = self._impacted_items(details)  # WHY: one item for each impacted device or port.
        return {
            "entity_type": MarvisFieldReader.text(raw.get("entity_type")),  # WHY: the kind of impacted entity.
            "entity_id": MarvisFieldReader.text(raw.get("entity_id")),  # WHY: the identifier of the entity.
            "entity_names": self._joined(MarvisFieldReader.first_text(item, NAME_KEYS) for item in items),
            "entity_macs": self._joined(MarvisFieldReader.first_text(item, MAC_KEYS) for item in items),
            "entity_ports": self._joined(MarvisFieldReader.first_text(item, PORT_KEYS) for item in items),
            "impacted_entity_count": len(items),  # WHY: the number of impacted devices or ports.
            "detail_reason": MarvisFieldReader.first_text(details, REASON_KEYS),  # WHY: the cause of the action.
        }

    @staticmethod
    def _time_part(raw: Mapping[str, Any]) -> dict[str, Any]:
        """Return the readable time and the count columns of a row."""
        return {
            "start_time_iso": MarvisFieldReader.iso(raw.get("start_time")),  # WHY: when the problem started.
            "end_time_iso": MarvisFieldReader.iso(raw.get("end_time")),  # WHY: when the problem stopped.
            "suggestion_time_iso": MarvisFieldReader.iso(raw.get("suggestion_time")),  # WHY: when Marvis wrote it.
            "resolve_time_iso": MarvisFieldReader.iso(raw.get("resolve_time")),  # WHY: when the action closed.
            "validation_time_iso": MarvisFieldReader.iso(raw.get("validation_time")),  # WHY: when Marvis checked.
            "reoccur_time_iso": MarvisFieldReader.iso(raw.get("reoccur_time")),  # WHY: when the problem came back.
            "duration": MarvisFieldReader.integer(raw.get("duration")),  # WHY: the length of the problem.
            "reoccur_count": MarvisFieldReader.integer(raw.get("reoccur_count")),  # WHY: how often it came back.
            "batch_count": MarvisFieldReader.integer(raw.get("batch_count")),  # WHY: the grouped entity count.
        }

    def _audit_part(self, raw: Mapping[str, Any], details: Mapping[str, Any]) -> dict[str, Any]:
        """Return the self-drive and the audit columns of a row."""
        return {
            "self_drivable": MarvisFieldReader.flag(raw.get("self_drivable")),  # WHY: Marvis can fix it alone.
            "self_driven": MarvisFieldReader.flag(raw.get("self_driven")),  # WHY: Marvis did fix it alone.
            "zendesk_ticket": MarvisFieldReader.text(raw.get("zendesk_ticket")),  # WHY: the support case link.
            "details_json": MarvisFieldReader.text(dict(details)),  # WHY: keep every topic value for an audit.
            "exported_at": self._exported_at,  # WHY: the time of this run.
        }

    @staticmethod
    def _impacted_items(details: Mapping[str, Any]) -> list[Mapping[str, Any]]:
        """Return the impacted entity items of a details object."""
        items = details.get("impacted_tuple")  # WHY: Mist lists the impacted devices under this key.
        if not isinstance(items, list):  # WHY: a topic without devices holds no list.
            return []  # WHY: no device means no device columns.
        return [item for item in items if isinstance(item, Mapping)]  # WHY: skip an item that is not an object.

    @staticmethod
    def _joined(values: Iterable[str]) -> str:
        """Return the values that hold text, without duplicates, joined with a semicolon."""
        unique = dict.fromkeys(value for value in values if value)  # WHY: keep the first order, drop repeats.
        return "; ".join(unique)  # WHY: one CSV cell holds every name of the action.
