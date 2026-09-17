# Tasks: Unattended Interactive-Safe Test Run

**Input**: `specs/1785-testinteractive/spec.md` and `specs/1785-testinteractive/plan.md`

**Prerequisites**: The worktree uses branch `feat/1785-testinteractive`.

## Phase 1: Setup

- [x] T001 Read issue #1785 and mark it in progress. (delivered: GitHub issue #1785)
- [x] T002 Verify the current registry count and record the 92 `interactive_safe` entries. (delivered: command output)
- [x] T003 Check open pull requests for file overlap before editing `MistHelper.py`. (delivered: command output)

## Phase 2: Foundational

- [x] T004 Add `UnattendedInteractiveInputProvider` in `src/troubleshooting/interactive_test_runner.py`. (delivered: `src/troubleshooting/interactive_test_runner.py`)
- [x] T005 Inject `InputUtils` through `_build_interactive_test_runner` in `MistHelper.py`. (delivered: `MistHelper.py`)
- [x] T006 Add candidate validation to refuse non-`interactive_safe` operations. (delivered: `src/troubleshooting/interactive_test_runner.py`)

## Phase 3: User Story 1 - Run unattended

- [x] T007 Add prompt-provider unit tests for defaults and generated answers. (delivered: `tests/unit/troubleshooting/test_interactive_test_runner.py`)
- [x] T008 Add a unit test that proves `safe_input` is restored after one option. (delivered: `tests/unit/troubleshooting/test_interactive_test_runner.py`)

## Phase 4: User Story 2 - Refuse unsafe operations

- [x] T009 Add a destructive-refusal unit test for menu `154`. (delivered: `tests/unit/troubleshooting/test_interactive_test_runner.py`)
- [x] T010 Add a zero-candidate unit test that returns failure. (delivered: `tests/unit/troubleshooting/test_interactive_test_runner.py`)

## Phase 5: User Story 3 - Report measurement

- [x] T011 Add prompt harness failure reporting in the summary. (delivered: `src/troubleshooting/interactive_test_runner.py`)
- [x] T012 Add a non-empty skip reason fallback. (delivered: `src/troubleshooting/interactive_test_runner.py`)

## Phase 6: Validation and Delivery

- [ ] T013 Run the focused unit test file.
- [ ] T014 Run local gates and available shards.
- [ ] T015 Commit, push, and open the pull request.
