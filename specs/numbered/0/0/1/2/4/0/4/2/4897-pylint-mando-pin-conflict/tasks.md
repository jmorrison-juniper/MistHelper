# Tasks: Pylint gate failure from the mando 0.8.2 pin

**Input**: Numeric record `specs\numbered\0\0\1\2\4\0\4\2\4897-pylint-mando-pin-conflict\`.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design\research.md`, and `design\quickstart.md`.

**Format**: Each task names its requirements, its files, its acceptance statement, its verification command, and its status. `[P]` marks a task that touches a file no other open task touches. Read-only and delivery tasks name a GitHub or quickstart command, because no local gate applies to them.

**Status values**: `open` means not started. `verified-present` means the state already holds on main. `absent` means the change is not on main yet. `partial` means some of the change exists.

## Phase 1: Root cause verification

### T001 Reproduce the failed check from the CI log

- **Requirements**: FR-001
- **Files**: None. The task is read-only.
- **Acceptance**: The failed log of job 137338442217 shows the resolution error at lines 932 to 946. Step `Run Pylint` does not run.
- **Verification**: Run the Scenario 1 commands in `design\quickstart.md`.
- **Status**: verified-present

### T002 Confirm the pins and the radon requirement on main

- **Requirements**: FR-001, FR-003
- **Files**: `requirements-dev.txt` (lines 179 and 365), `pyproject.toml` (line 118), and `uv.lock` (lines 1301 and 2428).
- **Acceptance**: Main pins `mando==0.7.1`. The installed radon 6.0.1 declares `mando (<0.8,>=0.6)`.
- **Verification**: Run the Scenario 2 commands in `design\quickstart.md`.
- **Status**: verified-present

## Phase 2: Core change

### T003 [P] Add the mando ignore entry to the Dependabot pip stream

- **Requirements**: FR-005
- **Files**: `.github/dependabot.yml`, the pip stream at lines 3 to 11.
- **Acceptance**: The pip stream holds an `ignore` list. The list has `dependency-name: "mando"` and `versions: [">= 0.8"]`. The npm stream stays unchanged.
- **Verification**: `python -m pytest tests/guardrails/test_pr_title_workflow.py -q`, after T004.
- **Status**: absent

### T004 Update the Dependabot policy snapshot

- **Depends on**: T003
- **Requirements**: FR-006
- **Files**: `tests/guardrails/test_pr_title_workflow.py`, the pip item of `POLICY_SNAPSHOTS["dependabot"]` at lines 23 to 30.
- **Acceptance**: The pip item holds the same `ignore` list as T003. Class `TestDependabotPolicy` passes.
- **Verification**: `python -m pytest tests/guardrails/test_pr_title_workflow.py -q`.
- **Status**: absent

### T005 [P] Add the pinned mando test

- **Requirements**: FR-007
- **Files**: `tests/guardrails/test_dependency_lock_file.py`. Add `import importlib.metadata` before line 9. Append function `test_pinned_mando_satisfies_radon_requirement` after the last function.
- **Acceptance**: The function reads the mando pins from both exports through `DependencyLock.read_requirements`. It requires exactly one pin. It reads the installed radon requirements with `importlib.metadata.requires`. It requires exactly one unconditional mando requirement. It asserts that the pinned version satisfies that requirement. Each new line has an inline comment. Log lines appear before and after each read.
- **Verification**: `python -m pytest tests/guardrails/test_dependency_lock_file.py -q`.
- **Status**: absent

### T006 Prove the red state of T005 on the pull request #4888 pin

- **Depends on**: T005
- **Requirements**: FR-007, SC-003
- **Files**: None changed. Use a worktree of commit `e86098cdc2b189d217805b3b4060ef609cbc37af`.
- **Acceptance**: The new test fails in that worktree. The failure message names radon and `mando==0.8.2`. The pull request body quotes the failing output.
- **Verification**: Run Scenario 3, step 4, in `design\quickstart.md`.
- **Status**: open

### T007 [P] Add the Known pitfalls entry

- **Requirements**: FR-011
- **Files**: `.github/copilot-instructions.md`. Insert one bullet after line 574, before the blank line that precedes `## Key files`.
- **Acceptance**: One bullet names issue #4897, radon 6.0.1, and the rule to keep mando below 0.8. The file passes the STE gate.
- **Verification**: Run the STE command in Scenario 4 of `design\quickstart.md`, which covers `.github/copilot-instructions.md` and the other instruction files.
- **Status**: absent

