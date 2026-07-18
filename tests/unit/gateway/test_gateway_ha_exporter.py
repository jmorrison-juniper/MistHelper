"""Unit tests for ``src.gateway.gateway_ha_exporter.GatewayHaExporter``.

Why: Un-omitting this module from ``[tool.coverage.run].omit`` requires 100%
line + branch coverage across the 6 static methods that back Menu #87 -- the
Gateway HA Cluster Info export. Cross-class collaborators (APICoreFetchUtils,
ConfigUtils, PromptUtils, DataExporter) are resolved lazily through
``importlib.import_module("MistHelper")``; ``mistapi`` and
``DataProcessingUtils`` are module-level imports patched directly on the
module. Tests inject a fake ``MistHelper`` module via ``sys.modules`` to
observe and control lazy collaborator interactions without importing the
monolith.
"""

from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def fake_mh(monkeypatch):
    """Install a fake MistHelper module for lazy importlib resolution.

    Why: GatewayHaExporter reads ``mh.apisession``, ``mh.APICoreFetchUtils``,
    ``mh.ConfigUtils``, ``mh.PromptUtils``, and ``mh.DataExporter`` at call
    time. Replacing the module lets tests observe and control those
    interactions cleanly.
    """
    mh = ModuleType("MistHelper")
    mh.apisession = MagicMock(name="apisession")
    mh.APICoreFetchUtils = MagicMock(name="APICoreFetchUtils")
    mh.ConfigUtils = MagicMock(name="ConfigUtils")
    mh.PromptUtils = MagicMock(name="PromptUtils")
    mh.DataExporter = MagicMock(name="DataExporter")
    monkeypatch.setitem(sys.modules, "MistHelper", mh)
    return mh


class TestClassAttributes:
    """Cover module-level class attributes."""

    def test_ha_stat_fields_list(self):
        """HA_STAT_FIELDS enumerates all HA stat columns preserved from the API response."""
        from src.gateway.gateway_ha_exporter import GatewayHaExporter

        assert "mac" in GatewayHaExporter.HA_STAT_FIELDS
        assert "is_ha" in GatewayHaExporter.HA_STAT_FIELDS
        assert "cluster_stat" in GatewayHaExporter.HA_STAT_FIELDS
        assert len(GatewayHaExporter.HA_STAT_FIELDS) == 14

    def test_empty_ha_pair_shape(self):
        """EMPTY_HA_PAIR provides the three node-pair fallback keys with safe defaults."""
        from src.gateway.gateway_ha_exporter import GatewayHaExporter

        assert GatewayHaExporter.EMPTY_HA_PAIR == {
            "ha_cluster_node0_mac": None,
            "ha_cluster_node1_mac": None,
            "ha_cluster_node_count": 0,
        }


class TestPersistHaExport:
    """Cover GatewayHaExporter._persist_ha_export."""

    def test_flattens_writes_and_logs(self, fake_mh, caplog):
        """Rows are flattened via DataProcessingUtils, written via DataExporter, and count logged."""
        from src.gateway.gateway_ha_exporter import GatewayHaExporter

        rows = [{"mac": "aa", "cluster_stat": {"n": 1}}]
        flat = [{"mac": "aa", "cluster_stat_n": 1}]

        with (
            patch(
                "src.gateway.gateway_ha_exporter.DataProcessingUtils.flatten_nested_fields",
                return_value=flat,
            ) as flatten,
            caplog.at_level("INFO", logger="root"),
        ):
            GatewayHaExporter._persist_ha_export(rows)

        flatten.assert_called_once_with(rows)
        fake_mh.DataExporter.write_with_format_selection.assert_called_once_with(
            flat, "GatewayHaClusterInfo.csv", api_function_name="listSiteGatewayHaStats"
        )
        assert any("Exported 1 HA gateway records" in r.message for r in caplog.records)


