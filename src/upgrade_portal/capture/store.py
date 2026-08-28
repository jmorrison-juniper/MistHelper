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
from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Any, ClassVar
from urllib.parse import urlparse

from arango.client import ArangoClient

from src.dataclasses.export_backend_options import ExportBackendOptions
from src.db import DatabaseConfig
from src.export.data_exporter import DataExporter

logger = logging.getLogger(__name__)

CAPTURE_COLLECTION = "upgrade_captures"
RUN_COLLECTION = "upgrade_runs"
EDGE_COLLECTION = "capture_for_run"

# WHY: The operation name and the collection name must be one value, because the
# router uses the operation name as the collection name and creates whatever it
# is handed.
#
# `DataExporter.write_with_format_selection(api_function_name=...)` passes the
# name to `DatabaseRouter.write`, which passes it to
# `ArangoWriter.write(data, collection_name, strategy)`. That method calls
# `_ensure_collection(collection_name)`, and `_ensure_collection` creates the
# collection when it is absent. Nothing translates the name on the way.
#
# Issue #2061: these two constants used to read `upgradeCaptureWrite` and
# `upgradeRunWrite`. Every capture therefore wrote into a collection of that
# name, and the read-back below looked in `upgrade_captures`, found nothing, and
# reported `document_absent`. Every capture failed while the write itself
# succeeded, and the storage bootstrap still reported all three collections
# ready. Binding each operation to its collection removes the second name, so
# the two cannot drift again.
CAPTURE_OPERATION = CAPTURE_COLLECTION
RUN_OPERATION = RUN_COLLECTION

SCHEMA_VERSION = 1

EDGE_KEY_PREFIX = "edge-"

# The bound on one request to the document store, in seconds. The driver of the
# store waits 60 seconds by default, and that value applies to the connect step
# as well as the read step. A readiness probe against a host that never answers
# then holds one worker thread for a full minute, and enough probes empty the
# worker pool. Every call this portal makes is one small document write or one
# indexed query, so 10 seconds is far above the normal time and still bounds the
# wait. Raise this number if a later query needs longer.
REQUEST_TIMEOUT_SECONDS = 10.0

# The default page of the capture history view. The section
# `GET /api/sites/<site_id>/history` of contracts/http-api.md fixes this number.
DEFAULT_LIST_LIMIT = 25

STORAGE_DATABASE = "database"
STORAGE_BACKUP_FILE = "backup_file"
STORAGE_NONE = "none"

REASON_VERIFIED = ""
REASON_NO_KEY = "missing_key"
REASON_NO_DATABASE = "database_unreachable"
REASON_ABSENT = "document_absent"
REASON_SCHEMA = "schema_version_mismatch"
REASON_DIGEST = "digest_mismatch"
REASON_BAD_SCHEMA = "bad_schema_version"
REASON_BAD_STATE = "illegal_capture_state"
REASON_EMPTY_SIZE = "empty_stored_size"
REASON_SCHEMA_TOO_NEW = "schema_version_too_new"  # The read refusal of a record from a later release.
REASON_STATE_UNSET = "state_not_marked"

# The two refusals of the capture read routes. Each value repeats the error code
# of section 4 of contracts/http-api.md, so a route passes it straight on.
REASON_CAPTURE_NOT_FOUND = "capture_not_found"
REASON_CAPTURE_NOT_VERIFIED = "capture_not_verified"

_BACKUP_SENTENCE = "The backup file under data/ holds this record."

# WHY: The plain sentence of US6. A reader that meets a later schema version says
# so in the words of the operator. It names no backup file, because the record is
# present and only the reader is too old to render it.
_TOO_NEW_SENTENCE = (
    "This record comes from a later version of the portal. This portal is too old to show it. Upgrade the portal."
)

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
    REASON_BAD_SCHEMA: "The portal wrote nothing, because the capture holds no schema version of the integer 1.",
    REASON_BAD_STATE: "The portal wrote nothing, because the state of the capture cannot move to writing.",
    REASON_EMPTY_SIZE: "The database returned an empty document for this key. " + _BACKUP_SENTENCE,
    REASON_SCHEMA_TOO_NEW: _TOO_NEW_SENTENCE,
    REASON_STATE_UNSET: "The database holds this record, but the portal could not mark it verified.",
}

# The link message never names a backup file. No backup file holds an edge,
# because the capture carries run_id and role and rebuilds the link alone.
_EDGE_MESSAGE_VERIFIED = "The database holds the link from the run to the capture."
_EDGE_MESSAGE_FAILED = "The portal could not link the capture to the run. The capture still names its run."

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
class RepairReport:
    """The outcome of the one-time dangling edge repair.

    Why:
        The portal logs one line at start. The report gives that line the
        facts, and a test reads the same report. Issue 2096 left edges that
        point at a run that never existed, and this report counts how many the
        repair removed.

    Attributes:
        scanned: The number of edges the repair read.
        removed: The number of dangling edges the repair removed.
        database_available: True when the repair reached the database.
    """

    scanned: int
    removed: int
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


class CaptureTransitionError(ValueError):
    """Raised when a caller asks for a capture state move that the model forbids.

    Why:
        A silent illegal move leaves a stored capture that no reader can
        explain months later, and it lets a half-built capture join a
        comparison. The message names the state before and the state after, so
        the caller sees the exact refusal. The class extends ValueError, so a
        caller that catches ValueError still works.
    """


class CaptureState(StrEnum):
    """Every state one capture may hold.

    Why:
        A closed set of names keeps a stored capture readable years after the
        upgrade. The names come from the capture state list of the data model
        (``data-model.md`` lines 200 to 206) and from no other source.

        The value ``partial`` also appears in the separate ``capture_status``
        field. The two fields answer two questions. ``capture_status`` reports
        how complete the content is, and this state reports how far the
        lifecycle went. A reader must not treat one as the other.
    """

    PENDING = "pending"
    COLLECTING = "collecting"
    PARTIAL = "partial"
    ASSEMBLING = "assembling"
    WRITING = "writing"
    VERIFIED = "verified"
    WRITE_FAILED = "write_failed"
    FAILED = "failed"


# The capture document carries its lifecycle state under this name. The field
# table of data-model.md section 3.1 does not list the field, and section 3.8
# needs it, because only a verified capture may take part in a comparison. The
# store is the only component that learns the outcome of the read-back, so the
# store writes the field.
CAPTURE_STATE_FIELD = "state"


