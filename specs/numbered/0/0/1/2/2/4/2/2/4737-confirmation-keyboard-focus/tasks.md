# Tasks: Confirmation dialog keyboard focus

## Phase 1: Setup

- [x] T001 Read issue #4737 and the uncommitted candidate in the source worktree.
- [x] T002 Save the candidate patch and copy the untracked changelog fragment.
- [x] T003 Create the fleet worktree from `origin/main` and apply the candidate with `git apply --index`.

## Phase 2: Keyword focus

**Independent test**: The keyword field has focus after two animation frames on the first dialog of a module instance.

- [x] T004 [US1] Pass the keyword field as `initialFocus` in `ops-portal/src/components/ConfirmationDialog.tsx`.
- [x] T005 [US1] Add the cold-start regression test in `ops-portal/src/components/ConfirmationDialog.focus.test.tsx`.
- [x] T006 [US1] Add settled-focus tests in `ops-portal/src/components/ConfirmationDialog.test.tsx`.

## Phase 3: Gate and no-keyword behavior

- [x] T007 [US2] Keep the exact keyword gate tests, including the whitespace cases.
- [x] T008 [US3] Keep the focus-in-dialog test for a dialog with no keyword.

## Phase 4: Verification and delivery

- [x] T009 Run typecheck, lint, and the full Vitest suite in `ops-portal/`.
- [x] T010 Run the mutation check and confirm that the cold-start test fails without `initialFocus`.
- [x] T011 Add `changelog.d/issue-4737-confirmation-dialog-keyboard-focus.md`.
- [ ] T012 Run browser validation of the issue steps.
- [ ] T013 Open the pull request after browser validation and human review.

## Dependencies and Execution

T001 through T003 precede implementation. T004 precedes T005 and T006.
T009 and T010 precede the local commit. T012 and T013 remain open after the commit.
