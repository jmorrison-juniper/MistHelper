# Tasks: RADIUS API Failure Test Assertion

**Input**: Records in `specs/numbered/0/0/1/2/3/1/4/3/4798-radius-api-failure-test-assertion/`.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, `design/quickstart.md`, `design/contracts/operator-failure-message.md`.

**Format**: `[ID] [P?] Description`. `[P]` marks a task that can run in parallel with other `[P]` tasks. Each task names its requirements, exact paths, acceptance statement, verification command, and status.

**Status values**: `open`, `verified-present`, `partial`, `absent`.

## Phase 1: Target Change

### T001 Edit the target test

- Parallel: no
- Requirements: FR-001, FR-002, FR-007
- Files: `tests/unit/refactors/test_wlanradius_timer_manager_paths.py`
- Acceptance: The header, body, and assertion match plan section "File-by-File Change Map". Each changed line has a `# WHY:` comment.
- Verification: `.venv\Scripts\python.exe -m pytest -q tests\unit\refactors\test_wlanradius_timer_manager_paths.py::TestApplyChangesDispatch::test_an_api_failure_is_contained`
- Status: partial. The assertion commit `843be63` has the assertion. Lines 707, 710, and 712 lack comments (research RC-06, analysis A-9).

### T002 [P] Keep the baseline unchanged

- Requirements: FR-005, FR-004
- Files: `.github/test-quality-baseline.json`
- Acceptance: `git diff --quiet origin/main -- .github/test-quality-baseline.json` exits 0. No write option runs.
- Verification: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt`
- Status: verified-present. PR #4208 does not list the baseline file. The `main` blob is `512da22b` (research RC-14, section 2).

### T003 [P] Confirm the one-file scope

- Requirements: FR-006, SC-004
- Files: `src/foundation/support/refactors/wlanradius_timer_manager.py`, `tests/unit/refactors/test_wlanradius_timer_manager_paths.py`
- Acceptance: `symbol-diff` reports no module-level change. The production file has no diff against `origin/main`.
- Verification: `.venv\Scripts\symbol-diff.exe --base origin/main tests\unit\refactors\test_wlanradius_timer_manager_paths.py`
- Status: verified-present. Commit `843be63` changes one file, the test module (research RC-07).

## Phase 2: Proof

### T004 Run the scoped test-quality gate

- Parallel: no
- Requirements: FR-004, SC-001
- Files: `tests/unit/refactors/test_wlanradius_timer_manager_paths.py`, `.github/test-quality-config.toml`, `.github/test-quality-baseline.json`
- Acceptance: The output prints `gate: 0 new findings vs baseline`. The exit code is 0.
- Verification: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt`
- Status: open. The remote job reports SUCCESS on PR head `843be63`. The local run is still open.

### T005 Run the full-suite test-quality gate

- Parallel: no
- Requirements: FR-004
- Files: `.github/test-quality-baseline.json`, `.github/test-quality-config.toml`
- Acceptance: The output prints `gate: 0 new findings vs baseline`. If the count is not zero, stop and report it.
- Verification: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json`
- Status: open.

### T006 [P] Prove that the target test can fail

- Parallel: yes, in a separate worktree
- Requirements: FR-003, SC-003
- Files: `src/foundation/support/refactors/wlanradius_timer_manager.py` (temporary edit in a worktree only), `tests/unit/refactors/test_wlanradius_timer_manager_paths.py`
- Acceptance: Mutation 1 and mutation 2 each fail the target test. Each revert restores the file. No `src` file differs from `origin/main`.
- Verification: `.venv\Scripts\python.exe -m pytest -q tests\unit\refactors\test_wlanradius_timer_manager_paths.py::TestApplyChangesDispatch::test_an_api_failure_is_contained`
- Status: open. Quickstart Scenario 4 lists both mutations.

### T007 Run the module tests

- Parallel: no
- Requirements: FR-008, SC-002
- Files: `tests/unit/refactors/test_wlanradius_timer_manager_paths.py`
- Acceptance: The module run reports zero failed tests and zero errors.
- Verification: `.venv\Scripts\python.exe -m pytest -q tests\unit\refactors\test_wlanradius_timer_manager_paths.py`
- Status: open.

## Phase 3: Final Tasks

### T-LOCAL-GATES Run each applicable local gate

- Parallel: no
- Requirements: FR-007, FR-008
- Files: `tests/unit/refactors/test_wlanradius_timer_manager_paths.py`
- Acceptance: Compile prints nothing. Lint, format, bandit, and symbols pass. Quickstart Scenario 5 lists each skipped gate with its reason.
- Verification: `.venv\Scripts\python.exe -m ruff check .`
- Status: open.

### T-PR Deliver through PR #4208

- Parallel: no
- Requirements: FR-009
- Files: `tests/unit/refactors/test_wlanradius_timer_manager_paths.py`
- Acceptance: The follow-up commit sits on the PR branch with no force push. The PR title keeps the Conventional Commits form. No second open PR changes the module.
- Verification: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt`, run on the PR head.
- Status: open.
- Fallback: If PR #4208 closes unmerged, branch `fix/4798-radius-api-failure-test-assertion` from `main`. Commit `test(tests): assert the contained RADIUS API failure message`. Open a PR with `Closes #4798` in its body.

### T-REMOTE-CI Watch the remote checks

- Parallel: no
- Requirements: FR-004
- Files: `tests/unit/refactors/test_wlanradius_timer_manager_paths.py`
- Acceptance: The check `Test quality ratchet (gate)` reports SUCCESS on the final PR head. No required check reports FAILURE.
- Verification: The `test_quality_gate` job in `.github/workflows/ci.yml` (line 602, job name at line 603), run through the same scoped command as T004.
- Status: open. The snapshot on 2026-11-26 shows SUCCESS on head `843be63`. The follow-up commit needs a new run.

### T-MERGE Merge after authorization

- Parallel: no
- Requirements: FR-009
- Files: `tests/unit/refactors/test_wlanradius_timer_manager_paths.py`
- Acceptance: The orchestrator authorizes the merge. The PR is not a draft. The merge state is CLEAN. The owner then closes issue #4798 by hand.
- Verification: The full-suite command from T005, run on `main` after the squash merge. The result must read `gate: 0 new findings vs baseline`.
- Status: open. Blocked by analysis item A-2, because PR #4208 is a draft with merge state DIRTY.

## Dependencies

- T001 must finish before T002, T004, T005, T006, and T007.
- T002 and T003 run in parallel after T001.
- T006 runs in a separate worktree after T001.
- T-LOCAL-GATES runs after T004, T005, T007, and T003.
- T-PR runs after T-LOCAL-GATES.
- T-REMOTE-CI runs after T-PR.
- T-MERGE runs after T-REMOTE-CI and after the orchestrator authorizes the merge.

## Requirement Coverage

| Requirement | Tasks | Tests |
| - | - | - |
| FR-001 | T001 | TC-001 |
| FR-002 | T001 | TC-001 |
| FR-003 | T006 | TC-002, TC-003 |
| FR-004 | T002, T004, T005, T-REMOTE-CI | TC-005, TC-006 |
| FR-005 | T002 | TC-007 |
| FR-006 | T003 | TC-008 |
| FR-007 | T001, T-LOCAL-GATES | TC-009 |
| FR-008 | T007, T-LOCAL-GATES | TC-004, TC-009 |
| FR-009 | T-PR, T-MERGE | TC-010 |
| FR-010 | Record self-review | TC-011 |
