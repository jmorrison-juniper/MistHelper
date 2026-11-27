# Tasks: MSP inventory batch coverage

**Input**: Numeric record `specs/numbered/0/0/1/2/2/3/1/3/4708-msp-inventory-reporting/`.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, `design/data-model.md`, `design/contracts/console.md`, and `design/contracts/export.md`.

**Format**: `[ID] [P?] [Story] Description`. Each task lists its requirement IDs, its exact paths, its acceptance statement, its verification command, and its status. A status is `open`, `verified-present`, `partial`, or `absent`.

**Tests**: Required. Each new test covers a defect in this record, or it guards behavior that must not change.

## Phase 1: Foundation

- [ ] T001 [US1] Confirm the defect on `main`. Keep the legacy commits as reference only.
  - Requirements: FR-011, SC-001.
  - Paths: `src/mist/resources/inventory/org_device_inventory_msp.py` (lines 466, 480, and 516 on `main`).
  - Acceptance: Remote checks R-14, R-15, and R-16 match on `main`. No legacy commit reaches the branch.
  - Verification: `python -m pytest tests/unit/inventory/test_org_device_inventory_msp.py`
  - Status: verified-present

- [ ] T002 [US1] Add the `block_network` fixture at the end of the test module.
  - Requirements: FR-007.
  - Paths: `tests/unit/inventory/test_org_device_inventory_msp.py` (append only).
  - Acceptance: The fixture makes socket creation and DNS lookup raise. The fixture imports `socket` inside its body. Existing import lines stay unchanged.
  - Verification: `python -m pytest tests/unit/inventory/test_org_device_inventory_msp.py`
  - Status: open

## Phase 2: User Story 1, accurate batch coverage

- [ ] T003 [US1] Append the five batch-count tests to the test module.
  - Tests: `test_execute_msp_footer_reports_complete_coverage`, `test_execute_msp_footer_reports_partial_skip_and_failure`, `test_execute_msp_continues_after_earlier_failure`, `test_execute_msp_zero_successes_writes_no_combined_reports`, and `test_execute_msp_empty_successful_result_counts_as_success`.
  - Requirements: FR-001, FR-002, FR-005, FR-006, FR-007, SC-001, SC-003.
  - Paths: `tests/unit/inventory/test_org_device_inventory_msp.py` (append only).
  - Acceptance: On `main`, the partial, continuation, and zero-success tests fail. The complete and empty-result tests pass.
  - Verification: `python -m pytest tests/unit/inventory/test_org_device_inventory_msp.py`
  - Status: open

- [ ] T004 [US1] Add `_COMPLETE_COVERAGE_LABEL`, `_BatchCoverage`, and `_announce_batch_coverage`. Update `execute_msp` and `_process_org`.
  - Requirements: FR-001, FR-002, FR-003, FR-006, SC-001.
  - Paths: `src/mist/resources/inventory/org_device_inventory_msp.py` (constant near line 22, new class after line 52, `_process_org` at line 469, and `execute_msp` at line 502).
  - Acceptance: The footer text matches `design/contracts/console.md`. The skipped line matches the same contract. `execute_msp` and `_announce_batch_coverage` each stay at 25 lines or fewer.
  - Verification: `python -m pytest tests/unit/inventory/test_org_device_inventory_msp.py`
  - Status: open

## Phase 3: User Story 2, partial combined reports

- [ ] T005 [US2] Append `test_execute_msp_partial_reports_carry_label_and_filename_marker` to the test module.
  - Requirements: FR-004, FR-008, SC-002, SC-003, SC-004.
  - Paths: `tests/unit/inventory/test_org_device_inventory_msp.py` (append only).
  - Acceptance: On `main`, the heading assertions and the file name assertions fail.
  - Verification: `python -m pytest tests/unit/inventory/test_org_device_inventory_msp.py`
  - Status: open

- [ ] T006 [US2] Pass the label and the file marker through the combined-report functions.
  - Requirements: FR-004, FR-005, FR-008, SC-002, SC-003, SC-004.
  - Paths: `src/mist/resources/inventory/org_device_inventory_msp.py`.
  - Functions to change, with their line numbers on `main`:
    - `_print_combined_model_report` (line 183)
    - `_print_combined_version_report` (line 195)
    - `_print_and_export_pivot` (line 369)
    - `_display_combined_pivot_and_export` (line 391)
    - `_emit_combined_model` (line 411)
    - `_emit_combined_version` (line 422)
    - `_build_combined_reports` (line 433)
  - Acceptance: The complete output matches `main`. The partial output matches `design/contracts/console.md` and `design/contracts/export.md`. Each function keeps five parameters or fewer.
  - Verification: `python -m pytest tests/unit/inventory/test_org_device_inventory_msp.py`
  - Status: open

## Phase 4: User Story 3, assertions and release note

