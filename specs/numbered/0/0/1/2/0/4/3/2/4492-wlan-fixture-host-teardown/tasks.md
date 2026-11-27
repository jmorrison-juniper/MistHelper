# Tasks: WLAN fixture host teardown

**Input**: `specs\numbered\0\0\1\2\0\4\3\2\4492-wlan-fixture-host-teardown\plan.md` and `spec.md`. Evidence lives in `design\research.md` (rows R-01 to R-76). Commands live in `design\quickstart.md`.

**Format**: `[ID] [P?] Description`. `[P]` marks a task that can run in parallel with other `[P]` tasks. Each task lists its requirement IDs, exact paths, acceptance, one verification command from the local gates table in `.github\copilot-instructions.md` (R-57), and its status. Status values are open, verified-present, partial, or absent.

## Phase 1: Implementation

- [ ] T001 Replace fixture lines 44 to 46 with the seven-line block in plan.md, and remove the `bind_root_module` call. Requirements: FR-001, FR-002, FR-003, FR-004, FR-005, FR-007. Files: `tests/unit/refactors/test_wlanradius_timer_manager_paths.py`. Acceptance: lines 44 to 50 match plan.md, and no other line changes. Verification: `python -m ruff check .` (Lint row) prints `All checks passed`. Quickstart Scenario 3 confirms the expected matches. Status: open.
- [ ] T002 Shift seven WLAN baseline `line_number` values by +4. The values are 351, 694, 729, 737, 807, 817, and 841, moving to 355, 698, 733, 741, 811, 821, and 845. Requirements: FR-006. Files: `.github/test-quality-baseline.json`. Acceptance: the JSON parses, and only those seven integers change. Verification: the Test quality command (Test quality row) prints `gate: 0 new findings vs baseline` (quickstart Scenario 6). Depends on T001. Status: open.

## Phase 2: Verification

- [ ] T003 [P] Run the three-node sequence on the fixed file. Requirements: FR-008, SC-001. Files: `tests/unit/refactors/test_wlanradius_timer_manager_paths.py`. Acceptance: no failed tests in the WLAN module and in the two named tests. Verification: `python -m pytest tests/<the changed file>` (Tests row) reports all tests passed. Quickstart Scenario 2 adds the two named tests. Depends on T001. Status: open.
- [ ] T004 Run the mutation proof. Remove the `patch.object` line in the working tree, run the three-node sequence, expect two failed tests, then restore the line. Requirements: FR-008, SC-004. Files: `tests/unit/refactors/test_wlanradius_timer_manager_paths.py`. Acceptance: `test_returns_misthelper_module` and `test_returns_false_when_args_absent` fail without the line. Verification: the Tests row command on the same file reports the expected failure (quickstart Scenario 4). Depends on T001. Status: open.
- [ ] T005 Run the root-units shard in sorted order. Requirements: FR-008, SC-002. Files: `tests` tree (no edit). Acceptance: the summary line reports no failed tests. Verification: the first pytest-chunks command (Full tests row, quickstart Scenario 7). Depends on T001 and T002. Status: open.
- [ ] T006 Run the second shard. Requirements: SC-002. Files: `tests` tree (no edit). Acceptance: the summary line reports no failed tests. Verification: the second pytest-chunks command (Full tests row, quickstart Scenario 7). Depends on T001 and T002. Status: open.

## Phase 3: Local Gates and Delivery

- [ ] T-LOCAL-GATES Commit the three intended paths locally. Then run each applicable gate. Requirements: FR-003, FR-009, FR-011. Files: the two modified files and the record folder. Acceptance: Lint, Format, Tests, Full tests, Test quality, and Symbols rows report their expected results. Skipped gates name their reasons in the pull request body (D-10). Verification: the Lint, Format, Tests, Full tests, Test quality, and Symbols rows of the local gates table (quickstart Scenarios 5 to 8). Depends on T003, T004, T005, and T006. Status: open.
- [ ] T-PR Push the branch `fix/4492-wlan-fixture-host-teardown` and open the pull request. Requirements: FR-010, FR-011. Files: explicit paths only. Acceptance: the title is `fix(tests): restore the resolver host after the WLAN fixture`. The body contains `Closes #4492`, the gate results, and the mutation proof output. Verification: the Test quality row command on the pushed commit prints `gate: 0 new findings vs baseline` (quickstart Scenario 6), then Scenario 9 reads the body. Depends on T-LOCAL-GATES. Status: open.
- [ ] T-REMOTE-CI Watch the pull request checks until each check reports a result. Requirements: FR-008, SC-002. Files: none. Acceptance: root-units, coverage gate, test quality gate, Ruff, Black, and the title check report success. Verification: the Full tests row, run on the pushed commit as the CI shard evidence (quickstart Scenario 7). Then Scenario 9 watches the checks. Depends on T-PR. Status: open.
- [ ] T-MERGE Add the `auto-merge` label only after every check reports success. Then wait for a human review that clears `needs-human-review`. Then squash-merge, verify the main run, and remove the branch. Requirements: FR-010. Files: none. Acceptance: the merge commit appears on `main`, and the main root-units shard reports success. Verification: the Full tests row, run on the main head after the merge (quickstart Scenario 9, last command for the main run). Depends on T-REMOTE-CI. Status: open.

## Dependencies and Execution Order

- T001 starts first. It has no prerequisite task.
- T002 depends on T001, because the line shift comes from T001.
- T003 and T004 depend on T001. They run one at a time, because T004 edits the file.
- T005 and T006 depend on T001 and T002.
- T-LOCAL-GATES depends on T003 through T006.
- T-PR, T-REMOTE-CI, and T-MERGE run in order after T-LOCAL-GATES.
