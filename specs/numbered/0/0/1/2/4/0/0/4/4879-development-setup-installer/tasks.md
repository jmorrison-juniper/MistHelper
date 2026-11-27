# Tasks: Development setup installer text

**Input**: Design documents in `specs\numbered\0\0\1\2\4\0\0\4\4879-development-setup-installer\`

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, `design/quickstart.md`, and `design/contracts/bootstrap-installer-flow.md`

**Tests**: No new pytest case is added (D-6). Verification uses the local STE gate, the existing guard `tests/guardrails/test_container_policy_docs.py`, and the checks TST-001 to TST-010 in `design/quickstart.md`.

**Organization**: Tasks are grouped by user story. US1 is the install command. US2 is the setting check against the script. US3 is the writing score and the change scope.

## Format

Each task line gives its ID, parallel marker, story, requirement IDs, paths, acceptance, verification, and status. A status is `open`, `verified-present`, `partial`, or `absent`. The status describes the text on `main` at commit `f03c6c9b`, before the task runs.

## Phase 1: Setup

- [ ] T001 [US1] [FR-001] Create the worktree `..\MistHelper-4879` on branch `fix/4879-development-setup-installer` from `origin/main`. Files: none. Acceptance: The worktree holds `documentation\development-setup.md` at blob `1733975a7e0a0962fe5367e165a21f5831f8c3e5`. Verification: `python -m py_compile MistHelper.py`. Status: open.

## Phase 2: User Story 1 - Read the install command that the bootstrap runs

- [ ] T002 [US1] [FR-001, FR-002] Replace the Step 2 paragraph at lines 28 and 29 (plan M-01). Files: `documentation\development-setup.md`. Acceptance: Step 2 names `uv sync --locked --extra dev`, and no sentence names a requirement-file install (checks TST-002 and TST-003). Verification: `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 documentation\development-setup.md`. Status: absent (R-03 stale at line 28, R-11 absent).
- [ ] T003 [US1] [FR-001, FR-003] Modify line 59. Add the locked sync paragraph after line 61. Add the drift sentence after line 64 (plan M-02 to M-04). Files: `documentation\development-setup.md`. Acceptance: The installer section names the locked sync, the uv executable condition, and the drift message (checks TST-003 and TST-004). Verification: `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 documentation\development-setup.md`. Status: absent (R-11 absent).
- [ ] T004 [US1] [FR-002, FR-006] Replace the report paragraph at lines 83 to 87 (plan M-08). Files: `documentation\development-setup.md`. Acceptance: The paragraph quotes the report line exactly and holds none of the three retired sentences (checks TST-002 and TST-006). Verification: `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 documentation\development-setup.md`. Status: partial (R-06, R-07, and R-08 stale. The "Actual duration" sentence is present.)
- [ ] T005 [US1] [FR-007] Add the pip export paragraph after line 87 (plan M-09). Files: `documentation\development-setup.md`. Acceptance: The paragraph says that the bootstrap installs neither pip export file (check TST-007). Verification: `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 documentation\development-setup.md`. Status: absent.
- [ ] T006 [US1] [FR-002] Modify line 91 (plan M-10). Files: `documentation\development-setup.md`. Acceptance: The caution names a uv command, not a uv installation (check TST-002). Verification: `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 documentation\development-setup.md`. Status: partial (the caution text is present, with the retired term).
- [ ] T010 [US1] [FR-003, FR-004] Confirm that lines 57, 58, 60, 63, 64, 65, and 66 keep their text (plan M-16). Files: `documentation\development-setup.md`. Acceptance: The uv discovery order, the install refusal, the lock message, and the public index text match the `main` blob (checks TST-004 and TST-008). Verification: `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 documentation\development-setup.md`. Status: verified-present (R-18 and R-23 agree with the text).

## Phase 3: User Story 2 - Check each installer setting against the script

- [ ] T007 [US2] [FR-005] Modify line 68 and add eight rows after line 75. Keep the four rows at lines 72 to 75 (plan M-05, M-06). Files: `documentation\development-setup.md`. Acceptance: The table names all twelve settings of contract section 3 (check TST-005). Verification: `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 documentation\development-setup.md`. Status: partial (four of twelve names present. R-10 is absent.)
- [ ] T008 [US2] [FR-005] Modify lines 77 and 79, and add the `PYTHONNOUSERSITE` sentence after line 81 (plan M-07). Files: `documentation\development-setup.md`. Acceptance: The text names the `UV_CONFIG_FILE` removal, the child copy of the caller environment, and the `PYTHONNOUSERSITE` removal (check TST-005). Verification: `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 documentation\development-setup.md`. Status: partial (line 77 is correct in part. Line 79 uses the retired term "Each file". The PYTHONNOUSERSITE sentence is absent.)
- [ ] T009 [US2] [FR-005] Delete line 103 and modify line 104. Modify lines 109 to 111. Delete lines 115 and 116. Modify line 117 (plan M-11, M-12, M-13). Files: `documentation\development-setup.md`. Acceptance: No "Extra-source order" sentence remains. The `PIP_CONFIG_FILE` and `UV_NO_CONFIG` sentences name their effect (checks TST-002 and TST-005). Verification: `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 documentation\development-setup.md`. Status: partial (line 103 is stale, R-09. Lines 109 to 111 name the right settings, but they state the scope wrongly.)
- [ ] T011 [US2] [FR-002, FR-005] Modify lines 122, 124, and 127, and delete line 125 (plan M-14, M-15). Files: `documentation\development-setup.md`. Acceptance: The browser section names the health check, the browser download, the report, and the account checks. The browser child process receives no uv setting. The username is set, not kept (checks TST-002 and TST-005). Verification: `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 documentation\development-setup.md`. Status: partial (line 125 is an editorial sentence. Line 127 says "keeps".)
- [ ] T013 [US2] [FR-001, FR-003, FR-004, FR-005, FR-006, FR-007] Compare each name, condition, and report line of `design/contracts/bootstrap-installer-flow.md` with the guide and with `scripts/bootstrap_worktree.py`. Files: `documentation\development-setup.md` (read), `scripts/bootstrap_worktree.py` (read). Acceptance: Each contract row for a setting appears in the guide with the same name and condition. Each setting name in the guide appears in the script. Verification: `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 documentation\development-setup.md`. Status: partial (the contract rows are not all in the guide until T007 runs). The script side is verified-present (R-15 to R-33).

## Phase 4: User Story 3 - Confirm the writing score and the change scope

- [ ] T012 [P] [US3] [FR-009] Create the fragment `changelog.d\issue-4879-development-setup-installer.md` (plan M-17). Files: `changelog.d\issue-4879-development-setup-installer.md`. Acceptance: The fragment holds one `###` heading and one `- **Fixed**:` bullet that names issue #4879 (check TST-009). Verification: `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 changelog.d\issue-4879-development-setup-installer.md`. Status: absent (no fragment for 4879 on `main`, R-53).
- [ ] T014 [US3] [FR-008] Run the STE gate on the changed guide and on the fragment. Files: `documentation\development-setup.md`, `changelog.d\issue-4879-development-setup-installer.md`. Acceptance: Each file scores 80 or above (check TST-001). Verification: `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 documentation\development-setup.md changelog.d\issue-4879-development-setup-installer.md`. Status: open.
- [ ] T015 [US3] [FR-009] Run the existing guard that reads the guide. Files: `tests/guardrails/test_container_policy_docs.py` (read). Acceptance: The guard passes, and no case skips the guide (check TST-010). Verification: `python -m pytest tests/guardrails/test_container_policy_docs.py`. Status: open.
- [ ] T016 [US3] [FR-009] Check the list of changed files. Files: none. Acceptance: The list holds exactly the guide and the fragment (check TST-009). Verification: `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 documentation\development-setup.md`. Status: open.

