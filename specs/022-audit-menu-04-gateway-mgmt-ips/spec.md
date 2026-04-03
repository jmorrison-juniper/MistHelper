# Audit: Menu Option #4 - Export gateway management overlay IPs grouped by template association

## Current state analysis
- Location: MistHelper.py, class `GatewayExportUtils`, method `management_ips` (lines ~22044 onwards).
- The method collects data from cached CSVs (SiteList.csv, OrgGatewayTemplates.csv, GatewaysWithSiteInfo.csv, AllSiteGatewayConfigs.csv), correlates gateway records, and writes output to `GatewayManagementIPs.csv` via `DataExporter.save_data_to_output()`.

## Issues found
1. SQL export compliance:
   - Function uses `DataExporter.save_data_to_output(...)` not `DataExporter.write_with_format_selection(..., api_function_name=...)`.
   - No `api_function_name` parameter is provided; therefore SQLite upsert/PK strategy is not applied.
   - No matching entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES` for this derived export (no key such as `GatewayManagementIPs`).

2. Test coverage:
   - No unit or integration tests found in `tests/` referencing `management_ips` or `GatewayExportUtils`.
   - Existing `test_pk_strategies.py` validates structure but does not include this endpoint.

3. Data quality / robustness:
   - Device lookup creation contains a line `{dev.get("name"): dev for dev in gateway_devices}` that discards the lookup result (no variable assignment).
   - Management IP lookup is keyed by device name; name collisions or name mismatches between configs and inventory may cause missing IPs.
   - No explicit handling for multiple management IPs per gateway.

## SQL export compliance check
- Requirement: Exports must call `DataExporter.write_with_format_selection(..., api_function_name="<endpoint>")` so the exporter can apply `ENDPOINT_PRIMARY_KEY_STRATEGIES` for SQLite upsert behavior.
- Current state: method does not use `write_with_format_selection()` and no PK strategy key exists for this export.
- Result: Not compliant — data will be written only to CSV, not to SQLite with upsert semantics.

## Test coverage
- No tests detected for this menu option. Coverage: 0% for this feature.

## Acceptance criteria
1. The `management_ips` export is updated to call `DataExporter.write_with_format_selection(final_results, filename, api_function_name="..." )` (string chosen to match PK strategy).
2. An appropriate entry is added to `ENDPOINT_PRIMARY_KEY_STRATEGIES` mapping explaining PK columns and indexes for the export.
3. Unit tests covering:
   - Correct CSV/SQLite invocation (mocking DataExporter) and that `api_function_name` is passed.
   - Data correlation correctness for typical, missing, and duplicate name cases.
4. Fix the discarded device lookup (assign it to a variable) and add defensive checks for name collisions.
5. Documentation: Update README or specs referencing dual-output and list the new PK strategy.


-- End of analysis
