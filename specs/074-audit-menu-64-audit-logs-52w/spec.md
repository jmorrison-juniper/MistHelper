Spec: Menu 64 — WIP Export audit logs 52 weeks (OrgExportUtils.audit_logs(full_history=True))

Summary of findings:
- OrgExportUtils.audit_logs(full_history=True) exists in MistHelper.py and is wired via menu (menu 64 refers to Audit Logs 52w).
- Existing spec (specs/021-audit-menu-03-audit-logs) documents that audit_logs should call DataExporter.write_with_format_selection with api_function_name 'listOrgAuditLogs'; that change may not yet be implemented.
- Tests: No dedicated unit test found asserting SQL-export compliance for OrgExportUtils.audit_logs; prior tasks planned adding tests/tests_audit_logs.py.

Action required: Align audit_logs with DataExporter.write_with_format_selection pattern and add PK strategy entry for listOrgAuditLogs in ENDPOINT_PRIMARY_KEY_STRATEGIES.
