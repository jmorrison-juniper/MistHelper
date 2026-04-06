# Plan

## Objective
Deliver a fully specified, tested, and review-ready plan so implementation can proceed with minimal ambiguity. This plan stops prior to implementation.

## High-level phases
1. Specification finalization (this artifact)
   - Confirm schema, PK strategy, and acceptance criteria with stakeholders.
   - Milestone: spec.md accepted.
2. Design and test scaffolding
   - Design SQL schema, indexes, and migration/snippets to include in repo (in specs dir).
   - Prepare unit and integration test specifications and fixtures (no code changes yet).
   - Produce change proposal for ENDPOINT_PRIMARY_KEY_STRATEGIES entry for this endpoint.
3. Review & sign-off before implement
   - Peer review of spec, schema, and test plans.
   - Stakeholder sign-off.
   - Milestone: sign-off recorded (issue/pr template filled).
4. Implementation (IMPLEMENT phase; not performed now)
   - Implement exporter changes, add PK strategy to ENDPOINT_PRIMARY_KEY_STRATEGIES, wire DataExporter.write_with_format_selection, add tests.
5. Testing & verification
   - Run unit tests, then integration tests against a test SQLite DB and verify upsert semantics.
6. Release & documentation
   - Update README/menu index, add changelog entry, and update spec directory with final artifacts.

## Dependencies
- Decision: final primary-key fields (id vs id+org_id) — affects schema and tests.
- Fixtures: representative device JSON responses required before tests can be written.
- Test harness: lightweight SQLite test DB available in tests suite.
- Coordination: small review window with QA to validate SQL verification steps.

## Risks & mitigations
- Risk: API payload variations (missing fields) — mitigation: include edge-case fixtures with missing/extra fields and assert exporter tolerates them.
- Risk: Choosing wrong PK causing duplicate rows — mitigation: review PK choice with release owner and include composite fallback in schema notes.

## Deliverables before implement
- Finalized spec.md (this file), SQL schema snippet, test plan and test fixtures under specs/024-audit-menu-12-org-inventory, and a prioritized actionable task list (tasks.md).

---
