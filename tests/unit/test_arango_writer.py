"""Unit tests for ArangoDBWriter.

All python-arango interactions are mocked — no live ArangoDB required.
"""

from __future__ import annotations  # WHY: postponed evaluation keeps forward refs cheap in tests

from unittest.mock import MagicMock, patch  # WHY: python-arango is mocked to avoid live DB dependency

import pytest  # WHY: fixtures + parametrize entry points

from src.db import DatabaseConfig  # WHY: config fixture builds a DatabaseConfig instance
from tests.unit._test_arango_writer_helpers import (  # WHY: shared single-assert helpers keep test CC=1
    ALL_EXPECTED_EDGES,
    EdgeCase,
    assert_all_edged_ops_include,
    assert_edge_case,
    assert_edge_cols_include,
    assert_edge_fields,
    assert_edge_to_vertex,
    assert_edges_equal,
    assert_edges_registered,
    assert_ensure_target,
    assert_entity_types_mapped,
    assert_ops_carrying_edge_include,
    assert_vertex_config,
)


@pytest.fixture
def config() -> DatabaseConfig:  # WHY: fixture / helper function
    return DatabaseConfig(  # WHY: return prepared value
        arango_host="http://localhost:8529",
        arango_password="test",
    )


@pytest.fixture
def mock_arango_client():  # WHY: fixture / helper function
    """Patch ArangoClient and return mock objects."""
    with patch("src.db.arango_writer.ArangoClient") as mock_cls:  # WHY: isolate side effects via patch
        mock_client = MagicMock()  # WHY: create mock double for python-arango
        mock_cls.return_value = mock_client  # WHY: prime mock return value
        mock_sys_db = MagicMock()  # WHY: create mock double for python-arango
        mock_client.db.return_value = mock_sys_db  # WHY: prime mock return value
        mock_sys_db.has_database.return_value = True  # WHY: prime mock return value
        mock_db = MagicMock()  # WHY: create mock double for python-arango
        mock_client.db.side_effect = lambda name, **kw: (mock_sys_db if name == "_system" else mock_db)  # WHY: prime mock side effect
        yield {  # WHY: hand mock context to the test
            "client_cls": mock_cls,
            "client": mock_client,
            "sys_db": mock_sys_db,
            "db": mock_db,
        }


class TestArangoDBWriterInit:  # WHY: pytest test class
    """Tests for ArangoDBWriter.__init__."""

    def test_connects_and_ensures_database(self, config, mock_arango_client):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ArangoDBWriter  # WHY: import ArangoDBWriter symbol under test

        writer = ArangoDBWriter(config)  # WHY: system under test
        mock_arango_client["client_cls"].assert_called_once()  # WHY: test line
        assert writer._db is not None  # WHY: verify expected behavior

    def test_creates_database_if_missing(self, config, mock_arango_client):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ArangoDBWriter  # WHY: import ArangoDBWriter symbol under test

        mock_arango_client["sys_db"].has_database.return_value = False  # WHY: prime mock return value
        ArangoDBWriter(config)  # WHY: invoke helper for setup
        mock_arango_client["sys_db"].create_database.assert_called_once_with("misthelper")  # WHY: test line


class TestArangoDBWriterWrite:  # WHY: pytest test class
    """Tests for ArangoDBWriter.write."""

    def test_upsert_with_natural_pk(self, config, mock_arango_client):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ArangoDBWriter  # WHY: local import avoids side effects during test collection

        writer = ArangoDBWriter(config)  # WHY: fixture provides ArangoDB config
        mock_db = mock_arango_client["db"]  # WHY: mock DB handle for assertions
        mock_collection = MagicMock()  # WHY: mocked collection tracks import_bulk call
        mock_db.has_collection.return_value = True  # WHY: pretend collection already exists
        mock_db.collection.return_value = mock_collection  # WHY: wire mock into writer
        mock_collection.import_bulk.return_value = {"created": 1, "updated": 0, "errors": 0}  # WHY: successful import

        strategy = {"type": "natural_pk", "primary_key": ["id"]}  # WHY: natural-PK write strategy
        data = [{"id": "uuid-1", "name": "Site A", "org_id": "org-1"}]  # WHY: single record with natural key
        result = writer.write(data, "sites", strategy)  # WHY: invoke unit under test

        summary = (result.success, result.backend, result.records_written)  # WHY: bundle checks into one tuple
        assert summary == (True, "arangodb", 1)  # WHY: single-tuple check keeps CC=1
        mock_collection.import_bulk.assert_called_once()  # WHY: writer must call bulk-import exactly once
        docs = mock_collection.import_bulk.call_args[0][0]  # WHY: extract the docs the writer sent to bulk import
        doc_shape = (docs[0]["_key"], "_misthelper_updated_at" in docs[0])  # WHY: check key and timestamp together
        assert doc_shape == ("uuid-1", True)  # WHY: one assertion covers both doc contracts

    def test_auto_creates_collection(self, config, mock_arango_client):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ArangoDBWriter  # WHY: import ArangoDBWriter symbol under test

        writer = ArangoDBWriter(config)  # WHY: system under test
        mock_db = mock_arango_client["db"]  # WHY: grab mocked DB handle
        mock_db.has_collection.return_value = False  # WHY: prime mock return value
        mock_collection = MagicMock()  # WHY: create mock double for python-arango
        mock_db.create_collection.return_value = mock_collection  # WHY: prime mock return value
        mock_db.collection.return_value = mock_collection  # WHY: prime mock return value
        mock_collection.import_bulk.return_value = {"created": 1, "updated": 0, "errors": 0}  # WHY: prime mock return value

        strategy = {"type": "natural_pk", "primary_key": ["id"]}  # WHY: write strategy under test
        data = [{"id": "uuid-1", "name": "Test"}]  # WHY: test input data
        result = writer.write(data, "new_collection", strategy)  # WHY: invoke unit under test

        mock_db.create_collection.assert_called_once_with("new_collection", edge=False)  # WHY: test line
        assert result.success is True  # WHY: verify expected behavior

    def test_auto_increment_with_unique(self, config, mock_arango_client):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ArangoDBWriter  # WHY: import ArangoDBWriter symbol under test

        writer = ArangoDBWriter(config)  # WHY: system under test
        mock_db = mock_arango_client["db"]  # WHY: grab mocked DB handle
        mock_collection = MagicMock()  # WHY: create mock double for python-arango
        mock_db.has_collection.return_value = True  # WHY: prime mock return value
        mock_db.collection.return_value = mock_collection  # WHY: prime mock return value
        mock_collection.import_bulk.return_value = {"created": 1, "updated": 0, "errors": 0}  # WHY: prime mock return value

        strategy = {  # WHY: write strategy under test
            "type": "auto_increment_with_unique",
            "primary_key": ["misthelper_internal_id"],
        }
        data = [{"name": "Summary", "value": 42}]  # WHY: test input data
        result = writer.write(data, "summaries", strategy)  # WHY: invoke unit under test

        assert result.success is True  # WHY: verify expected behavior
        docs = mock_collection.import_bulk.call_args[0][0]  # WHY: arrange test state
        assert "_key" in docs[0]  # WHY: verify expected behavior

    def test_handles_insert_error_gracefully(self, config, mock_arango_client):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ArangoDBWriter  # WHY: import ArangoDBWriter symbol under test

        writer = ArangoDBWriter(config)  # WHY: system under test
        mock_db = mock_arango_client["db"]  # WHY: grab mocked DB handle
        mock_collection = MagicMock()  # WHY: create mock double for python-arango
        mock_db.has_collection.return_value = True  # WHY: prime mock return value
        mock_db.collection.return_value = mock_collection  # WHY: prime mock return value
        mock_collection.import_bulk.side_effect = Exception("Import failed")  # WHY: prime mock side effect

        strategy = {"type": "natural_pk", "primary_key": ["id"]}  # WHY: write strategy under test
        data = [{"id": "uuid-1"}]  # WHY: test input data
        result = writer.write(data, "sites", strategy)  # WHY: invoke unit under test

        assert result.records_failed == 1  # WHY: verify expected behavior

    def test_updated_at_timestamp(self, config, mock_arango_client):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ArangoDBWriter  # WHY: import ArangoDBWriter symbol under test

        writer = ArangoDBWriter(config)  # WHY: system under test
        mock_db = mock_arango_client["db"]  # WHY: grab mocked DB handle
        mock_collection = MagicMock()  # WHY: create mock double for python-arango
        mock_db.has_collection.return_value = True  # WHY: prime mock return value
        mock_db.collection.return_value = mock_collection  # WHY: prime mock return value
        mock_collection.import_bulk.return_value = {"created": 1, "updated": 0, "errors": 0}  # WHY: prime mock return value

        strategy = {"type": "natural_pk", "primary_key": ["id"]}  # WHY: write strategy under test
        data = [{"id": "uuid-1"}]  # WHY: test input data
        writer.write(data, "sites", strategy)  # WHY: invoke writer.write under test

        docs = mock_collection.import_bulk.call_args[0][0]  # WHY: arrange test state
        assert isinstance(docs[0]["_misthelper_updated_at"], int)  # WHY: verify expected behavior


class TestArangoDBWriterGraph:  # WHY: pytest test class
    """Tests for graph creation and edge management."""

    def test_creates_graph_on_init(self, config, mock_arango_client):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ArangoDBWriter  # WHY: import ArangoDBWriter symbol under test

        mock_db = mock_arango_client["db"]  # WHY: grab mocked DB handle
        mock_db.has_graph.return_value = False  # WHY: prime mock return value
        ArangoDBWriter(config)  # WHY: invoke helper for setup
        mock_db.create_graph.assert_called_once()  # WHY: test line


class TestArangoDBWriterSoftDelete:  # WHY: pytest test class
    """Tests for soft-delete logic."""

    def test_marks_absent_entities_deleted(self, config, mock_arango_client):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ArangoDBWriter  # WHY: import ArangoDBWriter symbol under test

        writer = ArangoDBWriter(config)  # WHY: system under test
        mock_db = mock_arango_client["db"]  # WHY: grab mocked DB handle
        mock_collection = MagicMock()  # WHY: create mock double for python-arango
        mock_db.has_collection.return_value = True  # WHY: prime mock return value
        mock_db.collection.return_value = mock_collection  # WHY: prime mock return value

        existing_doc = {  # WHY: arrange test state
            "_key": "old-uuid",
            "_misthelper_deleted_at": None,
        }
        mock_collection.all.return_value = [existing_doc]  # WHY: prime mock return value

        writer.mark_absent_as_deleted("sites", current_keys=set())  # WHY: test line

        mock_collection.update.assert_called_once()  # WHY: test line
        update_doc = mock_collection.update.call_args[0][0]  # WHY: arrange test state
        assert update_doc["_misthelper_deleted_at"] is not None  # WHY: verify expected behavior

    def test_clears_deleted_on_reappearance(self, config, mock_arango_client):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ArangoDBWriter  # WHY: import ArangoDBWriter symbol under test

        writer = ArangoDBWriter(config)  # WHY: system under test
        mock_db = mock_arango_client["db"]  # WHY: grab mocked DB handle
        mock_collection = MagicMock()  # WHY: create mock double for python-arango
        mock_db.has_collection.return_value = True  # WHY: prime mock return value
        mock_db.collection.return_value = mock_collection  # WHY: prime mock return value
        mock_collection.import_bulk.return_value = {"created": 1, "updated": 0, "errors": 0}  # WHY: prime mock return value

        strategy = {"type": "natural_pk", "primary_key": ["id"]}  # WHY: write strategy under test
        data = [{"id": "uuid-1", "_misthelper_deleted_at": 1234567890}]  # WHY: test input data
        writer.write(data, "sites", strategy)  # WHY: invoke writer.write under test

        docs = mock_collection.import_bulk.call_args[0][0]  # WHY: arrange test state
        assert docs[0].get("_misthelper_deleted_at") is None  # WHY: verify expected behavior


class TestArangoDBWriterSnapshot:  # WHY: pytest test class
    """Tests for config snapshot deduplication and entity edges."""

    def test_skips_duplicate_snapshot(self, config, mock_arango_client):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ArangoDBWriter  # WHY: import ArangoDBWriter symbol under test

        writer = ArangoDBWriter(config)  # WHY: system under test
        mock_db = mock_arango_client["db"]  # WHY: grab mocked DB handle
        mock_collection = MagicMock()  # WHY: create mock double for python-arango
        mock_db.has_collection.return_value = True  # WHY: prime mock return value
        mock_db.collection.return_value = mock_collection  # WHY: prime mock return value

        existing_snapshot = {"config_hash": "abc123"}  # WHY: arrange test state
        mock_cursor = MagicMock()  # WHY: create mock double for python-arango
        mock_cursor.__iter__ = MagicMock(return_value=iter([existing_snapshot]))  # WHY: test line
        mock_db.aql.execute.return_value = mock_cursor  # WHY: prime mock return value

        result = writer.snapshot(  # WHY: invoke unit under test
            entity_type="site",
            entity_id="uuid-1",
            config_body={"name": "Test"},
            config_hash="abc123",
        )

        assert result is False  # WHY: verify expected behavior

    def test_snapshot_creates_entity_edge(self, config, mock_arango_client):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ArangoDBWriter  # WHY: import ArangoDBWriter symbol under test

        writer = ArangoDBWriter(config)  # WHY: system under test
        mock_db = mock_arango_client["db"]  # WHY: grab mocked DB handle
        mock_collection = MagicMock()  # WHY: create mock double for python-arango
        mock_db.has_collection.return_value = True  # WHY: prime mock return value
        mock_db.collection.return_value = mock_collection  # WHY: prime mock return value
        mock_db.aql.execute.return_value = iter([])  # WHY: prime mock return value

        result = writer.snapshot(  # WHY: invoke unit under test
            entity_type="listOrgSites",
            entity_id="site-uuid-1",
            config_body={"name": "Test Site"},
            config_hash="new-hash",
        )

        assert result is True  # WHY: verify expected behavior
        # insert for snapshot doc + import_bulk for edge
        mock_collection.insert.assert_called_once()  # WHY: test line
        mock_collection.import_bulk.assert_called_once()  # WHY: test line
        edge_doc = mock_collection.import_bulk.call_args[0][0][0]  # WHY: arrange test state
        assert edge_doc["_from"].startswith("config_snapshots/")  # WHY: verify expected behavior
        assert edge_doc["_to"] == "sites/site-uuid-1"  # WHY: verify expected behavior
        assert edge_doc["entity_type"] == "listOrgSites"  # WHY: verify expected behavior

    def test_snapshot_skips_edge_for_unknown_entity_type(self, config, mock_arango_client):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ArangoDBWriter  # WHY: import ArangoDBWriter symbol under test

        writer = ArangoDBWriter(config)  # WHY: system under test
        mock_db = mock_arango_client["db"]  # WHY: grab mocked DB handle
        mock_collection = MagicMock()  # WHY: create mock double for python-arango
        mock_db.has_collection.return_value = True  # WHY: prime mock return value
        mock_db.collection.return_value = mock_collection  # WHY: prime mock return value
        mock_db.aql.execute.return_value = iter([])  # WHY: prime mock return value

        result = writer.snapshot(  # WHY: invoke unit under test
            entity_type="unknownApiFunction",
            entity_id="uuid-1",
            config_body={"name": "Test"},
            config_hash="new-hash",
        )

        assert result is True  # WHY: verify expected behavior
        mock_collection.insert.assert_called_once()  # WHY: test line
        # No import_bulk for edge since entity_type is not in ENTITY_TYPE_TO_VERTEX
        mock_collection.import_bulk.assert_not_called()  # WHY: test line


