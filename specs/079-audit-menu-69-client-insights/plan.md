Plan to remediate menu #69:

1. Add PK strategy entry for getSiteInsightMetricsForClient (composite key e.g., ['client_mac','metric_type','timestamp']).
2. Update SiteClientExporter.client_insights to call DataExporter.write_with_format_selection(processed, filename, api_function_name="getSiteInsightMetricsForClient").
3. Add unit tests mocking API and DataExporter; assert SQL path and CSV fallback.
4. Run py_compile and pytest.
