Plan:
1. Inspect OrgExportUtils.audit_logs implementation to confirm current export path. If it uses save_data_to_output or similar, update to DataExporter.write_with_format_selection(processed_data, "OrgAuditLogs", api_function_name="listOrgAuditLogs").
2. Add ENDPOINT_PRIMARY_KEY_STRATEGIES entry for 'listOrgAuditLogs' using natural_pk with 'id' or composite as appropriate.
3. Create tests/tests_audit_logs.py with tests to assert DataExporter.write_with_format_selection called and to validate empty-result handling.
4. Run python -m py_compile and pytest; fix any failures.

Deliverables:
- PK strategy entry
- Code update to use write_with_format_selection
- Unit tests covering non-empty and empty cases
