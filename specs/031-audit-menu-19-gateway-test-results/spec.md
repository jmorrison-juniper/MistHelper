1. Title: Audit — Menu 19: Export all synthetic test results (including speed tests) for gateways

2. Summary
- Location: MistHelper.py -> class GatewayTestExporter -> test_results_by_site (lines ~21601).
- Purpose: Export aggregated synthetic test results (including speed tests) for sites that have gateways.

3. Current state analysis
- Method collects site-level synthetic test results via mistapi.api.v1.sites.synthetic_test.searchSiteSyntheticTest and aggregates into `all_results`.
- Output pipeline uses DataExporter.save_data_to_output(sanitized, filename) (CSV-only) rather than DataExporter.write_with_format_selection(..., api_function_name=...).
- ENDPOINT_PRIMARY_KEY_STRATEGIES (starts at line 3260) contains no explicit entry for "searchSiteSyntheticTest"; fallback strategy will be used for SQL exports.

4. Issues found
1) SQL export compliance: method does not call DataExporter.write_with_format_selection with api_function_name; SQLite export/upsert behavior will not be configured.
2) Missing PK strategy: ENDPOINT_PRIMARY_KEY_STRATEGIES lacks a dedicated mapping for "searchSiteSyntheticTest" (site-level synthetic tests).
3) Test coverage: No unit tests detected targeting GatewayTestExporter.test_results_by_site; existing specs reference menu 16 but not menu 19.

5. Acceptance criteria
- Update method to call DataExporter.write_with_format_selection(sanitized, filename, api_function_name="searchSiteSyntheticTest").
- Add ENDPOINT_PRIMARY_KEY_STRATEGIES entry for "searchSiteSyntheticTest" using a composite_pk (e.g., ["id","site_id","timestamp"]) with appropriate indexes.
- Add unit tests covering both fast and non-fast paths, asserting api_function_name usage and record counts.

6. Notes/assumptions
- searchSiteSyntheticTest returns time-series records; composite_pk is preferred.
- Implementation changes are OUT OF SCOPE for this audit. This spec documents required remediation only.
