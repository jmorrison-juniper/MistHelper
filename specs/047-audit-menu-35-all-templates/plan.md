Plan to strengthen audit/test coverage for Menu #35:

1. Add a unit test that mocks mistapi and DataExporter to call OrgTemplateExporter.all_templates in test mode, asserting DataExporter.write_with_format_selection was invoked with api_function_name matching each API function name (e.g., 'listOrgNetworkTemplates').
2. Add an integration-style test that runs APIDataFetcher.execute with a synthetic response and validates both CSV file creation and SQLite table schema (in-memory DB or temp data/mist_data.db), ensuring primary keys/indexes match ENDPOINT_PRIMARY_KEY_STRATEGIES.
3. Update README/spec index noting test added and coverage.

Notes/Assumptions:
- Use unittest.mock to patch DataExporter.write_with_format_selection and mistapi.get_all to return sample payloads.
- Do not change production code in this task.