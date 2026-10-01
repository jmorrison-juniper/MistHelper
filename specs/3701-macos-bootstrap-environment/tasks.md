# Tasks: macOS bootstrap environment

**Input**: [spec.md](spec.md) and [plan.md](plan.md).

**Prerequisites**: Read issue #3701, all claims, open pull request file lists, and parent reservations.

**Tests**: Native red and green checks plus offline platform and adjacent bootstrap contracts are required.

## Phase 1: Setup

- [x] T001 Confirm the claim and permitted manifest. (delivered: specs/3701-macos-bootstrap-environment/.spec-context.json)
- [x] T002 Complete the specification checklist. (delivered: specs/3701-macos-bootstrap-environment/checklists/requirements.md)

## Phase 2: Foundational

- [x] T003 Preserve the native failure before source edits. (delivered: private files/issue3701/native-red.log)
- [x] T004 Recover only the ignored worktree environment. (delivered: private files/issue3701/bootstrap-recovery.log)

## Phase 3: User Story 1 - Create a working environment

**Goal**: Preserve native interpreter library resolution without changing the installer.

**Independent Test**: Create a real environment and run its interpreter with required imports and prefix checks.

- [x] T005 [US1] Add creation tests. (delivered: tests/unit/scripts/environment_creation/test_worktree_environment_creation.py)
- [x] T006 [US1] Set the platform policy. (delivered: scripts/bootstrap_worktree.py)
- [x] T007 [US1] Prove native creation and negative guards. (delivered: private files/issue3701/focused-tests.log)

## Phase 4: User Story 2 - Keep optional installer support

**Goal**: Keep uv optional and retain existing installation behavior.

**Independent Test**: Run native creation without uv discovery and the existing offline installation selectors.

- [x] T008 [US2] Update the coupled flag assertion and run contracts. (delivered: tests/unit/bootstrap/test_pip_index_probe.py)
- [x] T009 [US2] Run adjacent offline contracts. (delivered: private files/issue3701/focused-tests.log)

## Phase 5: User Story 3 - Recover a partial environment

**Goal**: Retain explicit recreation and document recovery.

**Independent Test**: Recreate an owned partial environment and preserve a neighboring directory.

- [x] T010 [US3] Cover reuse, recreation, and errors. (delivered: tests/unit/scripts/environment_creation/test_worktree_environment_creation.py)
- [x] T011 [US3] Update recovery guidance. (delivered: documentation/development-setup.md)
- [x] T012 [US3] Add the release fragment. (delivered: changelog.d/issue-3701-macos-bootstrap-environment.md)

## Phase 6: Validation and Local Handoff

- [x] T013 Measure coverage and run local gates. (delivered: private files/issue3701/validation.json)
- [x] T014 Preserve the original 23-item template in the unposted body. (delivered: private files/issue3701/pr-body.md)
- [x] T015 Remove exact owned environments and verify source boundaries. (delivered: private files/issue3701/validation.json)
- [x] T016 Prepare the ten-file manifest and local handoff. (delivered: private files/issue3701/validation.json)

## Dependencies & Execution Order

T001 and T002 precede T003.
T003 precedes T004, T005, and T006.
T005 precedes T006.
T006 precedes T007, T008, T009, and T010.
Parent documentation ownership confirmation precedes T011.
T007 through T012 precede T013 through T016.

## Parallel Opportunities

Independent read-only contract checks can run together.
Do not run two writers against the same environment or evidence file.
Do not edit the documentation before the parent releases its reservation.

## Implementation Strategy

Prove the original failure first.
Make the single policy repair.
Validate all three user stories.
Finish the local commit without publication.

The commit and required post-commit check occur after these tracked records become immutable.
Private session evidence records the final commit SHA and clean tree.
Publication, protected merge, and actual-main proof require the later parent grant.
