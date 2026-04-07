# Tasks

Below are concrete, non-implementation tasks that prepare repository and team to implement Zone Configuration Analysis safely. Stop before any code-level implementation.

1. id: verify-api-function
   - Short description: Confirm existence, import path, and signature of ZoneConfigurationAnalyzer.analyze; capture sample return payloads.
   - Complexity: small
   - Dependencies: none

2. id: analyze-return-schema
   - Short description: From verified function, extract the output schema (fields, nested objects) and identify stable identifiers (id/org_id/site_id/name/timestamp).
   - Complexity: small
   - Dependencies: verify-api-function

3. id: choose-primary-key-strategy
   - Short description: Decide and document final primary-key strategy (recommended natural_pk) and specify exact primary_key columns (e.g., ['org_id','id']). Document rationale.
   - Complexity: medium
   - Dependencies: analyze-return-schema

4. id: draft-sql-schema-and-upsert-examples
   - Short description: Write SQL DDL for SQLite table(s) for export and include example upsert statements (INSERT OR REPLACE or UPSERT) demonstrating expected behavior.
   - Complexity: small
   - Dependencies: choose-primary-key-strategy

5. id: create-spec-files
   - Short description: Create spec documents under specs/089-audit-menu-119-zone-analysis (spec.md, plan.md, tasks.md) and include PK, api_function_name, and SQL drafts.
   - Complexity: small
   - Dependencies: choose-primary-key-strategy, draft-sql-schema-and-upsert-examples

6. id: draft-unit-test-plan
   - Short description: Enumerate unit tests for ZoneConfigurationAnalyzer behaviors (edge cases, nulls, flattening), with inputs/expected outputs and fixtures to capture.
   - Complexity: small
   - Dependencies: analyze-return-schema

7. id: scaffold-integration-test-plan
   - Short description: Define integration tests that verify end-to-end analyzer -> exporter (CSV+SQLite) and SQL upsert semantics; list fixtures and required mocks.
   - Complexity: medium
   - Dependencies: draft-unit-test-plan, draft-sql-schema-and-upsert-examples

8. id: create-test-stubs-and-fixtures
   - Short description: Add test file stubs and JSON fixtures under tests/ referencing the unit and integration plans (do not implement assertions beyond placeholders). Include instructions for how CI should run them.
   - Complexity: medium
   - Dependencies: scaffold-integration-test-plan, draft-unit-test-plan

9. id: register-endpoint-metadata-draft
   - Short description: Draft the required ENDPOINT_PRIMARY_KEY_STRATEGIES (or equivalent) entry in design docs showing operation key, api_function_name, type, primary_key, and indexes for reviewer approval. (Design-only, no code changes.)
   - Complexity: small
   - Dependencies: choose-primary-key-strategy, verify-api-function

10. id: create-implementation-ticket
    - Short description: Prepare an implementation ticket (JIRA/GH issue) listing required code changes, referencing spec and tests, estimating effort, and scheduling the implement phase.
    - Complexity: small
    - Dependencies: stakeholder-review-and-signoff

Priority order (pre-implementation): verify-api-function -> analyze-return-schema -> choose-primary-key-strategy -> draft-sql-schema-and-upsert-examples -> create-spec-files -> draft-unit-test-plan -> scaffold-integration-test-plan -> create-test-stubs-and-fixtures -> register-endpoint-metadata-draft -> create-implementation-ticket

Notes:
- None of the above tasks change production code; they prepare artifacts required for a safe implementation phase.
- After approval, the implement phase tasks will include: coding analyzer changes (if any), wiring exporter to write_with_format_selection, adding upsert logic, and running CI to validate.
