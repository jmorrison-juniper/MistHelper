Summary of Changes Needed
- Replace DataExporter.save_data_to_output(...) with DataExporter.write_with_format_selection(..., api_function_name="searchOrgDeviceEvents") in OrgAlarmEventExporter.device_events.
- Apply DataProcessingUtils.flatten_nested_fields() and DataProcessingUtils.escape_multiline() to events (mirroring device_events_52w) before export.
- Add minimal try/except around the API call to log and re-raise errors for observability.
- Create unit tests for the 24-hour export and update test harness to assert SQLite-call semantics.

Technical Context
- The DataExporter.write_with_format_selection() centralizes CSV and SQLite dual output and relies on ENDPOINT_PRIMARY_KEY_STRATEGIES to enforce primary keys for SQLite upserts.
- searchOrgDeviceEvents is a time-series endpoint already declared as composite_pk in ENDPOINT_PRIMARY_KEY_STRATEGIES; using api_function_name="searchOrgDeviceEvents" is necessary for correct SQLite schema and upsert behavior.
- device_events_52w already demonstrates flattening and escaping patterns; replicate those steps for 24h export.

Constitution Check (5-item rule & architecture)
- File-level: OrgAlarmEventExporter contains exactly 5 public methods related to events — conforms to the 5-item rule.
- Function-level: device_events should remain short; extract flatten/escape into helper calls if necessary to respect 25-line rule.
- Class-based: Changes remain within OrgAlarmEventExporter (no wrappers), maintaining class-based architecture.
- Safety: Use try/except to avoid silent failures; do not perform any write/update operations to Mist API.
- Dual output: Ensure DataExporter.write_with_format_selection() is used to preserve CSV+SQLite behavior and PK strategy.
