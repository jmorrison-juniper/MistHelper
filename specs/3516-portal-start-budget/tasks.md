# Tasks: Give the browser portal a robust start budget

**Issue**: #3516
**Specification**: `specs/3516-portal-start-budget/spec.md`
**Plan**: `specs/3516-portal-start-budget/plan.md`

## Implementation

- [x] T001 Write the specification and plan.
- [x] T002 Raise the default portal start budget to 60 seconds.
- [x] T003 Check the child process after each failed port probe.
- [x] T004 Report the measured wait and the child exit code.
- [x] T005 Add focused ready, early-exit, and timeout tests.
- [x] T006 Add the changelog fragment.

## Verification

- [x] T007 Run the focused unit tests.
- [x] T008 Run Ruff and Black on the changed Python files.
- [x] T009 Run the changelog fragment guard.
- [x] T010 Run Bandit and the complexity gate on the changed Python files.
- [ ] T011 Run the test quality preflight and changed-test gate.
