# Specification Analysis Report: Resumed 52-week device-event CSV export

**Scope**: Consistency across `spec.md`, `plan.md`, `tasks.md`, and the remote code on `main`. The remote code reference is commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

## Findings

| ID | Severity | Finding | Evidence | Resolution |
| - | - | - | - | - |
| A-01 | High | The issue reproduction used blob `db6d6b1092be47feaddd7c8ac70d66e1d0254b7b`. Main now holds blob `97e574382993ca34d56108d6cbf660d047b74be4`. | `design\research.md` C-04, C-05. PR #4834 merged on 2026-11-19 (merge commit `19bec34ea1edfae30782fc0f23dde44b3516e369`, C-02). | The record tests the current main code. Task statuses reflect that code. |
| A-02 | High | PR #4834 does not close issue #4721. The PR body uses `Refs #4721`. | PR #4834 body. The issue state is OPEN. | Task T-PR uses `Closes #4721`. |
| A-03 | High | An empty checkpoint file starts a fresh run. The fresh run then replaces the CSV file. | `device_events_52w_exporter.py` line 152 returns `None` for an empty token. Line 311 opens the CSV with mode `w`. C-06, C-08. | FR-006 and task T002. |
| A-04 | High | A checkpoint write opens the live file with mode `w` before it writes. A failed write can leave an empty file. A later run then reaches A-03. | Line 350. C-07. | FR-007 and task T003. |
| A-05 | Medium | A resumed run with no new rows calls `DataExporter` with empty rows. The run then logs "No device events found", and the DataExporter logs a warning. Both messages mislead the operator. | Lines 90-91 and 120-125. `DataExporter` rejects empty rows and writes nothing (C-32). | FR-008 and task T004. |
| A-06 | Medium | The existing test `test_read_checkpoint_returns_none_for_empty_file` pins the risky behavior. The test has no `monkeypatch.chdir`, so a real CSV in the working directory would change its outcome after the fix. | Test lines 83-88 (C-23). | Task T001 updates the test with `chdir` and a missing CSV. |
| A-07 | Medium | The proposed test path `tests\unit\export\test_device_events_checkpoint_recovery.py` adds a child to a folder with 55 children. Principle I forbids that. | C-25, C-26. Constitution line 40 and line 42. | Decision D-8. Tests go into the existing module. |
| A-08 | Low | The issue comment of 2026-11-09 says PR #4358 owns the two device-event test files. PR #4358 merged on 2026-11-13. | C-55. | No action. The clarification in `spec.md` records the change. |
| A-09 | Medium | A failed checkpoint write after a CSV append repeats the last batch on the next resume. | Docstring at lines 343-346. | Decision D-5. FR-013 documents the risk. |
| A-10 | High | Cross-organization mixing is reachable. The CSV name is fixed (line 17). The checkpoint name includes the organization (line 19). A later run for another organization can append rows when the headers match. | Lines 17, 19, 136, 138. | Out of scope. Decision D-6. A follow-up issue must track it. |
| A-11 | Medium | Field drift drops new fields silently. The header comes from the preload rows only (line 92). `_write_rows` keeps only the header fields (lines 385-387). | C-33 for the sorted header. | Out of scope. A follow-up issue must track it. |
| A-12 | Low | The README does not mention menu 97 or the resume rules. Principle README (constitution line 400) requires an update for a behavior change. | C-51. A search of README for `checkpoint`, `resume`, and `52w` returns no match. | Task T006. |
| A-13 | Low | The endpoint note names menus 2 and 63 for device events. Menu 2 exports sites with locations. Menu 63 exports virtual chassis data. | C-48 (stale). C-49 (MistHelper.py line 3966). MistHelper.py lines 3855 and 3966. | Task T008. |
| A-14 | Medium | The live form of `next` is unknown. The schema says "cursor or URL". The exporter sends the raw value as `search_after`. | C-17 to C-19. Lines 174-175, 212-214, and 335-339 of the exporter. | Unverified item U-1. Decision D-11. Owner check before merge. |
| A-15 | Medium | Draft PR #4813 changes the shared `escape_multiline` helper. The exporter calls that helper in `_process_rows` (lines 217-220). | C-56. C-34 (helper at line 156). | Coordination. Rebase after #4813 lands, then rerun the resume tests. |
| A-16 | Low | Pre-existing debt in the touched module. `_fetch_page` logs nothing (lines 157-164). CSV writes bypass `DataExporter` (lines 311 and 326). | Plan Constitution Check and Complexity Tracking. | Recorded. The change does not add debt of this kind. |
| A-17 | Low | The issue reproduction used Python 3.13.13. The project requires Python 3.15 or newer. | Issue body. `pyproject.toml` line 23. | The implementer runs the gates on Python 3.15. |
| A-18 | Low | No script in `scripts` contains the endpoint note sentence. | Search of `scripts` returns no match. Line 707 of `scripts\generate_api_docs.py` creates category folders. | Task T008 edits the line directly. Unverified item U-6 covers an enrichment file. |
| A-19 | High | An API connection error or HTTP error returns an empty page, not an exception. A streaming run then logs completion and removes the checkpoint. | `__api_request.py` lines 219, 225-228, and 258 (C-64). The retry wrapper in the exporter retries exceptions only (lines 233-239). An empty page ends the loop (lines 336-337, C-65), and the checkpoint is removed (line 117). | Out of scope. Decision D-12. A follow-up issue must track it. |

