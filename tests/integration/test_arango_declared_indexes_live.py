"""Measure declared indexes only in an explicitly owned isolated ArangoDB store."""

from collections.abc import Iterator
from copy import deepcopy
from os import environ
from typing import Any
from unittest.mock import patch
from urllib.parse import urlparse
from uuid import uuid4

import pytest
import structlog
from arango.collection import StandardCollection

from src.foundation.persistence.db import DatabaseConfig
from src.foundation.persistence.db.writers.arango_writer import ArangoDBWriter
from src.foundation.support.refactors.endpoint_primary_key_strategies import ENDPOINT_PRIMARY_KEY_STRATEGIES

logger = structlog.get_logger(__name__)


class IsolatedArangoIndexTarget:
    """Reject every URL outside the issue's loopback test port range."""

    @staticmethod
    def configuration(url: str) -> DatabaseConfig:
        """Validate the explicit target before any SDK connection."""
        logger.info("arango_index_test_target_check")
        parsed = urlparse(url)
        try:
            port = parsed.port
        except ValueError as error:
            logger.error("arango_index_test_target_invalid", checked_count=1)
            raise ValueError("The isolated ArangoDB test URL has an invalid port.") from error
        checks = (
            parsed.scheme == "http",
            parsed.netloc == f"127.0.0.1:{port}",
            port is not None and 9600 <= port <= 9699,
            parsed.path in ("", "/"),
            not (parsed.query or parsed.fragment),
        )
        if not all(checks):
            logger.error("arango_index_test_target_invalid", checked_count=1)
            raise ValueError("The isolated ArangoDB test requires 127.0.0.1 and a port from 9600 through 9699.")
        logger.debug("arango_index_test_target_ready", checked_count=1)
        return DatabaseConfig(
            arango_host=url, arango_database=f"misthelper-tmp-issue3309-{uuid4().hex}", arango_password=""
        )


class IsolatedIndexQueryProof:
    """Read exact documents, field indexes, and optimizer plans from the owned store."""

    @staticmethod
    def rows() -> list[dict[str, Any]]:
        """Create selective records without any production identifier."""
        return [
            {
                "uuid": f"action-{number}",
                "org_id": "issue3309-org",
                "site_id": f"issue3309-site-{number % 10}",
                "category": "wired",
                "symptom": "link_down",
                "status": "selected" if number == 0 else "open",
                "details": {"number": number, "enabled": True},
            }
            for number in range(1001)
        ]

    @staticmethod
    def documents(writer: ArangoDBWriter) -> list[dict[str, Any]]:
        """Compare stored keys and values without server revision identifiers."""
        logger.info("arango_index_documents_read")
        documents = list(
            writer._db.aql.execute(
                'FOR action IN listOrgMarvisActions SORT action._key RETURN UNSET(action, "_id", "_rev")'
            )
        )
        logger.debug("arango_index_documents_read_complete", checked_count=len(documents))
        return documents

    @staticmethod
    def query_plan(writer: ArangoDBWriter) -> list[list[str]]:
        """Inspect the normal optimizer choice without an index hint."""
        logger.info("arango_index_query_plan")
        plan = writer._db.aql.explain(
            "FOR action IN listOrgMarvisActions FILTER action.status == @status RETURN action.uuid",
            bind_vars={"status": "selected"},
        )
        nodes = [node for node in plan["nodes"] if node["type"] == "IndexNode"]
        logger.debug("arango_index_query_explained", checked_count=1, index_node_count=len(nodes))
        return [index["fields"] for node in nodes for index in node["indexes"]]

    @staticmethod
    def persistent_fields(collection: StandardCollection) -> list[tuple[list[str], bool]]:
        """Exclude the unchanged primary index from the declared-field measurement."""
        logger.info("arango_index_list", collection=collection.name)
        indexes = collection.indexes()
        fields = [(index["fields"], index["unique"]) for index in indexes if index["type"] == "persistent"]
        logger.debug("arango_index_list_complete", checked_count=len(indexes), persistent_count=len(fields))
        return fields

    @staticmethod
    def selected_uuids(writer: ArangoDBWriter) -> list[str]:
        """Verify the selective query's exact result through the normal optimizer."""
        logger.info("arango_index_query_run")
        result = list(
            writer._db.aql.execute(
                "FOR action IN listOrgMarvisActions FILTER action.status == @status RETURN action.uuid",
                bind_vars={"status": "selected"},
            )
        )
        logger.debug("arango_index_query_complete", checked_count=len(result))
        return result


