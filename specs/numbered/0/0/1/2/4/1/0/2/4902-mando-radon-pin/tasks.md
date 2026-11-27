# Tasks: Quality gate failure from the mando 0.8.2 pin

**Input**: Design documents in `specs/numbered/0/0/1/2/4/1/0/2/4902-mando-radon-pin/`

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, and `design/quickstart.md`.

**Tests**: Five test targets. Section 3 of `design/quickstart.md` lists them. The pin test is new. The other four targets already exist on main.

## Format

- **[P]**: The task can run in parallel with other tasks of its phase. It edits a file that no other open task edits.
- **Requirements**: FR identifiers from `spec.md`.
- **Status**: `open` means not started. `absent` means the change is not on main. `verified-present` means the state was checked on main.

## Phase 1: Evidence and Baseline

### T001 [P] Reproduce the failure from the CI log

- **Requirements**: FR-001, SC-001
- **Files**: None. Read only.
- **Acceptance**: The log of job 137336719038 contains `ERROR: Cannot install -r requirements-dev.txt (line 365) and mando==0.8.2` and `ERROR: ResolutionImpossible`.
- **Verification**: The first command in `design/quickstart.md` section 1.
- **Local gate**: Not applicable. T001 reads the CI log only and changes no file.
- **Status**: verified-present (research R03).

### T002 [P] Confirm that main keeps mando 0.7.1 and radon 6.0.1

- **Requirements**: FR-002
- **Files**: `requirements-dev.txt` (lines 179 and 365), `uv.lock` (line 1300), and `pyproject.toml` (line 118). Read only.
- **Acceptance**: `requirements-dev.txt` pins `mando==0.7.1` and `radon==6.0.1`. The export guard passes on the current tree.
- **Verification**: `python -m pytest tests/guardrails/test_dependency_export.py`
- **Status**: verified-present (research R09, R10, R18, R20).

## Phase 2: Policy and Guard Change

### T003 Add the mando ignore rule to the pip update stream

- **Requirements**: FR-003
- **Files**: `.github/dependabot.yml`. Add the `ignore` block after line 11, inside the pip stream (lines 3 to 11).
- **Acceptance**: The pip stream holds one `ignore` entry for `mando`. The entry lists `version-update:semver-minor` and `version-update:semver-major`. The npm stream does not change.
- **Verification**: Run the command in T004 after T004 completes.
- **Status**: absent (research R21).

### T004 Update the pip stream snapshot

- **Requirements**: FR-003
- **Depends on**: T003
- **Files**: `tests/guardrails/test_pr_title_workflow.py`. Add the `ignore` mapping to `POLICY_SNAPSHOTS["dependabot"]["updates"][0]` after line 29.
- **Acceptance**: `TestDependabotPolicy.test_complete_policy` passes with the new rule. The comparison still covers every other field (research R22, R23).
- **Verification**: `python -m pytest tests/guardrails/test_pr_title_workflow.py`
- **Status**: absent.

### T005 Add the pinned mando guard test

- **Requirements**: FR-004
- **Depends on**: T004. Both tasks edit the same file.
- **Files**: `tests/guardrails/test_pr_title_workflow.py`. Add `from packaging.version import Version` after line 15. Add `test_pinned_mando_stays_below_radon_limit` after `test_complete_policy` (line 297) in `TestDependabotPolicy`.
- **Acceptance**: The method passes with the pin `mando==0.7.1`. It fails with the pin `mando==0.8.2`. Each executable line has an inline comment. The method logs before and after the file read. The method uses no bare `assert result` (research R43).
- **Verification**: `python -m pytest tests/guardrails/test_pr_title_workflow.py`
- **Status**: absent.

## Phase 3: Release Note and Record

### T006 [P] Add the changelog fragment

- **Requirements**: FR-005
- **Files**: `changelog.d/issue-4902-mando-radon-pin.md`. Add the file.
- **Acceptance**: The file has one `###` heading and one `- **Fixed**:` bullet. The bullet names issue #4902. The file name uses the form `issue-<number>-<slug>.md` (research R24, R26).
- **Verification**: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
- **Status**: absent.

### T007 [P] Add this record to the repository

