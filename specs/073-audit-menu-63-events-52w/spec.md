Spec: Menu 63 — WIP Export device events 52 weeks (OrgAlarmEventExporter.device_events_52w)

Summary of findings:
- OrgAlarmEventExporter.device_events_52w exists in MistHelper.py and is wired to menu 63.
- tests/test_exports.py includes a call to MistHelper.OrgAlarmEventExporter.device_events_52w(), indicating some test coverage exists.
- Verify that the implementation calls DataExporter.write_with_format_selection(..., api_function_name="searchOrgDeviceEvents") or equivalent. Prior specs requested this change for device_events; confirm device_events_52w matches that pattern.
- Check ENDPOINT_PRIMARY_KEY_STRATEGIES for searchOrgDeviceEvents entry (expected composite_pk primary_key = ['id','device_id','timestamp']).

Observations:
- Partial test coverage exists, but need explicit assertions that DataExporter.write_with_format_selection is invoked with api_function_name and that PK strategy exists.
