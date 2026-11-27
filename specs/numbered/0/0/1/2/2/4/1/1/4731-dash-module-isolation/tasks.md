# Tasks: Dash module isolation for map callback tests

**Input**: Numeric record at `specs/numbered/0/0/1/2/2/4/1/1/4731-dash-module-isolation/`.

**Available documents**: plan.md, spec.md, analysis.md, design/research.md, design/data-model.md, design/quickstart.md, and the three checklists under design/checklists/. The contracts folder does not apply (see plan.md).

**Prerequisites**: plan.md (required) and spec.md (required for the user stories).

**Organization**: Tasks are grouped by user story. User Story 1 keeps the real dash entry through collection. User Story 2 keeps the callback tests and their meaning. User Story 3 publishes each slice in serial order.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel. It edits a different file and has no open dependency.
- **[Story]**: The user story that the task serves.
- Each task names the requirements, the exact file paths, the acceptance statement, one verification command, and a status.
- Status values are open, verified-present, partial, or absent.

## Phase 1: Setup (Evidence)

### T001 Confirm the merged wave E1 file

- Requirements: FR-029, SC-008
- Files: `tests/maps/test_viewer_callbacks_wave_e1.py` (read only)
- Acceptance: Main holds blob `88f93f1d30c2690f69b57f5781bc0610e94c9c98` from merge commit `ef1434de`. The scoped helper stays at lines 47 to 63.
- Verification: `python -m pytest tests/maps/test_viewer_callbacks_wave_e1.py`
- Status: verified-present (research rows R14 to R16)

## Phase 2: Foundational

Not applicable. Each slice owns one file. The change adds no shared module, no conftest change, and no shared fixture (D-1, D-3).

## Phase 3: User Story 1 - Keep the real dash entry through collection (Priority: P1)

### T002 [P] [US1] Remove the wave A module-level stub install

- Requirements: FR-001, FR-006, FR-012, FR-015, FR-016
- Files: modify `tests/maps/test_viewer_callbacks_wave_a.py` at lines 40 to 44
- Acceptance: No module-level statement assigns `sys.modules['dash']`. The launcher import keeps `# noqa: E402`. No module-level name changes.
- Verification: `python -m pytest tests/maps/test_viewer_callbacks_wave_a.py`
- Status: open

### T003 [US1] Rewrite the wave A autouse fixture

- Requirements: FR-002, FR-003, FR-004, FR-005, FR-009, FR-013, FR-014, FR-015
- Files: modify `tests/maps/test_viewer_callbacks_wave_a.py` at lines 49 to 60, and recheck the line numbers after T002
- Acceptance: The fixture follows the target in plan.md. It yields the stub. It logs before and after each state change. It restores the exact prior entry in a `finally` block.
- Verification: `python -m pytest tests/maps/test_viewer_callbacks_wave_a.py`
- Status: open
- Depends on: T002

### T004 [P] [US1] Replace the wave B/C module install and fixture

- Requirements: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-012, FR-013, FR-014, FR-015, FR-016
- Files: modify `tests/maps/test_viewer_callbacks_wave_b_c.py` at line 48 and lines 53 to 68
- Acceptance: The statement at line 48 is removed. The fixture follows the target in plan.md. The fixture already yields the stub, so the signature does not change.
- Verification: `python -m pytest tests/maps/test_viewer_callbacks_wave_b_c.py`
- Status: open

### T005 [P] [US1] Replace the wave D module install and fixture

- Requirements: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-012, FR-013, FR-014, FR-015, FR-016
- Files: modify `tests/maps/test_viewer_callbacks_wave_d.py` at line 46 and lines 51 to 63
- Acceptance: The statement at line 46 is removed. The fixture follows the target in plan.md. The fixture already yields the stub, so the signature does not change.
- Verification: `python -m pytest tests/maps/test_viewer_callbacks_wave_d.py`
- Status: open

### T006 [P] [US1] Replace the wave E2 module install and fixture

- Requirements: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-012, FR-013, FR-014, FR-015, FR-016
- Files: modify `tests/maps/test_viewer_callbacks_wave_e2.py` at line 45 and lines 50 to 62
- Acceptance: The statement at line 45 is removed. The fixture follows the target in plan.md. The fixture already yields the stub, so the signature does not change.
- Verification: `python -m pytest tests/maps/test_viewer_callbacks_wave_e2.py`
- Status: open

## Phase 4: User Story 2 - Keep the callback tests and their meaning (Priority: P1)

### T007 [US2] Replace the two weak checks in wave A

- Requirements: FR-007, FR-008, FR-011, FR-015
- Files: modify `tests/maps/test_viewer_callbacks_wave_a.py` at line 134, at the test signature near line 169, and at line 181
- Acceptance: Line 134 checks that the bound value is a function or a bound method. Line 181 checks identity with `_dash_stub.html`. The test near line 169 takes the `_dash_stub` argument. Every changed line fits 120 characters.
- Verification: `python -m pytest tests/maps/test_viewer_callbacks_wave_a.py`
- Status: open
- Depends on: T003

