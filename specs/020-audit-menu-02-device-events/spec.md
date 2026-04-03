# Feature Specification: Audit Menu #2 - Device Events Export
**Created**: 2026-04-03
**Status**: Audit

## Current State Analysis
OrgAlarmEventExporter.device_events is a static method that:
- Prompts/loads org_id via ConfigUtils
- Computes a dynamic 24h lookback via TimeUtils
- Calls mistapi.api.v1.orgs.devices.searchOrgDeviceEvents(apisession, org_id, device_type="all", limit=1000, duration=duration)
- Uses mistapi.get_all(...) to paginate and collect results
- Assigns events = rawdata and writes CSV via DataExporter.save_data_to_output(events, "OrgDeviceEvents.csv")
- Logs counts and sample rows

It does not perform flattening/escaping like the 52w variant.

## Issues Found
- Uses DataExporter.save_data_to_output rather than DataExporter.write_with_format_selection; therefore SQLite export path is not engaged.
- Missing api_function_name parameter when saving output; breaks PK-based SQLite upsert semantics.
- No data normalization (flatten/escape) present unlike device_events_52w.
- No tests covering the 24-hour device_events export; only device_events_52w is tested.
- No explicit error handling around the mistapi call (no try/except) unlike some other exporters.

## SQL Export Compliance
- DataExporter.write_with_format_selection with api_function_name is required for SQLite export and PK strategy use. device_events does not use it.
- ENDPOINT_PRIMARY_KEY_STRATEGIES contains an entry for "searchOrgDeviceEvents" with type: composite_pk and primary_key: ["id", "device_id", "timestamp"]. So PK strategy exists.
- To be compliant, device_events must call DataExporter.write_with_format_selection(events, filename, api_function_name="searchOrgDeviceEvents") and apply DataProcessingUtils.flatten/escape as appropriate.

## Test Coverage
- tests/test_exports.py includes test_device_events_52w_writes_csv which exercises the 52-week exporter; it asserts filename and that DataExporter was called for the 52w flow.
- There is no unit/integration test for the 24-hour OrgAlarmEventExporter.device_events method.
- Unit tests exist for ENDPOINT_PRIMARY_KEY_STRATEGIES mapping (tests/unit/test_pk_strategies.py) covering the presence of searchOrgDeviceEvents.

## Acceptance Criteria for Fixes
- device_events writes dual output via DataExporter.write_with_format_selection(events, filename, api_function_name="searchOrgDeviceEvents").
- Exported rows are flattened and escaped similarly to device_events_52w.
- A new unit test covers the 24-hour device_events path, asserting that write_with_format_selection is invoked with correct api_function_name and filename, and that it handles empty results gracefully.
- Existing pk strategy tests continue to pass.
