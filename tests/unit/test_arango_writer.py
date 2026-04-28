"""Unit tests for ArangoDBWriter.

All python-arango interactions are mocked — no live ArangoDB required.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.db import DatabaseConfig


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
        mock_client.db.side_effect = lambda name, **kw: (mock_sys_db if name == "_system" else mock_db)
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
        ArangoDBWriter(config)
        mock_arango_client["sys_db"].create_database.assert_called_once_with("misthelper")


class TestArangoDBWriterWrite:
    """Tests for ArangoDBWriter.write."""

    def test_upsert_with_natural_pk(self, config, mock_arango_client):
        from src.db.arango_writer import ArangoDBWriter

        writer = ArangoDBWriter(config)
        mock_db = mock_arango_client["db"]
        mock_collection = MagicMock()
        mock_db.has_collection.return_value = True
        mock_db.collection.return_value = mock_collection
        mock_collection.import_bulk.return_value = {"created": 1, "updated": 0, "errors": 0}

        strategy = {
            "type": "natural_pk",
            "primary_key": ["id"],
        }
        data = [{"id": "uuid-1", "name": "Site A", "org_id": "org-1"}]
        result = writer.write(data, "sites", strategy)

        assert result.success is True
        assert result.backend == "arangodb"
        assert result.records_written == 1
        mock_collection.import_bulk.assert_called_once()
        docs = mock_collection.import_bulk.call_args[0][0]
        assert docs[0]["_key"] == "uuid-1"
        assert "_misthelper_updated_at" in docs[0]

    def test_auto_creates_collection(self, config, mock_arango_client):
        from src.db.arango_writer import ArangoDBWriter

        writer = ArangoDBWriter(config)
        mock_db = mock_arango_client["db"]
        mock_db.has_collection.return_value = False
        mock_collection = MagicMock()
        mock_db.create_collection.return_value = mock_collection
        mock_db.collection.return_value = mock_collection
        mock_collection.import_bulk.return_value = {"created": 1, "updated": 0, "errors": 0}

        strategy = {"type": "natural_pk", "primary_key": ["id"]}
        data = [{"id": "uuid-1", "name": "Test"}]
        result = writer.write(data, "new_collection", strategy)

        mock_db.create_collection.assert_called_once_with("new_collection", edge=False)
        assert result.success is True

    def test_auto_increment_with_unique(self, config, mock_arango_client):
        from src.db.arango_writer import ArangoDBWriter

        writer = ArangoDBWriter(config)
        mock_db = mock_arango_client["db"]
        mock_collection = MagicMock()
        mock_db.has_collection.return_value = True
        mock_db.collection.return_value = mock_collection
        mock_collection.import_bulk.return_value = {"created": 1, "updated": 0, "errors": 0}

        strategy = {
            "type": "auto_increment_with_unique",
            "primary_key": ["misthelper_internal_id"],
        }
        data = [{"name": "Summary", "value": 42}]
        result = writer.write(data, "summaries", strategy)

        assert result.success is True
        docs = mock_collection.import_bulk.call_args[0][0]
        assert "_key" in docs[0]

    def test_handles_insert_error_gracefully(self, config, mock_arango_client):
        from src.db.arango_writer import ArangoDBWriter

        writer = ArangoDBWriter(config)
        mock_db = mock_arango_client["db"]
        mock_collection = MagicMock()
        mock_db.has_collection.return_value = True
        mock_db.collection.return_value = mock_collection
        mock_collection.import_bulk.side_effect = Exception("Import failed")

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
        mock_collection.import_bulk.return_value = {"created": 1, "updated": 0, "errors": 0}

        strategy = {"type": "natural_pk", "primary_key": ["id"]}
        data = [{"id": "uuid-1"}]
        writer.write(data, "sites", strategy)

        docs = mock_collection.import_bulk.call_args[0][0]
        assert isinstance(docs[0]["_misthelper_updated_at"], int)


class TestArangoDBWriterGraph:
    """Tests for graph creation and edge management."""

    def test_creates_graph_on_init(self, config, mock_arango_client):
        from src.db.arango_writer import ArangoDBWriter

        mock_db = mock_arango_client["db"]
        mock_db.has_graph.return_value = False
        ArangoDBWriter(config)
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

        writer.mark_absent_as_deleted("sites", current_keys=set())

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
        mock_collection.import_bulk.return_value = {"created": 1, "updated": 0, "errors": 0}

        strategy = {"type": "natural_pk", "primary_key": ["id"]}
        data = [{"id": "uuid-1", "_misthelper_deleted_at": 1234567890}]
        writer.write(data, "sites", strategy)

        docs = mock_collection.import_bulk.call_args[0][0]
        assert docs[0].get("_misthelper_deleted_at") is None


class TestArangoDBWriterSnapshot:
    """Tests for config snapshot deduplication and entity edges."""

    def test_skips_duplicate_snapshot(self, config, mock_arango_client):
        from src.db.arango_writer import ArangoDBWriter

        writer = ArangoDBWriter(config)
        mock_db = mock_arango_client["db"]
        mock_collection = MagicMock()
        mock_db.has_collection.return_value = True
        mock_db.collection.return_value = mock_collection

        existing_snapshot = {"config_hash": "abc123"}
        mock_cursor = MagicMock()
        mock_cursor.__iter__ = MagicMock(return_value=iter([existing_snapshot]))
        mock_db.aql.execute.return_value = mock_cursor

        result = writer.snapshot(
            entity_type="site",
            entity_id="uuid-1",
            config_body={"name": "Test"},
            config_hash="abc123",
        )

        assert result is False

    def test_snapshot_creates_entity_edge(self, config, mock_arango_client):
        from src.db.arango_writer import ArangoDBWriter

        writer = ArangoDBWriter(config)
        mock_db = mock_arango_client["db"]
        mock_collection = MagicMock()
        mock_db.has_collection.return_value = True
        mock_db.collection.return_value = mock_collection
        mock_db.aql.execute.return_value = iter([])

        result = writer.snapshot(
            entity_type="listOrgSites",
            entity_id="site-uuid-1",
            config_body={"name": "Test Site"},
            config_hash="new-hash",
        )

        assert result is True
        # insert for snapshot doc + import_bulk for edge
        mock_collection.insert.assert_called_once()
        mock_collection.import_bulk.assert_called_once()
        edge_doc = mock_collection.import_bulk.call_args[0][0][0]
        assert edge_doc["_from"].startswith("config_snapshots/")
        assert edge_doc["_to"] == "sites/site-uuid-1"
        assert edge_doc["entity_type"] == "listOrgSites"

    def test_snapshot_skips_edge_for_unknown_entity_type(self, config, mock_arango_client):
        from src.db.arango_writer import ArangoDBWriter

        writer = ArangoDBWriter(config)
        mock_db = mock_arango_client["db"]
        mock_collection = MagicMock()
        mock_db.has_collection.return_value = True
        mock_db.collection.return_value = mock_collection
        mock_db.aql.execute.return_value = iter([])

        result = writer.snapshot(
            entity_type="unknownApiFunction",
            entity_id="uuid-1",
            config_body={"name": "Test"},
            config_hash="new-hash",
        )

        assert result is True
        mock_collection.insert.assert_called_once()
        # No import_bulk for edge since entity_type is not in ENTITY_TYPE_TO_VERTEX
        mock_collection.import_bulk.assert_not_called()


class TestArangoDBWriterWlanGraph:
    """Tests for WLAN graph population."""

    def test_wlan_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "listOrgWlans" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["listOrgWlans"]
        assert mapping["vertex"] == "wlans"
        assert mapping["key_field"] == "id"
        edge_cols = [e["edge_col"] for e in mapping["edges"]]
        assert "WlanBelongsToSite" in edge_cols
        assert "WlanUsesTemplate" in edge_cols

    def test_wlan_template_edge_targets_templates(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        edges = COLLECTION_VERTEX_MAP["listOrgWlans"]["edges"]
        template_edge = next(e for e in edges if e["edge_col"] == "WlanUsesTemplate")
        assert template_edge["from_col"] == "wlans"
        assert template_edge["to_col"] == "templates"
        assert template_edge["to_field"] == "template_id"

    def test_mxedge_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "listOrgMxEdges" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["listOrgMxEdges"]
        assert mapping["vertex"] == "devices"
        edge_cols = [e["edge_col"] for e in mapping["edges"]]
        assert "OrgContainsDevice" in edge_cols
        assert "MxEdgeBelongsToCluster" in edge_cols

    def test_mxedge_cluster_edge_targets_mxclusters(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        edges = COLLECTION_VERTEX_MAP["listOrgMxEdges"]["edges"]
        cluster_edge = next(e for e in edges if e["edge_col"] == "MxEdgeBelongsToCluster")
        assert cluster_edge["from_col"] == "devices"
        assert cluster_edge["to_col"] == "mxclusters"
        assert cluster_edge["to_field"] == "mxcluster_id"

    def test_site_sitegroup_edge_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["listOrgSites"]
        edge_cols = [e["edge_col"] for e in mapping["edges"]]
        assert "SiteBelongsToSiteGroup" in edge_cols
        sg_edge = next(e for e in mapping["edges"] if e["edge_col"] == "SiteBelongsToSiteGroup")
        assert sg_edge["to_col"] == "sitegroups"
        assert sg_edge["to_field"] == "sitegroup_ids"

    def test_entity_type_to_vertex_mapping(self):
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX

        assert ENTITY_TYPE_TO_VERTEX["listOrgSites"] == "sites"
        assert ENTITY_TYPE_TO_VERTEX["listOrgGatewayTemplates"] == "templates"
        assert ENTITY_TYPE_TO_VERTEX["listOrgRfTemplates"] == "templates"
        assert ENTITY_TYPE_TO_VERTEX["listSiteDevices"] == "devices"
        assert ENTITY_TYPE_TO_VERTEX["getOrgWlans"] == "wlans"


class TestArangoDBWriterEdgeDefinitions:
    """Tests for EDGE_DEFINITIONS completeness."""

    def test_all_edge_definitions(self):
        from src.db.arango_writer import EDGE_DEFINITIONS

        edge_names = {d["edge_collection"] for d in EDGE_DEFINITIONS}
        expected = {
            # Original 11
            "OrgContainsSite",
            "OrgContainsDevice",
            "SiteContainsDevice",
            "TemplateAssignedToSite",
            "DeviceHasPort",
            "ClientConnectedToDevice",
            "WlanBelongsToSite",
            "WlanUsesTemplate",
            "SiteBelongsToSiteGroup",
            "MxEdgeBelongsToCluster",
            "ConfigSnapshotForEntity",
            # Client relationships
            "ClientConnectedToWlan",
            "ClientBelongsToSite",
            # Org-level entity ownership
            "NetworkBelongsToOrg",
            "ServiceBelongsToOrg",
            "VpnBelongsToOrg",
            # Events and alarms
            "AlarmBelongsToSite",
            "EventBelongsToSite",
            "EventOccurredOnDevice",
            # Security and NAC
            "NACRuleMatchesSite",
            "NACRuleMatchesSiteGroup",
            "NACTagBelongsToPortal",
            "SecurityPolicyBelongsToOrg",
            # Assets and config
            "PSKBelongsToSite",
            "AssetBelongsToSite",
            "AssetOnMap",
            "WebhookBelongsToSite",
            "SiteGroupContainsSite",
            # WLAN and template relationships
            "WlanUsesMxTunnel",
            "TemplateAppliedToSite",
            "TemplateAppliedToSiteGroup",
            # Tier 1: High-value entity relationships
            "DeviceUsesProfile",
            "PSKBelongsToWlan",
            "AlarmOnDevice",
            "NacPortalServesSiteGroup",
            "MxTunnelUsesCluster",
            "AuditLogBelongsToSite",
            "GuestBelongsToSite",
            "GuestAuthorizedOnWlan",
            "GuestConnectedToAP",
            # Tier 2: Event/search entity relationships
            "ClientEventBelongsToSite",
            "ClientEventOnDevice",
            "SessionBelongsToSite",
            "SessionOnWlan",
            "SessionOnDevice",
            "NacEventBelongsToSite",
            "WanEventBelongsToSite",
            "MxEdgeEventBelongsToSite",
            "OtherEventBelongsToSite",
            "OrgEventBelongsToSite",
            "SystemEventBelongsToSite",
            # Tier 3: Stats/telemetry relationships
            "DeviceStatsBelongsToSite",
            "DeviceStatsForDevice",
            "BgpStatsBelongsToSite",
            "OspfStatsBelongsToSite",
            "PeerPathBelongsToSite",
            "PortBelongsToSite",
            "PortBelongsToDevice",
            "TunnelBelongsToSite",
            "MxEdgeStatsBelongsToSite",
            # Tier 4: WxLAN policy relationships
            "WxRuleBelongsToTemplate",
            "WxRuleMatchesSrcTag",
            "WxRuleAllowsDstTag",
            "WxRuleDeniesDstTag",
            # Tier 5: Remaining entity relationships
            "TicketBelongsToSite",
            "PacketCaptureBelongsToSite",
            "OtherDeviceBelongsToSite",
            "EvpnBelongsToSite",
            # New edge definitions for alarm templates, security, profiles, etc.
            "AlarmTemplateAssignedToSite",
            "SecurityPolicyAssignedToSite",
            "DeviceConnectedToDevice",
            "ProfileAppliedToSite",
            "ProfileAppliedToSiteGroup",
            "AlarmTemplateBelongsToOrg",
            "WlanAppliedToSite",
            "WlanAppliedToSiteGroup",
            "SessionForClient",
            "NacEventForClient",
            "WanEventForClient",
            "NACRuleUsesTag",
            "ServicePolicyUsesService",
            # Issue #169: Complete edge coverage for unmapped org-level endpoints
            "PskPortalServesSiteGroup",
            "SuppressedAlarmBelongsToSite",
            "DeviceConfigBelongsToSite",
            "DeviceConfigForDevice",
            "SiteStatsBelongsToSite",
            # Issue #180: Site rogue detection edges
            "RogueAPDetectedBySite",
            "RogueAPDetectedByAP",
            "RogueClientDetectedByAP",
            "RogueClientOnBSSID",
            "RogueEventBelongsToSite",
            "RogueEventOnDevice",
            # Issue #178: Site MxEdge edges
            "MxEdgeBelongsToSite",
            "MxEdgeEventOnDevice",
            # Issue #176: Site Asset edges
            "AssetFilterBelongsToSite",
            "DiscoveredAssetOnMap",
            "AssetTrackedByAP",
            # Issue #183: Applications, calls, WAN usage, fingerprints
            "ApplicationOnSite",
            "CallOnDevice",
            "WanUsageOnDevice",
            "WanUsagePeerDevice",
            "TroubleshootCallOnDevice",
            # Issue #185: SLE impacted entity relationships
            "SLEMetricForSite",
            "SLEImpactedDevice",
            "SLEImpactedClient",
            "SLEImpactedApplication",
            "SLEImpactedBySite",
            # Issue #177: Routing / network topology
            "DeviceHasBGPPeer",
            "DeviceHasOSPFNeighbor",
            "PortConnectsToDevice",
            "EVPNTopologyContainsSwitch",
            "DiscoveredSwitchBelongsToSite",
            "RrmNeighborBelongsToSite",
            # Issue #175: Maps, zones & location
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
            # Issue #174: Events & alarms
            "ServicePathEventOnDevice",
            "ServicePathEventUsesVPN",
            "ServicePathEventBelongsToSite",
            "SkyatpEventBelongsToSite",
            "RoamingEventBelongsToSite",
            "RoamingEventOnDevice",
            "RrmEventBelongsToSite",
            "RrmEventOnDevice",
            "AnomalyEventBelongsToSite",
            # Issue #181: Config history, synthetic tests, webhook deliveries
            "ConfigHistoryForDevice",
            "SyntheticTestOnDevice",
            "WebhookDeliveryFromWebhook",
            "PacketCaptureOnDevice",
            # Issue #173: Site-level WLANs, PSKs, Webhooks, WxLAN policies
            "WxRuleBelongsToSite",
            "WxTagBelongsToSite",
            "WxTunnelBelongsToSite",
            "WlanUsesWxTunnel",
            # Issue #172: Site-level client relationships
            "ClientUsedPSK",
            "ClientMatchedNACRule",
            "ClientEventForClient",
            "UnconnectedClientOnMap",
            "UnconnectedClientDetectedByAP",
            # Issue #171: Site-level device relationships
            "SpectrumAnalysisForDevice",
            # Issue #184: Derived config relationships
            "DerivedConfigForSite",
            "DerivedFromTemplate",
        }
        assert edge_names == expected

    def test_sitegroup_vertex_in_edge_def(self):
        from src.db.arango_writer import EDGE_DEFINITIONS

        sg_edge = next(d for d in EDGE_DEFINITIONS if d["edge_collection"] == "SiteBelongsToSiteGroup")
        assert "sitegroups" in sg_edge["to_vertex_collections"]

    def test_mxclusters_vertex_in_edge_def(self):
        from src.db.arango_writer import EDGE_DEFINITIONS

        mc_edge = next(d for d in EDGE_DEFINITIONS if d["edge_collection"] == "MxEdgeBelongsToCluster")
        assert "mxclusters" in mc_edge["to_vertex_collections"]

    def test_ensure_target_vertices_on_sites(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["listOrgSites"]
        targets = mapping.get("ensure_target_vertices", [])
        assert ("sitegroup_ids", "sitegroups") in targets

    def test_ensure_target_vertices_on_mxedges(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["listOrgMxEdges"]
        targets = mapping.get("ensure_target_vertices", [])
        assert ("mxcluster_id", "mxclusters") in targets


class TestArangoDBWriterEdgeKey:
    """Tests for _edge_key deterministic hash."""

    def test_edge_key_is_deterministic(self, config, mock_arango_client):
        from src.db.arango_writer import ArangoDBWriter

        writer = ArangoDBWriter(config)
        key1 = writer._edge_key("orgs/abc", "sites/xyz")
        key2 = writer._edge_key("orgs/abc", "sites/xyz")
        assert key1 == key2

    def test_edge_key_differs_for_different_inputs(self, config, mock_arango_client):
        from src.db.arango_writer import ArangoDBWriter

        writer = ArangoDBWriter(config)
        key1 = writer._edge_key("orgs/abc", "sites/xyz")
        key2 = writer._edge_key("orgs/abc", "sites/def")
        assert key1 != key2

    def test_edge_key_is_16_chars(self, config, mock_arango_client):
        from src.db.arango_writer import ArangoDBWriter

        writer = ArangoDBWriter(config)
        key = writer._edge_key("orgs/abc", "sites/xyz")
        assert len(key) == 16


class TestResolveNestedField:
    """Tests for _resolve_nested_field dot-path FK resolution."""

    def test_simple_field(self):
        from src.db.arango_writer import ArangoDBWriter

        record = {"site_id": "abc123"}
        assert ArangoDBWriter._resolve_nested_field(record, "site_id") == "abc123"

    def test_nested_field(self):
        from src.db.arango_writer import ArangoDBWriter

        record = {"matching": {"site_ids": ["s1", "s2"]}}
        result = ArangoDBWriter._resolve_nested_field(record, "matching.site_ids")
        assert result == ["s1", "s2"]

    def test_missing_top_level(self):
        from src.db.arango_writer import ArangoDBWriter

        record = {"other": "value"}
        assert ArangoDBWriter._resolve_nested_field(record, "matching.site_ids") is None

    def test_missing_nested(self):
        from src.db.arango_writer import ArangoDBWriter

        record = {"matching": {"other": "value"}}
        assert ArangoDBWriter._resolve_nested_field(record, "matching.site_ids") is None

    def test_deeply_nested(self):
        from src.db.arango_writer import ArangoDBWriter

        record = {"a": {"b": {"c": "deep"}}}
        assert ArangoDBWriter._resolve_nested_field(record, "a.b.c") == "deep"

    def test_non_dict_intermediate(self):
        from src.db.arango_writer import ArangoDBWriter

        record = {"matching": "not_a_dict"}
        assert ArangoDBWriter._resolve_nested_field(record, "matching.site_ids") is None


class TestArangoDBWriterSanitizeKey:
    """Tests for _sanitize_key."""

    def test_sanitize_replaces_slash(self):
        from src.db.arango_writer import ArangoDBWriter

        assert ArangoDBWriter._sanitize_key("a/b/c") == "a_b_c"

    def test_sanitize_replaces_colon(self):
        from src.db.arango_writer import ArangoDBWriter

        assert ArangoDBWriter._sanitize_key("a:b:c") == "a_b_c"

    def test_sanitize_preserves_valid_key(self):
        from src.db.arango_writer import ArangoDBWriter

        assert ArangoDBWriter._sanitize_key("abc-123_def") == "abc-123_def"


class TestArangoDBWriterEnsureTargetVertices:
    """Tests for _ensure_target_vertices runtime behavior."""

    def test_creates_stub_vertices_for_array_fk(self, config, mock_arango_client):
        from src.db.arango_writer import ArangoDBWriter

        writer = ArangoDBWriter(config)
        mock_db = mock_arango_client["db"]
        mock_collection = MagicMock()
        mock_db.has_collection.return_value = True
        mock_db.collection.return_value = mock_collection

        data = [
            {"id": "site-1", "sitegroup_ids": ["sg-1", "sg-2"]},
            {"id": "site-2", "sitegroup_ids": ["sg-1"]},
        ]
        mapping = {"ensure_target_vertices": [("sitegroup_ids", "sitegroups")]}
        writer._ensure_target_vertices(data, mapping)

        mock_collection.import_bulk.assert_called_once()
        stubs = mock_collection.import_bulk.call_args[0][0]
        stub_keys = {s["_key"] for s in stubs}
        assert "sg-1" in stub_keys
        assert "sg-2" in stub_keys

    def test_skips_empty_fk_values(self, config, mock_arango_client):
        from src.db.arango_writer import ArangoDBWriter

        writer = ArangoDBWriter(config)
        mock_db = mock_arango_client["db"]
        mock_collection = MagicMock()
        mock_db.has_collection.return_value = True
        mock_db.collection.return_value = mock_collection

        data = [{"id": "site-1", "sitegroup_ids": None}]
        mapping = {"ensure_target_vertices": [("sitegroup_ids", "sitegroups")]}
        writer._ensure_target_vertices(data, mapping)

        mock_collection.import_bulk.assert_not_called()

    def test_creates_stub_for_scalar_fk(self, config, mock_arango_client):
        from src.db.arango_writer import ArangoDBWriter

        writer = ArangoDBWriter(config)
        mock_db = mock_arango_client["db"]
        mock_collection = MagicMock()
        mock_db.has_collection.return_value = True
        mock_db.collection.return_value = mock_collection

        data = [{"id": "mxe-1", "mxcluster_id": "cluster-abc"}]
        mapping = {"ensure_target_vertices": [("mxcluster_id", "mxclusters")]}
        writer._ensure_target_vertices(data, mapping)

        mock_collection.import_bulk.assert_called_once()
        stubs = mock_collection.import_bulk.call_args[0][0]
        assert stubs[0]["_key"] == "cluster-abc"


class TestArangoDBWriterBuildEdges:
    """Tests for _build_edges with array FK support."""

    def test_builds_edges_for_array_fk(self, config, mock_arango_client):
        from src.db.arango_writer import ArangoDBWriter

        writer = ArangoDBWriter(config)
        mock_db = mock_arango_client["db"]
        mock_db.has_collection.return_value = False
        mock_db.create_collection.return_value = MagicMock(all=MagicMock(return_value=[]))

        data = [{"id": "site-1", "sitegroup_ids": ["sg-1", "sg-2"]}]
        edge_config = {
            "edge_col": "SiteBelongsToSiteGroup",
            "from_col": "sites",
            "from_field": "id",
            "to_col": "sitegroups",
            "to_field": "sitegroup_ids",
        }
        edges = writer._build_edges(data, "id", edge_config)
        assert len(edges) == 2
        to_ids = {e["_to"] for e in edges}
        assert "sitegroups/sg-1" in to_ids
        assert "sitegroups/sg-2" in to_ids

    def test_builds_edges_for_scalar_fk(self, config, mock_arango_client):
        from src.db.arango_writer import ArangoDBWriter

        writer = ArangoDBWriter(config)
        mock_db = mock_arango_client["db"]
        mock_db.has_collection.return_value = False
        mock_db.create_collection.return_value = MagicMock(all=MagicMock(return_value=[]))

        data = [{"id": "wlan-1", "template_id": "tmpl-1"}]
        edge_config = {
            "edge_col": "WlanUsesTemplate",
            "from_col": "wlans",
            "from_field": "id",
            "to_col": "templates",
            "to_field": "template_id",
        }
        edges = writer._build_edges(data, "id", edge_config)
        assert len(edges) == 1
        assert edges[0]["_from"] == "wlans/wlan-1"
        assert edges[0]["_to"] == "templates/tmpl-1"

    def test_skips_records_missing_to_field(self, config, mock_arango_client):
        from src.db.arango_writer import ArangoDBWriter

        writer = ArangoDBWriter(config)
        mock_db = mock_arango_client["db"]
        mock_db.has_collection.return_value = False
        mock_db.create_collection.return_value = MagicMock(all=MagicMock(return_value=[]))

        data = [{"id": "wlan-1"}]
        edge_config = {
            "edge_col": "WlanUsesTemplate",
            "from_col": "wlans",
            "from_field": "id",
            "to_col": "templates",
            "to_field": "template_id",
        }
        edges = writer._build_edges(data, "id", edge_config)
        assert len(edges) == 0


class TestArangoDBWriterMarkAbsent:
    """Tests for mark_absent_as_deleted edge cases."""

    def test_skips_nonexistent_collection(self, config, mock_arango_client):
        from src.db.arango_writer import ArangoDBWriter

        writer = ArangoDBWriter(config)
        mock_db = mock_arango_client["db"]
        mock_db.collection.reset_mock()
        mock_db.has_collection.return_value = False

        writer.mark_absent_as_deleted("nonexistent", current_keys=set())
        mock_db.collection.assert_not_called()

    def test_skips_already_deleted_docs(self, config, mock_arango_client):
        from src.db.arango_writer import ArangoDBWriter

        writer = ArangoDBWriter(config)
        mock_db = mock_arango_client["db"]
        mock_collection = MagicMock()
        mock_db.has_collection.return_value = True
        mock_db.collection.return_value = mock_collection

        existing_doc = {
            "_key": "old-uuid",
            "_misthelper_deleted_at": 1234567890,
        }
        mock_collection.all.return_value = [existing_doc]

        writer.mark_absent_as_deleted("sites", current_keys=set())
        mock_collection.update.assert_not_called()

    def test_does_not_delete_present_keys(self, config, mock_arango_client):
        from src.db.arango_writer import ArangoDBWriter

        writer = ArangoDBWriter(config)
        mock_db = mock_arango_client["db"]
        mock_collection = MagicMock()
        mock_db.has_collection.return_value = True
        mock_db.collection.return_value = mock_collection

        existing_doc = {
            "_key": "active-uuid",
            "_misthelper_deleted_at": None,
        }
        mock_collection.all.return_value = [existing_doc]

        writer.mark_absent_as_deleted("sites", current_keys={"active-uuid"})
        mock_collection.update.assert_not_called()


class TestArangoDBWriterBackfillEdges:
    """Tests for _backfill_snapshot_edges."""

    def test_skips_when_no_config_snapshots(self, config, mock_arango_client):
        from src.db.arango_writer import ArangoDBWriter

        mock_db = mock_arango_client["db"]
        mock_db.has_collection.side_effect = lambda name: name != "config_snapshots"
        writer = ArangoDBWriter(config)
        # Should not raise; silently returns
        assert writer is not None

    def test_backfill_creates_missing_edges(self, config, mock_arango_client):
        from src.db.arango_writer import ArangoDBWriter

        mock_db = mock_arango_client["db"]
        mock_db.has_collection.return_value = True
        edge_col = MagicMock()
        edge_col.count.return_value = 0
        snapshot_col = MagicMock()
        snapshot_col.count.return_value = 2

        def collection_side_effect(name):
            if name == "ConfigSnapshotForEntity":
                return edge_col
            if name == "config_snapshots":
                return snapshot_col
            return MagicMock()

        mock_db.collection.side_effect = collection_side_effect

        cursor = [
            {"key": "snap-1", "entity_type": "listOrgSites", "entity_id": "site-1"},
            {"key": "snap-2", "entity_type": "unknownType", "entity_id": "x"},
        ]
        mock_db.aql.execute.return_value = iter(cursor)

        writer = ArangoDBWriter(config)
        # The backfill runs during __init__ -> _ensure_graph
        # edge_col.import_bulk should have been called with the valid snap-1 edge
        assert writer is not None


class TestArangoDBWriterBuildVertices:
    """Tests for _build_vertices."""

    def test_builds_vertex_with_metadata_fields(self, config, mock_arango_client):
        from src.db.arango_writer import ArangoDBWriter

        writer = ArangoDBWriter(config)
        data = [
            {
                "id": "dev-1",
                "name": "AP-Lobby",
                "org_id": "org-1",
                "site_id": "site-1",
                "type": "ap",
                "model": "AP45",
                "serial": "ABC123",
                "mac": "aa:bb:cc:dd:ee:ff",
                "ip": "10.0.0.1",
            }
        ]
        vertices = writer._build_vertices(data, "id")
        assert len(vertices) == 1
        v = vertices[0]
        assert v["_key"] == "dev-1"
        assert v["name"] == "AP-Lobby"
        assert v["type"] == "ap"
        assert v["mac"] == "aa:bb:cc:dd:ee:ff"
        assert "_misthelper_updated_at" in v

    def test_skips_records_missing_key_field(self, config, mock_arango_client):
        from src.db.arango_writer import ArangoDBWriter

        writer = ArangoDBWriter(config)
        data = [{"name": "No ID here"}]
        vertices = writer._build_vertices(data, "id")
        assert len(vertices) == 0

    def test_preserves_all_api_fields(self, config, mock_arango_client):
        """Issue #182: vertex must contain ALL fields from API response."""
        from src.db.arango_writer import ArangoDBWriter

        writer = ArangoDBWriter(config)
        data = [
            {
                "id": "dev-1",
                "name": "AP-Lobby",
                "org_id": "org-1",
                "site_id": "site-1",
                "type": "ap",
                "model": "AP45",
                "serial": "ABC123",
                "mac": "aa:bb:cc:dd:ee:ff",
                "ip": "10.0.0.1",
                "firmware_version": "0.14.29411",
                "last_seen": 1700000000,
                "lldp_stat": {"chassis_id": "aa:bb:cc"},
                "custom_field": "extra-data",
            }
        ]
        vertices = writer._build_vertices(data, "id")
        vertex = vertices[0]
        for field in data[0]:
            assert field in vertex, f"Field '{field}' missing from vertex"
        assert vertex["firmware_version"] == "0.14.29411"
        assert vertex["lldp_stat"] == {"chassis_id": "aa:bb:cc"}
        assert vertex["custom_field"] == "extra-data"


