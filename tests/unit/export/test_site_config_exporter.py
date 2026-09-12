"""Unit tests for ``src.export.site_config_exporter.SiteConfigExporter``.

Why: Un-omitting this module in ``[tool.coverage.run].omit`` requires 100%
line + branch coverage on the seven static methods that ship site-level
WLAN, map, zone, and settings exports. The module resolves its cross-class
collaborators lazily through ``importlib.import_module("MistHelper")``; tests
inject a fake ``MistHelper`` module via ``sys.modules`` to observe and control
those interactions without importing the monolith.
"""

from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def fake_mh(monkeypatch):
    """Install a fake MistHelper module for lazy importlib resolution.

    Why: SiteConfigExporter reads ``mh.apisession``, ``mh.ConfigUtils``,
    ``mh.DataExporter``, ``mh.PromptUtils``, ``mh.TimeUtils``,
    ``mh.EnhancedSSHRunner``, ``mh.InsightMetricsUtils``,
    ``mh.PacketCaptureManager``, ``mh.APICoreFetchUtils``, ``mh.IsDebugMode``,
    ``mh.PrettyTable``, and ``mh.mistapi`` at call time. Replacing the module
    lets tests observe those interactions cleanly.
    """
    mh = ModuleType("MistHelper")
    mh.apisession = MagicMock()
    mh.ConfigUtils = MagicMock()
    mh.DataExporter = MagicMock()
    mh.PromptUtils = MagicMock()
    mh.TimeUtils = MagicMock()
    mh.EnhancedSSHRunner = MagicMock()
    mh.InsightMetricsUtils = MagicMock()
    mh.PacketCaptureManager = MagicMock()
    mh.APICoreFetchUtils = MagicMock()
    mh.IsDebugMode = MagicMock()
    mh.PrettyTable = MagicMock()
    mh.mistapi = MagicMock()
    monkeypatch.setitem(sys.modules, "MistHelper", mh)
    return mh


class TestResolveWlanSiteName:
    """Cover SiteConfigExporter._resolve_wlan_site_name."""

    def test_returns_matched_site_name(self, fake_mh):
        """Happy path: matching site id → returns that site's name."""
        from src.export.site_config_exporter import SiteConfigExporter

        sites = [{"id": "s1", "name": "HQ"}, {"id": "s2", "name": "Branch"}]
        with (
            patch("src.export.site_config_exporter.mistapi.api.v1.orgs.sites.listOrgSites", return_value=MagicMock()),
            patch("src.export.site_config_exporter.mistapi.get_all", return_value=sites),
        ):
            fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org1"
            result = SiteConfigExporter._resolve_wlan_site_name("s2")

        assert result == "Branch"

    def test_no_match_falls_back_to_site_id(self, fake_mh):
        """No matching id → falls back to the given site_id."""
        from src.export.site_config_exporter import SiteConfigExporter

        sites = [{"id": "s1", "name": "HQ"}]
        with (
            patch("src.export.site_config_exporter.mistapi.api.v1.orgs.sites.listOrgSites", return_value=MagicMock()),
            patch("src.export.site_config_exporter.mistapi.get_all", return_value=sites),
        ):
            result = SiteConfigExporter._resolve_wlan_site_name("unknown")

        assert result == "unknown"

    def test_exception_returns_site_id(self, fake_mh):
        """listOrgSites failure is logged and the site_id is returned as fallback."""
        from src.export.site_config_exporter import SiteConfigExporter

        with patch(
            "src.export.site_config_exporter.mistapi.api.v1.orgs.sites.listOrgSites",
            side_effect=RuntimeError("api down"),
        ):
            result = SiteConfigExporter._resolve_wlan_site_name("s1")

        assert result == "s1"