class CaptureStateMachine:
    """Move one capture between the states the data model allows.

    Why:
        A comparison rests on the word ``verified``. A caller that wrote that
        word by hand would defeat the read-back that FR-031 asks for, so every
        move passes this table and an illegal move raises instead of landing
        silently in the document.

        The table stamps no time. The capture field table names ``started_at``
        and ``finished_at`` and names no update time, so a stamp here would add
        a field that no reader expects and would change the digest.
    """

    # WHY: The arrows of data-model.md section 3.8. Every state that is not
    # final reaches FAILED, which matches the run diagram of section 4.1. An
    # earlier table allowed FAILED from COLLECTING alone, so a capture that
    # failed while it assembled had nowhere to move and stayed in ASSEMBLING
    # for ever.
    MOVES: ClassVar[dict[CaptureState, frozenset[CaptureState]]] = {
        CaptureState.PENDING: frozenset({CaptureState.COLLECTING, CaptureState.FAILED}),
        CaptureState.COLLECTING: frozenset(
            {CaptureState.ASSEMBLING, CaptureState.PARTIAL, CaptureState.FAILED},
        ),
        CaptureState.PARTIAL: frozenset({CaptureState.ASSEMBLING, CaptureState.FAILED}),
        CaptureState.ASSEMBLING: frozenset({CaptureState.WRITING, CaptureState.FAILED}),
        CaptureState.WRITING: frozenset(
            {CaptureState.VERIFIED, CaptureState.WRITE_FAILED, CaptureState.FAILED},
        ),
        CaptureState.VERIFIED: frozenset(),
        CaptureState.WRITE_FAILED: frozenset(),
        CaptureState.FAILED: frozenset(),
    }

    # WHY: A finished capture moves nowhere. A repeat capture takes a higher
    # ordinal and becomes a new document.
    TERMINAL: ClassVar[frozenset[CaptureState]] = frozenset(
        {CaptureState.VERIFIED, CaptureState.WRITE_FAILED, CaptureState.FAILED},
    )

    def advance(self, record: MutableMapping[str, Any], target: CaptureState | str) -> MutableMapping[str, Any]:
        """Move one capture to a new state.

        Args:
            record: The capture. The method edits it in place.
            target: The wanted state, as a CaptureState or as its plain name.

        Returns:
            The same capture, with the new state.

        Raises:
            CaptureTransitionError: When the model forbids the move.
        """
        current = self.read_state(record)
        wanted = self.coerce(target)
        if wanted not in self.allowed_next(current):
            raise CaptureTransitionError(f"A capture cannot move from {current.value} to {wanted.value}.")
        record[CAPTURE_STATE_FIELD] = wanted.value
        logger.info("Capture %s moved from %s to %s", record.get("capture_id", ""), current.value, wanted.value)
        return record

    @classmethod
    def allowed_next(cls, state: CaptureState) -> frozenset[CaptureState]:
        """Return every state one capture may enter from one state.

        Args:
            state: The current state of the capture.

        Returns:
            The legal next states. An empty set for a final state.
        """
        return cls.MOVES[state]

    @classmethod
    def permits(cls, current: CaptureState | str, target: CaptureState | str) -> bool:
        """Report whether one move is legal, and raise nothing.

        Why:
            The write path must answer the operator with a reason code rather
            than an exception, so it asks this question before it moves.

        Args:
            current: The state the capture holds now.
            target: The wanted state.

        Returns:
            True when the move is legal. False for an illegal move and for a
            name that stands for no state.
        """
        try:
            return cls.coerce(target) in cls.allowed_next(cls.coerce(current))
        except CaptureTransitionError:
            return False

    @classmethod
    def read_state(cls, record: Mapping[str, Any]) -> CaptureState:
        """Return the state one capture holds.

        Why:
            A capture that names no state has not started, so an absent field
            reads as ``pending``. A field that holds an unknown name is a
            different case, and it raises.

        Args:
            record: The capture to read.

        Returns:
            The state of the capture.

        Raises:
            CaptureTransitionError: When the capture holds an unknown state name.
        """
        return cls.coerce(str(record.get(CAPTURE_STATE_FIELD, "") or CaptureState.PENDING.value))

    @staticmethod
    def coerce(value: CaptureState | str) -> CaptureState:
        """Return the capture state that one name stands for.

        Why:
            The routes and the drivers pass plain text. A name outside the
            model must fail here, at the edge, and never reach the store.

        Args:
            value: A CaptureState or the plain name of one state.

        Returns:
            The matching CaptureState.

        Raises:
            CaptureTransitionError: When no state carries that name.
        """
        try:
            return CaptureState(value)
        except ValueError as error:
            raise CaptureTransitionError(f"{value!r} is not a capture state of this model.") from error


_CAPTURE_STATES = CaptureStateMachine()


