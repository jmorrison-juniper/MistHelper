Objective:
Validate Menu #46 PSK exporter uses PK strategy and add tests.

Plan:
1. Review OrgConfigExporter.psks implementation to find where OrgExportUtils.export_data is invoked.
2. Verify whether APIDataFetcher/DataExporter receive api_function_name; if not, document change to pass api function name.
3. Create unit tests mocking mistapi to assert that DataExporter.save_data_to_output is called with api_function_name="listOrgPsks" for SQLite.
4. Run tests and record results.
