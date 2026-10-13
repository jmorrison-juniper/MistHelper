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
    assert summaries[0].metrics["utilization"] == (42.5, 42.5, "percent")
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
    assert weekly.metrics["utilization"] == (61.25, 80.0, "percent")
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
