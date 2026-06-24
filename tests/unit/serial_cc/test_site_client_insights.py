"""Unit tests for extracted SiteClientInsightsService."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.refactors.serial_cc.site_client_insights import SiteClientInsightsService


def _deps_bundle():
    deps = SimpleNamespace()
    deps.mistapi = MagicMock()
    deps.apisession = MagicMock()
    deps.InsightMetricsUtils = MagicMock()
    deps.ConstDefinitionsExporter = MagicMock()  # Canonical insight-metrics refresh exporter double
    deps.PromptUtils = MagicMock()
    deps.InputUtils = MagicMock()
    deps.EnhancedSSHRunner = MagicMock()
    deps.DataProcessingUtils = MagicMock()
    deps.DataExporter = MagicMock()
    deps.SiteClientExporter = MagicMock()
    deps.DataProcessingUtils.flatten_nested_fields.side_effect = lambda rows: rows
    deps.DataProcessingUtils.escape_multiline.side_effect = lambda rows: rows
    deps.EnhancedSSHRunner.sanitize_filename.side_effect = lambda value: value
    return deps


@patch("src.refactors.serial_cc.site_client_insights._resolve_runtime_dependencies")
def test_no_site_selected_returns_early(mock_resolve_runtime_dependencies):
    deps = _deps_bundle()
    deps.PromptUtils.select_site.return_value = None
    mock_resolve_runtime_dependencies.return_value = deps

    SiteClientInsightsService.execute()

    deps.DataExporter.write_with_format_selection.assert_not_called()


@patch("src.refactors.serial_cc.site_client_insights._resolve_runtime_dependencies")
def test_invalid_client_mac_returns_early(mock_resolve_runtime_dependencies):
    deps = _deps_bundle()
    deps.PromptUtils.select_site.return_value = "site-1"
    deps.mistapi.api.v1.sites.listSites.return_value = MagicMock()
    deps.mistapi.get_all.side_effect = [
        [{"id": "site-1", "name": "My Site"}],
        [{"mac": "aa:bb:cc:dd:ee:ff", "hostname": "h1", "last_seen": "now"}],
    ]
    deps.InputUtils.safe_input.return_value = "aa:bb:cc:dd:ee:ff"
    deps.SiteClientExporter._normalize_client_mac_or_none.return_value = None
    mock_resolve_runtime_dependencies.return_value = deps

    SiteClientInsightsService.execute()

    deps.DataExporter.write_with_format_selection.assert_not_called()


@patch("src.refactors.serial_cc.site_client_insights._resolve_runtime_dependencies")
def test_happy_path_exports_rows(mock_resolve_runtime_dependencies):
    deps = _deps_bundle()
    deps.PromptUtils.select_site.return_value = "site-1"
    deps.mistapi.api.v1.sites.listSites.return_value = MagicMock()
    deps.mistapi.api.v1.sites.stats.listSiteWirelessClientsStats.return_value = MagicMock()
    deps.mistapi.api.v1.sites.insights.getSiteInsightMetricsForClient.return_value = MagicMock(data={"score": 99})
    deps.mistapi.get_all.side_effect = [
        [{"id": "site-1", "name": "My Site"}],
        [{"mac": "aa:bb:cc:dd:ee:ff", "hostname": "h1", "last_seen": "now"}],
    ]
    deps.InputUtils.safe_input.return_value = "0"
    deps.SiteClientExporter._normalize_client_mac_or_none.return_value = "aa:bb:cc:dd:ee:ff"
    deps.InsightMetricsUtils.get_by_scope.return_value = ["throughput"]
    mock_resolve_runtime_dependencies.return_value = deps

    SiteClientInsightsService.execute()

    deps.DataExporter.write_with_format_selection.assert_called_once()
