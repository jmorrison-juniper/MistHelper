# Tasks: Early dependency check without half-removed packages

**Input**: `plan.md`, `spec.md`, `design/research.md`, `design/data-model.md`, `design/contracts/startup-messages.md`, `design/quickstart.md`.

**Prerequisites**: Issue #4930 is open. Create the branch `fix/4930-early-dependency-updater` from `main` after the orchestrator authorizes the work.

**Format**: `[ID] [P?] [Requirements] Description`. `[P]` marks a task that can run in parallel, because it edits a different file. Each task names exact paths, an acceptance statement, one verification command, and a status.

**Status values**: `open` means the work has not started. `absent` means the code or text that the task adds is not on `main`. `partial` means some of the target exists on `main`, and the task changes it.

**Tests**: Test cases TC-01 to TC-13 are defined in `design/quickstart.md`. Each case is a unit, integration, or edge-case test. TC-12 is a regression test.

## Phase 1: Tests first

- [ ] T001 [P] [FR-001, FR-002, FR-003, FR-004, FR-006, FR-007, FR-008] Write test cases TC-01 to TC-11. Each case fails on `main` for the reason that it names. TC-12 is a regression case that passes on `main` and after the change.
  - Files: `tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_dependency_check_paths.py`, `tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_package_installer_wave9.py`, `tests/bootstrap/test_dependency_check_venv_guard.py`.
  - Acceptance: Each new case asserts an installer call count, a file state, or a log text. No case asserts only a constant.
  - Verification: `python -m pytest tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_dependency_check_paths.py`
  - Status: absent

- [ ] T002 [P] [FR-009] Write test case TC-13. It compares each pin in `requirements.txt` with the version in `uv.lock`.
  - File: `tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_uv_locked_sync.py`
  - Acceptance: The case fails for any pin that differs from the lock version, and it prints the count of pins that it checked.
  - Verification: `python -m pytest tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_uv_locked_sync.py`
  - Status: absent

## Phase 2: Inventory and snapshot classes

- [ ] T003 [FR-001, FR-002, FR-003] Add the class `DistributionInventory` to `src/foundation/runtime/bootstrap/package_installer.py`. It reports whether a package has an incomplete RECORD, and whether a package is loaded.
  - Acceptance: The loaded check reads `packages_distributions()` through an injected metadata module. It treats a package with no top-level name as loaded. The incomplete check returns true when RECORD is missing or a listed file is missing.
  - Depends on: T001
  - Verification: `python -m pytest tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_package_installer_wave9.py`
  - Status: absent

- [ ] T004 [FR-004] Add the class `DistributionSnapshot` to `src/foundation/runtime/bootstrap/package_installer.py`. It captures RECORD files, restores them, and discards the copy.
  - Acceptance: A capture failure returns a failure value and copies nothing. A restore copies every captured file back. A discard removes only the snapshot folder.
  - Depends on: T001 (and T003 for the same file, so this task runs after T003)
  - Verification: `python -m pytest tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_package_installer_wave9.py`
  - Status: absent

## Phase 3: Orchestrator behavior

- [ ] T005 [FR-002, FR-003, FR-008] In `src/foundation/runtime/bootstrap/dependency_check.py`, replace `_is_importable` (line 175) with a metadata presence read and the inventory incomplete check. Remove the field `package_import_map` (line 72) and its lookup (line 167).
  - Acceptance: The classification path calls no requirement module import. A missing version marks the package as missing. The disabled short-circuit at the start of `run()` stays first.
  - Depends on: T003
  - Verification: `python -m pytest tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_dependency_check_paths.py`
  - Status: partial

- [ ] T006 [FR-001, FR-005, FR-006] In `src/foundation/runtime/bootstrap/dependency_check.py`, add the loaded-package skip and the drift threshold to `run()` (line 80) and to the classification path.
  - Acceptance: A loaded package makes no in-process change. A run with more than five drifted packages makes no in-process change and logs the refusal. A run with exactly five drifted packages proceeds.
  - Depends on: T005
  - Verification: `python -m pytest tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_dependency_check_paths.py`
  - Status: absent

- [ ] T007 [FR-004] In `src/foundation/runtime/bootstrap/dependency_check.py`, wrap each upgrade in `_upgrade_one` (line 284) with capture, restore, and discard. A capture failure skips that upgrade.
  - Acceptance: A failed upgrade restores the snapshot. A restore failure logs the snapshot path and the repair command. A successful upgrade discards the snapshot.
  - Depends on: T004, T006
  - Verification: `python -m pytest tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_dependency_check_paths.py`
  - Status: absent

- [ ] T008 [FR-006, FR-007] In `src/foundation/runtime/bootstrap/dependency_check.py`, add the log records from `design/contracts/startup-messages.md`. Each record uses the exact text in that contract.
  - Acceptance: Each in-process change has an info record before it and a debug record after it. Every new changed line has an inline comment.
  - Depends on: T007
  - Verification: `python -m pytest tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_dependency_check_paths.py`
  - Status: absent

## Phase 4: Entry point and existing tests

