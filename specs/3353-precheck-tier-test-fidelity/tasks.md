# Tasks: Pre-check tier test fidelity

**Input**: [spec.md](spec.md) and [plan.md](plan.md).

## Setup

- [x] T001 Check issue ownership and all exact files of the open pull requests.
  Reserve the seven issue-owned paths before edits. (delivered: specs/3353-precheck-tier-test-fidelity/spec.md)
- [x] T002 Define the test-only scope and preserve the existing selection rules.
  (delivered: specs/3353-precheck-tier-test-fidelity/plan.md)

## User Story 1 - Read the selected capture tier

- [x] T003 [US1] Add exact identifier and tier cases to `tests/unit/upgrade_portal/test_e2e_standin_precheck_adopter.py`.
  Prove absent captures, missing tiers, malformed tiers, and unchanged standalone selection.
  (delivered: tests/unit/upgrade_portal/test_e2e_standin_precheck_adopter.py)
- [x] T004 [US1] Record the new unit tests failing against the unchanged stand-in.
  The red run reports 23 new failures and 10 existing passes.
  (delivered: tests/unit/upgrade_portal/test_e2e_standin_precheck_adopter.py)
- [x] T005 [US1] Add `newest_precheck_tier` to `tests/support/upgrade_portal_e2e/records/portal.py`.
  Reuse the selected capture and production tier conversion.
  (delivered: tests/support/upgrade_portal_e2e/records/portal.py)
- [x] T006 [US1] Prove full coverage of the new method. Run the focused unit and contract tests.
  The method covers 9 of 9 statements and 2 of 2 branches. All 152 focused tests pass.
  (delivered: tests/support/upgrade_portal_e2e/records/portal.py)

## User Story 2 - Prove the displayed tier

- [x] T007 [US2] Add actual tier-cell assertions to `tests/e2e/upgrade_portal/test_org_missing_precheck_journey.py`.
  (delivered: tests/e2e/upgrade_portal/test_org_missing_precheck_journey.py)
- [x] T008 [US2] Record the tier 3 cell assertion failing before the stand-in repair.
  Chromium reports the actual cell value as 2, not 3.
  That failure also reaches the existing teardown guard with one in-process hold.
  (delivered: tests/e2e/upgrade_portal/test_org_missing_precheck_journey.py)
- [x] T009 [US2] Run the repaired journey and adjacent capture, standalone-adoption, and tier journeys in isolated Chromium.
  The broad run reports 33 passes and one confirmed pre-existing skip.
  The three required tier tests pass with zero skips. The green guards report zero holds and zero live runs.
  (delivered: tests/e2e/upgrade_portal/test_org_missing_precheck_journey.py)

## Delivery

- [x] T010 Run the configured local quality checks with unchanged manifests, exclusions, baselines, and thresholds.
  Ruff, Black, the CI type scope, strict changed-test types, Bandit, links, citations, and the quality ratchet pass.
  The strict runtime audit checks 105 dependencies and reports zero known vulnerabilities.
  The STE check uses heuristic rules because the licensed dictionary is absent. PowerShell is absent.
  (delivered: specs/3353-precheck-tier-test-fidelity/tasks.md)
- [x] T011 Add `changelog.d/issue-3353-precheck-tier-test-fidelity.md`.
  (delivered: changelog.d/issue-3353-precheck-tier-test-fidelity.md)
- [x] T012 Verify the exact reserved file set and prepare the local delivery evidence.
  (delivered: specs/3353-precheck-tier-test-fidelity/tasks.md)

After these tasks, commit the seven reserved files.
Report the clean SHA and the command results to the parent.
Do not push or open a pull request.

## Confirmed Adjacent Limitation

The unchanged released revision is `856e5065413d3026f9c0f6d5222d9d379ec79d8b`.
An owned detached worktree at that revision reproduced the standalone walk's skip in Chromium.
The exact reason is "The options page offered no version, so the save would keep an empty plan."

The imported baseline stand-in has no tier pair reader. Its tracked source remained unchanged.
The baseline guards reported zero holds and zero live runs.
The cleanup removed the owned baseline worktree after the check.

The same adjacent walk remains unverified on the repaired tree.
The issue changes no version wiring, shared factory, quality baseline, or unreserved journey.

## Dependencies

T003 and T007 require T001 and T002.
T004 requires T003. T008 requires T007.

T005 requires T004 and T008.
T006 and T009 require T005.

T010 requires T006 and T009. T011 requires the verified repair.
T012 requires T010 and T011.