- [ ] T007 [P] [US3] Add the release note fragment.
  - Requirements: FR-010.
  - Paths: `changelog.d/issue-4708-msp-inventory-reporting.md` (add).
  - Acceptance: The file holds one `###` heading and one `- **Fixed**:` bullet that names issue #4708. The file uses ASCII text. The change does not edit `CHANGELOG.md`.
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4708-msp-inventory-reporting.md`
  - Status: open

- [ ] T008 [US3] Append the pivot display test and the unnamed-record test to the test module.
  - Tests: `test_display_combined_pivot_shows_row_values_and_total` and `test_process_org_missing_name_uses_unnamed_label`.
  - Requirements: FR-003, FR-009.
  - Paths: `tests/unit/inventory/test_org_device_inventory_msp.py` (append only).
  - Acceptance: The pivot test asserts each displayed row value and the TOTAL row value. The unnamed-record test asserts that the console line contains `unnamed record`.
  - Verification: `python -m pytest tests/unit/inventory/test_org_device_inventory_msp.py`
  - Status: open

## Final Tasks

- [ ] T-LOCAL-GATES [US3] Run each applicable gate from `design/quickstart.md`.
  - Requirements: FR-005, FR-007, SC-003.
  - Paths: `src/mist/resources/inventory/org_device_inventory_msp.py`, `tests/unit/inventory/test_org_device_inventory_msp.py`, `changelog.d/issue-4708-msp-inventory-reporting.md`, and `specs/numbered/0/0/1/2/2/3/1/3/4708-msp-inventory-reporting/`.
  - Acceptance: Each applicable gate reports its expected result. Each gate that does not apply names its reason.
  - Verification: `python -m ruff check .`
  - Depends on: T001, T002, T003, T004, T005, T006, T007, and T008.
  - Status: open

- [ ] T-PR [US3] Commit, push, and open the pull request after owner authorization.
  - Requirements: FR-010, FR-011.
  - Paths: `src/mist/resources/inventory/org_device_inventory_msp.py`, `tests/unit/inventory/test_org_device_inventory_msp.py`, `changelog.d/issue-4708-msp-inventory-reporting.md`, and `specs/numbered/0/0/1/2/2/3/1/3/4708-msp-inventory-reporting/`.
  - Acceptance: One commit uses the subject `fix(inventory): report accurate MSP batch coverage`, a body that contains `Closes #4708`, and the Co-authored-by trailer. One push sends `fix/4708-msp-inventory-reporting`. One pull request targets `main`.
  - Verification: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt`
  - Depends on: T-LOCAL-GATES and owner authorization, as decision D-9 records.
  - Status: open

- [ ] T-REMOTE-CI [US3] Watch every required check on the pull request.
  - Requirements: SC-003.
  - Paths: Verified, not changed: `src/mist/resources/inventory/org_device_inventory_msp.py` and `tests/unit/inventory/test_org_device_inventory_msp.py`.
  - Acceptance: Every required check reports success. Run `gh pr checks` with the pull request number and the `--watch` option.
  - Verification: `python -m pytest tests/unit/inventory/test_org_device_inventory_msp.py`, run locally after the rebase.
  - Depends on: T-PR.
  - Status: open

- [ ] T-MERGE [US3] Add the `auto-merge` label, then squash-merge after orchestrator authorization.
  - Requirements: FR-010.
  - Paths: Verified, not changed: `changelog.d/issue-4708-msp-inventory-reporting.md` and `tests/unit/inventory/test_org_device_inventory_msp.py`.
  - Acceptance: The label appears only after every check reports success. One squash commit lands on `main`. The branch and the worktree are removed.
  - Verification: `python -m pytest tests/unit/inventory/test_org_device_inventory_msp.py`, run on the merged revision of `main`.
  - Depends on: T-REMOTE-CI and orchestrator authorization.
  - Status: open

Warning: a squash merge to `main` cannot be undone by deleting its commit. Only a new revert pull request reverses it.

## Dependencies and Execution Order

- T001 comes first. T002 follows T001.
- T003 follows T002. T004 follows T003, because T003 shows the defect first.
- T005 follows T004. T006 follows T005.
- T007 can run in parallel with the test tasks, because it changes a different file.
- T008 follows T006, because it covers the final renderers.
- T-LOCAL-GATES follows T001 through T008. T-PR follows T-LOCAL-GATES. T-REMOTE-CI follows T-PR. T-MERGE follows T-REMOTE-CI.

## Requirement Coverage

Each requirement maps to at least one task and at least one test or gate.

| Requirement | Tasks | Test or gate |
| --- | --- | --- |
| FR-001 | T003, T004 | `test_execute_msp_footer_reports_partial_skip_and_failure` and `test_execute_msp_empty_successful_result_counts_as_success` |
| FR-002 | T003, T004 | `test_execute_msp_footer_reports_partial_skip_and_failure` and `test_execute_msp_zero_successes_writes_no_combined_reports` |
| FR-003 | T004, T008 | `test_execute_msp_footer_reports_partial_skip_and_failure` and `test_process_org_missing_name_uses_unnamed_label` |
| FR-004 | T005, T006 | `test_execute_msp_partial_reports_carry_label_and_filename_marker` |
| FR-005 | T003, T006, T-LOCAL-GATES | `test_execute_msp_footer_reports_complete_coverage` |
| FR-006 | T003, T004 | `test_execute_msp_continues_after_earlier_failure` |
| FR-007 | T002, T003, T-LOCAL-GATES | The `block_network` fixture, used by each new test, and the Tests gate |
| FR-008 | T005, T006 | `test_execute_msp_partial_reports_carry_label_and_filename_marker` |
| FR-009 | T008 | `test_display_combined_pivot_shows_row_values_and_total` |
| FR-010 | T007, T-PR, T-MERGE | The STE gate on the changelog fragment (T007) |
| FR-011 | T001, T-PR | The Tests gate run on the base revision (T001) |

