"""Read and upsert WAN measurements in the already configured SQLite database."""

import json
import logging
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

from src.interfaces.portals.wan_performance.domain.calendar import MAX_HISTORY_RECORDS, MAX_HISTORY_WINDOW_DAYS
from src.interfaces.portals.wan_performance.domain.measurement import HourlyMeasurement, MeasurementIdentity
from src.interfaces.portals.wan_performance.integration.record_codec import RecordCodec

logger = logging.getLogger(__name__)


class SQLiteHistory:
    """Use one existing database and a transaction for each bounded history batch."""

    def __init__(self, path: Path) -> None:
        """Keep the selected application path without creating another database."""
        self.path = path.resolve()

    def _connect(self) -> sqlite3.Connection:
        """Require an existing file and keep SQLite lock waits finite."""
        return sqlite3.connect(f"{self.path.as_uri()}?mode=rw", uri=True, timeout=2)

    def upsert(self, records: tuple[HourlyMeasurement, ...]) -> None:
        """Validate the full batch before an atomic natural-key upsert."""
        rows = [
            (
                json.dumps(record.identity.natural_key),
                record.hour_start_utc.isoformat(),
                RecordCodec.encode(record),
            )
            for record in records
        ]
        logger.info("Write %d WAN history records to the selected SQLite store.", len(rows))
        try:
            with closing(self._connect()) as connection, connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    "CREATE TABLE IF NOT EXISTS wan_performance_hours "
                    "(identity TEXT NOT NULL, hour TEXT NOT NULL, payload TEXT NOT NULL, PRIMARY KEY(identity, hour))"
                )
                connection.executemany(
                    "INSERT INTO wan_performance_hours VALUES (?, ?, ?) "
                    "ON CONFLICT(identity,hour) DO UPDATE SET payload=excluded.payload",
                    rows,
                )
        except sqlite3.Error:
            logger.exception("WAN SQLite history write failed.")
            raise
        logger.debug("Committed %d WAN history records.", len(rows))

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