class TestFetchWlansWithFallback:
    """Cover SiteConfigExporter._fetch_wlans_with_fallback."""

    def test_derived_success_returns_rows(self, fake_mh):
        """Happy path: derived listing succeeds and returns paged rows."""
        from src.export.site_config_exporter import SiteConfigExporter

        rows = [{"ssid": "WiFi1"}]
        with (
            patch(
                "src.export.site_config_exporter.mistapi.api.v1.sites.wlans.listSiteWlansDerived",
                return_value=MagicMock(),
            ) as api,
            patch("src.export.site_config_exporter.mistapi.get_all", return_value=rows),
        ):
            result = SiteConfigExporter._fetch_wlans_with_fallback("s1")

        api.assert_called_once()
        assert result == rows

    def test_derived_failure_falls_back_to_local(self, fake_mh):
        """Derived listing failure → falls back to site-local WLAN listing."""
        from src.export.site_config_exporter import SiteConfigExporter

        rows = [{"ssid": "Local"}]
        with (
            patch(
                "src.export.site_config_exporter.mistapi.api.v1.sites.wlans.listSiteWlansDerived",
                side_effect=RuntimeError("derived down"),
            ),
            patch(
                "src.export.site_config_exporter.mistapi.api.v1.sites.wlans.listSiteWlans",
                return_value=MagicMock(),
            ) as local_api,
            patch("src.export.site_config_exporter.mistapi.get_all", return_value=rows),
        ):
            result = SiteConfigExporter._fetch_wlans_with_fallback("s1")

        local_api.assert_called_once()
        assert result == rows


class TestPersistSiteWlansCsv:
    """Cover SiteConfigExporter._persist_site_wlans_csv."""

    def test_empty_writes_empty_csv(self, fake_mh, caplog):
        """Empty list → writes empty CSV and logs a zero-record notice."""
        from src.export.site_config_exporter import SiteConfigExporter

        with caplog.at_level("INFO", logger="root"):
            SiteConfigExporter._persist_site_wlans_csv([], "SiteWlans_HQ.csv", "HQ")

        fake_mh.DataExporter.write_with_format_selection.assert_called_once_with([], "SiteWlans_HQ.csv")
        messages = " ".join(rec.getMessage() for rec in caplog.records)
        assert "0 records" in messages

    def test_non_empty_flattens_sorts_and_writes(self, fake_mh, caplog):
        """Non-empty list flows through flatten/escape/sort/write with SSID ordering."""
        from src.export.site_config_exporter import SiteConfigExporter

        rows = [{"ssid": "B"}, {"ssid": "A"}]
        with (
            caplog.at_level("INFO", logger="root"),
            patch("src.export.site_config_exporter.DataProcessingUtils") as dpu,
        ):
            dpu.flatten_nested_fields.return_value = rows
            dpu.escape_multiline.return_value = rows
            SiteConfigExporter._persist_site_wlans_csv(rows, "SiteWlans_HQ.csv", "HQ")

        dpu.flatten_nested_fields.assert_called_once_with(rows)
        dpu.escape_multiline.assert_called_once_with(rows)
        # Sorted rows: A then B.
        written = fake_mh.DataExporter.write_with_format_selection.call_args.args[0]
        assert [r["ssid"] for r in written] == ["A", "B"]
        messages = " ".join(rec.getMessage() for rec in caplog.records)
        assert "2 records" in messages


class TestWlans:
    """Cover SiteConfigExporter.wlans."""

    def test_no_site_id_and_prompt_cancel_returns_early(self, fake_mh):
        """No site given and prompt returns None → aborts silently before any fetch."""
        from src.export.site_config_exporter import SiteConfigExporter

        fake_mh.PromptUtils.select_site.return_value = None
        with (
            patch.object(SiteConfigExporter, "_resolve_wlan_site_name") as resolve,
            patch.object(SiteConfigExporter, "_fetch_wlans_with_fallback") as fetch,
            patch.object(SiteConfigExporter, "_persist_site_wlans_csv") as persist,
        ):
            SiteConfigExporter.wlans()

        resolve.assert_not_called()
        fetch.assert_not_called()
        persist.assert_not_called()

    def test_prompts_when_no_site_and_dispatches(self, fake_mh):
        """No site_id + successful prompt → runs full resolve/fetch/persist pipeline."""
        from src.export.site_config_exporter import SiteConfigExporter

        fake_mh.PromptUtils.select_site.return_value = "s1"
        with (
            patch.object(SiteConfigExporter, "_resolve_wlan_site_name", return_value="HQ Site") as resolve,
            patch.object(SiteConfigExporter, "_fetch_wlans_with_fallback", return_value=[{"ssid": "A"}]) as fetch,
            patch.object(SiteConfigExporter, "_persist_site_wlans_csv") as persist,
        ):
            SiteConfigExporter.wlans()

        resolve.assert_called_once_with("s1")
        fetch.assert_called_once_with("s1")
        # Site name is sanitized: spaces → underscores.
        persist.assert_called_once_with([{"ssid": "A"}], "SiteWlans_HQ_Site.csv", "HQ Site")

    def test_explicit_site_id_skips_prompt(self, fake_mh):
        """Explicit site_id → skips PromptUtils.select_site."""
        from src.export.site_config_exporter import SiteConfigExporter

        with (
            patch.object(SiteConfigExporter, "_resolve_wlan_site_name", return_value="Branch"),
            patch.object(SiteConfigExporter, "_fetch_wlans_with_fallback", return_value=[]),
            patch.object(SiteConfigExporter, "_persist_site_wlans_csv"),
        ):
            SiteConfigExporter.wlans(site_id="s2")

        fake_mh.PromptUtils.select_site.assert_not_called()


