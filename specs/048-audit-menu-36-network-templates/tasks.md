Tasks (Menu #36):

1. Create tests/unit/test_menu_36_network_templates.py
   - Patch mistapi.api.v1.orgs.networktemplates.listOrgNetworkTemplates to return sample data.
   - Patch DataExporter.write_with_format_selection to capture calls.
   - Call OrgTemplateExporter.network_templates().
   - Assert DataExporter.write_with_format_selection called with filename 'OrgNetworkTemplates.csv' and api_function_name 'listOrgNetworkTemplates'.

2. If missing, add a small integration test verifying SQLite table created with PK 'id' when OUTPUT_FORMAT='sqlite'.

3. Document test results in PR description.