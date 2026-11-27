# Tasks: Restart healthy reset test repair

**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `design/research.md`, and `design/data-model.md`. No contracts folder exists, because this change adds no interface.

**Organization**: Tasks are grouped by user story. Final tasks close the phases.

## Format

`[ID] [P?] [Story] Description`

- **[P]**: No task carries this mark. Every open task edits the same test file or depends on an earlier task.
- **[Story]**: The user story that the task serves.
- Each task lists its requirement IDs, exact paths, an acceptance statement, one verification command from the local gates table, and its status.
- Status values: open, verified-present, partial, or absent.
- A checked box means the delivered file is verified. The evidence note names the delivered file.
- A box stays unchecked when a task needs a live system or a human decision. The task text names the condition.

## Phase 1: Setup and Phase 2: Foundational

No setup or shared infrastructure task is needed. The pinned environment appears in `design/quickstart.md`.

## Phase 3: User Story 1 - Stable restart results on a loaded machine (Priority: P1)

**Goal**: The restart class returns the same delays on every run.

**Independent Test**: Run the restart class ten times. All eight restart cases pass.

- [x] T001 [US1] Restart clock uses planned seconds (delivered: `tests/unit/container/output_defaults/test_session.py`)
  - Requirements: FR-001, FR-002
  - Paths: `tests/unit/container/output_defaults/test_session.py` (controlled clock at lines 237 to 263, execution at line 333, assertion at line 344)
  - Acceptance: The controlled clock sets each measured duration from the test plan. The assertion at line 344 compares the full tuple and the session output.
  - Verification: `python -m pytest tests/unit/container/output_defaults/test_session.py`
  - Status: verified-present. Remote blob `4c4bc48bd5071c438fd7d02a5cbb8caacb02a313` on main. Merge commit `02ffc4ac1ad65f5018a93b548fc65bc70a445d40` is in main.

- [x] T002 [US1] Threshold, stall, and exhaustion regressions (delivered: `tests/unit/container/output_defaults/test_session.py`)
  - Requirements: FR-003, FR-004
  - Paths: `tests/unit/container/output_defaults/test_session.py` (plan rows at lines 278 to 319, stall regression at lines 351 to 370, clock exhaustion at lines 372 to 380)
  - Acceptance: Five plan cases exist. The stall regression delays the fourth launch by two seconds. The exhaustion case expects exit code 97 after two launch entries.
  - Verification: `python -m pytest tests/unit/container/output_defaults/test_session.py::TestSessionRestarts`
  - Status: verified-present. Remote blob `4c4bc48bd5071c438fd7d02a5cbb8caacb02a313` on main.

- [x] T003 [US1] Session script and shared helper unchanged (delivered: `container/scripts/misthelper-session.sh`)
  - Requirements: FR-004, FR-007
  - Paths: `container/scripts/misthelper-session.sh` (defaults at lines 26, 32, 37, and 42), `tests/unit/container/output_defaults/session.py` (recorder sleep at line 67)
  - Acceptance: The session script blob equals the baseline blob. The shared helper differs from the baseline only in one import path and one comment. The default assertions at lines 384 to 388 of the test file match the script.
  - Verification: `python -m pytest tests/unit/container/output_defaults/test_session.py::TestSessionRestarts::test_original_restart_defaults_remain`
  - Status: verified-present. Session script blob `599d5753b35981e60085d0c4342dacf0e484ec3b` on main and at baseline. The shared helper behavior is unchanged.

- [x] T004 [US1] Main evidence after the merge (delivered: `tests/unit/container/output_defaults/test_session.py`)
  - Requirements: FR-001, FR-008
  - Paths: `tests/unit/container/output_defaults/test_session.py` (restart case lines 44821 to 44828 of CI run 45774119357 on main head `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`)
  - Acceptance: The log shows eight restart cases with status PASSED. The five plan cases and the three regression functions are included.
  - Verification: `python -m pytest tests/unit/container/output_defaults/test_session.py::TestSessionRestarts`
  - Status: verified-present

## Phase 4: User Story 2 - Compliant test changes (Priority: P1)

**Goal**: Each changed or added test function and the controlled clock meet Principles VI and VII.

**Independent Test**: Read the two functions and the fixture. Each action has a log line before and after it. Each bash line has a comment. The restart class passes.

- [ ] T005 [US2] Compliance repairs in the restart test
  - Requirements: FR-005, FR-006
  - Paths: `tests/unit/container/output_defaults/test_session.py` only
  - Acceptance: (1) `test_restart_controls_ignore_startup_stall` logs an info line before the source injection and before the delegated call. It logs a debug line after each. (2) `test_clock_exhaustion_refuses_unmeasured_launch` logs an info line before the session run and a debug line after it. (3) Each bash line in `CLOCK_SOURCE` carries a bash comment. (4) The opening line of `CLOCK_SOURCE` keeps no comment. (5) Before the first edit, the overlap check shows no other open pull request on this file.
  - Verification: `python -m pytest tests/unit/container/output_defaults/test_session.py`
  - Status: open

