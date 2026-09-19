"""Tests for the rogue DHCP record shape, the normalizer, and the merge rule.

Three Mist sources name the switch, the time, and the detail text in different
fields. These tests prove that all three produce one column set, and that the
merge collapses two reports of one real event into one row.
"""

from __future__ import annotations

from src.security.rogue_dhcp.records import (
    SOURCE_MARVIS_ACTION,
    SOURCE_ORG_ALARM,
    SOURCE_ORG_EVENT,
    STATE_ACTIVE,
    STATE_HISTORICAL,
    RogueDhcpFinding,
    RogueDhcpFindingMerger,
    RogueDhcpRecordNormalizer,
)

WINDOW_END = 1_700_000_000.0  # A fixed end time keeps every state assertion deterministic.
RECENT = WINDOW_END - 3600  # One hour before the window end, so the state reads active.
OLD = WINDOW_END - (20 * 86400)  # Twenty days before the window end, so the state reads historical.


def build_normalizer() -> RogueDhcpRecordNormalizer:
    """Return a normalizer bound to the fixed test window."""
    return RogueDhcpRecordNormalizer("org-1", "2026-09-18T00:00:00+00:00", WINDOW_END)


ALARM_RECORD = {
    "id": "alarm-1",
    "type": "sw_rogue_dhcp_server_detected",
    "site_id": "site-a",
    "switches": ["544b8c167179"],
    "hostnames": ["SW-EDGE-01"],
    "models": ["EX2300-48MP"],
    "port_id": "ge-0/0/9.0",
    "severity": "warn",
    "timestamp": OLD,
    "last_seen": RECENT,
    "count": 7,
    "reasons": ["AS_PKT_DHCP_DROPPED: DHCP Packet Drop"],
}

EVENT_RECORD = {
    "type": "SW_ROGUE_DHCP_SERVER_DETECTED",
    "site_id": "site-a",
    "mac": "544b8c167179",
    "model": "EX2300-48MP",
    "device_type": "switch",
    "port_id": "ge-0/0/9.0",
    "timestamp": RECENT,
    "first_seen": OLD,
    "count": 7,
    "text": "AS_PKT_DHCP_DROPPED: DHCP Packet Drop",
}

MARVIS_RECORD = {
    "reason": "rogue_dhcp_server_detected",
    "op": "disable_port",
    "site_id": "site-a",
    "mac": "544b8c167179",
    "port_id": "ge-0/0/9.0",
    "timestamp": RECENT,
}


def test_every_source_produces_the_same_column_set() -> None:
    """FR-018. One table must hold an alarm, an event, and a Marvis action together."""
    normalizer = build_normalizer()
    rows = [
        normalizer.from_alarm(ALARM_RECORD, SOURCE_ORG_ALARM).as_row(),
        normalizer.from_device_event(EVENT_RECORD, SOURCE_ORG_EVENT).as_row(),
        normalizer.from_marvis_action(MARVIS_RECORD, "site-a").as_row(),
    ]
    expected = set(RogueDhcpFinding.column_names())
    for row in rows:
        assert set(row.keys()) == expected


def test_the_alarm_normalizer_reads_the_switch_from_the_list() -> None:
    """FR-015. An alarm names its switches in a list, so the first entry identifies the device."""
    finding = build_normalizer().from_alarm(ALARM_RECORD, SOURCE_ORG_ALARM)
    assert finding.device_mac == "544b8c167179"
    assert finding.device_name == "SW-EDGE-01"
    assert finding.device_model == "EX2300-48MP"
    assert finding.port_id == "ge-0/0/9.0"


def test_the_event_normalizer_reads_the_scalar_fields() -> None:
    """FR-015. An event names one MAC address in a scalar field."""
    finding = build_normalizer().from_device_event(EVENT_RECORD, SOURCE_ORG_EVENT)
    assert finding.device_mac == "544b8c167179"
    assert finding.device_type == "switch"
    assert finding.occurrence_count == 7


def test_the_marvis_normalizer_names_the_operation_and_the_reason() -> None:
    """The detail text must tell an engineer what Marvis did and why."""
    finding = build_normalizer().from_marvis_action(MARVIS_RECORD, "site-a")
    assert "disable_port" in finding.details
    assert "rogue_dhcp_server_detected" in finding.details
    assert finding.source == SOURCE_MARVIS_ACTION


