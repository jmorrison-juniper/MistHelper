# Tasks: Windows Symlink Privilege in the Spec-Route Contract Guard

**Input**: Design documents in `specs/numbered/0/0/1/2/3/1/0/3/4778-windows-symlink-privilege/`

**Prerequisites**: `plan.md`, `spec.md`, `design/research.md`, `design/contracts/link-fallback.md`, and `design/contracts/selection-rejection.md`

**Tests**: TEST-01 modifies the symlink case. TEST-02, TEST-03, and TEST-04 are new test methods. Each new method fails before T004 adds `link_selection`.

**Ownership**: Change only the files that each task names. Add each file by explicit path.

**Environment**: Use the Python 3.15.2 environment of the worktree. Put PowerShell 7 on PATH before the guard runs.

## Format: `[ID] [P?] [FR] Description`

- **[P]**: The task can run in parallel. It edits a different file, or it reads only.
- **[FR]**: The requirement IDs that the task serves.
- **Status**: One of `open`, `verified-present`, `partial`, or `absent`.

## Phase 1: Verify and Baseline

- [ ] T001 [P] [FR-006] Verify that the reparse-point checks exist on `main`. Files: `.specify/scripts/powershell/common.ps1` (lines 258-259) and `.specify/scripts/powershell/spec-route.ps1` (line 110). Acceptance: both checks match research rows RC-12, RC-13, and RC-15. Verify: `python -m pytest tests/guardrails/test_spec_route_contract.py`. Status: verified-present.

- [ ] T002 [P] [FR-011] Record the baseline on the Windows host with the unchanged test file. Files: `tests/guardrails/test_spec_route_contract.py` (read only). Acceptance: setup fails at line 296 with WinError 1314, as issue #4778 reports. Verify: `python -m pytest tests/guardrails/test_spec_route_contract.py`. Status: open.

## Phase 2: Tests First

- [ ] T003 [FR-002, FR-003, FR-004, FR-008] Add the class `TestLinkSelectionFallback` after line 301 of `tests/guardrails/test_spec_route_contract.py`. Its methods are `test_uses_junction_after_privilege_error` (TEST-02), `test_skips_when_junction_fails` (TEST-03), and `test_raises_other_os_errors` (TEST-04). Acceptance: each method fails with `AttributeError` before T004. Each executable line has an inline comment. Verify: `python -m pytest tests/guardrails/test_spec_route_contract.py`. Status: open.

## Phase 3: Implementation

- [ ] T004 [FR-001, FR-002, FR-003, FR-004, FR-008, FR-011] Add `import logging` after line 5. Add the class attribute `PRIVILEGE_NOT_HELD = 1314` and the method `link_selection` to `SpecCommandFixture` in `tests/guardrails/test_spec_route_contract.py`. The method goes after the `feature` method. Acceptance: the method returns `symlink` or `junction`. It raises other errors again and skips with the `mklink` output. It logs info before and debug after each attempt. Verify: `python -m pytest tests/guardrails/test_spec_route_contract.py`. Status: open.

- [ ] T005 [FR-001, FR-005, FR-011] Replace line 296 of `tests/guardrails/test_spec_route_contract.py` with `fixture.link_selection(selected, parent)`. Keep the parametrize list and lines 298-301 unchanged. Acceptance: the three assertions match the current file. Verify: `python -m pytest tests/guardrails/test_spec_route_contract.py`. Status: open.

- [ ] T006 [P] [FR-009] Update `documentation/development-setup.md`. Add a PowerShell 7 row after line 15. Add a note under Step 4 (lines 168-174) that names the junction fallback and the Ubuntu shard. Acceptance: the note states what the fixture does when the symlink privilege is missing. Verify: `ste-linter --config .ste-linter.toml --min-score 80 documentation/development-setup.md`. Status: open.

- [ ] T007 [P] [FR-010] Confirm that `changelog.d/README.md` line 58 applies, and draft the reason for the pull request. Files: `changelog.d/README.md` (read only). Acceptance: the pull request body contains the reason. Verify: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`. Status: open.

- [ ] T008 [FR-006, FR-007] Run the red proof on the task branch. Temporarily remove the `ReparsePoint` condition at `.specify/scripts/powershell/common.ps1` line 258. Run the guard file and record the failures. Revert the edit. Acceptance: at least one symlink-case assertion fails, and `git diff -- .specify` shows no change after the revert. Verify: `python -m pytest tests/guardrails/test_spec_route_contract.py`. Status: open.

## Phase 4: Gates and Delivery

- [ ] T-LOCAL-GATES [FR-011, FR-009, FR-010] Files: `tests/guardrails/test_spec_route_contract.py` and `documentation/development-setup.md`. Run each applicable gate in the Gate Map of `plan.md`. Run `python -m pytest tests/guardrails/test_spec_route_contract.py -k unsafe_feature_selection --log-cli-level=INFO -rs` on the Windows host, and record the link kind. Acceptance: each applicable gate reports its expected result, and the link kind appears in the pull request. Verify: `python -m ruff check .`. Status: open.

- [ ] T-PR [FR-010] Files: `tests/guardrails/test_spec_route_contract.py`, `documentation/development-setup.md`, and `specs/numbered/0/0/1/2/3/1/0/3/4778-windows-symlink-privilege/`. Commit these files by explicit path. Use the subject `fix(tests): use a junction when the symlink privilege is missing`. Run the test-quality ratchet, push `fix/4778-windows-symlink-privilege`, and open the pull request. The body contains `Closes #4778`, the gate results, the link kind, and the changelog reason. Verify: `python -m pytest tests/guardrails/test_spec_route_contract.py`. Status: open.

- [ ] T-REMOTE-CI [FR-001, FR-002, FR-003] Files: `tests/guardrails/test_spec_route_contract.py`, as CI runs it. Wait for each required check to finish. Confirm that the Ubuntu shard passes with the real symlink case. Verify: `gh pr checks --watch`, for the pull request of the current branch. Status: open.

- [ ] T-MERGE [FR-007] Files: the same three paths as T-PR. Add the `auto-merge` label only after every check passes and the orchestrator authorizes the merge. Verify: `gh pr view --json labels,state`, for the pull request of the current branch. Status: open.

## Dependencies and Execution Order

- T001 and T002 run first. Both read only.
- T003 needs T001 and T002.
- T004 needs T003. T005 needs T004. T008 needs T005.
- T006 and T007 run in parallel with T003 through T005.
- T-LOCAL-GATES needs T005, T006, T007, and T008. T008 must end with the revert.
- T-PR needs T-LOCAL-GATES. T-REMOTE-CI needs T-PR. T-MERGE needs T-REMOTE-CI and the orchestrator authorization.

## Guard Rules

- Run the guard file after each edit of `tests/guardrails/test_spec_route_contract.py`.
- Add each file by explicit path before the commit.
- Stop at the red proof if T008 leaves any edit in `.specify`.
