# Tasks: Dependency lock group

**Input**: [Specification](spec.md), [plan](plan.md), and supporting documents under `design/`.

## Phase 1: Setup

- [x] T001 Inspect the five original diffs and record issue mapping in spec.md. (delivered: spec.md)
- [x] T002 Reproduce the stale-lock failure and record prerequisites in design/research.md. (delivered: design/research.md)

## Phase 2: Foundational

- [x] T003 Save five exact original revisions in refs/recovery/issue4811/ and record them in design/research.md. (delivered: design/research.md)

## Phase 3: User Story 2 - Preserve original work

**Goal**: Preserve exact original work without remote changes.

**Independent Test**: Resolve the five references and compare them with design/research.md.

- [x] T004 [US2] Verify all five recovery references and unchanged remote heads in design/research.md. (delivered: design/research.md)

## Phase 4: User Story 1 - Consistent installation

**Goal**: Resolve all five requested versions without unrelated changes.

**Independent Test**: Run all three existing dependency guard modules under tests/guardrails/.

- [x] T005 [US1] Apply the direct version declarations in pyproject.toml and regenerate uv.lock with exact requested update selectors. (delivered: uv.lock)
- [x] T006 [US1] Generate requirements.txt and requirements-dev.txt from uv.lock. (delivered: requirements-dev.txt)
- [x] T007 [US1] Run consistency, lint, type, SSH, and portal compatibility checks and record results in analysis.md. (delivered: analysis.md)

## Phase 5: User Story 3 - Isolated application check

**Goal**: Prove local application compatibility without using unauthorized credentials.

**Independent Test**: Record exact container results and resource absence in analysis.md.

- [x] T008 [US3] Attempt an isolated project container smoke and verify exact-name cleanup in analysis.md. (delivered: analysis.md)
- [x] T009 [US3] Record staging credential authorization and verified organization, or the explicit blocker, in analysis.md. (delivered: analysis.md)

## Phase 6: Cross-Cutting Concerns

- [x] T010 Add the grouped release note in changelog.d/pr-4806.md. (delivered: changelog.d/pr-4806.md)
- [x] T011 Complete Spec Kit consistency analysis and record findings, exact commands, and unresolved blockers in analysis.md. (delivered: analysis.md)
- [ ] T012 Commit only the explicit feature files and report the exact local head to the coordinator. Keep the validation record in analysis.md.

## Dependencies & Execution Order

T001 and T002 precede T003. T003 precedes T004 and T005.
T005 precedes T006. T006 precedes T007 and T008.
T009 depends only on the prerequisite inspection.
T010 follows T006. T011 follows T004, T007, T008, T009, and T010.
T012 follows T011.

## Parallel Examples

For User Story 1, independent SSH and portal checks can run concurrently after dependency generation.
For User Story 2, recovery verification can run independently from application tests.
For User Story 3, credential-presence inspection does not depend on container startup.
No two processes can regenerate the shared dependency records concurrently.

## Implementation Strategy

Preserve original work first.
Resolve and validate one dependency set before the application smoke.
If an independent compatibility blocker appears, stop grouping that update and record the reason.
Report blocked checks honestly. Leave publication, issue closure, merges, and deployment to the coordinator.
