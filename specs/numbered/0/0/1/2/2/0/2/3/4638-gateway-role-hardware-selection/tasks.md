# Tasks: Add explicit gateway role and hardware selection

**Input**: Numeric record at `specs/numbered/0/0/1/2/2/0/2/3/4638-gateway-role-hardware-selection/`. Parity map: `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md`, lines 57 and 58.

**Prerequisites**: plan.md (required), spec.md (required), design/research.md, design/data-model.md, design/contracts/

**Tests**: Required. The issue test plan asks for tests before implementation. Write each test and see it fail before its code task.

**Status values**: `open` for a non-code task. `absent` for a code change that does not exist on main.

## Phase 1: Prerequisites

- [ ] T001 Confirm issue 4634 field semantics, issue 4636 merge, and issue 4637 merge. Rebase the branch onto `main`.
  - Requirements: FR-005, FR-007, FR-012, A-1.
  - Files: none changed.
  - Acceptance: Issue 4634 holds one field-semantics entry for each verified row. The `state/` package exists on `main`.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py`
  - Status: open.
  - Depends on: none.

## Phase 2: Tests first

- [ ] T002 [P] Write the seventeen hardware tests in `tests/integration/web_portal/cisco_config_converter/test_hardware.py`.
  - Requirements: FR-001 to FR-012, FR-019, FR-020. Tests: TST-01 to TST-17 in analysis.md.
  - Files: `tests/integration/web_portal/cisco_config_converter/test_hardware.py` (add).
  - Acceptance: Each test fails before T005 to T007. The module makes no socket connection and writes no file.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/test_hardware.py`
  - Status: absent.
  - Depends on: T001.

- [ ] T003 [P] Write the eight route tests in `tests/integration/web_portal/cisco_config_converter/test_routes.py`.
  - Requirements: FR-013 to FR-018. Tests: TST-18 to TST-25 in analysis.md.
  - Files: `tests/integration/web_portal/cisco_config_converter/test_routes.py` (modify).
  - Acceptance: The form posts the new fields. The retired `type` field returns HTTP 400. Each route test fails before T009.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py`
  - Status: absent.
  - Depends on: T001.

- [ ] T004 [P] Update the unit tests for the new import path and the new `SourceConfiguration.read` signature.
  - Requirements: FR-015.
  - Files: `tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py` (modify).
  - Acceptance: Imports name `conversion.common.dns` and `state.intake`. The `hub` expectation at line 39 moves to the hardware tests. The DNS expectation has no template type.
  - Verification: `python -m pytest tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py`
  - Status: absent.
  - Depends on: T001.

## Phase 3: Evidence, mapping, and package move

- [ ] T005 Move the DNS converter into `conversion/common/dns.py` and delete `conversion.py`.
  - Requirements: FR-015, FR-018.
  - Files: `src/interfaces/portals/cisco_config_converter/conversion.py` (delete), `conversion/__init__.py` (add), `conversion/common/__init__.py` (add), `conversion/common/dns.py` (add).
  - Acceptance: The DNS behavior and tests stay unchanged. The known-gap sentence names only the hardware selection as new scope. Each new line has an inline comment.
  - Verification: `symbol-diff --base origin/main src/interfaces/portals/cisco_config_converter/conversion/common/dns.py`
  - Status: absent.
  - Depends on: T002, T003, T004.

- [ ] T006 Add the evidence register in `conversion/hardware/register.py` and `conversion/hardware/__init__.py`.
  - Requirements: FR-008, FR-009, FR-010, FR-012, FR-020.
  - Files: `conversion/hardware/__init__.py` (add), `conversion/hardware/register.py` (add).
  - Acceptance: The register holds the rows in `contracts/hardware-register.md`. Each row cites local lines. The register exposes `CURRENT_REVISION`, `options`, and `row`.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/test_hardware.py`
  - Status: absent.
  - Depends on: T005.

