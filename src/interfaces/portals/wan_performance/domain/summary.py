"""Summarize retained observations without collecting or persisting data."""

import logging
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from statistics import fmean
from types import MappingProxyType

from src.interfaces.portals.wan_performance.domain.calendar import CalendarPeriod
from src.interfaces.portals.wan_performance.domain.measurement import HourlyMeasurement, MeasurementIdentity

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ThresholdObservation:
    """Report sparse hourly snapshot counts without claiming measured duration."""

    metric_name: str
    threshold_percent: int
    valid_hours: int
    above_hours: int
    longest_run: int


@dataclass(frozen=True, slots=True)
class StateObservationSummary:
    """Report sampled state and adjacent-hour changes without claiming uptime."""

    valid_hours: int
    expected_hours: int
    up_hours: int
    down_hours: int
    observed_up_percent: float | None
    observed_transitions: int


@dataclass(frozen=True, slots=True)
class LinkEventSummary:
    """Aggregate source link-event minutes and transitions with explicit coverage."""

    complete_hours: int
    known_hours: int
    expected_hours: int
    up_minutes: float
    down_minutes: float
    flap_count: float
    observed_up_percent: float | None


@dataclass(frozen=True, slots=True)
class CongestionDurationSummary:
    """Aggregate complete sample-based threshold durations without filling gaps."""

    threshold_percent: int
    complete_hours: int
    expected_hours: int
    minutes: float


@dataclass(frozen=True, slots=True)
class PeriodSummary:
    """Keep period metrics, record coverage, and provenance explicit."""

    period: CalendarPeriod
    observed_hours: int
    metrics: Mapping[str, tuple[float | None, float | None, float | None, str]]
    provenance: str
    threshold_observations: tuple[ThresholdObservation, ...] = ()
    state_observations: StateObservationSummary | None = None
    link_event_summary: LinkEventSummary | None = None
    congestion_durations: tuple[CongestionDurationSummary, ...] = ()

    def __post_init__(self) -> None:
        """Prevent a consumer from changing metrics after calculation."""
        object.__setattr__(self, "metrics", MappingProxyType(dict(self.metrics)))


class SummaryValidation:
    """Refuse input combinations that would make summaries ambiguous."""

    @staticmethod
    def check(records: tuple[HourlyMeasurement, ...]) -> None:
        """Reject duplicate hours, mixed provenance, and incompatible units."""
        if len({record.natural_key for record in records}) != len(records):
            logger.error("Rejected calendar summaries with duplicate hours")
            raise ValueError("Calendar summaries cannot contain duplicate hours.")
        if len({record.provenance for record in records}) > 1:
            logger.error("Rejected calendar summaries with mixed provenance")
            raise ValueError("Calendar summaries cannot mix provenance.")
        units: dict[str, str] = {}
        for record in records:
            for name, metric in record.metrics.items():
                if name in units and units[name] != metric.unit:
                    logger.error("Rejected calendar metric %s with incompatible units", name)
                    raise ValueError("Calendar summaries cannot mix metric units.")
                units[name] = metric.unit


