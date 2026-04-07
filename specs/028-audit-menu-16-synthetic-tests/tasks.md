# Tasks — actionable and dependency-ordered

Below are concrete tasks prepared for the IMPLEMENT phase. Tasks are ordered and include dependencies. Do not implement code until the IMPLEMENT phase begins.

1. id: spec-add-menu-16
   - title: Add spec artifacts to repo
   - description: Create `specs/028-audit-menu-16-synthetic-tests/spec.md` and include example API payloads and expected flattened records. Add README stub referencing menu_id 16.
   - complexity: small
   - dependencies: []

2. id: design-confirm-pk-and-api-name
   - title: Confirm PK columns and canonical api_function_name
   - description: Decide exact composite PK column names/types (recommendation: gateway_id, test_run_id, timestamp) and lock the `api_function_name` string mapping to `GatewayTestExporter.synthetic_tests` for use by DataExporter.
   - complexity: small
   - dependencies: ["spec-add-menu-16"]

3. id: create-test-fixtures-synthetic-tests
   - title: Create unit/integration test fixtures
   - description: Add JSON fixture files (good payload, duplicate-run payload, large payload) under `specs/028-audit-menu-16-synthetic-tests/fixtures` to drive tests.
   - complexity: small
   - dependencies: ["spec-add-menu-16"]

4. id: tests-scaffold
   - title: Add test scaffolding and helpers
   - description: Add test modules and helper utilities to mock DataExporter, create temporary SQLite DBs, and validate upsert semantics. Do not add assertions specific to implementation yet; just scaffold test harnesses and fixtures usage.
   - complexity: medium
   - dependencies: ["create-test-fixtures-synthetic-tests"]

5. id: endpoint-pk-config-entry
   - title: Draft ENDPOINT_PRIMARY_KEY_STRATEGIES entry
   - description: Prepare the config entry describing type=composite_pk and primary_key list for the exporter. Add migration notes in the spec directory. (This is a repo config change that will be committed during IMPLEMENT.)
   - complexity: small
   - dependencies: ["design-confirm-pk-and-api-name"]

6. id: exporter-interface-spec
   - title: Define exporter-to-dataexporter contract
   - description: Document required fields that GatewayTestExporter.synthetic_tests must emit (e.g., gateway_id, test_run_id, timestamp, metrics...) and the exact call signature for DataExporter.write_with_format_selection(..., api_function_name=...).
   - complexity: small
   - dependencies: ["design-confirm-pk-and-api-name"]

7. id: implementation-refactor-exporter
   - title: Refactor GatewayTestExporter.synthetic_tests to use DataExporter
   - description: Update function to (a) produce deterministic flattened records with PK fields; (b) call DataExporter.write_with_format_selection(records, filename, api_function_name='GatewayTestExporter.synthetic_tests'); (c) add logging and assertions for sanity checks.
   - complexity: large
   - dependencies: ["endpoint-pk-config-entry","exporter-interface-spec","tests-scaffold"]

8. id: implementation-add-sql-schema-and-upsert
   - title: Implement SQL table creation and upsert semantics
   - description: Ensure SQLite export path creates table with composite primary key and uses `INSERT OR REPLACE` (or equivalent) to guarantee idempotent exports. Add index on gateway_id and timestamp.
   - complexity: medium
   - dependencies: ["implementation-refactor-exporter","endpoint-pk-config_entry"]

9. id: unit-tests-for-exporter
   - title: Write unit tests for exporter behavior
   - description: Implement unit tests that mock DataExporter and assert call parameters, PK derivation, and flattening correctness.
   - complexity: medium
   - dependencies: ["implementation-refactor-exporter","tests-scaffold"]

10. id: integration-tests-sql-upsert
    - title: Integration tests for SQLite upsert behavior
    - description: Run full export to a temporary SQLite DB using fixtures; verify table schema, indexes, initial insert, and upsert (run twice with changed data and assert update, not duplicate insert).
    - complexity: large
    - dependencies: ["implementation-add-sql-schema-and-upsert","unit-tests-for-exporter"]

11. id: performance-smoke-test
    - title: Run large-payload export and measure duration
    - description: Use the large payload fixture to test batching, rate limits, and DB upsert performance; document results and acceptable thresholds.
    - complexity: medium
    - dependencies: ["integration-tests-sql-upsert"]

12. id: docs-and-readme-update
    - title: Update README and menu documentation
    - description: Add menu entry documentation, version changelog, and migration notes in `specs/028-audit-menu-16-synthetic-tests`.
    - complexity: small
    - dependencies: ["integration-tests-sql-upsert"]

13. id: ci-and-pipeline_validation
    - title: Ensure py_compile and CI tasks pass
    - description: Add tests to CI matrix if needed; run `python -m py_compile` and test suite; fix issues until green.
    - complexity: medium
    - dependencies: ["unit-tests-for-exporter","integration-tests-sql-upsert"]

14. id: final-review-and-merge
    - title: Code review, finalize spec, merge to main
    - description: Run final review, squash/fix commits, merge and ensure CI passes on main.
    - complexity: small
    - dependencies: ["ci-and-pipeline_validation","docs-and-readme-update"]


## Notes on prioritization
- Early work should focus on spec, design, and test fixtures (tasks 1–4) to allow TDD during the IMPLEMENT phase.
- The actual code changes (tasks 7–9) are explicitly staged for IMPLEMENT and depend on completed design and test harness.

## Where to find artifacts
- Spec and fixtures: `specs/028-audit-menu-16-synthetic-tests/`

