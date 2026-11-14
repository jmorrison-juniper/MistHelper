"""Read and upsert WAN measurements in the already configured SQLite database."""

import json
import logging
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

from src.interfaces.wan_performance.domain.calendar import MAX_HISTORY_RECORDS, MAX_HISTORY_WINDOW_DAYS
from src.interfaces.wan_performance.domain.measurement import (
    HourlyMeasurement,
    MeasurementIdentity,
    SampleMeasurement,
)
from src.interfaces.wan_performance.integration.record_codec import (
    ArchiveCodec,
    DeclarationCodec,
    RecordCodec,
    SampleRecordCodec,
    SampleReplayPolicy,
)

logger = logging.getLogger(__name__)


class ProjectionReplay:
    """Validate immutable archive projection decisions independently of either datastore."""

    @staticmethod
    def requires_new(previous: object, document: dict[str, str]) -> bool:
        """Reject invalid stored metadata or changed payloads before accepting replay or a new key."""
        if previous is None:
            return True
        if not isinstance(previous, dict) or any(
            previous.get(name) != document[name] for name in ("_key", "identity", "hour")
        ):
            raise ValueError("Existing archive row metadata conflicts with its requested identity and hour.")
        payload = previous.get("payload")
        if not isinstance(payload, str):
            raise ValueError("An existing archive row has an invalid payload.")
        value = ArchiveCodec._json(payload.encode())
        if not isinstance(value, dict):
            raise ValueError("An existing archive payload must be an object.")
        ArchiveCodec._record(value, DeclarationCodec.identity(value["identity"]), value["provenance"])
        if json.dumps(value, sort_keys=True, allow_nan=False) != document["payload"]:
            raise ValueError("Archive projection conflicts with an existing full-identity hour.")
        return False


class SQLiteArchive:
    """Append reviewed projection documents without creating schema or replacing existing rows."""

    @classmethod
    def append(cls, repository: SQLiteHistory, documents: tuple[dict[str, str], ...]) -> int:
        """Commit all new rows in one existing-file transaction or surface an unconfirmed commit."""
        logger.info("Append WAN projections under an existing SQLite write transaction.")
        try:
            with closing(repository._connect()) as connection, connection:
                connection.execute("BEGIN IMMEDIATE")
                additions = cls._new_rows(connection, documents)
                connection.executemany(
                    "INSERT INTO wan_performance_hours (identity,hour,payload) VALUES (?, ?, ?)", additions
                )
        except (sqlite3.Error, ValueError, TypeError, KeyError, OSError):
            logger.exception("WAN SQLite archive append did not confirm a commit.")
            raise
        logger.debug("Committed %s new projection records without replacement.", len(additions))
        return len(additions)

    @staticmethod
    def _new_rows(connection: sqlite3.Connection, documents: tuple[dict[str, str], ...]) -> list[tuple[str, str, str]]:
        """Inspect exact existing keys before any insert so one conflict rejects the full batch."""
        logger.info("Inspect exact SQLite archive replay keys.")
        additions = []
        for document in documents:
            row = connection.execute(
                "SELECT identity,hour,payload FROM wan_performance_hours WHERE identity=? AND hour=?",
                (document["identity"], document["hour"]),
            ).fetchone()
            previous = (
                {**dict(zip(("identity", "hour", "payload"), row, strict=True)), "_key": document["_key"]}
                if row is not None
                else None
            )
            if ProjectionReplay.requires_new(previous, document):
                additions.append((document["identity"], document["hour"], document["payload"]))
        logger.debug("Checked %s requested rows and selected %s new rows.", len(documents), len(additions))
        return additions