class CalendarSummaries:
    """Build UTC summaries from retained hourly observation records."""

    @classmethod
    def build(cls, records: tuple[HourlyMeasurement, ...], identity: MeasurementIdentity) -> tuple[PeriodSummary, ...]:
        """Summarize only one identity and preserve missing observations."""
        logger.info("Building UTC calendar summaries for %s", identity.natural_key)
        selected = tuple(record for record in records if record.identity == identity)
        SummaryValidation.check(selected)
        daily = cls._daily(selected)
        results = daily + cls._merge(daily, "weekly") + cls._merge(daily, "monthly") + cls._rolling(selected)
        results = tuple(
            replace(
                summary,
                threshold_observations=ThresholdObservations.build(selected, summary.period),
                state_observations=StateObservations.build(selected, summary.period),
                link_event_summary=LinkEventSummaries.build(selected, summary.period),
                congestion_durations=CongestionDurations.build(selected, summary.period),
            )
            for summary in results
        )
        logger.debug("Built %d calendar summaries from %d hourly records", len(results), len(selected))
        return results

    @classmethod
    def _daily(cls, records: tuple[HourlyMeasurement, ...]) -> tuple[PeriodSummary, ...]:
        """Calculate means, maxima, and observed p95 values from non-null hourly values."""
        groups: dict[CalendarPeriod, list[HourlyMeasurement]] = defaultdict(list)
        for record in records:
            groups[CalendarPeriod.containing(record.hour_start_utc, "daily")].append(record)
        summaries = []
        for period, members in sorted(groups.items(), key=lambda item: item[0].start):
            metrics = cls._observed_metrics(members)
            summaries.append(PeriodSummary(period, len(members), metrics, members[0].provenance))
        return tuple(summaries)

    @classmethod
    def _rolling(cls, records: tuple[HourlyMeasurement, ...]) -> tuple[PeriodSummary, ...]:
        """Summarize 3-hour, 12-hour, and 24-hour windows ending at the latest observation."""
        if not records:
            return ()
        end = max(record.hour_start_utc for record in records) + timedelta(hours=1)
        summaries = []
        for kind in ("rolling_3h", "rolling_12h", "rolling_24h"):
            period = CalendarPeriod.ending_at(end, kind)
            members = tuple(record for record in records if period.contains(record.hour_start_utc))
            metrics = cls._observed_metrics(members)
            summaries.append(PeriodSummary(period, len(members), metrics, members[0].provenance))
        return tuple(summaries)

    @classmethod
    def _merge(cls, daily: tuple[PeriodSummary, ...], kind: str) -> tuple[PeriodSummary, ...]:
        """Preserve source equal daily weights without claiming elapsed coverage."""
        groups: dict[CalendarPeriod, list[PeriodSummary]] = defaultdict(list)
        for summary in daily:
            groups[CalendarPeriod.containing(summary.period.start, kind)].append(summary)
        summaries = []
        for period, members in sorted(groups.items(), key=lambda item: item[0].start):
            metrics = cls._merged_metrics(members)
            hours = sum(summary.observed_hours for summary in members)
            summaries.append(PeriodSummary(period, hours, metrics, members[0].provenance))
        return tuple(summaries)

    @classmethod
    def _merged_metrics(
        cls, members: list[PeriodSummary]
    ) -> dict[str, tuple[float | None, float | None, float | None, str]]:
        """Merge daily percentiles with the source max-of-daily-p95 rule."""
        metrics = {}
        for name in sorted({name for summary in members for name in summary.metrics}):
            values = [summary.metrics[name] for summary in members if name in summary.metrics]
            metrics[name] = cls._merge_metric(values, name)
        return metrics

    @classmethod
    def _merge_metric(
        cls,
        values: list[tuple[float | None, float | None, float | None, str]],
        name: str,
    ) -> tuple[float | None, float | None, float | None, str]:
        """Merge one metric's daily means, maxima, percentiles, and unit."""
        means = [value[0] for value in values if value[0] is not None]
        maxima = [value[1] for value in values if value[1] is not None]
        percentiles = [value[2] for value in values if value[2] is not None]
        merged = cls._values(means, maxima, percentiles, name, values[0][3])
        source_p95 = round(max(percentiles), 4 if "loss" in name else 2) if percentiles else None
        return merged[0], merged[1], source_p95, merged[3]

    @classmethod
    def _observed_metrics(
        cls, members: tuple[HourlyMeasurement, ...] | list[HourlyMeasurement]
    ) -> dict[str, tuple[float | None, float | None, float | None, str]]:
        """Calculate mean, maximum, and observed p95 for retained values."""
        metrics = {}
        for name in sorted({name for record in members for name in record.metrics}):
            values = [record.metrics[name] for record in members if name in record.metrics]
            present = [float(metric.value) for metric in values if metric.value is not None]
            metrics[name] = cls._values(present, present, present, name, values[0].unit)
        return metrics

    @staticmethod
    def _values(
        means: list[float],
        maxima: list[float],
        percentiles: list[float],
        name: str,
        unit: str,
    ) -> tuple[float | None, float | None, float | None, str]:
        """Keep missing values null and apply the source metric precision."""
        precision = 4 if "loss" in name else 2
        mean = round(fmean(means), precision) if means else None
        maximum = round(max(maxima), precision) if maxima else None
        p95 = round(CalendarSummaries._p95(percentiles), precision) if percentiles else None
        return mean, maximum, p95, unit

    @staticmethod
    def _p95(values: list[float]) -> float:
        """Use the source index rule and its maximum fallback for short samples."""
        ordered = sorted(values)
        if len(ordered) < 20:
            return ordered[-1]
        return ordered[min(int(len(ordered) * 0.95), len(ordered) - 1)]


