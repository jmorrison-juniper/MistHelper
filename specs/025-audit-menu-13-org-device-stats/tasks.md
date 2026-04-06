# Tasks

List of concrete, actionable tasks. These tasks are prioritized to avoid touching the implementation before the IMPLEMENT phase; they prepare specs, tests, fixtures, and configuration proposals.

- id: create-spec-files
  description: Create spec files under specs/025-audit-menu-13-org-device-stats including this spec.md and a brief README describing the endpoint and expected artifacts.
  complexity: small
  dependencies: []

- id: propose-pk-strategy
  description: Author a change proposal for ENDPOINT_PRIMARY_KEY_STRATEGIES to add a composite_pk entry for the device stats endpoint with fields [device_id, metric_name, timestamp] and recommended indexes.
  complexity: medium
  dependencies: [create-spec-files]

- id: create-api-metadata-proposal
  description: Draft the metadata snippet to register function_ref OrgDeviceStatsExporter.device_stats in the operation registry (operation name, menu_id, sql_export_relevant flag).
  complexity: small
  dependencies: [create-spec-files]

- id: draft-unit-test-skeletons
  description: Create unit test skeleton files (pytest) that mock OrgDeviceStatsExporter.device_stats and APIDataFetcher; include tests for flattening, timestamp normalization, and DataExporter invocation stubs.
  complexity: medium
  dependencies: [create-spec-files]

- id: prepare-fixtures
  description: Produce canonical JSON fixture responses representing common and edge-case device-stat payloads (normal, missing fields, duplicate samples, out-of-order timestamps).
  complexity: small
  dependencies: [draft-unit-test-skeletons]

- id: write-sql-verification-scripts
  description: Create scripts that run against a test SQLite DB to validate upsert semantics: insert fixtures, re-insert duplicates, assert row counts and values.
  complexity: medium
  dependencies: [propose-pk-strategy, prepare-fixtures]

- id: create-integration-test-plan
  description: Document an integration test plan that wires mocks for APIDataFetcher to return paginated fixtures and asserts end-to-end CSV + SQLite outputs; include commands to run tests locally.
  complexity: small
  dependencies: [draft-unit-test-skeletons, write-sql-verification-scripts]

- id: update-readme-menu-entry
  description: Prepare a PR patch that updates README/menu index to include menu_id 13, description, function_ref, and spec_dir. Keep it informational; do not change behavior.
  complexity: small
  dependencies: [create-spec-files]

- id: create-qa-checklist
  description: Produce a short QA checklist referencing acceptance criteria, SQL verification steps, and performance/rate-limit checks for reviewers to follow during implementation testing.
  complexity: small
  dependencies: [write-sql-verification-scripts, create-integration-test-plan]

- id: schedule-code-review-and-qa
  description: Coordinate and document a requested reviewer list and a timeline for review/testing post-implementation (who, what to check, expected turnaround).
  complexity: small
  dependencies: [create-qa-checklist, update-readme-menu-entry]

Notes:
- All tasks are preparatory; none modify runtime implementation. Implementation tasks (wiring exporter to write_with_format_selection, adding runtime PK config, and code-level unit test implementations) are intentionally excluded and will be executed in the IMPLEMENT phase.