def is_comparable(record: Mapping[str, Any]) -> bool:
    """Report whether one capture may take part in a comparison.

    Why:
        Section 3.8 of the data model allows a comparison of a ``verified``
        capture alone, because ``verified`` is the one word that proves the
        portal read the key back and matched the digest. The rule lives at the
        store boundary, so no caller has to remember it.

    Args:
        record: The capture to test.

    Returns:
        True only when the capture holds the verified state.
    """
    try:
        return _CAPTURE_STATES.read_state(record) is CaptureState.VERIFIED
    except CaptureTransitionError:
        return False


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
        client = ArangoClient(hosts=config.arango_host, request_timeout=REQUEST_TIMEOUT_SECONDS)
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
        logger.warning("Upgrade portal could not create collection %s: %s", name, type(error).__name__)
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
        logger.warning("Upgrade portal could not create index %s: %s", plan.name, type(error).__name__)
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
        logger.warning("Upgrade portal could not read the indexes of %s: %s", EDGE_COLLECTION, type(error).__name__)
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
    repair = repair_dangling_edges(handle)  # Issue 2096. One pass for each worker at start clears old dangling edges.
    logger.info(
        "Upgrade portal storage ready, collections=%s, indexes=%s, edge_index=%s, edges_removed=%s",
        len(collections),
        len(indexes),
        edge_ready,
        repair.removed,  # The count of dangling edges the repair cleared this start.
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


def _has_own_fields(document: Mapping[str, Any]) -> bool:
    """Report whether a document holds one field that the caller wrote.

    Why:
        The canonical text of an empty body is the two-character string ``{}``,
        so a plain byte count reports two bytes for a record that holds
        nothing. A stored record that comes back with driver fields alone is
        the exact shape of a lost write, and the size rule must call it empty.

    Args:
        document: The document to test.

    Returns:
        True when at least one field name does not start with an underscore.
    """
    return any(not str(name).startswith("_") for name in document)


def measure_size_bytes(document: Mapping[str, Any]) -> int:
    """Return the byte count of the canonical JSON form of a document.

    Why:
        FR-032b asks for the stored size of every capture, and a size needs one
        stated definition. This function measures the length in bytes of the
        canonical JSON text of the document body, encoded as UTF-8. The
        serialized document length is the honest choice here, for three
        reasons.

        First, it is reproducible. The same document gives the same number on
        every host, in every release, with no database at hand.

        Second, it matches the digest. The digest covers the same canonical
        text, so a size and a digest never disagree about which bytes they
        describe.

        Third, the alternative cannot be had. The true footprint of the record
        on disk holds the compressed value store, the revision history, and the
        eight indexes of this feature. The server reports that number for a
        whole collection and never for one key. A guess at that number would
        read like a fact and would be wrong.

        The number is therefore the size of the content, not the size of the
        record on disk. The name of the field says ``stored``, so this
        difference is written here, once, in plain words. The count leaves out
        every field whose name starts with an underscore, because the driver
        adds those fields after the caller builds the document.

        An empty body counts as zero and never as the two bytes of ``{}``. A
        record that comes back with driver fields alone then fails the size
        rule instead of passing it with a number that means nothing.

    Args:
        document: The document to measure.

    Returns:
        The byte count. Zero for a document that holds no field of its own.
    """
    if not _has_own_fields(document):
        return 0
    return len(canonical_json(document).encode("utf-8"))


def size_rule_holds(size_bytes: int) -> bool:
    """Report whether a measured size satisfies the size rule of the data model.

    Why:
        Rule 6 of ``data-model.md`` line 194 asks that ``stored_size_bytes`` is
        greater than zero after a successful write. A zero means the read-back
        returned an empty body, which is the shape of a lost write. The rule
        lives in its own function, so the write path and a test read the same
        one line.

    Args:
        size_bytes: The measured size of the stored document.

    Returns:
        True when the size is greater than zero.
    """
    return size_bytes > 0


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
        logger.warning("Upgrade portal could not read %s %s back: %s", collection, key, type(error).__name__)
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


def is_schema_version(value: Any) -> bool:
    """Report whether a value is the schema version integer that this release writes.

    Why:
        Python treats ``True`` as the integer 1, so a plain ``value != 1`` test
        accepts the boolean ``True`` as the schema version. A capture that
        carries a boolean there passes a naive check today and breaks the
        reader that meets it years from now. The test therefore refuses a
        boolean before it compares the number.

    Args:
        value: The value that a document carries under ``schema_version``.

    Returns:
        True only for the integer that this release writes.
    """
    return _whole_number(value) and value == SCHEMA_VERSION


def _whole_number(value: Any) -> bool:
    """Report whether a value is a plain integer and not a boolean.

    Why:
        Python makes ``bool`` a subclass of ``int``, so ``isinstance(True, int)``
        is True. Every schema version test in this module needs the same guard,
        so the guard lives in one place and no later test forgets it.

    Args:
        value: The value to test.

    Returns:
        True for an integer that is not a boolean.
    """
    return isinstance(value, int) and not isinstance(value, bool)


def is_readable_schema_version(value: Any) -> bool:
    """Report whether this release can render a record that carries this schema version.

    Why:
        A reader understands its own version and every version before it,
        because an older record holds a subset of the fields this release knows.
        A later version may hold a field with a new meaning, so this release
        must not guess at it. The rule is therefore ``stored <= SCHEMA_VERSION``
        and never a strict equality, which would hide every older record.

    Args:
        value: The value that a stored document carries under ``schema_version``.

    Returns:
        True for an integer at or below the version of this release.
    """
    return _whole_number(value) and value <= SCHEMA_VERSION


def schema_version_refusal(document: Mapping[str, Any]) -> str:
    """Return the reason this release cannot render one stored document.

    Why:
        US6 asks for two answers, not one. An older record opens, and a later
        record earns a plain sentence that names the true cause. A single
        mismatch reason for both would send an operator to hunt a corrupt write
        that never happened.

    Args:
        document: The stored document to test.

    Returns:
        ``REASON_SCHEMA_TOO_NEW`` for a later version, ``REASON_BAD_SCHEMA`` for
        a value that is no integer, or an empty string when the record renders.
    """
    value = document.get("schema_version")  # The one field that decides the answer.
    if is_readable_schema_version(value):  # This version, or any version before it.
        return REASON_VERIFIED  # The reader understands the record, so it opens.
    if _whole_number(value):  # An integer that this release does not reach.
        return REASON_SCHEMA_TOO_NEW  # The record is newer than the reader.
    return REASON_BAD_SCHEMA  # A boolean, a string, or an absent field.


def _same_schema_version(expected: Any, stored: Any) -> bool:
    """Report whether two schema version values are the same value and the same type.

    Why:
        The read-back must not accept the boolean ``True`` for the integer 1.
        ``True != 1`` is False in Python, so a plain comparison would call that
        write verified and would hide a corrupt record.

    Args:
        expected: The value the portal wrote.
        stored: The value that came back.

    Returns:
        True when both values match in value and in type.
    """
    return type(expected) is type(stored) and expected == stored


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
    if not _same_schema_version(expected.get("schema_version"), stored.get("schema_version")):
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

        The last check is the size rule of the data model. A document that
        matches the digest and still measures zero bytes holds no field of its
        own, and that shape is a lost write with a matching empty digest.

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
    if reason:
        return Verification(False, reason, measure_size_bytes(stored))
    size_bytes = measure_size_bytes(stored)
    if not size_rule_holds(size_bytes):
        return Verification(False, REASON_EMPTY_SIZE, 0)
    return Verification(True, REASON_VERIFIED, size_bytes)


def _storage_path(verified: bool, backup_written: bool) -> str:
    """Return the name of the store that truly holds the record.

    Why:
        A result that names the backup file after a refusal that wrote no file
        repeats the very lie this module exists to catch. The name therefore
        follows what happened, and it names no store when nothing was written.

    Args:
        verified: True after a matching read-back.
        backup_written: True when the exporter wrote the backup file.

    Returns:
        ``database``, ``backup_file``, or ``none``.
    """
    if verified:
        return STORAGE_DATABASE
    return STORAGE_BACKUP_FILE if backup_written else STORAGE_NONE


def _build_result(key: str, target: _Target, backup_written: bool, verification: Verification) -> StoreResult:
    """Assemble the outcome that the portal shows to the operator.

    Why:
        The result names the database only after a read-back matched. It names
        the backup file in every other case that wrote one, so an operator
        never mistakes a file fallback for a database write.

    Args:
        key: The document key.
        target: The write target.
        backup_written: True when the exporter wrote the backup file.
        verification: The read-back outcome.

    Returns:
        The store result.
    """
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
        storage_path=_storage_path(verification.verified, backup_written),
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


# WHY: A caller that tracks no lifecycle hands the store a document the
# assembly already built. The write path therefore reads an absent state as
# assembling. A document that names an earlier state or a final state still
# fails the table, so the guard keeps its teeth.
_WRITE_ENTRY_STATE = CaptureState.ASSEMBLING


def _prepare_capture(document: Mapping[str, Any]) -> tuple[dict[str, Any], str, str]:
    """Check one capture and move it to the writing state.

    Why:
        Three faults must never reach the database. A capture with no business
        key would land under an empty key. A capture with the boolean ``True``
        under ``schema_version`` would pass a plain ``!= 1`` test, because
        Python treats ``True`` as the integer 1. That capture would break the
        reader that meets it years from now. A capture in the wrong state would
        let a half-built document reach a comparison.

        The order of the checks matters. The key comes first, so the refusal
        for an empty document names the missing key and not the schema.

    Args:
        document: The capture the caller offers.

    Returns:
        The prepared copy, the business key, and the reason for a refusal. The
        reason is an empty string when the capture may be written.
    """
    payload = dict(document)
    key = str(payload.get(_CAPTURE_TARGET.key_field, ""))
    if not key:
        return payload, "", REASON_NO_KEY
    if not is_schema_version(payload.get("schema_version")):
        return payload, key, REASON_BAD_SCHEMA
    payload[CAPTURE_STATE_FIELD] = str(payload.get(CAPTURE_STATE_FIELD) or _WRITE_ENTRY_STATE.value)
    if not CaptureStateMachine.permits(payload[CAPTURE_STATE_FIELD], CaptureState.WRITING):
        return payload, key, REASON_BAD_STATE
    _CAPTURE_STATES.advance(payload, CaptureState.WRITING)
    return _stamp_size(payload), key, REASON_VERIFIED


def _verified_document(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return the capture as it must read after a matching read-back.

    Why:
        The word ``verified`` is one byte longer than the word ``writing``, so
        the size that the writing copy carries is stale as soon as the state
        moves. The function therefore measures the size again, and the patch
        writes both fields together. A document that carried a size for
        another body would fail its own read-back.

    Args:
        payload: The capture as the portal wrote it.

    Returns:
        The verified copy, with a fresh size.
    """
    verified = dict(payload)
    verified[CAPTURE_STATE_FIELD] = CaptureState.VERIFIED.value
    return _stamp_size(verified)


def _patch_capture(database: Any, key: str, final: Mapping[str, Any]) -> bool:
    """Write the verified state and the fresh size onto one stored capture.

    Args:
        database: The database handle.
        key: The capture key.
        final: The verified copy that holds the two new values.

    Returns:
        True when the driver accepted the patch.
    """
    patch = {
        "_key": key,
        CAPTURE_STATE_FIELD: final[CAPTURE_STATE_FIELD],
        "stored_size_bytes": final["stored_size_bytes"],
    }
    try:
        database.collection(CAPTURE_COLLECTION).update(patch)
    except Exception as error:  # An unmarked capture is safe, because no comparison takes it.
        logger.warning("Upgrade portal could not mark capture %s verified: %s", key, type(error).__name__)
        return False
    return True


def _mark_verified(result: StoreResult, payload: dict[str, Any], database: Any) -> StoreResult:
    """Move one stored capture to the verified state and confirm the move.

    Why:
        ``verified`` is the one word that lets a capture join a comparison, so
        the portal writes it only after the read-back matched and then reads
        the key back a second time. A capture that keeps the writing state is
        stored and whole, and it stays out of every comparison until an
        operator repeats the capture.

    Args:
        result: The outcome of the first read-back.
        payload: The capture as the portal wrote it. The method edits it in place.
        database: A database handle for a test.

    Returns:
        The final store result.
    """
    handle = database if database is not None else connect_database()
    final = _verified_document(payload)
    confirmed = _patch_capture(handle, result.key, final) if handle is not None else False
    if confirmed:
        confirmed = verify_write(CAPTURE_COLLECTION, result.key, final, handle).verified
    if not confirmed:
        return replace(
            result,
            verified=False,
            storage_path=_storage_path(False, result.backup_written),
            reason=REASON_STATE_UNSET,
            message=_MESSAGES[REASON_STATE_UNSET],
        )
    payload.update(final)
    return replace(result, stored_size_bytes=int(final["stored_size_bytes"]))


def write_capture(document: Mapping[str, Any], database: Any = None) -> StoreResult:
    """Store one capture and prove that the database holds it.

    Why:
        A capture is the evidence of the upgrade. The portal marks it verified
        only after the key comes back with the same schema version, the same
        digest, and a size above zero. The state moves through the table of
        the data model, so a comparison later reads one word and trusts it.

        This method is the one door that every stored capture passes through,
        so it also links the capture to its run. The link comes last, because
        an edge that points at a capture the database does not hold is worse
        than no edge at all. The link never changes the result.

    Args:
        document: The capture to store.
        database: A database handle for a test.

    Returns:
        The store result.
    """
    payload, key, reason = _prepare_capture(document)  # Checks the key, the schema version, and the state.
    if reason:  # A refused capture never reaches the database.
        return _build_result(key, _CAPTURE_TARGET, False, Verification(False, reason, 0))  # The reason travels.
    result = _store(payload, _CAPTURE_TARGET, database)  # Writes the backup file, then reads the key back.
    if not result.verified:  # The database does not hold the capture.
        _CAPTURE_STATES.advance(payload, CaptureState.WRITE_FAILED)  # A failed capture joins no comparison.
        return result  # The result already names the backup file.
    final = _mark_verified(result, payload, database)  # Moves the stored capture to the verified state.
    if final.verified:  # Only a proven capture may carry a link to its run.
        _link_capture_to_run(payload, database)  # A best effort that never changes the result below.
    return final  # The capture result travels unchanged, with the edge or without it.


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


# ---------------------------------------------------------------------------
# The CaptureForRun edge
# ---------------------------------------------------------------------------

# WHY: The four fields of the edge, from data-model.md section 5. Three of the
# four names start with an underscore, and ``canonical_json`` drops those
# fields, so a digest over an edge would cover the role alone. The read-back of
# an edge therefore compares these four names one by one.
EDGE_FIELDS: tuple[str, ...] = ("_key", "_from", "_to", "role")


def build_edge(capture: Mapping[str, Any]) -> dict[str, Any]:
    """Return the edge that links one capture to its run.

    Why:
        The capture already names its run and its role, so the link needs no
        second source and no operator input. A derived edge can never disagree
        with the capture it points at.

    Args:
        capture: The capture that the database holds.

    Returns:
        The edge document.
    """
    capture_key = str(capture.get("capture_id", ""))
    run_key = str(capture.get("run_id", ""))
    return {
        "_key": EDGE_KEY_PREFIX + capture_key,
        "_from": RUN_COLLECTION + "/" + run_key,
        "_to": CAPTURE_COLLECTION + "/" + capture_key,
        "role": str(capture.get("role", "")),
    }


def _edge_size_bytes(edge: Mapping[str, Any]) -> int:
    """Return the byte count of the four fields of one edge.

    Why:
        ``measure_size_bytes`` drops every field whose name starts with an
        underscore, and three of the four fields of an edge carry such a name.
        A plain measurement would report the size of the role alone.

    Args:
        edge: The edge to measure.

    Returns:
        The byte count of the canonical form of the four fields.
    """
    body = {name: edge.get(name) for name in EDGE_FIELDS}
    return len(json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8"))


def _edge_matches(expected: Mapping[str, Any], stored: Mapping[str, Any]) -> bool:
    """Report whether a stored edge holds the four values the portal wrote.

    Args:
        expected: The edge the portal wrote.
        stored: The edge that came back.

    Returns:
        True when all four fields agree.
    """
    return all(stored.get(name) == expected.get(name) for name in EDGE_FIELDS)


def _edge_result(edge: Mapping[str, Any], verified: bool, reason: str) -> StoreResult:
    """Assemble the outcome of one edge write.

    Why:
        No backup file holds an edge. The registry of the data model names two
        operations only, and the capture already carries its run and its role,
        so the portal rebuilds a lost edge from the capture. The result
        therefore reports no backup file and names no store after a failure.

    Args:
        edge: The edge the portal wrote.
        verified: True after a matching read-back.
        reason: The machine name of the failure, or an empty string.

    Returns:
        The store result.
    """
    return StoreResult(
        key=str(edge.get("_key", "")),
        collection=EDGE_COLLECTION,
        verified=verified,
        storage_path=STORAGE_DATABASE if verified else STORAGE_NONE,
        backup_written=False,
        stored_size_bytes=_edge_size_bytes(edge) if verified else 0,
        reason=reason,
        message=_EDGE_MESSAGE_VERIFIED if verified else _EDGE_MESSAGE_FAILED,
    )


def _insert_edge(database: Any, edge: Mapping[str, Any]) -> bool:
    """Write one edge, and replace an edge that already carries the same key.

    Why:
        A repeat write must leave one edge and never two. The bulk import with
        the replace rule is the idiom the shared writer uses for every edge of
        this codebase (``src/db/arango_writer.py:4370``).

    Args:
        database: The database handle.
        edge: The edge to write.

    Returns:
        True when the driver accepted the write.
    """
    try:
        database.collection(EDGE_COLLECTION).import_bulk([dict(edge)], on_duplicate="replace")
    except Exception as error:  # A lost edge hides no capture, because the capture names its run.
        logger.warning("Upgrade portal could not write edge %s: %s", edge.get("_key", ""), type(error).__name__)
        return False
    return True


def write_edge(capture: Mapping[str, Any], database: Any = None) -> StoreResult:
    """Link one stored capture to its run, and prove that the link arrived.

    Why:
        The history view walks the graph from a run to its two captures, so a
        lost edge hides the pair. The write follows the same rule as a
        document write. The portal reads the key back before it reports
        success, because the write result alone is not proof.

    Args:
        capture: The capture that the database holds.
        database: A database handle for a test.

    Returns:
        The store result for the edge.
    """
    edge = build_edge(capture)
    if not str(capture.get("capture_id", "")) or not str(capture.get("run_id", "")):
        logger.error("Upgrade portal refused an edge, because the capture names no run or no capture")
        return _edge_result(edge, False, REASON_NO_KEY)
    handle = database if database is not None else connect_database()
    if handle is None:
        return _edge_result(edge, False, REASON_NO_DATABASE)
    if not _insert_edge(handle, edge):
        return _edge_result(edge, False, REASON_ABSENT)
    stored = _read_document(handle, EDGE_COLLECTION, str(edge["_key"]))
    if stored is None:
        return _edge_result(edge, False, REASON_ABSENT)
    if not _edge_matches(edge, stored):
        return _edge_result(edge, False, REASON_DIGEST)
    return _edge_result(edge, True, REASON_VERIFIED)


def _link_capture_to_run(capture: Mapping[str, Any], database: Any) -> None:
    """Link one verified capture to its run, and leave the capture result alone.

    Why:
        The history view walks the graph from a run to its captures. An
        operator returns a month after the upgrade and reads that view, so a
        capture with no edge never reaches that operator. The link therefore
        runs inside the store, where every stored capture passes.

        The link is a best effort, which is the stated design of this section.
        ``_insert_edge`` records that a lost edge hides no capture, because the
        capture names its run, and ``_edge_result`` records that the portal
        rebuilds a lost edge from the capture. A failed link therefore writes
        one log record, returns nothing, and raises nothing.

        A capture that names no run leaves at the debug level. Such a capture
        has no link to build, so the case is not a fault. ``write_edge`` logs
        an error for the same shape, because a caller that asks for a link by
        name states a wrong expectation.

    Args:
        capture: The capture that the database holds and proved.
        database: A database handle for a test.
    """
    capture_key = str(capture.get("capture_id", ""))  # Names the capture in each log record below.
    if not str(capture.get("run_id", "")):  # A capture that names no run has no link to build.
        logger.debug("Upgrade portal built no edge for %s, because it names no run", capture_key)  # A quiet exit.
        return  # A capture may stand alone, so this exit reports no fault.
    outcome = write_edge(capture, database)  # The edge write reads the key back before it reports success.
    if outcome.verified:  # The history view can now walk from the run to this capture.
        logger.info("Upgrade portal linked capture %s to its run", capture_key)  # One record for the audit trail.
        return  # The link is complete.
    logger.warning(
        "Upgrade portal built no edge for %s, reason=%s. The capture still names its run.",  # The capture survives.
        capture_key,  # The capture that holds no link.
        outcome.reason,  # The machine name of the failure.
    )


# ---------------------------------------------------------------------------
# The one-time repair of dangling edges (issue 2096)
# ---------------------------------------------------------------------------

# WHY: The scan reads every edge of the capture_for_run collection. The name
# comes from a module constant, so no caller text reaches the query.
_EDGE_SCAN_QUERY = "FOR edge IN " + EDGE_COLLECTION + " RETURN edge"


def _edge_run_key(edge: Mapping[str, Any]) -> str:
    """Return the run key that one edge names in its ``_from`` field.

    Why:
        The edge stores its run as ``upgrade_runs/run-xxxx``. The repair reads
        the run key alone, so it can look the run up by key.

    Args:
        edge: The edge document.

    Returns:
        The run key, or an empty string when the ``_from`` field names no run.
    """
    origin = str(edge.get("_from", ""))  # The handle of the run, with the collection prefix.
    prefix = RUN_COLLECTION + "/"  # The prefix that every run handle carries.
    return origin[len(prefix) :] if origin.startswith(prefix) else ""  # The key alone, or nothing.


def _run_absent(database: Any, run_key: str) -> bool | None:
    """Report whether the run of one edge is absent. None means the read failed.

    Why:
        The repair removes an edge only when its run does not exist. A read that
        raises is not proof of absence, so the repair leaves that edge and this
        function reports the failed read.

    Args:
        database: The database handle.
        run_key: The key of the run to read.

    Returns:
        True when the run is absent. False when it exists. None when the read
        failed.
    """
    if not run_key:  # A broken handle names no run, so no run document exists for it.
        return True
    try:
        stored = database.collection(RUN_COLLECTION).get(run_key)  # The run document, or None when absent.
    except Exception as error:  # A failed read is not proof of absence, so the edge stays.
        logger.warning("Upgrade portal could not read run %s for a repair: %s", run_key, type(error).__name__)
        return None
    return stored is None  # A clean None means the run is truly absent.


def _remove_edge(database: Any, edge_key: str) -> bool:
    """Remove one edge by key.

    Why:
        A dangling edge points at a run that never existed, so the removal
        frees the history view. A lost removal hides no capture, because the
        capture names its run.

    Args:
        database: The database handle.
        edge_key: The key of the edge to remove.

    Returns:
        True when the driver accepted the removal.
    """
    try:
        database.collection(EDGE_COLLECTION).delete(edge_key)  # The next scan no longer sees this edge.
    except Exception as error:  # A failed removal loses no capture, so the repair reports it and moves on.
        logger.warning("Upgrade portal could not remove edge %s: %s", edge_key, type(error).__name__)
        return False
    return True


def _repair_one_edge(database: Any, edge: Mapping[str, Any]) -> bool:
    """Remove one edge when its run is absent, and leave every other edge.

    Args:
        database: The database handle.
        edge: The edge document.

    Returns:
        True when the repair removed the edge.
    """
    edge_key = str(edge.get("_key", ""))  # Names the edge in each log record below.
    run_key = _edge_run_key(edge)  # The run the edge points at.
    absent = _run_absent(database, run_key)  # True absent, False live, None on a failed read.
    if not absent:  # A live edge and a failed read both keep the edge.
        return False
    logger.info("Upgrade portal removes dangling edge %s, because run %s is absent", edge_key, run_key)
    removed = _remove_edge(database, edge_key)  # The driver removes the edge from the collection.
    logger.debug("Upgrade portal removed dangling edge %s, result=%s", edge_key, removed)
    return removed


def _scan_edges(database: Any) -> list[dict[str, Any]]:
    """Return every edge of the ``capture_for_run`` collection.

    Args:
        database: The database handle.

    Returns:
        One copy of each edge document, or an empty list on a failed scan.
    """
    return [dict(edge) for edge in _run_aql(database, _EDGE_SCAN_QUERY, {})]  # A read fault reports an empty scan.


def repair_dangling_edges(database: Any = None) -> RepairReport:
    """Remove every capture edge whose run no longer exists.

    Why:
        Issue 2096 left dangling edges. The old start invented a run for a
        run-less capture and wrote an edge to that invented run. The run never
        existed, so the history view walked into nothing. This repair reads
        every edge, reads the run each edge names before any removal, and
        removes only an edge whose run is absent. It leaves every capture and
        every live edge, and a second run removes nothing (D2, FR-098, FR-099).

    Args:
        database: A database handle for a test. The function opens the shared
            handle when the caller passes nothing.

    Returns:
        The repair report.
    """
    handle = database if database is not None else connect_database()
    if handle is None:  # A repair needs the database, so an unreachable store skips the pass.
        logger.warning("Upgrade portal skipped the dangling edge repair, the document store is out of reach")
        return RepairReport(0, 0, False)
    logger.info("Upgrade portal starts the dangling edge repair")  # One record before the scan.
    edges = _scan_edges(handle)  # Every edge of the collection.
    removed = sum(1 for edge in edges if _repair_one_edge(handle, edge))  # One removal for each dangling edge.
    logger.debug("Upgrade portal finished the dangling edge repair, scanned=%s removed=%s", len(edges), removed)
    return RepairReport(len(edges), removed, True)


# ---------------------------------------------------------------------------
# Reading a capture back out
# ---------------------------------------------------------------------------

# WHY: The history row of the section `GET /api/sites/<site_id>/history` in
# contracts/http-api.md, and the four fields a caller needs to judge a capture
# before it opens one. A page returns this projection and never the whole
# document, because one capture of a large site holds every device record and
# every client record.
#
# `counts` is the one nested name here. It is the nine integer map that
# `capture/assembly.py` writes, so it costs nine numbers a row and no second
# read. The history page shows a device count and a client count beside each
# capture, and a history of an upgrade that cannot show those two numbers
# cannot answer the question the operator asked.
LIST_FIELDS: tuple[str, ...] = (
    "capture_id",
    "run_id",
    "ordinal",
    "role",
    "org_id",
    "site_id",
    "site_name",
    "started_at",
    "finished_at",
    "duration_seconds",
    "capture_status",
    "actor_email",
    "stored_size_bytes",
    "schema_version",
    CAPTURE_STATE_FIELD,
    "tier",
    "counts",
)

# WHY: The three fields a caller may narrow a page by. Each name is also the
# name of its bind parameter, so the clause builder needs one list.
_QUERY_FIELDS: tuple[str, ...] = ("site_id", "org_id", "run_id")

# WHY: Every name below comes from the two fixed tuples above and never from
# caller text, so no value of an operator reaches the query text. Each value
# travels as a bind parameter instead.
_LIST_HEAD = "FOR doc IN " + CAPTURE_COLLECTION + "\n"
_LIST_TAIL = (
    "  SORT doc.started_at DESC\n"
    "  LIMIT @offset, @limit\n"
    "  RETURN {" + ",".join(name + ":doc." + name for name in LIST_FIELDS) + "}\n"
)
_COUNT_TAIL = "  COLLECT WITH COUNT INTO total\n  RETURN total\n"

# WHY: The run history row. Every name below comes from the UpgradeRun table of
# data-model.md section 4 and from `RunRecordBuilder.REQUIRED_FIELDS` in
# src/upgrade_portal/runtime/runs.py, so the row names the fields the writer
# truly stores. The run holds `created_at` and `updated_at` and holds no
# `started_at` and no `finished_at`. The run holds `state` and holds no
# `run_state`. The run names no device family at all, because a family belongs
# to one entry of `targets` and a run may carry more than one family.
RUN_LIST_FIELDS: tuple[str, ...] = (
    "run_id",
    "org_id",
    "site_id",
    "site_name",
    "actor_email",
    "created_at",
    "updated_at",
    "state",
    "tier",
    "pre_capture_id",
    "post_capture_id",
    "schema_version",
)

# WHY: The three fields a caller may narrow a run page by. The site index and
# the operator index of data-model.md lines 396 and 398 each open with one of
# these names, so a narrowed page reads an index and never the whole collection.
_RUN_QUERY_FIELDS: tuple[str, ...] = ("site_id", "org_id", "actor_email")

# WHY: The sort follows `created_at`, because the run history index of
# data-model.md line 396 is `site_id` and `created_at`. A sort on any other
# field would read every run of the site and then sort it in memory.
_RUN_LIST_HEAD = "FOR doc IN " + RUN_COLLECTION + "\n"
_RUN_LIST_TAIL = (
    "  SORT doc.created_at DESC\n"
    "  LIMIT @offset, @limit\n"
    "  RETURN {" + ",".join(name + ":doc." + name for name in RUN_LIST_FIELDS) + "}\n"
)


@dataclass(frozen=True, slots=True)
class CaptureQuery:
    """The narrowing values and the page bounds of one capture list.

    Why:
        The history route carries a site, a page size, and an offset, and the
        run page carries a run. One record keeps the store signature at two
        parameters and stops a wrong positional order.

    Attributes:
        site_id: Narrow the page to one site. An empty string reads every site.
        org_id: Narrow the page to one organization.
        run_id: Narrow the page to one run.
        limit: The largest number of rows in the page.
        offset: The number of rows to pass over first.
    """

    site_id: str = ""
    org_id: str = ""
    run_id: str = ""
    limit: int = DEFAULT_LIST_LIMIT
    offset: int = 0


@dataclass(frozen=True, slots=True)
class CaptureListPage:
    """One page of capture rows, with the total behind it.

    Why:
        The history contract answers with the rows and a total, so the page
        below the list can show how many captures the site holds. The report
        also says whether the database answered, so a caller never shows an
        empty history as a fact when the database was out of reach.

    Attributes:
        captures: The rows of this page, newest first.
        total: The number of captures that match, across every page.
        limit: The page size that produced these rows.
        offset: The offset that produced these rows.
        database_available: True when the database answered.
    """

    captures: tuple[dict[str, Any], ...]
    total: int
    limit: int
    offset: int
    database_available: bool


@dataclass(frozen=True, slots=True)
class RunQuery:
    """The narrowing values and the page bounds of one run list.

    Why:
        The run history route carries a site, a page size, and an offset, and
        the operator view carries an email. One record keeps the store
        signature at two parameters and stops a wrong positional order.

    Attributes:
        site_id: Narrow the page to one site. An empty string reads every site.
        org_id: Narrow the page to one organization.
        actor_email: Narrow the page to the runs of one operator.
        limit: The largest number of rows in the page.
        offset: The number of rows to pass over first.
    """

    site_id: str = ""
    org_id: str = ""
    actor_email: str = ""
    limit: int = DEFAULT_LIST_LIMIT
    offset: int = 0


@dataclass(frozen=True, slots=True)
class RunListPage:
    """One page of run rows, with the total behind it.

    Why:
        The run history page shows how many runs the site holds, so the row
        count alone is not enough. The report also says whether the database
        answered, so a caller never shows an empty history as a fact when the
        database was out of reach.

    Attributes:
        runs: The rows of this page, newest first.
        total: The number of runs that match, across every page.
        limit: The page size that produced these rows.
        offset: The offset that produced these rows.
        database_available: True when the database answered.
    """

    runs: tuple[dict[str, Any], ...]
    total: int
    limit: int
    offset: int
    database_available: bool


@dataclass(frozen=True, slots=True)
class CaptureLoad:
    """One capture that the store read back, with the comparison verdict.

    Why:
        Section 3.8 of the data model allows a comparison of a ``verified``
        capture alone. The verdict travels with the document, so a route reads
        one field instead of repeating the rule.

    Attributes:
        capture: The stored capture, or None when the store hands out nothing.
        comparable: True only when the capture may take part in a comparison.
        reason: ``capture_not_found``, ``capture_not_verified``,
            ``database_unreachable``, or an empty string.
    """

    capture: dict[str, Any] | None
    comparable: bool
    reason: str


def _filter_binds(query: CaptureQuery) -> dict[str, Any]:
    """Return the bind values for the narrowing fields the caller filled.

    Why:
        An unused bind parameter makes the server refuse the whole query, so
        the count query and the list query each receive their own binds and the
        empty fields travel with neither.

    Args:
        query: The list request.

    Returns:
        One entry for each narrowing field that holds a value.
    """
    filled = {"site_id": query.site_id, "org_id": query.org_id, "run_id": query.run_id}
    return {name: filled[name] for name in _QUERY_FIELDS if filled[name]}


def _run_filter_binds(query: RunQuery) -> dict[str, Any]:
    """Return the bind values for the narrowing fields of one run list.

    Why:
        An unused bind parameter makes the server refuse the whole query, so
        the empty fields travel with neither query. The run list narrows by a
        different set of fields than the capture list, because a run holds no
        run identifier to narrow by.

    Args:
        query: The list request.

    Returns:
        One entry for each narrowing field that holds a value.
    """
    filled = {"site_id": query.site_id, "org_id": query.org_id, "actor_email": query.actor_email}
    return {name: filled[name] for name in _RUN_QUERY_FIELDS if filled[name]}


def _filter_clause(binds: Mapping[str, Any], fields: tuple[str, ...]) -> str:
    """Return the filter lines for the narrowing fields the caller filled.

    Why:
        A fixed query that tests every field against an empty string cannot use
        the two site indexes of this feature. The clause therefore names the
        filled fields alone. Each name comes from a fixed tuple in this module,
        so no caller text reaches the query.

    Args:
        binds: The bind values for the narrowing fields.
        fields: The names a caller may narrow by, in query order.

    Returns:
        The filter lines, or an empty string when the caller narrowed nothing.
    """
    return "".join("  FILTER doc." + name + " == @" + name + "\n" for name in fields if name in binds)


def _run_aql(database: Any, query: str, binds: Mapping[str, Any]) -> list[Any]:
    """Run one query and return its rows.

    Why:
        A history page that raises would hide the whole run page. An empty page
        with a false availability flag tells the operator the truth instead.

    Args:
        database: The database handle.
        query: The query text.
        binds: The bind values.

    Returns:
        The rows, or an empty list when the query failed.
    """
    try:
        cursor = database.aql.execute(query, bind_vars=dict(binds))
        return list(cursor)
    except Exception as error:  # A failed read reports an empty page and never raises.
        logger.warning("Upgrade portal could not run a history query: %s", type(error).__name__)
        return []


def list_captures(query: CaptureQuery, database: Any = None) -> CaptureListPage:
    """Return one page of capture rows, newest first.

    Why:
        FR-032 asks for a site history. The page carries the small row of the
        contract and never the whole capture, so a site with a thousand
        devices still renders. The total comes from its own count query,
        because a page cannot report what lies beyond it.

    Args:
        query: The narrowing values and the page bounds.
        database: A database handle for a test.

    Returns:
        The page.
    """
    handle = database if database is not None else connect_database()
    if handle is None:
        return CaptureListPage((), 0, query.limit, query.offset, False)
    binds = _filter_binds(query)
    clause = _filter_clause(binds, _QUERY_FIELDS)
    counted = _run_aql(handle, _LIST_HEAD + clause + _COUNT_TAIL, binds)
    page_binds = dict(binds, offset=max(query.offset, 0), limit=max(query.limit, 1))
    rows = _run_aql(handle, _LIST_HEAD + clause + _LIST_TAIL, page_binds)
    total = int(counted[0]) if counted else 0
    return CaptureListPage(tuple(dict(row) for row in rows), total, query.limit, query.offset, True)


def list_runs(query: RunQuery, database: Any = None) -> RunListPage:
    """Return one page of run rows, newest first.

    Why:
        FR-085 asks for a run history beside the capture history. The page
        carries the small row of ``RUN_LIST_FIELDS`` and never the whole run,
        because a run of a large site holds one target entry for every device.
        The total comes from its own count query, because a page cannot report
        what lies beyond it.

    Args:
        query: The narrowing values and the page bounds.
        database: A database handle for a test.

    Returns:
        The page.
    """
    handle = database if database is not None else connect_database()
    if handle is None:
        return RunListPage((), 0, query.limit, query.offset, False)
    binds = _run_filter_binds(query)  # Only the fields the caller filled travel.
    clause = _filter_clause(binds, _RUN_QUERY_FIELDS)  # Each name comes from a fixed tuple.
    counted = _run_aql(handle, _RUN_LIST_HEAD + clause + _COUNT_TAIL, binds)  # The total behind the page.
    page_binds = dict(binds, offset=max(query.offset, 0), limit=max(query.limit, 1))  # A page holds one row at least.
    rows = _run_aql(handle, _RUN_LIST_HEAD + clause + _RUN_LIST_TAIL, page_binds)  # The rows of this page.
    total = int(counted[0]) if counted else 0  # A failed count reports zero and never raises.
    return RunListPage(tuple(dict(row) for row in rows), total, query.limit, query.offset, True)


def load_capture(capture_id: str, database: Any = None) -> CaptureLoad:
    """Read one capture back and report whether it may join a comparison.

    Why:
        The capture route answers 404 for a key the database does not hold and
        409 for a capture that never reached the verified state. The two
        answers need two reasons, so this function separates them and the route
        maps each reason to its status.

        The schema gate runs before the state gate. A record from a later
        release may hold a state word this release does not know, so the reader
        must refuse the record on its version and never on its state.

    Args:
        capture_id: The business key of the capture.
        database: A database handle for a test.

    Returns:
        The load outcome. The capture is present for an unverified record, so a
        caller may still show what the record holds.
    """
    handle = database if database is not None else connect_database()
    if handle is None:
        return CaptureLoad(None, False, REASON_NO_DATABASE)
    stored = _read_document(handle, CAPTURE_COLLECTION, capture_id) if capture_id else None
    if stored is None:
        return CaptureLoad(None, False, REASON_CAPTURE_NOT_FOUND)
    refusal = schema_version_refusal(stored)  # An older record passes, a later record stops here.
    if refusal:  # This release cannot render the record.
        logger.warning("Upgrade portal refused capture %s, reason=%s", capture_id, refusal)  # One audit record.
        return CaptureLoad(stored, False, refusal)  # The record travels, so a caller may show its version.
    if not is_comparable(stored):
        return CaptureLoad(stored, False, REASON_CAPTURE_NOT_VERIFIED)
    return CaptureLoad(stored, True, REASON_VERIFIED)


def load_capture_for_comparison(capture_id: str, database: Any = None) -> CaptureLoad:
    """Read one capture back for a comparison, and hand out nothing else.

    Why:
        Section 3.8 allows a comparison of a ``verified`` capture alone. The
        rule belongs at the store boundary, not in each caller, so this
        function returns no document at all for a capture that is not
        verified. A caller therefore cannot compare a half-written capture even
        by mistake.

    Args:
        capture_id: The business key of the capture.
        database: A database handle for a test.

    Returns:
        The load outcome. The capture is None for every refusal.
    """
    loaded = load_capture(capture_id, database)
    if loaded.comparable:
        return loaded
    logger.info("Upgrade portal withheld capture %s from a comparison, reason=%s", capture_id, loaded.reason)
    return CaptureLoad(None, False, loaded.reason)


__all__ = [
    "CAPTURE_COLLECTION",
    "CAPTURE_OPERATION",
    "CAPTURE_STATE_FIELD",
    "DEFAULT_LIST_LIMIT",
    "EDGE_COLLECTION",
    "EDGE_FIELDS",
    "EDGE_INDEX_FIELDS",
    "EDGE_KEY_PREFIX",
    "INDEX_PLAN",
    "LIST_FIELDS",
    "REASON_ABSENT",
    "REASON_BAD_SCHEMA",
    "REASON_BAD_STATE",
    "REASON_CAPTURE_NOT_FOUND",
    "REASON_CAPTURE_NOT_VERIFIED",
    "REASON_DIGEST",
    "REASON_EMPTY_SIZE",
    "REASON_NO_DATABASE",
    "REASON_NO_KEY",
    "REASON_SCHEMA",
    "REASON_SCHEMA_TOO_NEW",
    "REASON_STATE_UNSET",
    "REASON_VERIFIED",
    "RUN_COLLECTION",
    "RUN_LIST_FIELDS",
    "RUN_OPERATION",
    "SCHEMA_VERSION",
    "STORAGE_BACKUP_FILE",
    "STORAGE_DATABASE",
    "STORAGE_NONE",
    "BootstrapReport",
    "CaptureListPage",
    "CaptureLoad",
    "CaptureQuery",
    "CaptureState",
    "CaptureStateMachine",
    "CaptureTransitionError",
    "IndexPlan",
    "RunListPage",
    "RunQuery",
    "StoreResult",
    "Verification",
    "bootstrap_storage",
    "build_edge",
    "canonical_json",
    "connect_database",
    "document_digest",
    "is_comparable",
    "is_readable_schema_version",
    "is_schema_version",
    "list_captures",
    "list_runs",
    "load_capture",
    "load_capture_for_comparison",
    "measure_size_bytes",
    "reset_connection",
    "schema_version_refusal",
    "size_rule_holds",
    "verify_write",
    "write_capture",
    "write_edge",
    "write_run",
]
