"""Check UTC summaries with independently authored synthetic measurements."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone

import pytest

from src.interfaces.portals.wan_performance.domain.calendar import CalendarPeriod
from src.interfaces.portals.wan_performance.domain.measurement import MetricMeasurement
from src.interfaces.portals.wan_performance.domain.summary import CalendarSummaries
from src.interfaces.portals.wan_performance.presentation.offline_preview import OfflinePreviewFactory


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


def test_summary_keeps_missing_hours_and_peer_records_separate() -> None:
    """Count observed circuit hours without using peer rows or filling gaps."""
    dashboard = OfflinePreviewFactory.build()
    summaries = CalendarSummaries.build(dashboard.measurements, dashboard.circuit)
    assert [summary.period.kind for summary in summaries] == ["daily", "weekly", "monthly"]
    assert [summary.observed_hours for summary in summaries] == [1, 1, 1]
    assert [summary.period.expected_hours for summary in summaries] == [24, 168, 744]
    assert summaries[0].metrics["utilization"] == (12.5, 12.5, "percent")
    assert "packet_loss" not in summaries[0].metrics
    assert summaries[0].provenance == "synthetic"


def test_weekly_mean_preserves_source_unweighted_daily_means() -> None:
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
    assert weekly.metrics["utilization"] == (46.25, 80.0, "percent")
    assert weekly.observed_hours == 3


def test_summary_does_not_turn_missing_metrics_into_zero() -> None:
    """Preserve absent values without claiming a healthy measurement."""
    dashboard = OfflinePreviewFactory.build()
    record = replace(
        dashboard.measurements[0],
        metrics={"utilization": MetricMeasurement(None, "percent", missing_reason="No samples")},
    )
    summaries = CalendarSummaries.build((record,), dashboard.circuit)
    assert summaries[0].metrics == {"utilization": (None, None, "percent")}
    assert summaries[0].observed_hours == 1


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
