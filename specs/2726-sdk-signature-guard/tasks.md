# Tasks: mistapi SDK signature guard

**Input**: Design documents from `specs/2726-sdk-signature-guard/`

**Prerequisites**: `plan.md`, `spec.md`

**Tests**: Negative tests are required by issue #2726.

**Organization**: Tasks are ordered by dependency.

## Phase 1: Setup

- [x] T001 Read issue #2726, issue #2689, issue #2717, and repository instructions. (delivered: specs/2726-sdk-signature-guard/plan.md)
- [x] T002 Create worktree `MistHelper-2726-sig-guard` from `origin/main`. (delivered: specs/2726-sdk-signature-guard/plan.md)
- [x] T003 Confirm `mistapi` 0.64.0 and zero collection errors. (delivered: specs/2726-sdk-signature-guard/plan.md)

## Phase 2: Guard Design

- [x] T004 Add SDK signature records for required parameters, accepted keywords, and dynamic argument support. (delivered: tests/integration/test_mistapi_sdk_compatibility.py)
- [x] T005 Add call-site argument records for positional arguments, keywords, `*args`, and `**kwargs`. (delivered: tests/integration/test_mistapi_sdk_compatibility.py)
- [x] T006 Add the signature comparator for required parameters, removed keywords, and positional arity. (delivered: tests/integration/test_mistapi_sdk_compatibility.py)

## Phase 3: Guard Proof Tests

- [x] T007 Add a negative test for an omitted required parameter. (delivered: tests/integration/test_mistapi_sdk_compatibility.py)
- [x] T008 Add a negative test for a removed parameter. (delivered: tests/integration/test_mistapi_sdk_compatibility.py)
- [x] T009 Add a negative test for zero checked call signatures. (delivered: tests/integration/test_mistapi_sdk_compatibility.py)
- [x] T010 Add a dynamic-call baseline growth test. (delivered: tests/integration/test_mistapi_sdk_compatibility.py)

## Phase 4: Documentation and Release Note

- [x] T011 Write the feature specification. (delivered: specs/2726-sdk-signature-guard/spec.md)
- [x] T012 Write the implementation plan. (delivered: specs/2726-sdk-signature-guard/plan.md)
- [x] T013 Write this dependency-ordered task list. (delivered: specs/2726-sdk-signature-guard/tasks.md)
- [x] T014 Add the release-note fragment. (delivered: changelog.d/issue-2726-sdk-signature-guard.md)

## Phase 5: Validation and Delivery

- [x] T015 Run local quality gates and record final lines in the pull request. (delivered: pull request validation notes)
- [ ] T016 Commit, push, and open the pull request for issue #2726.
- [ ] T017 Wait for required checks, add `auto-merge` only after CodeQL passes, and verify issue closure.

## Dependencies & Execution Order

- Phase 1 blocks all other work.
- Phase 2 blocks Phase 3.
- Phase 3 blocks Phase 4.
- Phase 4 blocks Phase 5.

## Parallel Opportunities

- T011, T012, and T013 can be reviewed independently after T006.
- Local validation commands can run in separate shells only when they do not write shared output.