### T008 [US2] Replace the two weak checks in wave E2

- Requirements: FR-010, FR-011, FR-015
- Files: modify `tests/maps/test_viewer_callbacks_wave_e2.py` at lines 171 to 181
- Acceptance: The test creates a named serializer and a named figure builder. It passes both into `_make_state`. It asserts identity for each one. The other assertions in the test stay.
- Verification: `python -m pytest tests/maps/test_viewer_callbacks_wave_e2.py`
- Status: open
- Depends on: T006

## Phase 5: User Story 3 - Publish each slice in serial order (Priority: P2), and final checks

### T-LOCAL-GATES Run the local gates for each slice

- Requirements: FR-012, FR-013, FR-015, FR-017, FR-018, FR-019, SC-005
- Files: the slice file in its slice worktree. Run the slices in the order S1, S2, S3, S4.
- Acceptance: Each slice passes QS-02, QS-03, QS-04, QS-08 to QS-12, and QS-14. Each result matches the expected text in design/quickstart.md. Run QS-01 on main before the slice change, and record the red-control result for the pull request body.
- Verification: `python -m ruff check .`
- Status: open
- Depends on: T002 and T003 and T007 for S1, T004 for S2, T005 for S3, and T006 and T008 for S4

### T-PR Commit, push, and open one pull request for each slice

- Requirements: FR-016, FR-017, FR-022, FR-023, FR-024, FR-025, FR-026, FR-027, FR-028, FR-029
- Files: the slice file, and one new changelog fragment in the `changelog.d` folder
- Acceptance: Publication starts only after the owner releases the hold (FR-023) and after the previous pull request merges (FR-025). Each branch starts from main and uses these names: `fix/4731-wave-a-dash-restore`, `fix/4731-wave-b-c-dash-restore`, `fix/4731-wave-d-dash-restore`, and `fix/4731-wave-e2-dash-restore`. The commit subject and the pull request title start with `fix(maps):`. The pull request carries the `bug` and `tests` labels. The body follows `.github/PULL_REQUEST_TEMPLATE.md` and lists the gate results and the red-control result. Slices S1 to S3 use `Refs #4731`. Slice S4 uses `Closes #4731`. Name the fragment `issue-4731-dash-module-isolation.md` before the pull request exists. Rename it to a file named `pr-` followed by the pull request number, in a second commit, after the number exists.
- Verification: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt`
- Status: open
- Depends on: T-LOCAL-GATES for the slice, and T-MERGE for the previous slice

### T-REMOTE-CI Watch the remote checks for each pull request

- Requirements: FR-023, FR-025, SC-005
- Files: none changed
- Acceptance: Every check in the pull request rollup reports SUCCESS. Auto-merge jobs report SKIPPED until the label is added. The checks include `Ruff (lint)`, `Black (format check)`, `pytest coverage shard (root-and-contracts)`, `Test quality ratchet (gate)`, and `Conventional Commits PR title`.
- Verification: `python -m pytest tests/maps`
- Status: open
- Depends on: T-PR for the same slice

### T-MERGE Authorize, label, and squash-merge each pull request in order

- Requirements: FR-025, FR-026, SC-006
- Files: none changed. Remove the branch and the worktree after the merge.
- Acceptance: The orchestrator authorizes the merge. The `auto-merge` label is added only after every check reports SUCCESS. The merge is a squash merge. The issue closes only when the slice S4 pull request merges.
- Verification: `python -m pytest tests/maps`
- Status: open
- Depends on: T-REMOTE-CI for the same slice

### T009 Confirm combined collection after the final slice merges

- Requirements: FR-020, FR-021, SC-003, SC-004
- Files: none changed. Run quickstart QS-05, QS-06, QS-07, and QS-13 on main.
- Acceptance: QS-05, QS-06, and QS-07 print True. QS-13 exits 0.
- Verification: `python -m pytest tests/maps`
- Status: open
- Depends on: T-MERGE for slice S4

## Dependencies and Execution Order

- T001 has no dependency.
- Wave A runs in this order: T002, then T003, then T007.
- T004, T005, and T006 have no dependency on each other or on wave A.
- T008 depends on T006.
- Publication runs in this order: T-LOCAL-GATES and T-PR for S1, then T-REMOTE-CI and T-MERGE for S1. After that, S2, then S3, then S4 follow the same pattern.
- T009 runs after the S4 merge.

## Notes

- Implementation of the four slices can run in parallel, because each slice owns one file. Publication stays serial (FR-024, FR-025).
- Create one worktree for each slice. Do not run `git checkout` in a checkout that another session uses.
- Caution: Publishing a slice before the owner releases the hold breaks the owner's instruction.
- Warning: Do not force-push a branch that another agent shares. Other agents lose the commits that they built on.
- Do not edit a held candidate commit. Do not rebase it, amend it, or push it (FR-027).
