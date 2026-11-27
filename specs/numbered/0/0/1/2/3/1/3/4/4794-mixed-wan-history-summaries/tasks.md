# Tasks: Mixed WAN History Summaries

**Input**: Numeric record at `specs/numbered/0/0/1/2/3/1/3/4/4794-mixed-wan-history-summaries/`. Read `plan.md`, `spec.md`, and `design/research.md` first.

**Prerequisites**: plan.md (required), spec.md (required), design/research.md, design/data-model.md, design/quickstart.md, design/contracts/.

## Format

- `[P]` marks a task that can run in parallel with other `[P]` tasks. It touches different files.
- Each task lists requirement IDs, exact repository paths, an acceptance statement, one verification command, and a status.
- Status values are `open`, `verified-present`, `partial`, and `absent`.
- Each verification command comes from the local gates table in `.github/copilot-instructions.md` (lines 57 to 74). Named commands in that file also qualify (remote checks 91 to 93).
- Run each verification command in the worktree that holds the candidate branch. Use the parent worktree only for T002, as design/quickstart.md describes.

## Phase 1: Verify the Candidate

- [ ] **T001** `verified-present` [FR-010, FR-012]. Confirm that the candidate head holds repair commit d7a706d.
  - Paths: `src/interfaces/wan_performance/domain/summary.py`.
  - Acceptance: Head `843be63` contains `d7a706d` as an ancestor (remote check 44). Line 354 holds the presence check (remote check 52). Line 337 keeps each total unknown when no known or complete hour exists (remote check 53).
  - Verification: `symbol-diff --base 07b7751fb9e6c0e8d285d2adb9b0273bc5aae4fc src/interfaces/wan_performance/domain/summary.py`. Expected: `no module-level name changed`, exit code 0.

- [ ] **T002** `open` [P] [FR-010, SC-002]. Reproduce the defect on parent commit 07b7751.
  - Paths: `tests/unit/wan_performance/test_calendar_summaries.py` in the parent worktree only. Copy the file from head with the quickstart steps.
  - Acceptance: The mixed-hour test raises `KeyError: 'flap_count'` (remote checks 48 and 49). The missing-evidence test reports zero flaps and zero minutes. The known-zero test reports zero minutes.
  - Verification: `python -m pytest tests/unit/wan_performance/test_calendar_summaries.py -q` (Tests row, line 61).

## Phase 2: Repair the Code and Tests

- [ ] **T003** `partial` [P] [FR-002, FR-003, FR-006, FR-011]. Add inline comments and action logging to the link-event code.
  - Paths: `src/interfaces/wan_performance/domain/summary.py` at lines 44 to 49 (fields), 330 to 341 (`build`), and 344 to 354 (`_has_events` and `_complete`).
  - Acceptance: Each changed or touched executable line has a same-line comment that gives the purpose. `build` writes an info line before the period build and a debug line after it, with the complete and known hour counts. Log text is ASCII only.
  - Verification: `python -m ruff check .` (Lint row, line 58). Expected: `All checks passed`.

- [ ] **T004** `partial` [FR-001, FR-002, FR-004, FR-008, FR-010]. Extend the mixed-hour test to all six summaries.
  - Paths: `tests/unit/wan_performance/test_calendar_summaries.py` at lines 222 to 249.
  - Acceptance: The build returns six summaries (remote check 57 for the rolling windows). Each summary with a link-event summary reports `complete_hours` 1, `known_hours` 1, `up_minutes` 60, `down_minutes` 0, `flap_count` 0, and `observed_up_percent` 100. `expected_hours` equals `summary.period.expected_hours` (remote check 58).
  - Verification: `python -m pytest tests/unit/wan_performance/test_calendar_summaries.py -q` (Tests row, line 61).

- [ ] **T005** `absent` [FR-005, FR-010]. Add the snapshot-only test after line 284.
  - Paths: `tests/unit/wan_performance/test_calendar_summaries.py`. Name the new function `test_snapshot_only_hours_leave_event_summary_absent`.
  - Acceptance: Snapshot hours alone produce summaries whose `link_event_summary` is `None`. The test fails if `_has_events` returns true for a snapshot hour (remote check 54).
  - Verification: `python -m pytest tests/unit/wan_performance/test_calendar_summaries.py -q` (Tests row, line 61).

- [ ] **T006** `partial` [P] [FR-011, FR-010]. Add inline comments to the regression tests.
  - Paths: `tests/unit/wan_performance/test_calendar_summaries.py` at lines 222 to 284 and the new test from T005.
  - Acceptance: Each executable line in those functions has a same-line comment. The comments state the purpose of each assertion.
  - Verification: `python -m ruff check .` (Lint row, line 58). Expected: `All checks passed`.

