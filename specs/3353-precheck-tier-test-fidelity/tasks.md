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

The first local delivery stopped at commit `c7bdb2f1464fb710f22368b282f7e477ef45c9ba`.
The parent later grants sole publication on verified main `5d38898af5639e90715ec57eb8d48d2985e1acf8`.

## Current-Base Evidence

- [x] T013 Reclaim the temporary browser-file handoff and preserve the merged model controls during the authorized rebase.
  Keep the same capture exclusions without importing a second conftest instance.
  (delivered: tests/e2e/upgrade_portal/test_org_missing_precheck_journey.py)
- [x] T014 Repeat the red and green pair, tier-cell, collection, and leak-guard evidence on the granted base.
  The red unit run reports 23 failures and 10 passes.
  The red browser reads tier 2 instead of 3 and reaches the unchanged one-hold teardown refusal.
  Both source variants collect 515 E2E cases under the CI package name.
  The required three tier cases pass without skips.
  The complete E2E run reports 463 passes and 52 existing skips.
  Its guards check 134 trail records, eight sites, and 363 history rows across 65 modules.
  They report zero leaked holds, zero live runs, and an unchanged checkout trail.
  (delivered: tests/e2e/upgrade_portal/test_org_missing_precheck_journey.py)
- [x] T015 Verify current-base local checks without changing a quality input.
  The focused run reports 173 passes. The reader covers all nine statements and both branches.
  The complete portal unit run reports 4,407 passes and one Windows-only skip on macOS.
  The preflight reads and validates six required inputs and checks three active guides.
  The full ratchet checks 1,001 files and 725 existing findings. It reports zero new findings or parse errors.
  The runtime audit checks 105 dependencies with zero skipped records or known vulnerabilities.
  (delivered: specs/3353-precheck-tier-test-fidelity/tasks.md)

After local verification, publish one checked head under the parent's exact-base grant.
Keep auto-merge disabled and preserve all 23 template items.
Require all current strict statuses before the protected exact-head squash merge.
Test the exact resulting main revision locally and record a persistent pull request receipt.

## Confirmed Adjacent Limitation

The unchanged released revision is `856e5065413d3026f9c0f6d5222d9d379ec79d8b`.
An owned detached worktree at that revision reproduced the standalone walk's skip in Chromium.
The exact reason is "The options page offered no version, so the save would keep an empty plan."

The imported baseline stand-in has no tier pair reader. Its tracked source remained unchanged.
The baseline guards reported zero holds and zero live runs.
The cleanup removed the owned baseline worktree after the check.

The same adjacent walk remains unverified on the repaired tree.
The issue changes no version wiring, shared factory, quality baseline, or unreserved journey.

The unchanged granted base `5d38898af5639e90715ec57eb8d48d2985e1acf8` reproduces the same version-options skip.
The current full run preserves that skip and the 51 operator journeys that run only on request.
No required pair or tier-cell case is skipped.

## Dependencies

T003 and T007 require T001 and T002.
T004 requires T003. T008 requires T007.

T005 requires T004 and T008.
T006 and T009 require T005.

T010 requires T006 and T009. T011 requires the verified repair.
T012 requires T010 and T011.
