# Specification Analysis Report: Webhook response status

## Findings

- No behavior requirement lacks a task or a test.
- The status gates on `main` reject each defect that the issue names. The gates use the integer range 200 to 299 (R01 to R04).
- The repair adds only comments and debug lines. It changes no gate, no pagination call, and no return value.
- Two Principles block review on `main`. Principle VI lacks inline comments on changed lines (R05). Principle VII lacks debug lines after the SDK calls (R06, R07).
- PR #4852 omitted `Closes #4718`. Issue #4718 is still open, although its fix is on `main`.

## Coverage Summary

| Requirement | Tasks | Evidence |
| - | - | - |
| FR-001 | T001, T009 | List gate at exporter line 76 (R01). Rejection test at line 329 (R10). |
| FR-002 | T003, T009 | Delivery gate at line 138 (R04). Native 403, 500, and 503 tests (R15, R16). |
| FR-003 | T002 | Reader at line 28 (R02). Range at line 22 (R03). Rejection test parameters include Booleans, strings, and floats (R10). |
| FR-004 | T001, T003 | Error lines 77 to 81 and 139 to 143 (R01, R04). Rejection test at line 329 (R10). |
| FR-005 | T004 | Valid-empty test at line 355 (R11). |
| FR-006 | T006 | Native selection and writer test at line 393 (R13). Status-200 doubles (R17). Stable selection (R18). |
| FR-007 | T001 to T003 | SDK calls at lines 74 and 134 (R76, R77). No direct HTTP call exists. The tests assert the SDK call signature (`assert_called_once_with` at the 3188 test, R18). |
| FR-008 | T-PR | The diff changes only the exporter and the reserved test module, which the T-PR acceptance checks. Pagination helpers stay unchanged (R78, R80). |
| FR-009 | T009, T011 | Debug line added inside the reader. The planned test is at class line 298 (R09). |
| FR-010 | T010 | Inline comments added to the listed lines. Current gap is R05. No automated test exists for comments. The check is the manual review in T010 acceptance. |
| FR-011 | T012 | `block_network` fixture at test lines 27 and 28. |
| SC-001 | T004, T005 | Rejection tests (R10, R15, R16). |
| SC-002 | T004 | Valid-empty test (R11). |
| SC-003 | T006 | Writer test (R13). Stable selection (R18). |
| SC-004 | T011 | Planned debug-line test. |
| SC-005 | T012 | Offline guard (R09 class). |
| SC-006 | T-PR, T-MERGE | PR #4852 lacks `Closes`. The repair PR must include it. |

## Constitution Alignment

Plan.md gives each rule and its result. The failing rules are these.

- Principle I: `deliveries()` spans 32 lines (R08). The test module holds 11 top-level children (R14). `TestStableWebhookResolver` holds six methods (R19).
- Principle II: the module-level helper `_response_status_code` (R02) sits outside a class.
- Principle VI: changed executable lines lack inline comments (R05).
- Principle VII: no debug line follows the SDK calls (R06, R07).

Principles VI and VII block review under `.specify/memory/constitution.md` (R38, R39). The repair fixes them. Principles I and II stay open under RM-1 to RM-4.

## Legacy Record Review

