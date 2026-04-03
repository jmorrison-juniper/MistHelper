Tasks for auditing and remediating Menu #26 (Gateway Templates)

1. Update code (developer):
   - File: MistHelper.py
   - Function: GatewayExportUtils.templates
   - Change: Replace DataExporter.save_data_to_output(...) with DataExporter.write_with_format_selection(templates, "OrgGatewayTemplates.csv", api_function_name="listOrgGatewayTemplates")
   - Ensure DataProcessingUtils.flatten_nested_fields and escape_multiline remain applied.

2. Unit tests (engineer):
   - Add test: tests/unit/test_gateway_templates_export.py
     - Mock mistapi.api.v1.orgs.gatewaytemplates.listOrgGatewayTemplates to return sample data
     - Patch DataExporter.write_with_format_selection and assert called with api_function_name="listOrgGatewayTemplates"
     - Test empty response path returns gracefully

3. Integration test (QA):
   - Add test: tests/integration/test_gateway_templates_sql_export.py
     - Run templates() against a mocked apisession returning sample templates
     - Use a temporary SQLite DB (in-memory or under data/tmp) and verify table created with PK 'id'
     - Verify rows inserted and upsert semantics (call twice with modified row to verify replace)

4. Documentation & Changelog (writer):
   - Update README.md menu count if needed
   - Add changelog entry: version YY.MM.DD.HH.MM - "Audit: menu 26 gateway templates - SQL export compliance"

5. CI Checks (maintainer):
   - Run python -m py_compile MistHelper.py
   - Run pytest -q
   - Ensure tests pass and no flake or syntax errors

Notes:
- Do NOT change ENDPOINT_PRIMARY_KEY_STRATEGIES unless PK strategy is proven incorrect.
- If DataExporter.write_with_format_selection has a different signature, adapt accordingly and add adapter tests.

Owner: @maintainer
Priority: High (data export correctness)
Status: Pending

Estimated effort: 3-4 hours total.