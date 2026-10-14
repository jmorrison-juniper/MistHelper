"""Summarize isolated hourly records without collecting or persisting data."""

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
class PeriodSummary:
    """Keep calendar metrics, record coverage, and provenance explicit."""

    period: CalendarPeriod
    observed_hours: int
    metrics: Mapping[str, tuple[float | None, float | None, str]]
    provenance: str
    threshold_observations: tuple[ThresholdObservation, ...] = ()

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
    """Build daily summaries and source-compatible calendar summaries."""

    @classmethod
    def build(cls, records: tuple[HourlyMeasurement, ...], identity: MeasurementIdentity) -> tuple[PeriodSummary, ...]:
        """Summarize only one identity and preserve missing observations."""
        logger.info("Building UTC calendar summaries for %s", identity.natural_key)
        selected = tuple(record for record in records if record.identity == identity)
        SummaryValidation.check(selected)
        daily = cls._daily(selected)
        results = daily + cls._merge(daily, "weekly") + cls._merge(daily, "monthly")
        results = tuple(
            replace(summary, threshold_observations=ThresholdObservations.build(selected, summary.period))
            for summary in results
        )
        logger.debug("Built %d calendar summaries from %d hourly records", len(results), len(selected))
        return results

    @classmethod
    def _daily(cls, records: tuple[HourlyMeasurement, ...]) -> tuple[PeriodSummary, ...]:
        """Calculate means and maxima from non-null hourly values."""
        groups: dict[CalendarPeriod, list[HourlyMeasurement]] = defaultdict(list)
        for record in records:
            groups[CalendarPeriod.containing(record.hour_start_utc, "daily")].append(record)
        summaries = []
        for period, members in sorted(groups.items(), key=lambda item: item[0].start):
            metrics = {}
            for name in sorted({name for record in members for name in record.metrics}):
                values = [record.metrics[name] for record in members if name in record.metrics]
                present = [float(metric.value) for metric in values if metric.value is not None]
                metrics[name] = cls._values(present, present, name, values[0].unit)
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
    def _merged_metrics(cls, members: list[PeriodSummary]) -> dict[str, tuple[float | None, float | None, str]]:
        """Merge available daily means and maxima without filling missing values."""
        metrics = {}
        for name in sorted({name for summary in members for name in summary.metrics}):
            values = [summary.metrics[name] for summary in members if name in summary.metrics]
            means = [value[0] for value in values if value[0] is not None]
            maxima = [value[1] for value in values if value[1] is not None]
            metrics[name] = cls._values(means, maxima, name, values[0][2])
        return metrics

    @staticmethod
    def _values(
        means: list[float], maxima: list[float], name: str, unit: str
    ) -> tuple[float | None, float | None, str]:
        """Keep missing values null and apply the source metric precision."""
        precision = 4 if name == "packet_loss" else 2
        mean = round(fmean(means), precision) if means else None
        maximum = round(max(maxima), precision) if maxima else None
        return mean, maximum, unit


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
