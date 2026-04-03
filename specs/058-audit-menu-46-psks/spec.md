Title: Audit — Menu #46: Export PSK information

Summary:
- Menu impl: OrgConfigExporter.psks in MistHelper.py (calls OrgExportUtils.export_data with mistapi.api.v1.orgs.psks.listOrgPsks)
- PK strategy: ENDPOINT_PRIMARY_KEY_STRATEGIES includes listOrgPsks (natural_pk on id)
- Export path: OrgExportUtils → APIDataFetcher → DataExporter; API function name is not automatically propagated to DataExporter for SQLite writes.
- Tests: test_pk_strategies.py includes listOrgPsks (strategy validation). No unit tests directly validate OrgConfigExporter.psks.

Recommendations:
1) When exporting to SQLite, ensure api_function_name="listOrgPsks" is provided to DataExporter to pick the PK strategy.
2) Add a unit test to mock mistapi and assert exporter uses correct api_function_name for SQL exports.
3) Optionally add end-to-end test to check SQLite table schema uses 'id' as PK.
