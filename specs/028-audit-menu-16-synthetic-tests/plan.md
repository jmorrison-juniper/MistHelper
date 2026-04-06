# Plan — From current state to Done (menu 16)

## Objective
Make the Gateway synthetic test export SQL-compliant, robust, and tested, then document and deliver the feature.

## High-level phases
1. Finalize specification (this document) — done.
2. Design & configuration
   - Decide exact composite PK column names and types.
   - Define `api_function_name` canonical value and mapping.
   - Prepare SQL schema expectations and migration notes.
3. Preparation (non-invasive repository changes)
   - Add spec/metadata files into `specs/028-audit-menu-16-synthetic-tests`.
   - Create test scaffolding and example payloads for unit/integration tests.
4. Implementation (CODE CHANGES — reserved for IMPLEMENT step)
   - Add PK strategy to `ENDPOINT_PRIMARY_KEY_STRATEGIES`.
   - Refactor GatewayTestExporter.synthetic_tests to call DataExporter.write_with_format_selection(..., api_function_name=...)
   - Ensure exporter returns deterministic flattened records and includes PK fields.
5. Testing & validation
   - Run unit tests, integration tests, and SQL verification tests; iterate until green.
   - Validate upsert behavior and indexing.
6. Documentation & release
   - Update README/menu documentation and migration notes in `specs/028-audit-menu-16-synthetic-tests`.
   - Commit, run py_compile, and push through CI pipeline.

## Milestones
- M1: Spec and test plan added to `specs/028-audit-menu-16-synthetic-tests` (blocking: none).
- M2: PK strategy and api_function_name agreed and added to repository configuration (blocking: design decisions).
- M3: Unit tests implemented and passing (blocking: code refactor completed).
- M4: Integration tests (SQLite upsert verification) passing (blocking: M3).
- M5: Documentation and release notes published; CI green (blocking: M4).

## Dependencies and ordering
- Design decisions (phase 2) must complete before adding PK strategy or changing exporter function signatures.
- Tests and CI scaffolding (phase 3) should be created before implementation to enable TDD-style commits.
- Implementation (phase 4) depends on completed design and test harness.

## Risk & mitigations
- Risk: API payloads lack a stable per-run identifier. Mitigation: create deterministic `test_run_id` derived from (gateway_id + sequence + start_timestamp) and document it in spec.
- Risk: Upsert conflicts with existing tables. Mitigation: ensure unique composite PK and test migrations on a temp DB first.

## Deliverables
- Spec files in `specs/028-audit-menu-16-synthetic-tests`.
- PK config entry in endpoint strategies (planned change).
- Unit and integration test suite covering exporter and SQL upsert behavior.
- README/menu documentation and migration notes.
