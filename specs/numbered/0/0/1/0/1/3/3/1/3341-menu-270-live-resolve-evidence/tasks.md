# Tasks: Menu 270 Live Resolve Acceptance Evidence

**Input**: `spec.md`, `plan.md`, `design\research.md`, `design\data-model.md`, `design\contracts\`, and `design\quickstart.md`.

**Format**: `[ID] [P?] [Story] Description`. Each task names its requirements, its files, its acceptance statement, its verification, and its status. A status is `open`, `verified-present`, `partial`, or `absent`.

**Order**: Tasks run in the order of this file. A task names each prerequisite task.

## Phase 1: Verify the Existing Code and Tests

- **T001** [US2][US3] Verify the resolve path on `main`. Requirements: FR-007, FR-012. Files: `src/mist/intelligence/marvis/actions/client.py`, `src/mist/intelligence/marvis/actions/operation.py`, `src/mist/intelligence/marvis/actions/selection.py`, and `src/mist/intelligence/marvis/actions/model.py`. Acceptance: research rows 5 to 19 match the remote blob SHAs and the lines. Verification: the remote verification table in `design\research.md`, rows 5 to 19. No local gate applies, because no file changes. Status: verified-present.

- **T002** [US3] Verify the offline test set on `main`. Requirements: FR-012. Files: `tests/unit/marvis/actions/test_client.py`, `tests/unit/marvis/actions/test_operation.py`, `tests/unit/marvis/actions/test_selection.py`, and `tests/unit/marvis/actions/test_portal_contract.py`. Acceptance: research rows 20 to 23 match, and each test of the test set below appears in its file. Verification: `python -m pytest tests\unit\marvis\actions -q`, run in T-LOCAL-GATES. Status: verified-present. The authoring run read the test names. It did not run the tests.

## Phase 2: Endpoint Report and Owner-Only Evidence

- **T003** [US2] Correct the endpoint report. Requirements: FR-009, SC-002. Depends on: T001 and T002. Files: `documentation/marvis-actions-api-endpoints.md`. Changes:
  1. Line 13: name mistapi 0.64.1 in place of 0.64.0.
  2. Line 582: replace the sentence that says no live resolve request was sent. State the 2026-10-21 attempt, the date, HTTP 403, outcome `error`, and the open status.
  3. Add this sentence to the live section: No retry occurs until issue #4389 names a cause.

  Acceptance: no sentence says that no live resolve request was sent. Both version statements name the installed package. Acceptance statement: none. Verification: the STE command and the link check of T-LOCAL-GATES. Status: open.

- **T004** [US1] Run the owner live check. Requirements: FR-001, FR-002, FR-003, FR-004, FR-008, FR-011. Files: none in the repository. Procedure: `design\quickstart.md`, section "Run the live check". Acceptance: the results file holds one row with an HTTP 2xx status, outcome `resolved`, and a verified status outside `OPEN_STATUSES`. Preconditions: the owner approves in writing. The lab organization holds one open Marvis Action. Issue #4389 names a cause, or the owner approves a new run in writing. Status: absent. The owner runs this step. The authoring run had no lab credential and sent no Mist request. Verification: the results file read in `design\quickstart.md`, Part 2. No local gate applies to an owner run.

- **T005** [US1] Record the live evidence in issue #3341. Requirements: FR-005, FR-006, FR-010. Depends on: T004. Files: none in the repository. Format: `design\contracts\live-evidence-record.md`. Acceptance: one owner comment states the UTC date, the HTTP status, the outcome, the verified status, and the next step. The comment holds no credential and no raw response body. Verification: checklist `design\checklists\live-check.md`, items CHK108 and CHK109. Status: absent.

- **T006** [US2] Add the accepted-run date to the endpoint report. Requirements: FR-007, FR-009, SC-001. Depends on: T005. Files: `documentation/marvis-actions-api-endpoints.md`. Acceptance: the live section states the date of the first accepted live resolve. If the pull request from T-PR already merged, file a new issue and branch again from `main`, as AGENTS.md requires after a squash merge. Verification: the STE command of T-LOCAL-GATES. Status: absent.

## Phase 3: Final Pipeline Tasks

- **T-LOCAL-GATES** [US2][US3] Run each local gate that applies. Requirements: FR-012, SC-003. Depends on: T003. Applicable gates:
  - STE: `ste-linter --config .ste-linter.toml --min-score 80 documentation/marvis-actions-api-endpoints.md`, and the same command for each Markdown file of the record folder. Expected: each file scores 80 or above.
  - Link check: `markdown-link-check documentation/marvis-actions-api-endpoints.md`. Expected: no broken link.
  - Offline tests: `python -m pytest tests\unit\marvis\actions -q`. Expected: every test passes, including the 22 tests of the test set.
  - Not applicable: compile, lint, format, types, complexity, security lint, and dead code. Not applicable: dependency audit, code quality, docstrings, menu reference, symbols, safe sweep, coverage, and test quality. Reason: the change alters no Python file, no registry row, and no test file.

  Acceptance: each applicable command exits 0. The results appear in the pull request body. Status: open.

- **T-PR** [US2] Commit, push, and open the pull request. Requirements: FR-013, FR-014. Depends on: T-LOCAL-GATES. Steps:
  1. Add the `in-progress` label to issue #3341 before the branch exists.
  2. Create the branch `docs/3341-menu-270-live-resolve-evidence` from `main`.
  3. Add these paths by explicit path: `documentation/marvis-actions-api-endpoints.md` and the record folder `specs\numbered\0\0\1\0\1\3\3\1\3341-menu-270-live-resolve-evidence\`.
  4. Commit with the message `docs(marvis): correct menu 270 live resolve status`. The commit body holds `Refs #3341`.
  5. Open the pull request with the same title. The body holds `Refs #3341`, the local gate results, and the note that the owner live check stays open.

  Acceptance: `gh pr view docs/3341-menu-270-live-resolve-evidence --json body` shows `Refs #3341`, and it shows no `Closes #3341`. No local gate applies to a pull request body. Status: open.

