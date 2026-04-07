# Plan for Export Site Maps

## High-level approach
1. Call site-level maps listing API (handle pagination & rate limits).
2. Normalize/flatten each map JSON into the agreed schema.
3. Deduplicate on map `id` and apply validation/assertions for required fields.
4. Export to CSV and upsert into SQLite using natural PK strategy.
5. Add unit and integration tests (mocked API and end-to-end with sample fixtures).
6. Update README and ENDPOINT_PRIMARY_KEY_STRATEGIES with mapping metadata.

## Deliverables
- Implementation: SiteConfigExporter.maps function or module that performs the export.
- Unit tests and integration tests for happy path + edge cases.
- README snippet documenting the new menu entry and usage examples.
- Spec and primary-key mapping entry in ENDPOINT_PRIMARY_KEY_STRATEGIES.

## Milestones
1. Design & spec finalization (this artifact) — 0.5 day
2. Implementation & local unit tests — 1.0 day
3. Integration tests with mocked API fixtures — 0.5 day
4. Documentation and README update — 0.25 day
5. Code review and merge — 0.25 day

## People / roles
- Implementer: developer (adds code and tests)
- Reviewer: maintainer/peer (code review)
- Tester: QA or integrator (validate SQLite upserts and CSV outputs)
- SME: NOC engineer (validates field selection and naming)

## Verification plan
- Automated unit tests: verify flattening logic, required-field assertions, and CSV formatting.
- Integration test: run export against mocked API responses (including pagination and partial fields) and assert SQLite contains expected rows and that re-run is idempotent.
- Manual smoke: run menu operation for a small site and visually confirm CSV, SQLite, and sample image URLs.
- Add CI job to run tests on PRs that touch exporter code.