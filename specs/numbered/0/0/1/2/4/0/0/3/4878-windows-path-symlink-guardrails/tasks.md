# Tasks: Windows Path and Symlink Guardrails

**Input**: Design documents in `specs\numbered\0\0\1\2\4\0\0\3\4878-windows-path-symlink-guardrails\`.

**Prerequisites**: `plan.md` and `spec.md` (required), `design\research.md`, `design\quickstart.md`, and `design\data-model.md`.

**Tests**: Each changed guard is an existing test. No new test function or class is added (D-7). The test set is listed below.

**Ownership**: Edit only the files named in each task. Stage each file by its explicit path.

**Environment**: Run each command from the worktree root, with the `.venv` of that worktree.

## Format

- **[P]**: The task edits a different file from the other [P] tasks of its phase, so it can run in parallel.
- **Requirements**: Requirement IDs from `spec.md`.
- **Status**: `open` means the work has not started. `absent` means the deliverable is not on `main` (R-06, R-15, R-19, R-70).
- **Verification**: T001 to T006 and T-LOCAL-GATES use local gate commands from `copilot-instructions.md`. T-PR, T-REMOTE-CI, and T-MERGE use GitHub commands, because the local gates table names no pull request gate.

Caution: five unrelated files are modified in the local checkout. Stage each file by explicit path, and do not use `git add -A` or `git add .`.

## Phase 1: Baseline

### T001 Record the Windows baseline on the untouched branch

- **Requirements**: FR-001, FR-005, FR-006
- **Files**: `tests\guardrails\test_spec_route_contract.py`, `tests\guardrails\local_test_quality_loop\test_scope.py`, `tests\guardrails\test_analytics_package_structure.py`
- **Acceptance**: On the reporter Windows host, the symlink, Git root, and missing-root tests each fail with the cause that the issue names.
- **Verification**: `python -m pytest tests/guardrails/test_spec_route_contract.py -q -rs -k symlink`
- **Status**: open

## Phase 2: Fixes

### T002 [P] Skip the symlink case on WinError 1314 with a logged cause

- **Requirements**: FR-001, FR-002, FR-003, FR-004, FR-008, FR-009
- **Files**: `tests\guardrails\test_spec_route_contract.py`
- **Acceptance**: Add method `SpecCommandFixture.symlink` after `feature` (R-08). The method skips only for winerror 1314 and logs the cause at error level first. Other `OSError` values re-raise. The test function calls the method in place of lines 294 to 296 (R-04, R-05). The module keeps no new top-level name, and `import logging` sits inside the method.
- **Verification**: `python -m pytest tests/guardrails/test_spec_route_contract.py -q -rs`
- **Status**: absent

### T003 [P] Compare the Git root as a path value

- **Requirements**: FR-005, FR-008, FR-009
- **Files**: `tests\guardrails\local_test_quality_loop\test_scope.py`
- **Acceptance**: `test_git_ignores_poisoned_locations` stores the `rev-parse` output, then asserts `Path(top_level) == repository.root.resolve()` (R-15). The function logs before and after each Git call. The module keeps `import logging` (R-16) and adds no import.
- **Verification**: `python -m pytest tests/guardrails/local_test_quality_loop/test_scope.py -q -k test_git_ignores_poisoned_locations`
- **Status**: absent

### T004 [P] Use one separator style in the missing-root message and pattern

- **Requirements**: FR-006, FR-007, FR-008, FR-009
- **Files**: `tests\guardrails\test_analytics_package_structure.py`
- **Acceptance**: `_package_directories` builds `missing_paths` with `as_posix()` (R-18, R-19). The method logs before and after the directory check, with the existing `LOGGER` (R-21). The expected pattern at line 177 uses `re.escape(missing_root.as_posix())` (R-20). The message wording stays the same.
- **Verification**: `python -m pytest tests/guardrails/test_analytics_package_structure.py -q -k test_missing_root_fails_with_path_and_cause`
- **Status**: absent

### T005 [P] Add the changelog fragment

- **Requirements**: FR-010
- **Files**: `changelog.d\issue-4878-windows-path-symlink-guardrails.md`
- **Acceptance**: The file holds one `###` heading, one `- **Fixed**:` bullet that names issue #4878, and no removed analytics module path (R-55, R-56, R-72). The name uses the issue form (R-56).
- **Verification**: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q`
- **Status**: absent

### T006 [P] Copy the record to the route

- **Requirements**: FR-011
- **Files**: `specs\numbered\0\0\1\2\4\0\0\3\4878-windows-path-symlink-guardrails\` (`spec.md`, `plan.md`, `tasks.md`, `analysis.md`, `design\research.md`, `design\data-model.md`, `design\quickstart.md`, `design\checklists\requirements.md`, `design\checklists\test-quality.md`)
- **Acceptance**: The route folder holds the record. Each folder holds five children or fewer. The route folder `specs\numbered\0\0\1\2\4\0\0\3` did not exist before this task (R-70).
- **Verification**: `python -m pytest tests/guardrails/test_spec_route_contract.py -q -k test_numeric_feature_route_remains_stable`
- **Status**: absent

Warning: the draft folder holds the only copy of the record until T006 finishes. Do not delete the draft folder before T006 finishes.

## Phase 3: Gates and Pull Request

### T-LOCAL-GATES Run each applicable local gate

- **Requirements**: FR-008, FR-009, FR-012
- **Files**: The three changed test files, the changelog fragment, and the record folder
- **Acceptance**: Each applicable command in `design\quickstart.md` section 3 passes, in table order (R-45 to R-52). Each gate that does not apply records its reason in the pull request body. Symbol-diff reports no module-level name change for each changed test file (R-51).
- **Verification**: `python -m ruff check .` (R-46)
- **Status**: open

### T-PR Commit, analyze, push, and open the pull request

- **Requirements**: FR-010, FR-011, FR-012
- **Files**: The explicit paths from T002 to T006
- **Acceptance**: Claim the issue with label `in-progress` before the branch exists. Create `fix/4878-windows-path-symlink-guardrails` from `main`. Commit with the subject `fix(tests): skip symlink guard without privilege and compare paths as values` (R-34). Run the test-quality analyzer on the commit (R-49). Push the branch. Open the pull request with `Closes #4878`, the local gate results, and one failing path for each guard (R-68, R-69).
- **Verification**: `gh pr view <number> -R jmorrison-juniper/MistHelper --json body --jq .body`
- **Status**: open

