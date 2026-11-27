# Tasks: Locked Worktree Bootstrap

**Input**: Numeric record `specs/numbered/0/0/1/2/1/3/3/1/4591-locked-worktree-bootstrap/`. Required documents: `plan.md` and `spec.md`. Supporting documents: `design/research.md`, `design/data-model.md`, `design/quickstart.md`, and `design/contracts/bootstrap-lock-cause.md`.

**Status values**: Use `verified-present` when the evidence exists on `main`. Use `open` when the work waits for its prerequisite. Use `absent` when the work has not started.

**Format**: `[ID] [P?] [Requirement IDs] Title`. Each task names exact paths, an acceptance statement, a verification command, and a status.

## Phase 1: Evidence (read-only)

- [X] T001 [P] [FR-001] Confirm the rejected metadata on `main`. Paths: `uv.lock` at blob `5445b4eb382dc9f6dd5c351ba40c521f01f93165`. Acceptance: the file holds 195 registry source lines, the first at line 8, and 197 package blocks. Verification: `Select-String -LiteralPath uv.lock -Pattern 'source = \{ registry = "https://pypi.org/simple" \}'` from the repository root. Status: verified-present (`design/research.md`, RC-14 and RC-15).

- [X] T002 [P] [FR-001, FR-002, FR-006] Confirm the locked sync and the child environment in the bootstrap. Paths: `scripts/bootstrap_worktree.py` lines 417, 418, 446, and 466. Acceptance: each line exists, and the file holds no frozen sync. Verification: `Select-String -LiteralPath scripts\bootstrap_worktree.py -Pattern 'UV_NATIVE_TLS|"--locked"|"--frozen"'`. Status: verified-present (RC-01 to RC-04).

- [X] T003 [P] [FR-002] Confirm the CI lock checks on `main`. Paths: `.github/workflows/ci.yml` line 648 and `.github/workflows/container-build.yml` line 95. Acceptance: both steps pass on run 45774119357 and run 45774128095. Verification: `gh run view --job 139753527647 -R jmorrison-juniper/MistHelper --log`, filtered for `Resolved`. Status: verified-present (RC-21, RC-23, RC-39, RC-40).

- [X] T004 [P] [FR-003, FR-005] Confirm the cause messages and the public index option on `main`. Paths: `scripts/bootstrap_worktree.py` lines 136, 141, and 679, and `scripts/bootstrap_worktree.ps1` line 68. Acceptance: each text exists. Verification: `Select-String -LiteralPath scripts\bootstrap_worktree.py -Pattern 'INDEX_MISMATCH_MESSAGE =|LOCK_DRIFT_MESSAGE =|--public-lock-index'`. Status: verified-present (RC-06, RC-07, RC-11, RC-13).

## Phase 2: Gate G-1 (reporter data)

- [ ] T005 [FR-011] Obtain from the reporter the uv version, the full locked sync output, and the active index variable names. Paths: none in the repository. Acceptance: an issue comment holds the three items and no host name, URL, or token. Verification: `gh issue view 4591 -R jmorrison-juniper/MistHelper --comments`. Status: open.

- [ ] T006 [FR-001, FR-003] Repeat the failing run in a new worktree and save the output outside the repository. This task confirms the extra-index behavior (plan risk R-04). Paths: none in the repository. Acceptance: the output shows the cause message or the original error. Verification: `design/quickstart.md`, section 3. Status: open. Depends on T005.

## Phase 3: Change (starts after gate G-1)

- [ ] T007 [FR-005, FR-008] Add or update the test cases TC-01 to TC-06 in `tests/unit/scripts/test_bootstrap_worktree_uv.py` before the code change. Keep TC-07 unchanged. Acceptance: TC-01, TC-03, TC-04, and TC-05 fail on the current script. TC-02, TC-06, and TC-07 pass before and after the change. Verification: `python -m pytest tests/unit/scripts/test_bootstrap_worktree_uv.py`. Status: open. Depends on T005.

- [ ] T008 [FR-003, FR-004] Add a method on `InstallationPolicy` that lists the active index variable names. Use it in the index cause message in `scripts/bootstrap_worktree.py` (lines 136-139) and in `diagnose_sync_failure` (lines 477-493). Acceptance: the message names the variables and holds no value. TC-01, TC-02, and TC-03 pass. Verification: `python -m pytest tests/unit/scripts/test_bootstrap_worktree_uv.py` and `python -m ruff check scripts/bootstrap_worktree.py`. Status: open. Depends on T007.

