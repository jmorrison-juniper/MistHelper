# Test Checklist: MSP inventory batch coverage

**Purpose**: Check that each new test covers a defect or guards a behavior, and that each test can fail.

**Created**: 2026-11-26

**Feature**: [Plan](../../plan.md) and [Tasks](../../tasks.md)

## New Tests (appended to `tests/unit/inventory/test_org_device_inventory_msp.py`)

| Test | Covers | Failure on `main` |
| --- | --- | --- |
| `test_execute_msp_footer_reports_complete_coverage` | FR-005, SC-003. Three successful records give the complete footer and `All Orgs`. | Passes. It guards the complete output. |
| `test_execute_msp_footer_reports_partial_skip_and_failure` | FR-001, FR-002, FR-003. One success, one missing ID, one failure. | Fails. `main` prints the complete footer. |
| `test_execute_msp_continues_after_earlier_failure` | FR-006. A failing record precedes a valid record. | Fails. `main` prints `Processed 2 organizations`. |
| `test_execute_msp_zero_successes_writes_no_combined_reports` | FR-002, SC-001. Two records without an ID. | Fails. `main` prints `Processed 2 organizations`. |
| `test_execute_msp_empty_successful_result_counts_as_success` | FR-001. Two successful results with empty lists. | Passes. It guards the success rule. |
| `test_execute_msp_partial_reports_carry_label_and_filename_marker` | FR-004, FR-008, SC-002. Two successes and one failure. | Fails. `main` prints `All Orgs` and uses complete names. |
| `test_display_combined_pivot_shows_row_values_and_total` | FR-009. Displayed row values and the TOTAL row. | Passes on `main`. It closes the #2708 assertion gap. |
| `test_process_org_missing_name_uses_unnamed_label` | FR-003. A record with no name and no ID. | Fails. `main` prints no skipped line. |

## Test Rules

- [x] Each test uses the `block_network` fixture or the existing mocked collaborators. No test opens a socket or runs a DNS lookup.
- [x] Each test asserts specific values. No test uses a bare `assert result`.
- [x] Each test that covers a defect fails on `main` before the source change. The table above names each failure.
- [x] Each test appends after the existing tests. No existing line moves.
- [x] Each test uses `capsys` or a mock to read the output. No test reads a file in `data/`.
- [x] Each test names a behavior, not an implementation detail.
- [x] Each test keeps its imports at the top of the module unchanged. The `block_network` fixture imports `socket` inside its body.

## Notes

- The change adds eight tests. The module holds 41 tests before the change, and 49 tests after it.
- The existing test `test_execute_msp_short_circuits_when_no_orgs` covers the empty organization list, so no new test covers that edge case.
