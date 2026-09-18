"""Tests for the rogue DHCP signal matcher.

The matcher decides which Mist records enter the scan result. A wrong accept
puts a DHCP pool fault in front of an operator as a security finding. A wrong
reject hides a live rogue DHCP server. Both faults are expensive, so every rule
carries a test here.
"""

from __future__ import annotations

import pytest

from src.security.rogue_dhcp.signals import (
    MARVIS_CONFIG_EVENT_TYPE,
    MARVIS_REMEDIATION_FAMILY,
    MARVIS_ROGUE_REASON,
    REJECTED_DHCP_TYPES,
    ROGUE_ALARM_TYPES,
    ROGUE_DETECTION_FAMILY,
    ROGUE_EVENT_TYPES,
    RogueDhcpSignalMatcher,
)


@pytest.mark.parametrize("alarm_type", sorted(ROGUE_ALARM_TYPES))
def test_accepts_every_literal_alarm_type(alarm_type: str) -> None:
    """FR-005. The matcher accepts each rogue DHCP alarm type from the Mist catalog."""
    assert RogueDhcpSignalMatcher.matches({"type": alarm_type}) is True


@pytest.mark.parametrize("event_type", sorted(ROGUE_EVENT_TYPES))
def test_accepts_every_literal_event_type(event_type: str) -> None:
    """FR-006. The matcher accepts each rogue DHCP switch event type."""
    assert RogueDhcpSignalMatcher.matches({"type": event_type}) is True


def test_accepts_the_marvis_event_with_a_rogue_reason() -> None:
    """FR-007. A Marvis config change counts only when its reason names a rogue DHCP server."""
    record = {"type": MARVIS_CONFIG_EVENT_TYPE, "reason": "rogue_dhcp_server"}
    assert RogueDhcpSignalMatcher.matches(record) is True


def test_rejects_the_marvis_event_with_another_reason() -> None:
    """FR-007. A Marvis config change for another cause never enters the result."""
    record = {"type": MARVIS_CONFIG_EVENT_TYPE, "reason": "port_stuck"}
    assert RogueDhcpSignalMatcher.matches(record) is False


def test_accepts_the_marvis_config_action_reason() -> None:
    """FR-008. A Marvis config action carries the reason and no type field."""
    assert RogueDhcpSignalMatcher.matches({"reason": MARVIS_ROGUE_REASON, "op": "disable_port"}) is True


def test_accepts_an_unknown_type_through_the_keyword_rule() -> None:
    """FR-009. A type string Mist adds later still matches when the text names both words."""
    record = {"type": "SW_ROGUE_DHCP_V2_DETECTED", "text": "an unknown future catalog entry"}
    assert RogueDhcpSignalMatcher.matches(record) is True


def test_accepts_a_keyword_match_from_the_alarm_reasons_list() -> None:
    """FR-009. An alarm stores its detail text in a list, so the keyword rule must read a list."""
    record = {"type": "some_new_type", "reasons": ["Rogue DHCP offer seen on ge-0/0/9"]}
    assert RogueDhcpSignalMatcher.matches(record) is True


def test_the_keyword_rule_ignores_letter_case() -> None:
    """FR-009. The keyword rule must not depend on the case the catalog uses."""
    record = {"type": "SOMETHING_NEW", "text": "ROGUE Dhcp Server observed"}
    assert RogueDhcpSignalMatcher.matches(record) is True


def test_rejects_a_record_that_names_only_dhcp() -> None:
    """FR-010. One word alone is not a rogue DHCP server."""
    assert RogueDhcpSignalMatcher.matches({"type": "SOMETHING_NEW", "text": "dhcp lease renewed"}) is False


def test_rejects_a_record_that_names_only_rogue() -> None:
    """FR-010. A rogue access point is a wireless finding, not a rogue DHCP server."""
    assert RogueDhcpSignalMatcher.matches({"type": "rogue_ap", "text": "rogue ap detected"}) is False


@pytest.mark.parametrize("rejected_type", sorted(REJECTED_DHCP_TYPES))
def test_rejects_every_known_dhcp_condition_that_is_not_a_rogue_server(rejected_type: str) -> None:
    """FR-010. A pool fault and a DHCP failure must never reach the result."""
    record = {"type": rejected_type, "text": "DHCP Pool vlan_215 is exhausted"}
    assert RogueDhcpSignalMatcher.matches(record) is False


def test_the_reject_list_outranks_the_keyword_rule() -> None:
    """FR-010. A rejected type wins even when the text holds both keywords."""
    record = {"type": "sw_dhcp_pool_exhausted", "text": "rogue dhcp words that would otherwise match"}
    assert RogueDhcpSignalMatcher.matches(record) is False


def test_is_rejected_ignores_case_and_spacing() -> None:
    """FR-010. A catalog value with a different case or a stray space still rejects."""
    assert RogueDhcpSignalMatcher.is_rejected(" SW_DHCP_POOL_EXHAUSTED ") is True
    assert RogueDhcpSignalMatcher.is_rejected("sw_dhcp_pool_exhausted") is True


def test_is_rejected_returns_false_for_an_empty_type() -> None:
    """A record with no type cannot match the reject list."""
    assert RogueDhcpSignalMatcher.is_rejected("") is False


def test_a_non_dict_record_never_matches() -> None:
    """A malformed page must not end the scan."""
    assert RogueDhcpSignalMatcher.matches(["not", "a", "dict"]) is False  # type: ignore[arg-type]


def test_the_alarm_filter_names_the_catalog_type() -> None:
    """The query parameter must equal the catalog string, or Mist returns nothing."""
    assert RogueDhcpSignalMatcher.alarm_type_filter() == "sw_rogue_dhcp_server_detected"


def test_the_event_filters_cover_both_event_types() -> None:
    """The scan must query the direct event and the Marvis config event."""
    filters = RogueDhcpSignalMatcher.event_type_filters()
    assert "SW_ROGUE_DHCP_SERVER_DETECTED" in filters
    assert MARVIS_CONFIG_EVENT_TYPE in filters


def test_the_marvis_reason_filter_names_the_catalog_reason() -> None:
    """The Marvis query filters server side, so the reason must match the catalog exactly."""
    assert RogueDhcpSignalMatcher.marvis_reason_filter() == "rogue_dhcp_server_detected"


def test_a_marvis_config_event_reads_as_a_repair() -> None:
    """A Marvis config change repairs the fault, so it must not merge with the detection."""
    record = {"type": MARVIS_CONFIG_EVENT_TYPE, "reason": "rogue_dhcp_server"}
    assert RogueDhcpSignalMatcher.signal_family(record) == MARVIS_REMEDIATION_FAMILY


def test_a_marvis_config_action_reads_as_a_repair() -> None:
    """A Marvis config action carries a reason and no type, and it is still a repair."""
    record = {"reason": MARVIS_ROGUE_REASON, "op": "disable_port"}
    assert RogueDhcpSignalMatcher.signal_family(record) == MARVIS_REMEDIATION_FAMILY


@pytest.mark.parametrize("detection_type", [*sorted(ROGUE_ALARM_TYPES), *sorted(ROGUE_EVENT_TYPES)])
def test_both_catalog_spellings_share_one_family(detection_type: str) -> None:
    """The alarm and the event spell one detection two ways, so the family must collapse them."""
    assert RogueDhcpSignalMatcher.signal_family({"type": detection_type}) == ROGUE_DETECTION_FAMILY


def test_the_two_families_are_different() -> None:
    """A detection and a repair must never share a merge family, or one row would hide the other."""
    assert ROGUE_DETECTION_FAMILY != MARVIS_REMEDIATION_FAMILY
