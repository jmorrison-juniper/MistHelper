Tasks to Fix and Test Menu #2 (Device Events Export)

T001 - Make device_events SQLite-compliant
- Modify OrgAlarmEventExporter.device_events to call DataProcessingUtils.flatten_nested_fields(events) and DataProcessingUtils.escape_multiline(events).
- Replace DataExporter.save_data_to_output(events, filename) with DataExporter.write_with_format_selection(events, filename, api_function_name="searchOrgDeviceEvents").
- Ensure filename uses timestamping if required by conventions (OrgDeviceEvents.csv is acceptable but timestamping optional per policy).
- Add try/except around the API call to log errors and re-raise.

T002 - Add unit tests for device_events (24h)
- Create new test in tests/test_exports.py or tests/unit/test_exports_device_events.py.
- Mock mistapi.api.v1.orgs.devices.searchOrgDeviceEvents to return a MagicMock response and ensure mistapi.get_all returns controlled sample events list.
- Patch DataExporter.write_with_format_selection to capture calls and assert api_function_name=="searchOrgDeviceEvents" and filename=="OrgDeviceEvents.csv" and that data passed equals processed (flattened/escaped) events.
- Test empty resultset path: ensure no exception and that write_with_format_selection is called with empty list.

T003 - Regression tests & PK strategy validation
- Ensure tests/unit/test_pk_strategies.py still passes; add assertion if necessary that "searchOrgDeviceEvents" maps to composite_pk and expected primary_key fields.

T004 - Documentation updates
- Update README.md changelog to mention Menu #2 fix and dual-output compliance.
- Add a short note in specs/020-audit-menu-02-device-events/spec.md referencing the change and the PR that implements it.

T005 - CI pipeline verification
- Run python -m py_compile MistHelper.py to validate syntax.
- Run existing test suite: pytest -q. Fix any failures caused by the change.
- Commit changes with version tag and Co-authored-by trailer as required.

Notes
- Do NOT modify ENDPOINT_PRIMARY_KEY_STRATEGIES; it already contains a correct composite_pk entry for searchOrgDeviceEvents.
- Keep changes surgical and limited to OrgAlarmEventExporter.device_events and unit tests. Do not refactor unrelated code.
