Plan for Menu #38 (Remediation):

1. Short-term fix: Update OrgTemplateExporter.ap_templates to call DataExporter.save_data_to_output(processed, filename, api_function_name='listOrgAptemplates').
2. Preferred fix: Replace the custom implementation with APIDataFetcher usage to standardize behavior: APIDataFetcher(api_call=mistapi.api.v1.orgs.aptemplates.listOrgAptemplates, filename='OrgApTemplates.csv', ...). That ensures api_function_name matches the strategy.
3. Add unit tests to assert api_function_name is passed and SQLite table uses natural_pk 'id'.
4. Run test suite and integration checks (validate sqlite table indexes/PKs).

Notes:
- Do NOT implement code changes in this task; document required PR and tests.