class ThresholdObservations:
    """Count source-defined thresholds only where a valid hourly observation exists."""

    @classmethod
    def build(cls, records: tuple[HourlyMeasurement, ...], period: CalendarPeriod) -> tuple[ThresholdObservation, ...]:
        """Keep missing hours separate and calculate each calendar period from raw observations."""
        logger.info("Count utilization threshold observations for %s.", period.start.isoformat())
        result = tuple(
            cls._count(name, threshold, samples)
            for name in ("rx_utilization_percent", "tx_utilization_percent")
            if (samples := cls._samples(records, period, name)) is not None
            for threshold in (70, 80, 90)
        )
        logger.debug("Counted %d directional threshold observation summaries.", len(result))
        return result

    @staticmethod
    def _samples(
        records: tuple[HourlyMeasurement, ...], period: CalendarPeriod, name: str
    ) -> dict[datetime, float | int] | None:
        """Select verified percentages without converting other units or filling unknown values."""
        matching = tuple(record for record in records if period.contains(record.hour_start_utc))
        if not any(name in record.metrics and record.metrics[name].unit == "%" for record in matching):
            return None
        return {
            record.hour_start_utc: metric.value
            for record in matching
            if (metric := record.metrics.get(name)) is not None and metric.unit == "%" and metric.value is not None
        }

    @staticmethod
    def _count(name: str, threshold: int, samples: dict[datetime, float | int]) -> ThresholdObservation:
        """Break a run at every unknown, absent, or non-exceeding hour."""
        above = sorted(instant for instant, value in samples.items() if value > threshold)
        previous = None
        longest = run = 0
        for instant in above:
            run = run + 1 if previous is not None and instant - previous == timedelta(hours=1) else 1
            longest, previous = max(longest, run), instant
        return ThresholdObservation(name, threshold, len(samples), len(above), longest)


class StateObservations:
    """Summarize observed link states while exposing incomplete coverage."""

    @classmethod
    def build(cls, records: tuple[HourlyMeasurement, ...], period: CalendarPeriod) -> StateObservationSummary | None:
        """Count known states and changes between directly adjacent observed hours."""
        matching = tuple(
            sorted(
                (record for record in records if period.contains(record.hour_start_utc)),
                key=lambda record: record.hour_start_utc,
            )
        )
        if not any(record.is_up_observation is not None for record in matching):
            return None
        known = tuple(record for record in matching if record.is_up_observation is not None)
        transitions = cls._transitions(known)
        up_hours = sum(record.is_up_observation is True for record in known)
        percent = round(up_hours / len(known) * 100, 2) if known else None
        return StateObservationSummary(
            valid_hours=len(known),
            expected_hours=period.expected_hours,
            up_hours=up_hours,
            down_hours=len(known) - up_hours,
            observed_up_percent=percent,
            observed_transitions=transitions,
        )

    @staticmethod
    def _transitions(records: tuple[HourlyMeasurement, ...]) -> int:
        """Count only status changes across consecutive known hourly observations."""
        count = 0
        previous = None
        for record in records:
            current = record.is_up_observation
            if (
                previous is not None
                and current is not None
                and record.hour_start_utc - previous.hour_start_utc == timedelta(hours=1)
                and current != previous.is_up_observation
            ):
                count += 1
            previous = record if current is not None else None
        return count