- [ ] **T007** `verified-present` [FR-009, FR-010]. Verify the portal Unknown test and its template guards.
  - Paths: `tests/e2e/web_portal/test_wan_performance_live.py` at line 2295. `src/interfaces/wan_performance/presentation/templates/wan_performance/live.html` at lines 404 to 419.
  - Acceptance: The e2e test passes. The template guards at lines 409 and 417 match FR-009 (remote checks 65, 68, and 69).
  - Verification: `python -m pytest tests/e2e/web_portal/test_wan_performance_live.py -k renders_missing_evidence_as_unknown -q` (Tests row, line 61).

## Phase 3: Documentation and Record

- [ ] **T008** `verified-present` [FR-005, FR-006, FR-007]. Verify the documented event rules.
  - Paths: `documentation/wan-performance.md` at lines 340 and 341. `changelog.d/pr-4208.md` at line 19.
  - Acceptance: Line 340 states that snapshot hours stay out of event summaries. Line 341 states that unknown stays unknown and a known zero remains zero. The changelog names issue 4794. No file changes in this task (remote checks 76, 77, and 79).
  - Verification: `python -m pytest tests/unit/wan_performance/test_calendar_summaries.py -q` (Tests row, line 61). The tests confirm the behavior that the lines describe.

- [ ] **T009** `partial` [P] [FR-012]. Add this record to the candidate branch as one docs commit.
  - Paths: `specs/numbered/0/0/1/2/3/1/3/4/4794-mixed-wan-history-summaries/` and every file in it.
  - Acceptance: The folder holds `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design/` with the child limits of five. Each Markdown file scores 80 or more.
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80 <each Markdown file in the record>` (STE row, line 74, remote check 5).

## Phase 4: Delivery

- [ ] **T-LOCAL-GATES** `open` [FR-001 to FR-011, SC-003]. Run every applicable gate from the local gates table on the changed files.
  - Paths: `src/interfaces/wan_performance/domain/summary.py`, `tests/unit/wan_performance/test_calendar_summaries.py`, and the Markdown files in the record.
  - Acceptance: Each applicable row reports its expected result. The gate map in `design/quickstart.md` lists each row as applicable or not applicable, with the cause. The coverage row reports 80 percent or more (line 64).
  - Verification: `python -m pytest tests/unit/wan_performance/test_calendar_summaries.py -q` (Tests row, line 61). The other applicable rows follow in the order of `design/quickstart.md`.

- [ ] **T-PR** `partial` [FR-012]. Rebase the candidate onto `origin/main`, push, and update the PR body.
  - Paths: branch `jmorrison-juniper-4200-migrate-mistwanperformance`. `.github/PULL_REQUEST_TEMPLATE.md` (remote check 31) for the body fields.
  - Acceptance: The rebase stops with a report if conflicts exceed 20 lines (decision D-9, remote check 3). The push uses `--force-with-lease` after authorization (remote check 95). The PR body contains `Closes #4794` (remote check 94) and keeps `Refs #4200` without a closing keyword. The body lists local gate results.
  - Verification: `python -m pytest tests/unit/wan_performance/test_calendar_summaries.py -q` (Tests row, line 61) after the rebase.

- [ ] **T-REMOTE-CI** `open` [FR-012, SC-004]. Watch the CI run for the pushed head.
  - Paths: `.github/workflows/ci.yml`. Its variables at lines 93, 101, 104, and 107 name the paths for four gates (remote checks 26 to 29).
  - Acceptance: `gh pr checks 4208 -R jmorrison-juniper/MistHelper --watch` reports no failed required check. CodeQL reports a pass.
  - Verification: `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal` (remote check 93, the first Full tests command).

- [ ] **T-MERGE** `open` [FR-012, SC-005]. Add the `auto-merge` label and squash merge after the gates pass and authorization exists.
  - Paths: `.github/workflows/auto-merge.yml` (remote check 32).
  - Acceptance: The label is added only after CI passes and the orchestrator authorizes the merge. Decision D-5 is resolved. After the merge, a remote read of `main` shows `summary.py` with the None-safe event code.
  - Verification: `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=` (Coverage row, line 64).

## Dependencies and Execution Order

- T001 has no prerequisite.
- T002 depends on T001.
- T003 depends on T001 and runs in parallel with T004 because the files differ.
- T004 depends on T002. T005 depends on T004 because both edit one file. T006 depends on T005 for the same reason.
- T007 and T008 have no prerequisite.
- T009 depends on T003, T004, T005, T006, and T008, because the record cites their results.
- T-LOCAL-GATES depends on T003, T004, T005, T006, T007, and T009.
- T-PR depends on T-LOCAL-GATES.
- T-REMOTE-CI depends on T-PR.
- T-MERGE depends on T-REMOTE-CI and on decision D-5.
