# Tasks: Statistics Export Processed Count After Failed Fetch

**Input**: `plan.md`, `spec.md`, `design\research.md`, and `design\quickstart.md`.

## Format: `[ID] [P?] Title`

- `[P]`: The task can run in parallel. No other open task edits the same file.
- Requirements: The FR IDs and coordination constraints (C-1 to C-5) that the task satisfies.
- Status: `absent` means the deliverable is not on main. `open` means the procedural step has not started.

## Phase 1: Tests First

- [ ] T001 Create the focused test module with six tests
  - Requirements: FR-001, FR-002, FR-003, FR-004, FR-005, FR-008, FR-009
  - Files: ADD `tests\unit\prod_readiness\standalone\operations\exporting\stats\test_stats_export_completion.py`
  - Depends on: none
  - Acceptance: The module contains the six tests named in `plan.md`. Tests 1 to 5 fail before T002. Test 6 passes before T002. No test writes under `data\`.
  - Verify: `python -m pytest tests/unit/prod_readiness/standalone/operations/exporting/stats/test_stats_export_completion.py`
  - Status: absent

- [ ] T004 [P] Add the release-note fragment
  - Requirements: FR-011
  - Files: ADD `changelog.d\issue-4746-stats-export-failed-fetch.md`
  - Depends on: none
  - Acceptance: The fragment has one `###` heading and one `Fixed` bullet. The bullet ends with "Issue #4746." The guard test passes.
  - Verify: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
  - Status: absent

## Phase 2: Repair

- [ ] T002 Repair the processed count in both statistics exports
  - Requirements: FR-001 to FR-008, C-1, C-4
  - Files: MODIFY `src\operations\exporting\export\org_device_stats_exporter.py` (lines 96 to 112 for `device_stats` and lines 486 to 501 for `vpn_peer_stats`)
  - Depends on: T001
  - Acceptance: All six tests pass. Each touched line has an inline comment. Each touched function logs a debug line after the fetch. The progress labels, operation names, and totals are unchanged. The change adds no method and no module-level name.
  - Verify: `python -m pytest tests/unit/prod_readiness/standalone/operations/exporting/stats/test_stats_export_completion.py`
  - Status: absent

- [ ] T003 Update the menu 13 completion test stub
  - Requirements: FR-010
  - Files: MODIFY `tests\unit\prod_readiness\standalone\operations\exporting\inventory\test_menu_13_device_stats.py` (the `MockFetcher.execute` method at line 146)
  - Depends on: T002. Both tasks land in the same commit.
  - Acceptance: `execute` returns True. `test_emits_start_and_complete` passes with processed count 1.
  - Verify: `python -m pytest tests/unit/prod_readiness/standalone/operations/exporting/inventory/test_menu_13_device_stats.py`
  - Status: absent

- [ ] T005 Confirm that module-level names are unchanged
  - Requirements: FR-006, SC-004
  - Files: VERIFY `src\operations\exporting\export\org_device_stats_exporter.py`
  - Depends on: T002
  - Acceptance: The symbol check reports "no module-level name changed" and exit code 0.
  - Verify: `symbol-diff --base origin/main src\operations\exporting\export\org_device_stats_exporter.py`
  - Status: open

## Phase 3: Gates and Publication

- [ ] T-LOCAL-GATES Run every applicable local gate
  - Requirements: SC-005, C-5
  - Files: Every changed file in the Source Code table of `plan.md`
  - Depends on: T003, T004, T005
  - Acceptance: Each applicable row in `design\quickstart.md`, section "Local Gates", reports its expected result. Each row marked not applicable names its reason. The results appear in the pull request body.
  - Verify: `python -m ruff check .`
  - Status: open

- [ ] T-PR Commit, push, and open the pull request
  - Requirements: C-2, C-3, FR-011
  - Files: Branch `fix/4746-stats-export-failed-fetch`, the Source Code table of `plan.md`, and the folder `specs\numbered\0\0\1\2\2\4\4\1\4746-stats-export-failed-fetch`
  - Depends on: T-LOCAL-GATES. The coordination checklist in `design\checklists\coordination.md` must show every item checked.
  - Acceptance: The commit subject is `fix(export): report zero processed items after a failed stats fetch`. The body contains `Closes #4746`. The pull request body lists the gate results and the changed files. The fragment name stays `issue-4746-stats-export-failed-fetch.md` after the pull request opens.
  - Verify: `python -m pytest tests/unit/prod_readiness/standalone/operations/exporting/stats/test_stats_export_completion.py`
  - Status: open

- [ ] T-REMOTE-CI Watch the remote checks
  - Requirements: SC-005
  - Files: `.github/workflows/ci.yml`
  - Depends on: T-PR
  - Acceptance: Every required check reports success on the latest commit. No check is skipped without a stated cause. The branch stays current with `main` before the merge.
  - Verify: `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal`
  - Status: open

- [ ] T-MERGE Enable auto-merge after the orchestrator authorizes the merge
  - Requirements: C-3, Principle IV
  - Files: `.github/workflows/container-build.yml` (watched, not changed)
  - Depends on: T-REMOTE-CI and the orchestrator authorization
  - Acceptance: The `auto-merge` label is added only after every check reports success. The container build for the merged revision succeeds, and its image revision label equals the merged commit SHA. The branch and its worktree are removed after the squash merge.
  - Verify: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json`
  - Status: open

## Dependencies and Execution Order

- T001 starts first. T004 can start at the same time, because it has no dependency.
- T002 requires T001. T003 and T005 require T002. T002 and T003 land in one commit.
- T-LOCAL-GATES requires T003, T004, and T005.
- T-PR requires T-LOCAL-GATES and the coordination checklist.
- T-REMOTE-CI requires T-PR. T-MERGE requires T-REMOTE-CI and the orchestrator authorization.

## Notes

- Every task names exact repository paths and one verification command from the local gates table in `.github/copilot-instructions.md`.
- Caution: Do not push while a remote check run is in flight, unless the new commit replaces the previous commit on purpose. The older run wastes runner minutes.