- [ ] T009 [FR-011] In `MistHelper.py`, inside `early_dependency_check()` (lines 1051 to 1062), pass an `inventory` argument that holds a `DistributionInventory` instance, and remove the `package_import_map` argument.
  - Acceptance: The function keeps its name, its zero-argument signature, and its call to `orchestrator.run()` (line 1063). The import line for `PackageImportMapManager` stays unless the linter reports it unused.
  - Depends on: T003, T005
  - Verification: `python -m py_compile MistHelper.py`
  - Status: partial

- [ ] T010 [FR-008] Update the existing tests that pass `package_import_map` or patch `_is_importable`. Affected files and lines: `tests/bootstrap/test_dependency_check_venv_guard.py` (43 to 47, 102). `tests/unit/config/standalone/foundation/runtime/startup/test_dependency_check.py` (26 to 30). `tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_dependency_check_paths.py` (41, 48, 61, 87 to 91, 102 to 106, 154 to 163, 333 to 348).
  - Acceptance: No test passes `package_import_map`. No test patches `_is_importable`. TC-12 passes for the disabled path.
  - Depends on: T009
  - Verification: `python -m pytest tests/bootstrap/test_dependency_check_venv_guard.py`
  - Status: partial

## Phase 5: Documentation and release note

- [ ] T011 [P] [FR-010] Add the startup dependency check section to `README.md`, before `## Documentation` (line 115). The section names the repair command, the threshold of five packages, and the `DISABLE_AUTO_INSTALL` workaround.
  - Acceptance: Each sentence passes the STE gate. The section has no instruction longer than 20 words.
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80 README.md AGENTS.md .github/copilot-instructions.md CLAUDE.md documentation/ASD-STE100_writing-guide.md`
  - Status: absent

- [ ] T012 [P] [FR-010] Add the repair steps to `documentation/operator-guide.md`. Include the `DISABLE_AUTO_INSTALL=true` workaround, and the rule to close each process before the repair command runs.
  - Acceptance: The file passes the STE gate. It names the repair command, and it does not name `documentation/development-setup.md`.
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80 documentation/operator-guide.md`
  - Status: absent

- [ ] T013 [P] [FR-009] Add `changelog.d/issue-4930-early-dependency-updater.md` with one `### Fixed` heading and one bullet that names issue 4930.
  - Acceptance: The file follows the fragment rule in `changelog.d/README.md`.
  - Verification: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
  - Status: absent

## Phase 6: Final tasks

- [ ] T-LOCAL-GATES [FR-001 to FR-011] Run each applicable gate in the Local gates table of `.github/copilot-instructions.md` on the changed files. Record each command and its result in the pull request body.
  - Acceptance: Each applicable gate passes. The quickstart lists the exact commands. The record names each gate that does not apply, with its reason.
  - Depends on: T001 to T013
  - Verification: `python -m ruff check .`
  - Status: open

- [ ] T-PR [FR-009] Commit with the Conventional Commits subject `fix(bootstrap): skip loaded packages in the early dependency check`. Push `fix/4930-early-dependency-updater`. Open the pull request with `Closes #4930`, the changed-file summary, the gate results, and the rollback notes. After the pull request opens, rename the changelog fragment as `changelog.d/README.md` names.
  - Acceptance: The pull request title passes the Conventional Commits title check. The body holds each item of `.github/PULL_REQUEST_TEMPLATE.md`.
  - Depends on: T-LOCAL-GATES
  - Verification: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
  - Status: open

- [ ] T-REMOTE-CI [FR-011] Watch the required checks for the pull request with `gh pr checks --watch`. Wait for CodeQL. Fix each failure on the same branch.
  - Acceptance: Each required check shows success on the latest commit. CodeQL shows success.
  - Depends on: T-PR
  - Verification: `gh pr checks --watch`
  - Status: open

- [ ] T-MERGE [FR-001 to FR-011] After the orchestrator authorizes the merge, add the `auto-merge` label. Squash merge the pull request. Wait for `.github/workflows/container-build.yml` on the merged commit. Verify that the image revision label equals the merged commit SHA. Deploy the approved image and check its health.
  - Acceptance: The pull request state is merged. The image revision label equals the merged commit SHA. The health check passes after deployment.
  - Depends on: T-REMOTE-CI
  - Verification: `gh pr view --json state,mergedAt,mergeCommit`
  - Status: open

## Dependencies and Execution Order

### Phase Dependencies

- Phase 1 has no dependency. T001 and T002 run in parallel.
- Phase 2 depends on T001. T004 runs after T003, because both edit `package_installer.py`.
- Phase 3 depends on Phase 2. T005, T006, T007, and T008 run in this order, because each edits `dependency_check.py`.
- Phase 4 depends on Phase 3. T009 runs before T010.
- Phase 5 tasks T011, T012, and T013 run in parallel after Phase 4. They edit different files.
- Phase 6 runs in this order: T-LOCAL-GATES, T-PR, T-REMOTE-CI, T-MERGE.

### Parallel Opportunities

- T001 and T002 edit different test files.
- T011, T012, and T013 edit different documentation and changelog files.

## Notes

- Verify each test fails before the change in its phase. A passing test on `main` does not prove the behavior.
- The verification commands for T-REMOTE-CI and T-MERGE check remote state. They sit outside the local gates table. AGENTS.md names the `gh pr checks` command for the check watch.
- No task changes `requirements.txt`, `pyproject.toml`, or `uv.lock` (FR-009).
