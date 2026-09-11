# Tasks: Discoverable Upgrade Confirmation Navigation

## Phase 1: Specification and design

- [x] T001 Write issue-scoped specification in `specs/2447-confirmation-navigation/spec.md`
- [x] T002 Write implementation plan and research artifacts in `specs/2447-confirmation-navigation/`

## Phase 2: Regression tests

- [x] T003 Add contract coverage for the confirmation link in `tests/contract/upgrade_portal/test_upgrade_routes.py`
- [x] T004 Add Playwright coverage for visible run-page navigation in `tests/e2e/upgrade_portal/test_capture.py`

## Phase 3: Implementation

- [x] T005 Render the state-gated confirmation link in `src/upgrade_portal/app/assets/templates/upgrade/progress.html`
- [x] T006 Run focused contract and Playwright tests and correct regressions

## Phase 4: Verification and issue update

- [x] T007 Verify the confirmation safety UI with Playwright tests; the full live walk was skipped because the isolated fixture had no usable cloud token/site data
- [x] T008 Update GitHub issue #2447 with SpecKit links, test results, and remaining findings
- [x] T009 Commit, push, open/update PR, and monitor checks
