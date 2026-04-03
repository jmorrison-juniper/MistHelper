Tasks for Audit & Test Coverage (Menu 13)

1. Create unit test file
   - Path: tests/unit/test_menu_13_device_stats.py
   - Implement test_device_stats_calls_export(monkeypatch)
     - Patch ConfigUtils.get_cached_or_prompted_org_id to return "org-test"
     - Patch mistapi.api.v1.orgs.stats.listOrgDevicesStats to return MagicMock()
     - Patch mistapi.get_all to return [{"device_id":"d1","timestamp":"2026-01-01T00:00:00Z"}]
     - Patch DataExporter.save_data_to_output to record (data, filename, api_function_name)
     - Call OrgDeviceStatsExporter.device_stats()
     - Assert filename == "OrgDeviceStats.csv"; api_function_name == "listOrgDevicesStats"; data length == 1
   - Estimate: 1 hour

2. Create SQLite-path test
   - Path: tests/unit/test_menu_13_device_stats_sqlite.py (or same file)
   - Set MistHelper.OUTPUT_FORMAT = "sqlite" in test scope
   - Patch SQLiteDatabaseWriter.write to a stub that records table_name and api_function_name (constructor args)
   - Run OrgDeviceStatsExporter.device_stats()
   - Assert SQLiteDatabaseWriter called with table_name "OrgDeviceStats" and api_function_name "listOrgDevicesStats"
   - Estimate: 1 hour

3. Add edge-case tests
   - No-data case: mistapi.get_all returns [] → assert no write called
   - Malformed data: mistapi.get_all returns [None, "string", {valid}] → assert only dicts exported
   - Estimate: 1 hour

4. Run full test suite locally
   - python -m pytest -q
   - Fix any failures or flakiness due to global state or file I/O. Use tmp_path for file outputs as needed.
   - Estimate: 30-60 minutes

5. Documentation update
   - Add short note in README or specs directory that Menu #13 now has unit tests and what they verify.
   - Estimate: 15 minutes

6. Review & Commit
   - Commit changes with message: "version YY.MM.DD.HH.MM - add tests for menu 13 device stats"
   - Include Co-authored-by trailer
   - Push branch and open PR (if workflow requires)
   - Estimate: 30 minutes

Priority: Implement tests in tasks 1-2 first (blocking). Edge cases and docs are secondary.
