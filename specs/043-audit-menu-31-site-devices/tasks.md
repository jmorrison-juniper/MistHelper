Tasks for Menu #31 (SiteDeviceExporter.devices):

- T1: Code update
  - File: MistHelper.py
  - Edit: Replace DataExporter.save_data_to_output(sanitized_data, filename) with DataExporter.write_with_format_selection(sanitized_data, filename, api_function_name="listSiteDevices")
  - Add logging to indicate SQLite upsert strategy used.

- T2: Unit tests
  - Create tests/unit/test_site_devices_exporter.py
  - Mock mistapi.api.v1.sites.devices.listSiteDevices to return sample data
  - Mock DataExporter.write_with_format_selection to assert call args

- T3: Integration test
  - Create tests/integration/test_site_devices_sqlite.py
  - Use temporary data directory or in-memory SQLite to verify table created and PK columns match ENDPOINT_PRIMARY_KEY_STRATEGIES["listSiteDevices"]

- T4: Run verification
  - Commands: python -m py_compile MistHelper.py; pytest -q

Estimated effort: 1-2 hours to implement and validate.