## Phase 5: User Story 3 - Traceable cause of the original failure (Priority: P2)

**Goal**: A reviewer finds the failing test, the assertion, the environment, and the cause status in one record.

**Independent Test**: Open `design/research.md`. The failing test ID, line 283, the assertion, the observed tuple, and the Unverified list are present.

No separate task exists for this story. Its evidence lives in `design/research.md`, and T-PR delivers it.

## Phase 6: User Story 4 - Verified merge on the exact head (Priority: P2)

**Goal**: The pull request head passes CI, and a human approves the merge.

**Independent Test**: Watch the head checks. Confirm eight passed restart cases in the root-units shard log. Confirm that auto-merge waits for approval.

Tasks T-REMOTE-CI and T-MERGE deliver this story. They appear in the final phase.

## Phase 7: Polish and Cross-Cutting Concerns

**Purpose**: Local gates, the pull request, the CI watch, and the merge. These tasks run after the user stories.

- [ ] T-LOCAL-GATES Local gates
  - Requirements: FR-005, FR-006, FR-007
  - Paths: `tests/unit/container/output_defaults/test_session.py` and each Markdown file in `specs/numbered/0/0/1/2/1/1/1/1/4531-restart-healthy-reset-delay/`
  - Acceptance: Each applicable gate reports its expected result. Applicable gates are compile, ruff, black, mypy, and the file tests. Also apply the two pytest-chunks shards, the test quality gate, complexity, security lint, symbols, and STE. Coverage runs in CI. Dependency audit, pylint, vulture, docstrings, the menu reference, and the safe sweep do not apply to this change. The pull request body states each reason.
  - Verification: `python -m pytest tests/unit/container/output_defaults/test_session.py`
  - Status: open

- [ ] T-PR Commit, push, and pull request
  - Requirements: FR-005, FR-006, FR-008
  - Paths: the modified test file `tests/unit/container/output_defaults/test_session.py` and the record folder `specs/numbered/0/0/1/2/1/1/1/1/4531-restart-healthy-reset-delay/`
  - Acceptance: The branch is `fix/4531-restart-healthy-reset-delay`, created from main. Each commit message uses Conventional Commits. The commit that edits the test file uses type `test` and scope `container`. The pull request title uses the same format. The pull request body contains `Closes #4531`, the local gate results, and the Principle IV scope note. The labels are `bug`, `tests`, and `in-progress`. Each item of `.github/PULL_REQUEST_TEMPLATE.md` is complete.
  - Verification: `python -m pytest tests/unit/container/output_defaults/test_session.py`
  - Status: open

- [ ] T-REMOTE-CI Watch CI on the exact head
  - Requirements: FR-008
  - Paths: `tests/unit/container/output_defaults/test_session.py` (restart case lines in the root-units shard log) and the checks of the pull request head
  - Acceptance: Run `gh pr checks --watch` from the branch worktree until the checks finish. Every required check passes on the head. CodeQL passes. The root-units shard log shows eight restart cases with status PASSED. Auto-merge stays disabled until T-MERGE.
  - Verification: `python -m pytest tests/unit/container/output_defaults/test_session.py::TestSessionRestarts`
  - Status: open

- [ ] T-MERGE Human review, merge, and build check
  - Requirements: FR-008
  - Paths: `.github/workflows/container-build.yml` (run list) and the pull request with its `needs-human-review` label. Leave this box unchecked until a human approves.
  - Acceptance: A human reviewer approves the pull request. The orchestrator authorizes the merge. Enable auto-merge only after the approval and a passing head. The squash title keeps the Conventional Commits form. Run `gh run list --workflow container-build.yml --branch main --limit 5` and confirm that no run exists for the merge commit. Caution: A commit pushed after the squash merge becomes orphaned. Open a new issue and branch from main in that case.
  - Verification: `python -m pytest tests/unit/container/output_defaults/test_session.py`
  - Status: open

## Dependencies and Execution Order

- T001 to T004 are verified. T005 depends on the verified baseline. T-LOCAL-GATES depends on T005. T-PR depends on T-LOCAL-GATES. T-REMOTE-CI depends on T-PR. T-MERGE depends on T-REMOTE-CI and on the human approval.
- No open task runs in parallel. Each open task edits the same test file or depends on an earlier task.

## Notes

- Tick a box only after the delivered file is verified. The evidence note names that file.
- Do not tick T-REMOTE-CI or T-MERGE until the remote condition holds.
