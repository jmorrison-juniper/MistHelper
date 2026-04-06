# Tasks

Below are actionable tasks to prepare for implementation. They avoid changing production implementation; they focus on discovery, design, tests, and documentation.

1. Task id: audit-pk-entries
   - Description: Inspect PK registry and confirm existence and format of entries sitesMissingInfrastructure and sitesWithOfflineInfrastructure. Capture sample rows and fields.
   - Complexity: small
   - Dependencies: none

2. Task id: review-analyze-api-signature
   - Description: Locate SiteInventoryHealthAnalyzer.analyze in codebase, record function signature, expected return type, and example outputs. Create a minimal contract doc describing expected fields.
   - Complexity: small
   - Dependencies: audit-pk-entries

3. Task id: define-pk-strategy-for-menu-121
   - Description: Decide and document final primary-key strategy (recommended natural_pk) including exact primary key columns and rationale. Produce SQL create-table statement draft and required indexes.
   - Complexity: medium
   - Dependencies: audit-pk-entries, review-analyze-api-signature

4. Task id: create-sql-schema-and-migration-skeleton
   - Description: Add SQL DDL (SQLite-compatible) and migration skeleton files under specs/090-audit-menu-121-inventory-health/ddl. Include table, primary key/unique constraints, and indexes. Do not run migrations yet.
   - Complexity: medium
   - Dependencies: define-pk-strategy-for-menu-121

5. Task id: author-unit-test-skeletons
   - Description: Create unit test files to validate analyze() outputs using mocks. Include tests for normal, empty, and malformed input. Use pytest conventions and put tests under tests/unit/.
   - Complexity: medium
   - Dependencies: review-analyze-api-signature

6. Task id: author-integration-test-skeletons
   - Description: Create integration test scaffolding that writes to an ephemeral SQLite DB, runs exporter write flow (mock exporter if needed), and includes SQL verification steps (insert -> re-run -> assert no duplicates and updated fields).
   - Complexity: medium
   - Dependencies: create-sql-schema-and-migration-skeleton, author-unit-test-skeletons

7. Task id: create-sql-verification-scripts
   - Description: Add executable SQL/Python scripts that programmatically verify upsert behavior for the table(s) (clear table, insert sample, re-run upsert, assert counts/values). Place under specs/090-audit-menu-121-inventory-health/testsql.
   - Complexity: small
   - Dependencies: create-sql-schema-and-migration-skeleton

8. Task id: add-spec-documents
   - Description: Commit spec.md, plan.md, and tasks.md into specs/090-audit-menu-121-inventory-health. Ensure they reference the artifacts produced by earlier tasks.
   - Complexity: small
   - Dependencies: audit-pk-entries, define-pk-strategy-for-menu-121

9. Task id: update-readme-and-menu-index (docs-only)
   - Description: Propose README update lines indicating the new menu operation (121) and link to spec dir. Keep it informational; do not change operation implementation. Prepare PR text for later.
   - Complexity: small
   - Dependencies: add-spec-documents

10. Task id: create-implementation-ticket
    - Description: Create an implementation ticket (JIRA/GH issue) listing required code changes, referencing spec and tests, estimating effort, and scheduling the implement phase.
    - Complexity: small
    - Dependencies: stakeholder-review-and-approval

11. Task id: create-implementation-ticket
    - Description: Create an implementation ticket (JIRA/GH issue) listing required code changes, referencing spec and tests, estimating effort, and scheduling the implement phase.
    - Complexity: small
    - Dependencies: stakeholder-review-and-approval

Notes:
- None of the above tasks change production code; they prepare artifacts required for a safe implementation phase.
- After approval, the implement phase tasks will include: coding analyzer changes (if any), wiring exporter to write_with_format_selection, adding upsert logic, and running CI to validate.
