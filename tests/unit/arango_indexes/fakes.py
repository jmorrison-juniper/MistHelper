"""Provide strict SDK handles for the real ArangoDB writer tests."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from threading import RLock
from typing import Any
from unittest.mock import MagicMock, create_autospec, patch
from uuid import uuid4

from arango import ArangoClient
from arango.collection import StandardCollection
from arango.database import StandardDatabase
from arango.exceptions import IndexCreateError
from arango.request import Request
from arango.response import Response

from src.db import DatabaseConfig
from src.db.arango_writer import GRAPH_EDGE_DEFINITIONS, ArangoDBWriter


@dataclass
class IndexCollectionState:
    """Retain fake server state without changing caller records."""

    indexes: dict[str, dict[str, Any]] = field(default_factory=dict)
    documents: dict[str, dict[str, Any]] = field(default_factory=dict)
    actions: list[tuple[str, Any]] = field(default_factory=list)
    failures: dict[str, Exception] = field(default_factory=dict)
    guard: RLock = field(default_factory=RLock)


class ArangoIndexCollectionFake:
    """Model equal-index reuse and replacement imports behind strict SDK methods."""

    def __init__(self, name: str) -> None:
        """Create a collection handle with the actual SDK method signatures."""
        self.state = IndexCollectionState()
        self.handle = create_autospec(StandardCollection, instance=True, spec_set=True)
        self.handle.name = name
        self.handle.add_index.side_effect = self.add_index
        self.handle.import_bulk.side_effect = self.import_bulk

    def add_index(self, definition: dict[str, Any]) -> dict[str, Any]:
        """Record each request and return the existing equal field index."""
        with self.state.guard:
            self.state.actions.append(("index", deepcopy(definition)))
            field_name = definition["fields"][0]
            error = self.state.failures.pop(field_name, None)
            if error is not None:
                raise error
            existing = self.state.indexes.get(field_name)
            if existing is not None:
                return {**deepcopy(existing), "isNewlyCreated": False}
            index = {**deepcopy(definition), "id": str(len(self.state.indexes) + 1), "unique": False}
            self.state.indexes[field_name] = index
            return {**deepcopy(index), "isNewlyCreated": True}

    def import_bulk(self, documents: list[dict[str, Any]], on_duplicate: str) -> dict[str, int]:
        """Apply the existing replacement behavior and report exact row counts."""
        if on_duplicate != "replace":
            raise ValueError("The writer must retain its replacement import option.")
        with self.state.guard:
            self.state.actions.append(("import", {"records": len(documents), "on_duplicate": on_duplicate}))
            created = 0
            updated = 0
            for document in documents:
                key = document["_key"]
                updated += int(key in self.state.documents)
                created += int(key not in self.state.documents)
                self.state.documents[key] = deepcopy(document)
            return {"created": created, "updated": updated, "errors": 0}

    @staticmethod
    def index_error(status: int) -> IndexCreateError:
        """Create the real SDK exception for a failed index response."""
        response = Response("post", "http://127.0.0.1:9609/_api/index", {}, status, "Index creation failed", "")
        response.is_success = False
        response.error_message = "The declared index could not be created."
        request = Request("post", "/_api/index", data={"type": "persistent", "fields": ["org_id"]})
        return IndexCreateError(response, request)


class ArangoIndexDatabaseFake:
    """Keep collection state behind the actual SDK database interface."""

    def __init__(self) -> None:
        """Keep constructor probes offline and graph definitions current."""
        self.collections: dict[str, ArangoIndexCollectionFake] = {}
        self.handle = create_autospec(StandardDatabase, instance=True, spec_set=True)
        self.handle.configure_mock(
            **{
                "has_database.return_value": True,
                "has_collection.side_effect": self.collections.__contains__,
                "collection.side_effect": self.collection,
                "create_collection.side_effect": self.create_collection,
                "has_graph.return_value": True,
            }
        )
        self.handle.graph.return_value.edge_definitions.return_value = deepcopy(GRAPH_EDGE_DEFINITIONS)

    def collection(self, name: str) -> MagicMock:
        """Return only a collection that the fake database actually holds."""
        return self.collections[name].handle

    def create_collection(self, name: str, edge: bool = False) -> MagicMock:
        """Reject duplicate creation instead of concealing a collection race."""
        if name in self.collections:
            raise ValueError("The collection already exists.")
        self.collections[name] = ArangoIndexCollectionFake(name)
        return self.collections[name].handle


class ArangoIndexWriterHarness:
    """Construct real writers against one owned fake database scope."""

    def __init__(self, config: DatabaseConfig | None = None, database: ArangoIndexDatabaseFake | None = None) -> None:
        """Give each independent test a distinct configured database scope."""
        self.config = config or DatabaseConfig(
            arango_host="http://127.0.0.1:9609",
            arango_database=f"misthelper-tmp-issue3309-{uuid4().hex}",
            arango_password="",
        )
        self.database = database or ArangoIndexDatabaseFake()
        self.client = create_autospec(ArangoClient, instance=True, spec_set=True)
        self.client.db.return_value = self.database.handle
        self.writers: list[ArangoDBWriter] = []

    def writer(self) -> ArangoDBWriter:
        """Run the actual constructor without a live connection."""
        with patch("src.db.arango_writer.ArangoClient", autospec=True, return_value=self.client):
            writer = ArangoDBWriter(self.config)
        self.writers.append(writer)
        return writer

    def close(self) -> None:
        """Close every writer created by this test."""
        for writer in self.writers:
            writer.close()
