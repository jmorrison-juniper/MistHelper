# Implementation Plan: Other-Device Event Export Fails Closed on Failed Pages

**Branch**: `fix/4709-other-device-events-page-failures` | **Date**: 2026-11-26 | **Spec**: [spec.md](./spec.md)

**Input**: Record folder `specs\numbered\0\0\1\2\2\3\1\4\4709-other-device-events-page-failures`.

## Summary

Replace the `mistapi.get_all` call in menu 258 with a page loop. The loop checks each search page before it accepts rows. It requests each later page with `mistapi.get_next`. It rejects every incomplete read, so the writer runs only for a complete read. The menu keeps its no-data message, its site resolver, and its outer error guard.

## Technical Context

**Language/Version**: Python 3.15 or newer (`pyproject.toml`, line 23).

**Primary Dependencies**: `mistapi` 0.64.1 (`requirements.txt`, line 129). The installed distribution is `mistapi-0.64.1.dist-info`. No new dependency.

**Storage**: Output through `DataExporter.write_with_format_selection` (CSV, SQLite, or ArangoDB). Unchanged.

**Testing**: pytest unit tests with mocks in `tests/unit/export/`.

**Target Platform**: Windows 11, macOS, and Linux, plus the Podman container (`.github/copilot-instructions.md`, line 8 section).

**Project Type**: Menu-driven command-line tool.

**Performance Goals**: One request for each search page. No new concurrency.

**Constraints**: ASCII log output. No secret in a log message. No direct HTTP request. Each function holds 25 lines or fewer, five parameters or fewer, and five logical blocks or fewer.

**Scale/Scope**: One source file, one test file, one changelog fragment, and this record.

## Constitution Check

| Rule | Result | Reason |
| - | - | - |
| I. Five-item rule, structure | PASS | The change adds no directory under a noncompliant parent. `src/operations/exporting/export/` receives no new child. The record route adds one level for each digit, and each level holds one child. |
| I. Five-item rule, functions | PASS (plan) | The design splits the logic into helpers. Task T007 checks the 25-line, five-parameter, and five-block limits. |
| II. Class-based architecture | PASS | Each helper is a static method of `SiteOtherDeviceEventsExporter`. No wrapper function is added. |
| III. Safety-first input | PASS | No new prompt is added. Site selection stays in `_resolve_site_for_stats` (RC-14). No secret reaches a log message (FR-011). |
| IV. Deployment pipeline | PASS (plan) | Steps 1 to 11 map to T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE. Step 12, deploy, stays an owner action after the revision check (RC-43). This record claims no deployment. |
| V. Observability | PASS | All new messages use ASCII. Levels follow the rule: INFO before a request, DEBUG after a response, and ERROR for a failure. |
| VI. Inline comments | PASS (plan) | Task T007 requires an inline comment on each changed line (RC-38). |
| VII. Action logging | PASS (plan) | Tasks T003 to T006 require an INFO line before each request and a DEBUG line after it (RC-39). |
| Technology: mistapi only | PASS | FR-015 limits requests to `searchSiteOtherDeviceEvents` and `get_next` (RC-37). No owned transport is proposed. |
| Output backends | PASS | The writer remains the only output path (FR-013). |
| Database keys | PASS | The composite key in the strategy at line 529 stays unchanged (RC-12, FR-017). |
| Data directory | PASS | The change adds no output path. Tests use `tmp_path` and write nothing under `data/`. |
| Multi-agent git | PASS (plan) | The branch starts from `main` (D-1). No open pull request touches the owned files (RC-55). The handoff gate applies (D-2). |
| Labels | PASS (plan) | The issue keeps `bug`, `tests`, and `in-progress`. The change adds `src` and `severity:high` (D-12). |
| Documentation | PASS | The changelog fragment is required (FR-020). The README and operator guide hold no text for this behavior. A search of `README.md` and `documentation/` found no match. |
| Specification | PASS | The change touches three files and two classes, so this record is required under the repository specification rule. |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/2/3/1/4/4709-other-device-events-page-failures/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      menu-258-outcome.md
      search-page-response.md
    checklists/
      requirements.md
      security.md
```

### Source Code (repository root)

```text
src/operations/exporting/export/site_other_device_events_exporter.py   (modify)
tests/unit/export/test_site_other_device_events_exporter.py            (modify)
changelog.d/issue-4709-other-device-events-page-failures.md            (add)
```

**Structure Decision**: Keep the logic inside the existing exporter class. Add no module and no directory. The exporter is the only source file that changes.

## Change Map

| Path | Action | Change | Requirements |
| - | - | - | - |
| `src/operations/exporting/export/site_other_device_events_exporter.py` | modify | Add page validation, the next-page loop, and the total check. Route `other_device_events` through the loop. Keep `_persist_events` and the outer guard. | FR-001 to FR-019 |
| `tests/unit/export/test_site_other_device_events_exporter.py` | modify | Add 16 test cases (Test 7 holds two cases). Update one existing test that patches `mistapi.get_all`. Keep four other existing tests. | FR-001 to FR-017, FR-019 |
| `changelog.d/issue-4709-other-device-events-page-failures.md` | add | One `###` heading and one `Fixed` bullet that names issue #4709. | FR-020 |
| `specs/numbered/0/0/1/2/2/3/1/4/4709-other-device-events-page-failures/` | add | This record. | Record |

