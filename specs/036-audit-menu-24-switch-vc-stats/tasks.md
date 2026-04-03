Tasks for fixing and testing Menu #24 (Audit 036)

Task 1: Pass api_function_name in exporter (code change)
- Modify MistHelper.py:OrgDeviceStatsExporter.switch_vc_stats
- Change DataExporter.save_data_to_output(all_vc_stats, "OrgSwitchVCStats.csv")
  to: DataExporter.save_data_to_output(all_vc_stats, "OrgSwitchVCStats.csv", api_function_name="getSiteDeviceVirtualChassis")
- Update logging to include api_function_name where helpful.
- Update unit tests accordingly.
- Update git commit message: "version YY.MM.DD.HH.MM - menu24: export switch VC stats SQL strategy"

Task 2: Add ENDPOINT_PRIMARY_KEY_STRATEGIES entry
- Insert mapping for "getSiteDeviceVirtualChassis" in ENDPOINT_PRIMARY_KEY_STRATEGIES near related site/device endpoints (around line 3260)
- Suggested config:
  "getSiteDeviceVirtualChassis": {
     "type": "natural_pk",
     "primary_key": ["id"],
     "indexes": ["site_id", "vc_mac", "mac", "serial", "model"],
     "unique_constraints": [],
     "description": "Virtual chassis info merged with inventory; use device id as natural key"
  }
- Validate JSON/dict formatting and run python -m py_compile MistHelper.py

Task 3: Add unit tests (tests/test_export_switch_vc_stats.py)
- Write tests for CSV output (OUTPUT_FORMAT=csv)
- Write tests for SQLite output (OUTPUT_FORMAT=sqlite), using a temp DB path inside the repo
- Mock mistapi.api.v1.sites.devices.getSiteDeviceVirtualChassis to return deterministic responses
- Assert CSV file contents and SQLite schema/rows

Task 4: CI and validation
- Run python -m py_compile MistHelper.py
- Run pytest
- Ensure new tests pass and no regressions

Task 5: Documentation & changelog
- Update README.md version and add short note about menu 24 audit and SQL strategy

Notes
- Do NOT change behavior of switch_vc_stats other than adding the api_function_name argument. Keep fast-path/cache behavior unchanged.
- Use existing testing patterns (monkeypatch, IS_TEST_MODE) as seen in tests/test_readopt.py

Owner: repo maintainer
Priority: High (SQL export compliance and test coverage)