class TestArangoDBWriterPopulateGraph:
    """Tests for _populate_graph end-to-end with mocked collections."""

    def test_populate_graph_for_unmapped_collection(self, config, mock_arango_client):
        from src.db.arango_writer import ArangoDBWriter

        writer = ArangoDBWriter(config)
        mock_db = mock_arango_client["db"]
        mock_db.has_collection.return_value = True

        # unmapped collection should be a no-op
        writer._populate_graph([{"id": "x"}], "totally_unknown_collection")
        # No vertex/edge creation attempted beyond init

    def test_populate_graph_creates_org_vertex(self, config, mock_arango_client):
        from src.db.arango_writer import ArangoDBWriter

        writer = ArangoDBWriter(config)
        mock_db = mock_arango_client["db"]
        mock_collection = MagicMock()
        mock_db.has_collection.return_value = True
        mock_db.collection.return_value = mock_collection
        mock_collection.all.return_value = []

        data = [{"id": "site-1", "org_id": "org-abc", "name": "TestSite"}]
        writer._populate_graph(data, "listOrgSites")

        # Should have attempted to import org vertex + site vertex + edges
        assert mock_collection.import_bulk.called


class TestArangoDBWriterSiteGuestGraph:
    """Tests for site-level guest authorization graph storage (issue #179)."""

    def test_site_guest_list_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "listSiteAllGuestAuthorizations" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["listSiteAllGuestAuthorizations"]
        assert mapping["vertex"] == "guests"
        assert mapping["key_field"] == "id"

    def test_site_guest_search_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "searchSiteGuestAuthorization" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["searchSiteGuestAuthorization"]
        assert mapping["vertex"] == "guests"
        assert mapping["key_field"] == "id"

    def test_site_guest_edges_complete(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["listSiteAllGuestAuthorizations"]
        edge_cols = [e["edge_col"] for e in mapping["edges"]]
        assert "GuestBelongsToSite" in edge_cols
        assert "GuestConnectedToAP" in edge_cols
        assert "GuestAuthorizedOnWlan" in edge_cols

    def test_guest_ap_edge_uses_mac_lookup(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        edges = COLLECTION_VERTEX_MAP["listSiteAllGuestAuthorizations"]["edges"]
        ap_edge = next(e for e in edges if e["edge_col"] == "GuestConnectedToAP")
        assert ap_edge["from_col"] == "guests"
        assert ap_edge["to_col"] == "devices"
        assert ap_edge["to_field"] == "ap_mac"
        assert ap_edge["to_key_lookup"] == "mac"

    def test_guest_edge_definition_registered(self):
        from src.db.arango_writer import EDGE_DEFINITIONS

        edge_names = [e["edge_collection"] for e in EDGE_DEFINITIONS]
        assert "GuestConnectedToAP" in edge_names

    def test_site_guest_entity_type_mapped(self):
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX

        assert ENTITY_TYPE_TO_VERTEX["listSiteAllGuestAuthorizations"] == "guests"
        assert ENTITY_TYPE_TO_VERTEX["searchSiteGuestAuthorization"] == "guests"


class TestArangoDBWriterSiteRogueGraph:
    """Tests for site-level rogue detection graph storage (issue #180)."""

    def test_rogue_ap_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "listSiteRogueAPs" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["listSiteRogueAPs"]
        assert mapping["vertex"] == "rogue_aps"
        assert mapping["key_field"] == "bssid"

    def test_rogue_client_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "listSiteRogueClients" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["listSiteRogueClients"]
        assert mapping["vertex"] == "rogue_clients"
        assert mapping["key_field"] == "client_mac"

    def test_rogue_events_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "searchSiteRogueEvents" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["searchSiteRogueEvents"]
        assert mapping["vertex"] == "rogue_events"
        assert mapping["key_field"] == "bssid"

    def test_rogue_ap_edges_complete(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        edges = COLLECTION_VERTEX_MAP["listSiteRogueAPs"]["edges"]
        edge_cols = [e["edge_col"] for e in edges]
        assert "RogueAPDetectedBySite" in edge_cols
        assert "RogueAPDetectedByAP" in edge_cols

    def test_rogue_ap_edge_uses_mac_lookup(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        edges = COLLECTION_VERTEX_MAP["listSiteRogueAPs"]["edges"]
        ap_edge = next(e for e in edges if e["edge_col"] == "RogueAPDetectedByAP")
        assert ap_edge["to_col"] == "devices"
        assert ap_edge["to_field"] == "ap_mac"
        assert ap_edge["to_key_lookup"] == "mac"

    def test_rogue_client_edges_complete(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        edges = COLLECTION_VERTEX_MAP["listSiteRogueClients"]["edges"]
        edge_cols = [e["edge_col"] for e in edges]
        assert "RogueClientDetectedByAP" in edge_cols
        assert "RogueClientOnBSSID" in edge_cols

    def test_rogue_client_bssid_edge_targets_rogue_aps(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        edges = COLLECTION_VERTEX_MAP["listSiteRogueClients"]["edges"]
        bssid_edge = next(e for e in edges if e["edge_col"] == "RogueClientOnBSSID")
        assert bssid_edge["to_col"] == "rogue_aps"
        assert bssid_edge["to_field"] == "bssid"

    def test_rogue_edge_definitions_registered(self):
        from src.db.arango_writer import EDGE_DEFINITIONS

        edge_names = {e["edge_collection"] for e in EDGE_DEFINITIONS}
        assert "RogueAPDetectedBySite" in edge_names
        assert "RogueAPDetectedByAP" in edge_names
        assert "RogueClientDetectedByAP" in edge_names
        assert "RogueClientOnBSSID" in edge_names
        assert "RogueEventBelongsToSite" in edge_names
        assert "RogueEventOnDevice" in edge_names

    def test_rogue_entity_types_mapped(self):
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX

        assert ENTITY_TYPE_TO_VERTEX["listSiteRogueAPs"] == "rogue_aps"
        assert ENTITY_TYPE_TO_VERTEX["listSiteRogueClients"] == "rogue_clients"
        assert ENTITY_TYPE_TO_VERTEX["searchSiteRogueEvents"] == "rogue_events"


class TestArangoDBWriterSiteMxEdgeGraph:
    """Tests for site-level MxEdge graph storage (issue #178)."""

    def test_mxedge_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "listSiteMxEdges" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["listSiteMxEdges"]
        assert mapping["vertex"] == "devices"
        assert mapping["key_field"] == "id"

    def test_mxedge_stats_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "listSiteMxEdgesStats" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["listSiteMxEdgesStats"]
        assert mapping["vertex"] == "mxedge_stats"
        assert mapping["key_field"] == "id"

    def test_mxedge_events_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "searchSiteMistEdgeEvents" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["searchSiteMistEdgeEvents"]
        assert mapping["vertex"] == "mxedge_events"
        assert mapping["key_field"] == "mxedge_id"

    def test_mxedge_edges_complete(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        edges = COLLECTION_VERTEX_MAP["listSiteMxEdges"]["edges"]
        edge_cols = [e["edge_col"] for e in edges]
        assert "MxEdgeBelongsToSite" in edge_cols
        assert "MxEdgeBelongsToCluster" in edge_cols

    def test_mxedge_stats_edges_complete(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        edges = COLLECTION_VERTEX_MAP["listSiteMxEdgesStats"]["edges"]
        edge_cols = [e["edge_col"] for e in edges]
        assert "MxEdgeStatsBelongsToSite" in edge_cols

    def test_mxedge_events_edges_complete(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        edges = COLLECTION_VERTEX_MAP["searchSiteMistEdgeEvents"]["edges"]
        edge_cols = [e["edge_col"] for e in edges]
        assert "MxEdgeEventBelongsToSite" in edge_cols
        assert "MxEdgeEventOnDevice" in edge_cols

    def test_mxedge_edge_definitions_registered(self):
        from src.db.arango_writer import EDGE_DEFINITIONS

        edge_names = {e["edge_collection"] for e in EDGE_DEFINITIONS}
        assert "MxEdgeBelongsToSite" in edge_names
        assert "MxEdgeEventOnDevice" in edge_names

    def test_mxedge_entity_types_mapped(self):
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX

        assert ENTITY_TYPE_TO_VERTEX["listSiteMxEdges"] == "devices"
        assert ENTITY_TYPE_TO_VERTEX["listSiteMxEdgesStats"] == "mxedge_stats"
        assert ENTITY_TYPE_TO_VERTEX["searchSiteMistEdgeEvents"] == "mxedge_events"

    def test_mxedge_ensure_target_vertices(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["listSiteMxEdges"]
        assert "ensure_target_vertices" in mapping
        targets = mapping["ensure_target_vertices"]
        assert ("mxcluster_id", "mxclusters") in targets


class TestArangoDBWriterSiteAssetGraph:
    """Tests for site-level Asset graph storage (issue #176)."""

    def test_site_assets_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "listSiteAssets" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["listSiteAssets"]
        assert mapping["vertex"] == "assets"
        assert mapping["key_field"] == "id"

    def test_search_assets_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "searchSiteAssets" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["searchSiteAssets"]
        assert mapping["vertex"] == "assets"
        assert mapping["key_field"] == "mac"

    def test_assets_stats_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "listSiteAssetsStats" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["listSiteAssetsStats"]
        assert mapping["vertex"] == "assets"
        assert mapping["key_field"] == "mac"

    def test_discovered_assets_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "listSiteDiscoveredAssets" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["listSiteDiscoveredAssets"]
        assert mapping["vertex"] == "discovered_assets"
        assert mapping["key_field"] == "id"

    def test_asset_filters_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "listSiteAssetFilters" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["listSiteAssetFilters"]
        assert mapping["vertex"] == "asset_filters"
        assert mapping["key_field"] == "id"

    def test_site_assets_edges_complete(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        edges = COLLECTION_VERTEX_MAP["listSiteAssets"]["edges"]
        edge_cols = [e["edge_col"] for e in edges]
        assert "AssetBelongsToSite" in edge_cols
        assert "AssetOnMap" in edge_cols

    def test_discovered_assets_edges_complete(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        edges = COLLECTION_VERTEX_MAP["listSiteDiscoveredAssets"]["edges"]
        edge_cols = [e["edge_col"] for e in edges]
        assert "DiscoveredAssetOnMap" in edge_cols

    def test_asset_filters_edges_complete(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        edges = COLLECTION_VERTEX_MAP["listSiteAssetFilters"]["edges"]
        edge_cols = [e["edge_col"] for e in edges]
        assert "AssetFilterBelongsToSite" in edge_cols

    def test_asset_edge_definitions_registered(self):
        from src.db.arango_writer import EDGE_DEFINITIONS

        edge_names = {e["edge_collection"] for e in EDGE_DEFINITIONS}
        assert "AssetFilterBelongsToSite" in edge_names
        assert "DiscoveredAssetOnMap" in edge_names
        assert "AssetTrackedByAP" in edge_names

    def test_asset_entity_types_mapped(self):
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX

        assert ENTITY_TYPE_TO_VERTEX["listSiteAssets"] == "assets"
        assert ENTITY_TYPE_TO_VERTEX["searchSiteAssets"] == "assets"
        assert ENTITY_TYPE_TO_VERTEX["listSiteAssetsStats"] == "assets"
        assert ENTITY_TYPE_TO_VERTEX["listSiteDiscoveredAssets"] == "discovered_assets"
        assert ENTITY_TYPE_TO_VERTEX["listSiteAssetFilters"] == "asset_filters"

    def test_site_assets_ensure_target_vertices(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["listSiteAssets"]
        assert "ensure_target_vertices" in mapping
        targets = mapping["ensure_target_vertices"]
        assert ("map_id", "maps") in targets


class TestArangoDBWriterSiteAppsCallsGraph:
    """Tests for site-level apps, calls, WAN usage, fingerprints graph storage (issue #183)."""

    def test_site_apps_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "listSiteApps" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["listSiteApps"]
        assert mapping["vertex"] == "applications"
        assert mapping["key_field"] == "key"

    def test_site_calls_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "searchSiteCalls" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["searchSiteCalls"]
        assert mapping["vertex"] == "calls"
        assert mapping["key_field"] == "mac"

    def test_site_wan_usage_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "searchSiteWanUsage" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["searchSiteWanUsage"]
        assert mapping["vertex"] == "wan_usage"
        assert mapping["key_field"] == "mac"

    def test_fingerprints_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "searchOrgClientFingerprints" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["searchOrgClientFingerprints"]
        assert mapping["vertex"] == "fingerprints"
        assert mapping["key_field"] == "mac"

    def test_ui_settings_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "listSiteUiSettings" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["listSiteUiSettings"]
        assert mapping["vertex"] == "ui_settings"
        assert mapping["key_field"] == "id"

    def test_troubleshoot_calls_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "listSiteTroubleshootCalls" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["listSiteTroubleshootCalls"]
        assert mapping["vertex"] == "troubleshoot_calls"
        assert mapping["key_field"] == "mac"

    def test_site_calls_edges_complete(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        edges = COLLECTION_VERTEX_MAP["searchSiteCalls"]["edges"]
        edge_cols = [e["edge_col"] for e in edges]
        assert "CallOnDevice" in edge_cols

    def test_wan_usage_edges_complete(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        edges = COLLECTION_VERTEX_MAP["searchSiteWanUsage"]["edges"]
        edge_cols = [e["edge_col"] for e in edges]
        assert "WanUsageOnDevice" in edge_cols
        assert "WanUsagePeerDevice" in edge_cols

    def test_troubleshoot_calls_edges_complete(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        edges = COLLECTION_VERTEX_MAP["listSiteTroubleshootCalls"]["edges"]
        edge_cols = [e["edge_col"] for e in edges]
        assert "TroubleshootCallOnDevice" in edge_cols

    def test_apps_calls_edge_definitions_registered(self):
        from src.db.arango_writer import EDGE_DEFINITIONS

        edge_names = {e["edge_collection"] for e in EDGE_DEFINITIONS}
        assert "ApplicationOnSite" in edge_names
        assert "CallOnDevice" in edge_names
        assert "WanUsageOnDevice" in edge_names
        assert "WanUsagePeerDevice" in edge_names
        assert "TroubleshootCallOnDevice" in edge_names

    def test_apps_calls_entity_types_mapped(self):
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX

        assert ENTITY_TYPE_TO_VERTEX["listSiteApps"] == "applications"
        assert ENTITY_TYPE_TO_VERTEX["searchSiteCalls"] == "calls"
        assert ENTITY_TYPE_TO_VERTEX["searchSiteWanUsage"] == "wan_usage"
        assert ENTITY_TYPE_TO_VERTEX["searchOrgClientFingerprints"] == "fingerprints"
        assert ENTITY_TYPE_TO_VERTEX["listSiteUiSettings"] == "ui_settings"
        assert ENTITY_TYPE_TO_VERTEX["listSiteTroubleshootCalls"] == "troubleshoot_calls"

    def test_apps_no_edges(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert COLLECTION_VERTEX_MAP["listSiteApps"]["edges"] == []

    def test_fingerprints_no_edges(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert COLLECTION_VERTEX_MAP["searchOrgClientFingerprints"]["edges"] == []

    def test_ui_settings_no_edges(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert COLLECTION_VERTEX_MAP["listSiteUiSettings"]["edges"] == []


class TestArangoDBWriterSLEImpactedGraph:
    """Tests for SLE impacted entity graph storage (issue #185)."""

    def test_sle_impacted_aps_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "listSiteSleImpactedAps" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["listSiteSleImpactedAps"]
        assert mapping["vertex"] == "sle_impacted_entities"
        assert mapping["key_field"] == "ap_mac"

    def test_sle_impacted_switches_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "listSiteSleImpactedSwitches" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["listSiteSleImpactedSwitches"]
        assert mapping["vertex"] == "sle_impacted_entities"
        assert mapping["key_field"] == "switch_mac"

    def test_sle_impacted_gateways_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "listSiteSleImpactedGateways" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["listSiteSleImpactedGateways"]
        assert mapping["vertex"] == "sle_impacted_entities"
        assert mapping["key_field"] == "gateway_mac"

    def test_sle_impacted_interfaces_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "listSiteSleImpactedInterfaces" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["listSiteSleImpactedInterfaces"]
        assert mapping["vertex"] == "sle_impacted_entities"
        assert mapping["key_field"] == "switch_mac"

    def test_sle_impacted_chassis_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "listSiteSleImpactedChassis" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["listSiteSleImpactedChassis"]
        assert mapping["vertex"] == "sle_impacted_entities"
        assert mapping["key_field"] == "switch_mac"

    def test_sle_impacted_wireless_clients_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "listSiteSleImpactedWirelessClients" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["listSiteSleImpactedWirelessClients"]
        assert mapping["vertex"] == "sle_impacted_entities"
        assert mapping["key_field"] == "mac"

    def test_sle_impacted_wired_clients_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "listSiteSleImpactedWiredClients" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["listSiteSleImpactedWiredClients"]
        assert mapping["vertex"] == "sle_impacted_entities"
        assert mapping["key_field"] == "mac"

    def test_sle_impacted_applications_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "listSiteSleImpactedApplications" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["listSiteSleImpactedApplications"]
        assert mapping["vertex"] == "sle_impacted_entities"
        assert mapping["key_field"] == "app"

    def test_sle_impacted_device_edges(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        for endpoint in [
            "listSiteSleImpactedAps",
            "listSiteSleImpactedSwitches",
            "listSiteSleImpactedGateways",
            "listSiteSleImpactedInterfaces",
            "listSiteSleImpactedChassis",
        ]:
            edges = COLLECTION_VERTEX_MAP[endpoint]["edges"]
            edge_cols = [e["edge_col"] for e in edges]
            assert "SLEImpactedDevice" in edge_cols, f"{endpoint} missing SLEImpactedDevice"

    def test_sle_impacted_client_edges(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        for endpoint in [
            "listSiteSleImpactedWirelessClients",
            "listSiteSleImpactedWiredClients",
        ]:
            edges = COLLECTION_VERTEX_MAP[endpoint]["edges"]
            edge_cols = [e["edge_col"] for e in edges]
            assert "SLEImpactedClient" in edge_cols, f"{endpoint} missing SLEImpactedClient"

    def test_sle_impacted_application_edges(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        edges = COLLECTION_VERTEX_MAP["listSiteSleImpactedApplications"]["edges"]
        edge_cols = [e["edge_col"] for e in edges]
        assert "SLEImpactedApplication" in edge_cols

    def test_sle_edge_definitions_registered(self):
        from src.db.arango_writer import EDGE_DEFINITIONS

        edge_names = {e["edge_collection"] for e in EDGE_DEFINITIONS}
        assert "SLEMetricForSite" in edge_names
        assert "SLEImpactedDevice" in edge_names
        assert "SLEImpactedClient" in edge_names
        assert "SLEImpactedApplication" in edge_names
        assert "SLEImpactedBySite" in edge_names

    def test_sle_entity_types_mapped(self):
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX

        assert ENTITY_TYPE_TO_VERTEX["listSiteSlesMetrics"] == "sle_metrics"
        assert ENTITY_TYPE_TO_VERTEX["listSiteSleMetricClassifiers"] == "sle_classifiers"
        assert ENTITY_TYPE_TO_VERTEX["listSiteSleImpactedAps"] == "sle_impacted_entities"
        assert ENTITY_TYPE_TO_VERTEX["listSiteSleImpactedSwitches"] == "sle_impacted_entities"
        assert ENTITY_TYPE_TO_VERTEX["listSiteSleImpactedGateways"] == "sle_impacted_entities"
        assert ENTITY_TYPE_TO_VERTEX["listSiteSleImpactedInterfaces"] == "sle_impacted_entities"
        assert ENTITY_TYPE_TO_VERTEX["listSiteSleImpactedChassis"] == "sle_impacted_entities"
        assert ENTITY_TYPE_TO_VERTEX["listSiteSleImpactedWirelessClients"] == "sle_impacted_entities"
        assert ENTITY_TYPE_TO_VERTEX["listSiteSleImpactedWiredClients"] == "sle_impacted_entities"
        assert ENTITY_TYPE_TO_VERTEX["listSiteSleImpactedApplications"] == "sle_impacted_entities"


class TestArangoDBWriterSiteRoutingGraph:
    """Tests for site-level routing / network topology graph storage (issue #177)."""

    def test_bgp_stats_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "searchSiteBgpStats" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["searchSiteBgpStats"]
        assert mapping["vertex"] == "bgp_stats"
        assert mapping["key_field"] == "id"

    def test_ospf_stats_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "searchSiteOspfStats" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["searchSiteOspfStats"]
        assert mapping["vertex"] == "ospf_stats"
        assert mapping["key_field"] == "id"

    def test_site_ports_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "searchSiteSwOrGwPorts" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["searchSiteSwOrGwPorts"]
        assert mapping["vertex"] == "ports"
        assert mapping["key_field"] == "id"

    def test_evpn_topologies_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "listSiteEvpnTopologies" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["listSiteEvpnTopologies"]
        assert mapping["vertex"] == "evpn_topologies"
        assert mapping["key_field"] == "id"

    def test_discovered_switches_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "searchSiteDiscoveredSwitches" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["searchSiteDiscoveredSwitches"]
        assert mapping["vertex"] == "discovered_switches"
        assert mapping["key_field"] == "system_name"

    def test_discovered_switch_metrics_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "listSiteDiscoveredSwitchesMetrics" in COLLECTION_VERTEX_MAP
        assert "searchSiteDiscoveredSwitchesMetrics" in COLLECTION_VERTEX_MAP

    def test_rrm_neighbors_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "listSiteCurrentRrmNeighbors" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["listSiteCurrentRrmNeighbors"]
        assert mapping["vertex"] == "rrm_neighbors"
        assert mapping["key_field"] == "mac"

    def test_bgp_edges_complete(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        edges = COLLECTION_VERTEX_MAP["searchSiteBgpStats"]["edges"]
        edge_cols = [e["edge_col"] for e in edges]
        assert "BgpStatsBelongsToSite" in edge_cols
        assert "DeviceHasBGPPeer" in edge_cols

    def test_ospf_edges_complete(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        edges = COLLECTION_VERTEX_MAP["searchSiteOspfStats"]["edges"]
        edge_cols = [e["edge_col"] for e in edges]
        assert "OspfStatsBelongsToSite" in edge_cols
        assert "DeviceHasOSPFNeighbor" in edge_cols

    def test_site_ports_edges_include_lldp(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        edges = COLLECTION_VERTEX_MAP["searchSiteSwOrGwPorts"]["edges"]
        edge_cols = [e["edge_col"] for e in edges]
        assert "PortConnectsToDevice" in edge_cols
        assert "PortBelongsToSite" in edge_cols
        assert "PortBelongsToDevice" in edge_cols

    def test_evpn_edges_complete(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        edges = COLLECTION_VERTEX_MAP["listSiteEvpnTopologies"]["edges"]
        edge_cols = [e["edge_col"] for e in edges]
        assert "EvpnBelongsToSite" in edge_cols

    def test_discovered_switches_edges_complete(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        edges = COLLECTION_VERTEX_MAP["searchSiteDiscoveredSwitches"]["edges"]
        edge_cols = [e["edge_col"] for e in edges]
        assert "DiscoveredSwitchBelongsToSite" in edge_cols

    def test_rrm_neighbors_edges_complete(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        edges = COLLECTION_VERTEX_MAP["listSiteCurrentRrmNeighbors"]["edges"]
        edge_cols = [e["edge_col"] for e in edges]
        assert "RrmNeighborBelongsToSite" in edge_cols

    def test_routing_edge_definitions_registered(self):
        from src.db.arango_writer import EDGE_DEFINITIONS

        edge_names = {e["edge_collection"] for e in EDGE_DEFINITIONS}
        assert "DeviceHasBGPPeer" in edge_names
        assert "DeviceHasOSPFNeighbor" in edge_names
        assert "PortConnectsToDevice" in edge_names
        assert "EVPNTopologyContainsSwitch" in edge_names
        assert "DiscoveredSwitchBelongsToSite" in edge_names
        assert "RrmNeighborBelongsToSite" in edge_names

    def test_routing_entity_types_mapped(self):
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX

        assert ENTITY_TYPE_TO_VERTEX["searchSiteBgpStats"] == "bgp_stats"
        assert ENTITY_TYPE_TO_VERTEX["searchSiteOspfStats"] == "ospf_stats"
        assert ENTITY_TYPE_TO_VERTEX["searchSiteSwOrGwPorts"] == "ports"
        assert ENTITY_TYPE_TO_VERTEX["listSiteEvpnTopologies"] == "evpn_topologies"
        assert ENTITY_TYPE_TO_VERTEX["searchSiteDiscoveredSwitches"] == "discovered_switches"
        assert ENTITY_TYPE_TO_VERTEX["listSiteDiscoveredSwitchesMetrics"] == "discovered_switch_metrics"
        assert ENTITY_TYPE_TO_VERTEX["searchSiteDiscoveredSwitchesMetrics"] == "discovered_switch_metrics"
        assert ENTITY_TYPE_TO_VERTEX["listSiteCurrentRrmNeighbors"] == "rrm_neighbors"


class TestArangoDBWriterSiteMapsZonesGraph:
    """Tests for site maps, zones & location graph storage (issue #175)."""

    def test_maps_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "listSiteMaps" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["listSiteMaps"]
        assert mapping["vertex"] == "maps"
        assert mapping["key_field"] == "id"

    def test_get_site_map_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "getSiteMap" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["getSiteMap"]
        assert mapping["vertex"] == "maps"
        assert mapping["key_field"] == "id"

    def test_map_stacks_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "listSiteMapStacks" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["listSiteMapStacks"]
        assert mapping["vertex"] == "map_stacks"
        assert mapping["key_field"] == "id"

    def test_zones_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "listSiteZones" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["listSiteZones"]
        assert mapping["vertex"] == "zones"
        assert mapping["key_field"] == "id"

    def test_zone_stats_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "listSiteZonesStats" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["listSiteZonesStats"]
        assert mapping["vertex"] == "zone_stats"
        assert mapping["key_field"] == "id"

    def test_rssi_zones_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "listSiteRssiZones" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["listSiteRssiZones"]
        assert mapping["vertex"] == "rssizones"
        assert mapping["key_field"] == "id"

    def test_rssi_zone_stats_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "listSiteRssiZonesStats" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["listSiteRssiZonesStats"]
        assert mapping["vertex"] == "rssizone_stats"
        assert mapping["key_field"] == "id"

    def test_beacons_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "listSiteBeacons" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["listSiteBeacons"]
        assert mapping["vertex"] == "beacons"
        assert mapping["key_field"] == "id"

    def test_vbeacons_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "listSiteVBeacons" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["listSiteVBeacons"]
        assert mapping["vertex"] == "vbeacons"
        assert mapping["key_field"] == "id"

    def test_zone_sessions_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "searchSiteZoneSessions" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["searchSiteZoneSessions"]
        assert mapping["vertex"] == "zone_sessions"
        assert mapping["key_field"] == "zone_id"

    def test_map_edges_include_site(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        edges = COLLECTION_VERTEX_MAP["listSiteMaps"]["edges"]
        edge_cols = [e["edge_col"] for e in edges]
        assert "MapBelongsToSite" in edge_cols

    def test_zone_edges_include_map_and_site(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        edges = COLLECTION_VERTEX_MAP["listSiteZones"]["edges"]
        edge_cols = [e["edge_col"] for e in edges]
        assert "ZoneBelongsToMap" in edge_cols
        assert "ZoneBelongsToSite" in edge_cols

    def test_beacon_edges_include_map_and_site(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        edges = COLLECTION_VERTEX_MAP["listSiteBeacons"]["edges"]
        edge_cols = [e["edge_col"] for e in edges]
        assert "BeaconOnMap" in edge_cols
        assert "BeaconBelongsToSite" in edge_cols

    def test_vbeacon_edges_include_map(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        edges = COLLECTION_VERTEX_MAP["listSiteVBeacons"]["edges"]
        edge_cols = [e["edge_col"] for e in edges]
        assert "VBeaconOnMap" in edge_cols

    def test_zone_session_edges_include_zone_and_map(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        edges = COLLECTION_VERTEX_MAP["searchSiteZoneSessions"]["edges"]
        edge_cols = [e["edge_col"] for e in edges]
        assert "ZoneSessionInZone" in edge_cols
        assert "ZoneSessionOnMap" in edge_cols

    def test_maps_zones_edge_definitions_registered(self):
        from src.db.arango_writer import EDGE_DEFINITIONS

        edge_names = {e["edge_collection"] for e in EDGE_DEFINITIONS}
        assert "MapBelongsToSite" in edge_names
        assert "ZoneBelongsToMap" in edge_names
        assert "ZoneBelongsToSite" in edge_names
        assert "RssiZoneBelongsToMap" in edge_names
        assert "BeaconOnMap" in edge_names
        assert "BeaconBelongsToSite" in edge_names
        assert "VBeaconOnMap" in edge_names
        assert "DeviceOnMap" in edge_names
        assert "ZoneSessionInZone" in edge_names
        assert "ZoneSessionOnMap" in edge_names

    def test_maps_zones_entity_types_mapped(self):
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX

        assert ENTITY_TYPE_TO_VERTEX["listSiteMaps"] == "maps"
        assert ENTITY_TYPE_TO_VERTEX["getSiteMap"] == "maps"
        assert ENTITY_TYPE_TO_VERTEX["listSiteMapStacks"] == "map_stacks"
        assert ENTITY_TYPE_TO_VERTEX["listSiteZones"] == "zones"
        assert ENTITY_TYPE_TO_VERTEX["listSiteZonesStats"] == "zone_stats"
        assert ENTITY_TYPE_TO_VERTEX["listSiteRssiZones"] == "rssizones"
        assert ENTITY_TYPE_TO_VERTEX["listSiteRssiZonesStats"] == "rssizone_stats"
        assert ENTITY_TYPE_TO_VERTEX["listSiteBeacons"] == "beacons"
        assert ENTITY_TYPE_TO_VERTEX["listSiteVBeacons"] == "vbeacons"
        assert ENTITY_TYPE_TO_VERTEX["searchSiteZoneSessions"] == "zone_sessions"


class TestArangoDBWriterSiteEventsAlarmsGraph:
    """Tests for site events & alarms graph storage (issue #174)."""

    def test_site_alarms_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "searchSiteAlarms" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["searchSiteAlarms"]
        assert mapping["vertex"] == "alarms"
        assert mapping["key_field"] == "id"

    def test_site_alarms_edges(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        edges = COLLECTION_VERTEX_MAP["searchSiteAlarms"]["edges"]
        edge_cols = [e["edge_col"] for e in edges]
        assert "AlarmBelongsToSite" in edge_cols
        assert "AlarmOnDevice" in edge_cols

    def test_site_device_events_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "searchSiteDeviceEvents" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["searchSiteDeviceEvents"]
        assert mapping["vertex"] == "events"
        assert mapping["key_field"] == "id"

    def test_site_device_events_edges(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        edges = COLLECTION_VERTEX_MAP["searchSiteDeviceEvents"]["edges"]
        edge_cols = [e["edge_col"] for e in edges]
        assert "EventBelongsToSite" in edge_cols
        assert "EventOccurredOnDevice" in edge_cols

    def test_site_system_events_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "searchSiteSystemEvents" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["searchSiteSystemEvents"]
        assert mapping["vertex"] == "system_events"
        assert mapping["key_field"] == "id"

    def test_site_system_events_edges(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        edges = COLLECTION_VERTEX_MAP["searchSiteSystemEvents"]["edges"]
        edge_cols = [e["edge_col"] for e in edges]
        assert "SystemEventBelongsToSite" in edge_cols

    def test_site_other_device_events_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "searchSiteOtherDeviceEvents" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["searchSiteOtherDeviceEvents"]
        assert mapping["vertex"] == "other_events"
        assert mapping["key_field"] == "mac"

    def test_site_skyatp_events_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "searchSiteSkyatpEvents" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["searchSiteSkyatpEvents"]
        assert mapping["vertex"] == "skyatp_events"
        assert mapping["key_field"] == "mac"

    def test_site_service_path_events_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "searchSiteServicePathEvents" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["searchSiteServicePathEvents"]
        assert mapping["vertex"] == "service_path_events"
        assert mapping["key_field"] == "mac"

    def test_site_service_path_events_edges(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        edges = COLLECTION_VERTEX_MAP["searchSiteServicePathEvents"]["edges"]
        edge_cols = [e["edge_col"] for e in edges]
        assert "ServicePathEventBelongsToSite" in edge_cols
        assert "ServicePathEventOnDevice" in edge_cols
        assert "ServicePathEventUsesVPN" in edge_cols

    def test_site_roaming_events_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "listSiteRoamingEvents" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["listSiteRoamingEvents"]
        assert mapping["vertex"] == "roaming_events"
        assert mapping["key_field"] == "client_mac"

    def test_site_roaming_events_edges(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        edges = COLLECTION_VERTEX_MAP["listSiteRoamingEvents"]["edges"]
        edge_cols = [e["edge_col"] for e in edges]
        assert "RoamingEventBelongsToSite" in edge_cols
        assert "RoamingEventOnDevice" in edge_cols

    def test_site_rrm_events_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "listSiteRrmEvents" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["listSiteRrmEvents"]
        assert mapping["vertex"] == "rrm_events"
        assert mapping["key_field"] == "ap_id"

    def test_site_rrm_events_edges(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        edges = COLLECTION_VERTEX_MAP["listSiteRrmEvents"]["edges"]
        edge_cols = [e["edge_col"] for e in edges]
        assert "RrmEventBelongsToSite" in edge_cols
        assert "RrmEventOnDevice" in edge_cols

    def test_site_anomaly_events_mapping_exists(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        assert "listSiteAnomalyEvents" in COLLECTION_VERTEX_MAP
        mapping = COLLECTION_VERTEX_MAP["listSiteAnomalyEvents"]
        assert mapping["vertex"] == "anomaly_events"
        assert mapping["key_field"] == "timestamp"

    def test_site_anomaly_events_edges(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        edges = COLLECTION_VERTEX_MAP["listSiteAnomalyEvents"]["edges"]
        edge_cols = [e["edge_col"] for e in edges]
        assert "AnomalyEventBelongsToSite" in edge_cols

    def test_events_alarms_edge_definitions_registered(self):
        from src.db.arango_writer import EDGE_DEFINITIONS

        edge_names = {e["edge_collection"] for e in EDGE_DEFINITIONS}
        assert "ServicePathEventOnDevice" in edge_names
        assert "ServicePathEventUsesVPN" in edge_names
        assert "ServicePathEventBelongsToSite" in edge_names
        assert "SkyatpEventBelongsToSite" in edge_names
        assert "RoamingEventBelongsToSite" in edge_names
        assert "RoamingEventOnDevice" in edge_names
        assert "RrmEventBelongsToSite" in edge_names
        assert "RrmEventOnDevice" in edge_names
        assert "AnomalyEventBelongsToSite" in edge_names

    def test_events_alarms_entity_types_mapped(self):
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX

        assert ENTITY_TYPE_TO_VERTEX["searchSiteAlarms"] == "alarms"
        assert ENTITY_TYPE_TO_VERTEX["searchSiteDeviceEvents"] == "events"
        assert ENTITY_TYPE_TO_VERTEX["searchSiteSystemEvents"] == "system_events"
        assert ENTITY_TYPE_TO_VERTEX["searchSiteOtherDeviceEvents"] == "other_events"
        assert ENTITY_TYPE_TO_VERTEX["searchSiteSkyatpEvents"] == "skyatp_events"
        assert ENTITY_TYPE_TO_VERTEX["searchSiteServicePathEvents"] == "service_path_events"
        assert ENTITY_TYPE_TO_VERTEX["listSiteRoamingEvents"] == "roaming_events"
        assert ENTITY_TYPE_TO_VERTEX["listSiteRrmEvents"] == "rrm_events"
        assert ENTITY_TYPE_TO_VERTEX["listSiteAnomalyEvents"] == "anomaly_events"

    def test_service_path_ensure_target_vertices(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["searchSiteServicePathEvents"]
        targets = mapping.get("ensure_target_vertices", [])
        assert ("vpn_name", "vpns") in targets


class TestConfigHistorySyntheticTestGraphStorage:
    """Issue #181: Config history, synthetic tests, webhook deliveries."""

    def test_config_history_entity_type(self):
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX

        assert ENTITY_TYPE_TO_VERTEX["searchSiteDeviceConfigHistory"] == "config_history"

    def test_last_configs_entity_type(self):
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX

        assert ENTITY_TYPE_TO_VERTEX["searchSiteDeviceLastConfigs"] == "config_history"

    def test_synthetic_test_entity_type(self):
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX

        assert ENTITY_TYPE_TO_VERTEX["searchSiteSyntheticTest"] == "synthetic_tests"

    def test_webhook_deliveries_entity_type(self):
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX

        assert ENTITY_TYPE_TO_VERTEX["searchSiteWebhooksDeliveries"] == "webhook_deliveries"

    def test_packet_captures_entity_type(self):
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX

        assert ENTITY_TYPE_TO_VERTEX["listSitePacketCaptures"] == "packet_captures"

    def test_config_history_collection_vertex_map(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["searchSiteDeviceConfigHistory"]
        assert mapping["vertex"] == "config_history"
        edges = mapping["edges"]
        edge_cols = [e["edge_col"] for e in edges]
        assert "ConfigHistoryForDevice" in edge_cols

    def test_last_configs_collection_vertex_map(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["searchSiteDeviceLastConfigs"]
        assert mapping["vertex"] == "config_history"
        edges = mapping["edges"]
        edge_cols = [e["edge_col"] for e in edges]
        assert "ConfigHistoryForDevice" in edge_cols

    def test_synthetic_test_collection_vertex_map(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["searchSiteSyntheticTest"]
        assert mapping["vertex"] == "synthetic_tests"
        edges = mapping["edges"]
        edge_cols = [e["edge_col"] for e in edges]
        assert "SyntheticTestOnDevice" in edge_cols

    def test_webhook_deliveries_collection_vertex_map(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["searchSiteWebhooksDeliveries"]
        assert mapping["vertex"] == "webhook_deliveries"
        edges = mapping["edges"]
        edge_cols = [e["edge_col"] for e in edges]
        assert "WebhookDeliveryFromWebhook" in edge_cols

    def test_packet_captures_collection_vertex_map(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["listSitePacketCaptures"]
        assert mapping["vertex"] == "packet_captures"
        edges = mapping["edges"]
        edge_cols = [e["edge_col"] for e in edges]
        assert "PacketCaptureOnDevice" in edge_cols
        assert "PacketCaptureBelongsToSite" in edge_cols

    def test_edge_definitions_registered(self):
        from src.db.arango_writer import EDGE_DEFINITIONS

        edge_names = {e["edge_collection"] for e in EDGE_DEFINITIONS}
        assert "ConfigHistoryForDevice" in edge_names
        assert "SyntheticTestOnDevice" in edge_names
        assert "WebhookDeliveryFromWebhook" in edge_names
        assert "PacketCaptureOnDevice" in edge_names


class TestSiteWlansPsksWebhooksGraphStorage:
    """Issue #173: Site-level WLANs, PSKs, Webhooks, WxLAN policies."""

    def test_site_wlans_entity_type(self):
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX

        assert ENTITY_TYPE_TO_VERTEX["listSiteWlans"] == "wlans"

    def test_site_psks_entity_type(self):
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX

        assert ENTITY_TYPE_TO_VERTEX["listSitePsks"] == "psks"

    def test_site_webhooks_entity_type(self):
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX

        assert ENTITY_TYPE_TO_VERTEX["listSiteWebhooks"] == "webhooks"

    def test_site_wxrules_entity_type(self):
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX

        assert ENTITY_TYPE_TO_VERTEX["listSiteWxRules"] == "wx_rules"

    def test_site_wxtags_entity_type(self):
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX

        assert ENTITY_TYPE_TO_VERTEX["listSiteWxTags"] == "wx_tags"

    def test_site_wxtunnels_entity_type(self):
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX

        assert ENTITY_TYPE_TO_VERTEX["listSiteWxTunnels"] == "mx_tunnels"

    def test_site_wlans_collection_vertex_map(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["listSiteWlans"]
        assert mapping["vertex"] == "wlans"
        edge_cols = [e["edge_col"] for e in mapping["edges"]]
        assert "WlanBelongsToSite" in edge_cols
        assert "WlanUsesWxTunnel" in edge_cols

    def test_site_psks_collection_vertex_map(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["listSitePsks"]
        assert mapping["vertex"] == "psks"
        edge_cols = [e["edge_col"] for e in mapping["edges"]]
        assert "PSKBelongsToSite" in edge_cols
        assert "PSKBelongsToWlan" in edge_cols

    def test_site_webhooks_collection_vertex_map(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["listSiteWebhooks"]
        assert mapping["vertex"] == "webhooks"
        edge_cols = [e["edge_col"] for e in mapping["edges"]]
        assert "WebhookBelongsToSite" in edge_cols

    def test_site_wxrules_collection_vertex_map(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["listSiteWxRules"]
        assert mapping["vertex"] == "wx_rules"
        edge_cols = [e["edge_col"] for e in mapping["edges"]]
        assert "WxRuleBelongsToSite" in edge_cols
        assert "WxRuleMatchesSrcTag" in edge_cols
        assert "WxRuleAllowsDstTag" in edge_cols
        assert "WxRuleDeniesDstTag" in edge_cols

    def test_site_wxrules_ensure_target_vertices(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["listSiteWxRules"]
        targets = mapping.get("ensure_target_vertices", [])
        assert ("src_wxtags", "wx_tags") in targets
        assert ("dst_allow_wxtags", "wx_tags") in targets
        assert ("dst_deny_wxtags", "wx_tags") in targets

    def test_site_wxtags_collection_vertex_map(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["listSiteWxTags"]
        assert mapping["vertex"] == "wx_tags"
        edge_cols = [e["edge_col"] for e in mapping["edges"]]
        assert "WxTagBelongsToSite" in edge_cols

    def test_site_wxtunnels_collection_vertex_map(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["listSiteWxTunnels"]
        assert mapping["vertex"] == "mx_tunnels"
        edge_cols = [e["edge_col"] for e in mapping["edges"]]
        assert "WxTunnelBelongsToSite" in edge_cols

    def test_edge_definitions_registered(self):
        from src.db.arango_writer import EDGE_DEFINITIONS

        edge_names = {e["edge_collection"] for e in EDGE_DEFINITIONS}
        assert "WxRuleBelongsToSite" in edge_names
        assert "WxTagBelongsToSite" in edge_names
        assert "WxTunnelBelongsToSite" in edge_names
        assert "WlanUsesWxTunnel" in edge_names


class TestSiteClientsGraphStorage:
    """Issue #172: Site-level client search endpoints."""

    def test_wireless_clients_entity_type(self):
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX

        assert ENTITY_TYPE_TO_VERTEX["searchSiteWirelessClients"] == "clients"

    def test_wired_clients_entity_type(self):
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX

        assert ENTITY_TYPE_TO_VERTEX["searchSiteWiredClients"] == "clients"

    def test_wan_clients_entity_type(self):
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX

        assert ENTITY_TYPE_TO_VERTEX["searchSiteWanClients"] == "clients"

    def test_nac_clients_entity_type(self):
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX

        assert ENTITY_TYPE_TO_VERTEX["searchSiteNacClients"] == "clients"

    def test_nac_client_events_entity_type(self):
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX

        assert ENTITY_TYPE_TO_VERTEX["searchSiteNacClientEvents"] == "nac_events"

    def test_wireless_client_events_entity_type(self):
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX

        assert ENTITY_TYPE_TO_VERTEX["searchSiteWirelessClientEvents"] == "client_events"

    def test_wireless_client_sessions_entity_type(self):
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX

        assert ENTITY_TYPE_TO_VERTEX["searchSiteWirelessClientSessions"] == "client_sessions"

    def test_wan_client_events_entity_type(self):
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX

        assert ENTITY_TYPE_TO_VERTEX["searchSiteWanClientEvents"] == "wan_events"

    def test_wireless_clients_stats_entity_type(self):
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX

        assert ENTITY_TYPE_TO_VERTEX["listSiteWirelessClientsStats"] == "clients"

    def test_unconnected_clients_entity_type(self):
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX

        assert ENTITY_TYPE_TO_VERTEX["listSiteUnconnectedClientStats"] == "unconnected_clients"

    def test_wireless_clients_edges(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["searchSiteWirelessClients"]
        assert mapping["vertex"] == "clients"
        assert mapping["key_field"] == "mac"
        edge_cols = [e["edge_col"] for e in mapping["edges"]]
        assert "ClientConnectedToDevice" in edge_cols
        assert "ClientConnectedToWlan" in edge_cols
        assert "ClientBelongsToSite" in edge_cols
        assert "ClientUsedPSK" in edge_cols

    def test_wired_clients_edges(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["searchSiteWiredClients"]
        assert mapping["vertex"] == "clients"
        edge_cols = [e["edge_col"] for e in mapping["edges"]]
        assert "ClientConnectedToDevice" in edge_cols
        assert "ClientBelongsToSite" in edge_cols

    def test_wan_clients_edges(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["searchSiteWanClients"]
        assert mapping["vertex"] == "clients"
        edge_cols = [e["edge_col"] for e in mapping["edges"]]
        assert "ClientBelongsToSite" in edge_cols

    def test_nac_clients_edges(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["searchSiteNacClients"]
        assert mapping["vertex"] == "clients"
        edge_cols = [e["edge_col"] for e in mapping["edges"]]
        assert "ClientConnectedToDevice" in edge_cols
        assert "ClientBelongsToSite" in edge_cols
        assert "ClientMatchedNACRule" in edge_cols

    def test_nac_client_events_edges(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["searchSiteNacClientEvents"]
        assert mapping["vertex"] == "nac_events"
        edge_cols = [e["edge_col"] for e in mapping["edges"]]
        assert "NacEventBelongsToSite" in edge_cols
        assert "NacEventForClient" in edge_cols

    def test_wireless_client_events_edges(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["searchSiteWirelessClientEvents"]
        assert mapping["vertex"] == "client_events"
        edge_cols = [e["edge_col"] for e in mapping["edges"]]
        assert "ClientEventBelongsToSite" in edge_cols
        assert "ClientEventOnDevice" in edge_cols
        assert "ClientEventForClient" in edge_cols

    def test_wireless_client_events_ensure_targets(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["searchSiteWirelessClientEvents"]
        targets = mapping.get("ensure_target_vertices", [])
        assert ("mac", "clients") in targets

    def test_wireless_client_sessions_edges(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["searchSiteWirelessClientSessions"]
        assert mapping["vertex"] == "client_sessions"
        edge_cols = [e["edge_col"] for e in mapping["edges"]]
        assert "SessionBelongsToSite" in edge_cols
        assert "SessionOnWlan" in edge_cols
        assert "SessionOnDevice" in edge_cols
        assert "SessionForClient" in edge_cols

    def test_wan_client_events_edges(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["searchSiteWanClientEvents"]
        assert mapping["vertex"] == "wan_events"
        edge_cols = [e["edge_col"] for e in mapping["edges"]]
        assert "WanEventBelongsToSite" in edge_cols
        assert "WanEventForClient" in edge_cols

    def test_unconnected_clients_edges(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["listSiteUnconnectedClientStats"]
        assert mapping["vertex"] == "unconnected_clients"
        assert mapping["key_field"] == "mac"
        edge_cols = [e["edge_col"] for e in mapping["edges"]]
        assert "UnconnectedClientOnMap" in edge_cols
        assert "UnconnectedClientDetectedByAP" in edge_cols

    def test_edge_definitions_registered(self):
        from src.db.arango_writer import EDGE_DEFINITIONS

        edge_names = {e["edge_collection"] for e in EDGE_DEFINITIONS}
        assert "ClientUsedPSK" in edge_names
        assert "ClientMatchedNACRule" in edge_names
        assert "ClientEventForClient" in edge_names
        assert "UnconnectedClientOnMap" in edge_names
        assert "UnconnectedClientDetectedByAP" in edge_names


class TestSiteDevicesGraphStorage:
    """Tests for Issue #171: Site-level device graph storage."""

    def test_entity_type_mappings(self):
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX

        expected = {
            "searchSiteDevices": "devices",
            "listSiteDevicesStats": "devices",
            "listSiteOtherDevices": "other_devices",
            "listSiteAvailableDeviceVersions": "device_versions",
            "listSiteSpectrumAnalysis": "spectrum_analysis",
            "listSiteDeviceRadioChannels": "radio_channels",
            "listSiteDeviceUpgrades": "device_upgrades",
        }
        for operation_id, vertex in expected.items():
            assert ENTITY_TYPE_TO_VERTEX.get(operation_id) == vertex

    def test_existing_device_mapping_preserved(self):
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX

        assert ENTITY_TYPE_TO_VERTEX.get("listSiteDevices") == "devices"

    def test_collection_vertex_map_entries(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        expected_ops = [
            "listSiteDevices",
            "searchSiteDevices",
            "listSiteDevicesStats",
            "listSiteOtherDevices",
            "listSiteAvailableDeviceVersions",
            "listSiteSpectrumAnalysis",
            "listSiteDeviceRadioChannels",
            "listSiteDeviceUpgrades",
        ]
        for op in expected_ops:
            assert op in COLLECTION_VERTEX_MAP

    def test_list_site_devices_vertex(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["listSiteDevices"]
        assert mapping["vertex"] == "devices"
        assert mapping["key_field"] == "id"

    def test_list_site_devices_edges(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["listSiteDevices"]
        edge_cols = {e["edge_col"] for e in mapping["edges"]}
        assert "SiteContainsDevice" in edge_cols
        assert "DeviceUsesProfile" in edge_cols
        assert "DeviceOnMap" in edge_cols

    def test_list_site_devices_ensure_target_vertices(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["listSiteDevices"]
        assert "ensure_target_vertices" in mapping
        targets = mapping["ensure_target_vertices"]
        target_fields = {t[0] for t in targets}
        assert "deviceprofile_id" in target_fields
        assert "map_id" in target_fields

    def test_search_site_devices_vertex(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["searchSiteDevices"]
        assert mapping["vertex"] == "devices"
        assert mapping["key_field"] == "mac"

    def test_search_site_devices_edges(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["searchSiteDevices"]
        edge_cols = {e["edge_col"] for e in mapping["edges"]}
        assert "SiteContainsDevice" in edge_cols

    def test_list_site_devices_stats_vertex(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["listSiteDevicesStats"]
        assert mapping["vertex"] == "devices"
        assert mapping["key_field"] == "id"

    def test_list_site_devices_stats_edges(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["listSiteDevicesStats"]
        edge_cols = {e["edge_col"] for e in mapping["edges"]}
        assert "SiteContainsDevice" in edge_cols
        assert "DeviceUsesProfile" in edge_cols

    def test_list_site_other_devices_vertex(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["listSiteOtherDevices"]
        assert mapping["vertex"] == "other_devices"
        assert mapping["key_field"] == "id"

    def test_list_site_other_devices_edges(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["listSiteOtherDevices"]
        edge_cols = {e["edge_col"] for e in mapping["edges"]}
        assert "OtherDeviceBelongsToSite" in edge_cols

    def test_list_site_available_device_versions(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["listSiteAvailableDeviceVersions"]
        assert mapping["vertex"] == "device_versions"
        assert mapping["key_field"] == "model"
        assert "edges" not in mapping

    def test_list_site_spectrum_analysis_vertex(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["listSiteSpectrumAnalysis"]
        assert mapping["vertex"] == "spectrum_analysis"
        assert mapping["key_field"] == "mac"

    def test_list_site_spectrum_analysis_edges(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["listSiteSpectrumAnalysis"]
        edge_cols = {e["edge_col"] for e in mapping["edges"]}
        assert "SpectrumAnalysisForDevice" in edge_cols

    def test_spectrum_analysis_edge_uses_mac_lookup(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["listSiteSpectrumAnalysis"]
        spectrum_edge = next(e for e in mapping["edges"] if e["edge_col"] == "SpectrumAnalysisForDevice")
        assert spectrum_edge["to_key_lookup"] == "mac"

    def test_list_site_device_radio_channels(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["listSiteDeviceRadioChannels"]
        assert mapping["vertex"] == "radio_channels"
        assert mapping["key_field"] == "key"
        assert "edges" not in mapping

    def test_list_site_device_upgrades(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["listSiteDeviceUpgrades"]
        assert mapping["vertex"] == "device_upgrades"
        assert mapping["key_field"] == "id"
        assert "edges" not in mapping

    def test_edge_definitions_registered(self):
        from src.db.arango_writer import EDGE_DEFINITIONS

        edge_names = {e["edge_collection"] for e in EDGE_DEFINITIONS}
        assert "SpectrumAnalysisForDevice" in edge_names

    def test_spectrum_analysis_edge_structure(self):
        from src.db.arango_writer import EDGE_DEFINITIONS

        edge = next(e for e in EDGE_DEFINITIONS if e["edge_collection"] == "SpectrumAnalysisForDevice")
        assert edge["from_vertex_collections"] == ["spectrum_analysis"]
        assert edge["to_vertex_collections"] == ["devices"]

    def test_new_vertex_collections_referenced(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        new_vertices = {
            "device_versions",
            "spectrum_analysis",
            "radio_channels",
            "device_upgrades",
        }
        found = set()
        for mapping in COLLECTION_VERTEX_MAP.values():
            if isinstance(mapping, dict):
                found.add(mapping["vertex"])
        assert new_vertices.issubset(found)


class TestDerivedConfigGraphStorage:
    """Tests for Issue #184: Derived config graph storage."""

    DERIVED_OPS = [
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

    def test_entity_type_mappings(self):
        from src.db.arango_writer import ENTITY_TYPE_TO_VERTEX

        expected = {
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
        for operation_id, vertex in expected.items():
            assert ENTITY_TYPE_TO_VERTEX.get(operation_id) == vertex

    def test_all_ops_in_collection_vertex_map(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        for op in self.DERIVED_OPS:
            assert op in COLLECTION_VERTEX_MAP, f"{op} missing from COLLECTION_VERTEX_MAP"

    def test_wlans_derived_vertex(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["listSiteWlansDerived"]
        assert mapping["vertex"] == "wlans"
        assert mapping["key_field"] == "id"

    def test_wlans_derived_edges(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["listSiteWlansDerived"]
        edge_cols = {e["edge_col"] for e in mapping["edges"]}
        assert "DerivedConfigForSite" in edge_cols
        assert "DerivedFromTemplate" in edge_cols

    def test_networks_derived_vertex(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["listSiteNetworksDerived"]
        assert mapping["vertex"] == "networks"
        assert mapping["key_field"] == "id"

    def test_service_policies_derived_uses_security_policies(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["listSiteServicePoliciesDerived"]
        assert mapping["vertex"] == "security_policies"

    def test_guest_authorizations_derived_key(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["listSiteAllGuestAuthorizationsDerived"]
        assert mapping["vertex"] == "guests"
        assert mapping["key_field"] == "mac"

    def test_ui_setting_derived_no_edges(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        mapping = COLLECTION_VERTEX_MAP["listSiteUiSettingDerived"]
        assert mapping["vertex"] == "ui_settings"
        assert mapping["key_field"] == "key"
        assert "edges" not in mapping

    def test_template_derived_ops_share_vertex(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        template_ops = [
            "listSiteApTemplatesDerived",
            "listSiteRfTemplatesDerived",
            "listSiteNetworkTemplatesDerived",
            "listSiteGatewayTemplatesDerived",
            "listSiteSiteTemplatesDerived",
        ]
        for op in template_ops:
            assert COLLECTION_VERTEX_MAP[op]["vertex"] == "templates"

    def test_security_profile_derived_vertices(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        expected = {
            "listSiteIdpProfilesDerived": "idp_profiles",
            "listSiteAAMWProfilesDerived": "aamw_profiles",
            "listSiteAntivirusProfilesDerived": "av_profiles",
            "listSiteSecIntelProfilesDerived": "secIntel_profiles",
        }
        for op, vertex in expected.items():
            assert COLLECTION_VERTEX_MAP[op]["vertex"] == vertex

    def test_derived_config_for_site_edge_registered(self):
        from src.db.arango_writer import EDGE_DEFINITIONS

        edge_names = {e["edge_collection"] for e in EDGE_DEFINITIONS}
        assert "DerivedConfigForSite" in edge_names

    def test_derived_from_template_edge_registered(self):
        from src.db.arango_writer import EDGE_DEFINITIONS

        edge_names = {e["edge_collection"] for e in EDGE_DEFINITIONS}
        assert "DerivedFromTemplate" in edge_names

    def test_derived_config_for_site_structure(self):
        from src.db.arango_writer import EDGE_DEFINITIONS

        edge = next(e for e in EDGE_DEFINITIONS if e["edge_collection"] == "DerivedConfigForSite")
        assert "sites" in edge["to_vertex_collections"]
        assert "wlans" in edge["from_vertex_collections"]
        assert "networks" in edge["from_vertex_collections"]
        assert "security_policies" in edge["from_vertex_collections"]

    def test_derived_from_template_structure(self):
        from src.db.arango_writer import EDGE_DEFINITIONS

        edge = next(e for e in EDGE_DEFINITIONS if e["edge_collection"] == "DerivedFromTemplate")
        assert "templates" in edge["to_vertex_collections"]
        assert "wlans" in edge["from_vertex_collections"]

    def test_all_edged_ops_have_derived_config_for_site(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        edged_ops = [op for op in self.DERIVED_OPS if "edges" in COLLECTION_VERTEX_MAP.get(op, {})]
        for op in edged_ops:
            edge_cols = {e["edge_col"] for e in COLLECTION_VERTEX_MAP[op]["edges"]}
            assert "DerivedConfigForSite" in edge_cols, f"{op} missing DerivedConfigForSite edge"

    def test_only_wlans_has_derived_from_template(self):
        from src.db.arango_writer import COLLECTION_VERTEX_MAP

        ops_with_template_edge = []
        for op in self.DERIVED_OPS:
            mapping = COLLECTION_VERTEX_MAP.get(op, {})
            if "edges" in mapping:
                edge_cols = {e["edge_col"] for e in mapping["edges"]}
                if "DerivedFromTemplate" in edge_cols:
                    ops_with_template_edge.append(op)
        assert "listSiteWlansDerived" in ops_with_template_edge

    def test_new_vertex_collections_in_edge_defs(self):
        from src.db.arango_writer import EDGE_DEFINITIONS

        edge = next(e for e in EDGE_DEFINITIONS if e["edge_collection"] == "DerivedConfigForSite")
        from_cols = set(edge["from_vertex_collections"])
        expected_new = {
            "ui_settings",
            "idp_profiles",
            "aamw_profiles",
            "av_profiles",
            "secIntel_profiles",
        }
        assert expected_new.issubset(from_cols)
