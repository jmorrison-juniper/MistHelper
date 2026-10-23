# Tasks: Organization metadata refusal

**Input**: [Specification](spec.md), [plan](plan.md), and the supporting artifacts under `design/`.
**Tests**: Required offline unit, SDK boundary, and export integration tests.

## Phase 1: Setup

- [x] T001 Execute the mandatory feature hook and resolve the numeric route (delivered: spec.md).
- [x] T002 Verify exact-path ownership and reproduce the refusal (delivered: design/research.md).

## Phase 2: Foundation

- [x] T003 Record the status, data, and safe logging contract (delivered: design/contracts/metadata.md).

## Phase 3: User Story 1 - Report a refused lookup

**Goal**: Return `Unknown` and report failure without sensitive contents.
**Independent Test**: Mock refused and invalid SDK results and inspect all captured lookup logs.

- [x] T004 [US1] Add failing refusal, malformed metadata, and exception tests (delivered: tests/unit/org/test_org_config_migration_workflow.py).
- [x] T005 [US1] Validate status before data and report safe failures (delivered: src/mist/resources/org/org_config_migration_manager.py).

## Phase 4: User Story 2 - Preserve a successful name

**Goal**: Keep successful names and the bundle shape.
**Independent Test**: Use native SDK success responses and inspect the export bundle in a temporary directory.

- [x] T006 [US2] Verify successful metadata and export persistence (delivered: tests/unit/org/test_org_config_migration_workflow.py).

## Phase 5: Final Checks

- [x] T007 Add the release note and run the relevant gates (delivered: changelog.d/issue-4280-organization-metadata-refusal.md).
- [x] T008 Analyze specification coverage, preserve the change, and report the human-review hold (delivered: analysis.md).

## Dependencies & Execution Order

T001 and T002 precede T003.
T003 precedes T004, which precedes T005.
T006 uses the completed validation from T005.
T007 follows T005 and T006.
T008 follows T007.

## Parallel Opportunities

Run independent quality gates concurrently after the test and source edits finish.
Do not edit user stories concurrently because both use the same test module.
For US1, compare refusal log checks with status-validation results.
For US2, compare the returned name with the saved metadata in the same offline test.

## Implementation Strategy

First make refusal tests fail against the old lookup.
Then repair the lookup and preserve successful export behavior.
Complete all gates before the final commit and report.
Human review remains a release condition, not permission for an automated merge.
