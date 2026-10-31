# Tasks: AP discovery failure

**Input**: [Specification](spec.md), [plan](plan.md), and supporting records under `design/`.

## Phase 1: Setup

- [x] T001 Reserve the exact source and test paths on #2753 before edits. (delivered: design/research.md)

## Phase 2: Foundation

- [x] T002 Verify the SDK read contract and managed record route. (delivered: design/data-model.md)

## Phase 3: User Story 1 - Refuse incomplete site discovery

**Goal**: Stop failed site reads before migration can use incomplete input.
**Independent test**: Run direct discovery and migration refusal cases with mocked SDK responses.

- [x] T003 [US1] Prove failed reads with absent, empty, and populated data. (delivered: tests/unit/device/test_ap_profile_migration_manager.py)
- [x] T004 [US1] Remove the organization site-read fallback. (delivered: src/mist/resources/device/ap_profile_migration_manager.py)
- [x] T005 [US1] Verify exact valid records and zero migration side effects. (delivered: tests/unit/device/test_ap_profile_migration_manager.py)

## Phase 4: Publication

- [x] T006 Add the release note and run applicable local checks. (delivered: changelog.d/issue-2753-ap-discovery-failure.md)
- [x] T007 Record requirement coverage and validation. (delivered: analysis.md)

## Dependencies & Execution Order

T001 precedes T002. T003 requires T002.
T004 requires the failing T003 proof. T005 requires T004.
T006 requires T005. T007 requires T006.
One story is the complete bounded delivery.

## Parallel Example: User Story 1

No source or test edits run in parallel.
Independent lint, type, and documentation checks can run together after T005.

## Implementation Strategy

Prove the old failure before the source repair.
Preserve accepted-input results. Publish one reviewed slice without merging.
