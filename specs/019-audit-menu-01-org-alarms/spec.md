# Feature Specification: Audit Menu #1 - Organization Alarms Export
**Created**: 2026-04-03
**Status**: Audit

## Current State Analysis
OrgAlarmEventExporter.alarms is a static method that:
- Computes a 24h dynamic lookback and calls APIDataFetcher with:
  - api_call=mistapi.api.v1.orgs.alarms.searchOrgAlarms
  - filename="OrgAlarms.csv"
  - duration set to f"{hours}h" and acked=False
- APIDataFetcher.execute() invokes the API, collects paginated results via mistapi.get_all, and calls DataExporter.export_with_processing(..., api_function_name=api_call.__name__), which flows to DataExporter.write_with_format_selection when saving.

## Issues Found
- No direct unit test exists for Menu #1 (OrgAlarmEventExporter.alarms).
- The alarms() method does not explicitly pass api_function_name into DataExporter; it relies on APIDataFetcher to set api_function_name via api_call.__name__ (indirect but functional).
- No explicit sort_key is provided for alarms export (may yield unsorted output).

## SQL Export Compliance
- DataExporter.write_with_format_selection is used in the export path (via APIDataFetcher -> DataExporter.export_with_processing -> save_data_to_output -> write_with_format_selection).
- ENDPOINT_PRIMARY_KEY_STRATEGIES contains an entry for "searchOrgAlarms" with type "composite_pk" and primary_key ["id","org_id","timestamp"].
- Therefore SQL export compliance is satisfied (api function name will resolve to the appropriate PK strategy).

## Test Coverage
- No existing unit or integration test targets OrgAlarmEventExporter.alarms directly.
- tests/unit/test_pk_strategies.py validates the presence of "searchOrgAlarms" in the PK strategies.
- tests/test_exports.py contains export tests for device_events_52w but not for OrgAlarms.

## Acceptance Criteria for Fixes
- A unit test exists that calls OrgAlarmEventExporter.alarms (via monkeypatch) and verifies:
  - DataExporter.save_data_to_output (or write_with_format_selection) is called with filename "OrgAlarms.csv" and api_function_name "searchOrgAlarms".
  - The number of rows written matches the mocked API response.
- Optionally, include an assertion that the exported SQLite table uses the composite PK strategy for searchOrgAlarms in integration tests (mocking SQLite writer).
- Alarms export remains reachable via Menu #1 with existing behavior preserved.