## Coverage Summary

Each requirement maps to at least one task and one test or check.

| Requirement | Task | Test or check |
| - | - | - |
| FR-001 | T009 | `test_resumed_csv_append_keeps_earlier_rows_and_adds_new_rows` (test line 649) |
| FR-002 | T009 | `test_resume_refuses_when_csv_is_missing_and_keeps_checkpoint` (line 703) |
| FR-003 | T009 | `test_resumed_csv_refuses_when_header_differs_and_keeps_bytes` (line 679) |
| FR-004 | T009 | `test_resumed_csv_refuses_when_last_row_is_partial` (line 725) |
| FR-005 | T009 | `test_export_stops_without_touching_output_when_checkpoint_cannot_be_read` (line 543) and `test_read_checkpoint_raises_and_logs_error_when_read_fails` (line 91) |
| FR-006 | T002 | N1 `test_read_checkpoint_refuses_empty_file_when_csv_exists`. N2 and N3 keep the fresh-run and SQLite paths. |
| FR-007 | T003 | N4 `test_write_checkpoint_keeps_previous_token_when_replace_fails`. N5 `test_write_checkpoint_never_truncates_live_checkpoint` |
| FR-008 | T004 | N6 `test_resumed_run_without_new_rows_keeps_both_files` |
| FR-009 | T002, T003, T004 | N1 asserts one error log. Test line 120 asserts one warning log. |
| FR-010 | T009 | `test_write_checkpoint_writes_token_to_file` (line 104) and the read test (line 71) |
| FR-011 | T009 | SQLite tests at lines 574, 597, and 625 |
| FR-012 | T003, T004 | N4 asserts the warning. N6 asserts the info line. Code review confirms the before and after logs. |
| FR-013 | T005, T006, T008 | STE gate on each Markdown file, and a manual read against the spec |
| FR-014 | T007 | STE gate on the fragment, and the naming rule in `changelog.d\README.md` line 19 |
| FR-015 | T-LOCAL-GATES | `test_nested_package_ratchet_matches_main` (guardrail line 169) and `symbol-diff` |

## Constitution Alignment

- Principle I: The plan records each touched violation and the remediation action. The proposed new file is rejected (A-07).
- Principle VI and VII: Each touched block has logs and inline comments in the implementation tasks.
- Principle V: All new log text is ASCII.
- Principle III: Every refusal runs before a write.

## Unmapped Tasks

None. Each task maps to a requirement.

## Metrics

- Requirements: 15 (FR-001 to FR-015).
- Success criteria: 5 (SC-001 to SC-005).
- Tasks: 13 (nine implementation and documentation tasks, plus four delivery tasks).
- Planned tests: 7 (six new, one updated).
- Decisions: 12 (D-1 to D-12). Human decisions: 0.
- Remote checks: 65 (C-01 to C-65).

## Unresolved Items

- U-1: The live form of the `next` value. An owner must confirm it before merge. The exporter logic does not change.
- U-2: Windows can block the replace step while another process holds the checkpoint file. The change handles the failure by a warning. Field testing on Windows is still open.
- U-3: Follow-up issues for A-10 (organization binding), A-11 (field drift), A-19 (API error completes a run), and D-7 (backup before a fresh run). The orchestrator must file them. This authoring agent cannot file issues.
- U-4: Coordination with draft PR #4813 (A-15).
- U-5: No gate has run. The authoring agent read code and documents only.
- U-6: The endpoint note may come from an enrichment file that the authoring agent did not read. T008 must confirm this before the edit.

## Convergence After Implementation

After T002 to T004 pass, the three defects in A-03, A-04, and A-05 close. The test fixture in A-06 changes with T001. The implementer must rerun T009 after each code task.
