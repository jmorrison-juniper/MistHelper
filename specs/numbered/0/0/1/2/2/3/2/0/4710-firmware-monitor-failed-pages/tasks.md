# Tasks: Firmware Monitor Treats Failed Stats Pages as Failed Checks

**Input**: Numeric record `specs/numbered/0/0/1/2/2/3/2/0/4710-firmware-monitor-failed-pages/`.

**Available docs**: `spec.md`, `plan.md`, `analysis.md`, `design/research.md`, `design/data-model.md`, `design/quickstart.md`, `design/contracts/stats-page-walk.md`, `design/contracts/monitor-exit-codes.md`, `design/checklists/requirements.md`, and `design/checklists/security.md`.

**Format**: `ID [P?] [FR-###] Description`. `[P]` means the task touches different files and has no dependency. The status values are open, verified-present, partial, and absent.

**Test identifiers**: N1 to N14 are new tests. U1 and U2 are updated tests. All of them live in `tests/unit/firmware/test_firmware_manager_monitoring.py`. The fake `get_next` in each walk test counts its calls and raises after 40 calls (the existing `_CHECK_CALL_CEILING` pattern). An unfixed walk therefore fails instead of hanging.

## Phase 1: Baseline and Defect Tests

| ID | Parallel | Requirements | Repository path | Acceptance | Verification | Status |
| - | - | - | - | - | - | - |
| T001 | no | FR-005 | `src/operations/execution/firmware/firmware_manager.py` (lines 637 to 647) | The method returns `mistapi.get_all` output with no status check (research RC-44). | `python -m pytest tests/unit/firmware/test_firmware_manager_monitoring.py` | verified-present |
| T002 | no | FR-002, FR-005 | `tests/unit/firmware/test_firmware_manager_monitoring.py` | Add N1 (HTTP 403 first page never completes) and N2 (HTTP 503 empty first page returns no count). Both fail before the change. | `python -m pytest tests/unit/firmware/test_firmware_manager_monitoring.py` | absent |
| T003 | no | FR-001 | `tests/unit/firmware/test_firmware_manager_monitoring.py` | Add N14, a characterization test that shows the SDK `get_all` path returns an empty list for an HTTP 403 first page. It passes before and after the change. | `python -m pytest tests/unit/firmware/test_firmware_manager_monitoring.py` | absent |

## Phase 2: Later-Page, Metadata, and Logging Tests

| ID | Parallel | Requirements | Repository path | Acceptance | Verification | Status |
| - | - | - | - | - | - | - |
| T004 | no | FR-002, FR-003, FR-004, FR-005 | `tests/unit/firmware/test_firmware_manager_monitoring.py` | Add N3 (missing status fails), N4 (non-list HTTP 200 body fails), N5 (later page HTTP 503 returns no count), and N6 (site branch later page failure is not completion). All four fail before the change. | `python -m pytest tests/unit/firmware/test_firmware_manager_monitoring.py` | absent |
| T005 | no | FR-006 | `tests/unit/firmware/test_firmware_manager_monitoring.py` | Add N7. The last page announces more rows than the walk collected, or announces a non-integer total. The test fails before the change. | `python -m pytest tests/unit/firmware/test_firmware_manager_monitoring.py` | absent |
| T006 | no | FR-007 | `tests/unit/firmware/test_firmware_manager_monitoring.py` | Add N8. A next link repeats, and the walk raises. The test fails before the change. | `python -m pytest tests/unit/firmware/test_firmware_manager_monitoring.py` | absent |
| T007 | no | FR-001, FR-008 | `tests/unit/firmware/test_firmware_manager_monitoring.py` | Add N9 (HTTP 200 with an empty array completes with exit 0) and N10 (two pages, the active upgrade on page two, count is one). N9 and N10 pass before the change and guard the success path. | `python -m pytest tests/unit/firmware/test_firmware_manager_monitoring.py` | absent |
| T008 | no | FR-009 | `tests/unit/firmware/test_firmware_manager_monitoring.py` | Add N11. Every check returns HTTP 403. The loop returns `MONITOR_EXIT_FAILED` after five checks, with waits of 7, 14, 28, and 56 seconds. The test fails before the change. | `python -m pytest tests/unit/firmware/test_firmware_manager_monitoring.py` | absent |
| T009 | no | FR-010, FR-012 | `tests/unit/firmware/test_firmware_manager_monitoring.py` | Add N12 (failure text names the status only and omits the body text) and N13 (an `info` line precedes each page request and a `debug` line follows each page result). Both fail before the change. | `python -m pytest tests/unit/firmware/test_firmware_manager_monitoring.py` | absent |
| T010 | no | FR-005, FR-011 | `tests/unit/firmware/test_firmware_manager_monitoring.py` (test doubles at lines 654 and 677) | Update U1 (`test_site_filter_uses_site_stats`) and U2 (`test_no_site_filter_uses_org_stats`). The doubles return HTTP 200 pages with a list body, headers, and a next link of `None`. The assertions check the arguments and the returned rows. | `python -m pytest tests/unit/firmware/test_firmware_manager_monitoring.py` | open |

## Phase 3: Implementation in the Existing Method

