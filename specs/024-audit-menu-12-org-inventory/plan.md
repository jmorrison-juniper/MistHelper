Plan: Implement tests and verification for Menu #12 (OrgInventoryExporter.inventory)

Goals
- Verify end-to-end export pipeline for menu #12 including CSV and SQLite paths.
- Ensure SQLite writes adhere to ENDPOINT_PRIMARY_KEY_STRATEGIES["getOrgInventory"].
- Add repeatable, fast unit and integration tests.

Assumptions
- Tests can mock mistapi and DataExporter behaviors where needed.
- The project test harness can run unit tests in isolation and uses data/mist_data.db by default for SQLite writes.
- No code changes required to production code; tests will mock and assert behaviors.

High-level Steps
1. Add unit test (tests/unit/test_menu_12_inventory.py):
   - Mock ConfigUtils.get_cached_or_prompted_org_id to return a test org id.
   - Mock mistapi.api.v1.orgs.inventory.getOrgInventory to return a fake response object with .data as list of device dicts and status_code=200; or patch mistapi.get_all to return sample list.
   - Patch DataExporter.write_with_format_selection (or DataExporter.save_data_to_output) to a mock and assert it was called with api_function_name="getOrgInventory" and filename "OrgInventory.csv".
2. Add integration-style test (tests/integration/test_menu_12_inventory_sqlite.py):
   - Use an in-repo temporary SQLite database path (e.g., data/mist_data_test.db) to avoid /tmp usage.
   - Run APIDataFetcher (or OrgInventoryExporter.inventory) with mistapi mocked to return sample data; configure OUTPUT_FORMAT="sqlite" via monkeypatch or environment to route writes to SQLite.
   - After run, open the DB and assert table 'OrgInventory' (or filename-derived table) exists and its schema includes primary key column 'id' and indexes declared in the strategy.
   - Clean up DB file after test.
3. Update tests/unit/test_pk_strategies.py if needed to assert that the strategy entry includes indexes or unique_constraints for getOrgInventory.
4. Add test data fixtures under tests/unit/fixtures/ or inline sample data in tests.

Validation
- Run existing test suite (pytest -q). All new tests must pass and not flake.
- Lint and static checks as per repo guidelines.

Risks & Mitigations
- Mistapi import side-effects: use monkeypatching or duplicate minimal response objects to avoid real API calls.
- SQLite schema checks depend on SQLiteDatabaseWriter implementation; assert presence of PK and indexes where possible; fallback to verifying creation and row counts if schema introspection is brittle.

Deliverables
- tests/unit/test_menu_12_inventory.py
- tests/integration/test_menu_12_inventory_sqlite.py
- Updated docs or README note (optional) summarizing added tests and how to run them.