Summary of changes
- Add unit test(s) for Menu #1 (OrgAlarmEventExporter.alarms).
- Ensure test asserts DataExporter is invoked with api_function_name="searchOrgAlarms" and filename "OrgAlarms.csv".
- Optional: add integration test to validate SQLite path by mocking SQLiteDatabaseWriter.

Technical context
- OrgAlarmEventExporter.alarms delegates fetching and export to APIDataFetcher which sets api_function_name using api_call.__name__.
- DataExporter.write_with_format_selection() requires the api_function_name to look up ENDPOINT_PRIMARY_KEY_STRATEGIES for SQLite writes.
- ENDPOINT_PRIMARY_KEY_STRATEGIES contains "searchOrgAlarms" configured as composite_pk.

Constitution check
- 5-item rule: OrgAlarmEventExporter contains 5 public methods (alarms, alarm_templates, events, device_events, device_events_52w) — compliant.
- Class-based architecture: The exporter is a class, matching the project convention.
- Safety: APIDataFetcher handles rate-limiting, emergency saves, and writes partial data on error.
- Dual output: Export path uses DataExporter which supports CSV and SQLite formats.
- PK strategy: "searchOrgAlarms" is present; ensure tests assert api_function_name propagation.

Constraints & assumptions
- Tests will use monkeypatch to avoid real API calls and filesystem writes.
- For SQLite behavior testing, mock SQLiteDatabaseWriter to avoid touching actual DB file.
