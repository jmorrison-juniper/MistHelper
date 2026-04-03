# Audit: Menu #84 — Export Site Anomaly Events (SiteAnomalyExporter.anomaly_events)

Target: SiteAnomalyExporter.anomaly_events in MistHelper.py
Location: Approx. MistHelper.py lines 14782-14875

Summary:
- Dynamically discovers anomaly metrics via AnomalyMetricsDiscovery and calls mistapi.api.v1.sites.anomaly.listSiteAnomalyEvents for each metric.
- Aggregates and writes to SiteAnomalyEvents_[Site].csv using DataExporter.save_data_to_output.

Checks:
- ENDPOINT_PRIMARY_KEY_STRATEGIES: No entry for listSiteAnomalyEvents found in strategies.
- DataExporter: Uses save_data_to_output; no api_function_name provided.
- Tests: No tests found covering anomaly_events.

Conclusion: SQL export compliance: FAIL. Test coverage: MISSING.
