Implementation Plan — Menu 16: synthetic_tests

Goal: Make GatewayTestExporter.synthetic_tests compliant with dual-output (CSV + SQLite) by routing exports through DataExporter.write_with_format_selection and adding primary key strategies and tests.

High-level steps
1. Design PK strategy
   - Inspect sample API response shape (if available). If unavailable, choose conservative strategy:
     * For searchSiteSyntheticTest (site-level multiple results): composite_pk with primary_key ["id","site_id","timestamp"]
     * For getSiteDeviceSyntheticTest (per-device single summary): auto_increment_with_unique with primary_key ["misthelper_internal_id"] and unique_constraints ["device_id","site_id","timestamp?"].
   - Document decision in ENDPOINT_PRIMARY_KEY_STRATEGIES entry comments.

2. Code changes
   - Replace DataExporter.save_data_to_output(sanitized, filename) with DataExporter.write_with_format_selection(sanitized, filename, api_function_name="getSiteDeviceSyntheticTest").
   - Ensure flattened/sanitized data is a list of dicts as expected by DataExporter.
   - For test_results_by_site (site-level exporter), ensure it calls DataExporter.write_with_format_selection(..., api_function_name="searchSiteSyntheticTest") when saving aggregated site results.

3. Tests
   - Add unit tests in tests/unit/test_gateway_synthetic_tests.py:
     * test_synthetic_tests_sequential_writes_sql(monkeypatch): mock ConfigUtils.get_cached_or_prompted_org_id, GatewayExportUtils._get_devices_with_sites to return sample device tuples, mock mistapi.api.v1.sites.devices.getSiteDeviceSyntheticTest to return MagicMock with .data, mock DataExporter.write_with_format_selection to capture calls and assert filename and api_function_name.
     * test_synthetic_tests_fast_mode_writes_sql(monkeypatch): same but exercise fast=True path using small device list; mock execute_with_connection_pool_management to return successful_results.
   - Run existing tests to ensure no regressions.

4. Documentation
   - Update README changelog entry noting menu 16 dual-output compliance.
   - Add a brief note in specs describing the chosen PK strategy.

5. Validation
   - Run python -m py_compile MistHelper.py
   - Run pytest -q; ensure new tests pass and no failures introduced.

Rollback plan
- If failures occur, revert changes, open an issue referencing this spec, and add more detailed inspection of API response shapes before reattempting.

Timeline estimate (single dev)
- PK decision & small code edits: 1-2 hours
- Tests + run: 1-2 hours
- Documentation & final validation: 30-60 minutes