class LinkEventSummaries:
    """Aggregate event-derived availability and flaps over retained port hours."""

    @staticmethod
    def build(records: tuple[HourlyMeasurement, ...], period: CalendarPeriod) -> LinkEventSummary | None:
        """Sum only complete event searches and retain unknown minutes as uncovered."""
        matching = tuple(record for record in records if period.contains(record.hour_start_utc))
        if not LinkEventSummaries._has_events(matching):
            return None
        complete = LinkEventSummaries._complete(matching)
        known = LinkEventSummaries._known(complete)
        up = LinkEventSummaries._sum(known, "up_minutes")
        down = LinkEventSummaries._sum(known, "down_minutes")
        flaps = LinkEventSummaries._flaps(complete)
        observed = LinkEventSummaries._observed_percent(up, down)
        return LinkEventSummary(len(complete), len(known), period.expected_hours, up, down, flaps, observed)

    @staticmethod
    def _has_events(records: tuple[HourlyMeasurement, ...]) -> bool:
        """Check whether the period contains any event-search result."""
        return any("flap_count" in record.metrics for record in records)

    @staticmethod
    def _complete(records: tuple[HourlyMeasurement, ...]) -> tuple[HourlyMeasurement, ...]:
        """Keep hours with a completed event search, including known zero-event hours."""
        return tuple(record for record in records if record.metrics["flap_count"].value is not None)

    @classmethod
    def _known(cls, records: tuple[HourlyMeasurement, ...]) -> tuple[HourlyMeasurement, ...]:
        """Keep hours with both up and down duration measurements."""
        return tuple(
            record
            for record in records
            if cls._value(record, "up_minutes") is not None and cls._value(record, "down_minutes") is not None
        )

    @staticmethod
    def _value(record: HourlyMeasurement, name: str) -> float | None:
        """Return only explicit status values without replacing unknown minutes with zero."""
        metric = record.metrics.get(name)
        return float(metric.value) if metric is not None and metric.value is not None else None

    @classmethod
    def _sum(cls, records: tuple[HourlyMeasurement, ...], name: str) -> float:
        """Add known status minutes and exclude incomplete state windows."""
        return sum(value for record in records if (value := cls._value(record, name)) is not None)

    @staticmethod
    def _flaps(records: tuple[HourlyMeasurement, ...]) -> float:
        """Sum the flap counts from completed event searches."""
        return sum(
            value for record in records if (value := LinkEventSummaries._value(record, "flap_count")) is not None
        )

    @staticmethod
    def _observed_percent(up: float, down: float) -> float | None:
        """Calculate observed availability only when event durations cover time."""
        return round(up / (up + down) * 100, 2) if up + down else None


class CongestionDurations:
    """Sum ten-minute utilization occupancy only for complete sample windows."""

    @classmethod
    def build(
        cls, records: tuple[HourlyMeasurement, ...], period: CalendarPeriod
    ) -> tuple[CongestionDurationSummary, ...]:
        """Report complete hours for each threshold and leave missing hours uncovered."""
        matching = tuple(record for record in records if period.contains(record.hour_start_utc))
        return tuple(
            cls._threshold(matching, period, threshold)
            for threshold in (70, 80, 90)
            if any(cls._name(threshold) in record.metrics for record in matching)
        )

    @classmethod
    def _threshold(
        cls, records: tuple[HourlyMeasurement, ...], period: CalendarPeriod, threshold: int
    ) -> CongestionDurationSummary:
        """Sum one threshold duration over complete six-sample hours."""
        name = cls._name(threshold)
        values = tuple(
            metric.value
            for record in records
            if (metric := record.metrics.get(name)) is not None
            and metric.value is not None
            and metric.coverage_fraction == 1.0
        )
        return CongestionDurationSummary(
            threshold,
            len(values),
            period.expected_hours,
            sum(float(value) for value in values),
        )

    @staticmethod
    def _name(threshold: int) -> str:
        """Use one canonical key for persisted threshold-duration metrics."""
        return f"congestion_minutes_over_{threshold}_pct"
