# Audit: Menu 33 — Export virtual chassis information for a selected switch device

Summary:
- Location: SiteDeviceExporter.device_virtual_chassis (MistHelper.py lines ~14158-14196)
- API used: mistapi.api.v1.sites.devices.getSiteDeviceVirtualChassis
- ENDPOINT_PRIMARY_KEY_STRATEGIES: No explicit entry for "getSiteDeviceVirtualChassis" was found in MistHelper.py mapping (FAIL).
- Data export call: DataExporter.save_data_to_output(...) — does NOT pass api_function_name

Findings:
- Missing PK strategy: ENDPOINT_PRIMARY_KEY_STRATEGIES lacks a mapping for getSiteDeviceVirtualChassis. Without it, SQLite exports will fall back to default auto-increment PK and lack useful indexes (FAIL).
- The exporter uses DataExporter.save_data_to_output instead of DataExporter.write_with_format_selection; even after adding PK strategy, the exporter must pass api_function_name to leverage it (FAIL).
- Minimal/no unit tests found covering this exporter (coverage gap).

Risk/Severity: Medium — Virtual chassis data is rare but important for VC member tracking; lacking PK/indexes reduces utility in SQLite exports.

Recommendation: Add an ENDPOINT_PRIMARY_KEY_STRATEGIES entry for "getSiteDeviceVirtualChassis" (see plan), and update exporter to call DataExporter.write_with_format_selection(..., api_function_name="getSiteDeviceVirtualChassis"). Add unit and integration tests.