Caution: stage each file by its explicit path. Check `git status` before each `git add` command, because five unrelated files are modified.

### T-REMOTE-CI Wait for remote checks

- **Requirements**: FR-012, SC-003, SC-005
- **Files**: The pull request from T-PR
- **Acceptance**: Every required check passes on the latest commit. The Linux `pytest` job runs the symlink case without a skip. The `test_quality_gate` job reports zero new findings.
- **Verification**: `gh pr checks <number> -R jmorrison-juniper/MistHelper --watch`
- **Status**: open

### T-MERGE Enable auto-merge after authorization

- **Requirements**: FR-012
- **Files**: The pull request from T-PR
- **Acceptance**: Enable auto-merge with label `auto-merge` only after T-REMOTE-CI passes and the orchestrator authorizes the merge. Remove the branch and the worktree after the merge.
- **Verification**: `gh pr view <number> -R jmorrison-juniper/MistHelper --json state,mergedAt,autoMergeRequest`
- **Status**: open

Warning: a merge changes `main` for every agent. Do not enable auto-merge before the orchestrator authorizes it.

## Dependencies

- T002, T003, and T004 depend on T001.
- T005 and T006 have no dependency.
- T-LOCAL-GATES depends on T002, T003, T004, T005, and T006.
- T-PR depends on T-LOCAL-GATES.
- T-REMOTE-CI depends on T-PR.
- T-MERGE depends on T-REMOTE-CI.

## Test Set

The test set holds 12 named tests (`tests_planned` = 12). Each test runs in the verification commands of this file and of `design\quickstart.md`.

| # | Test | Role |
| - | - | - |
| 1 | `tests/guardrails/test_spec_route_contract.py::test_unsafe_feature_selection_fails[symlink]` | Changed: skip on 1314, reject on a privileged host |
| 2 | `tests/guardrails/test_spec_route_contract.py::test_unsafe_feature_selection_fails[outside]` | Regression |
| 3 | `tests/guardrails/test_spec_route_contract.py::test_unsafe_feature_selection_fails[nested]` | Regression |
| 4 | `tests/guardrails/local_test_quality_loop/test_scope.py::TestFixtureSafety::test_git_ignores_poisoned_locations` | Changed: path-value comparison |
| 5 | `tests/guardrails/test_analytics_package_structure.py::TestAnalyticsPackageStructure::test_missing_root_fails_with_path_and_cause` | Changed: forward-slash message |
| 6 | `tests/guardrails/test_analytics_package_structure.py::TestAnalyticsPackageStructure::test_sixth_child_fails_with_measured_count` | Regression |
| 7 | `tests/guardrails/test_analytics_package_structure.py::TestAnalyticsPackageStructure::test_active_old_path_is_reported` | Regression |
| 8 | `tests/guardrails/test_analytics_package_structure.py::TestAnalyticsPackageStructure::test_git_input_failure_reports_cause` | Regression |
| 9 | `tests/guardrails/test_analytics_package_structure.py::TestAnalyticsPackageStructure::test_repository_structure_and_paths` | Regression, and it reads the changelog fragment |
| 10 | `tests/guardrails/test_changelog_fragment_policy.py::TestFragmentNaming::test_every_fragment_uses_an_allowed_name` | Guard for the fragment name |
| 11 | `tests/guardrails/test_changelog_fragment_policy.py::TestFragmentContent::test_every_fragment_holds_a_heading_and_a_bullet` | Guard for the fragment content |
| 12 | `tests/guardrails/test_changelog_fragment_policy.py::TestFragmentContent::test_every_fragment_states_a_change_type` | Guard for the fragment change type |
