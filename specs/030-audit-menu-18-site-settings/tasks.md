# Tasks

- id: add-endpoint-pk-entry
  title: Add primary-key strategy for getSiteSetting
  description: Create an ENDPOINT_PRIMARY_KEY_STRATEGIES entry for the getSiteSetting endpoint with composite_pk and primary_key ["site_id","setting_name"], include recommended indexes and a brief rationale comment. Commit to the configuration module where other endpoint strategies are defined.
  complexity: small
  dependencies: []

- id: add-api-function-name-metadata
  title: Attach api_function_name metadata for menu 18
  description: Ensure the endpoint metadata for menu_id 18 includes api_function_name: "getSiteSetting" (or exact SDK function), so DataExporter can record provenance and apply SQL schema correctly.
  complexity: small
  dependencies: []

- id: create-spec-files
  title: Create spec artifacts in specs/030-audit-menu-18-site-settings
  description: Add spec.md (this spec), plan.md (this plan), and tasks.md (this task list) into the specified spec_dir. Ensure filenames and minimal frontmatter if used by project tooling.
  complexity: small
  dependencies: []

- id: implement-exporter-write-selection
  title: Refactor SiteConfigExporter.settings to use DataExporter.write_with_format_selection
  description: Update SiteConfigExporter.settings to normalize settings records and call DataExporter.write_with_format_selection(data, filename, api_function_name='getSiteSetting'). Ensure the function passes the proper api name and that SQL path uses endpoint PK strategy for table creation/upsert.
  complexity: medium
  dependencies: [add-endpoint-pk-entry, add-api-function-name-m.metadata]

- id: add-normalization-adapter
  title: Add normalization adapter for site settings
  description: Implement small helper(s) that take SDK responses (list or dict) and emit rows with fields: site_id, setting_name, setting_value, source, last_updated. Include assertions to validate required fields.
  complexity: small
  dependencies: [implement-exporter-write-selection]

- id: add-unit-tests-exporter
  title: Unit tests for SiteConfigExporter.settings
  description: Write unit tests that mock the Mist API and DataExporter. Tests should assert normalization, that write_with_format_selection is invoked with api_function_name, and failure handling.
  complexity: medium
  dependencies: [implement-exporter-write-selection, add-normalization-adapter]

- id: add-integration-tests-sql
  title: Integration tests to verify SQLite schema and upsert
  description: Add integration tests that run exporter against a synthetic dataset and a temporary SQLite DB. Verify table schema (composite PK present), indexes, and that re-running exporter performs upserts (no duplicate logical rows and updated values).
  complexity: large
  dependencies: [add-endpoint-pk-entry, implement-exporter-write-selection]

- id: add-sql-verification-tests
  title: Targeted SQL verification
  description: Small focused tests that inspect PRAGMA table_info/table_indexes and validate ON CONFLICT/INSERT OR REPLACE semantics behave as expected for the composite key. Run as part of integration suite.
  complexity: medium
  dependencies: [add-integration-tests-sql]

- id: update-readme-and-changelog
  title: Document menu 18 and version change
  description: Add menu item to README menu table, bump version string in changelog/README using UTC timestamp format, and reference spec directory.
  complexity: small
  dependencies: [implement-exporter-write-selection, add-endpoint-pk-entry]

- id: ci-test-integration
  title: Add integration tests to CI pipeline
  description: Ensure new unit and integration tests run in CI; add ephemeral SQLite environment if required and mark slow tests appropriately. Update CI config if necessary.
  complexity: medium
  dependencies: [add-unit-tests-exporter, add-integration-tests-sql]

- id: code-review-and-qa
  title: Peer review and QA run
  description: Create PR, request review, and run manual QA for edge cases (missing setting_name, nulls, very large setting values). Capture and fix any issues discovered.
  complexity: small
  dependencies: [add-unit-tests-exporter, add-integration-tests-sql, update-readme-and-changelog]


Priority ordering notes:
1. add-endpoint-pk-entry and add-api-function-name-metadata (blocking, must complete first)
2. create-spec-files (parallel)
3. implement-exporter-write-selection and add-normalization-adapter
4. add-unit-tests-exporter
5. add-integration-tests-sql and add-sql-verification-tests
6. update-readme-and-changelog, ci-test-integration
7. code-review-and-qa