Not changed: `MistHelper.py`, `web_portal/`, `src/foundation/`, the organization exporters, `README.md`, `CHANGELOG.md` (forbidden on a feature branch), and every documentation page.

## Design

The names below are proposals. The implementer may rename a private helper, but the behavior and the test cases stay the same.

1. `other_device_events()` keeps its site resolution, its start logs, and its outer guard (lines 56 to 89 in RC-01).
2. It calls `mistapi.api.v1.sites.otherdevices.searchSiteOtherDeviceEvents(mh.apisession, site_id)` once (FR-016).
3. It passes the response to `_collect_all_pages(session, first_response, site_name)`. That method returns the rows of a complete read or raises `RuntimeError` (D-8).
4. `_collect_all_pages` loops over the pages. For each page it calls `_validate_page`, appends the rows, and reads `next`. It rejects a repeated `next` value (FR-006). It stops when `next` is absent or empty.
5. `_validate_page(response, page_number, site_name)` checks the status (FR-001 to FR-003) and the body shape (FR-004). It logs an ERROR line and raises on failure. For a malformed body, it calls `ResponseIntegrityChecker.body_failed_to_parse` (RC-19) to name the cause.
6. `_next_page(session, response, page_number, site_name)` logs an INFO line, calls `mistapi.get_next(mist_session=session, response=response)`, and logs a DEBUG line. It raises when the SDK returns `None` for a page that has a `next` value.
7. `_check_total(total, row_count, site_name)` compares the row count with `total` from the body, or with `X-Page-Total` when the body has no `total`. It rejects a non-integer header (FR-007, FR-008). It accepts the read when no page reports a total (A-2).
8. `_persist_events(rawdata, site_name)` keeps its signature and behavior (FR-012, FR-013, FR-017).

## Test Plan

All tests stay in `tests/unit/export/test_site_other_device_events_exporter.py`. Each test patches the SDK search function, `mistapi.get_next`, the site resolver, and the writer. Any file path comes from `tmp_path`. Each `get_next` mock uses a finite `side_effect` list, so a missing guard raises an error and does not loop.

| Test | Proposed name | Setup | Expected result | Requirements |
| - | - | - | - | - |
| 1 | `test_failed_first_page_writes_nothing[empty_body_200]` | First response has status 200 and an empty body. | No writer call. ERROR line. No no-data message. | FR-004, FR-009, FR-010 |
| 2 | `test_failed_first_page_writes_nothing[malformed_body_200]` | First response has status 200 and malformed JSON. | No writer call. ERROR line. | FR-004, FR-009 |
| 3 | `test_failed_first_page_writes_nothing[http_403_json]` | First response has status 403 and a JSON error. | No writer call. ERROR line that names HTTP 403. No no-data message. | FR-001, FR-009, FR-010 |
| 4 | `test_failed_first_page_writes_nothing[http_503_json]` | First response has status 503 and a JSON error. | No writer call. ERROR line that names HTTP 503. | FR-001, FR-009 |
| 5 | `test_failed_first_page_writes_nothing[no_status_transport]` | First response has no integer status. | No writer call. ERROR line. | FR-003 |
| 6 | `test_unknown_site_404_logs_error_without_raise` | First response has status 404. | ERROR line that names HTTP 404. The call returns without an exception. | FR-001, FR-014 |
| 7a | `test_later_page_http_503_writes_nothing[list_with_headers]` | Page 1 is a list with one row, `X-Page-Total` 2, `X-Page-Limit` 1, and `X-Page-Page` 1. `next` is set from the headers. `get_next` returns status 503 with an empty body. This is the issue's second case. | No writer call. ERROR line that names page 2. | FR-002, FR-009, FR-010 |
| 7b | `test_later_page_http_503_writes_nothing[dict_with_next]` | Page 1 is an object with one row and a `next` value. `get_next` returns status 503 with an empty body. | No writer call. ERROR line that names page 2. | FR-002, FR-009, FR-010 |
| 8 | `test_non_object_row_rejects_page` | A 2xx page holds a row that is a string. | No writer call. ERROR line. | FR-004 |
| 9 | `test_repeated_next_cursor_rejects_read` | Page 2 repeats the `next` value of page 1. | No writer call. ERROR line that names the repeated cursor, and the cursor value is absent. | FR-006, FR-010 |
| 10 | `test_total_mismatch_rejects_read` | One row, `total` 2, and no `next` value. | No writer call. ERROR line that names both counts. | FR-007, FR-009 |
| 11 | `test_non_integer_x_page_header_rejects_read` | `X-Page-Total` is 2, `X-Page-Limit` is 1, and `X-Page-Page` is not an integer. | No writer call. | FR-008, FR-009 |
| 12 | `test_complete_empty_read_prints_no_data_message` | A 200 page with an empty `results` list and `total` 0. | The no-data message appears. No writer call. This guard passes on the current code. | FR-012 |
| 13 | `test_complete_two_page_read_writes_once` | Page 1 has one row and a `next` value. Page 2 has one row, no `next`, and `total` 2. | One writer call with two rows. `api_function_name` is `searchSiteOtherDeviceEvents`. `get_next` is called with keyword arguments. The test patches `mistapi.get_all` with a mock, and the mock is not called. | FR-005, FR-013, FR-015, FR-016 |
| 14 | `test_failure_logs_omit_body_cursor_and_url` | A failed page has a body that holds a credential-like value and a cursor. | An ERROR line appears. No log message contains the body text, the cursor, or the URL. | FR-011 |
| 15 | `test_successful_page_logs_before_and_after_request` | Page 1 has one row and a `next` value. Page 2 succeeds. | An INFO line names page 2 before its request. A DEBUG line names page 2 after it. | FR-019 |

