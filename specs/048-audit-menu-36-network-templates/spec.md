Spec: Audit Menu #36 — Export network templates (OrgTemplateExporter.network_templates)

Findings:
- Implementation: OrgTemplateExporter.network_templates delegates to OrgExportUtils.export_data using api_call=mistapi.api.v1.orgs.networktemplates.listOrgNetworkTemplates.
- ENDPOINT_PRIMARY_KEY_STRATEGIES contains 'listOrgNetworkTemplates' (natural_pk primary_key ['id']).
- OrgExportUtils.export_data uses APIDataFetcher which supplies api_function_name to DataExporter; thus SQLite writes will use the configured strategy.

Test Coverage:
- ENDPOINT_PRIMARY_KEY_STRATEGIES entries covered in tests/unit/test_pk_strategies.py.
- No dedicated unit tests for network_templates to verify write_with_format_selection invocation.

SQL Export Compliance: PASS if exported via OrgExportUtils (which uses APIDataFetcher). Need to add test asserting api_function_name propagation.

Acceptance Criteria:
- Ensure a unit test verifies that network_templates export calls DataExporter with api_function_name='listOrgNetworkTemplates'.
- If missing, add test.