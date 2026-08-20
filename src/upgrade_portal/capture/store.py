"""The store that keeps an upgrade capture and an upgrade run.

Why:
    An operator reads a capture months after the upgrade, so a record must
    survive and the portal must prove that the record arrived. The exporter
    reports success for a write that reached no database, because it skips the
    database outside a container (``src/export/data_exporter.py:141``) and
    because the router returns a success envelope after a file fallback
    (``src/db/router.py:372``). This module therefore reads every key back and
    compares the schema version and the digest before it calls a write
    verified. The result also names the store that truly took the data, so an
    operator can tell a database write from a file backup.

    The store keeps every record forever. No index and no code path here
    expires a record, because the operator needs the capture long after the
    upgrade.
"""

from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from arango.client import ArangoClient

from src.dataclasses.export_backend_options import ExportBackendOptions
from src.db import DatabaseConfig
from src.export.data_exporter import DataExporter

logger = logging.getLogger(__name__)

CAPTURE_COLLECTION = "upgrade_captures"
RUN_COLLECTION = "upgrade_runs"
EDGE_COLLECTION = "capture_for_run"

CAPTURE_OPERATION = "upgradeCaptureWrite"
RUN_OPERATION = "upgradeRunWrite"

SCHEMA_VERSION = 1

STORAGE_DATABASE = "database"
STORAGE_BACKUP_FILE = "backup_file"

REASON_VERIFIED = ""
REASON_NO_KEY = "missing_key"
REASON_NO_DATABASE = "database_unreachable"
REASON_ABSENT = "document_absent"
REASON_SCHEMA = "schema_version_mismatch"
REASON_DIGEST = "digest_mismatch"

_BACKUP_SENTENCE = "The backup file under data/ holds this record."

# The digits of the size change the size of the document, so the measurement
# repeats. The value only grows, so four rounds always reach a stable number.
_SIZE_ROUNDS = 4

_MESSAGES: dict[str, str] = {
    REASON_VERIFIED: "The database holds this record. The portal read the key back and matched the digest.",
    REASON_NO_KEY: "The portal wrote nothing, because the document holds no business key.",
    REASON_NO_DATABASE: "The database is out of reach. " + _BACKUP_SENTENCE,
    REASON_ABSENT: "The write reported success, but the database does not hold the key. " + _BACKUP_SENTENCE,
    REASON_SCHEMA: "The database holds a different schema version for this key. " + _BACKUP_SENTENCE,
    REASON_DIGEST: "The database holds different content for this key. " + _BACKUP_SENTENCE,
}

_DATABASE_HANDLE: Any = None


@dataclass(frozen=True, slots=True)
class IndexPlan:
    """One persistent index that this feature owns.

    Why:
        The plan states the index table of the data model in one place, so a
        reader compares the code against the table without a search. The plan
        holds a persistent index only. It holds no index that expires a
        document, because the operator keeps every capture forever.

    Attributes:
        collection: The collection that holds the index.
        fields: The indexed fields, in order.
    """

    collection: str
    fields: tuple[str, ...]

    @property
    def name(self) -> str:
        """Return the stable name of the index.

        Why:
            A named index makes the creation idempotent. The server returns
            the index that exists when the name and the definition match, so
            a repeat start creates no second index.

        Returns:
            The index name.
        """
        return "idx_" + self.collection + "_" + "_".join(self.fields)


# The eight indexes of data-model.md lines 374 to 383. The line number of each
# row follows the row. No entry expires a document.
INDEX_PLAN: tuple[IndexPlan, ...] = (
    IndexPlan(CAPTURE_COLLECTION, ("site_id", "started_at")),  # data-model.md:376
    IndexPlan(CAPTURE_COLLECTION, ("run_id", "ordinal")),  # data-model.md:377
    IndexPlan(CAPTURE_COLLECTION, ("org_id", "started_at")),  # data-model.md:378
    IndexPlan(CAPTURE_COLLECTION, ("actor_email",)),  # data-model.md:379
    IndexPlan(RUN_COLLECTION, ("site_id", "created_at")),  # data-model.md:380
    IndexPlan(RUN_COLLECTION, ("state",)),  # data-model.md:381
    IndexPlan(RUN_COLLECTION, ("actor_email", "created_at")),  # data-model.md:382
)

# The eighth index of the table. The edge collection creates it, so the
# bootstrap confirms the index instead of creating a second one.
EDGE_INDEX_FIELDS: tuple[str, str] = ("_from", "_to")  # data-model.md:383

