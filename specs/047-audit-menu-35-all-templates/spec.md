Spec: Audit Menu #35 — Export all organization templates (OrgTemplateExporter.all_templates)

Findings:
- Implementation: OrgTemplateExporter.all_templates uses APIDataFetcher to call gateway, network, RF, site, and AP template endpoints (listOrgGatewayTemplates, listOrgNetworkTemplates, listOrgRfTemplates, listOrgSiteTemplates, listOrgAptemplates).
- ENDPOINT_PRIMARY_KEY_STRATEGIES contains entries for all five endpoints (natural_pk with primary_key ['id']).
- Data path: APIDataFetcher -> DataExporter.export_with_processing -> DataExporter.write_with_format_selection passes api_function_name (api_call.__name__) so SQLite writes use the mapped PK strategies.

Test Coverage:
- tests/unit/test_pk_strategies.py validates ENDPOINT_PRIMARY_KEY_STRATEGIES entries exist, covering the strategy definitions.
- No unit tests currently exercise OrgTemplateExporter.all_templates or assert the API function name is propagated to DataExporter.

SQL Export Compliance: PASS — all_templates uses APIDataFetcher which supplies api_function_name, so SQLite upserts will use the correct ENDPOINT_PRIMARY_KEY_STRATEGIES entries.

Acceptance Criteria:
- ENDPOINT_PRIMARY_KEY_STRATEGIES entries exist (verified).
- Exports use DataExporter.write_with_format_selection with api_function_name set (via APIDataFetcher). 
- Add unit/integration test to assert api_function_name propagation (see plan/tasks).