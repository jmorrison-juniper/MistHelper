# Tasks: Configure the multi-site write gate

**Issue**: #3203 | **Plan**: [plan.md](plan.md)

## Implementation

- [x] T001 Add the strict environment reader and the frozen write settings.
- [x] T002 Apply the setting to the existing Flask write gate.
- [x] T003 Name the setting on the closed confirmation page.
- [x] T004 Document the setting in `deploy/.env.example`.

## Validation

- [x] T005 Add unit tests for the default, true, false, and unknown values.
- [x] T006 Add a contract test for the open and closed page states.
- [x] T007 Add the release-note fragment.
- [x] T008 Run the focused tests and the required local quality gates.
