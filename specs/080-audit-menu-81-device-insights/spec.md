# Audit: Menu #81 — Export device insights for a site (SiteExportUtils.device_insights)

Target: SiteExportUtils.device_insights in MistHelper.py
Location: Approx. MistHelper.py lines 15296-15399

Summary:
- Prompts site and device, retrieves device-scoped metrics using mistapi.api.v1.sites.insights.getSiteInsightMetricsForDevice.
- Writes results to SiteDeviceInsights_[Site]_[Device].csv via DataExporter.save_data_to_output.

Checks:
- ENDPOINT_PRIMARY_KEY_STRATEGIES: No entry found for getSiteInsightMetricsForDevice in strategies.
- DataExporter: Uses save_data_to_output; missing api_function_name for SQL export.
- Tests: No associated tests found.

Conclusion: SQL export compliance: FAIL. Test coverage: MISSING.
