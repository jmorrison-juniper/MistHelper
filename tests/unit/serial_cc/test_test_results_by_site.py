"""Unit tests for gateway test results serial_cc service extraction."""

from unittest.mock import MagicMock, patch

from src.refactors.serial_cc.test_results_by_site import GatewayTestResultsService


class DummyDeps:
    """Lightweight dependency bundle for GatewayTestResultsService unit tests."""

    def __init__(self):
        self.ConfigUtils = MagicMock()  # Org ID prompt/cache utility
        self.CacheUtils = MagicMock()  # CSV cache existence checker
        self.OrgInventoryExporter = MagicMock()  # Inventory regeneration callback holder
        self.OrgInventoryExporter.inventory = MagicMock()  # Inventory callback attribute
        self.FilePathUtils = MagicMock()  # Canonical data/ path resolver
        self.GatewayExportUtils = MagicMock()  # API-based site-ID discovery
        self.ValidationUtils = MagicMock()  # site_id format validator
        self.DataProcessingUtils = MagicMock()  # Flatten and sanitise helpers
        self.DataExporter = MagicMock()  # Output writer
        self.RateLimitingUtils = MagicMock()  # Adaptive rate-limit delay calculator
        self.RateLimitingUtils.get_rate_limited_delay.return_value = (None, 0)  # No delay in tests
        self.execute_fn = MagicMock(return_value=([], []))  # Empty pool result (1012 SC-003 rename)
        self.mistapi = MagicMock()  # Mist SDK surface
        self.apisession = MagicMock()  # Active API session
        self._api_usage_cache = {}  # Empty telemetry cache for tests
        self.tqdm = lambda items=None, **_kwargs: (items or [])  # Identity progress wrapper


@patch("src.refactors.serial_cc.test_results_by_site._resolve_runtime_dependencies")
def test_execute_exits_early_when_no_gateway_sites(mock_resolve):
    """Service exits early and does not export when no gateway sites are found."""
    deps = DummyDeps()  # Create synthetic dependency bundle
    mock_resolve.return_value = deps  # Inject synthetic dependencies
    deps.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-abc"  # Provide a test org ID
    deps.GatewayExportUtils._get_site_ids_with_devices.return_value = []  # No gateway sites in org

    GatewayTestResultsService.execute(fast=False)  # Execute service in standard mode

    deps.DataExporter.write_with_format_selection.assert_not_called()  # No output written on empty site list


@patch("src.refactors.serial_cc.test_results_by_site._resolve_runtime_dependencies")
def test_execute_sequential_exports_records(mock_resolve):
    """Sequential mode fetches site results and exports a CSV."""
    deps = DummyDeps()  # Create synthetic dependency bundle
    mock_resolve.return_value = deps  # Inject synthetic dependencies
    deps.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-abc"  # Provide a test org ID
    deps.GatewayExportUtils._get_site_ids_with_devices.return_value = ["site-1"]  # One gateway site
    deps.DataProcessingUtils.flatten_nested_fields.side_effect = lambda rows: rows  # Identity flatten
    deps.DataProcessingUtils.escape_multiline.side_effect = lambda rows: rows  # Identity sanitise

    fake_result = {"site_id": "site-1", "type": "speedtest", "status": "passed"}  # Sample row
    response_mock = MagicMock()  # Mock API response object
    response_mock.data = {"results": [fake_result]}  # Single result per site
    deps.mistapi.api.v1.sites.synthetic_test.searchSiteSyntheticTest.return_value = response_mock

    GatewayTestResultsService.execute(fast=False)  # Execute service in standard mode

    deps.DataExporter.write_with_format_selection.assert_called_once()  # CSV must be written exactly once
    call_args = deps.DataExporter.write_with_format_selection.call_args.args  # Inspect positional args
    assert call_args[1] == "AllGatewayTestResults.csv"  # Filename contract must be preserved
    assert call_args[0][0]["status"] == "passed"  # Result rows must flow through to the writer


