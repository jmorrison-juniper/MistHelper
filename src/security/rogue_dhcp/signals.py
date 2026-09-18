"""Decide whether one Mist record reports a rogue DHCP server on a switch.

Why:
    Mist reports a rogue DHCP server through four different records, and each
    one carries a different literal type string. An alarm uses a lower-case
    string. A switch event uses an upper-case string. A Marvis self-driving
    event hides the reason in a second field. A Marvis config action names the
    reason and no type at all.

    This module holds every one of those strings one time. No other module in
    the feature repeats a Mist string, so a future catalog change edits one
    file.

Evidence:
    ``data/ConstAlarmDefs.csv`` line 117 carries the alarm string.
    ``data/ConstDeviceEvents.csv`` lines 306 and 239 carry the two event
    strings. ``documentation/mist-api-openapi31yaml.yaml`` lines 33913 and
    84290 carry the Marvis config action reason.

Trap:
    Mist reports several other DHCP conditions that are not a rogue server. A
    pool exhaustion record and a DHCP failure record both hold the word
    ``dhcp``, so a keyword rule alone would accept them. The reject list below
    runs before the keyword rule and blocks every one of them.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on the annotations in this module.

import logging  # WHY: record the match decision so an operator can audit a surprising row.
from typing import Any  # WHY: a Mist record is an untyped dict that the SDK returns.

logger = logging.getLogger(__name__)  # Name the logger for this module so a reader filters by source.

ROGUE_ALARM_TYPES = frozenset(
    {"sw_rogue_dhcp_server_detected"}
)  # WHY: the alarm catalog names exactly this type for a rogue DHCP server.

ROGUE_EVENT_TYPES = frozenset(
    {"SW_ROGUE_DHCP_SERVER_DETECTED"}
)  # WHY: the device event catalog names exactly this type for a rogue DHCP server.

# WHY: this event proves Marvis acted on a switch, but the reason field decides why it acted.
MARVIS_CONFIG_EVENT_TYPE = "SW_CONFIG_CHANGED_BY_MARVIS"

# WHY: the Marvis config action endpoint filters on this exact reason string.
MARVIS_ROGUE_REASON = "rogue_dhcp_server_detected"

REJECTED_DHCP_TYPES = frozenset(
    {
        "sw_dhcp_pool_exhausted",  # WHY: a full pool is a capacity fault, not a rogue server.
        "SW_DHCP_POOL_EXHAUSTED",  # WHY: the event catalog spells the same fault in upper case.
        "sw_non_dhcp_client_detected",  # WHY: a static client is not a rogue server.
        "SW_NON_DHCP_CLIENT_DETECTED",  # WHY: the event catalog spells the same record in upper case.
        "gw_dhcp_pool_exhausted",  # WHY: a gateway pool fault is not a switch rogue server.
        "GW_DHCP_POOL_EXHAUSTED",  # WHY: the event catalog spells the same fault in upper case.
        "infra_dhcp_failure",  # WHY: a DHCP failure names a broken server, not an unauthorized one.
        "infra_dhcp_success",  # WHY: a recovery record reports that DHCP works again.
        "dhcp_failure",  # WHY: the Marvis DHCP failure alarm names a broken server.
        "minis_dhcp_failure",  # WHY: the Marvis-Minis DHCP failure alarm names a broken server.
    }
)  # WHY: one reject list keeps a DHCP record that names no rogue server out of the result.

# WHY: a record that holds both words names a rogue DHCP server even under a type string Mist adds later.
KEYWORD_PAIR = ("rogue", "dhcp")

# WHY: the alarm catalog and the event catalog spell one detection in two cases, so the merge
# key reads this family instead of the literal string. Without it, one real event yields two rows.
ROGUE_DETECTION_FAMILY = "rogue_dhcp_detection"

# WHY: a Marvis record reports a repair, not a detection, so it keeps its own family and its own row.
MARVIS_REMEDIATION_FAMILY = "marvis_remediation"

_TEXT_FIELDS = (
    "type",
    "reason",
    "text",
    "details",
    "display",
)  # WHY: these five fields carry the words that the keyword rule reads.

_LIST_TEXT_FIELDS = ("reasons",)  # WHY: an alarm carries its detail text in a list, not a string.

# WHY: build the lower-case reject set one time, because the matcher runs for every record on every page.
_REJECTED_LOWER = frozenset(rejected.lower() for rejected in REJECTED_DHCP_TYPES)


class RogueDhcpSignalMatcher:
    """Report whether a Mist record names a rogue DHCP server on a switch.

    Why:
        The scan reads four record shapes from three endpoint families. One
        matcher keeps the accept rule and the reject rule identical for every
        shape, so an alarm and an event never disagree about the same event.
    """

    @staticmethod
    def alarm_type_filter() -> str:
        """Return the value for the ``type`` query parameter of an alarm search.

        Returns:
            The single alarm type string that names a rogue DHCP server.
        """
        return next(iter(ROGUE_ALARM_TYPES))  # WHY: the catalog holds exactly one alarm type today.

    @staticmethod
    def event_type_filters() -> tuple[str, ...]:
        """Return every event type the scan queries.

        Returns:
            The rogue event type, then the Marvis config event type. The caller
            issues one query for each value, because the Mist event search
            accepts one type at a time.
        """
        return (*sorted(ROGUE_EVENT_TYPES), MARVIS_CONFIG_EVENT_TYPE)  # WHY: a stable order keeps a test readable.

    @staticmethod
    def marvis_reason_filter() -> str:
        """Return the value for the ``reason`` query parameter of a Marvis config action search.

        Returns:
            The exact reason string that names a rogue DHCP server detection.
        """
        return MARVIS_ROGUE_REASON  # WHY: the endpoint filters server side, so the scan reads fewer rows.

    @staticmethod
    def signal_family(record: dict[str, Any]) -> str:
        """Return the canonical family of one accepted record.

        Why:
            The alarm catalog spells the detection in lower case, and the event
            catalog spells the same detection in upper case. A merge key that
            reads the literal string therefore never joins the two reports of
            one real event. The family collapses that spelling difference.

            A Marvis record is a separate family, because it reports a repair
            and not a detection. An operator must still see that Marvis acted.

        Args:
            record: One raw Mist alarm, event, or Marvis config action.

        Returns:
            ``marvis_remediation`` for a Marvis repair, or ``rogue_dhcp_detection``.
        """
        record_type = str(record.get("type") or "")  # WHY: the type decides the family for an event.
        if record_type == MARVIS_CONFIG_EVENT_TYPE:  # WHY: this event reports that Marvis changed the switch.
            return MARVIS_REMEDIATION_FAMILY
        if not record_type and record.get("reason"):  # WHY: a Marvis config action carries a reason and no type.
            return MARVIS_REMEDIATION_FAMILY
        return ROGUE_DETECTION_FAMILY  # WHY: every other accepted record reports the detection itself.

    @staticmethod
    def is_rejected(type_text: str) -> bool:
        """Report whether a type string names a DHCP condition that is not a rogue server.

        Args:
            type_text: The ``type`` field of a Mist record.

        Returns:
            True when the reject list holds the string, without regard to case.
        """
        if not type_text:  # WHY: a record with no type cannot match the reject list.
            return False
        candidate = type_text.strip()  # WHY: a trailing space in a catalog value must not defeat the lookup.
        return candidate.lower() in _REJECTED_LOWER  # WHY: one lower-case test covers every catalog spelling.

    @staticmethod
    def _collect_text(record: dict[str, Any]) -> str:
        """Join every text field of a record into one lower-case string.

        Args:
            record: One raw Mist alarm, event, or Marvis config action.

        Returns:
            One lower-case string that holds every readable field value.
        """
        parts: list[str] = []  # WHY: gather the pieces once, then join one time.
        for field in _TEXT_FIELDS:  # WHY: read the five fields that carry readable words.
            value = record.get(field)  # WHY: a missing field is normal across the four record shapes.
            if isinstance(value, str):  # WHY: only a string carries words the keyword rule can read.
                parts.append(value)  # WHY: keep the value for the joined search text.
        for field in _LIST_TEXT_FIELDS:  # WHY: an alarm stores its detail text in a list.
            values = record.get(field)  # WHY: the field is absent on an event and on a Marvis action.
            if isinstance(values, list):  # WHY: guard against a scalar that the API may return instead.
                parts.extend(str(item) for item in values)  # WHY: accept any item type the list carries.
        return " ".join(parts).lower()  # WHY: one lower-case copy makes the keyword test case-insensitive.

    @staticmethod
    def _matches_literal(record: dict[str, Any]) -> bool:
        """Report whether a record matches one of the four literal catalog rules.

        Args:
            record: One raw Mist alarm, event, or Marvis config action.

        Returns:
            True when a literal rule accepts the record.
        """
        record_type = str(record.get("type") or "")  # WHY: a Marvis config action carries no type field.
        if record_type in ROGUE_ALARM_TYPES or record_type in ROGUE_EVENT_TYPES:  # WHY: the two direct catalog hits.
            return True
        reason = str(record.get("reason") or "").lower()  # WHY: the two Marvis rules both read the reason field.
        if record_type == MARVIS_CONFIG_EVENT_TYPE:  # WHY: Marvis changed a switch, so the reason decides why.
            return KEYWORD_PAIR[0] in reason and KEYWORD_PAIR[1] in reason  # WHY: accept only a rogue DHCP reason.
        return reason == MARVIS_ROGUE_REASON  # WHY: a Marvis config action names the reason and no type.

    @classmethod
    def matches(cls, record: dict[str, Any]) -> bool:
        """Report whether a Mist record names a rogue DHCP server on a switch.

        The reject list runs first, so a DHCP pool fault never reaches the
        keyword rule. A literal catalog hit runs next, because it is exact. The
        keyword rule runs last and catches a type string Mist adds later.

        Args:
            record: One raw Mist alarm, event, or Marvis config action.

        Returns:
            True when the record names a rogue DHCP server.
        """
        if not isinstance(record, dict):  # WHY: the SDK can return a scalar inside a malformed page.
            logger.debug("Rogue DHCP matcher skipped a non-dict record of type %s", type(record).__name__)
            return False
        record_type = str(record.get("type") or "")  # WHY: both the reject rule and the literal rule read it.
        if cls.is_rejected(record_type):  # WHY: block a DHCP fault that names no rogue server.
            logger.debug("Rogue DHCP matcher rejected the known DHCP type %s", record_type)
            return False
        if cls._matches_literal(record):  # WHY: an exact catalog hit is the strongest evidence.
            logger.debug("Rogue DHCP matcher accepted the literal type %s", record_type or "<no type>")
            return True
        haystack = cls._collect_text(record)  # WHY: build the search text one time for the keyword rule.
        accepted = KEYWORD_PAIR[0] in haystack and KEYWORD_PAIR[1] in haystack  # WHY: both words must appear.
        if accepted:  # WHY: record the weaker match so an operator can audit an unexpected row.
            logger.debug("Rogue DHCP matcher accepted the keyword rule for type %s", record_type or "<no type>")
        return accepted
