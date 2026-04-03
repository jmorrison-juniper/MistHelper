# Tasks for Audit Menu #3 - Audit Logs Export

1. Add PK Strategy Entry
- File: MistHelper.py
- Task: Add a new entry to ENDPOINT_PRIMARY_KEY_STRATEGIES:
  Key: "listOrgAuditLogs"
  Value: {
    "type": "composite_pk",
    "primary_key": ["id", "org_id", "timestamp"],
    "indexes": ["org_id", "timestamp", "type", "actor"],
    "unique_constraints": [],
    "description": "Organization audit logs with composite key for time-series uniqueness",
  }
- Notes: Follow existing dict formatting and place near other composite_pk entries.

2. Update audit_logs Export Call
- File: MistHelper.py
- Task: Replace DataExporter.save_data_to_output(data, "OrgAuditLogs.csv") with:
  DataExporter.write_with_format_selection(data, "OrgAuditLogs", api_function_name="listOrgAuditLogs")
- Notes: Ensure DataProcessingUtils.flatten_nested_fields and escape_multiline outputs the list of dicts expected by write_with_format_selection. Preserve logging and prints.

3. Add Unit Tests
- File: tests/test_audit_logs.py (new)
- Tasks:
  a) test_audit_logs_writes_sql_compatible_call
     - Monkeypatch ConfigUtils.get_cached_or_prompted_org_id to return "org1"
     - Monkeypatch mistapi.api.v1.orgs.logs.listOrgAuditLogs to return MagicMock
     - Monkeypatch mistapi.get_all to return sample audit log records
     - Monkeypatch DataExporter.write_with_format_selection to record calls
     - Call OrgExportUtils.audit_logs()
     - Assert write_with_format_selection called with api_function_name="listOrgAuditLogs" and filename base "OrgAuditLogs"

  b) test_audit_logs_handles_empty_result
     - Monkeypatch get_all to return []
     - Ensure audit_logs returns without calling write_with_format_selection (or writes empty file according to project pattern). Assert behavior consistent with other exporters.

4. Run Tests
- Command: pytest -q
- Verify all tests pass.

5. Documentation
- Optional: Add brief changelog entry in README.md noting SQL export compliance for menu #3.

6. Commit
- Run python -m py_compile MistHelper.py to validate syntax
- git add changes and tests
- git commit -m "version 2026.04.03.1500 - Make audit_logs SQL export compliant; add PK strategy and tests"
- Include Co-authored-by trailer per project policy

7. CI Verification
- Push changes and ensure CI passes (container build workflow will validate syntax before build).