@patch("src.refactors.serial_cc.test_results_by_site._resolve_runtime_dependencies")
def test_execute_sequential_no_export_when_empty_results(mock_resolve):
    """Sequential mode does not write CSV when all sites return empty results."""
    deps = DummyDeps()  # Create synthetic dependency bundle
    mock_resolve.return_value = deps  # Inject synthetic dependencies
    deps.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-abc"  # Provide a test org ID
    deps.GatewayExportUtils._get_site_ids_with_devices.return_value = ["site-1"]  # One gateway site

    response_mock = MagicMock()  # Mock API response object
    response_mock.data = {"results": []}  # Site returns no results
    deps.mistapi.api.v1.sites.synthetic_test.searchSiteSyntheticTest.return_value = response_mock

    GatewayTestResultsService.execute(fast=False)  # Execute service in standard mode

    deps.DataExporter.write_with_format_selection.assert_not_called()  # No CSV on empty results


@patch("src.refactors.serial_cc.test_results_by_site._resolve_runtime_dependencies")
def test_execute_fast_uses_pool_management(mock_resolve):
    """Fast mode calls execute_fn (pool executor) and exports results."""
    deps = DummyDeps()  # Create synthetic dependency bundle
    mock_resolve.return_value = deps  # Inject synthetic dependencies
    deps.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-abc"  # Provide a test org ID
    deps.DataProcessingUtils.flatten_nested_fields.side_effect = lambda rows: rows  # Identity flatten
    deps.DataProcessingUtils.escape_multiline.side_effect = lambda rows: rows  # Identity sanitise

    fast_result = {"site_id": "site-1", "type": "dns", "status": "ok"}  # Sample fast-mode row
    deps.execute_fn.return_value = (
        [[fast_result]],  # successful_results: list-of-lists
        [],  # failed_sites: empty
    )  # Pool returns one successful site with one row

    # Fast-path goes through _resolve_site_ids with fast=True; GatewayExportUtils acts as fallback
    deps.GatewayExportUtils._get_site_ids_with_devices.return_value = ["site-1"]  # Fallback API path
    # Patch csv.DictReader to return empty so the cache-CSV fast path returns [] and falls through
    with (
        patch("src.refactors.serial_cc.test_results_by_site.csv.DictReader", return_value=[]),  # Empty CSV
        patch("src.refactors.serial_cc.test_results_by_site.open", MagicMock()),  # Avoid real file access
    ):
        GatewayTestResultsService.execute(fast=True)  # Execute service in fast mode

    deps.execute_fn.assert_called_once()  # Pool must be used in fast mode
    deps.DataExporter.write_with_format_selection.assert_called_once()  # CSV must be written
    call_args = deps.DataExporter.write_with_format_selection.call_args.args  # Inspect positional args
    assert call_args[1] == "AllGatewayTestResults.csv"  # Filename contract preserved in fast mode


@patch("src.refactors.serial_cc.test_results_by_site._resolve_runtime_dependencies")
def test_fetch_site_tests_returns_empty_on_api_error(mock_resolve):
    """_fetch_site_tests is non-fatal: returns empty list when API raises."""
    deps = DummyDeps()  # Create synthetic dependency bundle
    mock_resolve.return_value = deps  # Inject synthetic dependencies
    deps.mistapi.api.v1.sites.synthetic_test.searchSiteSyntheticTest.side_effect = RuntimeError(
        "timeout"
    )  # Simulate API failure so non-fatal guard is exercised

    result = GatewayTestResultsService._fetch_site_tests(deps, "site-bad", connection_semaphore=None)

    assert result == []  # Non-fatal API error must yield empty list, not exception


@patch("src.refactors.serial_cc.test_results_by_site._resolve_runtime_dependencies")
def test_fetch_site_tests_tags_results_with_site_id(mock_resolve):
    """_fetch_site_tests injects site_id into every returned row."""
    deps = DummyDeps()  # Create synthetic dependency bundle
    mock_resolve.return_value = deps  # Inject synthetic dependencies
    response_mock = MagicMock()  # Mock API response object
    response_mock.data = {"results": [{"type": "arp"}, {"type": "dns"}]}  # Two untagged rows
    deps.mistapi.api.v1.sites.synthetic_test.searchSiteSyntheticTest.return_value = response_mock

    results = GatewayTestResultsService._fetch_site_tests(deps, "site-xyz", connection_semaphore=None)

    assert len(results) == 2  # Both rows must be returned
    assert all(r["site_id"] == "site-xyz" for r in results)  # Every row must be tagged with site_id
