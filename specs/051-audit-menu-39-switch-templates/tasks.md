Tasks (Menu #39):

1. Create tests/unit/test_menu_39_switch_templates.py
   - Mock mistapi.api.v1.orgs.networktemplates.listOrgNetworkTemplates to return sample network templates.
   - Patch DataExporter.write_with_format_selection to capture api_function_name.
   - Call OrgTemplateExporter.switch_templates().
   - Assert DataExporter.write_with_format_selection is invoked with api_function_name 'listOrgNetworkTemplates'.

2. Code change (separate PR):
   - Add api_function_name parameter to DataExporter.save_data_to_output calls in OrgTemplateExporter.switch_templates (or use APIDataFetcher).

3. Integration test: Run export with OUTPUT_FORMAT='sqlite' and assert OrgSwitchTemplates table uses 'id' as primary key and 'org_id' index exists.

4. Document changes in README and update spec index.