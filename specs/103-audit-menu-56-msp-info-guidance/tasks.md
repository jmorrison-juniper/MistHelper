# Tasks for implementing Menu 56 (MSP Info Guidance)

- task: add-menu-entry
  title: Add CLI/menu entry for "MSP Info Guidance"
  description: Wire menu id 56 to call OrgConfigExporter.msp with selected org_id and options; include help text and output flags (--csv).
  depends_on: []

- task: implement-fetch-and-normalize
  title: Call OrgConfigExporter.msp and normalize results
  description: Call OrgConfigExporter.msp(org_id, options), validate returned items against expected schema, compute issue_summary_hash if needed, and remove any sensitive fields.
  depends_on: [add-menu-entry]

- task: implement-output-renderers
  title: Implement text and CSV renderers
  description: Render normalized guidance as readable text (default) and CSV when --csv provided; ensure consistent column order and escaping.
  depends_on: [implement-fetch-and-normalize]

- task: add-tests-fixtures
  title: Add fixture data and unit/integration tests
  description: Create sample OrgConfigExporter.msp fixtures (with guidance and empty) and unit tests to assert normalization, filtering, and rendering behavior.
  depends_on: [implement-fetch-and-normalize, implement-output-renderers]

- task: docs-and-specs
  title: Add spec and README updates
  description: Place spec files under specs/103-audit-menu-56-msp-info-guidance and update README menu index and changelog entry.
  depends_on: [add-menu-entry, implement-output-renderers]

- task: verification-and-qa
  title: Run verification tests and manual smoke tests
  description: Run unit tests, run integration fixture, perform manual CLI run and validate acceptance criteria; fix issues if any.
  depends_on: [add-tests-fixtures, docs-and-specs]

Notes:
- Keep tasks small and dependency-ordered. Stop before IMPLEMENT.
