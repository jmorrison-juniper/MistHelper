# Analysis: Other-Device Event Export Fails Closed on Failed Pages

**Scope**: Consistency review across `spec.md`, `plan.md`, `tasks.md`, `design/`, and the remote state of `main` on 2026-11-26. This file also lists defects in existing work and unresolved items.

## 1. Requirement Coverage Matrix

Each requirement maps to at least one task. Behavior requirements map to a unit test. Process requirements map to a named verification check, because no unit test can prove them. The check names appear in the Test or check column.

| Requirement | Tasks | Test or check |
| - | - | - |
| FR-001 first page status | T003 | Tests 3, 4, 6 |
| FR-002 later page status | T004 | Tests 7a and 7b |
| FR-003 missing or non-2xx status | T003 | Tests 3, 4, 5, 6 |
| FR-004 body shape and row type | T003, T004 | Tests 1, 2, 8 |
| FR-005 follow `next` until absent | T004 | Test 13 |
| FR-006 repeated cursor rejected | T004 | Test 9 |
| FR-007 row count against `total` | T005 | Test 10 |
| FR-008 integer `X-Page-*` headers | T005 | Test 11 |
| FR-009 no writer call after rejection | T003, T005, T006 | Tests 1, 3, 7, 10, 11 |
| FR-010 one ERROR line per rejected page | T003, T004 | Tests 3, 7, 9 |
| FR-011 no body, cursor, or URL in logs | T003, T007 | Test 14 |
| FR-012 no-data message for a complete empty read | T006 | Test 12 |
| FR-013 one writer call for complete rows | T006 | Test 13 |
| FR-014 no raise to the menu loop | T006 | Test 6 and the retained test at test file line 74 |
| FR-015 mistapi methods only | T004 | Test 13 (keyword call to `get_next`, no `get_all`) |
| FR-016 unchanged first request | T006 | Retained test at test file line 52 (call assertion at line 70) and Test 13 |
| FR-017 filename, operationId, composite key | T006 | Retained tests at test file lines 21 and 38 |
| FR-018 no module-level name added | T006, T-LOCAL-GATES, T-MERGE | Check: `symbol-diff` (T001 and T-LOCAL-GATES) |
| FR-019 inline comments and action logs | T007 | Test 15 and `radon` gate (complexity), with a code review of comments |
| FR-020 changelog fragment | T008 | Check: STE gate on the fragment (T008) |
| FR-021 no edit before the handoff | T001 | Check: `symbol-diff` and the handoff comment (T001) |
| FR-022 no organization or firmware edit | T-LOCAL-GATES | Tests: `python -m pytest tests/unit/export` |

Result: 22 of 22 requirements map to at least one task and at least one test or check.

## 2. Cross-Document Consistency

| Item | Source of truth | Value | Consistent in |
| - | - | - | - |
| Requirement count | `spec.md` | 22 (FR-001 to FR-022) | `tasks.md`, `analysis.md`, `design/checklists/requirements.md`, STATUS |
| Success criteria count | `spec.md` | 6 (SC-001 to SC-006) | `tasks.md` (T-LOCAL-GATES, T-REMOTE-CI) |
| Test count | `plan.md` Test Plan | 16 new cases (Test 7 holds two cases), plus 5 retained tests (4 unchanged, 1 updated) | `tasks.md` T002, STATUS `tests_planned` |
| Task count | `tasks.md` | 12 (T001 to T008, T-LOCAL-GATES, T-PR, T-REMOTE-CI, T-MERGE) | STATUS `tasks` |
| Decision count | `design/research.md` | 14 (D-1 to D-14) | STATUS `decisions` |
| Remote check count | `design/research.md` remote table | 80 (RC-01 to RC-80) | STATUS `remote_checks`, `summary.md` |
| Branch name | `spec.md`, `tasks.md` | `fix/4709-other-device-events-page-failures` | `tasks.md` T-PR |
| Changelog file name | `spec.md` FR-020 | `changelog.d/issue-4709-other-device-events-page-failures.md` | `tasks.md` T008, `plan.md` |
| Record folder | `plan.md` | `specs\numbered\0\0\1\2\2\3\1\4\4709-other-device-events-page-failures` | STATUS `record_dir` |

## 3. Defects and Gaps in Existing Work

Each item names its evidence and its disposition. "Fixed here" means that this change repairs it. "Owner" means that the #1794 owner or another agent must act. "Follow-up" means that a separate issue must track it.