class TestCollectHaGateways:
    """Cover GatewayHaExporter._collect_ha_gateways."""

    def test_returns_ha_filtered_gateways(self, fake_mh):
        """API returns mixed gateways; only is_ha=True entries are returned."""
        from src.gateway.gateway_ha_exporter import GatewayHaExporter

        gateways = [
            {"id": "g1", "is_ha": True},
            {"id": "g2", "is_ha": False},
            {"id": "g3", "is_ha": True},
        ]
        fake_mh.APICoreFetchUtils.get_api_response_data.return_value = gateways

        with patch(
            "src.gateway.gateway_ha_exporter.mistapi.api.v1.sites.stats.listSiteDevicesStats",
            return_value=MagicMock(),
        ) as api_call:
            result = GatewayHaExporter._collect_ha_gateways("site-x")

        api_call.assert_called_once_with(fake_mh.apisession, "site-x", type="gateway")
        assert result == [{"id": "g1", "is_ha": True}, {"id": "g3", "is_ha": True}]

    def test_no_ha_gateways_returns_none_and_prints(self, fake_mh, capsys):
        """No HA gateways -> prints notice and returns None."""
        from src.gateway.gateway_ha_exporter import GatewayHaExporter

        fake_mh.APICoreFetchUtils.get_api_response_data.return_value = [{"id": "g1", "is_ha": False}]

        with patch(
            "src.gateway.gateway_ha_exporter.mistapi.api.v1.sites.stats.listSiteDevicesStats",
            return_value=MagicMock(),
        ):
            result = GatewayHaExporter._collect_ha_gateways("site-x")

        assert result is None
        assert "No HA gateways found" in capsys.readouterr().out


class TestHaClusterInfo:
    """Cover GatewayHaExporter.ha_cluster_info (public entry)."""

    def test_no_site_selected_returns_early(self, fake_mh, monkeypatch):
        """PromptUtils.select_site returns falsy -> abort before fetching gateways."""
        from src.gateway.gateway_ha_exporter import GatewayHaExporter

        fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"
        fake_mh.PromptUtils.select_site.return_value = ""
        collect = MagicMock()
        monkeypatch.setattr(GatewayHaExporter, "_collect_ha_gateways", staticmethod(collect))

        GatewayHaExporter.ha_cluster_info()

        collect.assert_not_called()

    def test_collect_returns_none_returns_early(self, fake_mh, monkeypatch):
        """_collect_ha_gateways returns None -> abort before building rows."""
        from src.gateway.gateway_ha_exporter import GatewayHaExporter

        fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"
        fake_mh.PromptUtils.select_site.return_value = "site-x"
        monkeypatch.setattr(GatewayHaExporter, "_collect_ha_gateways", staticmethod(lambda site_id: None))
        build = MagicMock()
        monkeypatch.setattr(GatewayHaExporter, "_build_ha_rows", staticmethod(build))

        GatewayHaExporter.ha_cluster_info()

        build.assert_not_called()

    def test_happy_path_builds_prints_persists(self, fake_mh, monkeypatch):
        """Full path: gateways collected, rows built, printed, and persisted."""
        from src.gateway.gateway_ha_exporter import GatewayHaExporter

        fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"
        fake_mh.PromptUtils.select_site.return_value = "site-x"
        ha_gateways = [{"id": "g1", "is_ha": True}]
        rows = [{"mac": "aa"}]

        monkeypatch.setattr(GatewayHaExporter, "_collect_ha_gateways", staticmethod(lambda site_id: ha_gateways))
        monkeypatch.setattr(GatewayHaExporter, "_build_ha_rows", staticmethod(lambda gws, site_id: rows))
        print_summary = MagicMock()
        persist = MagicMock()
        monkeypatch.setattr(GatewayHaExporter, "_print_ha_summary", staticmethod(print_summary))
        monkeypatch.setattr(GatewayHaExporter, "_persist_ha_export", staticmethod(persist))

        GatewayHaExporter.ha_cluster_info()

        print_summary.assert_called_once_with(rows)
        persist.assert_called_once_with(rows)

    def test_exception_is_logged_and_swallowed(self, fake_mh, monkeypatch, caplog):
        """Any raised exception hits the broad except -> logged, no re-raise."""
        from src.gateway.gateway_ha_exporter import GatewayHaExporter

        fake_mh.ConfigUtils.get_cached_or_prompted_org_id.side_effect = RuntimeError("boom")

        with caplog.at_level("ERROR", logger="root"):
            GatewayHaExporter.ha_cluster_info()

        assert any("Failed to export HA gateway cluster info" in r.message for r in caplog.records)


