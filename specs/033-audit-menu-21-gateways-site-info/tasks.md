Tasks for Audit #033 — Gateways with Site Info

1. add-api-name-to-gateway-export
   - Title: Add api_function_name to gateways export
   - Description: Update OrgInventoryExporter.gateways_with_site_info to call DataExporter.write_with_format_selection (preferred) or DataExporter.save_data_to_output with api_function_name="getOrgInventory". Ensure filename is consistent (GatewaysWithSiteInfo.csv) and update any logging messages.
   - Assignee: dev
   - Estimate: 1h
   - Dependencies: None

2. add-unit-tests-for-gateway-export
   - Title: Add unit tests covering gateways_with_site_info
   - Description: Create tests/unit/test_org_inventory_exporter.py with mocks for ConfigUtils, APICoreFetchUtils, and DataExporter to assert correct filtering, enrichment, and that api_function_name is passed to DataExporter.
   - Assignee: qa
   - Estimate: 2h
   - Dependencies: Task 1

3. validate-pk-strategy-integration
   - Title: Validate PK strategy mapping for gateways export
   - Description: Ensure that when DataExporter receives api_function_name it maps to ENDPOINT_PRIMARY_KEY_STRATEGIES["getOrgInventory"] and results in SQLite table using primary key ['id'] when OUTPUT_FORMAT=="sqlite". Write a unit/integration test that asserts this mapping.
   - Assignee: dev
   - Estimate: 1h
   - Dependencies: Task 1, Task 2

4. run-test-suite-and-fix
   - Title: Run full pytest suite and fix regressions
   - Description: Run pytest, fix any test breaks introduced by changes, update mocks if needed.
   - Assignee: dev
   - Estimate: 1h
   - Dependencies: Tasks 1-3

5. update-docs-and-commit
   - Title: Update README and changelog
   - Description: Update README operation table (if maintained), add changelog entry 'version YY.MM.DD.HH.MM - Audit 033: Gateways export fixes', commit changes following repo guidelines.
   - Assignee: dev
   - Estimate: 30m
   - Dependencies: All prior tasks

Notes:
- Do NOT modify production behavior beyond adding api_function_name and tests without explicit review.
- If DataExporter lacks write_with_format_selection, use save_data_to_output with api_function_name param. If neither supports it, create minimal wrapper in DataExporter to accept api_function_name (requires separate audit).
