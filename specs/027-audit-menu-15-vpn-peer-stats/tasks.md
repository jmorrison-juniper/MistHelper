# Tasks

- id: create-spec-directory
  description: Create specs/027-audit-menu-15-vpn-peer-stats and add this spec.md plus a README describing the purpose and handoff artifacts.
  complexity: small
  dependencies: []

- id: capture-api-fixtures
  description: Record/save representative API responses for OrgDeviceStatsExporter.vpn_peer_stats (happy path, empty, partial/missing fields). Store JSON fixtures under the spec directory.
  complexity: medium
  dependencies: [create-spec-directory]

- id: define-pk-proposal-doc
  description: Create a short PK proposal document in the spec dir specifying exact composite key fields (device_id, peer_id, path_id?, timestamp), rationale, and sample SQL DDL for primary key and indexes. Do not modify code yet.
  complexity: small
  dependencies: [capture-api-fixtures]

- id: write-sql-verification-scripts
  description: Add SQL scripts (SQLite-compatible) that create temporary tables, apply the proposed PK/indexes, and run sample inserts/upsserts to demonstrate idempotency and upsert semantics.
  complexity: medium
  dependencies: [define-pk-proposal-doc]

- id: create-unit-test-templates
  description: Add unit test skeletons (pytest) in tests/ referencing the fixtures: tests should mock vpn_peer_stats, call exporter, and assert flattening + DataExporter call parameters. Include TODOs but do not implement mocks yet.
  complexity: small
  dependencies: [capture-api-fixtures]

- id: create-integration-test-plan
  description: Document an integration test plan that runs the exporter against a temporary SQLite DB using fixtures, verifies upsert semantics, and lists CI requirements (sqlite available, temp DB path). Include exact commands to run.
  complexity: small
  dependencies: [write-sql-verification-scripts, create-unit-test-templates]

- id: update-readme-menu-entry
  description: Add/update a line in README.md (or menu documentation) that notes menu_id 15 exists and references the spec_dir. Keep it informational; do not change behavior.
  complexity: small
  dependencies: [create-spec-directory]

- id: prepare-pr-checklist
  description: Create a PR checklist file in the spec dir listing required validation steps for implementation PR (py_compile, unit tests, integration tests, SQL verification, performance checks, reviewer list).
  complexity: small
  dependencies: [create-unit-test-templates, write-sql-verification-scripts]

- id: stakeholder-review
  description: Notify stakeholders (NOC, platform engineers, QA) with a short review request and include links to spec_dir artifacts; collect sign-off or feedback items.
  complexity: small
  dependencies: [create-spec-directory, define-pk-proposal-doc, prepare-pr-checklist]

Priority ordering (do these first): create-spec-directory -> capture-api-fixtures -> define-pk-proposal-doc -> write-sql-verification-scripts -> create-unit-test-templates -> create-integration-test-plan -> prepare-pr-checklist -> update-readme-menu-entry -> stakeholder-review

Notes:
- These tasks intentionally avoid changing runtime code. They prepare all artifacts and validations so the implement phase can be executed in a single focused PR with clear test coverage and SQL expectations.
