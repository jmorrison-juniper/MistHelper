# Plan: Implement SQL export compliance and tests for Menu #4 (Gateway Management IPs)

Goal: Make Menu #4 fully SQL-export-compliant, add primary key strategy, fix minor bugs, and add tests.

Assumptions:
- The export should be treated as a derived dataset; use a logical api_function_name of `gatewayManagementIPsExport`.
- Primary key strategy: composite key on `gateway_name` and `template_id` (or site_id) to avoid duplicates.
- Tests will mock file I/O and DataExporter to avoid real DB writes.

Steps:
1. Code changes (NOT in this task):
   - Update `GatewayExportUtils.management_ips` to call `DataExporter.write_with_format_selection(final_results, "GatewayManagementIPs.csv", api_function_name="gatewayManagementIPsExport")` instead of `save_data_to_output`.
   - Ensure `final_results` field names align with PK strategy columns (include `gateway_name`, `template_id`, `site_id` as needed).
   - Fix the discarded device lookup: assign `{dev.get('name'): dev for dev in gateway_devices}` to `device_lookup` and use it for status correlation.
   - Add defensive logic for name collisions: prefer inventory MAC/ID where possible; if names are duplicated, log warning and disambiguate by site_id.

2. Configuration:
   - Add an entry to `ENDPOINT_PRIMARY_KEY_STRATEGIES` in MistHelper.py:
     ```python
     "gatewayManagementIPsExport": {
         "type": "natural_pk" | "composite_pk",
         "primary_key": ["gateway_name", "template_id"],
         "indexes": ["site_name", "template_id", "management_ip"],
         "unique_constraints": [],
         "description": "Exported list of gateway management overlay IPs grouped by template association",
     },
     ```
     (Decide between natural_pk vs composite_pk depending on whether gateway_name is stable. Composite recommended.)

3. Tests:
   - Unit test: tests/unit/test_gateway_management_ips.py
     - Mock CSV loading functions (FilePathUtils.get_csv_path and open), feed sample CSV rows for sites, templates, gateway_devices, gateway_configs.
     - Mock DataExporter.write_with_format_selection to capture its args; assert it's called once with expected `api_function_name` and rows.
     - Test scenarios: normal mapping, missing management IPs, duplicate gateway names across sites, multiple templates.
   - PK strategy test: extend tests/unit/test_pk_strategies.py to include the new `gatewayManagementIPsExport` entry.

4. Documentation:
   - Update README.md entry listing dual-output operations and mention new endpoint key in ENDPOINT_PRIMARY_KEY_STRATEGIES.

5. Validation and CI:
   - Run unit tests: pytest tests/unit -q
   - Run existing pk strategy tests to ensure new entry passes validation.

Estimated effort: 2-3 developer-hours.


-- End of plan
