"""Select one WAN history backend from the existing export configuration."""

import hashlib
import json
import logging
from collections.abc import Callable, Mapping
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Protocol

from src.foundation.persistence.db import DatabaseConfig
from src.foundation.runtime.config.source_dependency_resolver import SourceDependencyResolver
from src.interfaces.wan_performance.domain.calendar import MAX_HISTORY_RECORDS
from src.interfaces.wan_performance.domain.measurement import (
    HourlyMeasurement,
    MeasurementIdentity,
    SampleMeasurement,
)
from src.interfaces.wan_performance.integration.arango_history import ArangoArchive, ArangoHistory
from src.interfaces.wan_performance.integration.record_codec import ArchiveCodec, DeclarationCodec, RecordCodec
from src.interfaces.wan_performance.integration.sqlite_history import SQLiteArchive, SQLiteHistory


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


class SyntheticArchiveStore:
    """Keep synthetic archives and immutable hour keys isolated from application history."""

    def __init__(self) -> None:
        """Allocate bounded in-memory archive and row namespaces without opening a datastore."""
        self.entries: dict[tuple[str, str], bytes] = {}
        self.lock = RLock()

    def accept(self, payload: bytes, identities: tuple[MeasurementIdentity, ...], confirmation: str) -> str:
        """Validate full scope and atomically retain original archive bytes with immutable synthetic rows."""
        archive = ArchiveCodec.decode(payload)
        if (
            confirmation != "IMPORT_SYNTHETIC"
            or archive["provenance"] != "synthetic"
            or archive["identity"] not in identities
        ):
            raise ValueError("Synthetic import requires IMPORT_SYNTHETIC and a current cached full identity.")
        org_id = archive["identity"].to_dict()["org_id"]
        rows = {
            (org_id, "row:" + json.dumps(record.natural_key)): json.dumps(
                record.to_dict(), sort_keys=True, allow_nan=False
            ).encode()
            for record in archive["records"]
        }
        logging.getLogger(__name__).info("Retain a scoped synthetic archive in process state.")
        digest = self._append(rows, payload, org_id)
        logging.getLogger(__name__).debug(
            "Retained %s synthetic projections without application history admission.", len(rows)
        )
        return digest

    def _append(self, rows: dict[tuple[str, str], bytes], payload: bytes, org_id: str) -> str:
        """Check all replay decisions and resource bounds before one locked state update."""
        digest = hashlib.sha256(payload).hexdigest()
        with self.lock:
            if (org_id, "archive:" + digest) in self.entries:
                logging.getLogger(__name__).debug("Preserved an identical synthetic archive.")
                return digest
            for key, value in rows.items():
                previous = self.entries.get(key)
                if previous is not None and previous != value:
                    raise ValueError("Synthetic archive hour conflicts with retained source data.")
            additions = {key: value for key, value in rows.items() if key not in self.entries}
            additions[(org_id, "archive:" + digest)] = payload
            self._bounds(additions, org_id)
            self.entries.update(additions)
        return digest

    def _bounds(self, additions: dict[tuple[str, str], bytes], org_id: str) -> None:
        """Reject state above the exact organization byte or distinct-hour cap without eviction."""
        scoped = {key: value for key, value in self.entries.items() if key[0] == org_id}
        if (
            sum(key[1].startswith("row:") for key in scoped | additions) > MAX_HISTORY_RECORDS
            or sum(map(len, (*scoped.values(), *additions.values()))) > 8 * 1024 * 1024
        ):
            raise ValueError("Synthetic organization state exceeds 9528 hours or eight MiB.")

    def export(self, org_id: str, digest: str) -> bytes:
        """Return original archive bounds and provenance only within the selected organization."""
        logging.getLogger(__name__).info("Export one scoped synthetic archive.")
        with self.lock:
            payload = self.entries.get((org_id, "archive:" + digest))
        if payload is None:
            raise ValueError("The selected synthetic archive is unavailable in this organization.")
        logging.getLogger(__name__).debug("Exported %s original synthetic archive bytes.", len(payload))
        return payload


class ArchiveImporter:
    """Admit only reviewed live bytes and atomically append without replacing existing hours."""

    def __init__(
        self, history: Callable[[], HistoryRepository | None], reviews: Mapping[tuple[str, ...], frozenset[str]]
    ) -> None:
        """Keep history acquisition lazy and snapshot trusted server-side full-identity approvals."""
        if not isinstance(reviews, Mapping):
            raise TypeError("Archive reviews require a trusted server-side identity mapping.")
        self.history, self.reviews = history, dict(reviews)

    def apply(self, payload: bytes, identities: tuple[MeasurementIdentity, ...], confirmation: str) -> str:
        """Require matching provenance, scope, confirmation, and exact-byte review before datastore acquisition."""
        archive = ArchiveCodec.decode(payload)
        if confirmation != "IMPORT" or archive["provenance"] != "live" or archive["identity"] not in identities:
            raise ValueError("Live import requires IMPORT and a current cached full identity.")
        approved = self.reviews.get(archive["identity"].natural_key, frozenset())
        if not isinstance(approved, frozenset):
            raise TypeError("Trusted archive approvals must be immutable digest sets.")
        if hashlib.sha256(payload).hexdigest() not in approved:
            raise ValueError(
                "Live import is unavailable without trusted review of these exact bytes and full identity."
            )
        documents = self._documents(archive["records"])
        repository = self.history()
        if isinstance(repository, SQLiteHistory):
            count = SQLiteArchive.append(repository, documents)
        elif isinstance(repository, ArangoHistory):
            count = ArangoArchive.append(repository, documents)
        else:
            raise ConnectionError(
                "Reviewed archive import requires an available supported synchronous history backend."
            )
        return f"Appended {count} reviewed live projection records. Source completeness remains unknown."

    @staticmethod
    def _documents(records: tuple[HourlyMeasurement, ...]) -> tuple[dict[str, str], ...]:
        """Encode reviewed live projection documents without opening the history backend."""
        logging.getLogger(__name__).info("Encode reviewed live archive projection documents.")
        documents = tuple(
            {
                "_key": hashlib.sha256(json.dumps(record.natural_key).encode()).hexdigest(),
                "identity": json.dumps(record.identity.natural_key),
                "hour": record.hour_start_utc.isoformat(),
                "payload": RecordCodec.encode(record),
            }
            for record in records
        )
        logging.getLogger(__name__).debug("Encoded %s reviewed projection documents.", len(documents))
        return documents


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
