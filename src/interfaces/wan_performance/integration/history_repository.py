"""Select one WAN history backend from the existing export configuration."""

from datetime import datetime
from pathlib import Path
from typing import Protocol

from src.foundation.persistence.db import DatabaseConfig
from src.foundation.runtime.config.source_dependency_resolver import SourceDependencyResolver
from src.interfaces.wan_performance.domain.measurement import (
    HourlyMeasurement,
    MeasurementIdentity,
    SampleMeasurement,
)
from src.interfaces.wan_performance.integration.arango_history import ArangoHistory
from src.interfaces.wan_performance.integration.sqlite_history import SQLiteHistory


class HistoryRepository(Protocol):
    """Define idempotent writes and bounded reads without exposing driver internals."""

    def upsert(self, records: tuple[HourlyMeasurement, ...], samples: tuple[SampleMeasurement, ...] = ()) -> None:
        """Write hourly projections and append-only samples in one store transaction."""

    def read(self, identity: MeasurementIdentity, start: datetime, end: datetime) -> tuple[HourlyMeasurement, ...]:
        """Read the exact identity in a bounded half-open UTC interval."""

    def read_samples(
        self, identity: MeasurementIdentity, start: datetime, end: datetime
    ) -> tuple[SampleMeasurement, ...]:
        """Read exact timestamped samples in a bounded half-open UTC interval."""


class HistorySelection:
    """Follow primary SQLite selection or the configured polyglot document store."""

    @staticmethod
    def open() -> HistoryRepository:
        """Resolve the same active output setting and SQLite path as DataExporter."""
        output_format = SourceDependencyResolver.OUTPUT_FORMAT
        if output_format not in {"sqlite", "csv"}:
            raise ValueError("WAN history requires the existing csv or sqlite output selection.")
        if output_format == "sqlite":
            return SQLiteHistory(Path(SourceDependencyResolver.DATABASE_PATH))
        return ArangoHistory.connect(DatabaseConfig.from_env())
