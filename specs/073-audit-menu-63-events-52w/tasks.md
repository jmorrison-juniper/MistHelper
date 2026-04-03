Tasks:
1. Open MistHelper.py and locate OrgAlarmEventExporter.device_events_52w; record exact API calls and exported filename.
2. Confirm or add ENDPOINT_PRIMARY_KEY_STRATEGIES entry for 'searchOrgDeviceEvents' (composite_pk).
3. Modify device_events_52w to use DataExporter.write_with_format_selection(processed_events, "OrgDeviceEvents", api_function_name="searchOrgDeviceEvents") if not already present.
4. Add tests/test_device_events_52w.py with two tests: non-empty (assert write_with_format_selection called) and empty (assert graceful handling).
5. Run pytest; iterate until passing.

Notes: Reuse existing test utilities and mocking patterns from tests/test_exports.py.