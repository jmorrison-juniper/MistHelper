# Tasks

Each task below is actionable and scoped. Tasks that change runtime implementation are flagged as IMPLEMENT-phase; they are included for planning but should not be executed in this pre-IMPLEMENT phase.

1. id: spec-review-org-alarms
   - title: Review and finalize specification files
   - description: Confirm spec.md content, acceptance criteria, and spec_dir layout. Ensure notes and SQL relevance are accurately captured.
   - complexity: small
   - dependencies: []

2. id: define-pk-strategy-for-alarms
   - title: Add PK strategy entry to ENDPOINT_PRIMARY_KEY_STRATEGIES
   - description: Propose and add a composite_pk configuration for the alarms endpoint including primary_key: ["id","org_id","timestamp"] and indexes on org_id+timestamp.
   - complexity: small
   - dependencies: spec-review-org-alarms

3. id: design-sql-schema-and-indexes
   - title: Draft SQL table schema and index definitions
   - description: Produce SQL CREATE TABLE statement and index statements for the alarms export (SQLite-focused). Include column types, PKs, and indexes for (org_id, timestamp).
   - complexity: small
   - dependencies: define-pk-strategy-for-alarms

4. id: create-test-fixtures-and-vcr-recordings
   - title: Prepare test fixtures and API recordings
   - description: Capture representative API responses (mock JSON) for: empty result, single page, multi-page with duplicates, and error cases. Store in specs/019-audit-menu-01-org-alarms/fixtures.
   - complexity: medium
   - dependencies: spec-review-org-alarms

5. id: add-unit-test-skeletons
   - title: Add unit test skeletons for OrgAlarmEventExporter
   - description: Create tests that import the exporter and assert behavior using mocks/fixtures. Tests should cover pagination handling, flattening, and invocation of DataExporter.write_with_format_selection. Mark failing tests as expected until IMPLEMENT step completes.
   - complexity: medium
   - dependencies: create-test-fixtures-and-vcr-recordings

6. id: add-sql-verification-test-skeletons
   - title: Add SQL verification tests (idempotency)
   - description: Create tests that use a temporary SQLite DB, run the exporter (mocked) twice against fixtures, and assert no duplicates and update-on-change semantics. Use the schema from design-sql-schema-and-indexes.
   - complexity: medium
   - dependencies: add-unit-test-skeletons, design-sql-schema-and-indexes

7. id: ci-test-integration-plan
   - title: Add CI job plan and labels for integration tests
   - description: Document CI steps to run integration tests (staging or fixture-based), resource needs, and flakiness handling. Add job definitions or checklists (do not modify CI pipelines yet).
   - complexity: small
   - dependencies: create-test-fixtures-and-vcr-recordings

8. id: docs-update-menu-entry
   - title: Update README/menu docs with new operation entry
   - description: Add the menu entry description, function_ref, spec_dir link, and SQL relevance. Do not change user-visible behavior.
   - complexity: small
   - dependencies: spec-review-org-alarms

---
IMPLEMENT-phase tasks (do not execute in this pre-IMPLEMENT stage; listed for planning):

9. id: implement-exporter-integration
   - title: Implement OrgAlarmEventExporter.alarms integration
   - description: Refactor exporter to call DataExporter.write_with_format_selection, implement pagination/retry logic, and perform SQL upsert using composite PK. Ensure logging and metrics.
   - complexity: large
   - dependencies: define-pk-strategy-for-alarms, design-sql-schema-and-indexes, add-unit-test-skeletons

10. id: run-tests-and-fix-failures
    - title: Run unit & integration tests and remediate failures
    - description: Execute full test suite, fix issues, and iterate until green.
    - complexity: medium
    - dependencies: implement-exporter-integration, add-sql-verification-test-skeletons

11. id: finalize-docs-and-release
    - title: Final documentation, version bump, changelog
    - description: Update README, changelog, and create release commit with required trailer.
    - complexity: small
    - dependencies: run-tests-and-fix-failures


Priority ordering (pre-IMPLEMENT):
1. spec-review-org-alarms
2. define-pk-strategy-for-alarms
3. design-sql-schema-and-indexes
4. create-test-fixtures-and-vcr-recordings
5. add-unit-test-skeletons
6. add-sql-verification-test-skeletons
7. ci-test-integration-plan
8. docs-update-menu-entry

Notes:
- Tasks explicitly modifying runtime exporter code are marked IMPLEMENT-phase and should not be executed until the implement step.
- Test skeletons should be written so they pass once implementation is complete; failures are acceptable pre-IMPLEMENT but should be visible in CI to guide the implement phase.