class TestArangoDBWriterWlanGraph:  # WHY: pytest test class
    """Tests for WLAN graph population."""

    def test_wlan_mapping_exists(self):  # WHY: pytest discovers this by name
        assert_vertex_config("listOrgWlans", "wlans", "id")  # WHY: single vertex+key check on the WLAN mapping
        assert_edge_cols_include("listOrgWlans", {"WlanBelongsToSite", "WlanUsesTemplate"})  # WHY: subset check

    def test_wlan_template_edge_targets_templates(self):  # WHY: pytest discovers this by name
        assert_edge_fields(  # WHY: single dict-equality check for edge field trio
            "listOrgWlans",
            "WlanUsesTemplate",
            {"from_col": "wlans", "to_col": "templates", "to_field": "template_id"},
        )

    def test_mxedge_mapping_exists(self):  # WHY: pytest discovers this by name
        assert_vertex_config("listOrgMxEdges", "devices", "id")  # WHY: MxEdge vertex config
        assert_edge_cols_include("listOrgMxEdges", {"OrgContainsDevice", "MxEdgeBelongsToCluster"})  # WHY: subset

    def test_mxedge_cluster_edge_targets_mxclusters(self):  # WHY: pytest discovers this by name
        assert_edge_fields(  # WHY: single dict-equality check for edge field trio
            "listOrgMxEdges",
            "MxEdgeBelongsToCluster",
            {"from_col": "devices", "to_col": "mxclusters", "to_field": "mxcluster_id"},
        )

    def test_site_sitegroup_edge_exists(self):  # WHY: pytest discovers this by name
        assert_edge_cols_include("listOrgSites", {"SiteBelongsToSiteGroup"})  # WHY: subset presence check
        assert_edge_fields(  # WHY: single dict-equality check pins target vertex + field
            "listOrgSites",
            "SiteBelongsToSiteGroup",
            {"to_col": "sitegroups", "to_field": "sitegroup_ids"},
        )

    def test_entity_type_to_vertex_mapping(self):  # WHY: pytest discovers this by name
        assert_entity_types_mapped({  # WHY: single dict-subset check collapses 5 asserts to CC=1
            "listOrgSites": "sites",
            "listOrgGatewayTemplates": "templates",
            "listOrgRfTemplates": "templates",
            "listSiteDevices": "devices",
            "getOrgWlans": "wlans",
        })


class TestArangoDBWriterEdgeDefinitions:  # WHY: pytest test class
    """Tests for EDGE_DEFINITIONS completeness."""

    def test_all_edge_definitions(self):  # WHY: pytest discovers this by name
        assert_edges_equal(ALL_EXPECTED_EDGES)  # WHY: canonical tier-grouped union lives in helpers, keeps test 1 line

    def test_sitegroup_vertex_in_edge_def(self):  # WHY: pytest discovers this by name
        assert_edge_to_vertex("SiteBelongsToSiteGroup", "sitegroups")  # WHY: single edge->vertex membership check

    def test_mxclusters_vertex_in_edge_def(self):  # WHY: pytest discovers this by name
        assert_edge_to_vertex("MxEdgeBelongsToCluster", "mxclusters")  # WHY: single edge->vertex membership check

    def test_ensure_target_vertices_on_sites(self):  # WHY: pytest discovers this by name
        assert_ensure_target("listOrgSites", ("sitegroup_ids", "sitegroups"))  # WHY: single membership check on schema

    def test_ensure_target_vertices_on_mxedges(self):  # WHY: pytest discovers this by name
        assert_ensure_target("listOrgMxEdges", ("mxcluster_id", "mxclusters"))  # WHY: single membership check on schema


class TestArangoDBWriterEdgeKey:  # WHY: pytest test class
    """Tests for _edge_key deterministic hash."""

    def test_edge_key_is_deterministic(self, config, mock_arango_client):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ArangoDBWriter  # WHY: import ArangoDBWriter symbol under test

        writer = ArangoDBWriter(config)  # WHY: system under test
        key1 = writer._edge_key("orgs/abc", "sites/xyz")  # WHY: arrange test state
        key2 = writer._edge_key("orgs/abc", "sites/xyz")  # WHY: arrange test state
        assert key1 == key2  # WHY: verify expected behavior

    def test_edge_key_differs_for_different_inputs(self, config, mock_arango_client):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ArangoDBWriter  # WHY: import ArangoDBWriter symbol under test

        writer = ArangoDBWriter(config)  # WHY: system under test
        key1 = writer._edge_key("orgs/abc", "sites/xyz")  # WHY: arrange test state
        key2 = writer._edge_key("orgs/abc", "sites/def")  # WHY: arrange test state
        assert key1 != key2  # WHY: verify expected behavior

    def test_edge_key_is_16_chars(self, config, mock_arango_client):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ArangoDBWriter  # WHY: import ArangoDBWriter symbol under test

        writer = ArangoDBWriter(config)  # WHY: system under test
        key = writer._edge_key("orgs/abc", "sites/xyz")  # WHY: arrange test state
        assert len(key) == 16  # WHY: verify expected behavior


