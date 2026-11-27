# Tasks: Native Report Failure-Boundary Tests

**Input**: `spec.md`, `plan.md`, `design/research.md`, `design/quickstart.md`.

**Status values**: `absent` means GitHub and the chain tip hold none of the change. `partial` means the chain tip holds part of the change, and GitHub holds none of it. `open` means the task is a check that has not run.

**Format**: `T### [P?] [Requirements] Description`. `[P]` marks a task that can run in parallel with other `[P]` tasks.

## Phase 1: Prerequisite

- [ ] T001 [FR-014] Confirm that GitHub holds the chain. Files: none. Acceptance: GitHub returns commit `07cf3eec5eafbc131091fb5debf9f20036f293d9`, and the branch tree lists the three hardware test modules. Verification: `gh api repos/jmorrison-juniper/MistHelper/commits/07cf3eec5eafbc131091fb5debf9f20036f293d9 --jq .sha` (remote read, no local gate applies). Status: absent (research R28 to R31). Depends on: decision D-2.

## Phase 2: Test Changes

- [ ] T002 [FR-006, FR-011] Replace `class ReportRun` with `_synthetic_identity` and `create_report_run` in `tests/unit/websocket_streams/web/hardware/test_report.py`. Acceptance: `create_report_run` is module-level, has four parameters, fits in 25 lines, and calls `SessionArtifactService` directly. `_synthetic_identity` holds the identity and ledger values. Verification: `python -m pytest tests/unit/websocket_streams/web/hardware/test_report.py`. Status: absent (chain tip holds `class ReportRun` at line 37). Depends on: T001.

- [ ] T003 [P] [FR-001, FR-002, FR-003] Edit `tests/unit/websocket_streams/web/hardware/test_normalization.py`. Restore `test_empty_body_cannot_become_zero_module_inventory` to `normalize("", native_format)` with `match="empty"`. Add `test_empty_raw_reply_is_refused_at_byte_boundary`, which passes `b""` to `HardwareXmlSupport.Decoder.decode_output`. Add `HardwareXmlPreset` and `HardwareXmlSupport` to the preset import at lines 14 to 16. Verification: `python -m pytest tests/unit/websocket_streams/web/hardware/test_normalization.py`. Status: partial (chain tip holds the marker-only `b""` decode at line 83). Depends on: T001.

- [ ] T004 [FR-001, FR-002, FR-005, FR-006] Rewrite `test_empty_body_refuses_native_publication_and_report` in `tests/unit/websocket_streams/web/hardware/test_report.py`. Acceptance: the test passes `b""` to `HardwareXmlSupport.Decoder.decode_output` with `HardwareXmlPreset.COMMANDS[native_format]` and expects `HardwareOutputError`. It then calls `create_report_run(tmp_path, native_format, native="")` and asserts `output_failed`, no master report, and no native file. Verification: `python -m pytest tests/unit/websocket_streams/web/hardware/test_report.py`. Status: partial (chain tip holds the marker-only decode at line 85). Depends on: T002.

- [ ] T005 [FR-004, FR-006] Rename the call in `test_malformed_json_refuses_report_and_preserves_native` in `tests/unit/websocket_streams/web/hardware/test_report.py`. Keep the precondition `with pytest.raises(json.JSONDecodeError): json.loads(native)` at line 96. Keep the manifest, native-byte, and master-report assertions. Verification: `python -m pytest tests/unit/websocket_streams/web/hardware/test_report.py`. Status: partial (chain tip holds the precondition, but the call still uses `ReportRun`). Depends on: T002.

- [ ] T006 [FR-003] Keep the cause assertion `assert isinstance(error.value.__cause__, json.JSONDecodeError)` in `tests/unit/websocket_streams/web/hardware/test_normalization.py` at line 92. Verification: `python -m pytest tests/unit/websocket_streams/web/hardware/test_normalization.py`. Status: partial (chain tip holds the assertion). Depends on: T003.

- [ ] T007 [FR-007, FR-011] Edit `tests/unit/websocket_streams/web/hardware/test_contracts.py`. Rename the import (line 24) and the call (line 120) to `create_report_run`. Keep `assert manager.started is True` at line 59. Verification: `python -m pytest tests/unit/websocket_streams/web/hardware/test_contracts.py`. Status: partial (chain tip holds the exact assertion, and the rename is absent). Depends on: T002.

- [ ] T008 [FR-011] Rename the import at line 25 and the call at line 177 in `tests/unit/websocket_streams/web/hardware/test_cli.py` to `create_report_run`. Verification: `python -m pytest tests/unit/websocket_streams/web/hardware/test_cli.py`. Status: absent. Depends on: T002.

## Phase 3: Records and Notes

- [ ] T009 [P] [FR-015] Add `changelog.d/issue-4783-native-report-failure-boundary-tests.md`. Acceptance: one `### Fixed` heading and one bullet that names issue #4783. Verification: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py` (the fragment policy guard reads the directory, as `copilot-instructions.md` records for issue #2541). Status: absent.

- [ ] T010 [FR-012, FR-013] Check each changed line. Acceptance: each changed line has an inline comment. Each new function has 25 lines or fewer and five parameters or fewer. The publication helper logs before and after the publication call. Verification: `python -m black --check .` (format check of the same changed files). Status: open. Depends on: T002 to T008.

