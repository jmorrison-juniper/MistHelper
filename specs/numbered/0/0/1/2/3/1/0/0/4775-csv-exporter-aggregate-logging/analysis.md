# Specification Analysis Report: Exported cell values stay out of DEBUG logs

## Findings

| ID | Category | Severity | Finding | Resolution |
| - | - | - | - | - |
| F1 | Defect in existing work | High | Four exporter DEBUG statements log cell values, device values, or tables. They are `data_exporter.py` line 443, `org_inventory_exporter.py` lines 613, 652, and 766, and `site_device_exporter.py` line 110. | Tasks T007, T008, and T010 remove them. |
| F2 | Defect in existing work | High | `sites_by_ap_model_exporter.py` line 88 logs a site address at DEBUG. | Task T009. Decision D-1. |
| F3 | Defect in existing work | Medium | `org_inventory_exporter.py` line 723 logs a site address at DEBUG. | Task T008. Decision D-6. |
| F4 | Defect in existing work | Medium | `data_exporter.py` line 410 logs the field names. | Task T007. Decision D-3. |
| F5 | Scope | High | Issue #4775 names two locations. The sweep found two more. | Decision D-1. The owner can narrow the scope before implementation starts. |
| F6 | Overlap | High | Pull request #4813 edits `data_exporter.py` lines 405 to 411 and the writer test class near lines 511 to 516. | FR-014, decision D-12, and task T001. |
| F7 | Constitution | Medium | Principle VII. Two pure parse helpers keep no per-call INFO line. | Decision D-7. Complexity Tracking records the deviation. |
| F8 | Constitution | Low | Principle I. `changelog.d/` holds 335 files, and `tests/unit/export/` holds 55 entries on `main`. | The change adds one fragment and no test file under `tests/unit/export/`. Remediation is a separate action. |
| F9 | Gate | Medium | `symbol-diff` reports the removed PrettyTable imports. The gate runs locally, and `ci.yml` runs no symbol-diff job. | Decision D-15. |
| F10 | Stale text | Low | `site_device_exporter.py` line 6 names prettytable. `org_inventory_exporter.py` line 28 names PrettyTable payloads. Two docstrings at lines 660 and 681 describe the removed tables. | Tasks T008 and T010 update each line. |
| F11 | Documentation | Low | `documentation/cli-reference.md` line 19, `documentation/wiki/Troubleshooting.md` line 27, and the `--debug` help text describe table data in logs. The statement stays true for DEBUG tables outside the package. | Decision D-10. |
| F12 | Residual risk | Medium | Warnings and errors with exception text remain. They are `data_exporter.py` lines 121, 149, and 315, and `org_inventory_exporter.py` lines 136, 193, 327, 529, and 543. | Decision D-8. A follow-up audit issue owns the review. |
| F13 | Residual risk | Medium | Three DEBUG tables outside the exporter package remain. They are `display_utils.py` line 58, `api_data_fetcher.py` line 428, and `arp_command_manager.py` line 299. | Decision D-9. A follow-up issue owns them. |
| F14 | Residual risk | Medium | Existing `data/script.log` files keep old values. | Decision D-14. The Warning in `design/research.md` tells operators to review the files. |
| F15 | Consistency | Info | The spec has 15 functional requirements, 6 success criteria, and 4 user stories. The plan lists ten changed paths. The tasks cover each requirement. | None required. |

## Coverage Summary

| Requirement | Tasks | Tests or gates |
| - | - | - |
| FR-001 | T002, T007 | `test_debug_output_has_no_cell_values` |
| FR-002 | T002, T007 | `test_field_names_are_logged_as_count_only`, `test_debug_output_has_no_cell_values` |
| FR-003 | T002, T007 | `test_csv_keeps_marker_cell_values` |
| FR-004 | T003, T008 | `test_enrich_devices_debug_output_has_no_device_values` |
| FR-005 | T008, T010, T011 | The test run in T011 (`tests/unit/export`), and the removed tests RV-57, RV-58, and RV-64 |
| FR-006 | T005, T010 | `test_debug_output_has_no_inventory_values` |
| FR-007 | T004, T009 | `test_failure_log_names_error_type_only` |
| FR-008 | T003, T004, T008, T009 | `test_split_full_address_failure_logs_error_type_only`, `test_failure_log_names_error_type_only` |
| FR-009 | T007, T008, T009, T010, T014 | Ruff lint in T014 |
| FR-010 | T002 to T005 | The six absence tests |
| FR-011 | T012 | STE gate on `documentation/security.md` |
| FR-012 | T013, T-PR | `tests/guardrails/test_changelog_fragment_policy.py` |
| FR-013 | T001, T-PR | Changed-path list (quickstart, verify step 3) |
| FR-014 | T001, T-PR | Pull request state check (quickstart, prerequisite 1) |
| FR-015 | T014 | Search in T014 |

| Success criterion | Evidence |
| - | - |
| SC-001 | The six absence tests in T002 to T005 |
| SC-002 | `test_csv_keeps_marker_cell_values` in T002 |
| SC-003 | Search in T014 |
| SC-004 | Local gates in `design/quickstart.md` |
| SC-005 | T-REMOTE-CI |
| SC-006 | Changed-path list in `design/quickstart.md` |

## Consistency Review

- The spec names four exporter locations (D-1). The plan change map lists the same four files. The tasks and the tests cover the same four files.
- The spec states six absence tests (SC-001). Tasks T002 to T005 create six absence tests. The round-trip test is the seventh new test.
- The non-goals in the spec match decisions D-8 and D-9.
- The plan line numbers match the blob SHAs in `design/research.md` (RV-09 to RV-64).
- Each task names one verification command. T-PR, T-REMOTE-CI, and T-MERGE name a remote command, because no local gate covers the remote state.
- The log contract in `design/contracts/log-messages.md` lists the same messages that tasks T007 to T009 write.

## Defects in Existing Work

- F1 to F4 list the log statements that log values.
- F10 lists two stale comments and two stale docstrings. The tasks update them.

## Unmapped Tasks

None. Each task maps to at least one requirement.

## Metrics

- Functional requirements: 15.
- Success criteria: 6.
- User stories: 4. Priority P1 has two stories, and priority P2 has two stories.
- Tasks: 18. Fourteen are implementation tasks, and four are delivery tasks.
- Decisions: 18. Human decisions: 0.
- New test cases: 7. Obsolete test cases removed: 5.
- Remote checks: 120.
- Changed paths: 10.

## Unresolved Items

- Pull request #4813 must merge first (F6). Its owner can hand over the two shared files instead.
- The owner can narrow the four-location scope before implementation starts (F5).
- Follow-up issues: a DEBUG table audit (F13), an exception text audit (F12), and a changelog folder remediation (F8).
- The symbol check reports the intended removals (F9). The pull request body explains them.
