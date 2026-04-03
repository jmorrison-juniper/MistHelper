# Feature Specification: Audit Menu #3 - Audit Logs Export
**Created**: 2026-04-03
**Status**: Audit

## Current State Analysis
OrgExportUtils.audit_logs is a static method that:
- Prompts (cached) for org_id via ConfigUtils.get_cached_or_prompted_org_id()
- Builds kwargs for API call: limit=1000 and either duration (if provided), duration for last 24 hours when full_history=False, or start=0 for full history
- Calls mistapi.api.v1.orgs.logs.listOrgAuditLogs(apisession, org_id, **kwargs)
- Uses mistapi.get_all to page through results
- Flattens and escapes multiline fields via DataProcessingUtils
- Calls DataExporter.save_data_to_output(data, "OrgAuditLogs.csv") to write CSV
- Logs progress and returns; raises exception on failure

## Issues Found
- DataExporter.save_data_to_output is used; however SQL export requires using DataExporter.write_with_format_selection(api_function_name=...) to support SQLite export. The current call does not pass api_function_name nor use write_with_format_selection.
- ENDPOINT_PRIMARY_KEY_STRATEGIES does not appear to contain an explicit entry for audit logs (no "listOrgAuditLogs" or similar key). Without a strategy, SQLite exports will fall back to the "default" strategy which uses auto-increment misthelper_internal_id and lacks useful indexes.
- audit_logs returns early with no output when API returns empty; this matches pattern elsewhere but may be acceptable.
- No specific error handling for unexpected schema (missing expected fields) — DataProcessingUtils.flatten_nested_fields may handle this, but there are no assertions.

## SQL Export Compliance
- Does it use DataExporter.write_with_format_selection with api_function_name? No. It calls DataExporter.save_data_to_output only.
- Is there an ENDPOINT_PRIMARY_KEY_STRATEGIES entry? No specific entry for audit logs (e.g., "listOrgAuditLogs" or "searchOrgAuditLogs") was found. The default fallback will be used.

If not compliant, what changes are needed?
- Change DataExporter.save_data_to_output(...) to DataExporter.write_with_format_selection(processed_data, "OrgAuditLogs", api_function_name="listOrgAuditLogs") or similar call. The write_with_format_selection function signature expects the data, filename base, and api_function_name argument to map to ENDPOINT_PRIMARY_KEY_STRATEGIES.
- Add ENDPOINT_PRIMARY_KEY_STRATEGIES entry for "listOrgAuditLogs" (or exact key used by the code) with type "composite_pk" and appropriate primary_key: e.g., ["id", "org_id", "timestamp"] and indexes: ["org_id", "timestamp", "type", "actor"] (actor/user fields optional), and description.

## Test Coverage
- tests/test_exports.py contains tests for 52-week exports and other exporters but does not include a test for OrgExportUtils.audit_logs (Menu #3). No unit test found that asserts write_with_format_selection is used or that ENDPOINT_PRIMARY_KEY_STRATEGIES contains audit logs.

## Acceptance Criteria for Fixes
- audit_logs writes outputs using DataExporter.write_with_format_selection with api_function_name="listOrgAuditLogs" so SQLite export includes proper schema and upsert behavior.
- ENDPOINT_PRIMARY_KEY_STRATEGIES contains an entry for "listOrgAuditLogs" with composite_pk primary key including id, org_id, timestamp, plus reasonable indexes.
- Unit test(s) added to tests/ asserting that when audit_logs is invoked, DataExporter.write_with_format_selection is called with the correct api_function_name and that the file name is OrgAuditLogs (or OrgAuditLogs.csv for CSV path). Mock mistapi.get_all and ConfigUtils for deterministic behavior.
- Tests must pass with CI (existing test suite unchanged except added tests).
