Implementation Plan: Audit Remediation for Menu 14 (device_port_stats)

Goal
Add deterministic unit tests covering both fast and non-fast paths for OrgDeviceStatsExporter.device_port_stats that assert correct usage of DataExporter for CSV/SQLite exports and record messaging.

High-level steps
1. Create unit tests: tests/unit/test_device_port_stats.py with two test cases:
   - test_device_port_stats_fast_mode_writes_with_site_api: simulate cached site list or force API site fetch; mock mistapi.api.v1.sites.stats.searchSiteSwOrGwPorts and mistapi.get_all to return sample port records; monkeypatch DataExporter.save_data_to_output to capture filename and api_function_name.
   - test_device_port_stats_nonfast_writes_with_org_api: mock mistapi.api.v1.orgs.stats.searchOrgSwOrGwPorts and mistapi.get_all; monkeypatch DataExporter.save_data_to_output similarly; call device_port_stats(fast=False).

2. Test stubbing guidance:
   - Avoid real file I/O: monkeypatch CacheUtils.check_and_generate_csv to raise or to be a no-op and monkeypatch FilePathUtils.get_csv_path when needed.
   - Monkeypatch ConfigUtils.get_cached_or_prompted_org_id to a fixed org id.
   - Ensure IS_TEST_MODE toggles if required to bypass interactive prompts.

3. Assertions:
   - DataExporter.save_data_to_output called once with filename "OrgDevicePortStats.csv" and api_function_name matching each path.
   - Recorded row counts equal to length of mocked mistapi.get_all return.

4. Run tests locally: pytest -q tests/unit/test_device_port_stats.py

5. Update specs/ and README if test additions change coverage metrics.

Estimated effort: 2–3 hours (write tests, run and fix flakiness, push changes)

