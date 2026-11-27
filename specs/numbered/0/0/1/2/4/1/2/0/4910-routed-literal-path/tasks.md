# Tasks: Restore -LiteralPath in the setup scripts

**Input**: Design documents in `specs/numbered/0/0/1/2/4/1/2/0/4910-routed-literal-path/`

**Prerequisites**: `plan.md`, `spec.md`, `design/research.md`, `design/quickstart.md`, `design/contracts/prerequisite-output.md`

**Tests**: The specification requires tests. Write each test task first, and run it before the fix. The bracket behavior tests and the guard must fail first (T003).

**Ownership**: Do not modify `.specify/feature.json`, `README.md`, or `CHANGELOG.md`. Do not edit `.specify/integrations/`. Add files by explicit path.

**Environment**: Run Python tests from the repository `.venv`. The behavior tests need `pwsh` 7 on `PATH`.

## Format

Each task line holds a task ID, an optional parallel marker, an optional story label, and a description.

- **P marker**: The literal text `[P]`. The task can run in parallel. It edits a different file, and it has no open dependency.
- **Story label**: The literal text `[US1]`, `[US2]`, or `[US3]`. It names the user story that the task serves. Setup and final tasks have no story label.
- **Status**: `open` means the task has not started. `absent` means the required code is missing on `main`, as verified by `design/research.md`. `verified-present` means the code exists on `main`.

## Phase 1: Tests First

**Purpose**: Write the guard and the behavior tests. Run them before any script changes.

- [ ] T001 [P] [US2] Add the line-scan guard to `tests/guardrails/test_routed_core_port.py`: class `LiteralProbeScanner`, test `test_scoped_scripts_use_literal_probes`, test `test_unreadable_scoped_script_fails`, and test `test_literal_probe_scanner_flags_bare_forms`. Requirements: FR-006, FR-007, FR-008, FR-009. Acceptance: the guard reports examined counts and fails on bare probes. Verification: `python -m pytest tests/guardrails/test_routed_core_port.py`. Status: absent (RC-01 to RC-16).
- [ ] T002 [P] [US1] Add `test_bracket_folder_lists_optional_documents` and `test_bracket_folder_without_documents_lists_none` to `tests/guardrails/test_spec_route_contract.py`, each with a case for `check-prerequisites.ps1` and for `setup-tasks.ps1`. Requirements: FR-010. Acceptance: each listing case names `design/research.md` and `design/contracts`, and each empty case exits with code 0. Verification: `python -m pytest tests/guardrails/test_spec_route_contract.py`. Status: absent (RC-27 to RC-30).
- [ ] T003 [US1] [US2] Run both guard modules before any script change, and record the red result in the pull request. Requirements: FR-010, SC-001, SC-002. Depends on T001 and T002. Acceptance: the guard reports 10 bare lines among 26 examined lines, and the bracket listing cases fail. Verification: `python -m pytest tests/guardrails/test_routed_core_port.py tests/guardrails/test_spec_route_contract.py`. Status: open.

## Phase 2: Restore the Literal Probes

**Purpose**: Change each bare probe. Keep the `design/` paths. Add comments and logs to each touched block.

- [ ] T004 [P] [US1] Restore the literal probes in `.specify/scripts/powershell/check-prerequisites.ps1`. Lines 135, 136, 139, and 143 use `-LiteralPath`. Line 139 reads the contracts folder with `Get-ChildItem -LiteralPath`. Add inline comments and the info and debug logs to the block from line 133 to line 146. Requirements: FR-001, FR-002, FR-005, FR-011, FR-012. Depends on T003. Acceptance: the scanner reports no bare line in this file. Verification: `python -m pytest tests/guardrails/test_spec_route_contract.py`. Status: absent (RC-01 to RC-06, RC-60).
- [ ] T005 [P] [US1] Restore the literal probes in `.specify/scripts/powershell/setup-tasks.ps1`. Lines 56, 57, 58, and 61 use `-LiteralPath`. Line 58 reads the contracts folder with `Get-ChildItem -LiteralPath`. Add inline comments and the info and debug logs to the block from line 54 to line 62. Requirements: FR-003, FR-005, FR-011, FR-012. Depends on T003. Acceptance: the scanner reports no bare line in this file. Verification: `python -m pytest tests/guardrails/test_spec_route_contract.py`. Status: absent (RC-07 to RC-11, RC-60).
- [ ] T006 [P] [US3] Restore the literal probes in `.specify/scripts/powershell/create-new-feature.ps1`: lines 211 and 213 use `-LiteralPath`. Add inline comments and the info and debug logs to the block from line 211 to line 225. Requirements: FR-004, FR-011, FR-012. Depends on T003. Acceptance: the scanner reports no bare line in this file, and the generator tests pass. Verification: `python -m pytest tests/guardrails/test_spec_route_contract.py`. Status: absent (RC-12 to RC-15, RC-60).
- [ ] T007 [P] Add `changelog.d/issue-4910-routed-literal-path.md` with one `###` heading and one `Fixed` bullet that names issue #4910. Requirements: FR-013. Acceptance: the fragment passes the naming and content rules of the changelog guard. Verification: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`. Status: absent (RC-31, RC-32, RC-98).

