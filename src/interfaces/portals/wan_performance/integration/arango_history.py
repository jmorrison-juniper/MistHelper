"""Use an isolated collection in the configured application ArangoDB database."""

import hashlib
import json
import logging
from datetime import UTC, datetime
from numbers import Number
from typing import cast

from arango.client import ArangoClient
from arango.cursor import Cursor
from arango.database import StandardDatabase
from arango.exceptions import ArangoError

from src.foundation.persistence.db import DatabaseConfig
from src.interfaces.portals.wan_performance.domain.calendar import MAX_HISTORY_RECORDS, MAX_HISTORY_WINDOW_DAYS
from src.interfaces.portals.wan_performance.domain.measurement import HourlyMeasurement, MeasurementIdentity
from src.interfaces.portals.wan_performance.integration.record_codec import RecordCodec

logger = logging.getLogger(__name__)


class ArangoHistory:
    """Keep atomic WAN upserts in one configured database, without a mirror."""

    COLLECTION = "wan_performance_hours"

    def __init__(self, database: StandardDatabase) -> None:
        """Accept a public database boundary so tests need no running service."""
        self.database = database

    @classmethod
    def connect(cls, config: DatabaseConfig) -> "ArangoHistory":
        """Reuse application connection settings with a finite request timeout."""
        if config.standalone_mode:
            raise ConnectionError("WAN history is unavailable in CSV-only mode.")
        logger.info("Connect WAN history to the configured ArangoDB database.")
        client = ArangoClient(hosts=config.arango_host, request_timeout=2)
        database = client.db(config.arango_database, username=config.arango_username, password=config.arango_password)
        if not database.has_collection(cls.COLLECTION):
            database.create_collection(cls.COLLECTION)
        logger.debug("WAN history collection is available.")
        return cls(database)

    def upsert(self, records: tuple[HourlyMeasurement, ...]) -> None:
        """Validate the complete batch before atomic natural-key replacements."""
        documents = [
            {
                "_key": hashlib.sha256(json.dumps(record.natural_key).encode()).hexdigest(),
                "identity": json.dumps(record.identity.natural_key),
                "hour": record.hour_start_utc.isoformat(),
                "payload": RecordCodec.encode(record),
            }
            for record in records
        ]
        logger.info("Write %d WAN history records to the configured ArangoDB store.", len(documents))
        transaction = self.database.begin_transaction(write=[self.COLLECTION])
        try:
            for document in documents:
                transaction.collection(self.COLLECTION).insert(document, overwrite=True, overwrite_mode="replace")
            transaction.commit_transaction()
        except (ArangoError, OSError) as error:
            transaction.abort_transaction()
            logger.exception("WAN ArangoDB history transaction failed: %s.", error)
            raise
        logger.debug("Committed %d WAN history records.", len(documents))

    def read(self, identity: MeasurementIdentity, start: datetime, end: datetime) -> tuple[HourlyMeasurement, ...]:
        """Read a thirteen-month half-open UTC window through the public AQL interface."""
        if any(value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value) for value in (start, end)):
            raise ValueError("History window must use UTC.")
        if not 0 < (end - start).total_seconds() <= MAX_HISTORY_WINDOW_DAYS * 86400:
            raise ValueError(f"History window must span more than zero and at most {MAX_HISTORY_WINDOW_DAYS} days.")
        logger.info("Read WAN history from the configured ArangoDB store.")
        cursor = self.database.aql.execute(
            "FOR record IN @@collection FILTER record.identity == @identity "
            "AND record.hour >= @start AND record.hour < @end "
            "SORT record.hour LIMIT @limit RETURN record.payload",
            bind_vars={
                "@collection": self.COLLECTION,
                "identity": json.dumps(identity.natural_key),
                "start": start.isoformat(),
                "end": end.isoformat(),
                "limit": cast(Number, MAX_HISTORY_RECORDS),
            },
        )
        if not isinstance(cursor, Cursor):
            raise TypeError("WAN history requires a synchronous ArangoDB cursor.")
        try:
            records = tuple(RecordCodec.decode(payload) for payload in cursor)
        finally:
            cursor.close()
        logger.debug("Read %d WAN history records.", len(records))
        return records
