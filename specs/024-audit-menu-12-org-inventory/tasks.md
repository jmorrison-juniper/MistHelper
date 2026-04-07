# Tasks

Below are actionable tasks to prepare for implementation. Tasks are ordered to prioritize design, tests, and review work before touching production code.

1. id: define-primary-key-strategy
   - title: Define and document primary key strategy for OrgInventory export
   - description: Decide primary_key fields (recommended: ["id"]; evaluate adding "org_id"). Produce a short rationale and record in specs/024-audit-menu-12-org-inventory/pk_strategy.md.
   - complexity: small
   - dependencies: []

2. id: design-sql-schema-and-indexes
   - title: Design SQL table schema and index definitions
   - description: Produce SQL DDL snippet for devices table (types, PRIMARY KEY, indexes for org_id, mac, serial). Place file specs/024-audit-menu-12-org-inventory/schema.sql and include a short rationale for chosen columns and NOT NULL choices.
   - complexity: small
   - dependencies: [define-primary-key-strategy]

3. id: create-sample-api-fixtures
   - title: Create representative API response fixtures
   - description: Capture 3–5 fixture JSON responses covering typical device, missing optional fields, and updated fields for testing; store under specs/024-audit-menu-12-org-inventory/fixtures/.
   - complexity: small
   - dependencies: []

4. id: write-unit-test-specs
   - title: Draft unit test cases and mocks
   - description: Create concrete unit test specifications (test vectors, expected flattened rows) and test skeletons that will use mocked OrgInventoryExporter.inventory and APIDataFetcher. Place under specs/024-audit-menu-12-org-inventory/tests/unit_tests.md.
   - complexity: small
   - dependencies: [create-sample-api-fixtures]

5. id: write-integration-test-specs
   - title: Draft integration test cases (SQLite verification)
   - description: Define integration test flows: test DB setup, run exporter against fixtures, verify upsert semantics by running twice with changes, assert indexes and counts. Provide SQL assertions and expected outcomes.
   - complexity: medium
   - dependencies: [design-sql-schema-and-indexes, create-sample-api-fixtures]

6. id: document-error-and-retry-behavior
   - title: Specify error handling and retry policy
   - description: Document expected retry/backoff behaviour for API failures and how exporter surfaces errors (log format, exit codes). Place in specs/024-audit-menu-12-org-inventory/errors.md.
   - complexity: small
   - dependencies: []

7. id: prepare-ci-test-matrix-entry
   - title: Prepare CI job/test-matrix notes
   - description: Draft CI-level instructions to run the new unit and integration tests (requirements, env variables, SQLite usage) and add to specs for CI owner to wire up later.
   - complexity: small
   - dependencies: [write-unit-test-specs, write-integration-test-specs]

8. id: update-readme-and-menu-docs
   - title: Draft README/menu documentation updates
   - description: Prepare documentation entry (menu register) describing Menu 12, expected outputs (CSV/SQL), and sample commands. Add sample output snippets to specs dir.
   - complexity: small
   - dependencies: [design-sql-schema-and-indexes]

9. id: review-and-signoff
   - title: Conduct peer review and capture sign-off
   - description: Run a lightweight review with stakeholders of spec, SQL schema, test specs, and fixtures. Collect approvals and record any requested changes.
   - complexity: small
   - dependencies: [define-primary-key-strategy, design-sql-schema-and-indexes, create-sample-api-fixtures, write-unit-test-specs, write-integration-test-specs, document-error-and-retry-behavior, update-readme-and-menu-docs]

10. id: implement-exporter-and-tests (IMPLEMENT PHASE - DO NOT START YET)
    - title: Implement exporter, PK config, and tests
    - description: (Implementation task reserved for IMPLEMENT phase) Add PK strategy to ENDPOINT_PRIMARY_KEY_STRATEGIES, implement exporter wiring (call DataExporter.write_with_format_selection), add unit and integration tests, run test suite, and fix issues until green.
    - complexity: large
    - dependencies: [review-and-signoff]

Notes:
- Tasks 1–9 must be completed, reviewed, and signed off before task 10 begins.
- Tasks were intentionally written to avoid modifying production code prior to implementation (task 10). Tasks produce the artifacts and approvals needed to implement safely.

---
