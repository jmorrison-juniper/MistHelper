# Analysis: Persist resumable firmware phase state

**Scope**: Consistency review of `spec.md`, `plan.md`, and `tasks.md`, checked against remote `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. Evidence IDs (RC-###) refer to the remote verification table in `design/research.md`.

## Findings

Each finding names its evidence and the task that repairs it. The "Severity" column uses high, medium, or low.

| ID | Severity | Finding | Evidence | Repair |
| - | - | - | - | - |
| F-01 | high | A single-site firmware call that raises a transport fault or returns a 5xx reply is recorded as a refusal. The operator reads "The cloud refused". | RC-022, RC-023, RC-024. The certainty contract classes these replies as unknown (RC-036). | T002 |
| F-02 | high | A single-site stop or failure releases the site lock. The release does not check whether a firmware reply was unknown. A second operator can then start a second write. | RC-014, RC-015, RC-016. The site lock contract releases at `complete`, `stopped`, or `failed` (RC-039). Tests RC-071 and RC-072 pin the release. | T003 |
| F-03 | high | The multi-site lease releases the site locks at the end of a watch or a stop. The release does not call the settlement predicate. | RC-012 (lease release at 175 and 182), RC-013 (no settlement check in `locks.py`), RC-047 (the predicate exists only in `org_upgrade.py`). Reachability is unverified (U-03). | T015 and a separate issue |
| F-04 | high | The multi-site submission sends every child in one loop with no phase order. | RC-044 (loop at 232). Issue #4021 is open. | T014, blocked by #4021 |
| F-05 | medium | The stop message reads "The run stopped." It names no phase and gives no next step. | RC-009 (line 650). | T013 |
| F-06 | medium | A stop during a settle wait writes no outcome for the phase. The phase has no durable state that describes the stop. | RC-019 (lines 1771 to 1773 return before `_write_phase`). | T007 |
| F-07 | medium | The retry route creates a new run and removes the dispatch fence of the source run. A retry during an unknown outcome can send a new write. | RC-054, RC-055. | T011 |
| F-08 | medium | The reconcile service can mark a failed run `complete` when the evidence proves each target. A resume must not use this outcome for an unresolved phase. | RC-061 (line 465). | T008 |
| F-09 | medium | The operator guide gives the lock life as 300 seconds. The key expiry is 3600 seconds, and 300 seconds is the quiet period. | RC-088 (line 625), RC-038 (contract line 23), RC-041 (`lock.py` line 144), RC-042 (line 190). | T016 |
| F-10 | low | Phase observation treats a failed phase as ended. The observation is read-only. Resume must reset the phase before it observes again. | RC-010, RC-011, RC-073. | T004 |
| F-11 | low | Two tests pin the operator text of the cadence and the warning. Each changed string needs a test change in the same commit. | RC-077, RC-078, and RC-079 (the e2e test expects the text "Stopped"). | T013 |
| F-12 | low | The state machine has no resume transition, and it treats `stopped` as terminal. | RC-006, RC-007, RC-008. | T005 |
| F-13 | low | Eleven code and test folders hold more than five children. The debt predates this change. The changelog folder is a process folder and is allowed. | RC-114 to RC-126. RC-127 holds the changelog folder count. | Recorded in plan.md. Separate remediation. |

## Corrections to the issue record

- **C-01**: The issue body says that a stop has no durable phase state. The 2026-10-07 comment corrects this. Phase entries exist on single-site runs (RC-005) and on multi-site records (RC-010).
- **C-02**: The 2026-10-07 comment lists line numbers in `driver.py`, `wiring.py`, and `aggregate_upgrade_service.py`. Pull request #4109 changed these files after that comment. This record uses the line numbers on `main` at commit `f03c6c9b` only.
- **C-03**: The 2026-11-10 comment on #4022 says that issue #3726 remains open. The current state is closed. Pull request #4701 merged its fix as commit `53ad73cc` on 2026-11-13 (RC-097).
- **C-04**: The 2026-11-10 comment on #4021 says that pull request #4109 must merge first. It merged as commit `acaae1ad` on 2026-10-12 (RC-095). Issue #4021 remains open.
- **C-05**: The 2026-10-07 comment on #4022 names draft pull requests #4085 and #4089 as overlaps. Both merged on 2026-10-09 and 2026-10-10. No open pull request overlaps the manifest of this change (see the overlap check below).
- **C-06**: The issue manifest lists six files. The comments add eleven or more files, including the multi-site and reconcile paths. `plan.md` lists the complete map.

## Overlap check

The check ran on 2026-11-26 with `gh pr list --state open`. Seven pull requests are open. The check compared each file list with the manifest of this change, which includes `runs.py`, `driver.py`, `wiring.py`, `org_upgrade.py`, `walk.py`, `progress.html`, and the matching test files. The check found no overlap. The check must run again before `T-PR`.

## Coverage Summary

Each requirement maps to at least one task and at least one test or gate.

| Requirement | Tasks | Test cases or gates |
| - | - | - |
| FR-001 | T005, T007 | TC-09 |
| FR-002 | T002, T005, T007 | TC-01, TC-02, TC-03, TC-04, TC-09 |
| FR-003 | T006 | TC-10 |
| FR-004 | T006 | TC-10 |
| FR-005 | T007, T012, T016 | TC-23 |
| FR-006 | T005, T010, T012 | TC-20, TC-23 |
| FR-007 | T010 | TC-20 |
| FR-008 | T010 | TC-20 |
| FR-009 | T009, T010 | TC-20 |
| FR-010 | T008 | TC-14 |
| FR-011 | T009 | TC-13 |
| FR-012 | T009 | TC-12 |
| FR-013 | T009 | TC-11 |
| FR-014 | T008 | TC-14 |
| FR-015 | T009 | TC-15 |
| FR-016 | T009 | TC-16 |
| FR-017 | T003, T014 | TC-05, TC-06, TC-27 |
| FR-018 | T003, T014, T015 | TC-05, TC-06, TC-07, TC-08, TC-28 |
| FR-019 | T002 | TC-01, TC-02, TC-03 |
| FR-020 | T002, T013 | TC-01 |
| FR-021 | T002, T009 | TC-14 |
| FR-022 | T011 | TC-21, TC-22 |
| FR-023 | T004 | TC-17, TC-18 |
| FR-024 | T014 | TC-27, TC-29 |
| FR-025 | T013, T016 | TC-23, TC-25, TC-26 |
| FR-026 | T013 | TC-25, TC-26 |
| FR-027 | T012 | TC-23, TC-24 |
| FR-028 | T-LOCAL-GATES | `tests/integration/test_mistapi_sdk_compatibility.py` (RC-086) |
| FR-029 | T009 | TC-11 |
| FR-030 | T-LOCAL-GATES | `tests/guardrails/test_destructive_menu_docs.py` (RC-085) |

## Constitution alignment

`plan.md` holds the complete constitution check. Two rules fail on `main` today. Principle III fails because of F-01 and F-02. The operational store rule for verified persistence fails because a stop writes no recovery point (F-06). Both pass after T002, T003, and T007 land.

## Unmapped tasks

None. Each task maps to a requirement, to a constitution rule, or to a delivery gate.

## Metrics

| Measure | Value |
| - | - |
| Functional requirements | 30 |
| Success criteria | 6 |
| Tasks | 22 (T000, T001 to T017, and four delivery tasks) |
| Test cases | 29 (24 new, 5 changed) |
| Remote checks | 144 |
| Decisions | 12 |
| Human decisions (HUMAN-DECISION-REQUIRED) | 1 (D-11) |
| Open pull requests that overlap the manifest | 0 |

## Unresolved items

- **U-01**: Owner approval (T000) and the separate single-site unknown-outcome issue are needed before any write. The brief forbids GitHub writes in this run, so the owner must file the issue.
- **U-02**: Mist job-list completeness after an unknown reply is unverified. FR-014 requires operator review of the evidence.
- **U-03**: Reachability of the multi-site lease release with an unknown child is unverified. T015 adds a test to settle the question.
- **U-04**: The phase deadline value and the settle timing were not checked in this record. The spec does not depend on them.

## Convergence after implementation

After T-LOCAL-GATES passes, rerun the coverage table. Each FR must still map to a passing test. Reread the remote table for any path that changed on `main` during the work. Repeat the overlap check before T-PR.