_COLLECTIONS: tuple[tuple[str, bool], ...] = (
    (CAPTURE_COLLECTION, False),
    (RUN_COLLECTION, False),
    (EDGE_COLLECTION, True),
)


@dataclass(frozen=True, slots=True)
class Verification:
    """The outcome of one read-back.

    Why:
        A write result alone proves nothing, so the portal needs a separate
        value that reports what the database really holds.

    Attributes:
        verified: True only when the database holds the matching document.
        reason: The machine name of the failure, or an empty string.
        stored_size_bytes: The measured size of the document that came back.
    """

    verified: bool
    reason: str
    stored_size_bytes: int


@dataclass(frozen=True, slots=True)
class StoreResult:
    """The outcome of one write, with the store that took the data.

    Why:
        The operator sees a verified badge only when the read-back succeeds.
        The result therefore carries the true store, the true size, and one
        plain sentence for the interface.

    Attributes:
        key: The document key.
        collection: The collection the portal wrote to.
        verified: True only after a matching read-back.
        storage_path: ``database`` or ``backup_file``.
        backup_written: True when the exporter wrote the backup file.
        stored_size_bytes: The measured size of the stored document.
        reason: The machine name of the failure, or an empty string.
        message: One sentence for the operator.
    """

    key: str
    collection: str
    verified: bool
    storage_path: str
    backup_written: bool
    stored_size_bytes: int
    reason: str
    message: str


@dataclass(frozen=True, slots=True)
class BootstrapReport:
    """The outcome of the collection and index bootstrap.

    Why:
        The portal logs one line at start. The report gives that line the
        facts, and a test reads the same report.

    Attributes:
        collections: The collections that are ready.
        indexes: The names of the persistent indexes that are ready.
        edge_index_present: True when the edge collection holds its edge index.
        database_available: True when the bootstrap reached the database.
    """

    collections: tuple[str, ...]
    indexes: tuple[str, ...]
    edge_index_present: bool
    database_available: bool


@dataclass(frozen=True, slots=True)
class _Target:
    """The write target for one kind of document.

    Why:
        The capture path and the run path differ in four values only. One
        small record keeps the write path single, so both kinds follow the
        same steps.

    Attributes:
        collection: The destination collection.
        operation: The registry operation name.
        key_field: The field that holds the business key.
        backup_prefix: The first part of the backup file name.
    """

    collection: str
    operation: str
    key_field: str
    backup_prefix: str


_CAPTURE_TARGET = _Target(CAPTURE_COLLECTION, CAPTURE_OPERATION, "capture_id", "upgrade_capture")
_RUN_TARGET = _Target(RUN_COLLECTION, RUN_OPERATION, "run_id", "upgrade_run")


def _safe_host(url: str) -> str:
    """Return the host name of a connection string.

    Why:
        A log line must never carry a password. A connection string may hold
        one, so the log gets the host name alone.

    Args:
        url: The connection string.

    Returns:
        The host name, or ``unknown`` when the string names no host.
    """
    return str(urlparse(url).hostname or "unknown")


def _open_database(config: DatabaseConfig) -> Any:
    """Open one verified connection to the document store.

    Why:
        A lazy handle hides a dead server until the first write. A verified
        handle fails here instead, so the caller names the backup file as the
        store. The store opens its own handle, because the shared writer runs
        a graph backfill in its constructor and a capture must not pay for it.

    Args:
        config: The connection settings.

    Returns:
        The database handle, or None when the server does not answer.
    """
    if config.standalone_mode:
        logger.info("Upgrade portal found no document store, the backup file holds every record")
        return None
    try:
        client = ArangoClient(hosts=config.arango_host)
        return client.db(
            config.arango_database,
            username=config.arango_username,
            password=config.arango_password,
            verify=True,
        )
    except Exception as error:  # The store must keep working without a database.
        logger.warning(
            "Upgrade portal cannot reach the document store at %s: %s",
            _safe_host(config.arango_host),
            type(error).__name__,
        )
        return None


def connect_database(config: DatabaseConfig | None = None) -> Any:
    """Return a handle to the document store, or None when it is out of reach.

    Why:
        Every call retries a store that was down before. The portal must use
        the database again as soon as it comes back, because a file backup is
        a fallback and never the goal.

    Args:
        config: Settings to use. The function reads the environment when the
            caller passes nothing, and it caches that shared handle only.

    Returns:
        The database handle, or None.
    """
    global _DATABASE_HANDLE
    if config is not None:
        return _open_database(config)
    if _DATABASE_HANDLE is None:
        _DATABASE_HANDLE = _open_database(DatabaseConfig.from_env())
    return _DATABASE_HANDLE


