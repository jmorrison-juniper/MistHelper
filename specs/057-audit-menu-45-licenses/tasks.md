tasks:
- audit-45-1: Confirm exact call site of DataExporter in OrgAdminExporter.licenses and capture lines (owner: dev, estimate: 1h)
- audit-45-2: Add unit test mocking mistapi to exercise OrgAdminExporter.licenses and assert DataExporter.save_data_to_output called with api_function_name (owner: dev, estimate: 2h)
- audit-45-3: Add integration test for SQLite write verifying table name and PK strategy applied (owner: dev, estimate: 2h)
- audit-45-4: Document findings in README or changelog (owner: dev, estimate: 30m)
