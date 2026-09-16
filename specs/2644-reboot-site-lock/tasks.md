# Tasks: Reboot Site Lock Safety

**Input**: `specs\2644-reboot-site-lock\spec.md` and `specs\2644-reboot-site-lock\plan.md`

**Prerequisites**: Issue #2644, issue #2575, pull request #2720 coordinator comment, and project instructions

## Phase 1: Setup

- [x] T001 Read issue #2644 and sibling issue #2575. (delivered: GitHub issue evidence)
- [x] T002 Read pull request #2720 coordinator comment. (delivered: GitHub pull request evidence)
- [x] T003 Create isolated worktree `..\MistHelper-2644-reboot-lock`. (delivered: worktree)
- [x] T004 Bootstrap the worktree and verify mistapi 0.64.0. (delivered: `.venv`)

## Phase 2: Foundational Measurement

- [x] T005 Verify the poll interval in `src\upgrade_portal\upgrade\gate.py`. (delivered: `spec.md`)
- [x] T006 Verify calls for each round in `src\upgrade_portal\upgrade\phase_gate.py`. (delivered: `spec.md`)
- [x] T007 Verify the schedule horizon in `src\upgrade_portal\upgrade\options.py`. (delivered: `spec.md`)
- [x] T008 Verify the maximum lock life in `src\upgrade_portal\runtime\lock.py`. (delivered: `spec.md`)

## Phase 3: User Story 1 - Refuse unsafe long schedules

- [x] T009 [US1] Add tests for the safe schedule limit in `tests\unit\upgrade_portal\test_upgrade_ssr_options.py`. (delivered: `tests\unit\upgrade_portal\test_upgrade_ssr_options.py`)
- [x] T010 [US1] Cap the schedule horizon in `src\upgrade_portal\upgrade\options.py`. (delivered: `src\upgrade_portal\upgrade\options.py`)

## Phase 4: User Story 2 - Stop polling before the scheduled reboot

- [x] T011 [US2] Add a phase gate test that proves no cloud poll before a future reboot in `tests\unit\upgrade_portal\test_phase_gate.py`. (delivered: `tests\unit\upgrade_portal\test_phase_gate.py`)
- [x] T012 [US2] Add scheduled pre-wait logic to `src\upgrade_portal\upgrade\phase_gate.py`. (delivered: `src\upgrade_portal\upgrade\phase_gate.py`)

## Phase 5: User Story 3 - Fail closed on lock loss

- [x] T013 [US3] Add driver tests that prove a lost lock stops later site actions in `tests\unit\upgrade_portal\test_upgrade_driver.py`. (delivered: `tests\unit\upgrade_portal\test_upgrade_driver.py`)
- [x] T014 [US3] Make `src\upgrade_portal\upgrade\driver.py` fail when the heartbeat reports a lost lock. (delivered: `src\upgrade_portal\upgrade\driver.py`)
- [x] T015 [US3] Make `src\upgrade_portal\upgrade\phase_gate.py` fail before cloud polling when the progress heartbeat reports a lost lock. (delivered: `src\upgrade_portal\upgrade\phase_gate.py`)

## Phase 6: Release Note and Validation

- [x] T016 Add `changelog.d\issue-2644-reboot-site-lock.md`. (delivered: `changelog.d\issue-2644-reboot-site-lock.md`)
- [x] T017 Run ruff, black, mypy, radon, and upgrade portal pytest gates. (delivered: local gate output)
- [ ] T018 Commit, push, and open a pull request.
