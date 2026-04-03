Spec: Audit Menu #39 — Export switch templates (OrgTemplateExporter.switch_templates)

Findings:
- Implementation: switch_templates fetches network templates via mistapi.api.v1.orgs.networktemplates.listOrgNetworkTemplates and processes them, but writes output with DataExporter.save_data_to_output(processed, filename) WITHOUT passing api_function_name.
- ENDPOINT_PRIMARY_KEY_STRATEGIES contains 'listOrgNetworkTemplates' (natural_pk primary_key ['id']).
- Because api_function_name is omitted, DataExporter will default to fallback strategy for SQLite writes.

Test Coverage:
- No unit tests currently assert that switch_templates uses the correct api_function_name or that SQLite schema matches ENDPOINT_PRIMARY_KEY_STRATEGIES.

SQL Export Compliance: FAIL — switch_templates should pass api_function_name='listOrgNetworkTemplates' to ensure natural_pk schema (id) is used instead of default auto-increment.

Recommendation:
- Update switch_templates to call DataExporter.save_data_to_output(processed, filename, api_function_name='listOrgNetworkTemplates') or use APIDataFetcher to standardize behavior.