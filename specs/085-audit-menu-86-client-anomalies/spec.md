# Audit: Menu #86 — Export Site Client Anomaly Events (SiteAnomalyExporter.client_anomaly_events)

Target: SiteAnomalyExporter.client_anomaly_events in MistHelper.py
Location: Approx. MistHelper.py lines 14978-15091

Summary:
- Discovers client anomaly metrics and calls mistapi.api.v1.sites.anomaly.listSiteAnomalyEvents for client-scoped metrics, tagging data_type 'client_anomaly_events'.
- Writes to SiteClientAnomalyEvents_[Site]_[Client].csv via DataExporter.save_data_to_output.

Checks:
- ENDPOINT_PRIMARY_KEY_STRATEGIES: No strategy entry detected for the anomaly endpoints used.
- DataExporter: Uses save_data_to_output; does not call write_with_format_selection with api_function_name.
- Tests: No tests found for client_anomaly_events.

Conclusion: SQL export compliance: FAIL. Test coverage: MISSING.
