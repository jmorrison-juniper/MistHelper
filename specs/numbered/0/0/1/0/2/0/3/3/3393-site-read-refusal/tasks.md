# Tasks: Site read refusal

**Input**: [spec.md](spec.md), [plan.md](plan.md), and the supporting artifacts under `design/`.

## Phase 1: Setup

- [x] T001 Verify current code, issue comments, artifacts, ownership, and the unchanged baseline. (delivered: design/research.md)
- [x] T002 Resolve the managed feature route and write the specification and design. (delivered: spec.md, plan.md)

## Phase 2: Foundational

- [x] T003 Reuse the existing site fixtures without live services. (delivered: tests/contract/upgrade_portal/test_issue_3393_cloud_read_refusal.py)

## Phase 3: User Story 1 - Save after a cloud failure

**Independent test**: Refuse connection failures and timeouts without saving a plan. Preserve earlier state and permit a successful repeated save.

- [x] T004 [US1] Add failing save, replacement, and recovery contracts. (delivered: tests/contract/upgrade_portal/test_issue_3393_cloud_read_refusal.py)
- [x] T005 [US1] Add the narrow save handler. (delivered: src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py)
- [x] T006 [US1] Prove form-value preservation after the 503 envelope. (delivered: tests/e2e/upgrade_portal/test_org_upgrade_flow.py)

## Phase 4: User Story 2 - Read an affected page

**Independent test**: Both page reads return 503 and preserve any earlier plan.

- [x] T007 [US2] Add page transport-failure contracts. (delivered: tests/contract/upgrade_portal/test_issue_3393_cloud_read_refusal.py)
- [x] T008 [US2] Protect the two page reads. (delivered: src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py)

## Phase 5: Cross-cutting checks

- [x] T009 Add the release fragment and run the focused regression tests and applicable local gates. (delivered: changelog.d/issue-3393-site-read-refusal.md, analysis.md)
- [x] T010 Analyze requirement coverage and record the result. (delivered: analysis.md)
- [ ] T011 Commit the explicit manifest and run the documented test-quality comparison.

## Dependencies

T001 precedes T002. T002 precedes T003.
T003 precedes T004 and T007.
T004 precedes T005. T005 precedes T006.
T007 precedes T008.
T006 and T008 precede T009. T009 precedes T010. T010 precedes T011.

## Parallel execution

The browser test can run independently of the contract runner after both route handlers exist.
The two stories share one route module, so implementation remains serial.

## Implementation strategy

Prove the save failure first. Add the page-read cases before repairing all three route boundaries.
Use the existing successful and validation contracts as regression coverage.
Preserve issue #3394 lines unchanged.
