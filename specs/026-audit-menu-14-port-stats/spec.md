Audit: Menu 14 — Export port-level statistics for switches and gateways

Summary
- Target function: OrgDeviceStatsExporter.device_port_stats (defined in MistHelper.py).
- Purpose: Verify SQL export compliance, test coverage, and document remediation plan.

Current state analysis
- Located OrgDeviceStatsExporter.device_port_stats (lines ~12215 onwards). It supports two modes: fast (site-parallel) and non-fast (org-level pagination).
- Fast mode fetches per-site data via mistapi.api.v1.sites.stats.searchSiteSwOrGwPorts and saves using DataExporter.save_data_to_output(..., api_function_name="searchSiteSwOrGwPorts").
- Non-fast mode uses APIDataFetcher with api_call=mistapi.api.v1.orgs.stats.searchOrgSwOrGwPorts which flows to DataExporter.export_with_processing and ultimately DataExporter.write_with_format_selection with api_function_name set to the API function name.

SQL export compliance
- ENDPOINT_PRIMARY_KEY_STRATEGIES contains entries for both "searchOrgSwOrGwPorts" and "searchSiteSwOrGwPorts" (composite_pk: ["device_id","port_id","timestamp"]).
- Both fast and non-fast code paths provide api_function_name when invoking DataExporter.save_data_to_output/export_with_processing. DataExporter.write_with_format_selection accepts api_function_name and will route to SQLite writer.
- Conclusion: SQL export compliance present. The correct primary key strategies exist for org- and site-level calls.

Issues found
1. No unit or integration tests exercise OrgDeviceStatsExporter.device_port_stats (menu 14). Tests directory contains generic export tests (tests/test_exports.py) but none target this function.
2. Fast-mode path does extra file I/O (tries cached SiteList.csv). Tests will need to stub CacheUtils/FilePathUtils or force API fetch path.
3. Minor: code uses DataExporter.save_data_to_output rather than direct write_with_format_selection; save_data_to_output delegates correctly, but tests should assert the final write call and api_function_name value.

Test coverage
- Coverage: none for device_port_stats. Existing patterns in tests/test_exports.py show how to monkeypatch mistapi.get_all and DataExporter.save_data_to_output.

Acceptance criteria
- Unit tests added for both fast and non-fast modes validating:
  - DataExporter.write_with_format_selection (via save_data_to_output) is called with correct api_function_name ("searchSiteSwOrGwPorts" for fast; "searchOrgSwOrGwPorts" for non-fast).
  - Output CSV filename is OrgDevicePortStats.csv and record counts match mocked API responses.
- ENDPOINT_PRIMARY_KEY_STRATEGIES mapping contains both keys (already present).
- Tests pass in CI without network calls (all mistapi calls and file I/O stubbed).

References
- MistHelper.py: device_port_stats implementation (~lines 12215-12433).
- ENDPOINT_PRIMARY_KEY_STRATEGIES (~lines 3360-3415).

