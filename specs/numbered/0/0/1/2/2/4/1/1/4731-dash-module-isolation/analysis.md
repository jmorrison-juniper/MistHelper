# Specification Analysis Report: Dash module isolation for map callback tests

## Findings

| ID | Severity | Finding | Evidence | Resolution |
| - | - | - | - | - |
| F-01 | High | Four slice files install the Dash stub at import time. Their fixtures save the stub, so the stub stays after collection and breaks later imports of Dash. | R02, R03, R06, R07, R08, R09, R10, R11 | Slices S1 to S4 remove the import-time install and restore the exact prior entry (T002 to T006). |
| F-02 | High | The held candidate commits add module-level names and repeat regression cases across files. The symbol gate and the write-each-case-once rule reject that design. | R19, R20, R21, R29 | D-2. Build new branches from main. Keep the held commits unchanged (FR-027). |
| F-03 | Medium | Baseline findings in wave A (lines 134 and 181) and wave E2 (lines 174 and 178) are keyed by line number. An edit above a finding moves it, and the analyzer then counts the moved finding as new. | R04, R05, R12, R13, R17, R18, R28 | D-4 and D-5 fix all four findings. Tasks T007 and T008 make the edits. Quickstart QS-11 confirms the result. |
| F-04 | Medium | The held wave D commit message contains `Closes #4731`. The owner says not to carry that reference into a squash merge. | R20 and the owner comment IC_kwDOQltU8c8AAAABkwM82g | FR-026. Only the final pull request uses Closes. |
| F-05 | Low | Wave E1 merged without action logging. It also keeps a scoped module-level install that differs from the four slices. | R14, R15, R43 | D-14. Keep wave E1 unchanged. Record the logging gap as debt for a follow-up issue. |
| F-06 | Medium | Constitution Principle I applies to test modules. Existing test modules hold more than five top-level names. | R39, R10 | Grandfathered debt in plan.md Complexity Tracking. The change adds no name. |
| F-07 | Medium | The copilot rule limits changelog fragments to user-visible changes. The constitution requires one fragment for each change. | R44, R45, R49 | D-8. Each pull request adds one fragment (FR-022). |
| F-08 | Medium | Constitution Principle IV steps 10 to 12 expect a container build on main. The container build ignores changes under `tests/`. | R32, R41 | D-10 and unresolved item UI-1. |
| F-09 | Low | The generic brief rule puts `Closes` in each pull request body. The owner needs `Refs` in three earlier pull requests. | R37, pull request 4735 body | D-7 and FR-026. |
| F-10 | Low | The held candidate commits are based on commit 3964d21. Main is 88 commits ahead of that base. | R19, R20, R21 | D-2. A rebase needs the owner release (FR-027). |

## Coverage Summary

Each requirement maps to at least one task and at least one verification. Verification IDs refer to design/quickstart.md. Checklist IDs refer to design/checklists/isolation.md and design/checklists/publication.md.

| Requirement | Tasks | Verification |
| - | - | - |
| FR-001 | T002, T004, T005, T006 | QS-02, QS-12 |
| FR-002 | T003, T004, T005, T006 | QS-02, QS-03 |
| FR-003 | T003, T004, T005, T006 | QS-02, QS-03, QS-05 |
| FR-004 | T003, T004, T005, T006 | ISO04 review, QS-04 |
| FR-005 | T003, T004, T005, T006 | QS-04, QS-12, ISO08 |
| FR-006 | T002, T004, T005, T006 | QS-08 (rule RUF100), ISO07 |
| FR-007 | T007 | QS-04, QS-11 |
| FR-008 | T007 | QS-04 |
| FR-009 | T003 | QS-04 |
| FR-010 | T006, T008 | QS-04 |
| FR-011 | T007, T008 | QS-04, QS-13 |
| FR-012 | T002, T004, T005, T006, T-LOCAL-GATES | QS-12, ISO06 |
| FR-013 | T003, T004, T005, T006 | QS-08 (rule G), ISO15 |
| FR-014 | T003, T004, T005, T006 | ISO13 review, QS-08 |
| FR-015 | T002 to T008 | QS-08 (rule E501), ISO14 |
| FR-016 | T-PR | QS-16, PUB11 |
| FR-017 | T-LOCAL-GATES, T-PR | QS-16, ISO11 |
| FR-018 | T-LOCAL-GATES | QS-08 to QS-12, QS-14 |
| FR-019 | T-LOCAL-GATES, T-PR | QS-11, ISO12 |
| FR-020 | T009 | QS-05, QS-06 |
| FR-021 | T009 | QS-07 |
| FR-022 | T-PR | PUB10 |
| FR-023 | T-PR, T-REMOTE-CI | PUB01 |
| FR-024 | T-PR | PUB02 |
| FR-025 | T-PR, T-MERGE | PUB03 |
| FR-026 | T-PR, T-MERGE | PUB07 |
| FR-027 | T-PR | PUB06 |
| FR-028 | T-PR | PUB08 |
| FR-029 | T001, T-PR | QS-16, PUB12 |

Gaps in verification:

- FR-004 has no automated check, because a failing test is needed to prove it. The review item ISO04 covers it.
- FR-014 has no automated check for the presence of logs. The review item ISO13 covers it.
- No test fails before the fix in a single file (D-3). The probes QS-01 to QS-03 give the red and the green evidence instead.

## Consistency Review

- Spec and plan: Each FR appears in the plan design, the tasks, or both. The plan states the 120 character limit, the logging scope, and the inline comment rule.
- Plan and tasks: The target fixture in plan.md applies to T003 to T006. The line numbers in tasks.md match research rows R02 to R13. T003 warns that the numbers move after T002.
- Research and remote code: Each cited line matches the local view or grep result for a file whose blob SHA matches the remote tree. Rows R14 to R16 match the merged wave E1 file.
- Research and gates: The gate commands come from the local gates table (R33). The symbol gate rule comes from the comparator source (R29). The test-quality rule comes from the baseline key (R28).
- Remote truth: The main head, the blob SHAs, and the commit checks came from `gh api` reads on 2026-11-26. Repository code claims rest on remote rows. Tool and package claims rest on installed local sources (R27, R28, and R29).

## Constitution Alignment

Fourteen of fifteen constitution rows pass, as plan.md shows. Principle IV steps 10 to 12 carry a documented exception (UI-1). Principle VII passes with the scope reading in D-9.

## Unmapped Tasks

None. Each task maps to at least one requirement or to a final gate that verifies a requirement.

## Metrics

- Functional requirements: 29.
- Success criteria: 8.
- Tasks: 13. Nine numbered tasks and four final gates.
- Decisions: 14. None needs a human answer.
- Remote verification rows: 67.
- Planned test-level checks: 16.
- Unverified items: 9.

## Unresolved Items

- UI-1: Principle IV steps 10 to 12 do not run for test-only changes. The owner can request a manual dispatch later (D-10).
- UI-2: Existing test modules exceed the five-item limit. This debt is grandfathered (plan.md Complexity Tracking).
- UI-3: No permanent collection guard exists. A follow-up issue should add one after slice S4 merges (D-3).
- UI-4: Wave E1 lacks action logging and keeps a different design. A follow-up issue can align it (F-05).
- UI-5: Baseline entries for the fixed findings become stale. The owner can prune them in a separate change (R46).
- UI-6: The owner can reject the line 134 scope. If so, the slice keeps its line count above line 134 unchanged (D-4).
- UI-7: The owner decides how to dispose of the held candidate commits (D-2).
- UI-8: Unverified items U-1 to U-9 in design/research.md remain open until the gates run.
