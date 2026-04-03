Plan for implementing tests and verification for Menu 13 (OrgDeviceStatsExporter.device_stats)

Goal
- Add unit and integration-style tests to validate correctness, SQL export compliance, and regression protection for Menu #13.

Assumptions
- MistHelper.ConfigUtils.get_cached_or_prompted_org_id can be monkeypatched.
- mistapi.get_all and the specific API function (mistapi.api.v1.orgs.stats.listOrgDevicesStats) can be monkeypatched to return synthetic data.
- SQLiteDatabaseWriter is mockable to avoid touching a real DB in unit tests.

High-level steps
1. Add unit test that:
   - Monkeypatches ConfigUtils.get_cached_or_prompted_org_id to return test org id.
   - Monkeypatches mistapi.get_all to return a small list of dicts (e.g., one record).
   - Monkeypatches mistapi.api.v1.orgs.stats.listOrgDevicesStats to return a dummy response object.
   - Monkeypatches DataExporter.save_data_to_output (or DataExporter.write_with_format_selection) to capture the filename and api_function_name.
   - Calls OrgDeviceStatsExporter.device_stats(fast=True/False) and asserts recorded filename == "OrgDeviceStats.csv" and api_function_name == "listOrgDevicesStats" and row count matches.

2. Add a test for SQLite flow (integration-style, unit with mocks):
   - Set OUTPUT_FORMAT to "sqlite" (monkeypatch module-level variable) for test scope.
   - Monkeypatch SQLiteDatabaseWriter.write to capture the table_name and api_function_name passed via its constructor.
   - Execute OrgDeviceStatsExporter.device_stats and assert SQLiteDatabaseWriter.write was called and constructor received api_function_name "listOrgDevicesStats" and table_name "OrgDeviceStats".

3. Add negative/edge test cases:
   - No data returned (mistapi.get_all returns []) → device_stats should log warning and not attempt write.
   - Malformed data (non-dict entries) → ensure export filters and does not crash.

4. Run test suite; fix flakiness by isolating environment, ensuring temp files are written to data/ and cleaned up.

Deliverables
- tests/unit/test_menu_13_device_stats.py with the three test cases described.
- Short README note in specs/ summarizing verification steps.

Timeline & risk
- Estimated ~2-3 hours to implement tests and run locally. Low risk: no production code changes required.
