Plan to remediate menu #84:

1. Add ENDPOINT_PRIMARY_KEY_STRATEGIES entry for listSiteAnomalyEvents (composite_pk: ['metric_name','site_id','timestamp']).
2. Update SiteAnomalyExporter.anomaly_events to call DataExporter.write_with_format_selection(processed, filename, api_function_name="listSiteAnomalyEvents").
3. Add unit tests mocking AnomalyMetricsDiscovery and API responses.
4. Validate via py_compile and pytest.
