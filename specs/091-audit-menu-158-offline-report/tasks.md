# Tasks (actionable, pre-implementation)

- id: refine-spec-and-store
  description: Add spec.md (this artifact) into specs/091-audit-menu-158-offline-report/ and include metadata (menu_id, function_ref, sql_export_relevant).
  complexity: small
  dependencies: []

- id: draft-sql-ddl
  description: Draft SQLite DDL file offline_devices.sql in the spec_dir with recommended columns, composite primary key (device_id, report_timestamp) and indexes (org_id, site_id). Include comments explaining types and constraints.
  complexity: small
  dependencies: refine-spec-and-store

- id: define-pk-strategy_entry
  description: Create a text fragment for ENDPOINT_PRIMARY_KEY_STRATEGIES describing the new entry (operation name, type: composite_pk, primary_key list, indexes). Save as specs/091-audit-menu-158-offline-report/pk_strategy.json (or .md) for implementers.
  complexity: small
  dependencies: draft-sql-ddl

- id: collect-and-curate-fixtures
  description: Create representative input fixtures (JSON and CSV) capturing: normal offline records, missing fields, and large-batch sample. Place under spec_dir/fixtures/.
  complexity: medium
  dependencies: refine-spec-and-store

- id: baseline-test-review
  description: Review existing tests/tests/test_offline_device_reporter.py for coverage and document any gaps (edge cases not covered). Produce a short report in spec_dir/test-plan.md.
  complexity: small
  dependencies: collect-and-curate-fixtures

- id: create-integration-test-skeleton
  description: Add pytest integration test skeleton that will validate: table creation, insert/upsert semantics, index existence, and query results. Tests should use fixtures and a disposable SQLite DB path (tmp_path). Save under specs/091-audit-menu-158-offline-report/tests_integration.py.
  complexity: medium
  dependencies: draft-sql-ddl, collect-and-curate-fixtures, baseline-test-review

- id: write-sql-verification-scripts
  description: Create small SQL/check scripts used by integration tests to assert upsert behavior (e.g., queries to count duplicates, verify primary key constraint, verify indexes). Place under spec_dir/sql_checks/.
  complexity: small
  dependencies: draft-sql-ddl, create-integration-test-skeleton

- id: document-test-runbook
  description: Draft a short README in spec_dir describing how to run unit + integration tests locally, how to validate the SQL upsert behavior manually, and expected results. Include sample pytest commands and SQL snippets.
  complexity: small
  dependencies: create-integration-test-skeleton, write-sql-verification-scripts

- id: prepare-implement-ticket
  description: Produce a ready-to-consume implement-ticket (markdown) that lists code changes to perform, files to edit (e.g., where to add ENDPOINT_PRIMARY_KEY_STRATEGIES entry), tests to update/enable, and verification checklist. Attach all spec_dir artifacts.
  complexity: small
  dependencies: document-test-runbook, define-pk-strategy_entry

- id: peer-review-plan
  description: Request a peer review of the spec_dir artifacts and collect feedback. Log required changes as follow-up tasks if necessary.
  complexity: small
  dependencies: prepare-implement-ticket

Notes:
- All tasks are intentionally preparatory: they produce schema, fixtures, tests skeletons and documentation but do not modify implementation code prior to the implement phase.
- Prioritization: start with refine-spec-and-store, draft-sql-ddl, collect-and-curate-fixtures, then create-integration-test-skeleton. The implement-ticket should be produced only after DDL and tests are in place.