def test_the_marvis_normalizer_falls_back_to_the_queried_site() -> None:
    """A Marvis record can omit the site, so the queried site must fill the column."""
    finding = build_normalizer().from_marvis_action({"reason": "x", "timestamp": RECENT}, "site-b")
    assert finding.site_id == "site-b"


def test_a_recent_finding_reads_active() -> None:
    """FR-017. A finding inside the trailing active window is still open."""
    assert build_normalizer().resolve_state(RECENT) == STATE_ACTIVE


def test_an_old_finding_reads_historical() -> None:
    """FR-017. A finding from twenty days ago is history, not a live fault."""
    assert build_normalizer().resolve_state(OLD) == STATE_HISTORICAL


def test_an_acknowledged_alarm_reads_historical() -> None:
    """FR-017. An operator who acknowledged the alarm closed it."""
    assert build_normalizer().resolve_state(RECENT, {"acked": True}) == STATE_HISTORICAL


def test_a_resolved_alarm_reads_historical() -> None:
    """Issue #2996. Mist resolved the fault, so the row must not read active."""
    record = {"type": "sw_rogue_dhcp_server_detected", "status": "resolved"}
    assert build_normalizer().resolve_state(RECENT, record) == STATE_HISTORICAL


def test_a_closed_alarm_reads_historical() -> None:
    """Issue #2996. A closed alarm is history, whatever the clock says."""
    assert build_normalizer().resolve_state(RECENT, {"status": "closed"}) == STATE_HISTORICAL


def test_a_resolved_time_stamp_reads_historical() -> None:
    """Issue #2996. The cloud stamped the moment it resolved the alarm."""
    assert build_normalizer().resolve_state(RECENT, {"resolved_time": RECENT}) == STATE_HISTORICAL


def test_a_reoccured_alarm_still_reads_active() -> None:
    """Issue #2996. A reoccured fault returned, so hiding it would lose a live rogue server."""
    assert build_normalizer().resolve_state(RECENT, {"status": "reoccured"}) == STATE_ACTIVE


def test_an_open_alarm_still_reads_active() -> None:
    """Issue #2996. An open alarm inside the window is a standing fault."""
    assert build_normalizer().resolve_state(RECENT, {"status": "open"}) == STATE_ACTIVE


def test_the_resolution_status_ignores_letter_case() -> None:
    """Issue #2996. A catalog value with another case must still close the row."""
    assert build_normalizer().resolve_state(RECENT, {"status": " Resolved "}) == STATE_HISTORICAL


def test_a_record_without_a_resolution_field_keeps_the_time_rule() -> None:
    """Issue #2996. A switch event carries no resolution field, so the clock still decides."""
    assert build_normalizer().resolve_state(RECENT, {"type": "SW_ROGUE_DHCP_SERVER_DETECTED"}) == STATE_ACTIVE


def test_a_resolved_alarm_reaches_the_finding() -> None:
    """Issue #2996. Prove the repair through the normalizer, not only the state helper."""
    resolved = {**ALARM_RECORD, "timestamp": RECENT, "last_seen": RECENT, "status": "resolved"}
    finding = build_normalizer().from_alarm(resolved, SOURCE_ORG_ALARM)
    assert finding.state == STATE_HISTORICAL


def test_an_open_alarm_reaches_the_finding_as_active() -> None:
    """Issue #2996. The repair must not turn every alarm into history."""
    open_alarm = {**ALARM_RECORD, "timestamp": RECENT, "last_seen": RECENT, "status": "open"}
    finding = build_normalizer().from_alarm(open_alarm, SOURCE_ORG_ALARM)
    assert finding.state == STATE_ACTIVE


def test_is_closed_reports_false_for_an_empty_record() -> None:
    """A record with no resolution field is not closed."""
    assert RogueDhcpRecordNormalizer.is_closed({}) is False


def test_a_missing_timestamp_reads_historical() -> None:
    """A record with no time cannot prove that the fault stands now."""
    assert build_normalizer().resolve_state(0.0) == STATE_HISTORICAL


def test_the_merge_collapses_two_reports_of_one_event() -> None:
    """FR-016 and SC-005. An alarm and an event about one port produce one row."""
    normalizer = build_normalizer()
    alarm = normalizer.from_alarm(ALARM_RECORD, SOURCE_ORG_ALARM)
    event = normalizer.from_device_event(EVENT_RECORD, SOURCE_ORG_EVENT)
    merged = RogueDhcpFindingMerger.merge([alarm, event])
    assert len(merged) == 1


