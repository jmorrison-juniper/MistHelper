Plan: Remediate Menu #24 export for SQL compliance and test coverage

Objective

Make OrgDeviceStatsExporter.switch_vc_stats fully compliant with SQL export strategy and add unit tests to ensure behavior is correct for CSV and SQLite outputs.

Assumptions

- The merged entry in switch_vc_stats includes an 'id' field coming from OrgInventory.csv (inventory rows include device 'id').
- Desired canonical API function name to use in endpoint strategy is "getSiteDeviceVirtualChassis" (matches mistapi operationId).
- Tests can run in isolation by setting IS_TEST_MODE and monkeypatching mistapi calls.

Steps (implementation NOT included in this ticket)

1. Code changes
   - Modify OrgDeviceStatsExporter.switch_vc_stats to call DataExporter.save_data_to_output(all_vc_stats, "OrgSwitchVCStats.csv", api_function_name="getSiteDeviceVirtualChassis") or DataExporter.write_with_format_selection(..., api_function_name=...).
   - Add an explicit entry to ENDPOINT_PRIMARY_KEY_STRATEGIES for "getSiteDeviceVirtualChassis" near related site/device endpoints. Suggested entry template:
     {
       "getSiteDeviceVirtualChassis": {
         "type": "natural_pk",
         "primary_key": ["id"],
         "indexes": ["site_id", "vc_mac", "mac", "serial", "model"],
         "unique_constraints": [],
         "description": "Virtual chassis info merged with inventory; use device id as natural key"
       }
     }
   - Ensure consistent api_function_name string is used (no module prefixes).

2. Tests
   - Create a new test file tests/test_export_switch_vc_stats.py
   - Test cases:
     a) CSV mode: monkeypatch mistapi getSiteDeviceVirtualChassis to return deterministic data for two switches; set OUTPUT_FORMAT="csv"; run switch_vc_stats(); assert OrgSwitchVCStats.csv exists and contains expected rows/headers.
     b) SQLite mode: set OUTPUT_FORMAT="sqlite" (and DATABASE_PATH to a temp file inside project), monkeypatch API to return test data; run switch_vc_stats(); assert SQLite table created with expected primary key and indexes (PRAGMA table_info and PRAGMA index_list); assert rows inserted.
     c) Edge cases: inventory missing site_id/device_id entries, API raises exception for a device (ensure those are logged and skipped), empty result set (no CSV/DB created).

3. Documentation
   - Update README or changelog entry noting addition of SQL strategy and tests.

4. Validation
   - Run python -m py_compile MistHelper.py
   - Run pytest -q and confirm new tests pass
   - Run any existing lints/tests to ensure no regressions

Estimated effort: 1-2 hours for changes and tests, additional time for CI validation.