- **T-REMOTE-CI** [US2] Watch the CI run. Requirements: SC-003. Depends on: T-PR. Command: `gh pr checks docs/3341-menu-270-live-resolve-evidence --watch`. Acceptance: every required check reports success. Read each failed job before a repair. Do not change a required status name. No local gate applies, because the CI run replaces it. Status: open.

- **T-MERGE** [US2] Review, then merge. Requirements: FR-014. Depends on: T-REMOTE-CI. Steps: the owner reviews the pull request, because the issue carries the `needs-human-review` label. The agent adds no `auto-merge` label until the owner and the orchestrator authorize the merge. The merge is a squash merge. The branch is removed after the merge. Acceptance: one squash commit reaches `main`, and issue #3341 stays open. Verification: `gh pr view docs/3341-menu-270-live-resolve-evidence --json state,mergedAt`. No local gate applies to a merge. Status: open.

## Requirement Traceability

| Requirement | Tasks | Test or owner step |
| - | - | - |
| FR-001 | T004 | Owner approval record. Owner step. |
| FR-002 | T004 | `test_operation.py`, `test_the_preview_lists_the_oldest_action_first`, line 526 |
| FR-003 | T004 | `test_selection.py`, `test_any_other_text_does_not_confirm`, line 478. `test_operation.py`, `test_a_wrong_or_blank_confirmation_changes_nothing`, line 560 |
| FR-004 | T004 | `test_operation.py`, `test_a_blank_alarm_confirmation_records_not_sent_and_calls_no_ack_endpoint`, line 494 |
| FR-005 | T005 | `test_operation.py`, `test_the_results_file_holds_one_row_for_each_action`, line 444 |
| FR-006 | T005 | `test_operation.py`, `test_the_results_file_holds_one_row_for_each_action`, line 444 |
| FR-007 | T004, T005 | `test_operation.py`, `test_the_confirmed_run_resolves_each_open_action`, line 432. `test_operation.py`, `test_an_accepted_request_without_a_closed_status_is_unverified`, line 605 |
| FR-008 | T004 | Owner rule in decision D-2. `test_operation.py`, `test_a_refused_request_is_an_error_row`, line 594 |
| FR-009 | T003, T006 | `ste-linter` and `markdown-link-check` in T-LOCAL-GATES, and a text check of the report |
| FR-010 | T005 | Owner record template in `design\contracts\live-evidence-record.md`. No automated test covers this rule. |
| FR-011 | T004 | Owner step. No automated test covers this rule. |
| FR-012 | T001, T002, T-LOCAL-GATES | The 22 tests of the test set below |
| FR-013 | T-PR | A diff check that `src/foundation/support/utils/operation_registry.py` has no change |
| FR-014 | T-PR, T-MERGE | The `gh pr view` body check in T-PR |

