# Audit: Menu 32 — Export device statistics for a selected site

Summary:
- Location: SiteDeviceExporter.device_stats (MistHelper.py lines ~14114-14143)
- API used: mistapi.api.v1.sites.stats.listSiteDevicesStats
- ENDPOINT_PRIMARY_KEY_STRATEGIES: contains "listSiteDevicesStats" (composite_pk ['device_id','timestamp']) — present
- Data export call: DataExporter.save_data_to_output(...) — does NOT pass api_function_name

Findings:
- Primary key strategy exists for listSiteDevicesStats (PASS).
- The exporter uses DataExporter.save_data_to_output instead of DataExporter.write_with_format_selection; SQLite upsert semantics will not use defined composite PK (FAIL).
- No unit tests found covering SiteDeviceExporter.device_stats (coverage gap).

Risk/Severity: Medium-High — statistics are time-series data and require correct composite PKs for dedup/upsert behavior.

Recommendation: Replace DataExporter.save_data_to_output(...) with DataExporter.write_with_format_selection(sanitized_data, filename, api_function_name="listSiteDevicesStats"). Add unit and integration tests to assert CSV and SQLite behave per ENDPOINT_PRIMARY_KEY_STRATEGIES.