# Tasks: Remove the MistHelper sys.modules Alias

**Input**: Design documents from `specs/2670-sysmodules-alias/`

**Prerequisites**: `spec.md` and `plan.md`

**Tests**: Include the requested local gates from issue #2670.

## Phase 1: Setup

**Purpose**: Confirm the blocker and isolate the work.

- [x] T001 Read issue #2670 and blocker issue #1703. (delivered: GitHub issue evidence)
- [x] T002 Create worktree `MistHelper-2670-alias` from current `origin/main`. (delivered: local worktree)
- [x] T003 Confirm `mistapi` version 0.64.0 and pytest collection. (delivered: setup command output)
- [x] T004 Confirm no open pull request touches `MistHelper.py`. (delivered: open pull request list)

## Phase 2: Specification

**Purpose**: Record the expected behavior before the edit.

- [x] T005 Create `specs/2670-sysmodules-alias/spec.md`. (delivered: specs/2670-sysmodules-alias/spec.md)
- [x] T006 Create `specs/2670-sysmodules-alias/plan.md`. (delivered: specs/2670-sysmodules-alias/plan.md)
- [x] T007 Create `specs/2670-sysmodules-alias/tasks.md`. (delivered: specs/2670-sysmodules-alias/tasks.md)

## Phase 3: Implementation

**Purpose**: Remove the alias without adding a replacement shim.

- [x] T008 Remove the `sys.modules["MistHelper"]` assignment from `MistHelper.py`. (delivered: MistHelper.py)
- [x] T009 Confirm the `sys` import remains necessary in `MistHelper.py`. (delivered: MistHelper.py)
- [x] T010 Remove remaining source root lookups from firmware and serial capture modules. (delivered: src/firmware/firmware_manager.py and src/refactors/serial_cc/)
- [x] T011 Update the guard so it rejects constant-based root imports and `sys.modules` reads. (delivered: tests/guardrails/test_source_misthelper_backrefs.py)
- [x] T012 Update firmware tests for the resolver seam. (delivered: tests/unit/firmware/)
- [x] T013 Create `changelog.d/issue-2670-sysmodules-alias.md`. (delivered: changelog.d/issue-2670-sysmodules-alias.md)

## Phase 4: Validation

**Purpose**: Prove each acceptance criterion.

- [x] T014 Confirm no executable `import MistHelper` remains under `src`. (delivered: grep proof)
- [x] T015 Confirm no executable `import_module(.MistHelper.)` remains under `src`. (delivered: grep proof)
- [x] T016 Confirm `MistHelper.py` no longer assigns `sys.modules["MistHelper"]`. (delivered: grep proof)
- [ ] T017 Confirm `python -c "import MistHelper"` succeeds.
- [ ] T018 Confirm `python -c "import wsgi"` succeeds.
- [ ] T019 Confirm the import graph guard rejects a new source back-reference.
- [ ] T020 Run Ruff, Black, mypy, Pylint, Radon, guardrails, symbol diff, and full pytest.

## Phase 5: Pull Request and Merge

**Purpose**: Deliver through the repository workflow.

- [ ] T021 Commit all feature files.
- [ ] T022 Push `refactor/2670-sysmodules-alias`.
- [ ] T023 Open a pull request that closes issue #2670.
- [ ] T024 Wait for required checks, including CodeQL.
- [ ] T025 Add `auto-merge` after required checks pass.
- [ ] T026 Verify the merge, issue closure, and issue #2645 comment.

## Dependencies and Execution Order

- Phase 1 must finish before Phase 3.
- Phase 2 must finish before the pull request opens.
- Phase 3 must finish before Phase 4.
- Phase 4 must pass before Phase 5.

## Parallel Opportunities

- Static searches can run in parallel after the implementation.
- Import checks can run in parallel with static searches.
- The full pytest suite can run after targeted guardrails pass.
