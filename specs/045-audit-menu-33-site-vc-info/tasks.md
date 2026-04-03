Tasks for Menu #33 (SiteDeviceExporter.device_virtual_chassis):

- T1: PK mapping
  - File: MistHelper.py
  - Add ENDPOINT_PRIMARY_KEY_STRATEGIES["getSiteDeviceVirtualChassis"] with appropriate type.
  - Suggested initial entry uses natural_pk ['id'] or composite_pk ['device_id','member_id','timestamp'] if no single id exists.

- T2: Code update
  - File: MistHelper.py
  - Replace DataExporter.save_data_to_output(sanitized, filename) with DataExporter.write_with_format_selection(sanitized, filename, api_function_name="getSiteDeviceVirtualChassis")

- T3: Tests
  - Unit: tests/unit/test_site_vc_exporter.py mocking API response and asserting DataExporter.write_with_format_selection call
  - Integration: tests/integration/test_site_vc_sqlite.py to assert table creation and PK behavior

- T4: Docs & Validation
  - Update README dual-output list
  - Run: python -m py_compile MistHelper.py; pytest -q

Estimated effort: 1-2 hours (inspection of API payload required to choose PK columns).