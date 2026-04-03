Plan for audit of Menu Option #22

Goals:
- Confirm that devices_with_site_info exports data with SQL-friendly keys and uses DataExporter.write_with_format_selection(api_function_name=...)
- Identify missing unit/integration tests and propose test cases
- Produce tasks to implement fixes (outside this audit)

Steps:
1. Inspect OrgInventoryExporter.devices_with_site_info implementation (MistHelper.py) for how it writes output.
2. Cross-reference the endpoint keys in ENDPOINT_PRIMARY_KEY_STRATEGIES to ensure corresponding API function names are present (e.g., getOrgInventory, listOrgSites, getOrgDevices).
3. Search tests/ for relevant tests; record missing coverage.
4. Compile recommendations: replace DataExporter.save_data_to_output calls with DataExporter.write_with_format_selection(api_function_name=...), or add SQL export mapping if intentionally omitted.
5. Prepare tasks.md listing concrete fixes and tests to add.

Timeline: single-sprint audit; estimated 2-4 hours.
