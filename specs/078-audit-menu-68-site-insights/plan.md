Plan to remediate menu #68:

1. Add ENDPOINT_PRIMARY_KEY_STRATEGIES entry for getSiteInsightMetrics or for an appropriate time-series composite key (e.g., ['metric_type','site_id','timestamp']).
2. Update SiteExportUtils.insight_metrics to call DataExporter.write_with_format_selection(processed, filename, api_function_name="getSiteInsightMetrics").
3. Add unit tests (mock DataExporter) to assert write_with_format_selection usage and ensure CSV output still works.
4. Validate with py_compile and pytest.