### T008 [P] Add the release-note fragment

- **Requirements**: FR-012
- **Files**: `changelog.d/issue-4897-pylint-mando-pin.md`, a new file.
- **Acceptance**: The file holds one `###` heading and one `Fixed` bullet that names issue #4897. It holds no version stamp. Its name follows the issue-only rule, and the name stays after the pull request opens.
- **Verification**: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q`.
- **Status**: absent

### T009 [P] Keep the pins, the lock, and the gate unchanged

- **Requirements**: FR-002, FR-003, FR-004, FR-009, FR-013
- **Files**: `requirements-dev.txt`, `requirements.txt`, `uv.lock`, `pyproject.toml`, `.github/workflows/ci.yml`, `src\`, and `MistHelper.py`. The change set holds none of these files.
- **Acceptance**: The change set contains none of these files. `uv lock --check` passes. The export guard passes.
- **Verification**: `uv lock --check`, then `python -m pytest -s -q tests/guardrails/test_dependency_export.py`.
- **Status**: verified-present

## Phase 3: Delivery

### T-LOCAL-GATES Run each local gate that applies

- **Depends on**: T003, T004, T005, T006, T007, T008, T009
- **Requirements**: FR-001 to FR-013
- **Files**: `.github/dependabot.yml`, `tests/guardrails/test_pr_title_workflow.py`, `tests/guardrails/test_dependency_lock_file.py`, `.github/copilot-instructions.md`, and `changelog.d/issue-4897-pylint-mando-pin.md`.
- **Acceptance**: Each gate in Scenario 4 of `design\quickstart.md` reports its expected result. The pull request body lists each gate and its result. A gate that does not apply carries a stated reason.
- **Verification**: Run Scenario 4 in `design\quickstart.md`.
- **Status**: open

### T-PR Commit, push, and open the pull request

- **Depends on**: T-LOCAL-GATES
- **Requirements**: FR-010
- **Files**: The five changed files, added by explicit path.
- **Acceptance**: The branch is `fix/4897-pylint-mando-pin`. The commit title is `fix(ci): hold mando below 0.8 while radon 6.0.1 is pinned`. The pull request body contains `Closes #4897`, the gate results, and the T006 failing output.
- **Verification**: Run `gh pr view --json title,body,headRefName` from the branch worktree.
- **Status**: open

### T-REMOTE-CI Watch the Quality Gates run

- **Depends on**: T-PR
- **Requirements**: FR-002, SC-001, SC-002, SC-004
- **Files**: None.
- **Acceptance**: Job `Pylint (score gate)` reports step `Run Pylint` as successful. Job `Dependency lock and exports` passes. The policy guard passes. No install step logs `ResolutionImpossible`. Both Windows checks pass.
- **Verification**: Run `gh pr checks --watch` from the branch worktree. Then run the job lookup in Scenario 5 of `design\quickstart.md`.
- **Status**: open

### T-MERGE Merge after authorization

- **Depends on**: T-REMOTE-CI
- **Requirements**: FR-008
- **Files**: None.
- **Acceptance**: The orchestrator authorizes the merge. The implementer then adds the `auto-merge` label. The squash merge completes. The implementer closes pull request #4888 and removes the branch.
- **Verification**: `gh pr view 4888 -R jmorrison-juniper/MistHelper --json state` reports `CLOSED` after the closure.
- **Status**: open

## Dependencies and execution order

- T003, T005, T007, T008, and T009 touch different files. They run in parallel.
- T004 waits for T003. T006 waits for T005.
- The four delivery tasks run in the order T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE.

## Tests planned

- `test_pinned_mando_satisfies_radon_requirement`, a new test in `tests/guardrails/test_dependency_lock_file.py` (T005).
- `TestDependabotPolicy::test_complete_policy`, updated through the snapshot in `tests/guardrails/test_pr_title_workflow.py` (T004).
- `TestDependabotPolicy::test_unrelated_changes_fail`, a regression test in `tests/guardrails/test_pr_title_workflow.py` (T004).
- `test_requirements_exports_match_the_lock`, a regression test in `tests/guardrails/test_dependency_export.py` (T009).
- `test_lock_satisfies_every_requirement`, a regression test in `tests/guardrails/test_dependency_lock_file.py` (T009).
- `test_lock_is_current_with_pyproject`, a regression test in `tests/guardrails/test_dependency_lock_file.py` (T009).
