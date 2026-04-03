Plan: Audit & Remediation for Menu #26 (Gateway Templates)

Objective:
- Ensure GatewayExportUtils.templates() is SQL-export compliant and covered by tests.

Steps:
1. Static Analysis
   - Verify current implementation (done): templates() calls mistapi listOrgGatewayTemplates and DataExporter.save_data_to_output.
   - Confirm ENDPOINT_PRIMARY_KEY_STRATEGIES contains listOrgGatewayTemplates (done).

2. Design Change
   - Update templates() to use DataExporter.write_with_format_selection(templates, filename, api_function_name="listOrgGatewayTemplates") to enable SQL export behavior and PK strategy mapping.
   - Preserve existing CSV output behavior and logging.

3. Unit Tests
   - Add unit test mocking mistapi response to verify DataExporter.write_with_format_selection called with expected args.
   - Add unit tests for empty response handling (no templates).

4. Integration Tests
   - Add test that runs templates() writing to a temporary SQLite DB (in data/test_...) and asserts table schema, primary keys, and sample rows are upserted correctly.

5. Documentation
   - Update README operation list if needed.
   - Add changelog entry.

6. Validation
   - Run python -m py_compile MistHelper.py
   - Run existing test suite (pytest).

Assumptions & Constraints:
- Modifications will not change public CLI behavior.
- No changes to endpoint primary key strategy required.

Deliverables:
- Patch to MistHelper.py updating GatewayExportUtils.templates
- New unit and integration tests under tests/unit and tests/integration
- specs/038-audit-menu-26-gateway-templates/* (this spec set)

Timeline (estimates):
- Code change + unit tests: 1-2 hours
- Integration tests + validation: 1 hour

Done: This plan is advisory only; no implementation changes in this spec.