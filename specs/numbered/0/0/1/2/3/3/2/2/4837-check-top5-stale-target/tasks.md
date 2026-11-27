# Tasks: Top-Five Complexity Target Map

**Input**: Numeric record `specs/numbered/0/0/1/2/3/3/2/2/4837-check-top5-stale-target/`.

**Prerequisites**: `plan.md`, `spec.md`, `design/research.md`, `design/quickstart.md`, and `design/contracts/top5-cli.md`.

**Tests**: The constitution and AGENTS.md require tests. Write each guard test before the map change, and see it fail first.

**Status values**: `open`, `verified-present`, `partial`, or `absent`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel with other tasks of its phase, because it edits a different file.
- **[Story]**: The user story that the task serves.
- Each task lists its requirements, exact paths, acceptance statement, verification command, and status.

## Phase 1: Verification

- [X] T001 [P] [US1] Verify the five target locations on main.
  - Requirements: FR-001.
  - Files: none. The task reads GitHub only and runs no local gate.
  - Acceptance: research.md rows R01 to R13 record each location, including the stale map entry in R01.
  - Verification: `gh api repos/jmorrison-juniper/MistHelper/contents/MistHelper.py?ref=main --jq .sha` returns `98d7828479ded6bc4c83d15e0c1847171cfbfd49`.
  - Status: verified-present.

## Phase 2: Guard Tests and Map Fix

- [ ] T002 [US2] Add three guard tests before the map change.
  - Requirements: FR-001, FR-002, FR-003, FR-004.
  - Files: `tests/integration/test_top5_compatibility_paths.py`.
  - Acceptance: three new test functions with docstrings. The mapping test fails on the current map and names the missing targets and files.
  - Verification: `.venv\Scripts\python.exe -m pytest tests\integration\test_top5_compatibility_paths.py -q` (local gate: Tests).
  - Status: open.

- [ ] T003 [US1] Replace the target map with the current file of each target. Depends on T002.
  - Requirements: FR-001.
  - Files: `scripts/check_top5_complexity.py` (lines 14 to 22).
  - Acceptance: four keys built with `pathlib.Path`. Each line of the block has an inline comment. The five target names and module-level names stay unchanged.
  - Verification: `.venv\Scripts\python.exe -m pytest tests\integration\test_top5_compatibility_paths.py -q` (local gate: Tests) passes. The symbol check runs in T-LOCAL-GATES.
  - Status: open.

- [ ] T004 [US1] Run the utility from the repository root. Depends on T003.
  - Requirements: FR-002, FR-003, SC-001.
  - Files: `scripts/check_top5_complexity.py` (read only).
  - Acceptance: five result rows, one PASS or FAIL line, and exit code 0 for PASS. Record the printed output and the run time. The run uses quickstart scenario 3.
  - Verification: `.venv\Scripts\python.exe -m pytest tests\integration\test_top5_compatibility_paths.py -q` (local gate: Tests) passes. The utility output is recorded beside it.
  - Status: open.

## Phase 3: Delivery Artifacts

- [ ] T005 [P] [US1] Add the changelog fragment.
  - Requirements: D-8 and D-9.
  - Files: `changelog.d/issue-4837-check-top5-stale-target.md`.
  - Acceptance: one `###` heading and one `Fixed` bullet that names issue #4837. The file name stays after the pull request opens.
  - Verification: none in the local gates table applies to a changelog fragment. Read the file and confirm the heading and bullet.
  - Status: open.

- [ ] T006 [P] [US2] Copy the draft folder into the record path.
  - Requirements: the spec record in plan.md.
  - Files: `specs/numbered/0/0/1/2/3/3/2/2/4837-check-top5-stale-target/`.
  - Acceptance: the record holds `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design/`. Each folder holds five children or fewer.
  - Verification: none in the local gates table applies to a record copy. Compare the record folder with the draft folder by file name and size.
  - Status: open.

## Phase 4: Gates and Delivery

- [ ] T-LOCAL-GATES Run every local gate that applies to the changed files. Depends on T003, T005, and T006.
  - Requirements: FR-001 to FR-004 and SC-001 to SC-004.
  - Files: the four changed paths.
  - Acceptance: each gate output is recorded. A gate that fails on existing debt is recorded with its cause and not changed.
  - Verification: the commands in `design/quickstart.md`, scenarios 4 to 9.
  - Status: open.

- [ ] T-PR Commit, push, and open the pull request. Depends on T-LOCAL-GATES.
  - Requirements: the git flow in AGENTS.md and the Conventional Commit rule.
  - Files: the four changed paths.
  - Acceptance: commit subject `fix(tests): map top-five complexity targets to current files`. The branch is `fix/4837-check-top5-stale-target`. The pull request body contains `Closes #4837`, the local gate results, and the reason for D-10.
  - Verification: `gh pr view fix/4837-check-top5-stale-target --json title,body,headRefName`.
  - Status: open.

- [ ] T-REMOTE-CI Watch the remote checks. Depends on T-PR.
  - Requirements: SC-003 and the required checks of the pull request.
  - Files: none.
  - Acceptance: each required check is green. The integration test shard runs the three guard tests.
  - Verification: `gh pr checks fix/4837-check-top5-stale-target --watch`.
  - Status: open.

- [ ] T-MERGE Add the `auto-merge` label and squash merge. Depends on T-REMOTE-CI and orchestrator authorization.
  - Requirements: D-10 and the merge rules in AGENTS.md.
  - Files: none.
  - Acceptance: one squash commit on main. The branch and the worktree are removed. Principle IV steps 10 to 12 are recorded as not triggered.
  - Verification: `gh pr view fix/4837-check-top5-stale-target --json state,mergedAt`.
  - Status: open.

## Dependencies and Execution Order

- T002 comes before T003. T003 comes before T004.
- T005 and T006 run in parallel with each other. Both come before T-LOCAL-GATES.
- T-LOCAL-GATES comes before T-PR. T-PR comes before T-REMOTE-CI. T-REMOTE-CI comes before T-MERGE.
