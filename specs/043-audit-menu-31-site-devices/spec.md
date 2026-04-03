# Audit: Menu 31 — Export device list for a selected site

Summary:
- Location: SiteDeviceExporter.devices (MistHelper.py lines ~14199-14222)
- API used: mistapi.api.v1.sites.devices.listSiteDevices
- ENDPOINT_PRIMARY_KEY_STRATEGIES: contains "listSiteDevices" (natural_pk on ['id']) — present
- Data export call: DataExporter.save_data_to_output(...) — does NOT pass api_function_name

Findings:
- Primary key strategy exists for listSiteDevices (PASS).
- The exporter uses DataExporter.save_data_to_output instead of DataExporter.write_with_format_selection. This means SQLite exports will not use ENDPOINT_PRIMARY_KEY_STRATEGIES for upsert schema; the default strategy will be used (FAIL).
- No unit tests found covering SiteDeviceExporter.devices (coverage gap).

Risk/Severity: Medium — exports work as CSV today but SQLite upserts may be incorrect or lack proper PK/indexing.

Recommendation (high level): Replace DataExporter.save_data_to_output(...) with DataExporter.write_with_format_selection(sanitized_data, filename, api_function_name="listSiteDevices") and add unit/integration tests to verify CSV and SQLite outputs.