## Phase 3: Verify the Fix

**Purpose**: Show the green result and the unchanged behavior.

- [ ] T008 [US1] [US2] [US3] Run both guard modules after the fix, and record the green result. Requirements: FR-011, SC-001, SC-002, SC-003. Depends on T004, T005, and T006. Acceptance: the guard reports 0 bare lines among 26 examined lines, and all tests in both modules pass. Verification: `python -m pytest tests/guardrails/test_routed_core_port.py tests/guardrails/test_spec_route_contract.py`. Status: open.

## Final Tasks

- [ ] T-LOCAL-GATES Run each local gate that applies to the changed files. Files: `.specify/scripts/powershell/check-prerequisites.ps1`, `.specify/scripts/powershell/setup-tasks.ps1`, `.specify/scripts/powershell/create-new-feature.ps1`, `tests/guardrails/test_routed_core_port.py`, `tests/guardrails/test_spec_route_contract.py`, and `changelog.d/issue-4910-routed-literal-path.md`. Requirements: SC-004. Depends on T007 and T008. Acceptance: each applicable gate passes, and the output of each command is recorded. The gate list is in `design/quickstart.md`, Scenarios 5 to 10. Verification: `python -m pytest tests/guardrails`. Status: open.
- [ ] T-PR Commit with the title `fix(spec-kit): restore -LiteralPath in the setup scripts`, push `fix/4910-routed-literal-path`, and open the pull request. Files: the six paths of T-LOCAL-GATES. The body holds `Closes #4910`, the file list, the gate results, and the rollback note. Requirements: FR-014, FR-015, SC-004. Depends on T-LOCAL-GATES. Acceptance: the file list equals the change map in `plan.md`. Verification: `python -m pytest tests/guardrails`. Status: open.
- [ ] T-REMOTE-CI Watch each required check with `gh pr checks --watch` on the pushed branch. Files: the six paths of T-LOCAL-GATES, as pushed. Record each check name and its result in the pull request. Requirements: SC-005. Depends on T-PR. Acceptance: the Quality Gates check, the Conventional Commits PR title check, the STE compliance check, and CodeQL pass. Verification: `python -m pytest tests/guardrails/test_routed_core_port.py`, run again on the pushed commit. Status: open.
- [ ] T-MERGE After the orchestrator authorizes the merge, add the `auto-merge` label and let the squash merge complete. Files: the six paths of T-LOCAL-GATES, on `main` after the merge. Then verify the squash commit on `main`, the closed issue #4910, and the dispatched `container-build.yml` run. Requirements: SC-005. Depends on T-REMOTE-CI. Acceptance: the merge commit holds the change map only. Verification: `python -m pytest tests/guardrails/test_spec_route_contract.py`, run on the merge commit. Status: open.

Warning: a squash merge cannot be undone in place. Reverting requires a new pull request. Add `auto-merge` only after every required check passes.

## Dependencies and Execution Order

- T001 and T002 run in parallel.
- T003 depends on T001 and T002.
- T004, T005, and T006 run in parallel after T003. Each edits a different file.
- T007 runs at any time, because it has no code dependency.
- T008 depends on T004, T005, T006, and T007.
- T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE run in that order.

## Guard Rules

- Run the guard modules after each edit of a scoped script.
- Add each new file by explicit path before the guard run.
- Commit the tests first, as the test quality ratchet requires (`.github/copilot-instructions.md`, section Test quality ratchet).
