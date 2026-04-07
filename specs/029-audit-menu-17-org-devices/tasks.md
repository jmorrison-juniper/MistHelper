# Tasks

Each task entry: id, description, complexity, dependencies.

- id: review-current-exporter
  description: Inspect OrgInventoryExporter.devices source code to document existing control flow, whether it references getOrgDevices or listOrgDevices, and where api_function_name is set.
  complexity: small
  dependencies: []

- id: document-pk-mismatch
  description: Create a short technical note (in spec_dir) that explains the getOrgDevices vs listOrgDevices PK mismatch, including example payloads showing differing keys/fields.
  complexity: small
  dependencies: [review-current-exporter]

- id: propose-canonical-api-and-pk
  description: Choose canonical API function name (recommend listOrgDevices) and draft the ENDPOINT_PRIMARY_KEY_STRATEGIES entry (natural_pk with primary_key ['id'] and recommended indexes). Produce a concrete JSON/YAML snippet to be applied during IMPLEMENT.
  complexity: small
  dependencies: [document-pk-mismatch]

- id: create-test-skeletons-unit
  description: Add unit test skeleton files for OrgInventoryExporter.devices (tests/test_org_inventory_exporter_devices.py) with placeholder tests for flattening, PK extraction, and write_with_format_selection call (use mocks). Do not implement production code changes.
  complexity: small
  dependencies: [propose-canonical-api-and-pk]

- id: design-integration-tests-and-mocks
  description: Define integration test scenarios and mock responses for listOrgDevices (happy path, device without id, device updated). Include SQL verification steps and queries to run against ephemeral SQLite DB.
  complexity: medium
  dependencies: [propose-canonical-api-and-pk]

- id: create-sql-verification-script
  description: Draft SQL queries and a short PowerShell script (or test helper) that runs against the test SQLite DB to verify primary key behavior: table schema, count stability after repeated upserts, and sample device update verification.
  complexity: small
  dependencies: [design-integration-tests-and-mocks]

- id: add-regression-test-for-api-name
  description: Create a simple regression test that fails if OrgInventoryExporter.devices does not use the canonical api_function_name (or mapping). This prevents future reintroduction of the PK mismatch.
  complexity: small
  dependencies: [create-test-skeletons-unit]

- id: prepare-spec-and-plan-files
  description: Save spec.md and plan.md into specs/029-audit-menu-17-org-devices and include an implementation checklist. Ensure notes mention SQL_PARTIAL and intended fix.
  complexity: small
  dependencies: [propose-canonical-api-and-pk]

- id: prepare-pr-template-and-review-criteria
  description: Draft a PR template checklist and reviewer guidance focusing on: PK strategy correctness, SQL upsert behavior, tests coverage, and regression tests. Include SQL verification steps for reviewers to run locally.
  complexity: small
  dependencies: [create-sql-verification-script, add-regression-test-for-api-name]

Priority ordering (pre-IMPLEMENT):
1. review-current-exporter
2. document-pk-mismatch
3. propose-canonical-api-and-pk
4. prepare-spec-and-plan-files
5. create-test-skeletons-unit
6. design-integration-tests-and-mocks
7. create-sql-verification-script
8. add-regression-test-for-api-name
9. prepare-pr-template-and-review-criteria

Notes:
- None of these tasks modify production code; they prepare the ground for a safe IMPLEMENT phase.
- Tasks are scoped to minimize risk: drafting configs and tests first ensures the implementation can be reviewed and validated.