def reset_connection() -> None:
    """Drop the cached database handle.

    Why:
        A test installs its own handle, and a long-lived worker needs a fresh
        connection after a database restart.
    """
    global _DATABASE_HANDLE
    _DATABASE_HANDLE = None


def _ensure_collection(database: Any, name: str, edge: bool) -> bool:
    """Create one collection when it is absent.

    Why:
        The portal must start against an empty database. The call repeats on
        every start, so it creates the collection one time only.

    Args:
        database: The database handle.
        name: The collection name.
        edge: True for an edge collection.

    Returns:
        True when the collection is ready.
    """
    try:
        if not database.has_collection(name):
            database.create_collection(name, edge=edge)
            logger.info("Upgrade portal created collection %s, edge=%s", name, edge)
        return True
    except Exception as error:  # A second worker may create the same collection.
        logger.warning("Upgrade portal could not create collection %s: %s", name, error)
        return False


def _ensure_index(database: Any, plan: IndexPlan) -> bool:
    """Create one persistent index when it is absent.

    Why:
        The server returns the index that exists for a repeat call with the
        same name and the same fields, so the call is idempotent. The
        definition holds no expiry, because a capture must never disappear.

    Args:
        database: The database handle.
        plan: The index to create.

    Returns:
        True when the index is ready.
    """
    definition: dict[str, Any] = {
        "type": "persistent",
        "fields": list(plan.fields),
        "name": plan.name,
        "unique": False,
        "sparse": False,
    }
    try:
        database.collection(plan.collection).add_index(definition)
        return True
    except Exception as error:  # A missing index slows a query but loses no record.
        logger.warning("Upgrade portal could not create index %s: %s", plan.name, error)
        return False


def _edge_index_present(database: Any) -> bool:
    """Report whether the edge collection holds its own edge index.

    Why:
        The data model lists the edge index as the eighth index. The edge
        collection creates that index, so the bootstrap confirms it and
        creates no second index.

    Args:
        database: The database handle.

    Returns:
        True when an edge index is present.
    """
    try:
        indexes = database.collection(EDGE_COLLECTION).indexes() or []
        return any(str(entry.get("type")) == "edge" for entry in indexes)
    except Exception as error:  # The report stays honest when the read fails.
        logger.warning("Upgrade portal could not read the indexes of %s: %s", EDGE_COLLECTION, error)
        return False


def bootstrap_storage(database: Any = None) -> BootstrapReport:
    """Create the collections and the indexes that this feature owns.

    Why:
        The portal must run against an empty database. Every step repeats
        without harm, so the portal calls this function on every start.

    Args:
        database: A database handle for a test. The function opens the shared
            handle when the caller passes nothing.

    Returns:
        The bootstrap report.
    """
    handle = database if database is not None else connect_database()
    if handle is None:
        logger.warning("Upgrade portal skipped the storage bootstrap, the document store is out of reach")
        return BootstrapReport((), (), False, False)
    collections = tuple(name for name, edge in _COLLECTIONS if _ensure_collection(handle, name, edge))
    indexes = tuple(plan.name for plan in INDEX_PLAN if _ensure_index(handle, plan))
    edge_ready = _edge_index_present(handle)
    logger.info(
        "Upgrade portal storage ready, collections=%s, indexes=%s, edge_index=%s",
        len(collections),
        len(indexes),
        edge_ready,
    )
    return BootstrapReport(collections, indexes, edge_ready, True)


def canonical_json(document: Mapping[str, Any]) -> str:
    """Return the canonical JSON form of the body of a document.

    Why:
        A digest and a size must not change when the field order changes or
        when the driver adds a field of its own. The function drops every
        field whose name starts with an underscore, because the writer and the
        server add those fields after the caller builds the document.

    Args:
        document: The document to render.

    Returns:
        The canonical JSON text.
    """
    body = {key: value for key, value in document.items() if not key.startswith("_")}
    return json.dumps(body, sort_keys=True, separators=(",", ":"), default=str, ensure_ascii=True)


def document_digest(document: Mapping[str, Any]) -> str:
    """Return the digest of the body of a document.

    Why:
        The read-back compares content, not a field count. A digest of the
        canonical form catches a truncated write and a changed value.

    Args:
        document: The document to measure.

    Returns:
        The digest in hexadecimal.
    """
    return hashlib.sha256(canonical_json(document).encode("utf-8")).hexdigest()


