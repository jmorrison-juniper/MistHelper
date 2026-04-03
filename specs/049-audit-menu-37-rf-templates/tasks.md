Tasks (Menu #37):

1. Create tests/unit/test_menu_37_rf_templates.py
   - Mock API call mistapi.api.v1.orgs.rftemplates.listOrgRfTemplates.
   - Mock DataExporter.write_with_format_selection.
   - Call OrgTemplateExporter.rf_templates().
   - Assert write_with_format_selection invoked with filename 'OrgRfTemplates.csv' and api_function_name 'listOrgRfTemplates'.

2. Add integration test if necessary to validate SQLite table uses PK ['id'].

3. Update specs index.