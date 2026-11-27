# Specification Analysis Report: MSP inventory batch coverage

## Review Scope

The review covered these sources:

- The issue body and six owner comments on #4708.
- Local commits `5b25a48e` and `eaae12d3`, and the legacy record in them.
- The `main` files that the record cites, checked through the GitHub API and the local index.
- The pinned mistapi 0.64.1 files in `.venv`.
- The local OpenAPI file.

The review checked consistency among `spec.md`, `plan.md`, `tasks.md`, and the remote code. The review ran no build, test, or linter.

## Consistency Results

| Check | Result |
| --- | --- |
| Each FR maps to at least one task and at least one test. | Pass. The mapping appears in `tasks.md`, and the test list appears in `design/checklists/tests.md`. |
| Each task names exact paths and one verification command from the Local gates table. | Pass. |
| The planned test count (8) equals the new tests in T003 (5), T005 (1), and T008 (2). | Pass. |
| The remote check count in `STATUS.json` (39) equals the row count of the remote table in `design/research.md` (39). | Pass. The summary states the same count. |
| Each task status is `open`, except T001, which is `verified-present`. | Pass. |
| Existing test lines keep their positions. | Pass by design. New tests append at the end. |
| The feature root and the `design` folder hold five children or fewer. | Pass. |

## Findings

| ID | Finding | Evidence | Resolution |
| --- | --- | --- | --- |
| AN-01 | The legacy plan states Python 3.13 or newer. | Legacy `plan.md` in commit `eaae12d3`. `pyproject.toml` line 23 requires `>=3.15` (check R-13). | This record states Python 3.15. The legacy text is not reused. |
| AN-02 | The legacy baseline names commit `3964d21d` as the current `main`. | The `main` ref is `f03c6c9b` (checks R-01 and R-02). | This record uses `f03c6c9b`. |
| AN-03 | The legacy repair changes the complete footer for every batch. | The legacy `_report_batch_coverage` prints `complete. Succeeded: N. Skipped or failed: M.` The `main` footer reads `Processed N organizations` (check R-14). The owner asks to preserve successful batch behavior (comment IC_kwDOQltU8c8AAAABkerCbA). | Decision D-3 keeps the complete footer unchanged. |
| AN-04 | The legacy repair keeps export names for partial batches. | Legacy `design/contracts/console.md` keeps the file names. A partial CSV then carries the name of a full MSP report. The issue states that a partial report must not claim full coverage. | Decision D-5 adds the `_Partial` marker. |
| AN-05 | The follow-up test blob `841d9397` is missing. | GitHub returns HTTP 404 for the blob (check R-09). The local object store lacks the blob (check R-10). The working test blob is `44475247` (check R-20). | FR-009 adds a new test. The record does not depend on the missing blob. |
| AN-06 | The legacy record cites local test results that cannot be reproduced here. | The legacy `analysis.md` reports counts such as 55 passing tests and a 1,124-test snapshot. No hosted CI ran (comment IC_kwDOQltU8c8AAAABku0z0Q). | Unverified item U-01. The record does not reuse these results. |
| AN-07 | The legacy tasks are all marked complete. | Legacy `tasks.md` marks T001 through T008 as done. The evidence is local only. | This record marks T001 as verified-present and each other task as open. |
| AN-08 | The owner names an outstanding decision that the issue does not state. | Comment IC_kwDOQltU8c8AAAABkfIWFg says not to merge or close without the outstanding decision. The text of that decision does not appear in the issue. | Unverified item U-04. Decision D-9 holds publication. The owner must name the decision. |
| AN-09 | The owner says that 27 pull request head IDs were rechecked. | The search `gh pr list --search 4708` returns no pull request. The 27 IDs appear in no tracked file. | Unverified item U-03. The record does not repeat that claim. |
| AN-10 | The operator guide says that the `msp` grant follows each page. | `documentation/operator-guide.md` line 606 makes the claim (check R-33). The batch calls `listMspOrgs` once (check R-18). The pinned `mist_get` makes one request (check R-38). The OpenAPI GET operation lists no page or limit parameter (check R-34). | Out of scope. A separate issue owns the paging question. The live behavior stays unverified (U-05). |
| AN-11 | A failed organization listing looks like an empty MSP. | `_call_list_msp_orgs` returns an empty list after an exception, at lines 138-141. `execute_msp` then prints the no-organizations message, at lines 509-511. | Out of scope. The issue overlaps #4713. A separate issue owns the fix. |
| AN-12 | The constitution names mistapi `0.59+`. | The section `Technology & Compatibility Constraints` names `mistapi: 0.59+`. The repository pin is `>=0.64.0,<0.65`, as the Language and environment section of `.github/copilot-instructions.md` states. | Out of scope. The owner must update the constitution text in a separate change. |
| AN-13 | The orchestrator class holds 18 methods. The module holds 15 top-level functions. | Counted with the patterns `^    def` and `^def` in the source file. Principle I allows five. | Recorded debt under Principle I in `plan.md`. A separate issue owns the remediation. |
| AN-14 | The `main` source and test blobs equal the local index. | `git ls-files -s` and `git hash-object` both return `36523c13` for the source and `44475247` for the test (checks R-07 and R-20). | The local line numbers equal the remote line numbers. |
| AN-15 | The no-privilege path in `_resolve_active_msp` is the subject of #4713. | Comment IC_kwDOQltU8c8AAAABkgMNtg asks for coordination. `_resolve_active_msp` starts at line 231 and returns `None` when `msp_privileges` is empty. | Out of scope. Coordinate with #4713 before any change to that path. |

## Defects in the Existing Local Repair

The local repair commit `5b25a48e` changes 63 source lines and 109 test lines. The review found these defects:

- D1: The legacy repair changes the complete footer text (AN-03). The change keeps that text.
- D2: The legacy repair keeps the export names of partial batches (AN-04). The change adds the `_Partial` marker.
- D3: The legacy skipped-record line prints an empty name when a record has no name. The `_process_org` function sets `child_org_name` to the record `id`, which is empty. The change falls back to `unnamed record`.
- D4: The legacy follow-up test change exists only in a worktree that this repository does not hold (AN-05). The change adds a new test instead (FR-009).

## Unresolved Items

- U-01 to U-05 appear in `design/research.md`.
- The orchestrator must file separate issues for AN-10, AN-11, and AN-13. This record does not create issues, because the rules forbid GitHub writes in this session.
- The owner must state the outstanding decision in AN-08 before the owner authorizes publication.
