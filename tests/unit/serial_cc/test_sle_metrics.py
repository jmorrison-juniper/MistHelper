"""Unit tests for offender #9 SLE metrics service."""

import logging
from unittest.mock import MagicMock, patch

from src.refactors.serial_cc.sle_metrics import SLEMetricsService


class DummyDeps:
    """Lightweight dependency bundle for service tests."""

    def __init__(self):
        self.ConfigUtils = MagicMock()
        self.PROGRESS_EMITTER = None
        self.TimeUtils = MagicMock()
        self.DataProcessingUtils = MagicMock()
        self.DataExporter = MagicMock()
        self.mistapi = MagicMock()
        self.apisession = MagicMock()


def _make_dependency_bundle():
    """Create the service dependency bundle used by the resolver patch."""
    return DummyDeps()


@patch("src.refactors.serial_cc.sle_metrics._resolve_runtime_dependencies")
def test_sle_metrics_normal_mode_fetches_all_categories(mock_resolve_runtime_dependencies):
    """Normal mode fetches all SLE categories and specialized metrics."""
    deps = _make_dependency_bundle()
    mock_resolve_runtime_dependencies.return_value = deps
    deps.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"
    deps.TimeUtils.get_dynamic_lookback_hours.return_value = 168
    deps.mistapi.get_all.return_value = [{"id": "sle-1"}]
    deps.mistapi.api.v1.orgs.insights.getOrgSle.return_value = MagicMock(data={"metric": "summary"})
    deps.mistapi.api.v1.orgs.insights.getOrgSitesSle.return_value = MagicMock()
    deps.DataProcessingUtils.flatten_nested_fields.side_effect = lambda rows: rows
    deps.DataProcessingUtils.escape_multiline.side_effect = lambda rows: rows

    SLEMetricsService.execute(fast=False)

    assert deps.DataExporter.write_with_format_selection.called


@patch("src.refactors.serial_cc.sle_metrics._resolve_runtime_dependencies")
def test_sle_metrics_fast_mode_reduces_scope(mock_resolve_runtime_dependencies, caplog):
    """Fast mode only fetches wifi category and summary metric."""
    deps = _make_dependency_bundle()
    mock_resolve_runtime_dependencies.return_value = deps
    deps.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"
    deps.TimeUtils.get_dynamic_lookback_hours.return_value = 1
    deps.mistapi.get_all.return_value = []
    deps.mistapi.api.v1.orgs.insights.getOrgSle.return_value = MagicMock(data={})
    deps.mistapi.api.v1.orgs.insights.getOrgSitesSle.return_value = MagicMock()
    deps.DataProcessingUtils.flatten_nested_fields.side_effect = lambda rows: rows
    deps.DataProcessingUtils.escape_multiline.side_effect = lambda rows: rows

    with caplog.at_level(logging.INFO, logger="root"):
        SLEMetricsService.execute(fast=True)

    out = "\n".join(record.getMessage() for record in caplog.records)
    assert "SLE data retrieval completed" in out


@patch("src.refactors.serial_cc.sle_metrics._resolve_runtime_dependencies")
def test_sle_metrics_handles_empty_results(mock_resolve_runtime_dependencies):
    """Service writes empty file when no SLE data is returned."""
    deps = _make_dependency_bundle()
    mock_resolve_runtime_dependencies.return_value = deps
    deps.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"
    deps.TimeUtils.get_dynamic_lookback_hours.return_value = 168
    deps.mistapi.get_all.return_value = []
    deps.mistapi.api.v1.orgs.insights.getOrgSle.return_value = MagicMock(data={})
    deps.mistapi.api.v1.orgs.insights.getOrgSitesSle.return_value = MagicMock()
    deps.DataProcessingUtils.flatten_nested_fields.side_effect = lambda rows: rows
    deps.DataProcessingUtils.escape_multiline.side_effect = lambda rows: rows

    SLEMetricsService.execute(fast=False)

    save_calls = deps.DataExporter.write_with_format_selection.call_args_list
    assert any(call[0][0] == [] for call in save_calls)
