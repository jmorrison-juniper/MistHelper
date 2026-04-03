Plan to remediate menu #66:

1. Add or map PK strategy entries for API endpoints used:
   - getOrgSle -> define strategy (likely composite_pk or natural depending on returned schema)
   - getOrgSitesSle -> likely composite_pk with primary_key ['site_id','metric','timestamp'] or similar.
2. Update OrgExportUtils.sle_metrics to call DataExporter.write_with_format_selection(processed, "OrgSLEMetrics.csv", api_function_name="getOrgSle") or use getOrgSitesSle for site-level outputs.
3. Add unit tests to tests/unit to assert:
   - DataExporter.write_with_format_selection is called with api_function_name when SQL export desired (mocked).
   - When save_data_to_output is used, behavior remains unchanged.
4. Run py_compile and test suite.

Assumptions:
- API responses lack stable 'id' fields for some metric types; composite PK likely required.
- Backward compatibility: keep CSV saving if SQL not selected.
