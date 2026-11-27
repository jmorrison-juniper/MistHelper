# Tasks: Dependabot mando pin for the dependency_lock job

**Input**: Numeric record `specs/numbered/0/0/1/2/4/1/0/3/4903-mando-radon-pin/`

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, `design/quickstart.md`, `design/contracts/dependabot-policy.md`

**Tests**: The guard tests in `tests/guardrails` are the required tests. Each guard runs before its commit.

**Status values**: `verified-present` means the artifact is read on `main`. `absent` means the target change is not on `main`. `open` means the action has not started.

## Format: `[ID] [P?] [Requirement] Description`

- **[P]**: Can run in parallel. The task edits a different file and has no open dependency.
- **[Requirement]**: The `FR-###` identifiers from `spec.md`.
- Each task names its paths, its acceptance statement, its verification command, and its status.
- Mark a task `[X]` only after the delivered file is verified.

## Phase 1: Evidence

- [X] T001 [FR-001] Verify that the `dependency_lock` job blocks on lock and export drift.
  - Paths: `.github/workflows/ci.yml` (lines 634 to 650), and `tests/guardrails/test_dependency_lock_workflow.py` (line 74).
  - Acceptance: The job runs `pip install`, then `uv lock --check`, then the export guard. Each step blocks the job.
  - Verification: `python -m pytest tests/guardrails/test_dependency_lock_workflow.py`
  - Status: verified-present (blobs `d51efbc13c0f0a2076680030ed8be7ef7cf64523` and `e529b5c8dc2ce363c670a42595070135fac230c4`).

- [X] T002 [FR-004] Verify that `main` pins `mando` 0.7.1 and that radon 6.0.1 limits `mando`.
  - Paths: `requirements-dev.txt` (lines 179 and 365), `uv.lock` (lines 1301 and 2432), and `.venv\Lib\site-packages\radon-6.0.1.dist-info\METADATA` (line 31).
  - Acceptance: `requirements-dev.txt` pins `mando==0.7.1`. The radon metadata requires `mando (<0.8,>=0.6)`.
  - Verification: `python -m pytest tests/guardrails/test_dependency_lock_file.py`
  - Status: verified-present (blobs `9a528bfe03a10f7bc903f5768ef26de765bbff43` and `5445b4eb382dc9f6dd5c351ba40c521f01f93165`).

## Phase 2: Implementation

- [ ] T003 [FR-002] [FR-004] Add the mando ignore to the Dependabot pip update block.
  - Paths: `.github/dependabot.yml` (insert after line 11, inside the pip block).
  - Acceptance: The pip block holds one `ignore` entry. The entry names `mando` and lists the minor and major update types. Each new line carries a comment.
  - Verification: `python -m pytest tests/guardrails/test_pr_title_workflow.py`
  - Status: absent (no `mando` ignore exists on `main`, blob `be5ad1ea473a41662c2d225a174daa8a6f95df84`).

- [ ] T004 [FR-003] Update the policy snapshot and add two mutation rows.
  - Paths: `tests/guardrails/test_pr_title_workflow.py`, with the snapshot after line 29 and two rows in `test_unrelated_changes_fail` after the row for `("updates", 2, "ignore", 0, "update-types")`.
  - Acceptance: The snapshot equals the new policy. The two new rows fail the guard. Each new line carries a comment.
  - Depends on: T003.
  - Verification: `python -m pytest tests/guardrails/test_pr_title_workflow.py`
  - Status: absent (snapshot holds no pip ignore, blob `e44002451d8b50e059b4aa414b0633320af1ce7e`).

