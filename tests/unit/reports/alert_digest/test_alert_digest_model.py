"""Tests for alert digest model logic."""

from __future__ import annotations  # Enable modern annotations without runtime imports.

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


def test_result_rows_hold_one_row_per_candidate() -> None:
    """Each candidate receives one acknowledgement log result row."""
    definitions = AlertDigestModel.definitions_by_key([definition()])  # Build the category map.
    records = AlertDigestModel.records_from_rows([alarm(1), alarm(2)], definitions)  # Normalize two rows.
    candidates = AlertDigestModel.acknowledgement_candidates(records)  # Select both unacknowledged rows.
    results = AlertDigestModel.result_rows(candidates, "dry_run", None, "No request sent.")  # Build results.
    assert [result.outcome for result in results] == ["dry_run", "dry_run"]  # Confirm one outcome per row.
