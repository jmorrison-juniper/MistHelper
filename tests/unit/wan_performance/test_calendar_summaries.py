"""Check UTC summaries with independently authored synthetic measurements."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone

import pytest

from src.interfaces.wan_performance.domain.calendar import CalendarPeriod, CalendarWindow
from src.interfaces.wan_performance.domain.measurement import MetricMeasurement
from src.interfaces.wan_performance.domain.summary import (
    CalendarSummaries,
    LinkEventSummary,
    StateObservationSummary,
)
from src.interfaces.wan_performance.presentation.offline_preview import OfflinePreviewFactory


@pytest.mark.parametrize(
    ("instant", "kind", "start", "end", "hours"),
    [
        (datetime(2024, 2, 29, 12, tzinfo=UTC), "daily", "2024-02-29", "2024-03-01", 24),
        (datetime(2021, 1, 1, tzinfo=UTC), "weekly", "2020-12-28", "2021-01-04", 168),
        (datetime(2024, 2, 29, tzinfo=UTC), "monthly", "2024-02-01", "2024-03-01", 696),
        (datetime(2024, 12, 31, tzinfo=UTC), "monthly", "2024-12-01", "2025-01-01", 744),
    ],
)
def test_calendar_period_preserves_utc_boundaries(
    instant: datetime, kind: str, start: str, end: str, hours: int
) -> None:
    """Use ISO weeks and calendar months across year and leap-day boundaries."""
    period = CalendarPeriod.containing(instant, kind)
    assert period.start.date().isoformat() == start
    assert period.end.date().isoformat() == end
    assert period.expected_hours == hours
    assert period.start.tzinfo == UTC
    assert period.contains(period.start)
    assert not period.contains(period.end)


@pytest.mark.parametrize(
    "instant",
    [datetime(2024, 1, 1), datetime(2024, 1, 1, tzinfo=timezone(timedelta(hours=1)))],
)
def test_calendar_period_rejects_ambiguous_time(instant: datetime) -> None:
    """Refuse naive or non-UTC timestamps before grouping measurements."""
    with pytest.raises(ValueError, match="UTC"):
        CalendarPeriod.containing(instant, "daily")


def test_calendar_period_rejects_unsupported_kind() -> None:
    """Reject an unsupported reporting period instead of selecting a default."""
    with pytest.raises(ValueError, match="period"):
        CalendarPeriod.containing(datetime(2024, 1, 1, tzinfo=UTC), "annual")


def test_rolling_period_rejects_non_utc_time_and_unknown_window() -> None:
    """Reject rolling windows without an exact UTC boundary and supported duration."""
    with pytest.raises(ValueError, match="UTC"):
        CalendarPeriod.ending_at(datetime(2024, 1, 1), "rolling_3h")
    with pytest.raises(ValueError, match="3, 12, or 24"):
        CalendarPeriod.ending_at(datetime(2024, 1, 1, tzinfo=UTC), "rolling_7h")


@pytest.mark.parametrize(
    ("end", "start"),
    [
        (datetime(2024, 3, 31, 12, 45, tzinfo=UTC), datetime(2023, 2, 28, 12, 45, tzinfo=UTC)),
        (datetime(2025, 3, 31, 12, 45, tzinfo=UTC), datetime(2024, 2, 29, 12, 45, tzinfo=UTC)),
    ],
)
def test_history_window_uses_thirteen_calendar_months(end: datetime, start: datetime) -> None:
    """Clamp month-end dates while preserving the exact UTC time."""
    assert CalendarWindow.thirteen_months_ending(end) == (start, end)


@pytest.mark.parametrize(
    "end",
    [datetime(2024, 1, 1), datetime(2024, 1, 1, tzinfo=timezone(timedelta(hours=1)))],
)
def test_history_window_rejects_ambiguous_time(end: datetime) -> None:
    """Reject naive and non-UTC history boundaries."""
    with pytest.raises(ValueError, match="UTC"):
        CalendarWindow.thirteen_months_ending(end)


def test_summary_keeps_missing_hours_and_peer_records_separate() -> None:
    """Count observed circuit hours and rolling windows without using peer rows."""
    dashboard = OfflinePreviewFactory.build()
    summaries = CalendarSummaries.build(dashboard.measurements, dashboard.circuit)
    assert [summary.period.kind for summary in summaries] == [
        "daily",
        "weekly",
        "monthly",
        "rolling_3h",
        "rolling_12h",
        "rolling_24h",
    ]
    assert [summary.observed_hours for summary in summaries] == [1, 1, 1, 1, 1, 1]
    assert [summary.period.expected_hours for summary in summaries] == [24, 168, 744, 3, 12, 24]
    assert summaries[0].metrics["utilization"] == (12.5, 12.5, 12.5, "percent")
    assert "packet_loss" not in summaries[0].metrics
    assert summaries[0].provenance == "synthetic"


def test_rolling_windows_end_at_latest_retained_observation() -> None:
    """Show available values in each rolling window without filling missing hours."""
    dashboard = OfflinePreviewFactory.build()
    first = dashboard.measurements[0]
    records = tuple(
        replace(
            first,
            hour_start_utc=instant,
            collected_at_utc=instant,
            metrics={"latency": MetricMeasurement(value, "ms")},
        )
        for instant, value in (
            (datetime(2024, 1, 1, 10, tzinfo=UTC), 10),
            (datetime(2024, 1, 1, 12, tzinfo=UTC), 20),
            (datetime(2024, 1, 1, 13, tzinfo=UTC), 30),
        )
    )
    summaries = CalendarSummaries.build(records, first.identity)
    rolling = {summary.period.kind: summary for summary in summaries if summary.period.kind.startswith("rolling_")}

    assert rolling["rolling_3h"].period.start == datetime(2024, 1, 1, 11, tzinfo=UTC)
    assert rolling["rolling_3h"].period.end == datetime(2024, 1, 1, 14, tzinfo=UTC)
    assert rolling["rolling_3h"].observed_hours == 2
    assert rolling["rolling_3h"].metrics["latency"] == (25.0, 30.0, 30.0, "ms")
    assert rolling["rolling_12h"].observed_hours == 3
    assert rolling["rolling_24h"].observed_hours == 3


def test_weekly_mean_uses_equal_weighted_daily_means() -> None:
    """Use equal daily weights rather than silently changing source summaries."""
    dashboard = OfflinePreviewFactory.build()
    first = dashboard.measurements[0]
    second = replace(first, hour_start_utc=first.hour_start_utc + timedelta(hours=1))
    third = replace(
        first,
        hour_start_utc=first.hour_start_utc + timedelta(days=1),
        collected_at_utc=first.collected_at_utc + timedelta(days=1),
        metrics={"utilization": MetricMeasurement(80.0, "percent")},
    )
    summaries = CalendarSummaries.build((first, second, third), dashboard.circuit)
    weekly = next(summary for summary in summaries if summary.period.kind == "weekly")
    assert weekly.metrics["utilization"] == (46.25, 80.0, 80.0, "percent")
    assert weekly.observed_hours == 3


def test_monthly_p95_uses_maximum_daily_raw_sample_p95():
    """Use the local maximum-of-daily-p95 rule for calendar months."""
    dashboard = OfflinePreviewFactory.build()
    first = dashboard.measurements[0]
    records = tuple(
        replace(
            first,
            hour_start_utc=datetime(2024, 1, day, 12, tzinfo=UTC),
            collected_at_utc=datetime(2024, 1, day, 12, tzinfo=UTC),
            metrics={
                "utilization_pct": MetricMeasurement(
                    float(day),
                    "%",
                    sample_count=1,
                    coverage_fraction=1,
                    raw_values=(float(day),),
                )
            },
        )
        for day in range(1, 21)
    )

    monthly = next(
        summary for summary in CalendarSummaries.build(records, first.identity) if summary.period.kind == "monthly"
    )

    assert monthly.metrics["utilization_pct"] == (10.5, 20.0, 20.0, "%")


def test_event_availability_and_congestion_summaries_preserve_incomplete_hours():
    """Sum event minutes and sample occupancy only where each source window is complete."""
    dashboard = OfflinePreviewFactory.build()
    first = dashboard.measurements[0]
    metrics = {
        "up_minutes": MetricMeasurement(20.0, "min", sample_count=1, coverage_fraction=5 / 6),
        "down_minutes": MetricMeasurement(30.0, "min", sample_count=1, coverage_fraction=5 / 6),
        "flap_count": MetricMeasurement(2.0, "count", sample_count=1, coverage_fraction=1),
        "congestion_minutes_over_70_pct": MetricMeasurement(20.0, "min", sample_count=6, coverage_fraction=1),
        "congestion_minutes_over_80_pct": MetricMeasurement(
            None, "min", sample_count=4, coverage_fraction=4 / 6, missing_reason="Incomplete samples."
        ),
    }
    incomplete = {
        name: MetricMeasurement(
            None,
            "min" if name != "flap_count" else "count",
            sample_count=0,
            coverage_fraction=0,
            missing_reason="Incomplete source window.",
        )
        for name in metrics
    }
    records = (
        replace(first, metrics=metrics, provenance="live"),
        replace(
            first,
            hour_start_utc=first.hour_start_utc + timedelta(hours=1),
            collected_at_utc=first.collected_at_utc + timedelta(hours=1),
            metrics=incomplete,
            provenance="live",
        ),
    )

    daily = CalendarSummaries.build(records, first.identity)[0]

    assert daily.link_event_summary == LinkEventSummary(1, 1, 24, 20, 30, 2, 40)
    assert daily.congestion_durations[0].minutes == 20
    assert daily.congestion_durations[0].complete_hours == 1
    assert daily.congestion_durations[1].minutes == 0
    assert daily.congestion_durations[1].complete_hours == 0


def test_mixed_event_and_ordinary_hours_ignore_absent_event_metrics():
    """Exclude ordinary poll hours from event summaries without losing known evidence."""
    dashboard = OfflinePreviewFactory.build()
    first = dashboard.measurements[0]
    event_hour = replace(
        first,
        metrics={
            "up_minutes": MetricMeasurement(60.0, "min"),
            "down_minutes": MetricMeasurement(0.0, "min"),
            "flap_count": MetricMeasurement(0.0, "count"),
        },
        provenance="live",
    )
    ordinary_hour = replace(
        first,
        hour_start_utc=first.hour_start_utc + timedelta(hours=1),
        collected_at_utc=first.collected_at_utc + timedelta(hours=1),
        metrics={"rx_bps": MetricMeasurement(100, "bit/s")},
        provenance="live",
    )

    daily = next(
        summary
        for summary in CalendarSummaries.build((event_hour, ordinary_hour), first.identity)
        if summary.period.kind == "daily"
    )

    assert daily.link_event_summary == LinkEventSummary(1, 1, 24, 60, 0, 0, 100)


def test_missing_event_evidence_does_not_report_zero_flaps_or_minutes():
    """Keep absent event results unknown instead of reporting healthy zero values."""
    dashboard = OfflinePreviewFactory.build()
    first = dashboard.measurements[0]
    missing = MetricMeasurement(None, "count", missing_reason="The event search is incomplete.")
    record = replace(
        first,
        metrics={
            "up_minutes": MetricMeasurement(None, "min", missing_reason="The event search is incomplete."),
            "down_minutes": MetricMeasurement(None, "min", missing_reason="The event search is incomplete."),
            "flap_count": missing,
        },
        provenance="live",
    )

    daily = next(
        summary for summary in CalendarSummaries.build((record,), first.identity) if summary.period.kind == "daily"
    )

    assert daily.link_event_summary == LinkEventSummary(0, 0, 24, None, None, None, None)


def test_known_zero_flaps_do_not_infer_known_duration_minutes():
    """Keep a verified zero-flap result while duration evidence remains unknown."""
    dashboard = OfflinePreviewFactory.build()
    first = dashboard.measurements[0]
    record = replace(first, metrics={"flap_count": MetricMeasurement(0.0, "count")}, provenance="live")

    daily = next(
        summary for summary in CalendarSummaries.build((record,), first.identity) if summary.period.kind == "daily"
    )

    assert daily.link_event_summary == LinkEventSummary(1, 0, 24, None, None, 0, None)


def test_summary_does_not_turn_missing_metrics_into_zero() -> None:
    """Preserve absent values without claiming a healthy measurement."""
    dashboard = OfflinePreviewFactory.build()
    record = replace(
        dashboard.measurements[0],
        metrics={"utilization": MetricMeasurement(None, "percent", missing_reason="No samples")},
    )
    summaries = CalendarSummaries.build((record,), dashboard.circuit)
    assert summaries[0].metrics == {"utilization": (None, None, None, "percent")}
    assert summaries[0].observed_hours == 1


def test_daily_p95_uses_floor_index_and_short_sample_fallback() -> None:
    """Use a floor-index percentile and maximum fallback for short samples."""
    dashboard = OfflinePreviewFactory.build()
    first = dashboard.measurements[0]
    records = tuple(
        replace(
            first,
            hour_start_utc=datetime(2024, 1, 1, hour, tzinfo=UTC),
            collected_at_utc=datetime(2024, 1, 1, hour, tzinfo=UTC),
            metrics={"latency": MetricMeasurement(float(hour), "ms")},
        )
        for hour in range(22)
    )
    daily = CalendarSummaries.build(records, first.identity)[0]
    assert daily.metrics["latency"] == (10.5, 21.0, 20.0, "ms")

    short = CalendarSummaries.build(records[:3], first.identity)[0]
    assert short.metrics["latency"][2] == 2.0


@pytest.mark.parametrize("violation", ["duplicate", "provenance", "unit"])
def test_summary_rejects_ambiguous_records(violation: str) -> None:
    """Refuse duplicates, mixed origins, and incompatible units before calculation."""
    dashboard = OfflinePreviewFactory.build()
    first = dashboard.measurements[0]
    second = replace(first, hour_start_utc=first.hour_start_utc - timedelta(hours=1))
    if violation == "duplicate":
        second = first
    elif violation == "provenance":
        second = replace(second, provenance="live")
    else:
        second = replace(second, metrics={"utilization": MetricMeasurement(1.0, "milliseconds")})
    with pytest.raises(ValueError, match=violation):
        CalendarSummaries.build((first, second), dashboard.circuit)


def test_summary_without_matching_records_is_empty() -> None:
    """Return no periods when the requested circuit has no observations."""
    dashboard = OfflinePreviewFactory.build()
    summaries = CalendarSummaries.build((dashboard.measurements[1],), dashboard.circuit)
    assert summaries == ()


@pytest.mark.parametrize("hour_gap", [1, 24])
@pytest.mark.parametrize("reverse", [False, True])
def test_peer_mos_summary_preserves_retained_missing_units(hour_gap: int, reverse: bool, tmp_path) -> None:
    """Keep pre-change missing MOS records readable beside documented scores."""
    import sqlite3

    from src.interfaces.wan_performance.collection.snapshot_records import PeerSnapshotMetrics
    from src.interfaces.wan_performance.integration.record_codec import RecordCodec
    from src.interfaces.wan_performance.integration.sqlite_history import SQLiteHistory

    dashboard = OfflinePreviewFactory.build()
    peer = replace(
        next(record for record in dashboard.measurements if record.identity == dashboard.peer_path),
        provenance="live",
    )
    retained = replace(peer, metrics={"mos": MetricMeasurement(None, "unknown", missing_reason="Unit unknown.")})
    retained = RecordCodec.decode(RecordCodec.encode(retained))
    current = replace(
        peer,
        hour_start_utc=peer.hour_start_utc + timedelta(hours=hour_gap),
        collected_at_utc=peer.collected_at_utc + timedelta(hours=hour_gap),
        metrics=PeerSnapshotMetrics.parse({"mos": 4.2}),
    )
    path = tmp_path / "retained-mos.sqlite"
    sqlite3.connect(path).close()
    history = SQLiteHistory(path)
    history.upsert((retained,))
    history.upsert((current,))
    records = history.read(
        peer.identity, retained.hour_start_utc - timedelta(hours=1), current.hour_start_utc + timedelta(hours=1)
    )
    records = tuple(reversed(records)) if reverse else records

    summaries = CalendarSummaries.build(records, peer.identity)

    for summary in summaries:
        if summary.metrics["mos"][0] is not None:
            assert summary.metrics["mos"] == (4.2, 4.2, 4.2, "score")
    assert retained.metrics["mos"].value is None
    assert retained.metrics["mos"].unit == "unknown"
    assert len(records) == 2
    assert any(record.metrics["mos"].value is None and record.metrics["mos"].unit == "unknown" for record in records)


def test_peer_mos_summary_rejects_incompatible_present_units() -> None:
    """Do not reinterpret an actual measured value with an unknown unit."""
    dashboard = OfflinePreviewFactory.build()
    peer = next(record for record in dashboard.measurements if record.identity == dashboard.peer_path)
    first = replace(peer, metrics={"mos": MetricMeasurement(4, "unknown")})
    second = replace(
        first,
        hour_start_utc=first.hour_start_utc - timedelta(hours=1),
        metrics={"mos": MetricMeasurement(5, "score")},
    )
    with pytest.raises(ValueError, match="units"):
        CalendarSummaries.build((first, second), peer.identity)


@pytest.mark.parametrize("key,hours", [("6h", 6), ("12h", 12), ("24h", 24), ("7d", 168)])
def test_retained_view_windows_use_completed_utc_hour_buckets(key: str, hours: int) -> None:
    """Define independent UTC view intervals without claiming measurement coverage."""
    from src.interfaces.wan_performance.presentation.inspection.windows import ObservationWindow

    instant = datetime(2026, 11, 14, 6, 46, 32, tzinfo=UTC)
    window = ObservationWindow.select(key, instant)
    assert window is not None and window.end == datetime(2026, 11, 14, 6, tzinfo=UTC)
    assert window.start == window.end - timedelta(hours=hours)
    assert window.expected_hours == hours
    assert ObservationWindow.select("", instant) is None


@pytest.mark.parametrize(
    "instant",
    [
        datetime(2026, 11, 14, 6),
        datetime.fromisoformat("2026-11-14T06:00:00+05:00"),
    ],
)
def test_retained_view_rejects_non_utc_reference_times(instant: datetime) -> None:
    """Do not reinterpret local wall-clock references as UTC history bounds."""
    from src.interfaces.wan_performance.presentation.inspection.windows import ObservationWindow

    with pytest.raises(ValueError, match="UTC"):
        ObservationWindow.select("7d", instant)


def test_retained_view_reads_exact_identity_without_filling_missing_hours(tmp_path) -> None:
    """Use actual SQLite bounds and preserve absent metrics instead of synthesizing records."""
    import sqlite3

    from src.interfaces.wan_performance.integration.sqlite_history import SQLiteHistory
    from src.interfaces.wan_performance.presentation.inspection.windows import ObservationWindow, RetainedWindow

    record = OfflinePreviewFactory.build().measurements[0]
    window = ObservationWindow.select("6h", record.hour_start_utc + timedelta(hours=6, minutes=20))
    assert window is not None and window.start == record.hour_start_utc
    retained = replace(
        record,
        provenance="live",
        collected_at_utc=window.end + timedelta(hours=1),
        metrics={"mos": MetricMeasurement(None, "unknown", missing_reason="Absent.")},
    )
    path = tmp_path / "retained-window.sqlite"
    sqlite3.connect(path).close()
    history = SQLiteHistory(path)
    history.upsert(
        tuple(replace(retained, hour_start_utc=window.start + timedelta(hours=hour)) for hour in [-1, 0, 3, 6])
    )

    view = RetainedWindow.read(history, retained.identity, window)

    assert [entry.hour_start_utc for entry in view.records] == [window.start, window.start + timedelta(hours=3)]
    assert view.missing_hours == 4
    assert all(entry.metrics["mos"].value is None for entry in view.records)
    assert view.error is None


@pytest.mark.parametrize("bad", ["duplicate", "foreign", "before", "end", "synthetic"])
def test_retained_view_rejects_invalid_repository_results(bad: str) -> None:
    """Refuse history that breaks the exact-identity, half-open, live-only contract."""
    from unittest.mock import MagicMock

    from src.interfaces.wan_performance.presentation.inspection.windows import ObservationWindow, RetainedWindow

    dashboard = OfflinePreviewFactory.build()
    record = replace(
        dashboard.measurements[0],
        provenance="live",
        collected_at_utc=dashboard.measurements[0].hour_start_utc + timedelta(hours=7),
    )
    window = ObservationWindow.select("6h", record.hour_start_utc + timedelta(hours=6))
    assert window is not None and window.start == record.hour_start_utc
    changes = {
        "foreign": {"identity": dashboard.peer_path},
        "before": {"hour_start_utc": window.start - timedelta(hours=1)},
        "end": {"hour_start_utc": window.end},
        "synthetic": {"provenance": "synthetic"},
    }
    records = (record, record) if bad == "duplicate" else (replace(record, **changes[bad]),)
    history = MagicMock()
    history.read.return_value = records
    with pytest.raises(ValueError, match="retained"):
        RetainedWindow.read(history, record.identity, window)


def test_threshold_counts_break_runs_at_missing_and_unknown_hours() -> None:
    """Count retained observations rather than inferred time above a threshold."""
    dashboard = OfflinePreviewFactory.build()
    original = dashboard.measurements[0]
    records = tuple(
        replace(
            original,
            hour_start_utc=datetime(2024, 1, 1, hour, tzinfo=UTC),
            collected_at_utc=datetime(2024, 1, 1, hour, 30, tzinfo=UTC),
            metrics={
                "rx_utilization_percent": MetricMeasurement(
                    value, "%", missing_reason="Absent" if value is None else None
                ),
                "tx_utilization_percent": MetricMeasurement(70, "%"),
            },
            provenance="live",
        )
        for hour, value in [(0, 70), (1, 80), (2, 90), (4, 91), (5, None), (6, 100)]
    )
    daily = CalendarSummaries.build(records, dashboard.circuit)[0]
    assert daily.observed_hours == 6
    assert daily.period.expected_hours == 24
    counts = {(entry.metric_name, entry.threshold_percent): entry for entry in daily.threshold_observations}
    receive = counts[("rx_utilization_percent", 70)]
    assert (receive.valid_hours, receive.above_hours, receive.longest_run) == (5, 4, 2)
    assert counts[("rx_utilization_percent", 80)].above_hours == 3
    assert counts[("rx_utilization_percent", 90)].above_hours == 2
    assert counts[("tx_utilization_percent", 70)].above_hours == 0


def test_weekly_threshold_run_crosses_midnight_without_counting_missing_days() -> None:
    """Calculate weekly runs from actual adjacent hours, not merged daily maxima."""
    dashboard = OfflinePreviewFactory.build()
    records = tuple(
        replace(
            dashboard.measurements[0],
            hour_start_utc=instant,
            collected_at_utc=instant,
            metrics={"rx_utilization_percent": MetricMeasurement(95, "%")},
        )
        for instant in (
            datetime(2024, 1, 1, 23, tzinfo=UTC),
            datetime(2024, 1, 2, 0, tzinfo=UTC),
            datetime(2024, 1, 3, 0, tzinfo=UTC),
        )
    )
    summaries = CalendarSummaries.build(tuple(reversed(records)), dashboard.circuit)
    weekly = next(summary for summary in summaries if summary.period.kind == "weekly")
    assert weekly.threshold_observations[0].longest_run == 2
    assert weekly.threshold_observations[0].above_hours == 3
    assert weekly.threshold_observations[0].valid_hours == 3
    assert all(
        summary.threshold_observations[0].longest_run == 1 for summary in summaries if summary.period.kind == "daily"
    )


def test_thresholds_do_not_interpret_unverified_units_or_other_metrics() -> None:
    """Exclude rate fields and incompatible utilization units from threshold counts."""
    dashboard = OfflinePreviewFactory.build()
    record = replace(
        dashboard.measurements[0],
        metrics={"rx_bps": MetricMeasurement(100, "bit/s"), "rx_utilization_percent": MetricMeasurement(95, "ms")},
    )
    assert CalendarSummaries.build((record,), dashboard.circuit)[0].threshold_observations == ()


def test_unknown_threshold_observations_report_zero_valid_hours() -> None:
    """Show absent evidence rather than a healthy threshold result."""
    dashboard = OfflinePreviewFactory.build()
    record = replace(
        dashboard.measurements[0],
        metrics={"rx_utilization_percent": MetricMeasurement(None, "%", missing_reason="Absent")},
    )
    entry = CalendarSummaries.build((record,), dashboard.circuit)[0].threshold_observations[0]
    assert (entry.valid_hours, entry.above_hours, entry.longest_run) == (0, 0, 0)


def test_monthly_thresholds_exclude_other_identity_and_prior_month() -> None:
    """Keep calendar boundaries and complete circuit identities separate."""
    dashboard = OfflinePreviewFactory.build()
    record = replace(
        dashboard.measurements[0],
        hour_start_utc=datetime(2024, 2, 1, tzinfo=UTC),
        collected_at_utc=datetime(2024, 2, 1, tzinfo=UTC),
        metrics={"rx_utilization_percent": MetricMeasurement(95, "%")},
    )
    prior = replace(record, hour_start_utc=datetime(2024, 1, 31, 23, tzinfo=UTC))
    other = replace(record, identity=dashboard.measurements[1].identity)
    summaries = CalendarSummaries.build((prior, other, record), dashboard.circuit)
    monthly = [summary for summary in summaries if summary.period.kind == "monthly"]
    assert len(monthly) == 2
    assert [summary.period.expected_hours for summary in monthly] == [744, 696]
    assert [summary.threshold_observations[0].above_hours for summary in monthly] == [1, 1]
    assert [summary.threshold_observations[0].longest_run for summary in monthly] == [1, 1]


def test_status_summaries_count_observed_changes_and_expose_sparse_coverage() -> None:
    """Count known states and adjacent-hour changes without filling missing periods."""
    dashboard = OfflinePreviewFactory.build()
    first = dashboard.measurements[0]
    records = tuple(
        replace(
            first,
            hour_start_utc=first.hour_start_utc + timedelta(hours=hour),
            collected_at_utc=first.collected_at_utc + timedelta(hours=hour),
            is_up_observation=state,
        )
        for hour, state in ((0, True), (1, False), (2, False), (3, None), (4, True), (5, False))
    )

    daily = CalendarSummaries.build(records, first.identity)[0]

    assert daily.state_observations == StateObservationSummary(5, 24, 2, 3, 40, 2)


def test_status_summaries_remain_absent_without_boolean_evidence() -> None:
    """Do not render an availability-shaped result when no state is known."""
    dashboard = OfflinePreviewFactory.build()
    record = replace(dashboard.measurements[0], is_up_observation=None)

    daily = CalendarSummaries.build((record,), record.identity)[0]

    assert daily.state_observations is None