- [ ] T005 [P] [FR-006] Document the `dependency_lock` job and the mando pin.
  - Paths: `documentation/quality-gates.md`, with the job ID list, one table row after line 57, and one section before line 167.
  - Acceptance: The table holds one `dependency_lock` row. The section names radon 6.0.1 and `mando` below 0.8. The file scores 80 or above in `ste-linter`.
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80 documentation/quality-gates.md`
  - Status: absent (no `dependency_lock` text exists on `main`, blob `6776d334cca5d9b43273473a06da367a65605c6d`).

- [ ] T006 [P] [FR-005] Add the changelog fragment.
  - Paths: `changelog.d/issue-4903-mando-radon-pin.md` (new file).
  - Acceptance: The file name matches the issue form. The file holds one heading, one `Fixed` bullet, and no version stamp.
  - Verification: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
  - Status: absent (no fragment for issue 4903 exists on `main`).

- [ ] T007 [P] [FR-008] Copy this record into the repository route.
  - Paths: `specs/numbered/0/0/1/2/4/1/0/3/4903-mando-radon-pin/` (`spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design/`).
  - Acceptance: The route folder holds five children or fewer at each level. Each Markdown file scores 80 or above in `ste-linter`.
  - Verification: `python -m pytest tests/guardrails/test_process_folder_structure.py`
  - Status: absent (no route folder for issue 4903 exists on `main`).

## Phase 3: Final tasks

- [ ] T-LOCAL-GATES [FR-001] [FR-002] [FR-003] [FR-004] [FR-005] [FR-006] [FR-008] Run each applicable local gate.
  - Paths: `.github/dependabot.yml`, `tests/guardrails/test_pr_title_workflow.py`, `documentation/quality-gates.md`, `changelog.d/issue-4903-mando-radon-pin.md`, and `specs/numbered/0/0/1/2/4/1/0/3/4903-mando-radon-pin/`.
  - Acceptance: Each command below reports the expected result. The pull request body records each result.
  - Commands:
    - `python -m py_compile MistHelper.py` reports no output.
    - `python -m ruff check .` reports `All checks passed`.
    - `python -m black --check .` reports that no file needs a change.
    - `python -m pytest tests/guardrails` reports that all tests pass.
    - `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt` reports `gate: 0 new findings vs baseline`.
    - `symbol-diff --base origin/main tests/guardrails/test_pr_title_workflow.py` reports `no module-level name changed`.
    - `bandit -c pyproject.toml -r tests/guardrails/test_pr_title_workflow.py -q` reports no finding.
    - `ste-linter --config .ste-linter.toml --min-score 80` on each changed Markdown file reports a score of 80 or above.
  - Depends on: T003, T004, T005, T006, T007.
  - Verification: `python -m pytest tests/guardrails`
  - Status: open.

- [ ] T-PR [FR-001] [FR-002] [FR-003] [FR-004] [FR-005] [FR-006] [FR-008] Commit, push, and open the pull request.
  - Paths: `.github/dependabot.yml`, `tests/guardrails/test_pr_title_workflow.py`, `documentation/quality-gates.md`, `changelog.d/issue-4903-mando-radon-pin.md`, and `specs/numbered/0/0/1/2/4/1/0/3/4903-mando-radon-pin/`, staged by explicit name.
  - Acceptance: Add the `in-progress` label to issue #4903 and run the file overlap check before the branch exists. Rebase onto `origin/main` before the push. The commit subject is `fix(ci): ignore mando releases that radon rejects`. The commit body holds `Closes #4903` and the Co-authored-by trailer. The pull request gets the type label `bug` and the scope label `ci`. The pull request body holds `Closes #4903`, `Supersedes #4888`, the files-changed summary, the local gate results, and the rollback steps from `plan.md`.
  - Depends on: T-LOCAL-GATES.
  - Verification: `python -m ruff check .`
  - Status: open.

- [ ] T-REMOTE-CI [FR-001] [FR-002] Watch the pull request checks.
  - Paths: `.github/workflows/ci.yml` (the `dependency_lock` job, lines 634 to 650).
  - Acceptance: The check "Dependency lock and exports" reports SUCCESS on the pull request head. No check that passes on `main` fails on the pull request. Record the run ID in the pull request body.
  - Remote command: `gh pr checks <number> -R jmorrison-juniper/MistHelper --watch`
  - Depends on: T-PR.
  - Verification: `python -m pytest tests/guardrails/test_dependency_lock_workflow.py`
  - Status: open.

- [ ] T-MERGE [FR-007] Merge the fix and close pull request #4888.
  - Paths: `.github/dependabot.yml`, `tests/guardrails/test_pr_title_workflow.py`, `documentation/quality-gates.md`, `changelog.d/issue-4903-mando-radon-pin.md`, and `specs/numbered/0/0/1/2/4/1/0/3/4903-mando-radon-pin/`. GitHub pull request #4888 is also named.
  - Acceptance: After orchestrator authorization, add the `auto-merge` label to the fix pull request. After the squash merge, close pull request #4888 with a comment that names the merged commit.
  - Warning: do not push a commit to the fix branch after the squash merge. The pull request then becomes an orphan that nobody merges.
  - Caution: closing pull request #4888 is reversible. Reopen it only when the fix fails.
  - Depends on: T-REMOTE-CI.
  - Verification: `python -m pytest tests/guardrails`
  - Status: open.

## Dependencies & Execution Order

- T001 and T002 are complete.
- T003 comes first in Phase 2. T004 depends on T003, because the snapshot must equal the policy.
- T005, T006, and T007 run in parallel after T003 and T004.
- T-LOCAL-GATES waits for T003 through T007.
- T-PR, T-REMOTE-CI, and T-MERGE run in order.
