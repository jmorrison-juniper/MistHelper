Tasks: Audit & Test Coverage for Menu 12 (OrgInventoryExporter.inventory)

T001 - Create unit test for inventory pipeline
- Path: tests/unit/test_menu_12_inventory.py
- Steps:
  1. Mock ConfigUtils.get_cached_or_prompted_org_id to return a fixed org id.
  2. Mock mistapi.api.v1.orgs.inventory.getOrgInventory or mistapi.get_all to return a list of 2-5 sample device dicts (include 'id', 'org_id', 'site_id', 'mac', 'serial', 'model', 'type').
  3. Patch DataExporter.write_with_format_selection to a MagicMock.
  4. Call OrgInventoryExporter.inventory() and assert the mock was called with api_function_name="getOrgInventory" and filename containing "OrgInventory.csv".
  5. Ensure test runs fast and cleans up any files if accidentally written.
- Estimated effort: 1-2 hours
- Owner: dev

T002 - Create integration test to validate SQLite export
- Path: tests/integration/test_menu_12_inventory_sqlite.py
- Steps:
  1. Set OUTPUT_FORMAT to "sqlite" for the test via monkeypatch/env var.
  2. Set database path to data/mist_data_test.db (do not use /tmp).
  3. Mock API to return sample device list.
  4. Run OrgInventoryExporter.inventory() (or APIDataFetcher directly) to perform write.
  5. Open SQLite DB and assert table exists (table name derived from "OrgInventory"), row count matches sample data, and primary key column 'id' exists; check indexes if SQLiteDatabaseWriter creates them.
  6. Remove data/mist_data_test.db at test end.
- Estimated effort: 2-3 hours
- Owner: dev

T003 - Add fixtures and helper utils for tests
- Path: tests/unit/fixtures/menu_12_sample_devices.json or inline fixture
- Provide 3-5 realistic device dicts matching Mist API inventory shape.
- Estimated effort: 30-60 minutes

T004 - CI/test harness update & run
- Add tests to CI group if integration tests are isolated; ensure pytest collects new tests.
- Run full test suite locally: pytest -q
- Fix flakiness and cleanup issues.
- Estimated effort: 1-2 hours

T005 - Documentation update
- Update specs/024-audit-menu-12-org-inventory/spec.md with test results and link to new tests after implementation.
- Optional README note: how to run new tests and mention no /tmp usage.
- Estimated effort: 30 minutes

Notes:
- Do NOT change production code unless tests reveal a real bug. If production fixes are needed, create a separate task with code change steps and include ENDPOINT_PRIMARY_KEY_STRATEGIES review.