The legacy folder held eight files: `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, `design/research.md`, `design/data-model.md`, `design/quickstart.md`, and `design/checklists/requirements.md`. Each file was read in full. The review counts 19 claims.

| ID | Legacy claim | Legacy file | Result | Evidence |
| - | - | - | - | - |
| L-01 | Both initial responses are validated before pagination. | spec.md FR-001 | verified | R01, R04 |
| L-02 | Only non-Boolean integer statuses from 200 to 299 are accepted. | spec.md FR-002 | verified | R02, R03 |
| L-03 | A rejected response gives an error without empty or persistence messages. | spec.md FR-003 | verified | R10 |
| L-04 | A valid empty response keeps its notice. | spec.md FR-005 | verified | R11 |
| L-05 | The #4715 writer behavior is preserved. | spec.md FR-005 | verified | R13. PR #4849 merged as commit a3e8a2e7 (R75). |
| L-06 | A native transport failure has a status of None. | research.md | verified | R79 |
| L-07 | The previous helper turned missing or malformed statuses into 200. | research.md | verified | Pre-fix helper default `_HTTP_OK` in the PR #4852 diff, index line `dff2b4d6a..1dbd5f42c` |
| L-08 | The error names a missing or invalid status. | plan.md Summary | verified | R01 (lines 77 to 81) |
| L-09 | The list endpoint has no initial status check. | research.md | stale | Fixed by PR #4852. R01 is the current gate. |
| L-10 | Publication needs a separate decision, and the status is Ready. | spec.md Status | stale | PR #4852 merged on 2026-11-19. |
| L-11 | The branch stays based on commit 520da641. | spec.md Assumptions | stale | R72 shows that 520da641 is not on `main`. R75 is the squash commit. |
| L-12 | The exporter class holds more than five methods. | plan.md Constitution Check | absent | The class holds five static methods, at remote lines 34, 45, 70, 97, and 118. |
| L-13 | The entrypoint is a 32-line function. | plan.md | verified | R08 (lines 119 to 150) |
| L-14 | Python 3.13 or newer is the requirement. | plan.md Technical Context | stale | R34 (the repository states Python 3.15) |
| L-15 | The session file `issue4718/offline_checks.py` runs the offline checks. | quickstart.md | absent | No repository path matches the name. The session folder lies outside the repository. |
| L-16 | The session file `issue4718/export_candidate.py` exports the commit. | tasks.md T008 | absent | No repository path matches the name. |
| L-17 | The changelog fragment exists. | tasks.md T007 | verified | R20 |
| L-18 | The offline guards block socket, DNS, and SQLite access. | quickstart.md | verified | The PR #4852 diff adds `sqlite3.connect` to `block_network`. R09 holds the class. |
| L-19 | The coordinator confirms exclusive ownership of the exporter and both tests. | plan.md Constitution Check | stale | The owner comments of 2026-11-09 expand the ownership. PR #4852 then merged. |

Counts: verified 11, stale 5, absent 3. The legacy claims that the review cannot check appear in `design/research.md` under Unverified (U-5 and U-6).

## Defects in Existing Work

- DA-1: PR #4852 has the body "Refs #4718". The workflow `close-linked-issues` reported SUCCESS and closed no issue. Issue #4718 is open (remote issue state: OPEN).
- DA-2: Changed lines lack inline comments (R05). This breaks Principle VI.
- DA-3: No debug line follows the SDK calls (R06, R07). This breaks Principle VII.
- DA-4: `deliveries()` spans 32 lines (R08). This breaks the 25-line limit. PR #4852 kept the line count, so the violation predates the PR.
- DA-5: PR #4852 added three top-level children to the test module at lines 51, 64, and 298 (R14). The module already exceeded five children.
- DA-6: `TestStableWebhookResolver` holds six methods (R19). This violation predates PR #4852.
- DA-7: The legacy record states stale facts. Examples are L-09, L-10, L-11, and L-14.
- DA-8: The legacy record cites two session files that the repository does not hold (L-15, L-16).
- DA-9: `documentation/MIST_API_MISSING_ENDPOINTS.md` lists both webhook operations as missing (R56). Menus 45 and 256 call them.

## Unresolved Items

- UR-1: The web portal choice provider keeps the missing-status defect (R24, R25). Decision D-1 routes it to a separate issue.
- UR-2: Sibling exporters keep the 200 default (R31, R32). Decision D-11 routes them to separate issues.
- UR-3: The list call has no exception boundary. `_select_webhook_id` (lines 71 to 95, R01) has no `try` block. `deliveries()` calls it at line 126, before its `try` at line 130 (R08). An SDK exception from the list call reaches the menu loop. The specification keeps the existing behavior (FR-006). The owner decides whether to change it.
- UR-4: The image revision label is not checked (U-4).
- UR-5: Local gate results are pending until T-LOCAL-GATES runs.

## Metrics

- Requirements: 11 functional requirements and 6 success criteria.
- Tasks: 16. Twelve implementation and verification tasks and four final tasks.
- Planned tests: 12. Eleven exist, and one is new (T011).
- Remote checks: 87 rows in `design/research.md` and in the status file.
- Decisions: 12. Human decisions: 0.
- Requirement coverage: 100 percent. Each requirement maps to at least one task and one test or planned test.
