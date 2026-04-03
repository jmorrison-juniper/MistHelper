Plan for Menu #39 (Remediation):

1. Immediate fix: Modify OrgTemplateExporter.switch_templates to pass api_function_name='listOrgNetworkTemplates' to DataExporter.save_data_to_output.
2. Preferred: Use APIDataFetcher(api_call=mistapi.api.v1.orgs.networktemplates.listOrgNetworkTemplates, filename='OrgSwitchTemplates.csv', ...) so DataExporter gets api_function_name automatically.
3. Add unit tests to validate api_function_name propagation and SQLite table schema (PK and indexes).
4. Run tests and update documentation.

Notes:
- Changing filename to OrgSwitchTemplates.csv is fine; ensure table naming still maps logically to endpoint strategy (api_function_name controls strategy).