def measure_size_bytes(document: Mapping[str, Any]) -> int:
    """Return the byte count of the canonical form of a document.

    Why:
        FR-032b asks for the stored size of every capture. The count uses the
        same canonical form as the digest, so the size of a written document
        and the size of the document that comes back agree.

    Args:
        document: The document to measure.

    Returns:
        The byte count.
    """
    return len(canonical_json(document).encode("utf-8"))


def _stamp_size(document: Mapping[str, Any]) -> dict[str, Any]:
    """Return a copy of a capture that carries its measured size.

    Why:
        The measurement needs the field to be present already, and the digits
        of the value change the size of the document. The function therefore
        measures again until the value stops growing. The recorded size then
        equals the size the read-back reports, so an operator compares one
        number against one number.

    Args:
        document: The capture to stamp.

    Returns:
        The stamped copy.
    """
    payload = dict(document)
    payload["stored_size_bytes"] = 0
    for _ in range(_SIZE_ROUNDS):
        size = measure_size_bytes(payload)
        if size == payload["stored_size_bytes"]:
            break
        payload["stored_size_bytes"] = size
    return payload


def _is_scalar(value: Any) -> bool:
    """Report whether a value fits in one cell of a backup file.

    Args:
        value: The value to test.

    Returns:
        True for a value that needs no conversion.
    """
    return value is None or isinstance(value, str | int | float | bool)