def test_the_merged_row_names_every_source() -> None:
    """FR-020. An operator must see which searches reported the finding."""
    normalizer = build_normalizer()
    alarm = normalizer.from_alarm(ALARM_RECORD, SOURCE_ORG_ALARM)
    event = normalizer.from_device_event(EVENT_RECORD, SOURCE_ORG_EVENT)
    merged = RogueDhcpFindingMerger.merge([alarm, event])[0]
    assert SOURCE_ORG_ALARM in merged.source
    assert SOURCE_ORG_EVENT in merged.source


def test_the_merged_row_sums_the_occurrence_counts() -> None:
    """FR-019. A repeated fault must not lose its count during the merge."""
    normalizer = build_normalizer()
    alarm = normalizer.from_alarm(ALARM_RECORD, SOURCE_ORG_ALARM)
    event = normalizer.from_device_event(EVENT_RECORD, SOURCE_ORG_EVENT)
    merged = RogueDhcpFindingMerger.merge([alarm, event])[0]
    assert merged.occurrence_count == 14


def test_the_merged_row_keeps_the_open_state() -> None:
    """One open report outranks a closed one, because the fault still stands."""
    normalizer = build_normalizer()
    active = normalizer.from_device_event(EVENT_RECORD, SOURCE_ORG_EVENT)
    closed = normalizer.from_alarm({**ALARM_RECORD, "acked": True}, SOURCE_ORG_ALARM)
    merged = RogueDhcpFindingMerger.merge([closed, active])[0]
    assert merged.state == STATE_ACTIVE


def test_the_merge_keeps_two_different_ports_apart() -> None:
    """Two rogue servers on two ports are two findings, not one."""
    normalizer = build_normalizer()
    first = normalizer.from_device_event(EVENT_RECORD, SOURCE_ORG_EVENT)
    second = normalizer.from_device_event({**EVENT_RECORD, "port_id": "ge-0/0/20.0"}, SOURCE_ORG_EVENT)
    assert len(RogueDhcpFindingMerger.merge([first, second])) == 2


def test_the_merge_keeps_two_different_sites_apart() -> None:
    """Two sites that report one type are two findings."""
    normalizer = build_normalizer()
    first = normalizer.from_device_event(EVENT_RECORD, SOURCE_ORG_EVENT)
    second = normalizer.from_device_event({**EVENT_RECORD, "site_id": "site-z"}, SOURCE_ORG_EVENT)
    assert len(RogueDhcpFindingMerger.merge([first, second])) == 2


def test_the_merge_returns_an_empty_list_for_no_input() -> None:
    """An organization with no finding must not raise."""
    assert RogueDhcpFindingMerger.merge([]) == []


def test_the_merge_sorts_the_newest_finding_first() -> None:
    """An operator reads the standing fault at the top of the table."""
    normalizer = build_normalizer()
    old = normalizer.from_device_event({**EVENT_RECORD, "timestamp": OLD, "port_id": "ge-0/0/1"}, SOURCE_ORG_EVENT)
    new = normalizer.from_device_event(EVENT_RECORD, SOURCE_ORG_EVENT)
    merged = RogueDhcpFindingMerger.merge([old, new])
    assert merged[0].last_seen > merged[1].last_seen


def test_the_record_id_is_stable_for_one_event() -> None:
    """SC-006. A second run over one window must rewrite the same database row."""
    normalizer = build_normalizer()
    first = normalizer.from_device_event(EVENT_RECORD, SOURCE_ORG_EVENT)
    second = normalizer.from_device_event(EVENT_RECORD, SOURCE_ORG_EVENT)
    assert first.record_id == second.record_id


def test_a_malformed_timestamp_does_not_raise() -> None:
    """A text timestamp must never end the scan."""
    finding = build_normalizer().from_device_event({**EVENT_RECORD, "timestamp": "not a number"}, SOURCE_ORG_EVENT)
    assert finding.last_seen == ""


def test_the_row_dict_preserves_the_declared_column_order() -> None:
    """The CSV header must follow the dataclass declaration order."""
    row = build_normalizer().from_alarm(ALARM_RECORD, SOURCE_ORG_ALARM).as_row()
    assert list(row.keys()) == RogueDhcpFinding.column_names()
