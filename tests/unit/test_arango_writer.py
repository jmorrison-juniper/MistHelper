"""Unit tests for ArangoDBWriter.

All python-arango interactions are mocked — no live ArangoDB required.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.db import DatabaseConfig, WriteResult


@pytest.fixture
def config() -> DatabaseConfig:
    return DatabaseConfig(
        arango_host="http://localhost:8529",
        arango_password="test",
    )


@pytest.fixture
def mock_arango_client():
    """Patch ArangoClient and return mock objects."""
    with patch("src.db.arango_writer.ArangoClient") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_sys_db = MagicMock()
        mock_client.db.return_value = mock_sys_db
        mock_sys_db.has_database.return_value = True
        mock_db = MagicMock()
        mock_client.db.side_effect = lambda name, **kw: (
            mock_sys_db if name == "_system" else mock_db
        )
        yield {
            "client_cls": mock_cls,
            "client": mock_client,
            "sys_db": mock_sys_db,
            "db": mock_db,
        }


class TestArangoDBWriterInit:
    """Tests for ArangoDBWriter.__init__."""

    def test_connects_and_ensures_database(self, config, mock_arango_client):
        from src.db.arango_writer import ArangoDBWriter

        writer = ArangoDBWriter(config)
        mock_arango_client["client_cls"].assert_called_once()
        assert writer._db is not None

    def test_creates_database_if_missing(self, config, mock_arango_client):
        from src.db.arango_writer import ArangoDBWriter

        mock_arango_client["sys_db"].has_database.return_value = False
        writer = ArangoDBWriter(config)
        mock_arango_client["sys_db"].create_database.assert_called_once_with(
            "misthelper"
        )


class TestArangoDBWriterWrite:
    """Tests for ArangoDBWriter.write."""

    def test_upsert_with_natural_pk(self, config, mock_arango_client):
        from src.db.arango_writer import ArangoDBWriter

        writer = ArangoDBWriter(config)
        mock_db = mock_arango_client["db"]
        mock_collection = MagicMock()
        mock_db.has_collection.return_value = True
        mock_db.collection.return_value = mock_collection
        mock_collection.insert.return_value = {"_key": "uuid-1"}

        strategy = {
            "type": "natural_pk",
            "primary_key": ["id"],
        }
        data = [{"id": "uuid-1", "name": "Site A", "org_id": "org-1"}]
        result = writer.write(data, "sites", strategy)

        assert result.success is True
        assert result.backend == "arangodb"
        assert result.records_written == 1
        mock_collection.insert.assert_called_once()
        call_args = mock_collection.insert.call_args
        doc = call_args[0][0]
        assert doc["_key"] == "uuid-1"
        assert "_misthelper_updated_at" in doc

    def test_auto_creates_collection(self, config, mock_arango_client):
        from src.db.arango_writer import ArangoDBWriter

        writer = ArangoDBWriter(config)
        mock_db = mock_arango_client["db"]
        mock_db.has_collection.return_value = False
        mock_collection = MagicMock()
        mock_db.create_collection.return_value = mock_collection
        mock_collection.insert.return_value = {"_key": "uuid-1"}

        strategy = {"type": "natural_pk", "primary_key": ["id"]}
        data = [{"id": "uuid-1", "name": "Test"}]
        result = writer.write(data, "new_collection", strategy)

        mock_db.create_collection.assert_called_once_with("new_collection")
        assert result.success is True

    def test_auto_increment_with_unique(self, config, mock_arango_client):
        from src.db.arango_writer import ArangoDBWriter

        writer = ArangoDBWriter(config)
        mock_db = mock_arango_client["db"]
        mock_collection = MagicMock()
        mock_db.has_collection.return_value = True
        mock_db.collection.return_value = mock_collection
        mock_collection.insert.return_value = {"_key": "auto-1"}

        strategy = {
            "type": "auto_increment_with_unique",
            "primary_key": ["misthelper_internal_id"],
        }
        data = [{"name": "Summary", "value": 42}]
        result = writer.write(data, "summaries", strategy)

        assert result.success is True
        call_doc = mock_collection.insert.call_args[0][0]
        assert "_key" in call_doc

    def test_handles_insert_error_gracefully(self, config, mock_arango_client):
        from src.db.arango_writer import ArangoDBWriter

        writer = ArangoDBWriter(config)
        mock_db = mock_arango_client["db"]
        mock_collection = MagicMock()
        mock_db.has_collection.return_value = True
        mock_db.collection.return_value = mock_collection
        mock_collection.insert.side_effect = Exception("Insert failed")

        strategy = {"type": "natural_pk", "primary_key": ["id"]}
        data = [{"id": "uuid-1"}]
        result = writer.write(data, "sites", strategy)

        assert result.records_failed == 1

    def test_updated_at_timestamp(self, config, mock_arango_client):
        from src.db.arango_writer import ArangoDBWriter

        writer = ArangoDBWriter(config)
        mock_db = mock_arango_client["db"]
        mock_collection = MagicMock()
        mock_db.has_collection.return_value = True
        mock_db.collection.return_value = mock_collection
        mock_collection.insert.return_value = {"_key": "uuid-1"}

        strategy = {"type": "natural_pk", "primary_key": ["id"]}
        data = [{"id": "uuid-1"}]
        writer.write(data, "sites", strategy)

        call_doc = mock_collection.insert.call_args[0][0]
        assert isinstance(call_doc["_misthelper_updated_at"], int)


class TestArangoDBWriterGraph:
    """Tests for graph creation and edge management."""

    def test_creates_graph_on_init(self, config, mock_arango_client):
        from src.db.arango_writer import ArangoDBWriter

        mock_db = mock_arango_client["db"]
        mock_db.has_graph.return_value = False
        writer = ArangoDBWriter(config)
        mock_db.create_graph.assert_called_once()


class TestArangoDBWriterSoftDelete:
    """Tests for soft-delete logic."""

    def test_marks_absent_entities_deleted(self, config, mock_arango_client):
        from src.db.arango_writer import ArangoDBWriter

        writer = ArangoDBWriter(config)
        mock_db = mock_arango_client["db"]
        mock_collection = MagicMock()
        mock_db.has_collection.return_value = True
        mock_db.collection.return_value = mock_collection

        existing_doc = {
            "_key": "old-uuid",
            "_misthelper_deleted_at": None,
        }
        mock_collection.all.return_value = [existing_doc]

        writer.mark_absent_as_deleted(
            "sites", current_keys=set()
        )

        mock_collection.update.assert_called_once()
        update_doc = mock_collection.update.call_args[0][0]
        assert update_doc["_misthelper_deleted_at"] is not None

    def test_clears_deleted_on_reappearance(self, config, mock_arango_client):
        from src.db.arango_writer import ArangoDBWriter

        writer = ArangoDBWriter(config)
        mock_db = mock_arango_client["db"]
        mock_collection = MagicMock()
        mock_db.has_collection.return_value = True
        mock_db.collection.return_value = mock_collection
        mock_collection.insert.return_value = {"_key": "uuid-1"}

        strategy = {"type": "natural_pk", "primary_key": ["id"]}
        data = [{"id": "uuid-1", "_misthelper_deleted_at": 1234567890}]
        writer.write(data, "sites", strategy)

        call_doc = mock_collection.insert.call_args[0][0]
        assert call_doc.get("_misthelper_deleted_at") is None


class TestArangoDBWriterSnapshot:
    """Tests for config snapshot deduplication."""

    def test_skips_duplicate_snapshot(self, config, mock_arango_client):
        from src.db.arango_writer import ArangoDBWriter

        writer = ArangoDBWriter(config)
        mock_db = mock_arango_client["db"]
        mock_collection = MagicMock()
        mock_db.has_collection.return_value = True
        mock_db.collection.return_value = mock_collection

        existing_snapshot = {"config_hash": "abc123"}
        mock_cursor = MagicMock()
        mock_cursor.__iter__ = MagicMock(
            return_value=iter([existing_snapshot])
        )
        mock_db.aql.execute.return_value = mock_cursor

        result = writer.snapshot(
            entity_type="site",
            entity_id="uuid-1",
            config_body={"name": "Test"},
            config_hash="abc123",
        )

        assert result is False
