Plan for Menu #36:

1. Add unit test to patch DataExporter.write_with_format_selection and call OrgTemplateExporter.network_templates().
2. Assert write_with_format_selection called once with filename 'OrgNetworkTemplates.csv' and api_function_name 'listOrgNetworkTemplates'.
3. Add an integration test using APIDataFetcher with mocked API response to validate CSV and SQLite write behavior.

Notes:
- Reuse test fixtures from spec #35 where applicable.
- No production code changes required if test passes; otherwise, update exporter to pass api_function_name explicitly.