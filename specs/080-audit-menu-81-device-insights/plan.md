Plan to remediate menu #81:

1. Add ENDPOINT_PRIMARY_KEY_STRATEGIES entry for getSiteInsightMetricsForDevice (composite_pk). Recommended keys: ['device_mac','metric_type','timestamp'].
2. Update SiteExportUtils.device_insights to call DataExporter.write_with_format_selection(processed, filename, api_function_name="getSiteInsightMetricsForDevice").
3. Add unit tests (tests/unit/test_device_insights.py) mocking API responses and DataExporter.
4. Run validation and tests.
