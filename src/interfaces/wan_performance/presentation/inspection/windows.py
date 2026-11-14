"""Show bounded retained hourly observations without inventing temporal coverage or aggregation."""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from fractions import Fraction

from flask import abort, request

from src.interfaces.wan_performance.domain.measurement import HourlyMeasurement, MeasurementIdentity
from src.interfaces.wan_performance.integration.history_repository import HistoryRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ObservationWindow:
    """Define an independent half-open UTC view interval, not a measured duration."""

    key: str
    start: datetime
    end: datetime

    @classmethod
    def select(cls, key: str, instant: datetime) -> ObservationWindow | None:
        """Allow only documented destination view choices ending before the current hour."""
        window_hours = {"6h": 6, "12h": 12, "24h": 24, "7d": 168}
        if not key:
            return None
        if key not in window_hours:
            raise ValueError("Select a retained window of 6h, 12h, 24h, or 7d.")
        if instant.tzinfo is None or instant.utcoffset() != timedelta(0):
            raise ValueError("The retained window reference must use UTC.")
        end = instant.replace(minute=0, second=0, microsecond=0)
        return cls(key, end - timedelta(hours=window_hours[key]), end)

    @property
    def expected_hours(self) -> int:
        """Count expected hour buckets without implying complete measurements."""
        return int((self.end - self.start).total_seconds() // 3600)

    @classmethod
    def from_request(cls) -> ObservationWindow | None:
        """Reject unsupported controls before accessing any store."""
        try:
            return cls.select(request.args.get("window", ""), datetime.now(UTC))
        except ValueError as failure:
            logger.error("Rejected retained observation window: %s", failure)
            abort(400, description=str(failure))


@dataclass(frozen=True)
class RetainedWindow:
    """Keep retained rows, missing buckets, and unavailable reads distinct."""

    window: ObservationWindow
    records: tuple[HourlyMeasurement, ...] = ()
    error: str | None = None

    @classmethod
    def read(
        cls, history: HistoryRepository | None, identity: MeasurementIdentity | None, window: ObservationWindow
    ) -> RetainedWindow:
        """Read one exact identity once, without raw-sample or calendar aggregation."""
        if identity is None:
            return cls(window, error="Select exactly one full detail identity to read retained observations.")
        if history is None:
            return cls(
                window, error="Retained observations are unavailable. The selected history store is not available."
            )
        logger.info("Read retained WAN observations for the selected %s window.", window.key)
        records = history.read(identity, window.start, window.end)
        cls._validate(records, identity, window)
        records = tuple(sorted(records, key=lambda record: record.hour_start_utc))
        logger.debug("Read %s retained records across %s expected hour buckets.", len(records), window.expected_hours)
        return cls(window, records)

    @staticmethod
    def _validate(
        records: tuple[HourlyMeasurement, ...], identity: MeasurementIdentity, window: ObservationWindow
    ) -> None:
        """Fail closed on foreign, duplicated, synthetic, or out-of-window history."""
        if len(records) > window.expected_hours:
            raise ValueError("The retained result exceeds the expected hour-bucket bound.")
        if len({record.natural_key for record in records}) != len(records):
            raise ValueError("The retained result contains duplicate hours.")
        for record in records:
            if record.identity != identity or record.provenance != "live":
                raise ValueError("The retained result has a foreign identity or non-live provenance.")
            if not window.start <= record.hour_start_utc < window.end:
                raise ValueError("The retained result contains an out-of-window hour.")

    @property
    def missing_hours(self) -> int | None:
        """Report absent retained hour keys, not unknown metric or elapsed duration."""
        return None if self.error else self.window.expected_hours - len(self.records)


@dataclass(frozen=True)
class RetainedPlot:
    """Keep independently positioned points separate by retained metric and unit."""

    name: str
    unit: str
    points: tuple[tuple[float, float, str, float | int, str], ...]

    @classmethod
    def build(cls, retained: RetainedWindow | None) -> tuple[RetainedPlot, ...]:
        """Plot present projections without filling gaps or changing stored values."""
        if retained is None or retained.error or not retained.records:
            return ()
        logger.info("Build discrete retained WAN observation plots.")
        groups: dict[tuple[str, str], list[tuple[HourlyMeasurement, float | int]]] = {}
        for record in retained.records:
            for name, metric in record.metrics.items():
                if metric.value is not None:
                    groups.setdefault((name, metric.unit), []).append((record, metric.value))
        plots = tuple(
            cls(name, unit, cls._coordinates(records, retained.window))
            for (name, unit), records in sorted(groups.items())
        )
        logger.debug(
            "Built %s retained plots with %s present points.", len(plots), sum(len(plot.points) for plot in plots)
        )
        return plots

    @staticmethod
    def _coordinates(
        records: list[tuple[HourlyMeasurement, float | int]], window: ObservationWindow
    ) -> tuple[tuple[float, float, str, float | int, str], ...]:
        """Use UTC bucket offsets and finite visual bounds, including extreme values."""
        values = tuple(Decimal(str(value)) for _, value in records)
        lower = min(values)
        span = max(values) - lower
        seconds = (window.end - window.start).total_seconds()
        return tuple(
            (
                32 + (record.hour_start_utc - window.start).total_seconds() * 588 / seconds,
                165 - 130 * float((Decimal(str(value)) - lower) / span) if span else 100,
                record.hour_start_utc.isoformat(),
                value,
                record.collected_at_utc.isoformat(),
            )
            for record, value in records
        )


class ObservationStatistics:
    """Apply the independent version-one policy only to present retained projections."""

    @classmethod
    def build(cls, plots: tuple[RetainedPlot, ...], threshold: int) -> tuple[dict[str, str | int | float | None], ...]:
        """Keep exact metric/unit groups and full-window counts separate from source statistics."""
        logger.info("Build version-one WAN hourly-projection observation statistics.")
        rows = tuple(cls._row(plot, threshold) for plot in plots)
        logger.debug("Built %s hourly-projection statistic rows.", len(rows))
        return rows

    @classmethod
    def _row(cls, plot: RetainedPlot, threshold: int) -> dict[str, str | int | float | None]:
        """Use one weight per present value and select an original nearest-rank percentile."""
        values = sorted(point[3] for point in plot.points)
        above, longest = cls._runs(plot, threshold) if plot.unit in {"%", "percent"} else (None, None)
        return {
            "name": plot.name,
            "unit": plot.unit,
            "count": len(values),
            "minimum": values[0],
            "mean": cls._mean(values),
            "p95": values[(95 * len(values) + 99) // 100 - 1],
            "maximum": values[-1],
            "above": above,
            "longest": longest,
        }

    @staticmethod
    def _mean(values: list[float | int]) -> str:
        """Avoid overflow and cancellation before rounding the derived display value."""
        mean = sum((Fraction(str(value)) for value in values), Fraction()) / len(values)
        with localcontext(Context(prec=28, rounding=ROUND_HALF_EVEN)):
            return str((Decimal(mean.numerator) / Decimal(mean.denominator)).normalize())

    @staticmethod
    def _runs(plot: RetainedPlot, threshold: int) -> tuple[int, int]:
        """Count adjacent observed UTC hour keys without extending through a missing point."""
        count, longest, current = 0, 0, 0
        previous: datetime | None = None
        for point in sorted(plot.points, key=lambda point: point[2]):
            hour = datetime.fromisoformat(point[2])
            if point[3] > threshold:
                current = current + 1 if previous is not None and hour - previous == timedelta(hours=1) else 1
                count += 1
                longest = max(longest, current)
            else:
                current = 0
            previous = hour
        return count, longest

    @staticmethod
    def from_request() -> int:
        """Reject malformed percentage controls before reading any cache or history."""
        text = request.args.get("observation_threshold", "80")
        if not text.isascii() or not text.isdecimal() or len(text) > 3 or int(text) > 100:
            message = "The observation threshold must be an integer from 0 through 100."
            logger.error("Rejected WAN observation threshold: %s", message)
            abort(400, description=message)
        return int(text)
