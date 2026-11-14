"""Show bounded retained hourly observations without inventing temporal coverage or aggregation."""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from flask import abort, request

from src.interfaces.wan_performance.domain.measurement import HourlyMeasurement, MeasurementIdentity
from src.interfaces.wan_performance.integration.history_repository import HistoryRepository

logger = logging.getLogger(__name__)
WINDOW_HOURS = {"6h": 6, "12h": 12, "24h": 24, "7d": 168}


@dataclass(frozen=True)
class ObservationWindow:
    """Define an independent half-open UTC view interval, not a measured duration."""

    key: str
    start: datetime
    end: datetime

    @classmethod
    def select(cls, key: str, instant: datetime) -> ObservationWindow | None:
        """Allow only documented destination view choices ending before the current hour."""
        if not key:
            return None
        if key not in WINDOW_HOURS:
            raise ValueError("Select a retained window of 6h, 12h, 24h, or 7d.")
        if instant.tzinfo is None or instant.utcoffset() != timedelta(0):
            raise ValueError("The retained window reference must use UTC.")
        end = instant.replace(minute=0, second=0, microsecond=0)
        return cls(key, end - timedelta(hours=WINDOW_HOURS[key]), end)

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
