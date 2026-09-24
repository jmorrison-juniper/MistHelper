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
    deps.mistapi.api.v1.sites.sites.getSiteInfo.return_value = MagicMock(
        data={"id": "site-1", "name": "My Site"}, status_code=200
    )  # WHY: getSiteInfo returns one site object.
    deps.mistapi.get_all.side_effect = [
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
    deps.mistapi.api.v1.sites.sites.getSiteInfo.return_value = MagicMock(
        data={"id": "site-1", "name": "My Site"}, status_code=200
    )  # WHY: getSiteInfo returns one site object.
    deps.mistapi.api.v1.sites.stats.listSiteWirelessClientsStats.return_value = MagicMock()
    # WHY: Menu 75 requests the path form through the session, because the live cloud refuses the SDK form (#3297).
    deps.apisession.mist_get.return_value = MagicMock(data={"score": 99}, status_code=200)
    deps.mistapi.get_all.side_effect = [
        [{"mac": "aa:bb:cc:dd:ee:ff", "hostname": "h1", "last_seen": "now"}],
    ]
    deps.InputUtils.safe_input.return_value = "0"
    deps.SiteClientExporter._normalize_client_mac_or_none.return_value = "aa:bb:cc:dd:ee:ff"
    deps.InsightMetricsUtils.get_by_scope.return_value = ["throughput"]
    mock_resolve_runtime_dependencies.return_value = deps

    SiteClientInsightsService.execute()

    deps.DataExporter.write_with_format_selection.assert_called_once()
    rows = deps.DataExporter.write_with_format_selection.call_args.args[0]  # WHY: Read the exported rows.
    assert [row["score"] for row in rows] == [99]  # WHY: The one metric with data reaches the export.


def test_resolve_site_name_uses_get_site_info() -> None:
    """The helper returns a known site name from the installed SDK route."""
    deps = _deps_bundle()  # WHY: build isolated dependencies for the helper.
    deps.mistapi.api.v1.sites.sites.getSiteInfo.return_value = MagicMock(
        data={"id": "site-1", "name": "My Site"}, status_code=200
    )  # WHY: getSiteInfo returns one site object.

    result = SiteClientInsightsService._resolve_site_name(deps, "site-1")  # WHY: exercise repaired call site.

    assert result == "My Site"  # WHY: known site name proves response-shape handling.
    deps.mistapi.api.v1.sites.listSites.assert_not_called()  # WHY: phantom SDK route must stay unused.
