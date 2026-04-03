Tasks (Menu #38):

1. Create tests/unit/test_menu_38_ap_templates.py
   - Mock mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles to return sample AP profiles.
   - Patch DataExporter.write_with_format_selection and DataExporter.save_data_to_output to capture api_function_name.
   - Execute OrgTemplateExporter.ap_templates().
   - Assert that DataExporter.write_with_format_selection/save_data_to_output is called with api_function_name='listOrgAptemplates' (after code change) OR document failure now.

2. Code change (separate PR):
   - Option A (quick): Change DataExporter.save_data_to_output(processed, filename) to include api_function_name='listOrgAptemplates'.
   - Option B (better): Use APIDataFetcher with mistapi.api.v1.orgs.aptemplates.listOrgAptemplates and APIDataFetcher.execute().

3. Integration: Run with OUTPUT_FORMAT='sqlite' and confirm OrgApTemplates table uses PK ['id'] and index 'org_id' present.

4. Update README/changelog with test and behavior note.