- [ ] T011 [FR-016] Record the analyzer blind spot and the six-child folder as separate follow-ups. Acceptance: `analysis.md` and the pull request body name each follow-up, and this change makes no fix for either. Verification: `python -m pytest tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides` (confirms the gate documentation still matches the live job). Status: open.

- [ ] T012 [FR-009, FR-010] Confirm that the change touches no protected path. Acceptance: the fix commit changes no path under `src/`, and the baseline and settings file keep their blob SHAs. Verification: `git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" diff --quiet origin/main -- .github/test-quality-baseline.json .github/test-quality-config.toml` (exit code 0 after the rebase). Status: open. Depends on: T002 to T008.

## Phase 4: Final Tasks

- [ ] T-LOCAL-GATES [FR-008, FR-009, FR-010, FR-012, FR-013] Run each applicable gate in the order that `quickstart.md` Scenario 4 lists. Stop at the first failed analyzer command. Applicable gates: preflight guard, compile, Ruff, Black, the four changed test modules, and Bandit on the hardware folder. Also run coverage, both analyzer scopes, the two unit shards, and `symbol-diff`. Acceptance: each applicable gate reports its expected result. Both analyzer scopes print `gate: 0 new findings vs baseline`. Status: open. Not applicable gates, with reason:
  - Types: `MYPY_PATHS` excludes `tests/` (`ci.yml` line 93).
  - Radon: `RADON_PATHS` excludes the hardware tests (`ci.yml` line 99).
  - Vulture: `VULTURE_PATHS` excludes `tests/` (`ci.yml` line 101).
  - Docstrings: `PYDOCSTYLE_PATHS` and `INTERROGATE_PATHS` exclude `tests/` (`ci.yml` lines 104 and 107).
  - Pylint: the scope is `src/` only (`ci.yml` line 78).
  - Safe sweep, dependency audit, menu reference, STE, ops portal, ops platform, and container: no matching change.

- [ ] T-PR [FR-014, FR-015] Open the pull request after the human records D-2 option 1 and T-LOCAL-GATES passes. Steps:
  1. Create branch `fix/4783-native-report-failure-boundary-tests` from main in a worktree.
  2. Apply the chain commits in order. Resolve conflicts per file.
  3. Add the fix commit `test(websocket): cover native report failure boundaries`.
  4. Add the changelog fragment. Copy this record to the route.
  5. Push the branch.
  6. Open the pull request with the title `feat(websocket): add optional transceiver master report`.

The body contains `Closes #4783`, `Refs #4773`, each gate result, the symbol-diff output, and the Principle IV exception. Verification: `gh pr view --json title,body` run from the branch worktree (remote read). Status: open. Depends on: T-LOCAL-GATES and D-2.

- [ ] T-REMOTE-CI [FR-008] Watch the CI run for the pull request with `gh pr checks --watch` from the branch worktree. Acceptance: each required check passes, including the `Test quality ratchet (gate)` job (`ci.yml` line 602) and CodeQL. If a check fails, file an issue with the full output before any fix, as `AGENTS.md` requires. Verification: `gh pr checks --watch` from the branch worktree. Status: open. Depends on: T-PR.

- [ ] T-MERGE [FR-014] Add the `auto-merge` label only after T-REMOTE-CI passes and the orchestrator authorizes the merge. Acceptance: `auto-merge.yml` squash-merges the pull request. Then remove the branch and the worktree. Principle IV steps 10 to 12 do not apply, because `container-build.yml` runs only for product files. Verification: `gh pr view --json state,mergedAt` run from the branch worktree (remote read). Status: open. Depends on: T-REMOTE-CI.

## Dependencies

- T001 blocks T002 to T008, T010, T011, and T012.
- T002 blocks T004, T005, T007, and T008.
- T003 and T009 run in parallel with T002.
- T-LOCAL-GATES waits for every task in Phase 2 and Phase 3.
- T-PR, T-REMOTE-CI, and T-MERGE run in order after T-LOCAL-GATES.

## Requirement Coverage

| Requirement | Tasks | Planned test |
| - | - | - |
| FR-001 | T003, T004 | `test_empty_raw_reply_is_refused_at_byte_boundary`, `test_empty_body_refuses_native_publication_and_report` |
| FR-002 | T003, T004 | The same two cases, with `b""` at the decoder |
| FR-003 | T003, T006 | `test_malformed_json_cannot_become_zero_module_inventory` |
| FR-004 | T005 | `test_malformed_json_refuses_report_and_preserves_native` |
| FR-005 | T004 | `test_empty_body_refuses_native_publication_and_report` |
| FR-006 | T002, T004, T005 | The three report and raw cases, through `create_report_run` or the decoder |
| FR-007 | T007 | `test_start_report_binding_precedes_artifact_creation` |
| FR-008 | T-LOCAL-GATES, T-REMOTE-CI | Both analyzer scopes |
| FR-009 | T012, T-LOCAL-GATES | Blob SHA check |
| FR-010 | T012 | `git diff` check on `src/` |
| FR-011 | T002, T007, T008 | `git grep -n ReportRun` returns no line in `tests/unit/websocket_streams/web/hardware` |
| FR-012 | T010 | Line and parameter check on `create_report_run` |
| FR-013 | T010 | Manual review of the changed lines |
| FR-014 | T001, T-PR, T-MERGE | Remote read commands |
| FR-015 | T009, T-PR | Changelog fragment check |
| FR-016 | T011 | Follow-up text in `analysis.md` and the pull request body |
