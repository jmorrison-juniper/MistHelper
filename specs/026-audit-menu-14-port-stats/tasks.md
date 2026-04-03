Tasks (actionable)

T001 - Add unit tests for fast mode
- File: tests/unit/test_device_port_stats.py
- Implement test_device_port_stats_fast_mode_writes_with_site_api
- Monkeypatches:
  - MistHelper.ConfigUtils.get_cached_or_prompted_org_id -> returns "org1"
  - MistHelper.CacheUtils.check_and_generate_csv -> raise Exception to force API fetch OR monkeypatch to no-op and provide a fake CSV path
  - MistHelper.mistapi.api.v1.sites.stats.searchSiteSwOrGwPorts -> lambda returning MagicMock()
  - MistHelper.mistapi.get_all -> returns sample port stats list (e.g., [{"device_id":"d1","port_id":"p1","timestamp":"2026-01-01T00:00:00Z"}])
  - MistHelper.DataExporter.save_data_to_output -> fake function capturing filename and api_function_name
- Assertions: filename == "OrgDevicePortStats.csv"; api_function_name == "searchSiteSwOrGwPorts"; record count == 1
- Estimate: 1 hour

T002 - Add unit tests for non-fast mode
- Same test file, implement test_device_port_stats_nonfast_writes_with_org_api
- Monkeypatch:
  - MistHelper.ConfigUtils.get_cached_or_prompted_org_id -> "org1"
  - MistHelper.mistapi.api.v1.orgs.stats.searchOrgSwOrGwPorts -> lambda returning MagicMock()
  - MistHelper.mistapi.get_all -> returns sample list of port stats
  - MistHelper.DataExporter.save_data_to_output -> capture call
- Assertions: filename == "OrgDevicePortStats.csv"; api_function_name == "searchOrgSwOrGwPorts"; record count == mocked
- Estimate: 1 hour

T003 - Add edge-case tests
- Test empty API response handling (no data -> CSV not created). Ensure DataExporter.save_data_to_output is not called and a warning logged.
- Estimate: 30 minutes

T004 - CI validation
- Run pytest full suite; fix any flakiness.
- Ensure no external API calls made; all mistapi and file I/O stubbed.
- Estimate: 30–60 minutes

T005 - Documentation
- Update specs index or README if needed to list added tests.
- Estimate: 15 minutes

Acceptance criteria
- All tests pass locally and in CI.
- Tests verify api_function_name is passed to DataExporter for both fast and non-fast paths.
- No changes to production code required.

Owner: engineering (junior dev) with reviewer senior maintainer