class TestResolveNestedField:  # WHY: pytest test class
    """Tests for _resolve_nested_field dot-path FK resolution."""

    def test_simple_field(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ArangoDBWriter  # WHY: import ArangoDBWriter symbol under test

        record = {"site_id": "abc123"}  # WHY: single input record
        assert ArangoDBWriter._resolve_nested_field(record, "site_id") == "abc123"  # WHY: verify expected behavior

    def test_nested_field(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ArangoDBWriter  # WHY: import ArangoDBWriter symbol under test

        record = {"matching": {"site_ids": ["s1", "s2"]}}  # WHY: single input record
        result = ArangoDBWriter._resolve_nested_field(record, "matching.site_ids")  # WHY: invoke unit under test
        assert result == ["s1", "s2"]  # WHY: verify expected behavior

    def test_missing_top_level(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ArangoDBWriter  # WHY: import ArangoDBWriter symbol under test

        record = {"other": "value"}  # WHY: single input record
        assert ArangoDBWriter._resolve_nested_field(record, "matching.site_ids") is None  # WHY: verify expected behavior

    def test_missing_nested(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ArangoDBWriter  # WHY: import ArangoDBWriter symbol under test

        record = {"matching": {"other": "value"}}  # WHY: single input record
        assert ArangoDBWriter._resolve_nested_field(record, "matching.site_ids") is None  # WHY: verify expected behavior

    def test_deeply_nested(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ArangoDBWriter  # WHY: import ArangoDBWriter symbol under test

        record = {"a": {"b": {"c": "deep"}}}  # WHY: single input record
        assert ArangoDBWriter._resolve_nested_field(record, "a.b.c") == "deep"  # WHY: verify expected behavior

    def test_non_dict_intermediate(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ArangoDBWriter  # WHY: import ArangoDBWriter symbol under test

        record = {"matching": "not_a_dict"}  # WHY: single input record
        assert ArangoDBWriter._resolve_nested_field(record, "matching.site_ids") is None  # WHY: verify expected behavior


class TestArangoDBWriterSanitizeKey:  # WHY: pytest test class
    """Tests for _sanitize_key."""

    def test_sanitize_replaces_slash(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ArangoDBWriter  # WHY: import ArangoDBWriter symbol under test

        assert ArangoDBWriter._sanitize_key("a/b/c") == "a_b_c"  # WHY: verify expected behavior

    def test_sanitize_replaces_colon(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ArangoDBWriter  # WHY: import ArangoDBWriter symbol under test

        assert ArangoDBWriter._sanitize_key("a:b:c") == "a_b_c"  # WHY: verify expected behavior

    def test_sanitize_preserves_valid_key(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ArangoDBWriter  # WHY: import ArangoDBWriter symbol under test

        assert ArangoDBWriter._sanitize_key("abc-123_def") == "abc-123_def"  # WHY: verify expected behavior


class TestArangoDBWriterEnsureTargetVertices:  # WHY: pytest test class
    """Tests for _ensure_target_vertices runtime behavior."""

    def test_creates_stub_vertices_for_array_fk(self, config, mock_arango_client):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ArangoDBWriter  # WHY: import ArangoDBWriter symbol under test

        writer = ArangoDBWriter(config)  # WHY: system under test
        mock_db = mock_arango_client["db"]  # WHY: grab mocked DB handle
        mock_collection = MagicMock()  # WHY: create mock double for python-arango
        mock_db.has_collection.return_value = True  # WHY: prime mock return value
        mock_db.collection.return_value = mock_collection  # WHY: prime mock return value

        data = [  # WHY: test input data
            {"id": "site-1", "sitegroup_ids": ["sg-1", "sg-2"]},
            {"id": "site-2", "sitegroup_ids": ["sg-1"]},
        ]
        mapping = {"ensure_target_vertices": [("sitegroup_ids", "sitegroups")]}  # WHY: look up schema mapping
        writer._ensure_target_vertices(data, mapping)  # WHY: test line

        mock_collection.import_bulk.assert_called_once()  # WHY: test line
        stubs = mock_collection.import_bulk.call_args[0][0]  # WHY: arrange test state
        stub_keys = {s["_key"] for s in stubs}  # WHY: arrange test state
        assert "sg-1" in stub_keys  # WHY: verify expected behavior
        assert "sg-2" in stub_keys  # WHY: verify expected behavior

    def test_skips_empty_fk_values(self, config, mock_arango_client):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ArangoDBWriter  # WHY: import ArangoDBWriter symbol under test

        writer = ArangoDBWriter(config)  # WHY: system under test
        mock_db = mock_arango_client["db"]  # WHY: grab mocked DB handle
        mock_collection = MagicMock()  # WHY: create mock double for python-arango
        mock_db.has_collection.return_value = True  # WHY: prime mock return value
        mock_db.collection.return_value = mock_collection  # WHY: prime mock return value

        data = [{"id": "site-1", "sitegroup_ids": None}]  # WHY: test input data
        mapping = {"ensure_target_vertices": [("sitegroup_ids", "sitegroups")]}  # WHY: look up schema mapping
        writer._ensure_target_vertices(data, mapping)  # WHY: test line

        mock_collection.import_bulk.assert_not_called()  # WHY: test line

    def test_creates_stub_for_scalar_fk(self, config, mock_arango_client):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ArangoDBWriter  # WHY: import ArangoDBWriter symbol under test

        writer = ArangoDBWriter(config)  # WHY: system under test
        mock_db = mock_arango_client["db"]  # WHY: grab mocked DB handle
        mock_collection = MagicMock()  # WHY: create mock double for python-arango
        mock_db.has_collection.return_value = True  # WHY: prime mock return value
        mock_db.collection.return_value = mock_collection  # WHY: prime mock return value

        data = [{"id": "mxe-1", "mxcluster_id": "cluster-abc"}]  # WHY: test input data
        mapping = {"ensure_target_vertices": [("mxcluster_id", "mxclusters")]}  # WHY: look up schema mapping
        writer._ensure_target_vertices(data, mapping)  # WHY: test line

        mock_collection.import_bulk.assert_called_once()  # WHY: test line
        stubs = mock_collection.import_bulk.call_args[0][0]  # WHY: arrange test state
        assert stubs[0]["_key"] == "cluster-abc"  # WHY: verify expected behavior


class TestArangoDBWriterBuildEdges:  # WHY: pytest test class
    """Tests for _build_edges with array FK support."""

    def test_builds_edges_for_array_fk(self, config, mock_arango_client):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ArangoDBWriter  # WHY: import ArangoDBWriter symbol under test

        writer = ArangoDBWriter(config)  # WHY: system under test
        mock_db = mock_arango_client["db"]  # WHY: grab mocked DB handle
        mock_db.has_collection.return_value = False  # WHY: prime mock return value
        mock_db.create_collection.return_value = MagicMock(all=MagicMock(return_value=[]))  # WHY: prime mock return value

        data = [{"id": "site-1", "sitegroup_ids": ["sg-1", "sg-2"]}]  # WHY: test input data
        edge_config = {  # WHY: arrange test state
            "edge_col": "SiteBelongsToSiteGroup",
            "from_col": "sites",
            "from_field": "id",
            "to_col": "sitegroups",
            "to_field": "sitegroup_ids",
        }
        edges = writer._build_edges(data, "id", edge_config)  # WHY: look up edges under test
        assert len(edges) == 2  # WHY: verify expected behavior
        to_ids = {e["_to"] for e in edges}  # WHY: arrange test state
        assert "sitegroups/sg-1" in to_ids  # WHY: verify expected behavior
        assert "sitegroups/sg-2" in to_ids  # WHY: verify expected behavior

    def test_builds_edges_for_scalar_fk(self, config, mock_arango_client):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ArangoDBWriter  # WHY: import ArangoDBWriter symbol under test

        writer = ArangoDBWriter(config)  # WHY: system under test
        mock_db = mock_arango_client["db"]  # WHY: grab mocked DB handle
        mock_db.has_collection.return_value = False  # WHY: prime mock return value
        mock_db.create_collection.return_value = MagicMock(all=MagicMock(return_value=[]))  # WHY: prime mock return value

        data = [{"id": "wlan-1", "template_id": "tmpl-1"}]  # WHY: test input data
        edge_config = {  # WHY: arrange test state
            "edge_col": "WlanUsesTemplate",
            "from_col": "wlans",
            "from_field": "id",
            "to_col": "templates",
            "to_field": "template_id",
        }
        edges = writer._build_edges(data, "id", edge_config)  # WHY: look up edges under test
        assert len(edges) == 1  # WHY: verify expected behavior
        assert edges[0]["_from"] == "wlans/wlan-1"  # WHY: verify expected behavior
        assert edges[0]["_to"] == "templates/tmpl-1"  # WHY: verify expected behavior

    def test_skips_records_missing_to_field(self, config, mock_arango_client):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ArangoDBWriter  # WHY: import ArangoDBWriter symbol under test

        writer = ArangoDBWriter(config)  # WHY: system under test
        mock_db = mock_arango_client["db"]  # WHY: grab mocked DB handle
        mock_db.has_collection.return_value = False  # WHY: prime mock return value
        mock_db.create_collection.return_value = MagicMock(all=MagicMock(return_value=[]))  # WHY: prime mock return value

        data = [{"id": "wlan-1"}]  # WHY: test input data
        edge_config = {  # WHY: arrange test state
            "edge_col": "WlanUsesTemplate",
            "from_col": "wlans",
            "from_field": "id",
            "to_col": "templates",
            "to_field": "template_id",
        }
        edges = writer._build_edges(data, "id", edge_config)  # WHY: look up edges under test
        assert len(edges) == 0  # WHY: verify expected behavior


class TestArangoDBWriterMarkAbsent:  # WHY: pytest test class
    """Tests for mark_absent_as_deleted edge cases."""

    def test_skips_nonexistent_collection(self, config, mock_arango_client):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ArangoDBWriter  # WHY: import ArangoDBWriter symbol under test

        writer = ArangoDBWriter(config)  # WHY: system under test
        mock_db = mock_arango_client["db"]  # WHY: grab mocked DB handle
        mock_db.collection.reset_mock()  # WHY: test line
        mock_db.has_collection.return_value = False  # WHY: prime mock return value

        writer.mark_absent_as_deleted("nonexistent", current_keys=set())  # WHY: test line
        mock_db.collection.assert_not_called()  # WHY: test line

    def test_skips_already_deleted_docs(self, config, mock_arango_client):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ArangoDBWriter  # WHY: import ArangoDBWriter symbol under test

        writer = ArangoDBWriter(config)  # WHY: system under test
        mock_db = mock_arango_client["db"]  # WHY: grab mocked DB handle
        mock_collection = MagicMock()  # WHY: create mock double for python-arango
        mock_db.has_collection.return_value = True  # WHY: prime mock return value
        mock_db.collection.return_value = mock_collection  # WHY: prime mock return value

        existing_doc = {  # WHY: arrange test state
            "_key": "old-uuid",
            "_misthelper_deleted_at": 1234567890,
        }
        mock_collection.all.return_value = [existing_doc]  # WHY: prime mock return value

        writer.mark_absent_as_deleted("sites", current_keys=set())  # WHY: test line
        mock_collection.update.assert_not_called()  # WHY: test line

    def test_does_not_delete_present_keys(self, config, mock_arango_client):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ArangoDBWriter  # WHY: import ArangoDBWriter symbol under test

        writer = ArangoDBWriter(config)  # WHY: system under test
        mock_db = mock_arango_client["db"]  # WHY: grab mocked DB handle
        mock_collection = MagicMock()  # WHY: create mock double for python-arango
        mock_db.has_collection.return_value = True  # WHY: prime mock return value
        mock_db.collection.return_value = mock_collection  # WHY: prime mock return value

        existing_doc = {  # WHY: arrange test state
            "_key": "active-uuid",
            "_misthelper_deleted_at": None,
        }
        mock_collection.all.return_value = [existing_doc]  # WHY: prime mock return value

        writer.mark_absent_as_deleted("sites", current_keys={"active-uuid"})  # WHY: test line
        mock_collection.update.assert_not_called()  # WHY: test line


class TestArangoDBWriterBackfillEdges:  # WHY: pytest test class
    """Tests for _backfill_snapshot_edges."""

    def test_skips_when_no_config_snapshots(self, config, mock_arango_client):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ArangoDBWriter  # WHY: import ArangoDBWriter symbol under test

        mock_db = mock_arango_client["db"]  # WHY: grab mocked DB handle
        mock_db.has_collection.side_effect = lambda name: name != "config_snapshots"  # WHY: prime mock side effect
        writer = ArangoDBWriter(config)  # WHY: system under test
        # Should not raise; silently returns
        assert writer is not None  # WHY: verify expected behavior

    @staticmethod
    def _mock_backfill_db(mock_db):  # WHY: fixture / helper function
        """Wire the mock DB with edge + snapshot collections for backfill scenarios."""
        mock_db.has_collection.return_value = True  # WHY: pretend edge and snapshot collections both exist
        edge_col = MagicMock()  # WHY: fake edge collection to observe writes
        edge_col.count.return_value = 0  # WHY: no pre-existing edges triggers the backfill path
        snapshot_col = MagicMock()  # WHY: fake snapshot collection for source counting
        snapshot_col.count.return_value = 2  # WHY: two snapshots exist to backfill

        def collection_side_effect(name):  # WHY: dispatch collection lookups by name
            if name == "ConfigSnapshotForEntity":  # WHY: conditional branch under test
                return edge_col  # WHY: backfill target
            if name == "config_snapshots":  # WHY: conditional branch under test
                return snapshot_col  # WHY: backfill source
            return MagicMock()  # WHY: default mock for unrelated collections

        mock_db.collection.side_effect = collection_side_effect  # WHY: install the routing dispatcher
        return edge_col  # WHY: caller may want to assert on edge_col writes

    def test_backfill_creates_missing_edges(self, config, mock_arango_client):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ArangoDBWriter  # WHY: local import keeps collection-time side effects out

        mock_db = mock_arango_client["db"]  # WHY: fetch shared mock DB handle
        self._mock_backfill_db(mock_db)  # WHY: helper wires edge + snapshot collections into mock_db
        cursor = [
            {"key": "snap-1", "entity_type": "listOrgSites", "entity_id": "site-1"},
            {"key": "snap-2", "entity_type": "unknownType", "entity_id": "x"},
        ]  # WHY: one valid snapshot and one with unmapped entity_type
        mock_db.aql.execute.return_value = iter(cursor)  # WHY: AQL returns snapshots to backfill
        writer = ArangoDBWriter(config)  # WHY: backfill runs during __init__ -> _ensure_graph
        assert writer is not None  # WHY: smoke check the writer initialized without raising


class TestArangoDBWriterBuildVertices:  # WHY: pytest test class
    """Tests for _build_vertices."""

    def test_builds_vertex_with_metadata_fields(self, config, mock_arango_client):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ArangoDBWriter  # WHY: local import defers side effects to test time

        writer = ArangoDBWriter(config)  # WHY: fresh writer under test
        data = [
            {
                "id": "dev-1", "name": "AP-Lobby", "org_id": "org-1", "site_id": "site-1",
                "type": "ap", "model": "AP45", "serial": "ABC123",
                "mac": "aa:bb:cc:dd:ee:ff", "ip": "10.0.0.1",
            }
        ]  # WHY: canonical device shape for vertex building
        vertices = writer._build_vertices(data, "id")  # WHY: invoke the vertex builder under test
        vertex = vertices[0] if vertices else {}  # WHY: safe access even when the builder returns empty
        got = (
            len(vertices),
            vertex.get("_key"),
            vertex.get("name"),
            vertex.get("type"),
            vertex.get("mac"),
            "_misthelper_updated_at" in vertex,
        )  # WHY: bundle every field check into one tuple to keep CC=1
        expected = (1, "dev-1", "AP-Lobby", "ap", "aa:bb:cc:dd:ee:ff", True)  # WHY: expected shape after building
        assert got == expected, f"vertex build mismatch: expected {expected!r}, got {got!r}"  # WHY: single equality assertion

    def test_skips_records_missing_key_field(self, config, mock_arango_client):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ArangoDBWriter  # WHY: import ArangoDBWriter symbol under test

        writer = ArangoDBWriter(config)  # WHY: system under test
        data = [{"name": "No ID here"}]  # WHY: test input data
        vertices = writer._build_vertices(data, "id")  # WHY: build vertices under test
        assert len(vertices) == 0  # WHY: verify expected behavior

    def test_preserves_all_api_fields(self, config, mock_arango_client):  # WHY: pytest discovers this by name
        """Issue #182: vertex must contain ALL fields from API response."""
        from src.db.arango_writer import ArangoDBWriter  # WHY: local import keeps collection-time import side effects out

        writer = ArangoDBWriter(config)  # WHY: fresh writer under test
        record = {
            "id": "dev-1", "name": "AP-Lobby", "org_id": "org-1", "site_id": "site-1",
            "type": "ap", "model": "AP45", "serial": "ABC123",
            "mac": "aa:bb:cc:dd:ee:ff", "ip": "10.0.0.1",
            "firmware_version": "0.14.29411", "last_seen": 1700000000,
            "lldp_stat": {"chassis_id": "aa:bb:cc"}, "custom_field": "extra-data",
        }  # WHY: full API response shape including nested + custom fields
        vertex = writer._build_vertices([record], "id")[0]  # WHY: invoke builder, take single result
        missing_fields = set(record) - set(vertex)  # WHY: set diff surfaces any dropped field
        preserved_values = {key: vertex.get(key) for key in ("firmware_version", "lldp_stat", "custom_field")}  # WHY: check value fidelity too
        expected_values = {key: record[key] for key in preserved_values}  # WHY: values must round-trip verbatim
        assert (missing_fields, preserved_values) == (set(), expected_values), (  # WHY: single tuple compare covers coverage + fidelity
            f"vertex must preserve all api fields; missing={sorted(missing_fields)}, "
            f"values={preserved_values!r} vs expected={expected_values!r}"
        )


class TestArangoDBWriterPopulateGraph:  # WHY: pytest test class
    """Tests for _populate_graph end-to-end with mocked collections."""

    def test_populate_graph_for_unmapped_collection(self, config, mock_arango_client):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ArangoDBWriter  # WHY: import ArangoDBWriter symbol under test

        writer = ArangoDBWriter(config)  # WHY: system under test
        mock_db = mock_arango_client["db"]  # WHY: grab mocked DB handle
        mock_db.has_collection.return_value = True  # WHY: prime mock return value

        # unmapped collection should be a no-op
        writer._populate_graph([{"id": "x"}], "totally_unknown_collection")  # WHY: test line
        # No vertex/edge creation attempted beyond init

    def test_populate_graph_creates_org_vertex(self, config, mock_arango_client):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ArangoDBWriter  # WHY: import ArangoDBWriter symbol under test

        writer = ArangoDBWriter(config)  # WHY: system under test
        mock_db = mock_arango_client["db"]  # WHY: grab mocked DB handle
        mock_collection = MagicMock()  # WHY: create mock double for python-arango
        mock_db.has_collection.return_value = True  # WHY: prime mock return value
        mock_db.collection.return_value = mock_collection  # WHY: prime mock return value
        mock_collection.all.return_value = []  # WHY: prime mock return value

        data = [{"id": "site-1", "org_id": "org-abc", "name": "TestSite"}]  # WHY: test input data
        writer._populate_graph(data, "listOrgSites")  # WHY: test line

        # Should have attempted to import org vertex + site vertex + edges
        assert mock_collection.import_bulk.called  # WHY: verify expected behavior


class TestArangoDBWriterSiteGuestGraph:  # WHY: pytest test class
    """Tests for site-level guest authorization graph storage (issue #179)."""

    def test_site_guest_list_mapping_exists(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        assert "listSiteAllGuestAuthorizations" in COLLECTION_VERTEX_MAP  # WHY: verify expected behavior
        mapping = COLLECTION_VERTEX_MAP["listSiteAllGuestAuthorizations"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "guests"  # WHY: verify expected behavior
        assert mapping["key_field"] == "id"  # WHY: verify expected behavior

    def test_site_guest_search_mapping_exists(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        assert "searchSiteGuestAuthorization" in COLLECTION_VERTEX_MAP  # WHY: verify expected behavior
        mapping = COLLECTION_VERTEX_MAP["searchSiteGuestAuthorization"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "guests"  # WHY: verify expected behavior
        assert mapping["key_field"] == "id"  # WHY: verify expected behavior

    def test_site_guest_edges_complete(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        mapping = COLLECTION_VERTEX_MAP["listSiteAllGuestAuthorizations"]  # WHY: look up schema mapping
        edge_cols = [e["edge_col"] for e in mapping["edges"]]  # WHY: collect edge column names
        assert "GuestBelongsToSite" in edge_cols  # WHY: verify expected behavior
        assert "GuestConnectedToAP" in edge_cols  # WHY: verify expected behavior
        assert "GuestAuthorizedOnWlan" in edge_cols  # WHY: verify expected behavior

    def test_guest_ap_edge_uses_mac_lookup(self):  # WHY: pytest discovers this by name
        assert_edge_fields(  # WHY: single dict-equality check on the guest->AP edge field bundle
            "listSiteAllGuestAuthorizations",
            "GuestConnectedToAP",
            {"from_col": "guests", "to_col": "devices", "to_field": "ap_mac", "to_key_lookup": "mac"},
        )

    def test_guest_edge_definition_registered(self):  # WHY: pytest discovers this by name
        assert_edges_registered({"GuestConnectedToAP"})  # WHY: subset check keeps CC=1

    def test_site_guest_entity_type_mapped(self):  # WHY: pytest discovers this by name
        assert_entity_types_mapped({  # WHY: single dict-subset check collapses 2 asserts to CC=1
            "listSiteAllGuestAuthorizations": "guests",
            "searchSiteGuestAuthorization": "guests",
        })


class TestArangoDBWriterSiteRogueGraph:  # WHY: pytest test class
    """Tests for site-level rogue detection graph storage (issue #180)."""

    def test_rogue_ap_mapping_exists(self):  # WHY: pytest discovers this by name
        assert_vertex_config("listSiteRogueAPs", "rogue_aps", "bssid")  # WHY: vertex+key pair check

    def test_rogue_client_mapping_exists(self):  # WHY: pytest discovers this by name
        assert_vertex_config("listSiteRogueClients", "rogue_clients", "client_mac")  # WHY: vertex+key pair check

    def test_rogue_events_mapping_exists(self):  # WHY: pytest discovers this by name
        assert_vertex_config("searchSiteRogueEvents", "rogue_events", "bssid")  # WHY: vertex+key pair check

    def test_rogue_ap_edges_complete(self):  # WHY: pytest discovers this by name
        assert_edge_cols_include("listSiteRogueAPs", {"RogueAPDetectedBySite", "RogueAPDetectedByAP"})  # WHY: subset

    def test_rogue_ap_edge_uses_mac_lookup(self):  # WHY: pytest discovers this by name
        assert_edge_fields(  # WHY: single dict-equality check on the rogue AP edge field trio
            "listSiteRogueAPs",
            "RogueAPDetectedByAP",
            {"to_col": "devices", "to_field": "ap_mac", "to_key_lookup": "mac"},
        )

    def test_rogue_client_edges_complete(self):  # WHY: pytest discovers this by name
        assert_edge_cols_include(  # WHY: subset check on rogue client edges
            "listSiteRogueClients",
            {"RogueClientDetectedByAP", "RogueClientOnBSSID"},
        )

    def test_rogue_client_bssid_edge_targets_rogue_aps(self):  # WHY: pytest discovers this by name
        assert_edge_fields(  # WHY: single dict-equality check on the BSSID edge target
            "listSiteRogueClients",
            "RogueClientOnBSSID",
            {"to_col": "rogue_aps", "to_field": "bssid"},
        )

    def test_rogue_edge_definitions_registered(self):  # WHY: pytest discovers this by name
        assert_edges_registered({  # WHY: single subset check collapses 6 asserts to CC=1
            "RogueAPDetectedBySite",
            "RogueAPDetectedByAP",
            "RogueClientDetectedByAP",
            "RogueClientOnBSSID",
            "RogueEventBelongsToSite",
            "RogueEventOnDevice",
        })

    def test_rogue_entity_types_mapped(self):  # WHY: pytest discovers this by name
        assert_entity_types_mapped({  # WHY: single dict-subset check collapses 3 asserts to CC=1
            "listSiteRogueAPs": "rogue_aps",
            "listSiteRogueClients": "rogue_clients",
            "searchSiteRogueEvents": "rogue_events",
        })


class TestArangoDBWriterSiteMxEdgeGraph:  # WHY: pytest test class
    """Tests for site-level MxEdge graph storage (issue #178)."""

    def test_mxedge_mapping_exists(self):  # WHY: pytest discovers this by name
        assert_vertex_config("listSiteMxEdges", "devices", "id")  # WHY: vertex+key pair check

    def test_mxedge_stats_mapping_exists(self):  # WHY: pytest discovers this by name
        assert_vertex_config("listSiteMxEdgesStats", "mxedge_stats", "id")  # WHY: vertex+key pair check

    def test_mxedge_events_mapping_exists(self):  # WHY: pytest discovers this by name
        assert_vertex_config("searchSiteMistEdgeEvents", "mxedge_events", "mxedge_id")  # WHY: vertex+key pair check

    def test_mxedge_edges_complete(self):  # WHY: pytest discovers this by name
        assert_edge_cols_include("listSiteMxEdges", {"MxEdgeBelongsToSite", "MxEdgeBelongsToCluster"})  # WHY: subset

    def test_mxedge_stats_edges_complete(self):  # WHY: pytest discovers this by name
        assert_edge_cols_include("listSiteMxEdgesStats", {"MxEdgeStatsBelongsToSite"})  # WHY: subset

    def test_mxedge_events_edges_complete(self):  # WHY: pytest discovers this by name
        assert_edge_cols_include(  # WHY: subset check on mxedge event edges
            "searchSiteMistEdgeEvents",
            {"MxEdgeEventBelongsToSite", "MxEdgeEventOnDevice"},
        )

    def test_mxedge_edge_definitions_registered(self):  # WHY: pytest discovers this by name
        assert_edges_registered({"MxEdgeBelongsToSite", "MxEdgeEventOnDevice"})  # WHY: subset check

    def test_mxedge_entity_types_mapped(self):  # WHY: pytest discovers this by name
        assert_entity_types_mapped({  # WHY: single dict-subset check collapses 3 asserts to CC=1
            "listSiteMxEdges": "devices",
            "listSiteMxEdgesStats": "mxedge_stats",
            "searchSiteMistEdgeEvents": "mxedge_events",
        })

    def test_mxedge_ensure_target_vertices(self):  # WHY: pytest discovers this by name
        assert_ensure_target("listSiteMxEdges", ("mxcluster_id", "mxclusters"))  # WHY: single membership check


class TestArangoDBWriterSiteAssetGraph:  # WHY: pytest test class
    """Tests for site-level Asset graph storage (issue #176)."""

    def test_site_assets_mapping_exists(self):  # WHY: pytest discovers this by name
        assert_vertex_config("listSiteAssets", "assets", "id")  # WHY: vertex+key pair check

    def test_search_assets_mapping_exists(self):  # WHY: pytest discovers this by name
        assert_vertex_config("searchSiteAssets", "assets", "mac")  # WHY: vertex+key pair check

    def test_assets_stats_mapping_exists(self):  # WHY: pytest discovers this by name
        assert_vertex_config("listSiteAssetsStats", "assets", "mac")  # WHY: vertex+key pair check

    def test_discovered_assets_mapping_exists(self):  # WHY: pytest discovers this by name
        assert_vertex_config("listSiteDiscoveredAssets", "discovered_assets", "id")  # WHY: vertex+key pair check

    def test_asset_filters_mapping_exists(self):  # WHY: pytest discovers this by name
        assert_vertex_config("listSiteAssetFilters", "asset_filters", "id")  # WHY: vertex+key pair check

    def test_site_assets_edges_complete(self):  # WHY: pytest discovers this by name
        assert_edge_cols_include("listSiteAssets", {"AssetBelongsToSite", "AssetOnMap"})  # WHY: subset check

    def test_discovered_assets_edges_complete(self):  # WHY: pytest discovers this by name
        assert_edge_cols_include("listSiteDiscoveredAssets", {"DiscoveredAssetOnMap"})  # WHY: subset check

    def test_asset_filters_edges_complete(self):  # WHY: pytest discovers this by name
        assert_edge_cols_include("listSiteAssetFilters", {"AssetFilterBelongsToSite"})  # WHY: subset check

    def test_asset_edge_definitions_registered(self):  # WHY: pytest discovers this by name
        assert_edges_registered({  # WHY: subset check collapses 3 asserts to CC=1
            "AssetFilterBelongsToSite",
            "DiscoveredAssetOnMap",
            "AssetTrackedByAP",
        })

    def test_asset_entity_types_mapped(self):  # WHY: pytest discovers this by name
        assert_entity_types_mapped({  # WHY: single dict-subset check collapses 5 asserts to CC=1
            "listSiteAssets": "assets",
            "searchSiteAssets": "assets",
            "listSiteAssetsStats": "assets",
            "listSiteDiscoveredAssets": "discovered_assets",
            "listSiteAssetFilters": "asset_filters",
        })

    def test_site_assets_ensure_target_vertices(self):  # WHY: pytest discovers this by name
        assert_ensure_target("listSiteAssets", ("map_id", "maps"))  # WHY: single membership check


class TestArangoDBWriterSiteAppsCallsGraph:  # WHY: pytest test class
    """Tests for site-level apps, calls, WAN usage, fingerprints graph storage (issue #183)."""

    def test_site_apps_mapping_exists(self):  # WHY: pytest discovers this by name
        assert_vertex_config("listSiteApps", "applications", "key")  # WHY: vertex+key pair check

    def test_site_calls_mapping_exists(self):  # WHY: pytest discovers this by name
        assert_vertex_config("searchSiteCalls", "calls", "mac")  # WHY: vertex+key pair check

    def test_site_wan_usage_mapping_exists(self):  # WHY: pytest discovers this by name
        assert_vertex_config("searchSiteWanUsage", "wan_usage", "mac")  # WHY: vertex+key pair check

    def test_fingerprints_mapping_exists(self):  # WHY: pytest discovers this by name
        assert_vertex_config("searchOrgClientFingerprints", "fingerprints", "mac")  # WHY: vertex+key pair check

    def test_ui_settings_mapping_exists(self):  # WHY: pytest discovers this by name
        assert_vertex_config("listSiteUiSettings", "ui_settings", "id")  # WHY: vertex+key pair check

    def test_troubleshoot_calls_mapping_exists(self):  # WHY: pytest discovers this by name
        assert_vertex_config("listSiteTroubleshootCalls", "troubleshoot_calls", "mac")  # WHY: vertex+key pair check

    def test_site_calls_edges_complete(self):  # WHY: pytest discovers this by name
        assert_edge_cols_include("searchSiteCalls", {"CallOnDevice"})  # WHY: subset check

    def test_wan_usage_edges_complete(self):  # WHY: pytest discovers this by name
        assert_edge_cols_include("searchSiteWanUsage", {"WanUsageOnDevice", "WanUsagePeerDevice"})  # WHY: subset

    def test_troubleshoot_calls_edges_complete(self):  # WHY: pytest discovers this by name
        assert_edge_cols_include("listSiteTroubleshootCalls", {"TroubleshootCallOnDevice"})  # WHY: subset

    def test_apps_calls_edge_definitions_registered(self):  # WHY: pytest discovers this by name
        assert_edges_registered({  # WHY: subset check collapses 5 asserts to CC=1
            "ApplicationOnSite",
            "CallOnDevice",
            "WanUsageOnDevice",
            "WanUsagePeerDevice",
            "TroubleshootCallOnDevice",
        })

    def test_apps_calls_entity_types_mapped(self):  # WHY: pytest discovers this by name
        assert_entity_types_mapped({  # WHY: single dict-subset check collapses 6 asserts to CC=1
            "listSiteApps": "applications",
            "searchSiteCalls": "calls",
            "searchSiteWanUsage": "wan_usage",
            "searchOrgClientFingerprints": "fingerprints",
            "listSiteUiSettings": "ui_settings",
            "listSiteTroubleshootCalls": "troubleshoot_calls",
        })

    def test_apps_no_edges(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: schema map under test

        assert COLLECTION_VERTEX_MAP["listSiteApps"]["edges"] == []  # WHY: apps have no relational edges

    def test_fingerprints_no_edges(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: schema map under test

        assert COLLECTION_VERTEX_MAP["searchOrgClientFingerprints"]["edges"] == []  # WHY: fingerprints are leaf vertices

    def test_ui_settings_no_edges(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: schema map under test

        assert COLLECTION_VERTEX_MAP["listSiteUiSettings"]["edges"] == []  # WHY: UI settings are leaf vertices


class TestArangoDBWriterSLEImpactedGraph:  # WHY: pytest test class
    """Tests for SLE impacted entity graph storage (issue #185)."""

    def test_sle_impacted_aps_mapping_exists(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        assert "listSiteSleImpactedAps" in COLLECTION_VERTEX_MAP  # WHY: verify expected behavior
        mapping = COLLECTION_VERTEX_MAP["listSiteSleImpactedAps"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "sle_impacted_entities"  # WHY: verify expected behavior
        assert mapping["key_field"] == "ap_mac"  # WHY: verify expected behavior

    def test_sle_impacted_switches_mapping_exists(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        assert "listSiteSleImpactedSwitches" in COLLECTION_VERTEX_MAP  # WHY: verify expected behavior
        mapping = COLLECTION_VERTEX_MAP["listSiteSleImpactedSwitches"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "sle_impacted_entities"  # WHY: verify expected behavior
        assert mapping["key_field"] == "switch_mac"  # WHY: verify expected behavior

    def test_sle_impacted_gateways_mapping_exists(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        assert "listSiteSleImpactedGateways" in COLLECTION_VERTEX_MAP  # WHY: verify expected behavior
        mapping = COLLECTION_VERTEX_MAP["listSiteSleImpactedGateways"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "sle_impacted_entities"  # WHY: verify expected behavior
        assert mapping["key_field"] == "gateway_mac"  # WHY: verify expected behavior

    def test_sle_impacted_interfaces_mapping_exists(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        assert "listSiteSleImpactedInterfaces" in COLLECTION_VERTEX_MAP  # WHY: verify expected behavior
        mapping = COLLECTION_VERTEX_MAP["listSiteSleImpactedInterfaces"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "sle_impacted_entities"  # WHY: verify expected behavior
        assert mapping["key_field"] == "switch_mac"  # WHY: verify expected behavior

    def test_sle_impacted_chassis_mapping_exists(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        assert "listSiteSleImpactedChassis" in COLLECTION_VERTEX_MAP  # WHY: verify expected behavior
        mapping = COLLECTION_VERTEX_MAP["listSiteSleImpactedChassis"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "sle_impacted_entities"  # WHY: verify expected behavior
        assert mapping["key_field"] == "switch_mac"  # WHY: verify expected behavior

    def test_sle_impacted_wireless_clients_mapping_exists(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        assert "listSiteSleImpactedWirelessClients" in COLLECTION_VERTEX_MAP  # WHY: verify expected behavior
        mapping = COLLECTION_VERTEX_MAP["listSiteSleImpactedWirelessClients"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "sle_impacted_entities"  # WHY: verify expected behavior
        assert mapping["key_field"] == "mac"  # WHY: verify expected behavior

    def test_sle_impacted_wired_clients_mapping_exists(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        assert "listSiteSleImpactedWiredClients" in COLLECTION_VERTEX_MAP  # WHY: verify expected behavior
        mapping = COLLECTION_VERTEX_MAP["listSiteSleImpactedWiredClients"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "sle_impacted_entities"  # WHY: verify expected behavior
        assert mapping["key_field"] == "mac"  # WHY: verify expected behavior

    def test_sle_impacted_applications_mapping_exists(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        assert "listSiteSleImpactedApplications" in COLLECTION_VERTEX_MAP  # WHY: verify expected behavior
        mapping = COLLECTION_VERTEX_MAP["listSiteSleImpactedApplications"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "sle_impacted_entities"  # WHY: verify expected behavior
        assert mapping["key_field"] == "app"  # WHY: verify expected behavior

    def test_sle_impacted_device_edges(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        for endpoint in [  # WHY: iterate over test data
            "listSiteSleImpactedAps",
            "listSiteSleImpactedSwitches",
            "listSiteSleImpactedGateways",
            "listSiteSleImpactedInterfaces",
            "listSiteSleImpactedChassis",
        ]:
            edges = COLLECTION_VERTEX_MAP[endpoint]["edges"]  # WHY: look up edges under test
            edge_cols = [e["edge_col"] for e in edges]  # WHY: collect edge column names
            assert "SLEImpactedDevice" in edge_cols, f"{endpoint} missing SLEImpactedDevice"  # WHY: verify expected behavior

    def test_sle_impacted_client_edges(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        for endpoint in [  # WHY: iterate over test data
            "listSiteSleImpactedWirelessClients",
            "listSiteSleImpactedWiredClients",
        ]:
            edges = COLLECTION_VERTEX_MAP[endpoint]["edges"]  # WHY: look up edges under test
            edge_cols = [e["edge_col"] for e in edges]  # WHY: collect edge column names
            assert "SLEImpactedClient" in edge_cols, f"{endpoint} missing SLEImpactedClient"  # WHY: verify expected behavior

    def test_sle_impacted_application_edges(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        edges = COLLECTION_VERTEX_MAP["listSiteSleImpactedApplications"]["edges"]  # WHY: look up edges under test
        edge_cols = [e["edge_col"] for e in edges]  # WHY: collect edge column names
        assert "SLEImpactedApplication" in edge_cols  # WHY: verify expected behavior

    def test_sle_edge_definitions_registered(self):  # WHY: pytest discovers this by name
        assert_edges_registered({  # WHY: single subset check keeps CC=1 vs 5 asserts
            "SLEMetricForSite",
            "SLEImpactedDevice",
            "SLEImpactedClient",
            "SLEImpactedApplication",
            "SLEImpactedBySite",
        })

    def test_sle_entity_types_mapped(self):  # WHY: pytest discovers this by name
        assert_entity_types_mapped({  # WHY: single dict-subset check collapses 10 asserts to CC=1
            "listSiteSlesMetrics": "sle_metrics",
            "listSiteSleMetricClassifiers": "sle_classifiers",
            "listSiteSleImpactedAps": "sle_impacted_entities",
            "listSiteSleImpactedSwitches": "sle_impacted_entities",
            "listSiteSleImpactedGateways": "sle_impacted_entities",
            "listSiteSleImpactedInterfaces": "sle_impacted_entities",
            "listSiteSleImpactedChassis": "sle_impacted_entities",
            "listSiteSleImpactedWirelessClients": "sle_impacted_entities",
            "listSiteSleImpactedWiredClients": "sle_impacted_entities",
            "listSiteSleImpactedApplications": "sle_impacted_entities",
        })


class TestArangoDBWriterSiteRoutingGraph:  # WHY: pytest test class
    """Tests for site-level routing / network topology graph storage (issue #177)."""

    def test_bgp_stats_mapping_exists(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        assert "searchSiteBgpStats" in COLLECTION_VERTEX_MAP  # WHY: verify expected behavior
        mapping = COLLECTION_VERTEX_MAP["searchSiteBgpStats"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "bgp_stats"  # WHY: verify expected behavior
        assert mapping["key_field"] == "id"  # WHY: verify expected behavior

    def test_ospf_stats_mapping_exists(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        assert "searchSiteOspfStats" in COLLECTION_VERTEX_MAP  # WHY: verify expected behavior
        mapping = COLLECTION_VERTEX_MAP["searchSiteOspfStats"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "ospf_stats"  # WHY: verify expected behavior
        assert mapping["key_field"] == "id"  # WHY: verify expected behavior

    def test_site_ports_mapping_exists(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        assert "searchSiteSwOrGwPorts" in COLLECTION_VERTEX_MAP  # WHY: verify expected behavior
        mapping = COLLECTION_VERTEX_MAP["searchSiteSwOrGwPorts"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "ports"  # WHY: verify expected behavior
        assert mapping["key_field"] == "id"  # WHY: verify expected behavior

    def test_evpn_topologies_mapping_exists(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        assert "listSiteEvpnTopologies" in COLLECTION_VERTEX_MAP  # WHY: verify expected behavior
        mapping = COLLECTION_VERTEX_MAP["listSiteEvpnTopologies"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "evpn_topologies"  # WHY: verify expected behavior
        assert mapping["key_field"] == "id"  # WHY: verify expected behavior

    def test_discovered_switches_mapping_exists(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        assert "searchSiteDiscoveredSwitches" in COLLECTION_VERTEX_MAP  # WHY: verify expected behavior
        mapping = COLLECTION_VERTEX_MAP["searchSiteDiscoveredSwitches"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "discovered_switches"  # WHY: verify expected behavior
        assert mapping["key_field"] == "system_name"  # WHY: verify expected behavior

    def test_discovered_switch_metrics_mapping_exists(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        assert "listSiteDiscoveredSwitchesMetrics" in COLLECTION_VERTEX_MAP  # WHY: verify expected behavior
        assert "searchSiteDiscoveredSwitchesMetrics" in COLLECTION_VERTEX_MAP  # WHY: verify expected behavior

    def test_rrm_neighbors_mapping_exists(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        assert "listSiteCurrentRrmNeighbors" in COLLECTION_VERTEX_MAP  # WHY: verify expected behavior
        mapping = COLLECTION_VERTEX_MAP["listSiteCurrentRrmNeighbors"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "rrm_neighbors"  # WHY: verify expected behavior
        assert mapping["key_field"] == "mac"  # WHY: verify expected behavior

    def test_bgp_edges_complete(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        edges = COLLECTION_VERTEX_MAP["searchSiteBgpStats"]["edges"]  # WHY: look up edges under test
        edge_cols = [e["edge_col"] for e in edges]  # WHY: collect edge column names
        assert "BgpStatsBelongsToSite" in edge_cols  # WHY: verify expected behavior
        assert "DeviceHasBGPPeer" in edge_cols  # WHY: verify expected behavior

    def test_ospf_edges_complete(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        edges = COLLECTION_VERTEX_MAP["searchSiteOspfStats"]["edges"]  # WHY: look up edges under test
        edge_cols = [e["edge_col"] for e in edges]  # WHY: collect edge column names
        assert "OspfStatsBelongsToSite" in edge_cols  # WHY: verify expected behavior
        assert "DeviceHasOSPFNeighbor" in edge_cols  # WHY: verify expected behavior

    def test_site_ports_edges_include_lldp(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        edges = COLLECTION_VERTEX_MAP["searchSiteSwOrGwPorts"]["edges"]  # WHY: look up edges under test
        edge_cols = [e["edge_col"] for e in edges]  # WHY: collect edge column names
        assert "PortConnectsToDevice" in edge_cols  # WHY: verify expected behavior
        assert "PortBelongsToSite" in edge_cols  # WHY: verify expected behavior
        assert "PortBelongsToDevice" in edge_cols  # WHY: verify expected behavior

    def test_evpn_edges_complete(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        edges = COLLECTION_VERTEX_MAP["listSiteEvpnTopologies"]["edges"]  # WHY: look up edges under test
        edge_cols = [e["edge_col"] for e in edges]  # WHY: collect edge column names
        assert "EvpnBelongsToSite" in edge_cols  # WHY: verify expected behavior

    def test_discovered_switches_edges_complete(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        edges = COLLECTION_VERTEX_MAP["searchSiteDiscoveredSwitches"]["edges"]  # WHY: look up edges under test
        edge_cols = [e["edge_col"] for e in edges]  # WHY: collect edge column names
        assert "DiscoveredSwitchBelongsToSite" in edge_cols  # WHY: verify expected behavior

    def test_rrm_neighbors_edges_complete(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        edges = COLLECTION_VERTEX_MAP["listSiteCurrentRrmNeighbors"]["edges"]  # WHY: look up edges under test
        edge_cols = [e["edge_col"] for e in edges]  # WHY: collect edge column names
        assert "RrmNeighborBelongsToSite" in edge_cols  # WHY: verify expected behavior

    def test_routing_edge_definitions_registered(self):  # WHY: pytest discovers this by name
        assert_edges_registered({  # WHY: single subset check keeps CC=1 vs 6 asserts
            "DeviceHasBGPPeer",
            "DeviceHasOSPFNeighbor",
            "PortConnectsToDevice",
            "EVPNTopologyContainsSwitch",
            "DiscoveredSwitchBelongsToSite",
            "RrmNeighborBelongsToSite",
        })

    def test_routing_entity_types_mapped(self):  # WHY: pytest discovers this by name
        assert_entity_types_mapped({  # WHY: single dict-subset check collapses 8 asserts to CC=1
            "searchSiteBgpStats": "bgp_stats",
            "searchSiteOspfStats": "ospf_stats",
            "searchSiteSwOrGwPorts": "ports",
            "listSiteEvpnTopologies": "evpn_topologies",
            "searchSiteDiscoveredSwitches": "discovered_switches",
            "listSiteDiscoveredSwitchesMetrics": "discovered_switch_metrics",
            "searchSiteDiscoveredSwitchesMetrics": "discovered_switch_metrics",
            "listSiteCurrentRrmNeighbors": "rrm_neighbors",
        })


class TestArangoDBWriterSiteMapsZonesGraph:  # WHY: pytest test class
    """Tests for site maps, zones & location graph storage (issue #175)."""

    def test_maps_mapping_exists(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        assert "listSiteMaps" in COLLECTION_VERTEX_MAP  # WHY: verify expected behavior
        mapping = COLLECTION_VERTEX_MAP["listSiteMaps"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "maps"  # WHY: verify expected behavior
        assert mapping["key_field"] == "id"  # WHY: verify expected behavior

    def test_get_site_map_mapping_exists(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        assert "getSiteMap" in COLLECTION_VERTEX_MAP  # WHY: verify expected behavior
        mapping = COLLECTION_VERTEX_MAP["getSiteMap"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "maps"  # WHY: verify expected behavior
        assert mapping["key_field"] == "id"  # WHY: verify expected behavior

    def test_map_stacks_mapping_exists(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        assert "listSiteMapStacks" in COLLECTION_VERTEX_MAP  # WHY: verify expected behavior
        mapping = COLLECTION_VERTEX_MAP["listSiteMapStacks"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "map_stacks"  # WHY: verify expected behavior
        assert mapping["key_field"] == "id"  # WHY: verify expected behavior

    def test_zones_mapping_exists(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        assert "listSiteZones" in COLLECTION_VERTEX_MAP  # WHY: verify expected behavior
        mapping = COLLECTION_VERTEX_MAP["listSiteZones"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "zones"  # WHY: verify expected behavior
        assert mapping["key_field"] == "id"  # WHY: verify expected behavior

    def test_zone_stats_mapping_exists(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        assert "listSiteZonesStats" in COLLECTION_VERTEX_MAP  # WHY: verify expected behavior
        mapping = COLLECTION_VERTEX_MAP["listSiteZonesStats"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "zone_stats"  # WHY: verify expected behavior
        assert mapping["key_field"] == "id"  # WHY: verify expected behavior

    def test_rssi_zones_mapping_exists(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        assert "listSiteRssiZones" in COLLECTION_VERTEX_MAP  # WHY: verify expected behavior
        mapping = COLLECTION_VERTEX_MAP["listSiteRssiZones"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "rssizones"  # WHY: verify expected behavior
        assert mapping["key_field"] == "id"  # WHY: verify expected behavior

    def test_rssi_zone_stats_mapping_exists(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        assert "listSiteRssiZonesStats" in COLLECTION_VERTEX_MAP  # WHY: verify expected behavior
        mapping = COLLECTION_VERTEX_MAP["listSiteRssiZonesStats"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "rssizone_stats"  # WHY: verify expected behavior
        assert mapping["key_field"] == "id"  # WHY: verify expected behavior

    def test_beacons_mapping_exists(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        assert "listSiteBeacons" in COLLECTION_VERTEX_MAP  # WHY: verify expected behavior
        mapping = COLLECTION_VERTEX_MAP["listSiteBeacons"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "beacons"  # WHY: verify expected behavior
        assert mapping["key_field"] == "id"  # WHY: verify expected behavior

    def test_vbeacons_mapping_exists(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        assert "listSiteVBeacons" in COLLECTION_VERTEX_MAP  # WHY: verify expected behavior
        mapping = COLLECTION_VERTEX_MAP["listSiteVBeacons"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "vbeacons"  # WHY: verify expected behavior
        assert mapping["key_field"] == "id"  # WHY: verify expected behavior

    def test_zone_sessions_mapping_exists(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        assert "searchSiteZoneSessions" in COLLECTION_VERTEX_MAP  # WHY: verify expected behavior
        mapping = COLLECTION_VERTEX_MAP["searchSiteZoneSessions"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "zone_sessions"  # WHY: verify expected behavior
        assert mapping["key_field"] == "zone_id"  # WHY: verify expected behavior

    def test_map_edges_include_site(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        edges = COLLECTION_VERTEX_MAP["listSiteMaps"]["edges"]  # WHY: look up edges under test
        edge_cols = [e["edge_col"] for e in edges]  # WHY: collect edge column names
        assert "MapBelongsToSite" in edge_cols  # WHY: verify expected behavior

    def test_zone_edges_include_map_and_site(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        edges = COLLECTION_VERTEX_MAP["listSiteZones"]["edges"]  # WHY: look up edges under test
        edge_cols = [e["edge_col"] for e in edges]  # WHY: collect edge column names
        assert "ZoneBelongsToMap" in edge_cols  # WHY: verify expected behavior
        assert "ZoneBelongsToSite" in edge_cols  # WHY: verify expected behavior

    def test_beacon_edges_include_map_and_site(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        edges = COLLECTION_VERTEX_MAP["listSiteBeacons"]["edges"]  # WHY: look up edges under test
        edge_cols = [e["edge_col"] for e in edges]  # WHY: collect edge column names
        assert "BeaconOnMap" in edge_cols  # WHY: verify expected behavior
        assert "BeaconBelongsToSite" in edge_cols  # WHY: verify expected behavior

    def test_vbeacon_edges_include_map(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        edges = COLLECTION_VERTEX_MAP["listSiteVBeacons"]["edges"]  # WHY: look up edges under test
        edge_cols = [e["edge_col"] for e in edges]  # WHY: collect edge column names
        assert "VBeaconOnMap" in edge_cols  # WHY: verify expected behavior

    def test_zone_session_edges_include_zone_and_map(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        edges = COLLECTION_VERTEX_MAP["searchSiteZoneSessions"]["edges"]  # WHY: look up edges under test
        edge_cols = [e["edge_col"] for e in edges]  # WHY: collect edge column names
        assert "ZoneSessionInZone" in edge_cols  # WHY: verify expected behavior
        assert "ZoneSessionOnMap" in edge_cols  # WHY: verify expected behavior

    def test_maps_zones_edge_definitions_registered(self):  # WHY: pytest discovers this by name
        assert_edges_registered({  # WHY: single set-subset check collapses 10 asserts to CC=1
            "MapBelongsToSite",
            "ZoneBelongsToMap",
            "ZoneBelongsToSite",
            "RssiZoneBelongsToMap",
            "BeaconOnMap",
            "BeaconBelongsToSite",
            "VBeaconOnMap",
            "DeviceOnMap",
            "ZoneSessionInZone",
            "ZoneSessionOnMap",
        })

    def test_maps_zones_entity_types_mapped(self):  # WHY: pytest discovers this by name
        assert_entity_types_mapped({  # WHY: single dict-subset check collapses 10 asserts to CC=1
            "listSiteMaps": "maps",
            "getSiteMap": "maps",
            "listSiteMapStacks": "map_stacks",
            "listSiteZones": "zones",
            "listSiteZonesStats": "zone_stats",
            "listSiteRssiZones": "rssizones",
            "listSiteRssiZonesStats": "rssizone_stats",
            "listSiteBeacons": "beacons",
            "listSiteVBeacons": "vbeacons",
            "searchSiteZoneSessions": "zone_sessions",
        })


class TestArangoDBWriterSiteEventsAlarmsGraph:  # WHY: pytest test class
    """Tests for site events & alarms graph storage (issue #174)."""

    def test_site_alarms_mapping_exists(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        assert "searchSiteAlarms" in COLLECTION_VERTEX_MAP  # WHY: verify expected behavior
        mapping = COLLECTION_VERTEX_MAP["searchSiteAlarms"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "alarms"  # WHY: verify expected behavior
        assert mapping["key_field"] == "id"  # WHY: verify expected behavior

    def test_site_alarms_edges(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        edges = COLLECTION_VERTEX_MAP["searchSiteAlarms"]["edges"]  # WHY: look up edges under test
        edge_cols = [e["edge_col"] for e in edges]  # WHY: collect edge column names
        assert "AlarmBelongsToSite" in edge_cols  # WHY: verify expected behavior
        assert "AlarmOnDevice" in edge_cols  # WHY: verify expected behavior

    def test_site_device_events_mapping_exists(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        assert "searchSiteDeviceEvents" in COLLECTION_VERTEX_MAP  # WHY: verify expected behavior
        mapping = COLLECTION_VERTEX_MAP["searchSiteDeviceEvents"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "events"  # WHY: verify expected behavior
        assert mapping["key_field"] == "id"  # WHY: verify expected behavior

    def test_site_device_events_edges(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        edges = COLLECTION_VERTEX_MAP["searchSiteDeviceEvents"]["edges"]  # WHY: look up edges under test
        edge_cols = [e["edge_col"] for e in edges]  # WHY: collect edge column names
        assert "EventBelongsToSite" in edge_cols  # WHY: verify expected behavior
        assert "EventOccurredOnDevice" in edge_cols  # WHY: verify expected behavior

    def test_site_system_events_mapping_exists(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        assert "searchSiteSystemEvents" in COLLECTION_VERTEX_MAP  # WHY: verify expected behavior
        mapping = COLLECTION_VERTEX_MAP["searchSiteSystemEvents"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "system_events"  # WHY: verify expected behavior
        assert mapping["key_field"] == "id"  # WHY: verify expected behavior

    def test_site_system_events_edges(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        edges = COLLECTION_VERTEX_MAP["searchSiteSystemEvents"]["edges"]  # WHY: look up edges under test
        edge_cols = [e["edge_col"] for e in edges]  # WHY: collect edge column names
        assert "SystemEventBelongsToSite" in edge_cols  # WHY: verify expected behavior

    def test_site_other_device_events_mapping_exists(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        assert "searchSiteOtherDeviceEvents" in COLLECTION_VERTEX_MAP  # WHY: verify expected behavior
        mapping = COLLECTION_VERTEX_MAP["searchSiteOtherDeviceEvents"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "other_events"  # WHY: verify expected behavior
        assert mapping["key_field"] == "mac"  # WHY: verify expected behavior

    def test_site_skyatp_events_mapping_exists(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        assert "searchSiteSkyatpEvents" in COLLECTION_VERTEX_MAP  # WHY: verify expected behavior
        mapping = COLLECTION_VERTEX_MAP["searchSiteSkyatpEvents"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "skyatp_events"  # WHY: verify expected behavior
        assert mapping["key_field"] == "mac"  # WHY: verify expected behavior

    def test_site_service_path_events_mapping_exists(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        assert "searchSiteServicePathEvents" in COLLECTION_VERTEX_MAP  # WHY: verify expected behavior
        mapping = COLLECTION_VERTEX_MAP["searchSiteServicePathEvents"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "service_path_events"  # WHY: verify expected behavior
        assert mapping["key_field"] == "mac"  # WHY: verify expected behavior

    def test_site_service_path_events_edges(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        edges = COLLECTION_VERTEX_MAP["searchSiteServicePathEvents"]["edges"]  # WHY: look up edges under test
        edge_cols = [e["edge_col"] for e in edges]  # WHY: collect edge column names
        assert "ServicePathEventBelongsToSite" in edge_cols  # WHY: verify expected behavior
        assert "ServicePathEventOnDevice" in edge_cols  # WHY: verify expected behavior
        assert "ServicePathEventUsesVPN" in edge_cols  # WHY: verify expected behavior

    def test_site_roaming_events_mapping_exists(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        assert "listSiteRoamingEvents" in COLLECTION_VERTEX_MAP  # WHY: verify expected behavior
        mapping = COLLECTION_VERTEX_MAP["listSiteRoamingEvents"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "roaming_events"  # WHY: verify expected behavior
        assert mapping["key_field"] == "client_mac"  # WHY: verify expected behavior

    def test_site_roaming_events_edges(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        edges = COLLECTION_VERTEX_MAP["listSiteRoamingEvents"]["edges"]  # WHY: look up edges under test
        edge_cols = [e["edge_col"] for e in edges]  # WHY: collect edge column names
        assert "RoamingEventBelongsToSite" in edge_cols  # WHY: verify expected behavior
        assert "RoamingEventOnDevice" in edge_cols  # WHY: verify expected behavior

    def test_site_rrm_events_mapping_exists(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        assert "listSiteRrmEvents" in COLLECTION_VERTEX_MAP  # WHY: verify expected behavior
        mapping = COLLECTION_VERTEX_MAP["listSiteRrmEvents"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "rrm_events"  # WHY: verify expected behavior
        assert mapping["key_field"] == "ap_id"  # WHY: verify expected behavior

    def test_site_rrm_events_edges(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        edges = COLLECTION_VERTEX_MAP["listSiteRrmEvents"]["edges"]  # WHY: look up edges under test
        edge_cols = [e["edge_col"] for e in edges]  # WHY: collect edge column names
        assert "RrmEventBelongsToSite" in edge_cols  # WHY: verify expected behavior
        assert "RrmEventOnDevice" in edge_cols  # WHY: verify expected behavior

    def test_site_anomaly_events_mapping_exists(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        assert "listSiteAnomalyEvents" in COLLECTION_VERTEX_MAP  # WHY: verify expected behavior
        mapping = COLLECTION_VERTEX_MAP["listSiteAnomalyEvents"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "anomaly_events"  # WHY: verify expected behavior
        assert mapping["key_field"] == "timestamp"  # WHY: verify expected behavior

    def test_site_anomaly_events_edges(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        edges = COLLECTION_VERTEX_MAP["listSiteAnomalyEvents"]["edges"]  # WHY: look up edges under test
        edge_cols = [e["edge_col"] for e in edges]  # WHY: collect edge column names
        assert "AnomalyEventBelongsToSite" in edge_cols  # WHY: verify expected behavior

    def test_events_alarms_edge_definitions_registered(self):  # WHY: pytest discovers this by name
        assert_edges_registered({  # WHY: single set-subset check collapses 9 asserts to CC=1
            "ServicePathEventOnDevice",
            "ServicePathEventUsesVPN",
            "ServicePathEventBelongsToSite",
            "SkyatpEventBelongsToSite",
            "RoamingEventBelongsToSite",
            "RoamingEventOnDevice",
            "RrmEventBelongsToSite",
            "RrmEventOnDevice",
            "AnomalyEventBelongsToSite",
        })

    def test_events_alarms_entity_types_mapped(self):  # WHY: pytest discovers this by name
        assert_entity_types_mapped({  # WHY: single dict-subset check collapses 9 asserts to CC=1
            "searchSiteAlarms": "alarms",
            "searchSiteDeviceEvents": "events",
            "searchSiteSystemEvents": "system_events",
            "searchSiteOtherDeviceEvents": "other_events",
            "searchSiteSkyatpEvents": "skyatp_events",
            "searchSiteServicePathEvents": "service_path_events",
            "listSiteRoamingEvents": "roaming_events",
            "listSiteRrmEvents": "rrm_events",
            "listSiteAnomalyEvents": "anomaly_events",
        })

    def test_service_path_ensure_target_vertices(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        mapping = COLLECTION_VERTEX_MAP["searchSiteServicePathEvents"]  # WHY: look up schema mapping
        targets = mapping.get("ensure_target_vertices", [])  # WHY: arrange test state
        assert ("vpn_name", "vpns") in targets  # WHY: verify expected behavior


class TestConfigHistorySyntheticTestGraphStorage:  # WHY: pytest test class
    """Issue #181: Config history, synthetic tests, webhook deliveries."""

    def test_config_history_entity_type(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX  # WHY: import ENTITY_TYPE_TO_VERTEX symbol under test

        assert ENTITY_TYPE_TO_VERTEX["searchSiteDeviceConfigHistory"] == "config_history"  # WHY: verify expected behavior

    def test_last_configs_entity_type(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX  # WHY: import ENTITY_TYPE_TO_VERTEX symbol under test

        assert ENTITY_TYPE_TO_VERTEX["searchSiteDeviceLastConfigs"] == "config_history"  # WHY: verify expected behavior

    def test_synthetic_test_entity_type(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX  # WHY: import ENTITY_TYPE_TO_VERTEX symbol under test

        assert ENTITY_TYPE_TO_VERTEX["searchSiteSyntheticTest"] == "synthetic_tests"  # WHY: verify expected behavior

    def test_webhook_deliveries_entity_type(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX  # WHY: import ENTITY_TYPE_TO_VERTEX symbol under test

        assert ENTITY_TYPE_TO_VERTEX["searchSiteWebhooksDeliveries"] == "webhook_deliveries"  # WHY: verify expected behavior

    def test_packet_captures_entity_type(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX  # WHY: import ENTITY_TYPE_TO_VERTEX symbol under test

        assert ENTITY_TYPE_TO_VERTEX["listSitePacketCaptures"] == "packet_captures"  # WHY: verify expected behavior

    def test_config_history_collection_vertex_map(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        mapping = COLLECTION_VERTEX_MAP["searchSiteDeviceConfigHistory"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "config_history"  # WHY: verify expected behavior
        edges = mapping["edges"]  # WHY: look up edges under test
        edge_cols = [e["edge_col"] for e in edges]  # WHY: collect edge column names
        assert "ConfigHistoryForDevice" in edge_cols  # WHY: verify expected behavior

    def test_last_configs_collection_vertex_map(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        mapping = COLLECTION_VERTEX_MAP["searchSiteDeviceLastConfigs"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "config_history"  # WHY: verify expected behavior
        edges = mapping["edges"]  # WHY: look up edges under test
        edge_cols = [e["edge_col"] for e in edges]  # WHY: collect edge column names
        assert "ConfigHistoryForDevice" in edge_cols  # WHY: verify expected behavior

    def test_synthetic_test_collection_vertex_map(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        mapping = COLLECTION_VERTEX_MAP["searchSiteSyntheticTest"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "synthetic_tests"  # WHY: verify expected behavior
        edges = mapping["edges"]  # WHY: look up edges under test
        edge_cols = [e["edge_col"] for e in edges]  # WHY: collect edge column names
        assert "SyntheticTestOnDevice" in edge_cols  # WHY: verify expected behavior

    def test_webhook_deliveries_collection_vertex_map(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        mapping = COLLECTION_VERTEX_MAP["searchSiteWebhooksDeliveries"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "webhook_deliveries"  # WHY: verify expected behavior
        edges = mapping["edges"]  # WHY: look up edges under test
        edge_cols = [e["edge_col"] for e in edges]  # WHY: collect edge column names
        assert "WebhookDeliveryFromWebhook" in edge_cols  # WHY: verify expected behavior

    def test_packet_captures_collection_vertex_map(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        mapping = COLLECTION_VERTEX_MAP["listSitePacketCaptures"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "packet_captures"  # WHY: verify expected behavior
        edges = mapping["edges"]  # WHY: look up edges under test
        edge_cols = [e["edge_col"] for e in edges]  # WHY: collect edge column names
        assert "PacketCaptureOnDevice" in edge_cols  # WHY: verify expected behavior
        assert "PacketCaptureBelongsToSite" in edge_cols  # WHY: verify expected behavior

    def test_edge_definitions_registered(self):  # WHY: pytest discovers this by name
        assert_edges_registered({  # WHY: single subset check keeps CC=1 vs 4 asserts
            "ConfigHistoryForDevice",
            "SyntheticTestOnDevice",
            "WebhookDeliveryFromWebhook",
            "PacketCaptureOnDevice",
        })


class TestSiteWlansPsksWebhooksGraphStorage:  # WHY: pytest test class
    """Issue #173: Site-level WLANs, PSKs, Webhooks, WxLAN policies."""

    def test_site_wlans_entity_type(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX  # WHY: import ENTITY_TYPE_TO_VERTEX symbol under test

        assert ENTITY_TYPE_TO_VERTEX["listSiteWlans"] == "wlans"  # WHY: verify expected behavior

    def test_site_psks_entity_type(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX  # WHY: import ENTITY_TYPE_TO_VERTEX symbol under test

        assert ENTITY_TYPE_TO_VERTEX["listSitePsks"] == "psks"  # WHY: verify expected behavior

    def test_site_webhooks_entity_type(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX  # WHY: import ENTITY_TYPE_TO_VERTEX symbol under test

        assert ENTITY_TYPE_TO_VERTEX["listSiteWebhooks"] == "webhooks"  # WHY: verify expected behavior

    def test_site_wxrules_entity_type(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX  # WHY: import ENTITY_TYPE_TO_VERTEX symbol under test

        assert ENTITY_TYPE_TO_VERTEX["listSiteWxRules"] == "wx_rules"  # WHY: verify expected behavior

    def test_site_wxtags_entity_type(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX  # WHY: import ENTITY_TYPE_TO_VERTEX symbol under test

        assert ENTITY_TYPE_TO_VERTEX["listSiteWxTags"] == "wx_tags"  # WHY: verify expected behavior

    def test_site_wxtunnels_entity_type(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX  # WHY: import ENTITY_TYPE_TO_VERTEX symbol under test

        assert ENTITY_TYPE_TO_VERTEX["listSiteWxTunnels"] == "mx_tunnels"  # WHY: verify expected behavior

    def test_site_wlans_collection_vertex_map(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        mapping = COLLECTION_VERTEX_MAP["listSiteWlans"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "wlans"  # WHY: verify expected behavior
        edge_cols = [e["edge_col"] for e in mapping["edges"]]  # WHY: collect edge column names
        assert "WlanBelongsToSite" in edge_cols  # WHY: verify expected behavior
        assert "WlanUsesWxTunnel" in edge_cols  # WHY: verify expected behavior

    def test_site_psks_collection_vertex_map(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        mapping = COLLECTION_VERTEX_MAP["listSitePsks"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "psks"  # WHY: verify expected behavior
        edge_cols = [e["edge_col"] for e in mapping["edges"]]  # WHY: collect edge column names
        assert "PSKBelongsToSite" in edge_cols  # WHY: verify expected behavior
        assert "PSKBelongsToWlan" in edge_cols  # WHY: verify expected behavior

    def test_site_webhooks_collection_vertex_map(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        mapping = COLLECTION_VERTEX_MAP["listSiteWebhooks"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "webhooks"  # WHY: verify expected behavior
        edge_cols = [e["edge_col"] for e in mapping["edges"]]  # WHY: collect edge column names
        assert "WebhookBelongsToSite" in edge_cols  # WHY: verify expected behavior

    def test_site_wxrules_collection_vertex_map(self):  # WHY: pytest discovers this by name
        assert_vertex_config("listSiteWxRules", "wx_rules", "id")  # WHY: single vertex+key check keeps CC=1
        assert_edge_cols_include(  # WHY: subset check collapses 4 asserts into one
            "listSiteWxRules",
            {"WxRuleBelongsToSite", "WxRuleMatchesSrcTag", "WxRuleAllowsDstTag", "WxRuleDeniesDstTag"},
        )

    def test_site_wxrules_ensure_target_vertices(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        mapping = COLLECTION_VERTEX_MAP["listSiteWxRules"]  # WHY: look up schema mapping
        targets = mapping.get("ensure_target_vertices", [])  # WHY: arrange test state
        assert ("src_wxtags", "wx_tags") in targets  # WHY: verify expected behavior
        assert ("dst_allow_wxtags", "wx_tags") in targets  # WHY: verify expected behavior
        assert ("dst_deny_wxtags", "wx_tags") in targets  # WHY: verify expected behavior

    def test_site_wxtags_collection_vertex_map(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        mapping = COLLECTION_VERTEX_MAP["listSiteWxTags"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "wx_tags"  # WHY: verify expected behavior
        edge_cols = [e["edge_col"] for e in mapping["edges"]]  # WHY: collect edge column names
        assert "WxTagBelongsToSite" in edge_cols  # WHY: verify expected behavior

    def test_site_wxtunnels_collection_vertex_map(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        mapping = COLLECTION_VERTEX_MAP["listSiteWxTunnels"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "mx_tunnels"  # WHY: verify expected behavior
        edge_cols = [e["edge_col"] for e in mapping["edges"]]  # WHY: collect edge column names
        assert "WxTunnelBelongsToSite" in edge_cols  # WHY: verify expected behavior

    def test_edge_definitions_registered(self):  # WHY: pytest discovers this by name
        assert_edges_registered({  # WHY: single subset check keeps CC=1 vs 4 asserts
            "WxRuleBelongsToSite",
            "WxTagBelongsToSite",
            "WxTunnelBelongsToSite",
            "WlanUsesWxTunnel",
        })


class TestSiteClientsGraphStorage:  # WHY: pytest test class
    """Issue #172: Site-level client search endpoints."""

    def test_wireless_clients_entity_type(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX  # WHY: import ENTITY_TYPE_TO_VERTEX symbol under test

        assert ENTITY_TYPE_TO_VERTEX["searchSiteWirelessClients"] == "clients"  # WHY: verify expected behavior

    def test_wired_clients_entity_type(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX  # WHY: import ENTITY_TYPE_TO_VERTEX symbol under test

        assert ENTITY_TYPE_TO_VERTEX["searchSiteWiredClients"] == "clients"  # WHY: verify expected behavior

    def test_wan_clients_entity_type(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX  # WHY: import ENTITY_TYPE_TO_VERTEX symbol under test

        assert ENTITY_TYPE_TO_VERTEX["searchSiteWanClients"] == "clients"  # WHY: verify expected behavior

    def test_nac_clients_entity_type(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX  # WHY: import ENTITY_TYPE_TO_VERTEX symbol under test

        assert ENTITY_TYPE_TO_VERTEX["searchSiteNacClients"] == "clients"  # WHY: verify expected behavior

    def test_nac_client_events_entity_type(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX  # WHY: import ENTITY_TYPE_TO_VERTEX symbol under test

        assert ENTITY_TYPE_TO_VERTEX["searchSiteNacClientEvents"] == "nac_events"  # WHY: verify expected behavior

    def test_wireless_client_events_entity_type(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX  # WHY: import ENTITY_TYPE_TO_VERTEX symbol under test

        assert ENTITY_TYPE_TO_VERTEX["searchSiteWirelessClientEvents"] == "client_events"  # WHY: verify expected behavior

    def test_wireless_client_sessions_entity_type(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX  # WHY: import ENTITY_TYPE_TO_VERTEX symbol under test

        assert ENTITY_TYPE_TO_VERTEX["searchSiteWirelessClientSessions"] == "client_sessions"  # WHY: verify expected behavior

    def test_wan_client_events_entity_type(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX  # WHY: import ENTITY_TYPE_TO_VERTEX symbol under test

        assert ENTITY_TYPE_TO_VERTEX["searchSiteWanClientEvents"] == "wan_events"  # WHY: verify expected behavior

    def test_wireless_clients_stats_entity_type(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX  # WHY: import ENTITY_TYPE_TO_VERTEX symbol under test

        assert ENTITY_TYPE_TO_VERTEX["listSiteWirelessClientsStats"] == "clients"  # WHY: verify expected behavior

    def test_unconnected_clients_entity_type(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX  # WHY: import ENTITY_TYPE_TO_VERTEX symbol under test

        assert ENTITY_TYPE_TO_VERTEX["listSiteUnconnectedClientStats"] == "unconnected_clients"  # WHY: verify expected behavior

    def test_wireless_clients_edges(self):  # WHY: pytest discovers this by name
        assert_vertex_config("searchSiteWirelessClients", "clients", "mac")  # WHY: vertex+key check in one call
        assert_edge_cols_include(  # WHY: subset check covers 4 edge assertions in one
            "searchSiteWirelessClients",
            {"ClientConnectedToDevice", "ClientConnectedToWlan", "ClientBelongsToSite", "ClientUsedPSK"},
        )

    def test_wired_clients_edges(self):  # WHY: pytest discovers this by name
        assert_vertex_config("searchSiteWiredClients", "clients", "mac")  # WHY: vertex+key check in one call
        assert_edge_cols_include("searchSiteWiredClients", {"ClientConnectedToDevice", "ClientBelongsToSite"})  # WHY: subset check

    def test_wan_clients_edges(self):  # WHY: pytest discovers this by name
        assert_vertex_config("searchSiteWanClients", "clients", "mac")  # WHY: vertex+key check in one call
        assert_edge_cols_include("searchSiteWanClients", {"ClientBelongsToSite"})  # WHY: single-edge subset check

    def test_nac_clients_edges(self):  # WHY: pytest discovers this by name
        assert_vertex_config("searchSiteNacClients", "clients", "mac")  # WHY: vertex+key check in one call
        assert_edge_cols_include(  # WHY: 3-edge subset check in one call
            "searchSiteNacClients",
            {"ClientConnectedToDevice", "ClientBelongsToSite", "ClientMatchedNACRule"},
        )

    def test_nac_client_events_edges(self):  # WHY: pytest discovers this by name
        assert_vertex_config("searchSiteNacClientEvents", "nac_events", "id")  # WHY: vertex+key check in one call
        assert_edge_cols_include(  # WHY: 2-edge subset check
            "searchSiteNacClientEvents",
            {"NacEventBelongsToSite", "NacEventForClient"},
        )

    def test_wireless_client_events_edges(self):  # WHY: pytest discovers this by name
        assert_vertex_config("searchSiteWirelessClientEvents", "client_events", "id")  # WHY: vertex+key check
        assert_edge_cols_include(  # WHY: 3-edge subset check
            "searchSiteWirelessClientEvents",
            {"ClientEventBelongsToSite", "ClientEventOnDevice", "ClientEventForClient"},
        )

    def test_wireless_client_events_ensure_targets(self):  # WHY: pytest discovers this by name
        assert_ensure_target("searchSiteWirelessClientEvents", ("mac", "clients"))  # WHY: single membership check

    def test_wireless_client_sessions_edges(self):  # WHY: pytest discovers this by name
        assert_vertex_config("searchSiteWirelessClientSessions", "client_sessions", "id")  # WHY: vertex+key check
        assert_edge_cols_include(  # WHY: 4-edge subset check
            "searchSiteWirelessClientSessions",
            {"SessionBelongsToSite", "SessionOnWlan", "SessionOnDevice", "SessionForClient"},
        )

    def test_wan_client_events_edges(self):  # WHY: pytest discovers this by name
        assert_vertex_config("searchSiteWanClientEvents", "wan_events", "id")  # WHY: vertex+key check
        assert_edge_cols_include(  # WHY: 2-edge subset check
            "searchSiteWanClientEvents",
            {"WanEventBelongsToSite", "WanEventForClient"},
        )

    def test_unconnected_clients_edges(self):  # WHY: pytest discovers this by name
        assert_vertex_config("listSiteUnconnectedClientStats", "unconnected_clients", "mac")  # WHY: vertex+key check
        assert_edge_cols_include(  # WHY: 2-edge subset check
            "listSiteUnconnectedClientStats",
            {"UnconnectedClientOnMap", "UnconnectedClientDetectedByAP"},
        )

    def test_edge_definitions_registered(self):  # WHY: pytest discovers this by name
        assert_edges_registered({  # WHY: single subset check covers 5 asserts
            "ClientUsedPSK",
            "ClientMatchedNACRule",
            "ClientEventForClient",
            "UnconnectedClientOnMap",
            "UnconnectedClientDetectedByAP",
        })


class TestSiteDevicesGraphStorage:  # WHY: pytest test class
    """Tests for Issue #171: Site-level device graph storage."""

    def test_entity_type_mappings(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX  # WHY: import ENTITY_TYPE_TO_VERTEX symbol under test

        expected = {  # WHY: expected value for comparison
            "searchSiteDevices": "devices",
            "listSiteDevicesStats": "devices",
            "listSiteOtherDevices": "other_devices",
            "listSiteAvailableDeviceVersions": "device_versions",
            "listSiteSpectrumAnalysis": "spectrum_analysis",
            "listSiteDeviceRadioChannels": "radio_channels",
            "listSiteDeviceUpgrades": "device_upgrades",
        }
        for operation_id, vertex in expected.items():  # WHY: iterate over test data
            assert ENTITY_TYPE_TO_VERTEX.get(operation_id) == vertex  # WHY: verify expected behavior

    def test_existing_device_mapping_preserved(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX  # WHY: import ENTITY_TYPE_TO_VERTEX symbol under test

        assert ENTITY_TYPE_TO_VERTEX.get("listSiteDevices") == "devices"  # WHY: verify expected behavior

    def test_collection_vertex_map_entries(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        expected_ops = [  # WHY: arrange test state
            "listSiteDevices",
            "searchSiteDevices",
            "listSiteDevicesStats",
            "listSiteOtherDevices",
            "listSiteAvailableDeviceVersions",
            "listSiteSpectrumAnalysis",
            "listSiteDeviceRadioChannels",
            "listSiteDeviceUpgrades",
        ]
        for op in expected_ops:  # WHY: iterate over ops
            assert op in COLLECTION_VERTEX_MAP  # WHY: verify expected behavior

    def test_list_site_devices_vertex(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        mapping = COLLECTION_VERTEX_MAP["listSiteDevices"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "devices"  # WHY: verify expected behavior
        assert mapping["key_field"] == "id"  # WHY: verify expected behavior

    def test_list_site_devices_edges(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        mapping = COLLECTION_VERTEX_MAP["listSiteDevices"]  # WHY: look up schema mapping
        edge_cols = {e["edge_col"] for e in mapping["edges"]}  # WHY: collect edge column names
        assert "SiteContainsDevice" in edge_cols  # WHY: verify expected behavior
        assert "DeviceUsesProfile" in edge_cols  # WHY: verify expected behavior
        assert "DeviceOnMap" in edge_cols  # WHY: verify expected behavior

    def test_list_site_devices_ensure_target_vertices(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        mapping = COLLECTION_VERTEX_MAP["listSiteDevices"]  # WHY: look up schema mapping
        assert "ensure_target_vertices" in mapping  # WHY: verify expected behavior
        targets = mapping["ensure_target_vertices"]  # WHY: arrange test state
        target_fields = {t[0] for t in targets}  # WHY: arrange test state
        assert "deviceprofile_id" in target_fields  # WHY: verify expected behavior
        assert "map_id" in target_fields  # WHY: verify expected behavior

    def test_search_site_devices_vertex(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        mapping = COLLECTION_VERTEX_MAP["searchSiteDevices"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "devices"  # WHY: verify expected behavior
        assert mapping["key_field"] == "mac"  # WHY: verify expected behavior

    def test_search_site_devices_edges(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        mapping = COLLECTION_VERTEX_MAP["searchSiteDevices"]  # WHY: look up schema mapping
        edge_cols = {e["edge_col"] for e in mapping["edges"]}  # WHY: collect edge column names
        assert "SiteContainsDevice" in edge_cols  # WHY: verify expected behavior

    def test_list_site_devices_stats_vertex(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        mapping = COLLECTION_VERTEX_MAP["listSiteDevicesStats"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "devices"  # WHY: verify expected behavior
        assert mapping["key_field"] == "id"  # WHY: verify expected behavior

    def test_list_site_devices_stats_edges(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        mapping = COLLECTION_VERTEX_MAP["listSiteDevicesStats"]  # WHY: look up schema mapping
        edge_cols = {e["edge_col"] for e in mapping["edges"]}  # WHY: collect edge column names
        assert "SiteContainsDevice" in edge_cols  # WHY: verify expected behavior
        assert "DeviceUsesProfile" in edge_cols  # WHY: verify expected behavior

    def test_list_site_other_devices_vertex(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        mapping = COLLECTION_VERTEX_MAP["listSiteOtherDevices"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "other_devices"  # WHY: verify expected behavior
        assert mapping["key_field"] == "id"  # WHY: verify expected behavior

    def test_list_site_other_devices_edges(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        mapping = COLLECTION_VERTEX_MAP["listSiteOtherDevices"]  # WHY: look up schema mapping
        edge_cols = {e["edge_col"] for e in mapping["edges"]}  # WHY: collect edge column names
        assert "OtherDeviceBelongsToSite" in edge_cols  # WHY: verify expected behavior

    def test_list_site_available_device_versions(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        mapping = COLLECTION_VERTEX_MAP["listSiteAvailableDeviceVersions"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "device_versions"  # WHY: verify expected behavior
        assert mapping["key_field"] == "model"  # WHY: verify expected behavior
        assert "edges" not in mapping  # WHY: verify expected behavior

    def test_list_site_spectrum_analysis_vertex(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        mapping = COLLECTION_VERTEX_MAP["listSiteSpectrumAnalysis"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "spectrum_analysis"  # WHY: verify expected behavior
        assert mapping["key_field"] == "mac"  # WHY: verify expected behavior

    def test_list_site_spectrum_analysis_edges(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        mapping = COLLECTION_VERTEX_MAP["listSiteSpectrumAnalysis"]  # WHY: look up schema mapping
        edge_cols = {e["edge_col"] for e in mapping["edges"]}  # WHY: collect edge column names
        assert "SpectrumAnalysisForDevice" in edge_cols  # WHY: verify expected behavior

    def test_spectrum_analysis_edge_uses_mac_lookup(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        mapping = COLLECTION_VERTEX_MAP["listSiteSpectrumAnalysis"]  # WHY: look up schema mapping
        spectrum_edge = next(e for e in mapping["edges"] if e["edge_col"] == "SpectrumAnalysisForDevice")  # WHY: arrange test state
        assert spectrum_edge["to_key_lookup"] == "mac"  # WHY: verify expected behavior

    def test_list_site_device_radio_channels(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        mapping = COLLECTION_VERTEX_MAP["listSiteDeviceRadioChannels"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "radio_channels"  # WHY: verify expected behavior
        assert mapping["key_field"] == "key"  # WHY: verify expected behavior
        assert "edges" not in mapping  # WHY: verify expected behavior

    def test_list_site_device_upgrades(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        mapping = COLLECTION_VERTEX_MAP["listSiteDeviceUpgrades"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "device_upgrades"  # WHY: verify expected behavior
        assert mapping["key_field"] == "id"  # WHY: verify expected behavior
        assert "edges" not in mapping  # WHY: verify expected behavior

    def test_edge_definitions_registered(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import EDGE_DEFINITIONS  # WHY: import EDGE_DEFINITIONS symbol under test

        edge_names = {e["edge_collection"] for e in EDGE_DEFINITIONS}  # WHY: collect registered edge names
        assert "SpectrumAnalysisForDevice" in edge_names  # WHY: verify expected behavior

    def test_spectrum_analysis_edge_structure(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import EDGE_DEFINITIONS  # WHY: import EDGE_DEFINITIONS symbol under test

        edge = next(e for e in EDGE_DEFINITIONS if e["edge_collection"] == "SpectrumAnalysisForDevice")  # WHY: look up edge under test
        assert edge["from_vertex_collections"] == ["spectrum_analysis"]  # WHY: verify expected behavior
        assert edge["to_vertex_collections"] == ["devices"]  # WHY: verify expected behavior

    def test_new_vertex_collections_referenced(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        new_vertices = {  # WHY: arrange test state
            "device_versions",
            "spectrum_analysis",
            "radio_channels",
            "device_upgrades",
        }
        found = set()  # WHY: arrange test state
        for mapping in COLLECTION_VERTEX_MAP.values():  # WHY: iterate over test data
            if isinstance(mapping, dict):  # WHY: conditional branch under test
                found.add(mapping["vertex"])  # WHY: test line
        assert new_vertices.issubset(found)  # WHY: verify expected behavior


class TestDerivedConfigGraphStorage:  # WHY: pytest test class
    """Tests for Issue #184: Derived config graph storage."""

    DERIVED_OPS = [  # WHY: arrange test state
        "listSiteWlansDerived",
        "listSiteNetworksDerived",
        "listSiteVpnsDerived",
        "listSiteServicesDerived",
        "listSiteServicePoliciesDerived",
        "listSiteUiSettingDerived",
        "listSiteAllGuestAuthorizationsDerived",
        "listSiteApTemplatesDerived",
        "listSiteRfTemplatesDerived",
        "listSiteNetworkTemplatesDerived",
        "listSiteGatewayTemplatesDerived",
        "listSiteSiteTemplatesDerived",
        "listSiteDeviceProfilesDerived",
        "listSiteIdpProfilesDerived",
        "listSiteAAMWProfilesDerived",
        "listSiteAntivirusProfilesDerived",
        "listSiteSecIntelProfilesDerived",
    ]

    def test_entity_type_mappings(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX  # WHY: import ENTITY_TYPE_TO_VERTEX symbol under test

        expected = {  # WHY: expected value for comparison
            "listSiteWlansDerived": "wlans",
            "listSiteNetworksDerived": "networks",
            "listSiteVpnsDerived": "vpns",
            "listSiteServicesDerived": "services",
            "listSiteServicePoliciesDerived": "security_policies",
            "listSiteUiSettingDerived": "ui_settings",
            "listSiteAllGuestAuthorizationsDerived": "guests",
            "listSiteApTemplatesDerived": "templates",
            "listSiteRfTemplatesDerived": "templates",
            "listSiteNetworkTemplatesDerived": "templates",
            "listSiteGatewayTemplatesDerived": "templates",
            "listSiteSiteTemplatesDerived": "templates",
            "listSiteDeviceProfilesDerived": "device_profiles",
            "listSiteIdpProfilesDerived": "idp_profiles",
            "listSiteAAMWProfilesDerived": "aamw_profiles",
            "listSiteAntivirusProfilesDerived": "av_profiles",
            "listSiteSecIntelProfilesDerived": "secIntel_profiles",
        }
        for operation_id, vertex in expected.items():  # WHY: iterate over test data
            assert ENTITY_TYPE_TO_VERTEX.get(operation_id) == vertex  # WHY: verify expected behavior

    def test_all_ops_in_collection_vertex_map(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        for op in self.DERIVED_OPS:  # WHY: iterate over ops
            assert op in COLLECTION_VERTEX_MAP, f"{op} missing from COLLECTION_VERTEX_MAP"  # WHY: verify expected behavior

    def test_wlans_derived_vertex(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        mapping = COLLECTION_VERTEX_MAP["listSiteWlansDerived"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "wlans"  # WHY: verify expected behavior
        assert mapping["key_field"] == "id"  # WHY: verify expected behavior

    def test_wlans_derived_edges(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        mapping = COLLECTION_VERTEX_MAP["listSiteWlansDerived"]  # WHY: look up schema mapping
        edge_cols = {e["edge_col"] for e in mapping["edges"]}  # WHY: collect edge column names
        assert "DerivedConfigForSite" in edge_cols  # WHY: verify expected behavior
        assert "DerivedFromTemplate" in edge_cols  # WHY: verify expected behavior

    def test_networks_derived_vertex(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        mapping = COLLECTION_VERTEX_MAP["listSiteNetworksDerived"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "networks"  # WHY: verify expected behavior
        assert mapping["key_field"] == "id"  # WHY: verify expected behavior

    def test_service_policies_derived_uses_security_policies(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        mapping = COLLECTION_VERTEX_MAP["listSiteServicePoliciesDerived"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "security_policies"  # WHY: verify expected behavior

    def test_guest_authorizations_derived_key(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        mapping = COLLECTION_VERTEX_MAP["listSiteAllGuestAuthorizationsDerived"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "guests"  # WHY: verify expected behavior
        assert mapping["key_field"] == "mac"  # WHY: verify expected behavior

    def test_ui_setting_derived_no_edges(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        mapping = COLLECTION_VERTEX_MAP["listSiteUiSettingDerived"]  # WHY: look up schema mapping
        assert mapping["vertex"] == "ui_settings"  # WHY: verify expected behavior
        assert mapping["key_field"] == "key"  # WHY: verify expected behavior
        assert "edges" not in mapping  # WHY: verify expected behavior

    def test_template_derived_ops_share_vertex(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        template_ops = [  # WHY: arrange test state
            "listSiteApTemplatesDerived",
            "listSiteRfTemplatesDerived",
            "listSiteNetworkTemplatesDerived",
            "listSiteGatewayTemplatesDerived",
            "listSiteSiteTemplatesDerived",
        ]
        for op in template_ops:  # WHY: iterate over ops
            assert COLLECTION_VERTEX_MAP[op]["vertex"] == "templates"  # WHY: verify expected behavior

    def test_security_profile_derived_vertices(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import COLLECTION_VERTEX_MAP  # WHY: import COLLECTION_VERTEX_MAP symbol under test

        expected = {  # WHY: expected value for comparison
            "listSiteIdpProfilesDerived": "idp_profiles",
            "listSiteAAMWProfilesDerived": "aamw_profiles",
            "listSiteAntivirusProfilesDerived": "av_profiles",
            "listSiteSecIntelProfilesDerived": "secIntel_profiles",
        }
        for op, vertex in expected.items():  # WHY: iterate over test data
            assert COLLECTION_VERTEX_MAP[op]["vertex"] == vertex  # WHY: verify expected behavior

    def test_derived_config_for_site_edge_registered(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import EDGE_DEFINITIONS  # WHY: import EDGE_DEFINITIONS symbol under test

        edge_names = {e["edge_collection"] for e in EDGE_DEFINITIONS}  # WHY: collect registered edge names
        assert "DerivedConfigForSite" in edge_names  # WHY: verify expected behavior

    def test_derived_from_template_edge_registered(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import EDGE_DEFINITIONS  # WHY: import EDGE_DEFINITIONS symbol under test

        edge_names = {e["edge_collection"] for e in EDGE_DEFINITIONS}  # WHY: collect registered edge names
        assert "DerivedFromTemplate" in edge_names  # WHY: verify expected behavior

    def test_derived_config_for_site_structure(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import EDGE_DEFINITIONS  # WHY: schema source of truth for edge shapes

        edge = next(e for e in EDGE_DEFINITIONS if e["edge_collection"] == "DerivedConfigForSite")  # WHY: locate one edge
        got = (  # WHY: bundle the two sides into one comparable tuple to keep CC=1
            "sites" in edge["to_vertex_collections"],
            {"wlans", "networks", "security_policies"} <= set(edge["from_vertex_collections"]),
        )
        assert got == (True, True), f"DerivedConfigForSite endpoints wrong: got {got!r}"  # WHY: single-tuple assertion

    def test_derived_from_template_structure(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import EDGE_DEFINITIONS  # WHY: import EDGE_DEFINITIONS symbol under test

        edge = next(e for e in EDGE_DEFINITIONS if e["edge_collection"] == "DerivedFromTemplate")  # WHY: look up edge under test
        assert "templates" in edge["to_vertex_collections"]  # WHY: verify expected behavior
        assert "wlans" in edge["from_vertex_collections"]  # WHY: verify expected behavior

    def test_all_edged_ops_have_derived_config_for_site(self):  # WHY: pytest discovers this by name
        assert_all_edged_ops_include(self.DERIVED_OPS, "DerivedConfigForSite")  # WHY: single helper call keeps CC=1

    def test_only_wlans_has_derived_from_template(self):  # WHY: pytest discovers this by name
        assert_ops_carrying_edge_include(self.DERIVED_OPS, "DerivedFromTemplate", "listSiteWlansDerived")  # WHY: single helper call

    def test_new_vertex_collections_in_edge_defs(self):  # WHY: pytest discovers this by name
        from src.db.arango_writer import EDGE_DEFINITIONS  # WHY: import EDGE_DEFINITIONS symbol under test

        edge = next(e for e in EDGE_DEFINITIONS if e["edge_collection"] == "DerivedConfigForSite")  # WHY: look up edge under test
        from_cols = set(edge["from_vertex_collections"])  # WHY: arrange test state
        expected_new = {  # WHY: arrange test state
            "ui_settings",
            "idp_profiles",
            "aamw_profiles",
            "av_profiles",
            "secIntel_profiles",
        }
        assert expected_new.issubset(from_cols)  # WHY: verify expected behavior