| ID | Finding | Evidence | Disposition |
| - | - | - | - |
| A-1 | The exporter passes the first response to `mistapi.get_all` with no status check. | RC-02 (exporter line 76). | Fixed here (T003, T006). |
| A-2 | `get_all` returns an empty list for a failed first response with a JSON error body. The menu then prints the no-data message. | RC-66 (`__pagination.py` lines 65 and 74) and RC-68 (`__api_response.py` line 39). | Fixed here. The new code does not call `get_all`. |
| A-3 | A list-shaped later page with an empty body adds no rows, and the export reports success. | RC-65 (`__pagination.py` line 62) and RC-68 (default data `{}`, line 39). | Fixed here (Tests 7a and 7b cover both shapes). |
| A-4 | A dict-shaped later page without `results` raises `KeyError` inside `get_all`. The outer guard then reports an error, and the message is not useful. | RC-66 (`__pagination.py` line 71). | Fixed here. The new code reads `results` only after validation. |
| A-5 | Header pagination drops `next` after a non-integer header, and the SDK logs the problem only. | RC-69 (`__api_response.py` lines 76 to 80). | Fixed here (FR-008, Test 11). |
| A-6 | A search response with `total` greater than the row count and no `next` value ends the read silently. This is the owner's first case. | Owner comment IC_kwDOQltU8c8AAAABkfIV2g (RC-61). `total` is defined in the schema (RC-23). | Fixed here (FR-007, Test 10). |
| A-7 | The owner candidate checks status and cursors but has no `total` or header check. | RC-06 (candidate at `196af800`, 146 lines, no `total` text). | Owner. This change covers the case, and the handoff can name the candidate methods that it reuses. |
| A-8 | The owner comment calls the candidate "local and unpublished". GitHub shows that both owner commits are ancestors of the archive branch head. | RC-51, RC-52, RC-53, RC-60. | Recorded. The handoff must name the commit and the branch. |
| A-9 | The issue body names `3964d21` as current `main`. `main` is now `f03c6c9`. | RC-50 and RC-54. | Recorded. The spec uses `f03c6c9`. |
| A-10 | The owner comment says "27 open PR heads". GitHub lists 7 open pull requests, and none touches the owned files. | RC-55. | Recorded. The overlap check repeats at T-PR. |
| A-11 | The organization audit log export checks only the first response status, then calls `get_all`. It has the same defect class. | RC-21 (`org_export_utils.py` lines 766 to 775). | Follow-up (D-14). Out of scope under FR-022. |
| A-12 | The mistapi pin text differs across files. | RC-31 (`>=0.64.1,<0.65`), RC-33 (`==0.64.1`), RC-34 (`>=0.64.0,<0.65`). | Follow-up (D-14). |
| A-13 | Spec 894 states Python 3.13 and mistapi 0.59 in its non-functional requirements. Its plan names mistapi 0.63.3 and `get_all`. | Observation only. Files in `specs/894-mist-search-site-other-device-events/`. These lines are not a dependency of this record. | Recorded. Superseded by this record. No edit in this change. |
| A-14 | The test module holds no HTTP 4xx or 5xx case. The copilot-instructions test quality rule requires one for each new API client test module. | RC-09 and RC-74 (copilot-instructions line 253). | Fixed here (Tests 3, 4, 6). |
| A-15 | The outer guard uses `except Exception` and root `logging` calls. The module logger exists at line 20 but the guard does not use it. | RC-04 (exporter lines 20, 83 to 89). | Owner (#1794). This change uses the module logger for new lines (D-10). |
| A-16 | The search time window defaults to `duration` `1d`. An export without a duration covers one day. | RC-71 (SDK docstring, line 115 and line 186). | Recorded. Out of scope (A-4 in the spec). |

## 4. Unresolved Items

| ID | Item | Impact | Owner |
| - | - | - | - |
| U-1 | The #1794 owner handoff is not posted. | T001 blocks every edit. | #1794 owner |
| U-2 | Live search pages may omit `total`. The schema does not require it (RC-23). | FR-007 does not apply to such a page. FR-008 and `next` still apply. | Live validation, outside this change |
| U-3 | The owner's "local correction" (comment IC_kwDOQltU8c8AAAABkfhU5w) is not on GitHub. No commit names it. | The change cannot compare the correction. The handoff must name a commit. | #1794 owner |
| U-4 | Transport failures outside the SDK request layer are unverified. RC-72 shows the layer returns an `APIResponse`. | Any exception that escapes the layer reaches the outer guard (A-6 in the spec). | Implementer, checked by Test 5 and the outer guard |
| U-5 | Follow-up issues for A-11 and A-12 are not filed. | No tracking exists until filed. | Orchestrator |
| U-6 | The API default time window for the search (A-16) may not match operator expectations. | Out of scope. | Product owner |

## 5. Verification Summary

- Verified on GitHub: rows RC-01 to RC-63, RC-74, and RC-75 to RC-80 in `design/research.md`. These cover the remote tree, the blob SHA of each cited file, the commit ancestry, the archive branch head, the open pull request overlap, the issue states, the labels, and the authorization comment.
- Verified locally: the SDK line numbers and the blob SHAs of the installed `mistapi` 0.64.1 files (RC-64 to RC-73), and the local checkout blobs of each cited repository file (method note 5 in research.md).
- Not verified: live Mist API responses, the owner's later local correction, and the outcome of any gate. This record runs no gate, as the brief requires.