- [ ] T007 Add `HardwareMapping.attach` in `conversion/hardware/mapping.py`.
  - Requirements: FR-001 to FR-007, FR-010 to FR-012, FR-014.
  - Files: `conversion/hardware/mapping.py` (add).
  - Acceptance: `attach` returns the blocker codes in `contracts/proposal-json.md`. The function logs before and after evaluation. Each function has five parameters or fewer.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/test_hardware.py`
  - Status: absent.
  - Depends on: T006.

- [ ] T008 Update `state/intake.py` and `state/proposal.py` from issue 4636.
  - Requirements: FR-001, FR-005, FR-016.
  - Files: `src/interfaces/portals/cisco_config_converter/state/intake.py` (modify), `src/interfaces/portals/cisco_config_converter/state/proposal.py` (modify).
  - Acceptance: `SourceConfiguration.read` takes no `kind` argument. `GatewayTemplate.type` is `NotRequired`. The class names and digest behavior stay unchanged.
  - Verification: `python -m pytest tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py`
  - Status: absent.
  - Depends on: T001.

## Phase 4: Route and page

- [ ] T009 Update `routes.py` for the selection parser, preview composition, and the review gate.
  - Requirements: FR-001 to FR-004, FR-013, FR-014, FR-016, FR-018.
  - Files: `src/interfaces/portals/cisco_config_converter/routes.py` (modify).
  - Acceptance: `ConverterInput.selection` validates each field. `preview` calls `HardwareMapping.attach`. `review` returns HTTP 409 for a blocked proposal. `page` passes the register to the template. No route is registered on the shared portal.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py`
  - Status: absent.
  - Depends on: T007, T008.

- [ ] T010 [P] Update `presentation/converter.html` with the stable controls and the register data block.
  - Requirements: FR-017.
  - Files: `src/interfaces/portals/cisco_config_converter/presentation/converter.html` (modify).
  - Acceptance: Each control has the `data-testid` value in `contracts/portal-selection.md`, section Stable selectors. Each control has a visible label. The retired `cisco-type` select is removed.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py`
  - Status: absent.
  - Depends on: T009.

- [ ] T011 Update `presentation/converter.js` for dynamic options, the `ports` JSON, and the reset on change.
  - Requirements: FR-014, FR-017.
  - Files: `src/interfaces/portals/cisco_config_converter/presentation/converter.js` (modify).
  - Acceptance: The script builds model options from the family and port rows from the model. The script sends `ports` as a JSON list. The script resets the proposal on `input` and `change`.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py`
  - Status: absent.
  - Depends on: T010.

## Phase 5: Documentation and audit

- [ ] T012 Add the changelog fragment `changelog.d/issue-4638-gateway-role-hardware-selection.md`.
  - Requirements: Copilot instructions line 451 (changelog rule).
  - Files: `changelog.d/issue-4638-gateway-role-hardware-selection.md` (add).
  - Acceptance: The fragment has one `###` heading. It has one `Added` bullet and one `Changed` bullet. Each bullet names issue 4638.
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4638-gateway-role-hardware-selection.md`
  - Status: absent.
  - Depends on: T011.

- [ ] T013 Add one browser selector test to `tests/e2e/web_portal/test_portal_smoke.py` after issue 4647 merges.
  - Requirements: FR-017. Copilot instructions line 303.
  - Files: `tests/e2e/web_portal/test_portal_smoke.py` (modify).
  - Acceptance: The test selects Standalone, SRX, and SRX300 with the keyboard. It reads each `data-testid` value in `contracts/portal-selection.md`, section Stable selectors.
  - Verification: `python -m pytest tests/e2e/web_portal/test_portal_smoke.py`
  - Status: absent.
  - Depends on: T011, issue 4647 merged.

- [ ] T014 Audit inline comments, action logs, ASCII output, and function limits in each changed module.
  - Requirements: Constitution Principles IV, V, VI, and VII.
  - Files: each file under `src/interfaces/portals/cisco_config_converter/` that this record changes.
  - Acceptance: Each executable line has an inline comment. Each action has an `info` line before and a `debug` line after. Each function has complexity 10 or less.
  - Verification: `radon cc src/interfaces/portals/cisco_config_converter -j | complexity-gate --max 10`
  - Status: absent.
  - Depends on: T011.

## Final Tasks

- [ ] T-LOCAL-GATES Run each applicable gate from the local gates table in `.github/copilot-instructions.md`.
  - Run each gate that applies. `design/quickstart.md`, Scenario 7, lists the exact commands.
  - The Types gate reads `MYPY_PATHS` from `ci.yml` line 93. The Dead code gate reads `VULTURE_PATHS` from line 101.
  - Also run the two `pytest-chunks` commands, the test quality gate, and the STE gate on each changed Markdown file.
  - Symbols gate: run `symbol-diff --base origin/main <file>` for each changed file.
  - Not applicable: Safe sweep and Menu reference, because no menu changes.
  - Not applicable: Dependency audit, because no dependency changes. Ops portal and Ops platform, because those trees stay unchanged.
  - Requirements: all.
  - Verification: `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=`
  - Status: open.
  - Depends on: T012, T013, T014.

- [ ] T-PR Commit with a Conventional Commits message, push `feat/4638-gateway-role-hardware-selection`, and open the pull request.
  - Requirements: AGENTS.md pull request section (line 221). Copilot instructions line 431 (issue and label rules).
  - Files: the changed files only. Add files by explicit path.
  - Acceptance: The commit subject is `feat(web-portal): add explicit gateway role and hardware selection`. The pull request body contains `Closes #4638` and the gate results. The `in-progress` label is added before the branch is created. The overlap check shows no open file conflict.
  - Verification: `python -m py_compile MistHelper.py`
  - Status: open.
  - Depends on: T-LOCAL-GATES.

