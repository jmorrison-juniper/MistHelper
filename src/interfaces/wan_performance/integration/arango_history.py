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
from src.interfaces.wan_performance.domain.calendar import MAX_HISTORY_RECORDS, MAX_HISTORY_WINDOW_DAYS
from src.interfaces.wan_performance.domain.measurement import (
    HourlyMeasurement,
    MeasurementIdentity,
    SampleMeasurement,
)
from src.interfaces.wan_performance.integration.record_codec import RecordCodec, SampleRecordCodec

logger = logging.getLogger(__name__)
HOURS_COLLECTION = "wan_performance_hours"
SAMPLES_COLLECTION = "wan_performance_samples"


class ArangoHistory:
    """Keep atomic WAN upserts in one configured database, without a mirror."""

    def __init__(self, database: StandardDatabase) -> None:
        """Accept a public database boundary so tests need no running service."""
        self.database = database

    @classmethod
    def connect(cls, config: DatabaseConfig) -> ArangoHistory:
        """Reuse application connection settings with a finite request timeout."""
        if config.standalone_mode:
            raise ConnectionError("WAN history is unavailable in CSV-only mode.")
        logger.info("Connect WAN history to the configured ArangoDB database.")
        client = ArangoClient(hosts=config.arango_host, request_timeout=2)
        database = client.db(config.arango_database, username=config.arango_username, password=config.arango_password)
        for collection_name in (HOURS_COLLECTION, SAMPLES_COLLECTION):
            if not database.has_collection(collection_name):
                database.create_collection(collection_name)
        logger.debug("WAN hourly and raw sample collections are available.")
        return cls(database)

    def upsert(self, records: tuple[HourlyMeasurement, ...], samples: tuple[SampleMeasurement, ...] = ()) -> None:
        """Validate both batches before atomic hourly replacements and sample appends."""
        documents = [
            {
                "_key": hashlib.sha256(json.dumps(record.natural_key).encode()).hexdigest(),
                "identity": json.dumps(record.identity.natural_key),
                "hour": record.hour_start_utc.isoformat(),
                "payload": RecordCodec.encode(record),
            }
            for record in records
        ]
        sample_documents = [
            {
                "_key": hashlib.sha256(json.dumps(sample.natural_key).encode()).hexdigest(),
                "identity": json.dumps(sample.identity.natural_key),
                "sampled_at": sample.sampled_at_utc.isoformat(),
                "payload": SampleRecordCodec.encode(sample),
            }
            for sample in samples
        ]
        logger.info(
            "Write %d hourly records and %d raw samples to the configured ArangoDB store.",
            len(documents),
            len(sample_documents),
        )
        transaction = self.database.begin_transaction(write=[HOURS_COLLECTION, SAMPLES_COLLECTION])
        try:
            for document in documents:
                transaction.collection(HOURS_COLLECTION).insert(document, overwrite=True, overwrite_mode="replace")
            for document in sample_documents:
                transaction.collection(SAMPLES_COLLECTION).insert(document)
            transaction.commit_transaction()
        except (ArangoError, OSError) as error:
            transaction.abort_transaction()
            logger.exception("WAN ArangoDB history transaction failed: %s.", error)
            raise
        logger.debug("Committed %d hourly records and %d raw samples.", len(documents), len(sample_documents))

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
                "@collection": HOURS_COLLECTION,
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

    def read_samples(
        self, identity: MeasurementIdentity, start: datetime, end: datetime
    ) -> tuple[SampleMeasurement, ...]:
        """Read timestamped samples without silently truncating the fixed result cap."""
        if any(value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value) for value in (start, end)):
            raise ValueError("History window must use UTC.")
        if not 0 < (end - start).total_seconds() <= MAX_HISTORY_WINDOW_DAYS * 86400:
            raise ValueError(f"History window must span more than zero and at most {MAX_HISTORY_WINDOW_DAYS} days.")
        logger.info("Read WAN raw samples from the configured ArangoDB store.")
        cursor = self.database.aql.execute(
            "FOR record IN @@collection FILTER record.identity == @identity "
            "AND record.sampled_at >= @start AND record.sampled_at < @end "
            "SORT record.sampled_at LIMIT @limit RETURN record.payload",
            bind_vars={
                "@collection": SAMPLES_COLLECTION,
                "identity": json.dumps(identity.natural_key),
                "start": start.isoformat(),
                "end": end.isoformat(),
                "limit": cast(Number, MAX_HISTORY_RECORDS + 1),
            },
        )
        if not isinstance(cursor, Cursor):
            raise TypeError("WAN raw history requires a synchronous ArangoDB cursor.")
        try:
            payloads = tuple(cursor)
            if len(payloads) > MAX_HISTORY_RECORDS:
                raise ValueError("WAN raw sample result exceeds the fixed history record limit.")
            samples = tuple(SampleRecordCodec.decode(payload) for payload in payloads)
        finally:
            cursor.close()
        logger.debug("Read %d WAN raw samples.", len(samples))
        return samples
