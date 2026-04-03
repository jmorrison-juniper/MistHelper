Plan: Audit and Remediation for Menu Option #21

Goal: Ensure gateways_with_site_info exports are SQL-compliant, covered by unit tests, and use DataExporter API tagging for correct PK strategy selection.

Assumptions:
- APICoreFetchUtils.all_inventory_with_limit wraps the Mist API call getOrgInventory; therefore api_function_name should be "getOrgInventory" for export.
- DataExporter has write_with_format_selection(rows, filename, api_function_name=...) helper; if not, save_data_to_output supports api_function_name parameter.

Steps:
1. Static review (complete) — locate function, verify behavior, check PK strategies and tests. (Done in spec.md)
2. Prepare code change: update OrgInventoryExporter.gateways_with_site_info to call DataExporter.write_with_format_selection(gateways, "GatewaysWithSiteInfo", api_function_name="getOrgInventory") or DataExporter.save_data_to_output(gateways, "GatewaysWithSiteInfo.csv", api_function_name="getOrgInventory").
3. Add unit tests: new test file tests/unit/test_org_inventory_exporter.py with tests that:
   - Monkeypatch ConfigUtils.get_cached_or_prompted_org_id to fixed org id.
   - Monkeypatch APICoreFetchUtils.all_sites_with_limit and all_inventory_with_limit to return sample data with gateways and non-gateways.
   - Monkeypatch DataExporter.write_with_format_selection / save_data_to_output to capture api_function_name and written filename and assert correct values and row counts.
4. Run existing test suite: pytest -q. Fix any test failures.
5. Validate SQL export path: run unit test that simulates OUTPUT_FORMAT='sqlite' and verify that DataExporter invoked with api_function_name leads to SQLite table following getOrgInventory PK strategy (unit test should assert that DataExporter attempts to create table with primary_key 'id' or that DataExporter received the api_function_name and downstream code maps it to PK strategy). If necessary, write a lightweight integration test that invokes DataExporter mapping logic (unit test of PK strategy resolution exists in tests/unit/test_pk_strategies.py; reuse patterns).
6. Update README and changelog noting audit completion and version bump.
7. Commit changes with message following UTC timestamp convention.

Acceptance Criteria:
- Gateways export uses DataExporter with api_function_name argument pointing to getOrgInventory
- One or more unit tests covering logic and api_function_name propagation
- All tests pass locally
- Documentation updated
