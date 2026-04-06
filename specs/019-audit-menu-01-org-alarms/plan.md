# Plan

## Goal
Bring Menu ID 1 from current state (SQL compliant, missing unit tests) to Done: documented spec, implemented exporter integrated with DataExporter, covered by unit and integration tests, and validated SQL upsert behavior.

## High-level phases
1. Finalize spec (this artifact) — DONE
2. Prepare design & configuration
   - Add primary-key strategy entry in ENDPOINT_PRIMARY_KEY_STRATEGIES
   - Define table schema and indexes for alarms
   - Add test fixtures and VCR recordings (or mocks)
3. Test scaffolding (non-implementation)
   - Add unit test skeletons and integration test plans; create test data fixtures
   - Configure CI job to run these tests (or tag them for later CI run)
4. Implementation (IMPLEMENT phase — stop before doing this)
   - Refactor OrgAlarmEventExporter.alarms to call DataExporter.write_with_format_selection
   - Implement upsert/INSERT OR REPLACE logic for composite_pk
   - Handle pagination, rate limits, and error retries
5. Test & verify
   - Run unit tests locally and in CI
   - Run integration tests against staging or recorded fixtures
   - SQL verification: double-run exporter to validate idempotency
6. Documentation & release
   - Update README and menu docs
   - Bump version and create changelog entry

## Milestones & acceptance gates
- Milestone A: PK strategy and schema defined and reviewed (blocks implementation)
- Milestone B: Test fixtures and unit test skeletons added & CI paths configured
- Milestone C: Implementation merged (code changes) — not performed here
- Milestone D: All tests pass, SQL idempotency verified, docs updated

## Dependencies
- PK strategy must be added before implementing exporter upsert logic.
- Test fixtures and mocks must exist before writing reliable unit/integration tests.
- DataExporter API must be available and stable (existing in repo).

## Risks & mitigations
- Ambiguity about alarm `id` uniqueness across orgs: mitigation — choose composite_pk including org_id and timestamp.
- Real API rate limits may affect integration tests: mitigation — use recorded fixtures or parameterize rate limits in tests.

## Exit criteria for this planning stage
- PK strategy and schema defined and documented
- Test fixtures and test templates exist in the spec_dir
- Stakeholder sign-off on spec and tests


