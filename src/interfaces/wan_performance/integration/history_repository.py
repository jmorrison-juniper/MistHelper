"""Select one WAN history backend from the existing export configuration."""

import json
import logging
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Protocol

from src.foundation.persistence.db import DatabaseConfig
from src.foundation.runtime.config.source_dependency_resolver import SourceDependencyResolver
from src.interfaces.wan_performance.domain.measurement import (
    HourlyMeasurement,
    MeasurementIdentity,
    SampleMeasurement,
)
from src.interfaces.wan_performance.integration.arango_history import ArangoHistory
from src.interfaces.wan_performance.integration.record_codec import DeclarationCodec
from src.interfaces.wan_performance.integration.sqlite_history import SQLiteHistory


class OperatorDeclarations:
    """Keep append-only metadata in isolated process state, with explicit export and restart loss."""

    def __init__(self) -> None:
        """Allocate only private in-memory state and a lock for concurrent replay decisions."""
        self.entries: dict[tuple[str, str], str] = {}
        self.lock = RLock()

    def accept(self, payload: bytes, identities: tuple[MeasurementIdentity, ...], confirmation: str) -> str:
        """Validate scope and confirmation before one atomic capped append or identical replay."""
        if confirmation != "DECLARE":
            raise ValueError("Type DECLARE to retain operator metadata.")
        declaration = DeclarationCodec.decode(payload)
        identity = DeclarationCodec.identity(declaration["identity"])
        if identity not in identities:
            raise ValueError("Declaration identity is absent from the current cached tenant.")
        key = (
            declaration["identity"]["org_id"],
            json.dumps([declaration["identity"], declaration["effective"]], sort_keys=True),
        )
        encoded = json.dumps(declaration, sort_keys=True, allow_nan=False)
        logging.getLogger(__name__).info("Retain one scoped WAN operator declaration.")
        with self.lock:
            previous = self.entries.get(key)
            if previous is not None:
                if previous != encoded:
                    raise ValueError("Declaration replay conflicts with existing metadata.")
                return "Identical declaration preserved."
            if sum(entry[0] == key[0] for entry in self.entries) >= 1000:
                raise ValueError("The selected organization already has 1000 declarations.")
            self.entries[key] = encoded
        logging.getLogger(__name__).debug("Retained one operator declaration without a network or history write.")
        return "Declaration accepted."

    def export(self, org_id: str) -> bytes:
        """Export selected-organization declarations without exposing mutable internal records."""
        logging.getLogger(__name__).info("Export scoped WAN operator declarations.")
        with self.lock:
            declarations = [json.loads(value) for key, value in sorted(self.entries.items()) if key[0] == org_id]
        payload = json.dumps(
            {"version": 1, "provenance": "operator-declaration", "lifetime": "process", "declarations": declarations},
            sort_keys=True,
            allow_nan=False,
        ).encode()
        logging.getLogger(__name__).debug("Exported %s operator declarations.", len(declarations))
        return payload


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
