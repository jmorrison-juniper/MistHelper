Plan to remediate menu #86:

1. Add PK strategy entries for client anomaly endpoints (composite keys e.g., ['client_mac','metric_name','timestamp']).
2. Update client_anomaly_events to call DataExporter.write_with_format_selection(processed, filename, api_function_name="listSiteAnomalyEvents").
3. Add unit tests tests/unit/test_client_anomaly_events.py to cover empty and non-empty flows.
4. Run py_compile and pytest; update documentation.