## Phase 5: Final tasks

- [ ] T-LOCAL-GATES [FR-008, FR-009] Run each local gate of the table that applies to the changed files. Files: `documentation\development-setup.md`, `changelog.d\issue-4879-development-setup-installer.md`. Acceptance: The STE gate, the guard test, and the test quality check each exit 0. The pull request body lists each gate that does not apply, with its reason (plan Constitution Check). Verification: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt`. Status: open.
- [ ] T-PR [FR-009] Commit the two files with the message `docs(setup): describe the locked uv sync in the bootstrap section`. Push the branch `fix/4879-development-setup-installer`. Open the pull request with the body `Closes #4879`. Files: `documentation\development-setup.md`, `changelog.d\issue-4879-development-setup-installer.md`. Acceptance: The pull request title passes the `Conventional Commits PR title` check. The body lists the changed files, the local gate results, and the reason that no changelog exemption applies (D-8). Verification: the same `test-quality-analyzer` command as T-LOCAL-GATES, run after the commit and before the push. Status: open.
- [ ] T-REMOTE-CI [FR-008] Wait for the CI run of the pull request that T-PR opens. Files: none. Acceptance: Each required check reports SUCCESS, including `ste-lint / STE compliance` and `Conventional Commits PR title`. Verification: `gh pr checks` for the pull request number that T-PR reports, with `--watch`. Status: open.
- [ ] T-MERGE [FR-009] After the remote CI passes and the orchestrator authorizes the merge, add the `auto-merge` label. Files: none. Acceptance: The pull request state becomes MERGED. The branch and the worktree are removed. Verification: `gh pr view` for the pull request number that T-PR reports, with `--json state,mergedAt`. Status: open.

## Dependencies and Execution Order

- T001 comes first.
- The guide edits share one file, so they run in one sequence. Run them from the bottom of the file to the top: T011, T009, T008, T007, T006, T005, T004, T003, and T002. Each edit then keeps the `main` line numbers of the edits above it.
- T010 reads the same lines and runs after T002 to T009 and T011, to confirm the kept text.
- T012 is independent of the guide edits and may run in parallel with them.
- T013 runs after T007 to T011.
- T014 to T016 run after every edit.
- The final tasks run in the order that the names show.

## Requirement Coverage

| Requirement | Tasks | Checks |
|-------------|-------|--------|
| FR-001 | T002, T003, T013 | TST-003 |
| FR-002 | T002, T004, T006, T008, T009, T011, T013 | TST-002 |
| FR-003 | T003, T010, T013 | TST-004 |
| FR-004 | T010, T013 | TST-008 |
| FR-005 | T007, T008, T009, T011, T013 | TST-005 |
| FR-006 | T004, T013 | TST-006 |
| FR-007 | T005, T013 | TST-007 |
| FR-008 | T014, T-LOCAL-GATES | TST-001 |
| FR-009 | T012, T015, T016, T-PR | TST-009, TST-010 |