class TestFetchHaPairForGateway:
    """Cover GatewayHaExporter._fetch_ha_pair_for_gateway."""

    def test_two_nodes_returns_both_macs(self, fake_mh):
        """Response with two nodes -> both node MACs and count=2."""
        from src.gateway.gateway_ha_exporter import GatewayHaExporter

        fake_mh.APICoreFetchUtils.get_api_response_data.return_value = {"nodes": [{"mac": "aa"}, {"mac": "bb"}]}

        with patch(
            "src.gateway.gateway_ha_exporter.mistapi.api.v1.sites.devices.GetSiteDeviceHaClusterNode",
            return_value=MagicMock(),
        ):
            result = GatewayHaExporter._fetch_ha_pair_for_gateway("s1", "d1")

        assert result == {"ha_cluster_node0_mac": "aa", "ha_cluster_node1_mac": "bb", "ha_cluster_node_count": 2}

    def test_one_node_second_mac_is_none(self, fake_mh):
        """Response with one node -> second MAC None and count=1."""
        from src.gateway.gateway_ha_exporter import GatewayHaExporter

        fake_mh.APICoreFetchUtils.get_api_response_data.return_value = {"nodes": [{"mac": "aa"}]}

        with patch(
            "src.gateway.gateway_ha_exporter.mistapi.api.v1.sites.devices.GetSiteDeviceHaClusterNode",
            return_value=MagicMock(),
        ):
            result = GatewayHaExporter._fetch_ha_pair_for_gateway("s1", "d1")

        assert result == {"ha_cluster_node0_mac": "aa", "ha_cluster_node1_mac": None, "ha_cluster_node_count": 1}

    def test_zero_nodes_both_macs_none(self, fake_mh):
        """Empty nodes list -> both MACs None and count=0."""
        from src.gateway.gateway_ha_exporter import GatewayHaExporter

        fake_mh.APICoreFetchUtils.get_api_response_data.return_value = {"nodes": []}

        with patch(
            "src.gateway.gateway_ha_exporter.mistapi.api.v1.sites.devices.GetSiteDeviceHaClusterNode",
            return_value=MagicMock(),
        ):
            result = GatewayHaExporter._fetch_ha_pair_for_gateway("s1", "d1")

        assert result == {"ha_cluster_node0_mac": None, "ha_cluster_node1_mac": None, "ha_cluster_node_count": 0}

    def test_non_dict_response_returns_empty_pair(self, fake_mh):
        """Non-dict response body -> EMPTY_HA_PAIR fallback."""
        from src.gateway.gateway_ha_exporter import GatewayHaExporter

        fake_mh.APICoreFetchUtils.get_api_response_data.return_value = ["unexpected"]

        with patch(
            "src.gateway.gateway_ha_exporter.mistapi.api.v1.sites.devices.GetSiteDeviceHaClusterNode",
            return_value=MagicMock(),
        ):
            result = GatewayHaExporter._fetch_ha_pair_for_gateway("s1", "d1")

        assert result == GatewayHaExporter.EMPTY_HA_PAIR
        # Ensure a copy, not the class attribute itself.
        assert result is not GatewayHaExporter.EMPTY_HA_PAIR

    def test_exception_returns_empty_pair(self, fake_mh, caplog):
        """API exception -> logs warning and returns EMPTY_HA_PAIR."""
        from src.gateway.gateway_ha_exporter import GatewayHaExporter

        with (
            patch(
                "src.gateway.gateway_ha_exporter.mistapi.api.v1.sites.devices.GetSiteDeviceHaClusterNode",
                side_effect=RuntimeError("404"),
            ),
            caplog.at_level("WARNING", logger="root"),
        ):
            result = GatewayHaExporter._fetch_ha_pair_for_gateway("s1", "d1")

        assert result == GatewayHaExporter.EMPTY_HA_PAIR
        assert any("Could not fetch HA node info" in r.message for r in caplog.records)