class SQLiteHistory:
    """Use one existing database and a transaction for each bounded history batch."""

    def __init__(self, path: Path) -> None:
        """Keep the selected application path without creating another database."""
        self.path = path.resolve()

    def _connect(self) -> sqlite3.Connection:
        """Require an existing file and keep SQLite lock waits finite."""
        return sqlite3.connect(f"{self.path.as_uri()}?mode=rw", uri=True, timeout=2)

    def upsert(self, records: tuple[HourlyMeasurement, ...], samples: tuple[SampleMeasurement, ...] = ()) -> None:
        """Validate both batches before atomic hourly updates and sample appends."""
        try:
            rows = [
                (
                    json.dumps(record.identity.natural_key),
                    record.hour_start_utc.isoformat(),
                    RecordCodec.encode(record),
                )
                for record in records
            ]
            unique_samples = SampleReplayPolicy.unique(samples)
            sample_rows = [
                (
                    json.dumps(sample.identity.natural_key),
                    sample.sampled_at_utc.isoformat(),
                    SampleRecordCodec.encode(sample),
                )
                for sample in unique_samples
            ]
            logger.info("Write %d hourly records and check %d raw sample replays.", len(rows), len(sample_rows))
            with closing(self._connect()) as connection, connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    "CREATE TABLE IF NOT EXISTS wan_performance_hours "
                    "(identity TEXT NOT NULL, hour TEXT NOT NULL, payload TEXT NOT NULL, PRIMARY KEY(identity, hour))"
                )
                connection.execute(
                    "CREATE TABLE IF NOT EXISTS wan_performance_samples "
                    "(identity TEXT NOT NULL, sampled_at TEXT NOT NULL, payload TEXT NOT NULL, "
                    "PRIMARY KEY(identity, sampled_at))"
                )
                samples_to_insert = []
                for sample, row in zip(unique_samples, sample_rows, strict=True):
                    existing = connection.execute(
                        "SELECT payload FROM wan_performance_samples WHERE identity=? AND sampled_at=?",
                        row[:2],
                    ).fetchone()
                    if existing is None:
                        samples_to_insert.append(row)
                    else:
                        SampleReplayPolicy.validate_existing(existing[0], sample)
                connection.executemany(
                    "INSERT INTO wan_performance_hours VALUES (?, ?, ?) "
                    "ON CONFLICT(identity,hour) DO UPDATE SET payload=excluded.payload",
                    rows,
                )
                connection.executemany(
                    "INSERT INTO wan_performance_samples VALUES (?, ?, ?)",
                    samples_to_insert,
                )
        except (sqlite3.Error, ValueError, TypeError, KeyError):
            logger.exception("WAN SQLite history write failed.")
            raise
        logger.debug("Committed %d hourly records and checked %d raw samples.", len(rows), len(sample_rows))

    def read(self, identity: MeasurementIdentity, start: datetime, end: datetime) -> tuple[HourlyMeasurement, ...]:
        """Read one identity in a half-open UTC window, bounded to thirteen months."""
        if any(value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value) for value in (start, end)):
            raise ValueError("History window must use UTC.")
        if not 0 < (end - start).total_seconds() <= MAX_HISTORY_WINDOW_DAYS * 86400:
            raise ValueError(f"History window must span more than zero and at most {MAX_HISTORY_WINDOW_DAYS} days.")
        logger.info("Read WAN history in a bounded UTC window.")
        try:
            with closing(self._connect()) as connection:
                exists = connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='wan_performance_hours'"
                ).fetchone()
                if exists is None:
                    return ()
                rows = connection.execute(
                    "SELECT payload FROM wan_performance_hours WHERE identity=? AND hour>=? AND hour<? "
                    "ORDER BY hour LIMIT ?",
                    (json.dumps(identity.natural_key), start.isoformat(), end.isoformat(), MAX_HISTORY_RECORDS),
                ).fetchall()
                records = tuple(RecordCodec.decode(row[0]) for row in rows)
        except (sqlite3.Error, ValueError, KeyError, TypeError):
            logger.exception("WAN SQLite history read failed.")
            raise
        logger.debug("Read %d WAN history records.", len(records))
        return records

    def read_samples(
        self, identity: MeasurementIdentity, start: datetime, end: datetime
    ) -> tuple[SampleMeasurement, ...]:
        """Read exact samples without truncating a result above the fixed cap."""
        if any(value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value) for value in (start, end)):
            raise ValueError("History window must use UTC.")
        if not 0 < (end - start).total_seconds() <= MAX_HISTORY_WINDOW_DAYS * 86400:
            raise ValueError(f"History window must span more than zero and at most {MAX_HISTORY_WINDOW_DAYS} days.")
        logger.info("Read WAN raw samples in a bounded UTC window.")
        try:
            with closing(self._connect()) as connection:
                exists = connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='wan_performance_samples'"
                ).fetchone()
                if exists is None:
                    return ()
                rows = connection.execute(
                    "SELECT payload FROM wan_performance_samples WHERE identity=? AND sampled_at>=? AND sampled_at<? "
                    "ORDER BY sampled_at LIMIT ?",
                    (
                        json.dumps(identity.natural_key),
                        start.isoformat(),
                        end.isoformat(),
                        MAX_HISTORY_RECORDS + 1,
                    ),
                ).fetchall()
                if len(rows) > MAX_HISTORY_RECORDS:
                    raise ValueError("WAN raw sample result exceeds the fixed history record limit.")
                samples = tuple(SampleRecordCodec.decode(row[0]) for row in rows)
        except (sqlite3.Error, ValueError, KeyError, TypeError):
            logger.exception("WAN SQLite raw sample read failed.")
            raise
        logger.debug("Read %d WAN raw samples.", len(samples))
        return samples