- [ ] T009 [FR-006] Remove the `UV_NATIVE_TLS` entry from the child environment in `scripts/bootstrap_worktree.py` line 417. Keep `UV_SYSTEM_CERTS` at line 418. Acceptance: TC-04 passes. Verification: `python -m pytest tests/unit/scripts/test_bootstrap_worktree_uv.py -k native`. Status: open. Depends on T007.

- [ ] T010 [FR-004] Log the active index variable names before the locked sync in `InstallationPolicy.sync` (`scripts/bootstrap_worktree.py` lines 462-470). Acceptance: TC-05 passes, and the info line runs before the command. Verification: `python -m pytest tests/unit/scripts/test_bootstrap_worktree_uv.py -k logged`. Status: open. Depends on T008.

- [ ] T011 [FR-007] Update `documentation/development-setup.md`. Replace the requirements sentence at line 28. Update the option text at lines 65-66 with the two cause messages. Remove the `UV_NATIVE_TLS=1` row at line 73. Add the uv 0.11.0 minimum near the table at lines 70-76. Acceptance: no sentence names the requirements files as the bootstrap install path, and no row names `UV_NATIVE_TLS`. Verification: `ste-linter --config .ste-linter.toml --min-score 80 documentation/development-setup.md`. Status: open. Depends on T008 and T009.

- [ ] T012 [FR-009] Add `changelog.d/issue-4591-locked-worktree-bootstrap.md`. Acceptance: the file holds one `###` heading and one bullet under `Changed`, and the bullet names issue 4591. Verification: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`. Status: open. Depends on T008, T009, and T010.

## Phase 4: Gates and delivery

- [ ] T-LOCAL-GATES [FR-008, FR-010] Run each applicable local gate from `design/quickstart.md`, section 4, against the changed files only. Acceptance: each command reports its expected result. Verification: the commands in `design/quickstart.md`, section 4. Status: open. Depends on T007 to T012.

- [ ] T-PR [FR-010] Commit with the subject `fix(scripts): name the index cause in the locked bootstrap`. Push `fix/4591-locked-worktree-bootstrap`. Open the pull request. The body holds `Closes #4591`, `Refs #4774`, the gate results, and the red and green test runs. Acceptance: `git diff --name-only origin/main HEAD` lists no dependency file. Verification: `gh pr view --json title,headRefName,body`. Status: absent. Depends on T-LOCAL-GATES.

- [ ] T-REMOTE-CI [SC-002] Watch the pull request checks. Acceptance: the job `Dependency lock and exports`, the Conventional Commits title check, the STE check, and CodeQL pass. Verification: `gh pr checks --watch`. Status: absent. Depends on T-PR.

- [ ] T-MERGE [FR-011] Add the `auto-merge` label only after T-REMOTE-CI passes and the orchestrator authorizes the merge. The `needs-human-review` label stays on the issue until the repository owner reviews the pull request. Acceptance: the squash merge closes issue 4591. Verification: `gh pr view --json state,mergedAt`. Status: absent. Depends on T-REMOTE-CI.

## Dependencies and Execution Order

- T006 depends on T005.
- T007 depends on T005.
- T008 depends on T007.
- T009 depends on T007.
- T010 depends on T008.
- T011 depends on T008 and T009.
- T012 depends on T008, T009, and T010.
- T-LOCAL-GATES depends on T007 to T012.
- T-PR depends on T-LOCAL-GATES.
- T-REMOTE-CI depends on T-PR.
- T-MERGE depends on T-REMOTE-CI.
- Tasks T001 to T004 have no prerequisite. They run in parallel.

## Requirement Coverage

- FR-001: T001, T002, T006.
- FR-002: T002, T003.
- FR-003: T004, T006, T007, T008.
- FR-004: T007, T008, T010.
- FR-005: T004, T007.
- FR-006: T002, T007, T009.
- FR-007: T011.
- FR-008: T007, T-LOCAL-GATES.
- FR-009: T012.
- FR-010: T-PR, T-LOCAL-GATES.
- FR-011: T005, T-MERGE.
