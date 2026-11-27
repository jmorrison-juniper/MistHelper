# Tasks: Pin the verified auto-merge commit

**Input**: Numeric record in `specs/numbered/0/0/1/2/4/1/1/1/4906-auto-merge-verified-pin/`.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, `design/quickstart.md`, `design/checklists/requirements.md`.

**Tests**: The guard file is the test. It exists and runs in CI. No new test case is added (decision D-4).

**Format**: `- [ ] ID [P?] [Story?] Description`. The box stays unchecked until a task is delivered. Each task lists its requirements, its files, its acceptance statement, one verification command from the local gates table, and its status. Status values are open, verified-present, partial, or absent.

## Phase 1: Reproduce the failure

- [ ] T001 [US1] Confirm the failure on the pull request head and on main.
  - Requirements: FR-001, FR-004
  - Files: `.github/workflows/auto-merge.yml` (line 61), `tests/guardrails/test_auto_merge_issue_close.py` (lines 46 and 145)
  - Acceptance: The pull request head pins `2239e7bd468fd27e40c43f2b87fcd35a2e49672b`. Main names `d63a120487cecf750184cb178387cdc25c0a7635` at both lines.
  - Verification: `python -m pytest tests/guardrails/test_auto_merge_issue_close.py` on the pull request head expects 1 failed and 16 passed.
  - Status: verified-present. Rows R-01 to R-04 in `design/research.md` and the failed run in `design/quickstart.md` confirm it.

## Phase 2: Apply the verified commit

- [ ] T002 [P] [US1] Pin the auto-merge job to the reviewed commit.
  - Requirements: FR-001, FR-003
  - Files: `.github/workflows/auto-merge.yml` (modify line 61)
  - Acceptance: Line 61 names `reusable-auto-merge.yml@2239e7bd468fd27e40c43f2b87fcd35a2e49672b`. The line keeps the comment `# Verified post-merge dispatch`.
  - Verification: `python -m pytest tests/guardrails/test_auto_merge_issue_close.py`
  - Status: open

- [ ] T003 [P] [US1] Move the verified commit constant with the pin.
  - Requirements: FR-002, FR-003, FR-004
  - Files: `tests/guardrails/test_auto_merge_issue_close.py` (modify lines 44 to 46)
  - Acceptance: Line 46 holds the same literal commit as T002. Two comment lines above it state the blob evidence. One inline comment on line 46 reads `# Verified: same blob as d63a120`. Each line stays 120 columns or fewer.
  - Verification: `python -m pytest tests/guardrails/test_auto_merge_issue_close.py`
  - Status: open

- [ ] T004 [US1] Run the targeted guard checks after T002 and T003.
  - Requirements: FR-001, FR-002, FR-005
  - Files: `tests/guardrails/test_auto_merge_issue_close.py`
  - Acceptance: All 17 tests pass. The test-quality analyzer command in `design/quickstart.md` reports zero new findings.
  - Verification: `python -m pytest tests/guardrails/test_auto_merge_issue_close.py`
  - Status: open. Depends on T002 and T003.

## Phase 3: Place the spec record

- [ ] T005 [P] Place this spec record under the numbered route.
  - Requirements: FR-007
  - Files: `specs/numbered/0/0/1/2/4/1/1/1/4906-auto-merge-verified-pin/` (add `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, `design/research.md`, `design/data-model.md`, `design/quickstart.md`, `design/checklists/requirements.md`, `design/checklists/security.md`)
  - Acceptance: The folder sits at the route. Each level holds five children or fewer. The folder holds one `spec.md`, and no other `spec.md` sits below it.
  - Verification: `python -m pytest tests/guardrails/test_process_folder_structure.py`
  - Status: open

## Final tasks

- [ ] T-LOCAL-GATES Run every local gate that applies to the changed files.
  - Requirements: FR-005, FR-006
  - Files: `.github/workflows/auto-merge.yml`, `tests/guardrails/test_auto_merge_issue_close.py`, and the record folder under `specs/numbered/0/0/1/2/4/1/1/1/`
  - Acceptance: Each command in `design/quickstart.md` reports its expected result. A repository search finds `d63a120487cecf750184cb178387cdc25c0a7635` only in this record folder.
  - Verification: `python -m ruff check .` reports `All checks passed`.
  - Status: open. Depends on T002, T003, T004, and T005.

- [ ] T-PR Commit, push, and open the replacement pull request.
  - Requirements: FR-006
  - Files: the three paths in the change map of `plan.md`
  - Acceptance: The branch `fix/4906-auto-merge-verified-pin` starts from rebased main. The commit title uses Conventional Commits, for example `fix(ci): pin the verified auto-merge commit`. The body names `Closes #4906`, the reason for no changelog fragment, the local gate results, and the superseded pull request 4886.
  - Verification: `python -m pytest tests/guardrails/test_auto_merge_issue_close.py`
  - Status: open. Depends on T-LOCAL-GATES.

- [ ] T-REMOTE-CI Watch the CI run on the replacement pull request.
  - Requirements: FR-001, FR-004
  - Files: none
  - Acceptance: Every required check passes, including `pytest (coverage gate)` and `pytest coverage shard (root-and-contracts)`. Run `gh pr checks -R jmorrison-juniper/MistHelper --watch` from the fix branch. Stop and report each failed check that the guard does not cause.
  - Verification: `python -m pytest tests/guardrails/test_auto_merge_issue_close.py` passes locally before the watch starts.
  - Status: open. Depends on T-PR.

- [ ] T-MERGE Enable auto-merge after the orchestrator authorizes it, then close pull request 4886.
  - Requirements: FR-001, FR-002
  - Files: none
  - Acceptance: T-REMOTE-CI passed, and the orchestrator authorized the merge. The `auto-merge` label is added only after every check passes. The replacement merges as one squash commit. Main names `2239e7bd468fd27e40c43f2b87fcd35a2e49672b` at both lines. Pull request 4886 closes with a comment that names the replacement and the files examined on main. The fix branch and its worktree are removed.
  - Verification: `python -m pytest tests/guardrails/test_auto_merge_issue_close.py` on a fresh checkout of main expects 17 passed.
  - Status: open. Depends on T-REMOTE-CI.

Warning: merging to main changes the pin for every later run of the auto-merge job. Merge only after T-REMOTE-CI passes.

Caution: closing pull request 4886 early removes the open update from the queue. Close it only after the replacement merges.

## Dependencies & Execution Order

- T001 comes first. It reads the reproduction only.
- T002 and T003 run in parallel, because they edit different files. Both must land in one commit.
- T004 runs after T002 and T003.
- T005 runs in parallel with T002 and T003.
- T-LOCAL-GATES runs after T002, T003, T004, and T005.
- T-PR, T-REMOTE-CI, and T-MERGE run in that order.

## Notes

- Every requirement appears in at least one task: FR-001 in T001, T002, T004, T-REMOTE-CI, and T-MERGE. FR-002 in T003, T004, and T-MERGE. FR-003 in T002 and T003. FR-004 in T001, T003, and T-REMOTE-CI. FR-005 in T004 and T-LOCAL-GATES. FR-006 in T-LOCAL-GATES and T-PR. FR-007 in T005.
- Commit T002 and T003 together. A commit with one value alone fails the guard.