- **Requirements**: FR-006
- **Files**: `specs/numbered/0/0/1/2/4/1/0/2/4902-mando-radon-pin/` with `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, `design/research.md`, `design/data-model.md`, `design/quickstart.md`, and `design/checklists/requirements.md`.
- **Acceptance**: The folder holds the same files as the draft. Each Markdown file scores 80 or above in the STE gate. The route leaf holds one child.
- **Verification**: `ste-linter --config .ste-linter.toml --min-score 80` followed by each record Markdown file (research R39, R42).
- **Status**: absent (research R35, R36).

## Phase 4: Gates, Pull Request, CI, and Merge

### T-LOCAL-GATES Run the applicable local gates

- **Requirements**: FR-007, SC-002, SC-004
- **Depends on**: T003, T004, T005, T006, and T007
- **Files**: The changed files only.
- **Acceptance**: Each applicable gate in `design/quickstart.md` section 3 reports its expected result. Each gate that does not apply reports its reason.
- **Verification**: The commands in `design/quickstart.md` section 3.
- **Status**: open.

### T-PR Commit, push, and open the pull request

- **Requirements**: FR-008
- **Depends on**: T-LOCAL-GATES
- **Files**: Branch `fix/4902-mando-radon-pin` from main, in its own worktree. The changed paths come from T003 to T007.
- **Acceptance**: Before the branch exists, issue #4902 carries the `in-progress` label. The commit subject reads `ci(dependabot): hold mando below 0.8 while radon 6.0.1 requires it`. The pull request body contains `Closes #4902`. The test quality analyzer reports no new findings before the push (research R16).
- **Verification**: `gh pr view <number> -R jmorrison-juniper/MistHelper --json title,body` shows the title and the `Closes #4902` line.
- **Local gate**: The Test quality row of the local gates table. Run the analyzer command in `design/quickstart.md` section 4 after the local commit.
- **Status**: open.

Warning: a force push rewrites history that other agents use. Do not force push to `dependabot/pip/mando-0.8.2`.

### T-REMOTE-CI Watch the required checks

- **Requirements**: FR-008, SC-003
- **Depends on**: T-PR
- **Files**: None.
- **Acceptance**: Every required check on the pull request head reports success. The jobs `Test quality ratchet (gate)` and `Dependency lock and exports` report success (research R12, R14).
- **Verification**: `gh pr checks <number> -R jmorrison-juniper/MistHelper --watch`
- **Local gate**: The Tests row for `tests/guardrails/test_pr_title_workflow.py`. Rerun it when a rebase changes the branch during the wait.
- **Status**: open.

### T-MERGE Merge and close pull request #4888

- **Requirements**: FR-009, FR-010, SC-005
- **Depends on**: T-REMOTE-CI and the orchestrator authorization
- **Files**: None.
- **Acceptance**: Auto-merge starts only after the orchestrator authorizes the merge. The squash merge lands on main. After the merge, pull request #4888 closes without a merge. The closing comment names the surviving branch `dependabot/pip/mando-0.8.2` at commit `e86098cdc2b189d217805b3b4060ef609cbc37af` as the preservation proof (research R08, R49). The branch exists until the comment posts. The first pip update proposal after the merge is recorded (research U-2, U-3).
- **Verification**: `gh pr view 4888 -R jmorrison-juniper/MistHelper --json state,closedAt` returns `CLOSED`.
- **Local gate**: The Tests row for `tests/guardrails/test_pr_title_workflow.py`, run on the merged main checkout after the merge.
- **Status**: open.

Warning: auto-merge publishes the change on main. Enable it only after the orchestrator authorizes the merge.

Caution: deleting the branch before the closing comment posts prevents a reopen of pull request #4888.

## Dependencies and Execution Order

- T001 and T002 run first. They can run in parallel.
- T003 precedes T004. T004 precedes T005. Both edit the same test file.
- T006 and T007 run in parallel with T003 to T005.
- T-LOCAL-GATES waits for T003 to T007.
- T-PR, T-REMOTE-CI, and T-MERGE run in that order.

## Implementation Strategy

The minimum change is T003 to T005. It fixes the policy and proves the pin. Add T006 and T007 before the gates run. Then run the gates, open the pull request, and watch the checks. Merge only after the orchestrator authorizes the merge.

## Guard Rules

- Do not push to main.
- Do not comment, label, close, merge, or create a GitHub item from the spec record. Use GitHub reads only.
- Do not switch branches in the main checkout. Use a worktree.
