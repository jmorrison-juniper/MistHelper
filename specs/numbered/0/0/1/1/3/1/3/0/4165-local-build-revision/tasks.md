# Tasks: Local build revision

**Input**: [Specification](spec.md), [plan](plan.md), and supporting records under `design/`.

## Phase 1: Setup

- [x] T001 Resolve the managed issue route for `spec.md`. (delivered: spec.md)
- [x] T002 Prepare the worktree environment and design in `plan.md`. (delivered: plan.md)

## Phase 2: Foundation

- [x] T003 Add the PowerShell execution fixture to `tests/contract/packaging/test_compose_local_revision.py`. (delivered: tests/contract/packaging/test_compose_local_revision.py)

## Phase 3: User Story 1 - Identify a local build

**Goal**: Record the full commit and dirty state for each helper build.
**Independent Test**: Observe the build environment through a simulated provider.

- [x] T004 [US1] Test clean, staged, unstaged, untracked, ignored, and failed revision reads in `tests/contract/packaging/test_compose_local_revision.py`. (delivered: tests/contract/packaging/test_compose_local_revision.py)
- [x] T005 [US1] Set and restore build metadata in `scripts/compose.ps1`. (delivered: scripts/compose.ps1)
- [x] T006 [US1] Write the OCI revision label through `compose.build.yml`. (delivered: compose.build.yml)

## Phase 4: User Story 2 - Compare a local image

**Goal**: Preserve clean comparisons and refuse unsupported dirty-image freshness.
**Independent Test**: Execute the revision command with controlled labels and repository history.

- [x] T007 [US2] Test dirty, missing, invalid, current, stale, and non-image-only labels in `tests/contract/packaging/test_compose_local_revision.py`. (delivered: tests/contract/packaging/test_compose_local_revision.py)
- [x] T008 [US2] Explain dirty and missing labels before clean comparison in `scripts/compose.ps1`. (delivered: scripts/compose.ps1)

## Phase 5: Documentation and verification

- [x] T009 Update the operator label contract in `documentation/container-deployment.md` and `deploy/.env.example`. (delivered: documentation/container-deployment.md, deploy/.env.example)
- [x] T010 [P] Add `changelog.d/issue-4165-local-build-revision.md`. (delivered: changelog.d/issue-4165-local-build-revision.md)
- [x] T011 Run the commands in `design/quickstart.md` and the applicable guardrails. (delivered: design/quickstart.md)
- [x] T012 Record the specification consistency review as issue artifact 1. (delivered: issue artifact 1)

## Dependencies and execution order

T001 and T002 precede T003.
T003 precedes T004 and T007.
T004 precedes T005 and T006.
T007 precedes T008.
T009 and T010 follow both stories.
T011 follows implementation and documentation. T012 follows T011.

## Parallel examples

For User Story 1, the build overlay edit can run separately from the helper edit after the tests exist.
For User Story 2, the documentation edit can run separately after its behavior is implemented.
The same test module and helper must not have concurrent writers.

## Implementation strategy

First prove the new tests fail against the previous helper.
Then implement the metadata path and dirty-label refusal.
Finally run both stories together, review the specification, and create one pull request.
