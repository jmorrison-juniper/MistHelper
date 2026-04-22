"""ArangoDBWriter: document store backend for configuration entities.

Handles upserts, graph edge management, soft-deletes, and config snapshots
for the MistHelper polyglot database layer.  Uses batch import for high
throughput on bulk API data pulls.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from typing import Any

from arango import ArangoClient

from src.db import DatabaseConfig, WriteResult, get_logger

logger = get_logger(__name__)

GRAPH_NAME = "mist_network_topology"
IMPORT_BATCH_SIZE = 5000

EDGE_DEFINITIONS = [
    {
        "edge_collection": "OrgContainsSite",
        "from_vertex_collections": ["orgs"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "SiteContainsDevice",
        "from_vertex_collections": ["sites"],
        "to_vertex_collections": ["devices"],
    },
    {
        "edge_collection": "TemplateAssignedToSite",
        "from_vertex_collections": ["templates"],
        "to_vertex_collections": ["sites"],
    },
    {
        "edge_collection": "DeviceHasPort",
        "from_vertex_collections": ["devices"],
        "to_vertex_collections": ["ports"],
    },
    {
        "edge_collection": "ClientConnectedToDevice",
        "from_vertex_collections": ["clients"],
        "to_vertex_collections": ["devices"],
    },
]


class ArangoDBWriter:
    """Write documents to ArangoDB with upsert, graph, and snapshot support."""

    def __init__(self, config: DatabaseConfig) -> None:
        self._client = ArangoClient(hosts=config.arango_host)
        self._config = config
        self._ensure_database()
        self._db = self._client.db(
            config.arango_database,
            username=config.arango_username,
            password=config.arango_password,
        )
        self._ensure_graph()
        logger.info("arango_writer_ready", database=config.arango_database)

    def _ensure_database(self) -> None:
        """Create the misthelper database if it does not exist."""
        sys_db = self._client.db(
            "_system",
            username=self._config.arango_username,
            password=self._config.arango_password,
        )
        if not sys_db.has_database(self._config.arango_database):
            sys_db.create_database(self._config.arango_database)
            logger.info("database_created", name=self._config.arango_database)

    def _ensure_graph(self) -> None:
        """Create the network topology graph if it does not exist."""
        if not self._db.has_graph(GRAPH_NAME):
            self._db.create_graph(GRAPH_NAME, edge_definitions=EDGE_DEFINITIONS)
            logger.info("graph_created", name=GRAPH_NAME)

    def _ensure_collection(self, name: str) -> Any:
        """Return collection, creating it if needed."""
        if not self._db.has_collection(name):
            self._db.create_collection(name)
            logger.info("collection_created", name=name)
        return self._db.collection(name)

    def write(self, data: list[dict], collection_name: str, strategy: dict) -> WriteResult:
        """Upsert documents using batch import for performance."""
        collection = self._ensure_collection(collection_name)
        if not data:
            return WriteResult(
                success=True,
                backend="arangodb",
                records_written=0,
                records_failed=0,
            )

        docs = [self._prepare_document(r, strategy) for r in data]
        written, failed = self._batch_import(collection, docs)

        return WriteResult(
            success=(failed == 0),
            backend="arangodb",
            records_written=written,
            records_failed=failed,
        )

    def _batch_import(
        self,
        collection: Any,
        docs: list[dict],
    ) -> tuple[int, int]:
        """Import documents in batches with on_duplicate=replace."""
        written = 0
        failed = 0
        for start in range(0, len(docs), IMPORT_BATCH_SIZE):
            batch = docs[start : start + IMPORT_BATCH_SIZE]
            try:
                result = collection.import_bulk(
                    batch,
                    on_duplicate="replace",
                )
                written += result.get("created", 0)
                written += result.get("updated", 0)
                failed += result.get("errors", 0)
            except Exception as error:
                failed += len(batch)
                logger.warning(
                    "batch_import_failed",
                    collection=collection.name,
                    batch_size=len(batch),
                    error=str(error),
                )
        logger.info(
            "import_complete",
            collection=collection.name,
            written=written,
            failed=failed,
        )
        return written, failed

    def _prepare_document(self, record: dict, strategy: dict) -> dict:
        """Add _key, timestamps, and clear soft-delete flag."""
        doc = dict(record)
        strategy_type = strategy.get("type", "natural_pk")
        primary_keys = strategy.get("primary_key", ["id"])

        if strategy_type == "auto_increment_with_unique":
            doc["_key"] = str(uuid.uuid4())
        else:
            key_value = doc.get(primary_keys[0], str(uuid.uuid4()))
            doc["_key"] = str(key_value)

        doc["_misthelper_updated_at"] = int(time.time())
        doc["_misthelper_deleted_at"] = None
        return doc

    def mark_absent_as_deleted(self, collection_name: str, current_keys: set[str]) -> None:
        """Soft-delete documents whose keys are absent from current data."""
        if not self._db.has_collection(collection_name):
            return

        collection = self._db.collection(collection_name)
        now = int(time.time())

        for doc in collection.all():
            key = doc.get("_key")
            already_deleted = doc.get("_misthelper_deleted_at")
            if key not in current_keys and not already_deleted:
                collection.update({"_key": key, "_misthelper_deleted_at": now})
                logger.debug("soft_deleted", collection=collection_name, key=key)

    def snapshot(
        self,
        entity_type: str,
        entity_id: str,
        config_body: dict,
        config_hash: str | None = None,
        trigger: str = "api_pull",
    ) -> bool:
        """Store a config snapshot, skipping if hash is unchanged."""
        if config_hash is None:
            config_hash = hashlib.sha256(json.dumps(config_body, sort_keys=True).encode()).hexdigest()

        collection = self._ensure_collection("config_snapshots")

        cursor = self._db.aql.execute(
            "FOR doc IN config_snapshots "
            "FILTER doc.entity_id == @eid "
            "SORT doc.timestamp DESC LIMIT 1 "
            "RETURN doc",
            bind_vars={"eid": entity_id},
        )
        for existing in cursor:
            if existing.get("config_hash") == config_hash:
                return False

        snapshot_doc = {
            "_key": str(uuid.uuid4()),
            "entity_type": entity_type,
            "entity_id": entity_id,
            "timestamp": int(time.time()),
            "config_hash": config_hash,
            "config_body": config_body,
            "trigger": trigger,
            "_misthelper_updated_at": int(time.time()),
        }
        collection.insert(snapshot_doc)
        logger.info(
            "snapshot_stored",
            entity_type=entity_type,
            entity_id=entity_id,
            trigger=trigger,
        )
        return True

    def close(self) -> None:
        """Close the ArangoDB client connection."""
        self._client.close()
        logger.info("arango_writer_closed")
