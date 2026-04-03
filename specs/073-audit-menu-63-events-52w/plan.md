Plan:
1. Inspect OrgAlarmEventExporter.device_events_52w implementation and confirm use of DataExporter.write_with_format_selection with api_function_name set to the exact mistapi function name (likely 'searchOrgDeviceEvents').
2. Verify ENDPOINT_PRIMARY_KEY_STRATEGIES contains an entry for searchOrgDeviceEvents with composite_pk primary_key ['id','device_id','timestamp'].
3. Add unit tests (tests/test_device_events_52w.py) that:
   - Mock the API to return sample events and assert DataExporter.write_with_format_selection called with filename 'OrgDeviceEvents' and api_function_name 'searchOrgDeviceEvents'.
   - Test empty result handling.
4. Run test suite and fix any issues.

Deliverables:
- Test file asserting SQL-export compatibility
- Small spec updates documenting exact API function names used
