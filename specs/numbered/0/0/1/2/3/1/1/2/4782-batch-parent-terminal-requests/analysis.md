# Specification Analysis: Batch Parent Terminal Requests

**Scope**: Consistency across `spec.md`, `plan.md`, `tasks.md`, and the remote code on `main`. Evidence IDs (R-nn, D-n, U-n, F-x) refer to `design/research.md`.

## Findings

- A-01: The defect in issue #4782 is fixed on `main`. Commit `4e81b2a4a7` added the guard (R-17, R-53). The issue remains open. Resolution: close the issue with the pull request (D-9).
- A-02: The owner comment of 2026-11-15 describes the code before the fix. The guard line was added on 2026-11-25 (research F-C). Resolution: this record replaces the comment's repair path.
- A-03: The owner comment names `origin/feat/4769-ex-hardware-inventory`. GitHub has no such branch (R-56). Local git holds the branch only as `refs/heads/feat/4769-ex-hardware-inventory`. Resolution: this record names the local ref and makes no remote claim about it.
- A-04: The owner comment counts ten open pull requests. Seven were open on 2026-11-26. None lists the held test module or `websockets.js` (R-62, R-63). Resolution: the overlap check passes.
- A-05: The owner comment says commits `8140bb3`, `58ab484`, `07cf3ee`, and `edc12d5` are unavailable. GitHub returns HTTP 422 for each (R-57 to R-60). Resolution: consistent.
- A-06: The owner comment says `isTerminalSession` accepts terminal output without excluding `multi_site`. This was true before commit `4e81b2a4a7`. It is false on `main` now (R-17). Resolution: consistent with the history.
- A-07: The retained commit `c07cb9f8` has no `multi_site` check in `isTerminalSession` (R-55). Merging it removes the guard. Resolution: D-4 and the Caution in research.
- A-08: The existing batch parent test asserts terminal reads only (R-49). The fake resize method records no call (R-41). Resolution: T003 adds the request assertion.
- A-09: No test covers a batch parent after a reload. The reload test (R-47) covers the CSV table only. Resolution: T004 adds the reload test.
- A-10: The constitution requires one fragment for each change (R-65). The changelog README exempts an internal-only change (R-66). Resolution: D-6 follows the README and states the reason in the pull request body.
- A-11: The route adds one child, `1`, to `specs/numbered/0/0/1/2/3/1`. That level holds three children now (R-67), so it holds four after the change. Resolution: the Five-Item Rule passes.
- A-12: No legacy record exists for issue 4782 on `main` (R-15, R-16) or under `specs\`. Resolution: `existing_record.found` is false.
- A-13: The owner comment expected a repair in `websockets.js`. Research shows the repair exists on `main`. Resolution: the implementation becomes a test-only change. The file map in `plan.md` reflects this.
- A-14: Documentation drift exists in `documentation/architecture.md` (U-7). It names the old path `src/mist/realtime/websocket/`. Resolution: out of scope.
- A-15: The Mist OpenAPI file has no match for the portal routes (R-10). Resolution: Mist API behavior is not applicable.
- A-16: The owner HEAD `2a6a5844` exists on GitHub (R-61). The current `main` head is `f03c6c9b` (R-52). Resolution: this record uses `f03c6c9b`.

## Traceability

| Requirement | Tasks | Tests or verification |
| - | - | - |
| FR-001 Page sends no terminal read for a batch parent | T002, T003, T-LOCAL-GATES | `test_a_batch_parent_of_a_shell_action_is_not_opened_as_a_terminal` (changed) |
| FR-002 Page sends no resize request for a batch parent | T003 | Same test (changed) |
| FR-003 Page treats `multi_site` as non-terminal on every path | T002, T004 | `test_a_batch_parent_restored_after_reload_sends_no_terminal_or_resize_request` (new) |
| FR-004 Page keeps terminal requests for terminal sessions | T006, T-REMOTE-CI | `test_j5_resize` (existing, R-50) |
| FR-005 Regression tests fail on a batch parent request | T005 | Both tests under guard removal |
| FR-006 Server keeps HTTP 409 `not_terminal` | T006 | `not_terminal` case (existing, R-51) |
| FR-007 No production file changes | T001, T-PR | File list check with `gh pr view` |

Each requirement maps to at least one task and at least one test or verification. The count is 7 of 7.

## Success criteria mapping

| Criterion | Evidence |
| - | - |
| SC-001 Zero matching requests during 1500 milliseconds | T003 |
| SC-002 Zero matching requests after reload | T004 |
| SC-003 `test_j5_resize` passes in `websockets-tab` | T006, T-REMOTE-CI |
| SC-004 Tests fail without the guard | T005 |
| SC-005 Pull request changes two paths | T-PR, T-MERGE |

## Consistency counts

| Item | Count in `spec.md` or `tasks.md` | Count in `design/research.md` | Count in STATUS | Count in `summary.md` |
| - | - | - | - | - |
| Functional requirements | 7 | Not applicable | `requirements`: 7 | Stated as 7 |
| Tasks | 10 | Not applicable | `tasks`: 10 | Stated as 10 |
| Tests planned | 2 | Not applicable | `tests_planned`: 2 | Stated as 2 |
| Remote checks | Not applicable | 68 rows | `remote_checks`: 68 | Stated as 68 |

## Constitution and process checks

- Five-Item Rule: The record folder holds five children. The `design` folder holds five children (R-67 supports the route count).
- Release note: The constitution requires one fragment (R-65). D-6 documents the exemption under the README (R-66).
- Ownership hold: The test module is held. T001 must pass before any edit.
- Git flow: The pull request uses one commit, one scope, and `Closes #4782`.

## Unresolved items

- HUMAN-DECISION-REQUIRED: The owner chooses the credential source and the staging organization for a live smoke test (D-8).
- Precondition: The owner releases the ownership hold before the test edit (T001).
- Unverified: The live messages route for a batch parent (U-2). The e2e tests use fake services.
- Unverified: Pass or fail status of the existing e2e tests on `main` (U-1). This step ran no test.
- Unverified: Keys of the terminal read success body (U-4) and the server parsing of the resize body (U-5). The contract marks both.
- Residual edge case: The operator selects a batch parent while a terminal session is open. No new test covers this order (`spec.md`, Edge Cases).