def _backup_row(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return one flat row for the backup file.

    Why:
        A capture holds nested sections, and a cell of a backup file holds
        text only. The row keeps every plain field as its own column for a
        quick read, and it holds the whole document as canonical JSON, so an
        operator rebuilds the record from the file alone.

    Args:
        payload: The document to write.

    Returns:
        The row.
    """
    row: dict[str, Any] = {key: value for key, value in payload.items() if _is_scalar(value)}
    row["document_json"] = canonical_json(payload)
    return row


def _export_document(payload: dict[str, Any], target: _Target, key: str) -> bool:
    """Write one document through the exporter.

    Why:
        The exporter writes the backup file and mirrors the document to the
        database in one call. The mirror reports nothing to the caller, so the
        caller reads the key back afterward. Each document gets its own file
        name, because the exporter replaces a file that exists.

    Args:
        payload: The document to write.
        target: The write target.
        key: The document key.

    Returns:
        True when the exporter wrote the backup file.
    """
    options = ExportBackendOptions(format_override="csv", raw_data=[payload])
    filename = target.backup_prefix + "_" + key + ".csv"
    return DataExporter.write_with_format_selection(
        [_backup_row(payload)],
        filename,
        api_function_name=target.operation,
        backend_options=options,
    )


def _read_document(database: Any, collection: str, key: str) -> dict[str, Any] | None:
    """Return the stored document for one key.

    Args:
        database: The database handle.
        collection: The collection to read.
        key: The document key.

    Returns:
        The stored document, or None when the key is absent or the read fails.
    """
    try:
        stored = database.collection(collection).get(key)
    except Exception as error:  # A failed read counts as an unverified write.
        logger.warning("Upgrade portal could not read %s %s back: %s", collection, key, error)
        return None
    if stored is None:
        return None
    return dict(stored)


def _stored_digest(document: Mapping[str, Any]) -> str:
    """Return the digest that a document carries for its whole body.

    Why:
        A capture holds a digest map that the assembly wrote, and that value
        is the stored digest the check compares. A run holds no digest map,
        and the function then returns an empty string, so the check falls back
        to the digest of the whole body.

    Args:
        document: The document to read.

    Returns:
        The stored digest, or an empty string.
    """
    digests = document.get("digests")
    if not isinstance(digests, dict):
        return ""
    return str(digests.get("whole", ""))


def _mismatch_reason(expected: Mapping[str, Any], stored: Mapping[str, Any]) -> str:
    """Return the reason a stored document differs from the written document.

    Why:
        The check reads the schema version first, because a reader refuses a
        version it does not understand. The check then compares the digest the
        document carries, and then the digest of the whole body, so a document
        with no digest map still gets a full comparison.

    Args:
        expected: The document the portal wrote.
        stored: The document that came back.

    Returns:
        The machine name of the failure, or an empty string.
    """
    if stored.get("schema_version") != expected.get("schema_version"):
        return REASON_SCHEMA
    if _stored_digest(stored) != _stored_digest(expected):
        return REASON_DIGEST
    if document_digest(stored) != document_digest(expected):
        return REASON_DIGEST
    return REASON_VERIFIED


def verify_write(collection: str, key: str, expected: Mapping[str, Any], database: Any = None) -> Verification:
    """Read one key back and compare it against the document the portal wrote.

    Why:
        FR-031 and decision D9 forbid trust in the write result. The exporter
        returns success when it skips the database outside a container
        (``src/export/data_exporter.py:141``) and when the router falls back to
        a file (``src/db/router.py:372``). A read-back is the only proof.

    Args:
        collection: The collection that holds the key.
        key: The document key.
        expected: The document the portal wrote.
        database: A database handle for a test.

    Returns:
        The verification outcome.
    """
    handle = database if database is not None else connect_database()
    if handle is None:
        return Verification(False, REASON_NO_DATABASE, 0)
    stored = _read_document(handle, collection, key)
    if stored is None:
        return Verification(False, REASON_ABSENT, 0)
    reason = _mismatch_reason(expected, stored)
    return Verification(not reason, reason, measure_size_bytes(stored))


def _build_result(key: str, target: _Target, backup_written: bool, verification: Verification) -> StoreResult:
    """Assemble the outcome that the portal shows to the operator.

    Why:
        The result names the database only after a read-back matched. It names
        the backup file in every other case, so an operator never mistakes a
        file fallback for a database write.

    Args:
        key: The document key.
        target: The write target.
        backup_written: True when the exporter wrote the backup file.
        verification: The read-back outcome.

    Returns:
        The store result.
    """
    storage_path = STORAGE_DATABASE if verification.verified else STORAGE_BACKUP_FILE
    if not verification.verified:
        logger.warning(
            "Upgrade portal did not verify %s in %s, reason=%s, backup_file=%s",
            key,
            target.collection,
            verification.reason or REASON_ABSENT,
            backup_written,
        )
    return StoreResult(
        key=key,
        collection=target.collection,
        verified=verification.verified,
        storage_path=storage_path,
        backup_written=backup_written,
        stored_size_bytes=verification.stored_size_bytes,
        reason=verification.reason,
        message=_MESSAGES.get(verification.reason, _MESSAGES[REASON_ABSENT]),
    )


def _store(payload: dict[str, Any], target: _Target, database: Any) -> StoreResult:
    """Write one document, then prove that the database holds it.

    Why:
        The backup file is written every time, not after a failure only, so a
        record exists even when the database never answers.

    Args:
        payload: The document to write.
        target: The write target.
        database: A database handle for a test.

    Returns:
        The store result.
    """
    key = str(payload.get(target.key_field, ""))
    if not key:
        logger.error("Upgrade portal refused a document that holds no %s", target.key_field)
        return _build_result("", target, False, Verification(False, REASON_NO_KEY, 0))
    backup_written = _export_document(payload, target, key)
    verification = verify_write(target.collection, key, payload, database)
    return _build_result(key, target, backup_written, verification)


def write_capture(document: Mapping[str, Any], database: Any = None) -> StoreResult:
    """Store one capture and prove that the database holds it.

    Why:
        A capture is the evidence of the upgrade. The portal marks it verified
        only after the key comes back with the same schema version and the
        same digest.

    Args:
        document: The capture to store.
        database: A database handle for a test.

    Returns:
        The store result.
    """
    return _store(_stamp_size(document), _CAPTURE_TARGET, database)


def write_run(document: Mapping[str, Any], database: Any = None) -> StoreResult:
    """Store one upgrade run and prove that the database holds it.

    Why:
        The run record ties the two captures together. A lost run record hides
        both captures from the history view, so the write needs the same proof
        as a capture.

    Args:
        document: The run to store.
        database: A database handle for a test.

    Returns:
        The store result.
    """
    return _store(dict(document), _RUN_TARGET, database)


__all__ = [
    "CAPTURE_COLLECTION",
    "CAPTURE_OPERATION",
    "EDGE_COLLECTION",
    "EDGE_INDEX_FIELDS",
    "INDEX_PLAN",
    "REASON_ABSENT",
    "REASON_DIGEST",
    "REASON_NO_DATABASE",
    "REASON_NO_KEY",
    "REASON_SCHEMA",
    "REASON_VERIFIED",
    "RUN_COLLECTION",
    "RUN_OPERATION",
    "SCHEMA_VERSION",
    "STORAGE_BACKUP_FILE",
    "STORAGE_DATABASE",
    "BootstrapReport",
    "IndexPlan",
    "StoreResult",
    "Verification",
    "bootstrap_storage",
    "canonical_json",
    "connect_database",
    "document_digest",
    "measure_size_bytes",
    "reset_connection",
    "verify_write",
    "write_capture",
    "write_run",
]
