Spec: Audit Menu #37 — Export RF templates (OrgTemplateExporter.rf_templates)

Findings:
- Implementation: OrgTemplateExporter.rf_templates delegates to OrgExportUtils.export_data with api_call=mistapi.api.v1.orgs.rftemplates.listOrgRfTemplates.
- ENDPOINT_PRIMARY_KEY_STRATEGIES contains 'listOrgRfTemplates' (natural_pk primary_key ['id']).
- OrgExportUtils.export_data -> APIDataFetcher ensures DataExporter receives api_function_name; therefore SQLite writes should use configured strategy.

Test Coverage:
- ENDPOINT_PRIMARY_KEY_STRATEGIES entries are validated by tests/unit/test_pk_strategies.py.
- No dedicated tests for rf_templates.

SQL Export Compliance: PASS via APIDataFetcher; add unit test to assert api_function_name propagation.

Acceptance Criteria:
- Unit test verifies DataExporter.write_with_format_selection is invoked with api_function_name='listOrgRfTemplates'.