# Tasks: Retry site scope

**Input**: [Specification](spec.md), [plan](plan.md), and the documents under `design/`.

## Phase 1: Setup

- [x] T001 Verify ownership and current main before changing `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py`. (delivered: specs/numbered/0/0/1/0/2/0/4/1/3396-retry-site-scope/design/research.md)
- [x] T002 Resolve and validate the managed numeric route for `spec.md`. (delivered: specs/numbered/0/0/1/0/2/0/4/1/3396-retry-site-scope/spec.md)

## Phase 2: Foundational

- [x] T003 Block external connections in `tests/contract/upgrade_portal/test_org_child_controls_routes.py`. (delivered: tests/contract/upgrade_portal/test_org_child_controls_routes.py)

## Phase 3: User Story 1 - Exact retry scope (Priority: P1)

**Goal**: Save, confirm, check, and lock only sites with planned retry devices.
**Independent test**: Clear switches in the two-site retry and require B only at every boundary.

- [x] T004 [US1] Prove parent names, child IDs, confirmation rows, submission reads, locks, and selection in `tests/contract/upgrade_portal/test_org_child_controls_routes.py`. (delivered: tests/contract/upgrade_portal/test_org_child_controls_routes.py)
- [x] T005 [US1] Filter retry rows and read the durable effective scope in `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py`. (delivered: src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py)
- [x] T006 [US1] Cover a departed retry device and mismatched effective context in `tests/contract/upgrade_portal/test_org_child_controls_routes.py`. (delivered: tests/contract/upgrade_portal/test_org_child_controls_routes.py)

## Phase 4: User Story 2 - Preserve complete scopes (Priority: P2)

**Goal**: Preserve plain saves and retries with a target at every site.
**Independent test**: Exercise the same route boundaries with both planned sites.

- [x] T007 [US2] Cover plain saves and complete retries in `tests/contract/upgrade_portal/test_org_child_controls_routes.py`. (delivered: tests/contract/upgrade_portal/test_org_child_controls_routes.py)

## Phase 5: Polish and delivery

- [x] T008 [P] Write `changelog.d/issue-3396-retry-site-scope.md`. (delivered: changelog.d/issue-3396-retry-site-scope.md)
- [x] T009 Run applicable local gates and record conformance in `analysis.md`. (delivered: specs/numbered/0/0/1/0/2/0/4/1/3396-retry-site-scope/analysis.md)
- [x] T010 Commit the explicit manifest and run the committed-difference quality gate for `tests/contract/upgrade_portal/test_org_child_controls_routes.py`. (delivered: tests/contract/upgrade_portal/test_org_child_controls_routes.py)

## Dependencies and execution order

T001 and T002 precede T003. T003 precedes T004 and T007.
T004 precedes T005. T005 precedes T006.
T004, T005, T006, T007, and T008 precede T009. T009 precedes T010.

## Parallel examples

The release note can proceed while contract tests run.
Story 1 and story 2 share one test file, so edits remain serial.
Focused contract and unit tests can run in one command.

## Implementation strategy

First prove the partial retry defect. Then repair the durable scope and its consumers.
Verify both stories before the tested commit.
Open a draft pull request after the committed-difference gate passes.
Human review and merge remain outside this task.

## Extension hooks

Optional pre-hook and post-hook: `/speckit-git-commit`.
Prompt: commit the current task changes.
Defer these optional commits to the requested tested implementation commit.
No mandatory task hook is enabled.
Implementation hooks use the same optional command and remain deferred.
