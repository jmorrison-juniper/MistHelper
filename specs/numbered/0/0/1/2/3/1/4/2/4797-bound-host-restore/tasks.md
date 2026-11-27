# Tasks: Bound host restore for the WLAN RADIUS fixture

**Input**: Record `specs/numbered/0/0/1/2/3/1/4/2/4797-bound-host-restore/`. Plan and spec are in this folder.

**Preconditions**:

- **Gate G-1**: PR #4208 is closed or merged. Check with `gh pr view 4208 --json state,mergedAt,headRefName` before T005 starts.
- **Gate G-2**: The orchestrator authorizes the merge before T-MERGE starts.
- **Decision D-9** (human): The owner chooses the merge timing of PR #4208. Gate G-1 follows that choice.

**Status values**: open (not run), verified-present (verified in remote content), partial (some parts verified), absent (not in repository).

## Phase 1: Verify the fix on PR #4208 before the merge

- [ ] T001 [P] [FR-003] Reproduce the defect on the candidate commit.
  - Files: `tests/unit/refactors/test_wlanradius_timer_manager_paths.py`, `tests/unit/wan_performance/test_request_admission.py` in commit 2037e9b95e2ad3b5cc1d02ac0b48a140d5dc1473.
  - Acceptance: The admission test fails with the site organization error. The run reports one failed test.
  - Verification: Tests row (local gates line 61): `python -m pytest -q tests\unit\refactors\test_wlanradius_timer_manager_paths.py tests\unit\wan_performance\test_request_admission.py::test_site_request_uses_the_selected_organization_context --tb=short --show-capture=no`
  - Status: open.

- [ ] T002 [P] [FR-004] Verify the fix on the PR head.
  - Files: the same two paths in commit 843be63bc837513b4442dae69da9f0db922e0ed1.
  - Acceptance: Both test targets pass. The run reports zero failed tests.
  - Verification: Tests row (local gates line 61), same command in the PR head worktree.
  - Status: open.

- [ ] T003 [FR-002] [FR-005] Run shard 1 on the PR head.
  - Files: `tests\unit` in the PR head worktree.
  - Acceptance: The summary line reports zero failed tests. The passed and skipped counts appear in the evidence.
  - Verification: Full tests row (local gates line 62), shard 1 (line 87).
  - Command: `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal`
  - Status: open. Depends on T002.

- [ ] T004 [FR-002] [FR-006] Run shard 2 on the PR head.
  - Files: `tests\contract`, `tests\guardrails`, `tests\integration` in the PR head worktree.
  - Acceptance: The summary line reports zero failed tests for shard 2.
  - Verification: Full tests row (local gates line 62), shard 2 (line 88).
  - Command: `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal`
  - Status: open. Depends on T002.

## Phase 2: Follow-up on main after PR #4208 closes

- [ ] T005 [FR-001] [FR-007] Add the `previous_host_guard` fixture and the `TestFakeHostRestore` class.
  - Files: `tests/unit/refactors/test_wlanradius_timer_manager_paths.py`.
  - Acceptance: Both cases pass with the restore in place. The fixture logs before and after each action.
  - Verification: Tests row (local gates line 61): `python -m pytest tests\unit\refactors\test_wlanradius_timer_manager_paths.py`
  - Status: absent. Depends on gate G-1.

- [ ] T006 [FR-007] Run the mutation check in a scratch worktree.
  - Files: `tests/unit/refactors/test_wlanradius_timer_manager_paths.py` in a scratch worktree. Replace the `patch.object` line with `_MH.bind_root_module(fake)`.
  - Acceptance: Both cases report an error at teardown without the restore.
  - Verification: Tests row (local gates line 61) in the scratch worktree.
  - Status: absent. Depends on T005.

- [ ] T007 [FR-006] Add the record folder under the route.
  - Files: `specs/numbered/0/0/1/2/3/1/4/2/4797-bound-host-restore/` with `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, `design/research.md`, `design/data-model.md`, `design/quickstart.md`, and `design/checklists/requirements.md`.
  - Acceptance: The process folder guard passes. Each directory holds five children or fewer.
  - Verification: Full tests row (local gates line 62), shard 2 (line 88).
  - Status: absent. Depends on T005.

- [ ] T008 [FR-009] Run the test quality ratchet on the committed change.
  - Files: `tests/unit/refactors/test_wlanradius_timer_manager_paths.py`.
  - Acceptance: The gate line reports zero new findings against the baseline.
  - Verification: Test quality row (local gates line 65): `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt`
  - Status: open. Depends on T005 and a local commit.

## Final tasks

- [ ] T-LOCAL-GATES [FR-001] [FR-005] [FR-006] [FR-008] [FR-009] Run the applicable local gates on the follow-up branch.
  - Files: `tests/unit/refactors/test_wlanradius_timer_manager_paths.py` and the record folder `specs/numbered/0/0/1/2/3/1/4/2/4797-bound-host-restore/`.
  - Verification: Lint row (line 58): `python -m ruff check .`. Format row (line 59): `python -m black --check .`. Tests row (line 61). Full tests row (line 62). Test quality row (line 65).
  - Status: open. Depends on T005, T006, T007, and T008.

- [ ] T-PR [FR-002] [FR-007] Open the follow-up pull request.
  - Files: branch `fix/4797-bound-host-restore` with `tests/unit/refactors/test_wlanradius_timer_manager_paths.py` and the record folder only.
  - Acceptance: The title is `fix(tests): restore the bound host after the fake_mh fixture`. The body contains `Closes #4797`.
  - Verification: Tests row (local gates line 61) on the committed change.
  - Status: absent. Depends on T-LOCAL-GATES.
  - Warning: a push to the PR #4208 branch changes work that another owner controls. Never push to that branch.

- [ ] T-REMOTE-CI [FR-005] [FR-006] Confirm the required checks on the follow-up pull request and on PR #4208.
  - Files: none changed.
  - Acceptance: All 15 required checks show SUCCESS on each pull request head.
  - Verification: Full tests row (local gates line 62) locally, and `gh pr checks` with the follow-up pull request number remotely.
  - Status: partial. PR #4208 shows 15 of 15 required checks as SUCCESS. The follow-up has no checks yet.

- [ ] T-MERGE [FR-002] Add the auto-merge label after gate G-2 and after every required check passes.
  - Files: none changed.
  - Acceptance: Main contains the follow-up commit. Issue #4797 closes through the closing reference.
  - Verification: Tests row (local gates line 61) on the merged main checkout.
  - Status: absent. Depends on T-REMOTE-CI and gate G-2.
