# Audit: Menu #85 — Export Site Device Anomaly Events (SiteAnomalyExporter.device_anomaly_events)

Target: SiteAnomalyExporter.device_anomaly_events in MistHelper.py
Location: Approx. MistHelper.py lines 14885-15000

Summary:
- Prompts for site and device, iterates anomaly metrics, and calls mistapi.api.v1.sites.anomaly.listSiteAnomalyEvents(apisession, site_id, metric) then filters device-specific entries.
- Writes to SiteDeviceAnomalyEvents_[Site]_[Device].csv using DataExporter.save_data_to_output.

Checks:
- ENDPOINT_PRIMARY_KEY_STRATEGIES: No entry for listSiteAnomalyEvents or device-specific anomaly endpoints present.
- DataExporter: Uses save_data_to_output; missing api_function_name.
- Tests: No tests found for device_anomaly_events.

Conclusion: SQL export compliance: FAIL. Test coverage: MISSING.
