# Specification Analysis Report: Menu 97 SQLite Write Status

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
| - | - | - | - | - | - |
| A-1 | Status drift | HIGH | Issue #4722, PR #4834, exporter lines 252 to 263 | Remote main already stops on a False SQLite result. The issue stays open because the partial batch is not fixed. | Record the partial status in the issue summary. Use `Closes #4722` only in the pull request that fixes the partial batch. |
| A-2 | Coverage gap | HIGH | Extended exporter test module, no partial-batch test | Remote main has no test for a partial batch. The three SQLite tests cover only a False result. | Add TC-10 and TC-11 with the real writer, and add the writer tests TC-01 to TC-04. |
| A-3 | Contract conflict | MEDIUM | Writer lines 459 to 475, writer test lines 636 to 655 | Issue #3350 pins a partial batch to True. Changing the default would break that contract. | Keep the default. Add the opt-in flag. TC-04 and the existing test guard the default. |
| A-4 | Shared file | HIGH | `data_exporter.py`, open PR #4813 | Open PR #4813 changes `data_exporter.py` and `test_data_exporter.py`. Two open pull requests on one file break the coordination rule. | Run T001 before any edit. Start T-PR after #4813 merges, or after the owner gives a handover. |
| A-5 | Weak verification | MEDIUM | Writer lines 502 to 521 | `_commit_and_verify` counts all rows in the table, not the rows of one batch. Its log line does not prove that a batch stored its rows. | Do not use this count as batch proof. The full-batch rule uses the writer row counts from the batch. |
| A-6 | Key collapse | MEDIUM | Key strategy line 267, writer line 362 | `INSERT OR REPLACE` counts a replaced row as stored. Issue #4723 reports that distinct events can replace each other. | Keep the key defect in issue #4723. The full-batch rule counts accepted rows only. The rule does not prove unique storage. |
| A-7 | Ignored result | LOW | Exporter line 123 | The empty-result branch ignores the return value of `write_with_format_selection`. The branch logs no success message. | Out of scope. Consider a follow-up if the owner requires the result. |
| A-8 | Unverified contract | HIGH | Exporter lines 175, 214, and 334. OpenAPI lines 60227 and 94038 to 94041 | The OpenAPI file says `next` can be a cursor or a URL. The exporter passes the raw value as `search_after`. A URL would break pagination. | Unverified. No live request was made. Open a new issue for a read-only API check. Do not change the pagination code in this record. |
| A-9 | Mirror behavior | LOW | Data exporter lines 176 to 180 | The polyglot mirror runs after the SQLite result. It can store rows from a discarded SQLite batch. | Keep the behavior. Decision D-9 explains the choice. |
| A-10 | Constitution debt | MEDIUM | Plan section Touched Existing Violations | The change touches noncompliant classes and one overlong function. | Record the debt in the plan. Remediation actions R-1 to R-3 are outside this change. |
| A-11 | Owner step | MEDIUM | Constitution line 143 | Principle IV steps 10 to 12 need the owner. The agent does not deploy. | The orchestrator runs the post-merge checks and the health check after the merge. |
| A-12 | Gate risk | LOW | Symbol and test quality gates | New private helpers can trigger the symbol gate or the test quality gate. | Run T-LOCAL-GATES. Fix each finding before the push. |
| A-13 | Fragment rule | LOW | Changelog guard lines 39 and 45 | The guard needs an allowed name, a heading, a bullet, and a change type word. | T014 meets each rule. The guard test runs in the local gates. |
| A-14 | Shared record | LOW | `changelog.d/issue-4722-export-writes.md` | The merged fragment from PR #4834 describes the first-batch fix. The new record must not edit it. | Add a new fragment. Do not edit the merged fragment. |
| A-15 | Term conflict | LOW | Writer line 464 | The existing writer message uses rolled back. The new message uses discarded. The record keeps the existing text. | Align both messages in a later change. Keep one term for each concept. |
| A-16 | Trigger semantics | MEDIUM | Issue comment IC_kwDOQltU8c8AAAABkoggfg | The trigger rejects one row in the issue reproduction. The record has no local run that proves the behavior. | TC-10 must prove the behavior before the change passes review. |

## Coverage Summary

| Requirement | Has Task | Task IDs | Test IDs | Notes |
| - | - | - | - | - |
| FR-001 | Yes | T002 | Existing test line 574, TC-08 | Verified on remote main. |
| FR-002 | Yes | T003 | Existing test line 597, TC-10 | Verified on remote main. |
| FR-003 | Yes | T003 | Existing tests lines 574 and 597, TC-10, TC-11 | Verified on remote main. |
| FR-004 | Yes | T006, T010, T011, T012 | TC-01, TC-04, TC-05 | Absent on remote main. |
| FR-005 | Yes | T006, T011 | TC-02, TC-03, TC-10 | Absent on remote main. |
| FR-006 | Yes | T008, T013 | TC-08, TC-09 | Absent on remote main. |
| FR-007 | Yes | T004 | Existing writer test line 636 | Verified on remote main. |
| FR-008 | Yes | T007, T012 | TC-05, TC-06, TC-07 | Absent on remote main. |
| FR-009 | Yes | T005 | Existing CSV tests, TC-09 | Verified on remote main. |
| FR-010 | Yes | T014 | Changelog guard test | Absent on remote main. |

## Constitution Alignment

- The five-item rule is recorded as debt. The change adds no direct child to a noncompliant directory.
- Class-based design holds. The helpers are methods of the owning classes.
- Safety rules hold. The change adds no external input and no secret.
- Output backend rules hold. Full-batch writes use `write_with_format_selection`.
- Inline comment and action logging rules apply to each new line. T010 to T013 carry these requirements.

## Unmapped Tasks

None. Each task maps to at least one requirement.

## Metrics

- Requirements: 10.
- Tasks: 18. Four tasks are verified present, one is partial, eight are absent, one is an open precondition (T001), and four are delivery tasks.
- Tests planned: 11.
- Remote checks: 106. The count matches `design/research.md` and `META_DIR\4722-STATUS.json`.
- Decisions: 10. None needs a human decision.

## Convergence After Implementation

- Every SQLite batch request carries `require_full_batch=True` from the exporter.
- A partial batch in a full-batch request returns False and stores none of its rows.
- A False result stops the export before the checkpoint advances or completion logs.
- The default writer result for other callers stays True for a partial batch.
- Remote CI passes on the pull request, and the merge closes issue 4722.

## Unresolved Items

- A-8: The Mist API `next` value format is unverified. A new issue must track it.
- A-4: The sequencing with PR #4813 is open until #4813 merges or the owner gives a handover.
- A-9: The polyglot mirror keeps its current behavior after a rejected batch.
- A-15: The writer uses two terms for the same action. A later change must align them.
