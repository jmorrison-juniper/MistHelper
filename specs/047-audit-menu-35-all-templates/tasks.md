Tasks (Menu #35):

1. Create tests/unit/test_menu_35_all_templates.py
   - Patch mistapi.api.v1.orgs.networktemplates.listOrgNetworkTemplates (and gateway, rf, site, aptemplates) to return a synthetic response object whose .data is a list of dicts.
   - Patch DataExporter.write_with_format_selection to capture calls.
   - Call OrgTemplateExporter.all_templates().
   - Assert DataExporter.write_with_format_selection was called for each filename (OrgNetworkTemplates.csv, OrgRfTemplates.csv, OrgSiteTemplates.csv, OrgApTemplates.csv, OrgGatewayTemplates.csv) with api_function_name equal to the underlying API function name (e.g., 'listOrgNetworkTemplates').

2. Add an integration test using a temporary SQLite DB path (monkeypatch DATABASE_PATH) to assert tables created have PK/index metadata per ENDPOINT_PRIMARY_KEY_STRATEGIES for one sample endpoint.

3. Update tests documentation (specs index) and run test suite.