# Specification Analysis Report: Stranded branch pull request coverage

## Findings

Each finding names its evidence. Severity values are `high`, `medium`, and `low`.

| ID | Severity | Finding | Evidence | Resolution |
| - | - | - | - | - |
| A-1 | high | The issue body names 54 branches. The replica of the report names 537. The orchestrator message framed the issue as one branch. | RC-055, RC-049, research.md R2 | Scope is the live report output at each batch start (D-1, FR-001). Each batch rereads the scope (T011). |
| A-2 | high | The reusable report cannot find its own open tracker. Five open trackers share the title. The workflow cannot close issue 4818. | RC-035 to RC-037, RC-052 to RC-054 | Owner closes the trackers after the report is clean (D-7, T019, T020). The defect gets its own issue (FR-017, T021). |
| A-3 | medium | The development requirements pin the devtools package at `2239e7b`. The workflows pin `79a5e45`, which is version 0.6.4. The installed build is 0.6.4. The two pins name different commits. | RC-030, RC-017, RC-019, RC-035, RC-045 | Not fixed in this record (D-9). Follow-up issue (FR-017, T022). |
| A-4 | medium | The stranded review page calls the pull request ref the only permanent copy. AGENTS.md accepts a pushed tag as a preservation proof. Git keeps a tag after a branch deletion. The two statements disagree. | RC-025 (lines 46 and 47), RC-002 (line 275) | The rollout follows the pull request rule because the report reads only pull requests (D-2). The owner decides whether tags join the rule. |
| A-5 | medium | The constitution requires one changelog fragment for each change. The repository instructions require one fragment only for a change that a user sees. | RC-113, RC-118, RC-031 | The record follows the stricter rule and adds one fragment (D-8, FR-018). |
| A-6 | medium | The brief for the record pull request asks for `Closes #4818`. A merged closing keyword closes the tracker before the report is clean. | research.md R7, RC-003, RC-036 | The record pull request uses `Refs #4818` (D-8, FR-003). The deviation appears in T-PR and in decision D-8. |
| A-7 | high | Each failed gate on a pull request opens an issue. Eighteen gate issues are open now. Stranded branches number 537. | RC-038, RC-051 | The pilot counts the gate issues (T007). The batch size is ten (D-5). The owner approves the volume (D-12, T010). |
| A-8 | medium | The stranded set grew from 505 rows on 2026-11-23 to 537 on 2026-11-26. The archive backup branches account for most of the change. | RC-056, RC-049 | Unresolved. The owner must confirm the disposition of the archive backups (U-7, U-8). |
| A-9 | low | The owner comments name two private-corpus branches. The branch names do not identify them. | Issue 4818 comments (S-5) | Out of scope. The rollout pushes no local-only branch (FR-015, T023, D-10). The owner must name them before T023 runs. |
| A-10 | low | The route value for issue 4818 matches the base-5 arithmetic and the route guard function. The route leaf holds no entry. | RC-009 to RC-011, RC-026, RC-034, research.md R6 | No defect. |
| A-11 | low | Repository instructions say the repository is public. The API confirms the visibility. The cost statement for runner minutes depends on that status. | RC-006, RC-050 | No defect. Each batch rechecks the visibility (R-12). |
| A-12 | low | The skip-CI page covers `pull_request` events. The head commit case is not tested. Three issue branches carry `[skip ci]` in their head subject. | S-3, U-2, RC-059 to RC-061 | Unresolved (U-2). The pilot includes no skip-CI branch. |

## Coverage Summary

Each functional requirement maps to at least one task. Each success criterion maps to at least one task.

| Requirement | Tasks | Success criterion | Tasks |
| - | - | - | - |
| FR-001 | T001, T002, T004, T011, T016 | SC-001 | T016 |
| FR-002 | T005, T012 | SC-002 | T017 |
| FR-003 | T005, T012, T017, T-PR | SC-003 | T018 |
| FR-004 | T008, T017, T018 | SC-004 | T017 |
| FR-005 | T005, T012, T013 | SC-005 | T007, T009 |
| FR-006 | T004, T005, T007 | SC-006 | T014, T016 |
| FR-007 | T006, T013 | | |
| FR-008 | T012, T015 | | |
| FR-009 | T005, T012, T-PR | | |
| FR-010 | T007, T008, T009, T014 | | |
| FR-011 | T003, T020 | | |
| FR-012 | T019 | | |
| FR-013 | T-LOCAL-GATES, T-PR, T-REMOTE-CI, T-MERGE | | |
| FR-014 | T016 | | |
| FR-015 | T023 | | |
| FR-016 | T024 | | |
| FR-017 | T001, T021, T022 | | |
| FR-018 | T-LOCAL-GATES, T-PR | | |
| FR-019 | T004, T011 | | |
| FR-020 | T010 | | |

## Constrained-Field Coverage

The title form, the body keyword rule, and the label set appear in the contract file. Each rule has a verification step.

| Constrained field | Rule | Verification |
| - | - | - |
| Title | Conventional Commits form (RC-112) | T005, T012 |
| Body | `Refs #4818` and no closing keyword | T017 |
| Labels | `chore` and `ci` only | T013 |
| Draft state | Draft on creation | T005, T012 |
| Head commit | Equal to the branch head | T008, T017 |

## Constitution Alignment

The plan records each rule with a verdict. No rule fails. The record adds no code, so the code rules do not apply. The five-child rule holds for each new folder (plan.md, Constitution Check).

## Unmapped Tasks

Every task maps to at least one requirement. No task is unmapped.

## Metrics

| Measure | Value |
| - | - |
| User stories | 5 |
| Functional requirements | 20 |
| Success criteria | 6 |
| Tasks | 28 |
| Remote checks | 118 |
| Decisions | 12 |
| Human decisions | 1 |
| Stranded branches at the snapshot | 537 |

## Convergence After Implementation

The rollout converges when the report exits with status 0 (T016). Convergence requires four facts. The report names no branch. Each batch comment lists its pull requests. The tracker closes after the owner authorizes the closure. No branch disappears from the remote.

## Unresolved Items

- U-1 to U-8 in research.md list the unverified items. Each item has a reason.
- The owner must approve the rollout volume (D-12, T010).
- The owner must name the two private-corpus branches (A-9, T023).
- The owner must decide whether tags join the preservation rule (A-4). This decision is outside the rollout.
- The authorization for the duplicate-tracker closures and the follow-up issues remains open (T019 to T022).