@pytest.fixture
def owned_writer() -> Iterator[ArangoDBWriter]:
    """Create and remove only an issue-prefixed database on the explicit test target."""
    url = environ.get("MISTHELPER_ISSUE3309_ARANGO_URL")
    if url is None:
        pytest.skip("Unmeasured: MISTHELPER_ISSUE3309_ARANGO_URL does not name an owned isolated ArangoDB capability.")
    config = IsolatedArangoIndexTarget.configuration(url)
    writer = ArangoDBWriter(config)
    try:
        yield writer
    finally:
        logger.info("arango_index_test_database_remove", database=config.arango_database)
        try:
            writer._client.db("_system").delete_database(config.arango_database)
            logger.debug("arango_index_test_database_removed", checked_count=1)
        finally:
            writer.close()


class TestIsolatedArangoDeclaredIndexes:
    """Prove equal-index reuse, preserved documents, and a real index-based query plan."""

    def test_declared_indexes_preserve_documents_and_change_the_query_plan(self, owned_writer: ArangoDBWriter) -> None:
        """Compare the normal query plan before and after a declared-index write."""
        api_name = "listOrgMarvisActions"
        strategy = ENDPOINT_PRIMARY_KEY_STRATEGIES[api_name]
        initial_strategy = {**deepcopy(strategy), "indexes": []}
        rows = IsolatedIndexQueryProof.rows()
        with patch("src.foundation.persistence.db.writers.arango_writer.time.time", return_value=1770000000):
            first = owned_writer.write(rows, api_name, initial_strategy)
            before = IsolatedIndexQueryProof.documents(owned_writer)
            before_plan = IsolatedIndexQueryProof.query_plan(owned_writer)
            second = owned_writer.write(rows, api_name, strategy)
            after = IsolatedIndexQueryProof.documents(owned_writer)
        collection = owned_writer._db.collection(api_name)
        fields = IsolatedIndexQueryProof.persistent_fields(collection)
        assert sorted(fields) == sorted(([name], False) for name in strategy["indexes"])
        assert (first.success, second.success) == (True, True)
        assert (first.records_written, second.records_written) == (1001, 1001)
        assert before == after
        after_plan = IsolatedIndexQueryProof.query_plan(owned_writer)
        assert (before_plan, after_plan) == ([], [["status"]])
        assert IsolatedIndexQueryProof.selected_uuids(owned_writer) == ["action-0"]

    def test_equal_index_return_preserves_identity_and_record_count(self, owned_writer: ArangoDBWriter) -> None:
        """Use the real server's existing-index response without creating a duplicate."""
        api_name = "listOrgMarvisActions"
        strategy = ENDPOINT_PRIMARY_KEY_STRATEGIES[api_name]
        first = owned_writer.write([{"uuid": "action-1", "status": "open"}], api_name, strategy)
        collection = owned_writer._db.collection(api_name)
        original = {
            tuple(index["fields"]): index["id"] for index in collection.indexes() if index["type"] == "persistent"
        }
        repeated = collection.add_index({"type": "persistent", "fields": ["status"]})
        second = owned_writer.write([{"uuid": "action-1", "status": "closed"}], api_name, strategy)
        current = {
            tuple(index["fields"]): index["id"] for index in collection.indexes() if index["type"] == "persistent"
        }
        assert current == original
        assert (repeated["id"], repeated["isNewlyCreated"]) == (original[("status",)], False)
        assert (first.records_written, second.records_written, collection.count()) == (1, 1, 1)
        assert collection.get("action-1")["status"] == "closed"