class TestBuildHaRows:
    """Cover GatewayHaExporter._build_ha_rows."""

    def test_merges_stats_fields_with_ha_pair(self, monkeypatch):
        """Each HA gateway row has stat fields, forced site_id, and merged node pair."""
        from src.gateway.gateway_ha_exporter import GatewayHaExporter

        gateways = [
            {"id": "d1", "mac": "aa", "name": "gw1", "is_ha": True, "site_id": "old-site"},
            {"id": "d2", "mac": "bb", "name": "gw2", "is_ha": True},
        ]

        def fake_pair(site_id, device_id):
            return {
                "ha_cluster_node0_mac": f"{device_id}-0",
                "ha_cluster_node1_mac": f"{device_id}-1",
                "ha_cluster_node_count": 2,
            }

        monkeypatch.setattr(GatewayHaExporter, "_fetch_ha_pair_for_gateway", staticmethod(fake_pair))

        rows = GatewayHaExporter._build_ha_rows(gateways, "site-x")

        assert len(rows) == 2
        assert rows[0]["mac"] == "aa"
        assert rows[0]["name"] == "gw1"
        assert rows[0]["site_id"] == "site-x"  # override the stat record's site_id
        assert rows[0]["ha_cluster_node0_mac"] == "d1-0"
        assert rows[1]["site_id"] == "site-x"
        assert rows[1]["ha_cluster_node1_mac"] == "d2-1"

    def test_missing_id_uses_empty_string(self, monkeypatch):
        """Gateway missing an ``id`` still produces a row -- device_id passes as ''."""
        from src.gateway.gateway_ha_exporter import GatewayHaExporter

        captured = {}

        def fake_pair(site_id, device_id):
            captured["device_id"] = device_id
            return dict(GatewayHaExporter.EMPTY_HA_PAIR)

        monkeypatch.setattr(GatewayHaExporter, "_fetch_ha_pair_for_gateway", staticmethod(fake_pair))
        rows = GatewayHaExporter._build_ha_rows([{"mac": "aa"}], "site-x")

        assert len(rows) == 1
        assert captured["device_id"] == ""


class TestPrintHaSummary:
    """Cover GatewayHaExporter._print_ha_summary."""

    def test_prints_header_separator_and_rows(self, capsys):
        """Prints section header, table header, separator, and one line per row."""
        from src.gateway.gateway_ha_exporter import GatewayHaExporter

        rows = [
            {
                "name": "gateway-01",
                "node_name": "node0",
                "status": "connected",
                "ha_cluster_node0_mac": "aa:bb",
                "ha_cluster_node1_mac": "cc:dd",
                "vc_mac": "ee:ff",
            },
            {
                "name": "very-very-long-gateway-name-that-exceeds-28-chars",
                "node_name": "node1",
                "status": "disconnected",
                "ha_cluster_node0_mac": None,  # exercises `or ""` branch
                "ha_cluster_node1_mac": None,
                "vc_mac": None,
            },
        ]

        GatewayHaExporter._print_ha_summary(rows)
        out = capsys.readouterr().out

        assert "HA Gateway Cluster Summary" in out
        assert "Name" in out and "Node0 MAC" in out
        assert "gateway-01" in out
        # The truncation caps at 28 chars, then padded to 30 -- confirm the truncated prefix appears.
        assert "very-very-long-gateway-name-" in out

    def test_empty_rows_prints_header_only(self, capsys):
        """Empty row list -> header + separator + trailing blank line, no data rows."""
        from src.gateway.gateway_ha_exporter import GatewayHaExporter

        GatewayHaExporter._print_ha_summary([])
        out = capsys.readouterr().out
        assert "HA Gateway Cluster Summary" in out
        assert "Node0 MAC" in out
