Plan to remediate menu #67:

1. Add ENDPOINT_PRIMARY_KEY_STRATEGIES entry for getOrgSitesSle (composite_pk); recommend primary_key ['site_id','sle_category','timestamp'] or ['site_id','metric','timestamp'] depending on API shape.
2. Modify OrgExportUtils.sites_sle_summary to call DataExporter.write_with_format_selection(processed, "OrgSitesSLESummary.csv", api_function_name="getOrgSitesSle").
3. Add unit tests to validate SQL export path and CSV fallback.
4. Run py_compile and pytest.