class TestMaps:
    """Cover SiteConfigExporter.maps."""

    def test_constructs_site_export_utils_and_delegates(self, fake_mh):
        """maps() builds a SiteExportUtils with mh.* dep symbols and calls _export_data."""
        from src.export.site_config_exporter import SiteConfigExporter

        with patch("src.export.site_config_exporter.SiteExportUtils") as SEU:
            SiteConfigExporter.maps()

        SEU.assert_called_once()
        SEU.return_value._export_data.assert_called_once()
        kwargs = SEU.return_value._export_data.call_args.kwargs
        assert kwargs["data_type"] == "maps"
        assert kwargs["sort_key"] == "name"


class TestZones:
    """Cover SiteConfigExporter.zones."""

    def test_constructs_site_export_utils_and_delegates(self, fake_mh):
        """zones() builds a SiteExportUtils with mh.* dep symbols and calls _export_data."""
        from src.export.site_config_exporter import SiteConfigExporter

        with patch("src.export.site_config_exporter.SiteExportUtils") as SEU:
            SiteConfigExporter.zones()

        SEU.assert_called_once()
        SEU.return_value._export_data.assert_called_once()
        kwargs = SEU.return_value._export_data.call_args.kwargs
        assert kwargs["data_type"] == "zones"
        assert kwargs["sort_key"] == "name"


class TestSettings:
    """Cover SiteConfigExporter.settings."""

    def test_no_data_warns_and_returns(self, fake_mh, caplog):
        """No data returned → warns "no site configurations" and skips the write."""
        from src.export.site_config_exporter import SiteConfigExporter

        with (
            caplog.at_level("WARNING", logger="root"),
            patch("src.export.site_config_exporter.APIFetchUtils.all_site_settings", return_value=[]),
        ):
            SiteConfigExporter.settings()

        fake_mh.DataExporter.write_with_format_selection.assert_not_called()
        messages = " ".join(rec.getMessage() for rec in caplog.records)
        assert "No site configurations" in messages

    def test_with_data_flattens_and_writes(self, fake_mh, caplog):
        """Data returned → flows through flatten/escape/write and reports the count."""
        from src.export.site_config_exporter import SiteConfigExporter

        rows = [{"id": "s1"}]
        with (
            caplog.at_level("INFO", logger="root"),
            patch("src.export.site_config_exporter.APIFetchUtils.all_site_settings", return_value=rows),
            patch("src.export.site_config_exporter.DataProcessingUtils") as dpu,
        ):
            dpu.flatten_nested_fields.return_value = rows
            dpu.escape_multiline.return_value = rows
            SiteConfigExporter.settings()

        dpu.flatten_nested_fields.assert_called_once_with(rows)
        dpu.escape_multiline.assert_called_once_with(rows)
        fake_mh.DataExporter.write_with_format_selection.assert_called_once_with(rows, "AllSiteConfigs.csv")
        messages = " ".join(rec.getMessage() for rec in caplog.records)
        assert "1 site configurations exported" in messages
