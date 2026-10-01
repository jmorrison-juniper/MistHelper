"""Tests for alert digest model logic."""

from __future__ import annotations  # Enable modern annotations without runtime imports.

from time import perf_counter  # Measure pure grouping speed for the performance acceptance criterion.

from src.reports.alert_digest.model import AlertDigestModel  # Test pure model helpers.

from .conftest import alarm, definition  # Reuse synthetic alarm factories.


def test_definition_map_uses_alarm_keys() -> None:
    """Alarm definitions are keyed by Mist alarm type."""
    mapped = AlertDigestModel.definitions_by_key([definition("device_down", "infrastructure", "critical")])
    assert mapped["device_down"].group == "infrastructure"  # Confirm category source.


def test_unknown_alarm_type_gets_unknown_category() -> None:
    """An alarm absent from definitions remains in the digest."""
    records = AlertDigestModel.records_from_rows([alarm(type="mystery_alarm")], {})  # Normalize without definitions.
    assert records[0].category == "unknown"  # Confirm unknown category.


def test_grouping_sums_recurrence_and_time_range() -> None:
    """Rows with the same type and site become one digest group."""
    definitions = AlertDigestModel.definitions_by_key([definition()])  # Build the category map.
    records = AlertDigestModel.records_from_rows([alarm(1), alarm(2, count=2)], definitions)  # Normalize rows.
    groups = AlertDigestModel.group_records(records)  # Group the rows.
    assert len(groups) == 1  # Confirm one row per alarm type and site.
    assert groups[0].recurrence == 3  # Confirm count summing.
    assert groups[0].first_seen == "2023-11-14T22:13:21Z"  # Confirm earliest first seen.
    assert groups[0].last_seen == "2023-11-14T22:15:02Z"  # Confirm latest last seen.


def test_acknowledgement_candidates_use_unacknowledged_ids() -> None:
    """Only unacknowledged alarms with IDs can be acknowledged."""
    definitions = AlertDigestModel.definitions_by_key([definition()])  # Build the category map.
    rows = [alarm(1), alarm(2, acked=True), alarm(3, id="")]  # Include allowed and rejected rows.
    candidates = AlertDigestModel.acknowledgement_candidates(AlertDigestModel.records_from_rows(rows, definitions))
    assert [candidate.alarm_id for candidate in candidates] == ["alarm-1"]  # Confirm safe filtering.


def test_acknowledgement_candidates_treat_missing_acked_as_open() -> None:
    """A live search row without acked remains an acknowledgement candidate."""
    definitions = AlertDigestModel.definitions_by_key([definition("idp_attack_detected")])  # Build live type map.
    row = {  # Mirror the live searchOrgAlarms payload shape from issue 3690.
        "applications": ["ssh"],  # Preserve a live-only field that the model ignores safely.
        "attacker_ips": ["192.0.2.10"],  # Preserve a live-only field that the model ignores safely.
        "attacks": ["scan"],  # Preserve a live-only field that the model ignores safely.
        "count": 1,  # Preserve recurrence from the live alarm row.
        "cve_ids": [],  # Preserve a live-only field that the model ignores safely.
        "group": "idp",  # Preserve a live-only category hint that definitions override.
        "id": "live-alarm-1",  # Preserve the identifier needed for acknowledgement.
        "ingress_ports": ["ge-0/0/1"],  # Preserve a live-only field that the model ignores safely.
        "last_seen": 1_700_000_100,  # Preserve the live last-seen epoch.
        "org_id": "00000000-0000-4000-8000-000000003690",  # Preserve the live organization field.
        "protocols": ["tcp"],  # Preserve a live-only field that the model ignores safely.
        "severity": "warn",  # Preserve the live severity when no definition overrides it.
        "site_id": "site-1",  # Preserve the live site identifier.
        "timestamp": 1_700_000_000,  # Preserve the live first-seen epoch.
        "type": "idp_attack_detected",  # Preserve the live alarm type key.
    }
    records = AlertDigestModel.records_from_rows([row], definitions)  # Normalize the live-shaped row.
    candidates = AlertDigestModel.acknowledgement_candidates(records)  # Select candidate rows for menu 281.
    assert [candidate.alarm_id for candidate in candidates] == ["live-alarm-1"]  # Confirm missing acked means open.


def test_result_rows_hold_one_row_per_candidate() -> None:
    """Each candidate receives one acknowledgement log result row."""
    definitions = AlertDigestModel.definitions_by_key([definition()])  # Build the category map.
    records = AlertDigestModel.records_from_rows([alarm(1), alarm(2)], definitions)  # Normalize two rows.
    candidates = AlertDigestModel.acknowledgement_candidates(records)  # Select both unacknowledged rows.
    results = AlertDigestModel.result_rows(candidates, "dry_run", None, "No request sent.")  # Build results.
    assert [result.outcome for result in results] == ["dry_run", "dry_run"]  # Confirm one outcome per row.


def test_missing_sample_ack_state_and_times_use_safe_defaults() -> None:
    """Missing optional alarm fields keep the digest readable."""
    definitions = AlertDigestModel.definitions_by_key([definition()])  # Build the category map.
    row = alarm(1, hostname="", acked=None, timestamp=None, last_seen=None)  # Remove optional evidence fields.
    groups = AlertDigestModel.group_records(AlertDigestModel.records_from_rows([row], definitions))  # Normalize.
    assert groups[0].sample_device_or_client == ""  # Confirm a missing sample stays blank.
    assert groups[0].acknowledged_state == "not_reported"  # Confirm omitted ack data stays explicit.
    assert groups[0].first_seen == ""  # Confirm a missing first seen value stays blank.
    assert groups[0].last_seen == ""  # Confirm a missing last seen value stays blank.


def test_grouping_performance_budget_for_local_rows() -> None:
    """Pure grouping stays well below the feature performance budget."""
    definitions = AlertDigestModel.definitions_by_key([definition()])  # Build the category map.
    rows = [alarm(number, site_name=f"Site {number % 5}") for number in range(1, 501)]  # Build local rows.
    started = perf_counter()  # Start a small local timing guard.
    groups = AlertDigestModel.group_records(AlertDigestModel.records_from_rows(rows, definitions))  # Group rows.
    elapsed = perf_counter() - started  # Stop the local timing guard.
    assert len(groups) == 5  # Confirm grouping worked while measuring speed.
    assert elapsed < 1.0  # Confirm pure processing cannot consume the 60 second operation budget.
