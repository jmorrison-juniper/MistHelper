# Tasks: Strategy Failure Limit

**Input**: [spec.md](spec.md), [plan.md](plan.md), and [UI contract](contracts/ui.md).

**Scope**: Prepare one validated local commit for issue #3326.
Publication requires a later parent grant and is not part of these tasks.

## Phase 1: Claim and Contract

- [x] T001 Read the live issue, all comments, and all paginated open PR file lists. Reserve the owned paths.
  (delivered: specs/3326-strategy-failure-limit/plan.md)
- [x] T002 Write the feature-only specification, plan, tasks, and UI contract from the current templates.
  (delivered: specs/3326-strategy-failure-limit/spec.md, specs/3326-strategy-failure-limit/plan.md,
  specs/3326-strategy-failure-limit/tasks.md, specs/3326-strategy-failure-limit/contracts/ui.md)

## Phase 2: User Story 1 - Applicable Failure Controls

- [x] T003 Restore only the ignored worktree environment after the actual missing-package and bootstrap failures.
  (delivered: specs/3326-strategy-failure-limit/plan.md)
- [x] T004 Add the dedicated browser proof and record its failure against the unchanged shipped template.
  (delivered: tests/e2e/upgrade_portal/strategy_failure_limit/test_journey.py)
- [x] T005 Add direct counted negative controls under `tests/unit/upgrade_portal/strategy_failure_limit/`.
  (delivered: tests/unit/upgrade_portal/strategy_failure_limit/test_guard_controls.py,
  tests/unit/upgrade_portal/strategy_failure_limit/test_boundary_counts.py)
- [x] T006 Add initial-render contracts under `tests/contract/upgrade_portal/strategy_failure_limit/`.
  (delivered: tests/contract/upgrade_portal/strategy_failure_limit/test_template.py)
- [x] T007 Change only the failure group and its initial-state expression in the owned organization options template.
  (delivered: src/upgrade_portal/app/assets/templates/upgrade/org_options.html)
- [x] T008 Prove all strategies, repeated changes, values, required validation, exact payloads, and zero firmware starts.
  (delivered: tests/e2e/upgrade_portal/strategy_failure_limit/test_journey.py,
  tests/e2e/upgrade_portal/strategy_failure_limit/browser.py,
  tests/e2e/upgrade_portal/strategy_failure_limit/portal.py)

## Phase 3: Preservation and Local Commit

- [x] T009 Run the browser proof under full CI collection and run adjacent existing option and strategy journeys.
  (delivered: tests/e2e/upgrade_portal/strategy_failure_limit/test_journey.py)
- [x] T010 Run applicable quality checks and document exact results, measured counts, and capability limits.
  (delivered: specs/3326-strategy-failure-limit/plan.md)
- [x] T011 Add the unique release fragment and complete read-only requirement-to-test analysis.
  (delivered: changelog.d/issue-3326-strategy-failure-limit.md,
  specs/3326-strategy-failure-limit/spec.md, specs/3326-strategy-failure-limit/plan.md)
- [x] T012 Prepare the full offline PR template. Verify resource cleanup and stage only owned files.
  (delivered: specs/3326-strategy-failure-limit/plan.md)
- [ ] T013 Await the parent's grant of a verified main SHA before publication or delivery completion.
  This task needs an explicit parent decision. The local receipt does not provide that decision.

## Dependencies & Execution Order

T001 precedes T002. T002 and T003 precede T004.
T004 precedes the product edit in T007.
T005 and T006 define the negative controls and initial states before the edit.
T007 precedes T008. T008 precedes T009 and T010.
T009 and T010 precede T011 and T012.
The local commit and its committed-scope check follow T012.
T013 remains outside local preparation until the parent supplies the required grant.

## Notes

Tick a task only after its evidence exists.
Missing packages, skips, bootstrap faults, and optional baseline failures do not prove acceptance.
No local task authorizes publication or a live firmware operation.
