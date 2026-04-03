Title: Audit — Menu #45: Export license information

Summary:
- Menu impl: OrgAdminExporter.licenses in MistHelper.py
- PK strategy: ENDPOINT_PRIMARY_KEY_STRATEGIES includes getOrgLicensesSummary (auto_increment_with_unique)
- Export path: uses Mist API and DataExporter.save_data_to_output; api_function_name is not consistently propagated.
- Tests: test_pk_strategies.py covers getOrgLicensesSummary (strategy validation); no unit tests exercise OrgAdminExporter.licenses.

Risk/Notes:
- SQLite exports require api_function_name to choose PK strategy; omission causes fallback strategy and may create poor schema or duplicate rows.

Recommendation:
1) Ensure OrgAdminExporter.licenses passes api_function_name="getOrgLicensesSummary" when saving to SQLite.
2) Add unit tests mocking mistapi to validate CSV and SQLite output paths.
3) Keep existing ENDPOINT_PRIMARY_KEY_STRATEGIES entry; add integration test to verify SQL writing.