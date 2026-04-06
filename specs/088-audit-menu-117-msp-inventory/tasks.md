# Tasks: Actionable, pre-implementation items

- id: verify-api-function-names
  description: "Identify and record the exact Mist API function name(s) required for MSP inventory (orgs/sites/devices). Save examples in spec_dir."
  complexity: small
  dependencies: []

- id: collect-api-sample-payloads
  description: "Call or retrieve sample responses for each API function and save canonical JSON fixtures to specs/088-audit-menu-117-msp-inventory/fixtures/. If live calls are not allowed, request recorded fixtures from platform team."
  complexity: medium
  dependencies: [verify-api-function-names]

- id: determine-primary-keys
  description: "For each exported entity, determine the primary key fields (e.g., id, device_id, timestamp) and record recommended PK strategy (natural_pk/composite_pk/auto_increment_with_unique)."
  complexity: small
  dependencies: [collect-api-sample-payloads]

- id: draft-sql-table-schemas
  description: "Draft SQL table schemas (SQLite) for all exported tables and include index recommendations and explicit PK declarations. Provide example upsert queries."
  complexity: medium
  dependencies: [determine-primary-keys]

- id: create-upsert-examples
  description: "Create canonical upsert SQL examples (INSERT OR REPLACE / ON CONFLICT DO UPDATE) and document expected behavior for repeated runs."
  complexity: small
  dependencies: [draft-sql-table-schemas]

- id: design-test-cases
  description: "Write unit and integration test cases in markdown: scenarios, inputs (fixtures), expected outputs, and SQL verification steps. Place in spec_dir."
  complexity: small
  dependencies: [collect-api-sample-payloads, draft-sql-table-schemas]

- id: prepare-fixtures-golden-outputs
  description: "Prepare golden outputs: expected CSV rows and expected SQLite DB state for each fixture run (initial insert and subsequent update). Save under spec_dir/fixtures/golden/.")
  complexity: medium
  dependencies: [collect-api-sample-payloads, create-upsert-examples]

- id: test-runbook-and-ci-template
  description: "Author a test runbook and CI job template describing how to run SQL verification tests (ephemeral SQLite DB), including commands to validate upsert behavior."
  complexity: small
  dependencies: [design-test-cases, prepare-fixtures-golden-outputs]

- id: spec-doc-updates
  description: "Update specs/088-audit-menu-117-msp-inventory/spec.md with verified api_function_name(s), PK strategy, and links to fixtures and test plans. Ensure acceptance criteria clearly list SQL upsert expectations."
  complexity: small
  dependencies: [determine-primary-keys, create-upsert-examples, design-test-cases]

- id: stakeholder-review-and-signoff
  description: "Circulate final spec, schemas, test plans, and fixtures to stakeholders for review and sign-off. Collect blockers as issues."
  complexity: small
  dependencies: [spec-doc-updates, test-runbook-and-ci-template]

- id: create-implementation-issue-template
  description: "Create an implementation issue/PR template referencing the spec, listing change tasks (code edits, refactor exporter to call DataExporter.write_with_format_selection, add tests) and CI steps. This task ensures implementers have a clear checklist."
  complexity: small
  dependencies: [stakeholder-review-and-signoff]

Notes:
- All tasks are preparatory; none require modifying exporter implementation code.
- After these tasks complete and stakeholder signoff is obtained, the IMPLEMENT phase can be executed with minimal ambiguity.