| ID | Parallel | Requirements | Repository path | Acceptance | Verification | Status |
| - | - | - | - | - | - | - |
| T011 | no | FR-001, FR-002, FR-003, FR-004, FR-008 | `src/operations/execution/firmware/firmware_manager.py` (method lines 637 to 647) | Replace the body with the strict page walk. The first page uses the existing org or site call. A page passes only when its status equals `_HTTP_OK` (line 29) and its body is a list. Later pages use `mistapi.get_next`. The method holds 25 lines or fewer and five logical blocks or fewer. | `python -m pytest tests/unit/firmware/test_firmware_manager_monitoring.py` | open |
| T012 | no | FR-006 | `src/operations/execution/firmware/firmware_manager.py` (same method) | After the walk, read `X-Page-Total` from the last page headers when present. Raise when the row count is lower. A non-integer header raises `ValueError` through `int()`. | `python -m pytest tests/unit/firmware/test_firmware_manager_monitoring.py` | open |
| T013 | no | FR-007 | `src/operations/execution/firmware/firmware_manager.py` (same method) | Keep a set of followed next links. Raise `RuntimeError` when a link repeats. | `python -m pytest tests/unit/firmware/test_firmware_manager_monitoring.py` | open |
| T014 | no | FR-012 | `src/operations/execution/firmware/firmware_manager.py` (same method) | Write an `info` line before each page request and a `debug` line after each page result. The lines carry the status and the row count only. | `python -m pytest tests/unit/firmware/test_firmware_manager_monitoring.py` | open |
| T015 | no | FR-005, FR-009 | `src/operations/execution/firmware/firmware_manager.py` (lines 417 to 437 and 702 to 722, unchanged) | The existing status-check failure path and retry policy handle the new exception with no edit to `_execute_monitoring_check` or `_run_monitoring_loop`. Tests N5 and N11 prove it. | `python -m pytest tests/unit/firmware/test_firmware_manager_monitoring.py` | open |
| T016 | no | FR-011 | `tests/unit/firmware/test_firmware_manager_monitoring.py` (lines 124, 209, 271, and 315) | The existing tests `test_response_status_code_preserves_http_failure_status`, `TestRunMonitoringLoop`, `TestMonitoringRetryPolicy`, and `TestRunMonitoringLoopRetryBound` pass without edit. | `python -m pytest tests/unit/firmware/test_firmware_manager_monitoring.py` | verified-present |

## Phase 4: Delivery Support

| ID | Parallel | Requirements | Repository path | Acceptance | Verification | Status |
| - | - | - | - | - | - | - |
| T017 | [P] | FR-005 | `changelog.d/issue-4710-firmware-monitor-failed-pages.md` | Create one release-note fragment. The text names the user-visible change in plain words. It states that a failed stats page no longer reports completion. | `ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4710-firmware-monitor-failed-pages.md` | absent |

## Final Tasks

| ID | Parallel | Requirements | Repository path | Acceptance | Verification | Status |
| - | - | - | - | - | - | - |
| T-LOCAL-GATES | no | FR-001 to FR-012 | `src/operations/execution/firmware/firmware_manager.py`, `tests/unit/firmware/test_firmware_manager_monitoring.py`, `changelog.d/issue-4710-firmware-monitor-failed-pages.md` | Run every applicable row of the local gates table in `.github/copilot-instructions.md` (lines 57 to 76) and the test-quality ratchet. Record each command and its result. Stop at the first failed command. | Each applicable row of the local gates table (`.github/copilot-instructions.md` line 62 for the full tests row) | open |
| T-PR | no | FR-001 to FR-012 | Branch `fix/4710-firmware-monitor-failed-pages` | Confirm the file reservation with the owner of issue #4709. Commit with the subject `fix(firmware): treat failed stats pages as failed checks`. The body holds `Closes #4710`. Push the branch and open the pull request. | Symbols row: `symbol-diff --base origin/main src/operations/execution/firmware/firmware_manager.py` (`.github/copilot-instructions.md` line 73) | open |
| T-REMOTE-CI | no | FR-001 to FR-012 | The pull request checks | Watch each required check with `gh pr checks <number> --watch`. Every required check passes. Read each failed job before a repair. | Full tests row (`.github/copilot-instructions.md` line 62) as run by the CI shards | open |
| T-MERGE | no | FR-005, FR-009 | The pull request | Add the `auto-merge` label only after every check passes, the human review of `needs-human-review` completes, and the orchestrator authorizes the merge. Squash the merge. Delete the branch. | Symbols row: `symbol-diff --base origin/main src/operations/execution/firmware/firmware_manager.py` (`.github/copilot-instructions.md` line 73) | open |

## Dependencies and Execution Order

- Phase 1 runs first. Tests N1 and N2 must fail before Phase 3 begins.
- Phase 2 adds tests that must fail before the implementation.
- Phase 3 implements the method. Tasks T011 to T014 edit the same method, so they run in order.
- T017 touches a different file and runs in parallel with Phase 3.
- The final tasks run in order: T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE.

## Traceability

| Requirement | Tasks | Tests |
| - | - | - |
| FR-001 mistapi methods only | T003, T007, T011 | N10, N14 |
| FR-002 status must equal 200 | T002, T004, T011 | N1, N2, N3 |
| FR-003 body must be a list | T004, T011 | N4 |
| FR-004 failed page returns no count | T004, T011 | N5 |
| FR-005 no false completion | T001, T002, T004, T010, T011, T015 | N1, N2, N5, N6, N11, U1, U2 |
| FR-006 announced total | T005, T012 | N7 |
| FR-007 repeated next link | T006, T013 | N8 |
| FR-008 empty success completes | T007, T011 | N9 |
| FR-009 persistent failure exit | T008, T015 | N11 |
| FR-010 status-only failure text | T009 | N12 |
| FR-011 unchanged exit codes, cadence, backoff, helper | T010, T016 | U1, U2, `test_response_status_code_preserves_http_failure_status`, `TestRunMonitoringLoop`, `TestMonitoringRetryPolicy`, `TestRunMonitoringLoopRetryBound` |
| FR-012 action logging | T009, T014 | N13 |

Counts: 12 requirements, 21 tasks, 14 new tests, and 2 updated tests (16 planned tests in total).
