Title: Audit - Menu 12: Org Inventory Exporter (OrgInventoryExporter.inventory)

Current State Analysis
- Location: MistHelper.py (class OrgInventoryExporter, inventory method at ~line 11760).
- Implementation: OrgInventoryExporter.inventory() constructs an APIDataFetcher with api_call=mistapi.api.v1.orgs.inventory.getOrgInventory and filename "OrgInventory.csv" then calls .execute().
- ENDPOINT_PRIMARY_KEY_STRATEGIES: Contains an entry for "getOrgInventory" (defined at ~line 3263) with type "natural_pk" and primary_key ["id"].
- Data export flow: APIDataFetcher -> DataExporter.export_with_processing -> DataExporter.save_data_to_output -> DataExporter.write_with_format_selection. APIDataFetcher sets api_function_name to self.api_call.__name__ ("getOrgInventory").

Issues Found
- No direct call to DataExporter.write_with_format_selection in OrgInventoryExporter.inventory (uses APIDataFetcher pipeline). This is acceptable if APIDataFetcher passes api_function_name correctly (it does).
- Lack of dedicated unit/integration tests for the OrgInventoryExporter.inventory pathway: no tests that exercise inventory() end-to-end or assert sqlite export behavior for menu #12.
- No test that mocks DataExporter to assert write_with_format_selection receives api_function_name="getOrgInventory" when inventory() runs.
- No integration test verifying SQLite table creation and primary key/index usage for getOrgInventory outputs.

SQL Export Compliance Check
- ENDPOINT_PRIMARY_KEY_STRATEGIES contains "getOrgInventory" with natural_pk and primary_key ["id"] \u00021: PASS.
- APIDataFetcher captures api_call.__name__ and passes api_function_name into DataExporter.export_with_processing, which eventually passes it to write_with_format_selection: PASS.
- Therefore menu #12 is architecturally compliant with dual-output CSV+SQLite and PK strategy requirements, but lacking test verification: PARTIAL PASS.

Test Coverage
- tests/unit/test_pk_strategies.py duplicates and validates the presence and structure of getOrgInventory strategy: PASS (strategy coverage).
- No unit test for OrgInventoryExporter.inventory; no test asserting DataExporter.call or SQLite write for this menu: MISSING.

Acceptance Criteria
- AC-1: ENDPOINT_PRIMARY_KEY_STRATEGIES includes "getOrgInventory" (natural_pk with primary_key ["id"]).
- AC-2: Running OrgInventoryExporter.inventory() results in DataExporter.write_with_format_selection being invoked with api_function_name="getOrgInventory" (mocked assertion acceptable).
- AC-3: Integration test that runs the pipeline (with API mocked) and verifies a SQLite table 'OrgInventory' (or appropriate table name) exists and has primary key/indices per strategy.
- AC-4: Tests added to tests/unit or tests/integration follow project conventions and run successfully under existing test harness.

Recommendations (summary)
- Add unit test to assert APIDataFetcher/OrgInventoryExporter pipeline supplies api_function_name correctly to DataExporter.
- Add integration test to validate SQLite table creation and PK constraints for getOrgInventory outputs.
- Ensure tests clean up created SQLite artifacts in data/mist_data.db or use a temp DB path within project (respecting no /tmp rule).