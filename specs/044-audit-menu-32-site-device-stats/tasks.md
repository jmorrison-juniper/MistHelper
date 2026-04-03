Tasks for Menu #32 (SiteDeviceExporter.device_stats):

- T1: Code update
  - File: MistHelper.py
  - Edit: Replace DataExporter.save_data_to_output(sanitized_data, filename) with DataExporter.write_with_format_selection(sanitized_data, filename, api_function_name="listSiteDevicesStats")

- T2: Unit tests
  - Create tests/unit/test_site_device_stats_exporter.py
  - Mock mistapi.api.v1.sites.stats.listSiteDevicesStats to return paginated sample data
  - Mock DataExporter.write_with_format_selection to assert call with api_function_name

- T3: Integration test
  - Create tests/integration/test_site_device_stats_sqlite.py
  - Use sample records with duplicate device_id/timestamp combos to validate upsert behavior and PK enforcement

- T4: Run verification
  - python -m py_compile MistHelper.py; pytest -q

Estimated effort: 2-3 hours (includes integration sqlite validation).