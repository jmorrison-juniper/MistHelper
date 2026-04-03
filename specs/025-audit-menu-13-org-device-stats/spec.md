# Audit: Menu 13 — OrgDeviceStatsExporter.device_stats

Summary
- Menu option #13: "Export statistics for all devices in the organization"
- Function: OrgDeviceStatsExporter.device_stats (MistHelper.py)
- Category: data_export

Current state analysis
- OrgDeviceStatsExporter.device_stats exists at MistHelper.py (class at line ~12165).
- It calls APIDataFetcher with api_call=mistapi.api.v1.orgs.stats.listOrgDevicesStats and filename "OrgDeviceStats.csv".
- APIDataFetcher executes, fetches paginated data, and calls DataExporter.export_with_processing(..., api_function_name=api_name).

Issues found
- No direct tests target OrgDeviceStatsExporter.device_stats specifically. Tests/ directory contains general export tests and PK strategy unit tests, but none exercise menu #13.
- device_stats uses APIDataFetcher (indirection) instead of calling DataExporter.write_with_format_selection directly. This is acceptable provided APIDataFetcher passes the api_function_name (it does).

SQL export compliance check
- ENDPOINT_PRIMARY_KEY_STRATEGIES contains an entry for "listOrgDevicesStats" (composite_pk with primary_key ["device_id","timestamp"]) at MistHelper.py (around line ~3380).
- APIDataFetcher sets api_name = self.api_call.__name__ and passes api_function_name down to DataExporter.export_with_processing -> save_data_to_output -> DataExporter.write_with_format_selection. Therefore the SQLite path receives api_function_name="listOrgDevicesStats" and will use the PK strategy for upserts. Compliance: PASS.

Test coverage
- No unit or integration tests specific to menu #13 found in tests/.
- tests/unit/test_pk_strategies.py includes a strategy entry for listOrgDevicesStats (good).
- tests cover export scaffolding in a generic way (test_exports.py) but do not validate that device_stats passes api_function_name to DataExporter or that SQLite upsert behavior is correct for this endpoint.

Acceptance criteria
- Unit test(s) added that assert OrgDeviceStatsExporter.device_stats triggers data export and passes api_function_name="listOrgDevicesStats" to the DataExporter path.
- Integration-style test that simulates OUTPUT_FORMAT="sqlite" and asserts SQLiteDatabaseWriter is invoked with table "OrgDeviceStats" and api_function_name="listOrgDevicesStats" (or an appropriate mock of SQLiteDatabaseWriter.write).
- No code changes required beyond tests; documentation updated to reference test coverage for menu #13.