Retained existing tests:

| Existing test | Test file line | Action |
| - | - | - |
| `test_primary_key_strategy_uses_mac_and_timestamp` | 21 | Keep. Covers FR-017. |
| `test_empty_results_do_not_write_an_export` | 28 | Keep. Covers FR-012. |
| `test_persistence_routes_flattened_rows_and_operation_name` | 38 | Keep. Covers FR-017. |
| `test_menu_entry_resolves_site_calls_sdk_and_persists_rows` | 52 | Update. Replace the `mistapi.get_all` patch (line 66) with a 200 response whose `results` and `total` match the rows. Keep the SDK call assertion (line 70) and the persistence assertion (line 71). Covers FR-016. |
| `test_sdk_failure_is_logged_without_raising` | 74 | Keep. Covers FR-014. |

## Implementation Outline

1. Wait for the #1794 handoff, then check the base blob (T001).
2. Write Tests 1 to 15 before the fix. Confirm that the new failure tests fail on the current code (T002).
3. Add `_validate_page` with status and body checks (T003).
4. Add `_next_page` and the loop with the cursor guard (T004).
5. Add `_check_total` for `total` and the `X-Page-*` headers (T005).
6. Route `other_device_events` through `_collect_all_pages`. Update the one existing menu test (T006).
7. Add the inline comments and action logs. Check the function size and the complexity (T007).
8. Add the changelog fragment (T008).
9. Run the gates and open the pull request after the orchestrator authorizes (T-LOCAL-GATES, T-PR).

## Decisions

The full decision list, with alternatives and risks, is in `design/research.md`. The decisions that shape this plan are D-1 (base on `main`), D-2 (handoff gate), D-3 (fail closed), D-4 (`get_next` instead of `get_all`), D-5 (completeness rules), D-6 (unchanged request), D-7 (no raise to the menu loop), D-8 (`RuntimeError` and no module-level name), D-9 (outer guard unchanged), and D-10 (module logger).

## Dependencies

- `mistapi` 0.64.1 functions `searchSiteOtherDeviceEvents` (RC-70) and `get_next` (RC-67, RC-73).
- `ResponseIntegrityChecker` in `src/mist/access/api/response_integrity.py` (RC-19).
- The #1794 owner handoff (gate, FR-021).
- Orchestrator authorization for each push, pull request, and merge (D-13).

## Risks and Mitigations

- **R-1**: The handoff is delayed. Mitigation: no edit happens before the handoff. T001 holds the gate.
- **R-2**: The #1794 owner's later local correction conflicts with this change. Mitigation: the handoff names the file and the commit. The implementer rebases onto `main` only after the handoff.
- **R-3**: Live responses omit `total`. Mitigation: the `next` checks still apply. Tests 10 and 11 cover the header and body checks. Unverified item U-2 records the gap.
- **R-4**: Pagination continues without end when the API sends new cursors. Mitigation: a repeated cursor fails the read (Test 9). This change adds no page cap. A page cap is a follow-up candidate (D-5).
- **R-5**: `symbol-diff` reports a module-level change. Mitigation: D-8 adds no module-level name.
- **R-6**: The test quality gate flags a new test. Mitigation: each test asserts a writer call or a log line. `documentation/quality-gates.md` describes the ratchet (RC-42).
- **R-7**: An operator sees two ERROR lines for one failure. Mitigation: the page line and the outer summary line have different text. The contract in `design/contracts/menu-258-outcome.md` names both lines.
- **R-8**: A force push to a shared branch removes the commits of another agent.

Warning: a force push to a shared branch removes the commits of other agents. Do not force push. Use a new commit on the feature branch.

## Rollback

1. Revert the squash commit through a new pull request, or restore the previous exporter and test files.
2. Remove `changelog.d/issue-4709-other-device-events-page-failures.md` in the same change.
3. No data migration, schema change, or stored state exists. Existing CSV files stay unchanged.

Caution: a rollback restores the silent partial export. Rerun menu 258 after the rollback when a complete file is needed.

## Complexity Tracking

Not applicable: the Constitution Check holds no violation that needs a justification.
