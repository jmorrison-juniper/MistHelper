Title: Audit — Menu #47: Export webhook configuration

Summary:
- Menu impl: OrgConfigExporter.webhooks in MistHelper.py (calls OrgExportUtils.export_data with mistapi.api.v1.orgs.webhooks.listOrgWebhooks)
- PK strategy: ENDPOINT_PRIMARY_KEY_STRATEGIES includes listOrgWebhooks (natural_pk on id)
- Export path: uses OrgExportUtils → APIDataFetcher → DataExporter; api_function_name not propagated automatically.
- Tests: test_pk_strategies.py covers listOrgWebhooks; no exporter-level unit tests found.

Recommendations:
1) Ensure DataExporter receives api_function_name="listOrgWebhooks" for SQLite exports.
2) Add unit tests for exporter behavior and SQLite schema validation.
3) Maintain strategy entry (already present).