## Offline Test Set

The test set holds 22 test functions. Each row names the file, the class, the function, and the line on `main`.

| # | File | Class | Function | Line |
| - | - | - | - | - |
| 1 | `tests/unit/marvis/actions/test_client.py` | `TestResolveRequest` | `test_the_request_goes_to_the_labs_suggestions_path` | 361 |
| 2 | `tests/unit/marvis/actions/test_client.py` | `TestResolveRequest` | `test_the_body_reaches_the_api_unchanged` | 367 |
| 3 | `tests/unit/marvis/actions/test_client.py` | `TestResolveRequest` | `test_every_success_status_returns_no_error` (200, 201, 204) | 375 |
| 4 | `tests/unit/marvis/actions/test_client.py` | `TestResolveRequest` | `test_a_refused_request_returns_the_status_and_the_body` | 381 |
| 5 | `tests/unit/marvis/actions/test_client.py` | `TestResolveRequest` | `test_a_server_error_returns_the_status_and_the_body` | 388 |
| 6 | `tests/unit/marvis/actions/test_client.py` | `TestResolveRequest` | `test_a_missing_answer_returns_no_status` | 404 |
| 7 | `tests/unit/marvis/actions/test_client.py` | `TestResolveRequest` | `test_a_refused_request_without_a_body_names_the_status_only` | 412 |
| 8 | `tests/unit/marvis/actions/test_operation.py` | `TestResolve` | `test_the_confirmed_run_resolves_each_open_action` | 432 |
| 9 | `tests/unit/marvis/actions/test_operation.py` | `TestResolve` | `test_the_results_file_holds_one_row_for_each_action` | 444 |
| 10 | `tests/unit/marvis/actions/test_operation.py` | `TestResolve` | `test_a_blank_alarm_confirmation_records_not_sent_and_calls_no_ack_endpoint` | 494 |
| 11 | `tests/unit/marvis/actions/test_operation.py` | `TestResolve` | `test_the_preview_lists_the_oldest_action_first` | 526 |
| 12 | `tests/unit/marvis/actions/test_operation.py` | `TestResolve` | `test_a_wrong_or_blank_confirmation_changes_nothing` | 560 |
| 13 | `tests/unit/marvis/actions/test_operation.py` | `TestResolve` | `test_the_cap_resolves_the_oldest_actions_first` | 584 |
| 14 | `tests/unit/marvis/actions/test_operation.py` | `TestResolve` | `test_a_refused_request_is_an_error_row` | 594 |
| 15 | `tests/unit/marvis/actions/test_operation.py` | `TestResolve` | `test_an_accepted_request_without_a_closed_status_is_unverified` | 605 |
| 16 | `tests/unit/marvis/actions/test_operation.py` | `TestResolve` | `test_a_failed_verify_read_leaves_the_rows_unverified` | 618 |
| 17 | `tests/unit/marvis/actions/test_operation.py` | `TestResolve` | `test_the_stop_signal_ends_the_run_between_two_requests` | 645 |
| 18 | `tests/unit/marvis/actions/test_operation.py` | `TestResolve` | `test_an_action_without_a_row_key_is_skipped` | 658 |
| 19 | `tests/unit/marvis/actions/test_selection.py` | `TestConfirmation` | `test_any_other_text_does_not_confirm` | 478 |
| 20 | `tests/unit/marvis/actions/test_selection.py` | `TestResolveRequest` | `test_the_body_holds_the_five_fields_of_the_mist_ui` | 546 |
| 21 | `tests/unit/marvis/actions/test_selection.py` | `TestResolveRequest` | `test_the_body_never_sends_the_suggestion_id` | 557 |
| 22 | `tests/unit/marvis/actions/test_portal_contract.py` | `TestPortalRuns` | `test_a_blank_confirmation_shows_the_count_and_sends_nothing` | 316 |

## Dependency Order

- T001 and T002 come first. T003 depends on both.
- T004 is owner-only. T005 depends on T004. T006 depends on T005.
- T-LOCAL-GATES depends on T003. T-PR depends on T-LOCAL-GATES. T-REMOTE-CI depends on T-PR. T-MERGE depends on T-REMOTE-CI.
