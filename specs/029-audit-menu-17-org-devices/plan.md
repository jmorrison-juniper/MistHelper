# Plan

## Goal
Move menu item 17 from SQL-partial / untested into a production-quality exporter with clear PK strategy, tests, and documentation.

## High-level phases
1. Spec finalization (this artifact)
2. Design & configuration
   - Decide canonical API name and PK mapping
   - Draft ENDPOINT_PRIMARY_KEY_STRATEGIES entry
3. Test scaffolding (pre-implementation)
   - Create unit test files and integration test plan/mocks
4. Implementation (IMPLEMENT step — stop before making code changes per instruction)
   - Update OrgInventoryExporter.devices to use canonical api_function_name and call write_with_format_selection
   - Add PK strategy to configuration
5. Testing & verification
   - Run unit + integration tests; iterate until green
6. Documentation & release
   - Add spec files to specs/029-audit-menu-17-org-devices
   - Update README/CHANGELOG

## Milestones
- M1: PK strategy approved and documented (ENDPOINT_PRIMARY_KEY_STRATEGIES draft) — dependency: spec
- M2: Test skeletons created (unit + integration + SQL verification) — dependency: M1
- M3: Implementation branch created with code changes (IMPLEMENT phase; not executed here) — dependency: M2
- M4: Tests passing and SQL behavior verified — dependency: M3
- M5: Docs updated and PR ready for review — dependency: M4

## Dependencies and risk mitigation
- Dependency: canonical API name decision (getOrgDevices vs listOrgDevices) — risk: mismatch causes wrong PK mapping. Mitigation: add alias mapping and regression test asserting canonical name.
- Dependency: stable device UUID presence — risk: some devices may lack id in rare API responses. Mitigation: unit tests to assert fallback behavior and a QA check to detect records without id.

## Deliverables before IMPLEMENT
- This spec.md saved to specs/029-audit-menu-17-org-devices/spec.md
- plan.md saved to specs/029-audit-menu-17-org-devices/plan.md
- tasks.md saved to specs/029-audit-menu-17-org-devices/tasks.md
- PR-ready checklist and test skeletons (no production code changes yet)

