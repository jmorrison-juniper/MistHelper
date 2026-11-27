# Tasks: Count export write results

**Input**: Design documents in `specs/numbered/0/0/1/2/2/3/4/0/4720-count-export-writer-results/`

**Prerequisites**: `plan.md`, `spec.md`, `design/research.md`, `design/data-model.md`, `design/contracts/`, and `design/quickstart.md`

**Tests**: Write T001 before T002. On unchanged source, seven of the twelve new cases fail.

**Ownership**: Edit only the paths in `plan.md`. Do not edit `README.md`, `MistHelper.py`, or any other file under `tests/unit/export/`.

**Environment**: Create the worktree and bootstrap it as `design/quickstart.md` describes. Run each command from the worktree root.

**Status values**: `open`, `verified-present`, `partial`, or `absent`. `absent` means the deliverable is missing on `main` now.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel with other [P] tasks, because it edits a different file.
- **[Story]**: The user story that the task serves.

## Phase 1: Regression tests

- [ ] T001 [US1] Add class `TestCountWriteOutcomes` to `tests/unit/export/test_count_exporter_workflows.py`.
  - Requirements: FR-008, FR-011, FR-012, FR-013, FR-014, SC-001.
  - Acceptance: twelve cases exist. Nine cover org, site, and MSP with `False`, `None`, and `True`. One covers an empty response. One covers a raised writer error. One checks the info line before the success notice. Seven fail on unchanged source.
  - Verification: `python -m pytest tests/unit/export/test_count_exporter_workflows.py -k CountWriteOutcomes -q`
  - Status: absent

## Phase 2: Fix

- [ ] T002 [US1] Change `_persist` in `src/operations/exporting/export/count_exporter.py` (defined at line 199 on `main`).
  - Requirements: FR-001 to FR-011, FR-015.
  - Acceptance: the writer result is stored and judged by truth value. A false result logs the error, prints the failure notice, and returns. The success notice follows that branch only. The info line precedes the writer call, and the debug line follows it. Each changed line has an inline comment.
  - Verification: `python -m pytest tests/unit/export/test_count_exporter_workflows.py -k CountWriteOutcomes -q`
  - Status: absent
- [ ] T003 [US1] Confirm the existing count tests and the contract guard pass with the fix, without editing them.
  - Requirements: FR-010, SC-002, SC-003.
  - Acceptance: both files pass. The existing persist test still sees the operation name at the writer call.
  - Verification: `python -m pytest tests/unit/export/test_count_exporter.py tests/contract/test_export_api_function_names.py -q`
  - Status: open

## Phase 3: Documentation and release note

- [ ] T004 [P] [US2] Add one paragraph after line 120 of `documentation/operator-guide.md`.
  - Requirements: FR-016.
  - Acceptance: the paragraph names menus 235 to 237. It states that a failed output write does not claim success. Its form matches the paragraph on line 120.
  - Verification: `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 documentation/operator-guide.md`
  - Status: absent
- [ ] T005 [P] [US2] Add `changelog.d/issue-4720-count-export-writer-results.md`.
  - Requirements: FR-017.
  - Acceptance: one `###` heading and one `Fixed` bullet that names issue #4720. The form matches `changelog.d/issue-4717-site-export-writer-results.md`.
  - Verification: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q`
  - Status: absent

## Phase 4: Gates on the changed files

- [ ] T006 Run the symbol gate on `src/operations/exporting/export/count_exporter.py`.
  - Requirements: FR-015.
  - Acceptance: the gate prints `no module-level name changed` and exits with code 0.
  - Verification: `symbol-diff --base origin/main src/operations/exporting/export/count_exporter.py`
  - Status: open
- [ ] T007 Run the test-quality ratchet on `tests/unit/export/test_count_exporter_workflows.py` after the local commit.
  - Requirements: FR-021.
  - Acceptance: the preflight passes. The gate prints `gate: 0 new findings vs baseline`.
  - Verification: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt`
  - Status: open

## Phase 5: Release gates and publication

- [ ] T-LOCAL-GATES Run each applicable local gate, and commit explicit paths.
  - Requirements: FR-018, FR-021.
  - Paths: the five paths in `plan.md`. Do not stage `README.md` or `MistHelper.py`.
  - Acceptance: each applicable row of the local gates table prints its expected result, as `design/quickstart.md` Scenario 8 lists. The commit subject is `fix(export): report failed count writes`.
  - Verification: `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=`
  - Status: open
- [ ] T-PR Rebase, push, and open the pull request. Do not open it until the owner lifts the publication hold.
  - Requirements: FR-018, FR-019, FR-020, FR-022.
  - Paths: branch `fix/4720-count-export-writer-results` and the record folder `specs\numbered\0\0\1\2\2\3\4\0\4720-count-export-writer-results`.
  - Acceptance: the title is `fix(export): report failed count writes`. The body holds `Closes #4720` and the local gate results. The route check in `design/quickstart.md` Scenario 9 prints the record path.
  - Verification: `gh pr view <number> -R jmorrison-juniper/MistHelper --json title,body,state`
  - Status: open (held)
- [ ] T-REMOTE-CI Watch the 15 required contexts on the pull request head commit.
  - Requirements: SC-005, FR-022.
  - Paths: the five paths in `plan.md`, on branch `fix/4720-count-export-writer-results`.
  - Acceptance: all 15 required contexts succeed. The context names are listed in `design/research.md`, Sources.
  - Verification: `gh pr checks <number> -R jmorrison-juniper/MistHelper --watch`
  - Status: open (held)
- [ ] T-MERGE Add the `auto-merge` label after the checks pass and the orchestrator authorizes the merge.
  - Requirements: FR-023.
  - Paths: the five paths in `plan.md`, on branch `fix/4720-count-export-writer-results`.
  - Acceptance: one squash commit lands on `main`. The `container-build.yml` run on that commit shows the same revision label. Issue #4720 is CLOSED.
  - Verification: `gh pr view <number> -R jmorrison-juniper/MistHelper --json state,mergedAt,mergeCommit`
  - Status: open (held)

Warning: do not push to the branch after the squash merge. The new commit never reaches `main`. File a new issue, then branch again from `main`.

## Dependencies & Execution Order

- T001 comes first. T002 depends on T001.
- T003 depends on T002.
- T004 and T005 can run in parallel with T001 to T003, because they edit different files.
- T006 and T007 depend on T002. T007 also depends on the local commit in T-LOCAL-GATES.
- T-LOCAL-GATES depends on T001 to T007.
- T-PR depends on T-LOCAL-GATES and on the owner lifting the hold.
- T-REMOTE-CI depends on T-PR.
- T-MERGE depends on T-REMOTE-CI and on orchestrator authorization.

## Notes

- Each task names one verification command. T-PR, T-REMOTE-CI, and T-MERGE name remote commands, because the local gates table has no remote row (decision D-13).
- A task with status `open (held)` stays unexecuted while the publication hold stands.
