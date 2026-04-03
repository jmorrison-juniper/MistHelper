Title: Audit — Menu 16: Export synthetic test results for all gateways

Summary
- Location: MistHelper.py -> class GatewayTestExporter -> synthetic_tests (lines ~21413).
- Purpose: Exports per-gateway synthetic test statistics to CSV.

Current state analysis
- The method collects synthetic test results for each gateway (getSiteDeviceSyntheticTest) and aggregates them into `all_stats`.
- Output uses DataExporter.save_data_to_output(sanitized, filename) to write CSV only.
- No api_function_name is passed to the exporter; therefore SQLite "dual output" path (DataExporter.write_with_format_selection) is not invoked.
- ENDPOINT_PRIMARY_KEY_STRATEGIES exists (starts at line 3260) but contains no entries for getSiteDeviceSyntheticTest or searchSiteSyntheticTest.

Issues found
1. SQL export compliance: synthetic_tests does NOT call DataExporter.write_with_format_selection(..., api_function_name=...). This prevents consistent SQLite exports and upsert behavior.
2. Missing primary key strategy: ENDPOINT_PRIMARY_KEY_STRATEGIES lacks an entry for relevant synthetic test API(s) (e.g., "getSiteDeviceSyntheticTest", "searchSiteSyntheticTest").
3. Test coverage: No unit tests found targeting GatewayTestExporter.synthetic_tests or menu 16. tests/test_exports.py covers other exporters but not this one.
4. Ambiguous data model: getSiteDeviceSyntheticTest responses may lack a stable primary id; strategy must be chosen carefully (composite key vs auto-increment).

SQL export compliance check
- Requirement: All structured exports must call DataExporter.write_with_format_selection(data, filename, api_function_name=...) so SQLite writes use ENDPOINT_PRIMARY_KEY_STRATEGIES for table schema and upsert semantics.
- Current code uses DataExporter.save_data_to_output -> CSV only. Non-compliant.

Test coverage
- No tests for synthetic_tests found under tests/*. Unit tests should assert the exporter is invoked with api_function_name and that record counts are correct for both fast and non-fast paths.

Acceptance criteria
- The method must be updated to call DataExporter.write_with_format_selection(..., api_function_name="getSiteDeviceSyntheticTest") when exporting per-device synthetic stats (menu 16), and/or use "searchSiteSyntheticTest" for site-level exports where appropriate.
- ENDPOINT_PRIMARY_KEY_STRATEGIES must include a mapping for the chosen api_function_name(s) with a documented primary key strategy.
- Unit tests added: at least one test exercising the sequential path and one exercising the fast/concurrent path; both must mock API responses and assert DataExporter.write_with_format_selection was called with correct parameters and record counts.
- No functional change to CSV contents beyond routing through write_with_format_selection.

Notes/assumptions
- We'll assume getSiteDeviceSyntheticTest returns per-device test records that can be upserted using a composite key (device_id + timestamp) if a timestamp exists; otherwise, use auto-increment with a unique constraint (device_id + site_id).
- Implementation changes are OUT OF SCOPE for this audit — this spec documents required work only.
