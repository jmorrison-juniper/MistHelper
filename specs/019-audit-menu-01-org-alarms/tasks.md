Actionable tasks to remediate findings for Menu #1 (Org Alarms)

T1 - Add unit test for OrgAlarmEventExporter.alarms
- Create tests/test_exports_org_alarms.py
- Use monkeypatch to stub:
  - MistHelper.ConfigUtils.get_cached_or_prompted_org_id -> return fixed org id
  - MistHelper.mistapi.api.v1.orgs.alarms.searchOrgAlarms -> return MagicMock() response
  - MistHelper.mistapi.get_all -> return sample list of alarm dicts
  - MistHelper.DataExporter.save_data_to_output (or DataExporter.write_with_format_selection) -> record calls
- Assert:
  - filename == "OrgAlarms.csv"
  - recorded row count matches mocked list length
  - api_function_name == "searchOrgAlarms"

T2 - Add integration-style test for SQLite path (optional but recommended)
- Mock MistHelper.SQLiteDatabaseWriter.write to capture table name and strategy lookup
- Run OrgAlarmEventExporter.alarms with OUTPUT_FORMAT forced to "sqlite" in test
- Assert SQLiteDatabaseWriter.write called with table derived from "OrgAlarms.csv" and api function name resolves to "searchOrgAlarms" strategy

T3 - Add test for empty API response
- Ensure APIDataFetcher handles empty results without attempting writes (DataExporter.save_data_to_output should not be called)

T4 - (Optional) Minor code clarity change
- Consider passing api_function_name explicitly when constructing APIDataFetcher in OrgAlarmEventExporter.alarms to make the export path explicit (not required for functionality). Example: APIDataFetcher(..., api_function_name="searchOrgAlarms"). Document change in PR.

T5 - Documentation update
- Update README or operation index to indicate Menu #1 has unit test coverage and SQL PK strategy is in place.

Notes
- Do NOT perform code changes in this task. Implement tests and optional refactor in a follow-up PR.
