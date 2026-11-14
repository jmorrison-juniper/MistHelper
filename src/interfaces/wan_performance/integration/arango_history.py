"""Use an isolated collection in the configured application ArangoDB database."""

import hashlib
import json
import logging
from datetime import UTC, datetime
from numbers import Number
from typing import cast

from arango.client import ArangoClient
from arango.cursor import Cursor
from arango.database import StandardDatabase, TransactionDatabase
from arango.exceptions import ArangoError

from src.foundation.persistence.db import DatabaseConfig
from src.interfaces.wan_performance.domain.calendar import MAX_HISTORY_RECORDS, MAX_HISTORY_WINDOW_DAYS
from src.interfaces.wan_performance.domain.measurement import (
    HourlyMeasurement,
    MeasurementIdentity,
    SampleMeasurement,
)
from src.interfaces.wan_performance.integration.record_codec import RecordCodec, SampleRecordCodec, SampleReplayPolicy
from src.interfaces.wan_performance.integration.sqlite_history import ProjectionReplay

logger = logging.getLogger(__name__)
HOURS_COLLECTION = "wan_performance_hours"
SAMPLES_COLLECTION = "wan_performance_samples"


class ArangoArchive:
    """Append scoped projection documents with bounded inspection and explicit transaction acknowledgments."""

    @classmethod
    def append(cls, repository: ArangoHistory, documents: tuple[dict[str, str], ...]) -> int:
        """Require every key and commit acknowledgment before reporting an atomic append."""
        logger.info("Append WAN projections in one bounded Arango transaction.")
        transaction = repository.database.begin_transaction(
            write=[HOURS_COLLECTION], lock_timeout=2, max_size=64 * 1024 * 1024, allow_implicit=False
        )
        try:
            additions = cls._inspect(transaction, documents)
            cls._insert(transaction, additions)
        except (ArangoError, ValueError, TypeError, KeyError, OSError):
            logger.exception("WAN Arango archive append did not confirm a commit.")
            cls._abort(transaction)
            raise
        logger.debug("Committed %s new projection records without replacement.", len(additions))
        return len(additions)

    @staticmethod
    def _inspect(transaction: TransactionDatabase, documents: tuple[dict[str, str], ...]) -> list[dict[str, str]]:
        """Read only requested keys and reject incomplete, invalid, or conflicting replay results."""
        logger.info("Inspect exact Arango archive replay keys.")
        cursor = transaction.aql.execute(
            "FOR key IN @keys RETURN DOCUMENT(@@collection, key)",
            bind_vars={"@collection": HOURS_COLLECTION, "keys": [document["_key"] for document in documents]},
        )
        if not isinstance(cursor, Cursor):
            raise TypeError("Archive replay inspection requires a synchronous bounded Arango cursor.")
        additions = []
        try:
            for document, previous in zip(documents, cursor, strict=True):
                if ProjectionReplay.requires_new(previous, document):
                    additions.append(document)
        finally:
            cursor.close()
        logger.debug("Checked %s requested keys and selected %s new documents.", len(documents), len(additions))
        return additions

    @classmethod
    def _insert(cls, transaction: TransactionDatabase, additions: list[dict[str, str]]) -> None:
        """Request one non-overwriting bulk append and validate its receipts before commit."""
        logger.info("Append %s new Arango projection documents without replacement.", len(additions))
        receipts = (
            transaction.collection(HOURS_COLLECTION).insert_many(
                additions, overwrite=False, raise_on_document_error=True
            )
            if additions
            else []
        )
        cls._finish(transaction, additions, receipts)
        logger.debug("Confirmed the bulk append and commit for %s new documents.", len(additions))

    @staticmethod
    def _finish(transaction: TransactionDatabase, additions: list[dict[str, str]], receipts: object) -> None:
        """Validate acknowledgment cardinality, exact keys, error flags, and confirmed commit status."""
        if not isinstance(receipts, list):
            raise TypeError("Archive append requires complete synchronous document acknowledgments.")
        for document, receipt in zip(additions, receipts, strict=True):
            if (
                not isinstance(receipt, dict)
                or receipt.get("_key") != document["_key"]
                or receipt.get("error", False) is not False
            ):
                raise ValueError("Archive append acknowledgment does not match its requested key.")
        if transaction.commit_transaction() is not True:
            raise ConnectionError("Archive append did not confirm its transaction commit.")

    @staticmethod
    def _abort(transaction: TransactionDatabase) -> None:
        """Attempt cleanup without hiding the original failure or asserting an unconfirmed rollback."""
        logger.info("Abort the unconfirmed Arango archive transaction.")
        try:
            if transaction.abort_transaction() is not True:
                logger.error("WAN Arango archive rollback did not confirm its result.")
            else:
                logger.debug("Confirmed the Arango archive transaction abort.")
        except (ArangoError, OSError):
            logger.exception("WAN Arango archive rollback could not be confirmed.")


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
        unique_samples = SampleReplayPolicy.unique(samples)
        sample_documents = [
            {
                "_key": hashlib.sha256(json.dumps(sample.natural_key).encode()).hexdigest(),
                "identity": json.dumps(sample.identity.natural_key),
                "sampled_at": sample.sampled_at_utc.isoformat(),
                "payload": SampleRecordCodec.encode(sample),
            }
            for sample in unique_samples
        ]
        logger.info(
            "Write %d hourly records and check %d raw sample replays in the configured ArangoDB store.",
            len(documents),
            len(sample_documents),
        )
        transaction = self.database.begin_transaction(write=[HOURS_COLLECTION, SAMPLES_COLLECTION])
        try:
            sample_collection = transaction.collection(SAMPLES_COLLECTION)
            samples_to_insert = []
            for document, sample in zip(sample_documents, unique_samples, strict=True):  # Match keys to source samples.
                existing = sample_collection.get(document["_key"])  # Read the stored document before a replay decision.
                if existing is None:
                    samples_to_insert.append(document)  # Keep a new source sample for the append step.
                    continue
                if not isinstance(existing, dict):  # Reject jobs that cannot prove payload equality.
                    raise TypeError("ArangoDB returned a non-document result for a WAN sample.")
                payload = existing.get("payload")  # Compare source data while excluding collection time.
                if not isinstance(payload, str):
                    raise ValueError("Stored WAN sample payload must be a string.")  # Fail closed on invalid evidence.
                SampleReplayPolicy.validate_existing(payload, sample)  # Reject changed data at the same natural key.
            for document in documents:
                transaction.collection(HOURS_COLLECTION).insert(document, overwrite=True, overwrite_mode="replace")
            for document in samples_to_insert:
                sample_collection.insert(document)
            transaction.commit_transaction()
        except (ArangoError, OSError, ValueError, TypeError, KeyError) as error:
            transaction.abort_transaction()
            logger.exception("WAN ArangoDB history transaction failed: %s.", error)
            raise
        logger.debug("Committed %d hourly records and checked %d raw samples.", len(documents), len(sample_documents))

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
