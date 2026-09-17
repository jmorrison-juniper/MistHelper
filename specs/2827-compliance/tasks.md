# Tasks: Compliance cleanup for org probes and AP profile migration

## Phase 1. Baseline

- [x] T001 Read issues #2827, #2828, parent #2645, and pull request #2780.
- [x] T002 Create isolated worktree `MistHelper-2827-compliance` from `origin/main`.
- [x] T003 Bootstrap the worktree and verify `mistapi` version 0.64.0.
- [x] T004 Run the analyzer and record the baseline findings.
- [x] T005 Run focused unit tests and the raw `input()` check before edits.

## Phase 2. Refactor

- [x] T006 Refactor AP profile summary and pacing helpers without changing behavior.
- [x] T007 Refactor AP backup payload and file-name helpers without changing behavior.
- [x] T008 Refactor org synthetic probe setting update code into a semantic class.
- [ ] T009 Re-run analyzer and confirm both files improve.

## Phase 3. Validation and delivery

- [ ] T010 Run the repository validation commands from the issue.
- [ ] T011 Add one changelog fragment for issues #2827 and #2828.
- [ ] T012 Commit, push, and open one pull request.
- [ ] T013 Watch required checks and add `auto-merge` only if all checks pass.
