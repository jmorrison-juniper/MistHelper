# Specification Analysis Report: Isolate Network Routing Support Modules

## Findings

| ID | Severity | Area | Finding | Evidence | Action |
| - | - | - | - | - | - |
| F-01 | Critical | Candidate | The preserved candidate payload module predates change `5e890ed6` on `main` (PR #4317). Merging the candidate can revert that security change. | Candidate blob `8e0229b79a05cbd1fab0af56c82608ba991cf28f` (R-10). Main blob `38c2458ff14370be660d956ca30c252dc4fd291c` (R-14, R-52). The candidate parent is `42a160acb3b3719f96221094217c107e900c253f`. | Rebuild from `main` (D-4, T004, T018). |
| F-02 | High | Nested ratchet | The nested-package guard merged in PR #4125 flags the network root after the move. The baseline entry becomes stale. The candidate does not change the baseline. | Baseline object at lines 106 to 110 (R-26). Guard stale check at lines 137 and 148 to 149, and literal report at lines 175 to 179 (R-27). | Remove the entry and change the literal (D-6, T012). |
| F-03 | High | Catalog guard | Three hook rows name old module paths. The catalog guard fails until its move map names the new paths. | Hook rows `hook-0281`, `hook-0283`, and `hook-0284` at CSV lines 282, 284, and 285 (R-25). The move map at guard lines 28 to 38 holds no routing entry (R-24). | Add map entries (D-7, T011). |
| F-04 | High | Queue | Open draft PR #4208 changes the symbol guard file. Only one open pull request can change each file. | PR #4208 is open, draft, and updated 2026-11-22 (R-51). | Hold publication (D-13 condition 1). |
| F-05 | High | Ownership | Issue #4728 is open. It reports an order-dependent failure in `tests/unit/test_routing_utils.py`. The candidate changes that file by 29 insertions and 23 deletions. The owner comments require a narrow handoff. | Issue #4728 state OPEN, updated 2026-11-10. Owner comments of 2026-11-10 (R3). | Obtain the handoff (D-13 condition 2). |
| F-06 | High | Guard quality | The candidate structure guard has one 27-line function. Its lines 67 to 71, 75, and 92 lack inline comments. | Candidate guard lines 55 to 81 and the lines named above (candidate blob `1278e6806026c6d873f23d96f5798449a98d6773`). | Refresh the guard (D-10, T013). |
| F-07 | Medium | Comments | The candidate symbol-guard entries lack inline comments. | Candidate patch adds three entries without comments. | Add comments (T010). |
| F-08 | Medium | Legacy record | Seven of seventeen legacy claims are verified, six are stale, and four are absent. The legacy `plan.md` names Python 3.13. The legacy `spec.md` says "Implemented". The legacy `tasks.md` marks all tasks done. | Legacy blobs `47a1589f11d187c74566b9f615dd3def43575033`, `35ea2420620a1a6574ee4ed35af5c7d5bbfd0d6f`, and `16677e1f44326b4781c976cc3ba58a769d86e82b`. `pyproject.toml` line 23 requires 3.15 (R-43). | Write a new record (D-15). |
| F-09 | Medium | Historical scope | The issue lists records 1780, 198, 1034, and 2448. A code search finds old names in 1778, 1924, and 2448. Records 1780, 198, and 1034 do not name the moved modules. | Code search results (R-48 to R-50). Local search of `specs/`. | Treat all `specs/` files as read-only (A-3, FR-013). |
| F-10 | Medium | Documentation | The issue asks for one active documentation path. Two generated pages name the old path. | `documentation/menu-api/websocket.md` and `documentation/wiki/Menu-API-Endpoints-Websocket.md` at lines 77, 100, and 123 (R-29, R-30). | Regenerate both pages (D-11, T014). |
| F-11 | Medium | Test counts | Owner comments give conflicting counts. One reports 195 passed on 2026-10-06. Another reports 199 collected, 196 passed, and 3 failed on 2026-10-07. | Issue #4006 comments dated 2026-10-06 and 2026-10-07. | Do not copy counts. Measure at implementation (A-6). |
| F-12 | Medium | SDK | The raw `requests.post` call at payload line 250 bypasses mistapi. The installed SDK has no generic endpoint function. The local OpenAPI has no raw endpoint path. | R-42, R-46, and R-14. | Record the debt. Separate issue (D-14). |
| F-13 | Low | Labels | The issue carries scope label `src`. The scope list in `copilot-instructions.md` does not name it. | Issue #4006 labels `refactor`, `networking`, and `src`. | Keep the labels. Add `in-progress` (D-12). |
| F-14 | Low | Branches | Archive branch names do not follow `<type>/<issue>-<slug>`. | Archive refs in `refs/remotes/origin/archive/laptop-20261121/`. | Use `chore/4006-network-routing-support` (D-12). |
| F-15 | Low | Import order | The candidate reorders the import block in `routing_utils.py`. Ruff may require another order. | Candidate patch for `routing_utils.py`. | Run the Lint gate (T005). |
| F-16 | Low | Pre-existing | `routing_utils.py` assigns the module logger twice, at lines 31 and 33. | R-18 and remote decode of `routing_utils.py`. | Not changed. Out of scope. |
| F-17 | Info | Interpretation | The issue says three orchestrators stay at the root. The facade is the fourth root module. | `routing_utils.py` line 113 and the orchestrator classes (R-15 to R-17). | Assumption A-2. |
| F-18 | Low | Guard output | The candidate guard prints counts only on failure. The repository guard rule requires counts on success. | Candidate guard lines 87 to 101. | Print counts on success (FR-016, T013). |
| F-19 | Medium | Limits | Two functions in moved modules have five parameters excluding `self`. One source function in a touched file and nine test functions exceed 25 lines. | Counts in `design/research.md` R5. | Record as debt (plan section "Existing Violations Touched by This Change"). |
| F-20 | High | Structure guard | The active-path scan would flag the approved catalog move map. Its keys are historical old paths with the `src/` prefix. The scan would fail on the change. | `tests/guardrails/test_performance_hook_catalog.py` lines 28 to 37 (R-24). | Exclude that one file from the scan, with a comment (D-7, D-10, T013). |

## Coverage Summary

| FR | Tasks | Test cases |
| - | - | - |
| FR-001 | T004, T018 | TC-11 |
| FR-002 | T004 | TC-08 |
| FR-003 | T013 | TC-01 |
| FR-004 | T013 | TC-01 |
| FR-005 | T004 | TC-01 |
| FR-006 | T005, T010, T013 | TC-08, TC-09 |
| FR-007 | T005, T006 | TC-02 |
| FR-008 | T008, T009 | TC-02, TC-03 |
| FR-009 | T017 | TC-09 |
| FR-010 | T007 | TC-09 |
| FR-011 | T010, T018 | TC-04, TC-14 |
| FR-012 | T014 | TC-10 |
| FR-013 | T011, T016 | TC-05, TC-09 |
| FR-014 | T011 | TC-05 |
| FR-015 | T012 | TC-06 |
| FR-016 | T013 | TC-01 |
| FR-017 | T015 | TC-12 |
| FR-018 | T004, T018 | TC-02, TC-11 |
| FR-019 | T-LOCAL-GATES | TC-15 |
| FR-020 | T-LOCAL-GATES, T-REMOTE-CI | TC-07, TC-14 |
| FR-021 | T001, T002, T003, T-PR, T-MERGE | TC-13, TC-16 |
| FR-022 | T-PR | TC-12 |

## Constrained-Field Coverage

- Every task names one verification command. Process tasks use TC-13 or TC-16.
- Every task names exact repository paths or states that it has none.
- Every requirement maps to at least one task and at least one test case.

## Constitution Alignment

- Principle I: The change meets the five-item rule after T012 and T013. Existing debt is recorded in the plan.
- Principle VI: Added lines in guard and map edits carry inline comments (T010 to T013).
- Principle IV: Gates and publication follow the pipeline. Post-merge steps belong to T-MERGE.

## Unmapped Tasks

None. Each task maps to at least one requirement.

## Metrics

- Requirements: 22 (FR-001 to FR-022).
- Success criteria: 8 (SC-001 to SC-008).
- Tasks: 22 (T001 to T018 and four final tasks).
- Test cases: 16 (TC-01 to TC-16).
- Decisions: 15 (D-1 to D-15). Human decisions: 0.
- Remote checks: 52 (R-01 to R-52).

## Unresolved Items

- Test runs, generator output, and gate results are unverified (research U-1 and U-2).
- PR #4208 status can change before publication (U-10).
- Issue #4728 handoff is pending (D-13 condition 2).
- The serial slot is not assigned (D-13 condition 3).
- The raw HTTP debt needs a separate issue (D-14).

## Convergence After Implementation

After implementation, these checks must pass together: TC-01 to TC-10, TC-11, TC-14, and the local gates table. Then TC-12 confirms the record and fragment are tracked.