- [ ] T-REMOTE-CI Watch the continuous integration run for the pull request.
  - Requirements: AGENTS.md (line 284) and the CI workflow table in the copilot instructions.
  - Acceptance: Each required check passes on the latest commit. A failure opens a new issue with the full log before any fix.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/test_hardware.py`
  - Status: open.
  - Depends on: T-PR.

- [ ] T-MERGE Enable auto-merge after the remote checks pass and the orchestrator authorizes the merge.
  - Requirements: AGENTS.md merge section (line 233). Constitution Principle IV steps 9 to 12.
  - Acceptance: The squash commit title uses the pull request title. The branch and worktree are removed after the merge. The container build on `main` reports the merged commit SHA.
  - Verification: `python -m py_compile MistHelper.py`
  - Status: open.
  - Depends on: T-REMOTE-CI.

## Dependencies & Execution Order

- T001 blocks T002, T003, T004, and T008.
- T002, T003, and T004 block T005. T005 blocks T006. T006 blocks T007. T007 and T008 block T009.
- T009 blocks T010. T010 blocks T011. T011 blocks T012, T014, and T013.
- T-LOCAL-GATES waits for T012, T013, and T014. T-PR, T-REMOTE-CI, and T-MERGE follow in order.

## Requirement Coverage

| Requirement | Tasks | Tests |
| --- | --- | --- |
| FR-001 | T002, T007, T008, T009 | TST-03, TST-04, TST-05, TST-21 |
| FR-002 | T002, T007, T009 | TST-03, TST-21 |
| FR-003 | T002, T006, T007, T009 | TST-01, TST-02, TST-06, TST-08 |
| FR-004 | T002, T007, T009 | TST-10, TST-11, TST-12, TST-13 |
| FR-005 | T002, T007, T008 | TST-01, TST-04 |
| FR-006 | T002, T007 | TST-05 |
| FR-007 | T002, T007 | TST-04 |
| FR-008 | T002, T006, T007 | TST-06, TST-07, TST-08 |
| FR-009 | T002, T006, T007 | TST-09 |
| FR-010 | T002, T006, T007 | TST-02, TST-10 |
| FR-011 | T002, T007 | TST-11, TST-12, TST-13, TST-14 |
| FR-012 | T002, T006, T007 | TST-15 |
| FR-013 | T003, T009 | TST-18 |
| FR-014 | T003, T009, T011 | TST-19 |
| FR-015 | T004, T005, T003 | TST-23 and the unit test file |
| FR-016 | T003, T008, T009 | TST-20 |
| FR-017 | T003, T010, T011, T013 | TST-22, TST-26 |
| FR-018 | T005, T009 | TST-25 |
| FR-019 | T002 | TST-17 |
| FR-020 | T002, T006 | TST-16 |
