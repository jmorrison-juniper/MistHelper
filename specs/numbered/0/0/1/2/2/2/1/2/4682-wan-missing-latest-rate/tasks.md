# Tasks: Report a missing latest WAN rate

**Input**: Numeric record `specs/numbered/0/0/1/2/2/2/1/2/4682-wan-missing-latest-rate/`.

**Prerequisites**: `spec.md` (required), `plan.md` (required), `design/research.md`, `design/data-model.md`, and `design/contracts/rate-sample.md`.

**Tests**: Required by FR-010 and SC-001. The five test names appear in `analysis.md`, section "Consistency Review".

**Organization**: Tasks run in phases. Each task lists its requirements, exact paths, acceptance statement, verification command, and status.

**Status values**: `open` means the step has not run. `absent` means the required change is not in the repository yet. `verified-present` means this pass confirmed the state.

## Phase 1: Preconditions

- [ ] T001 Confirm the release of `snapshot_client.py` and re-read the target function. Requirements: FR-001, FR-007. Paths: `src/interfaces/wan_performance/collection/snapshot_client.py`. Acceptance: Pull request 4208 is merged, or closed with the file released. The current line of `_sample` is recorded. Verification: `python -m pytest tests/unit/wan_performance/test_gateway_insights.py` (Tests gate, copilot-instructions.md line 61). Status: open.

## Phase 2: Red Tests

- [ ] T002 [US1] [US2] Add five test functions to the selected-port test group. Requirements: FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-010, and SC-001. Paths: `tests/unit/wan_performance/test_gateway_insights.py`. Acceptance: Five test functions exist, with the names listed in `analysis.md`. The first two fail before T003. Verification: `python -m pytest tests/unit/wan_performance/test_gateway_insights.py` (Tests gate). Status: absent. Depends on T001.

## Phase 3: Fix and Documentation

- [ ] T003 [US1] [US2] Change the rate sample builder to use the latest expected interval. Requirements: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-011. Paths: `src/interfaces/wan_performance/collection/snapshot_client.py`. Acceptance: `_sample` sets `value` from the latest expected start only. The reasons follow D-5. `raw_values`, `sample_count`, `coverage_fraction`, `points`, and `partial` keep their meaning. Each touched line has an inline comment. `_sample` logs before and after the selection. Verification: `python -m pytest tests/unit/wan_performance/test_gateway_insights.py` (Tests gate, all tests pass). Status: absent. Depends on T002.

- [ ] T004 [P] [US3] Update the missing-value rule in the guide. Requirements: FR-012. Paths: `documentation/wan-performance.md`. Acceptance: One sentence near line 152 states that a missing latest interval gives no current value. The sentence has no semicolon. Verification: `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 documentation\wan-performance.md` (writing gate, quality-gates.md line 283, R-39). The same tool appears in copilot-instructions.md line 74 (R-30). Status: absent. Depends on T001.

- [ ] T005 [P] [US3] Add the release-note fragment. Requirements: FR-012. Paths: `changelog.d/issue-4682-wan-missing-latest-rate.md`. Acceptance: The fragment has one `### Fixed` heading and one bullet that names issue 4682. Verification: `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 changelog.d\issue-4682-wan-missing-latest-rate.md` (writing gate, quality-gates.md line 283). Status: absent. Depends on T001.

## Phase 4: Local Checks

- [ ] T006 Check the module-level names of the touched module. Requirements: SC-003, SC-005. Paths: `src/interfaces/wan_performance/collection/snapshot_client.py`. Acceptance: The symbol gate reports that no module-level name changed. The helper uses four parameters. No existing function gains a parameter. Verification: `symbol-diff --base origin/main src/interfaces/wan_performance/collection/snapshot_client.py` (Symbols row, copilot-instructions.md line 73, R-75). Status: open. Depends on T003.

- [ ] T-LOCAL-GATES Run each applicable gate of the local gates table. Requirements: SC-002, SC-004. Paths: `src/interfaces/wan_performance/collection/snapshot_client.py`, `tests/unit/wan_performance/test_gateway_insights.py`, `documentation/wan-performance.md`, and `changelog.d/issue-4682-wan-missing-latest-rate.md`. Acceptance: Each applicable row passes. Each row that does not apply has a stated reason in the pull request body. Verification: Each applicable row of the Local gates table (copilot-instructions.md section "Local gates", line 50, R-76, with rows R-29 and R-30). Status: open. Depends on T003, T004, T005, and T006.

## Phase 5: Delivery

- [ ] T-PR Commit, push, and open the pull request. Requirements: FR-011, FR-012, and SC-002. Paths: the four files listed in T-LOCAL-GATES. Acceptance: The commit subject is `fix(web-portal): report a missing latest WAN rate`. The branch is `fix/4682-wan-missing-latest-rate`. The pull request body contains `Closes #4682` and each gate result. Verification: `python -m pytest tests/unit/wan_performance/test_gateway_insights.py` (Tests gate on the pushed commit). Status: open. Depends on T-LOCAL-GATES.

- [ ] T-REMOTE-CI Watch the remote checks until each one passes. Requirements: SC-002. Paths: the four files listed in T-LOCAL-GATES. Acceptance: Each required check of the pull request is green. Verification: `gh pr checks --watch` (AGENTS.md, section "Pull request", line 221, R-73). The local gates table cannot verify remote checks. Status: open. Depends on T-PR.

- [ ] T-MERGE Squash merge the pull request after authorization. Requirements: SC-002. Paths: the four files listed in T-LOCAL-GATES. Acceptance: The orchestrator authorizes the merge. The `auto-merge` label is added only after each check is green. The branch and worktree are removed after the merge. Verification: `gh pr view --json state,mergedAt` (remote state check, AGENTS.md, section "Merge", line 233, R-74). Status: open. Depends on T-REMOTE-CI.

## Dependencies and Execution Order

- T001 gates every other task.
- T002 runs after T001. T003 runs after T002.
- T004 and T005 run after T001. They may run in parallel with T003.
- T006 runs after T003. T-LOCAL-GATES runs after T003, T004, T005, and T006.
- T-PR, T-REMOTE-CI, and T-MERGE run in order.

## Notes

- Caution: Start T003 only after T002 fails for the two defect tests. The red step proves the test can fail.
- Warning: Deleting the work branch before its pull request exists can remove the only reference to its commits.
