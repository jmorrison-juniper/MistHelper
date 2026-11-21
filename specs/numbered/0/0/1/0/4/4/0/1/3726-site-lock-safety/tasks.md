# Tasks: Site Lock Safety for Uncertain Upgrade Replies

**Input**: Numeric specification from `/specs/numbered/0/0/1/0/4/4/0/1/3726-site-lock-safety/`.

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), `design/research.md`, `design/data-model.md`, and `design/quickstart.md`.

## Phase 1: Setup

The Python project and test structure already exist. No dependency or service setup is required.

## Phase 2: Foundational

- [x] T001 Run read-only consistency analysis on `specs/numbered/0/0/1/0/4/4/0/1/3726-site-lock-safety/` before implementation. (Verified: report in this session. The required PowerShell prerequisite command could not run because `pwsh` is not installed.)

## Phase 3: Regression Tests

Add every regression test before changing the production modules.

- [ ] T002 [P] [US1] Add the accepted, refusal, and uncertain response matrix plus a one-call no-retry check to `tests/unit/firmware/test_aggregate_upgrade_service.py`.
- [ ] T003 [P] [US1] Add uncertain, legacy rejected, proven refusal, and not-submitted lock cases to `tests/unit/upgrade_portal/test_org_upgrade_lock_release.py`.
- [ ] T004 [P] [US3] Add refusal and uncertainty cases to `tests/unit/upgrade_portal/test_org_cancel_outcomes.py`.

## Phase 4: Implementation

- [ ] T005 [US1] Add the shared refusal policy and classify organization and device replies in `src/operations/execution/firmware/aggregate_upgrade_service.py`.
- [ ] T006 [US2] Require a final child state or proven refusal evidence before releasing locks in `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py`.
- [ ] T007 [US3] Use the shared refusal policy in `src/interfaces/portals/upgrade_portal/upgrade/org_cancel_outcomes.py`.

## Phase 5: Validation and Documentation

- [ ] T008 Run the focused tests in `tests/unit/firmware/test_aggregate_upgrade_service.py`, `tests/unit/upgrade_portal/test_org_upgrade_lock_release.py`, `tests/unit/upgrade_portal/test_org_cancel_outcomes.py`, and `tests/contract/upgrade_portal/test_org_upgrade_routes.py::test_unknown_submission_blocks_a_repeat`. Review the diff for unchanged timeout and lock-lease behavior.
- [ ] T009 [P] Document uncertain submissions and retained site locks in `documentation/upgrade_capture_portal.md`.
- [ ] T010 [P] Add the issue-specific release note in `changelog.d/issue-3726-site-lock-safety.md`.

## Dependencies and Execution Order

### Phase Dependencies

- Run T001 before any implementation task.
- Regression tests T002, T003, and T004 can run in parallel because they use different test files.
- Implementation task T005 must precede T006 and T007 because both modules reuse its refusal policy.
- Run T008 after all implementation tasks. Add documentation and release notes only after the focused tests pass.

### Parallel Opportunities

- T002, T003, and T004 use different test files and can run in parallel after T001.
- T009 and T010 use separate files and can run in parallel after T008.
- T005, T006, and T007 are sequential because the route and cancellation modules import the shared policy.

## Implementation Strategy

1. Write the three offline regression test groups and confirm that they fail on the unsafe behavior.
2. Implement the shared outcome policy, lock release check, and cancellation-list check.
3. Run all focused tests and directly applicable local gates.
4. Add the portal guide update and the issue-specific release note.
5. Open one pull request for issue 3726. Do not merge, approve, enable auto-merge, or deploy.

## Notes

- Each task names its target file and follows the checklist format.
- Do not run live Mist requests, production lock actions, or firmware operations.
- Preserve the existing retry, timeout, lease, and operator recovery behavior.
- The README and deployment pipeline conflicts remain unresolved. Do not implement this plan until the user resolves them.
