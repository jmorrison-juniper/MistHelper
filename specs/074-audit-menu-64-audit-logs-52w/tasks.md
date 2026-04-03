Tasks:
1. Open MistHelper.py and locate OrgExportUtils.audit_logs; capture exact mistapi function name used and current output call.
2. Add or confirm ENDPOINT_PRIMARY_KEY_STRATEGIES['listOrgAuditLogs'] = {'type':'natural_pk','primary_key':['id'],'indexes':['org_id','actor','action']}.
3. Replace save_data_to_output or equivalent with DataExporter.write_with_format_selection(processed_data, "OrgAuditLogs", api_function_name="listOrgAuditLogs").
4. Add tests/tests_audit_logs.py: test_audit_logs_writes_sql_compatible_call and test_audit_logs_handles_empty_result.
5. Run test suite and fix issues.

Notes: Keep behavior identical for CSV output when OUTPUT_FORMAT forces CSV.