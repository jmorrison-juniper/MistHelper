# Specification Analysis Report: Preserve Repository Versions and Update the Local Main Checkout

**Scope**: Consistency across `spec.md`, `plan.md`, `tasks.md`, the design files, and the remote code. The findings list defects in existing work and unresolved items.

## Findings

| ID | Category | Severity | Location | Summary | Recommendation | Status |
| - | - | - | - | - | - | - |
| A-001 | Conflict | High | `plan.md` constitution table, `tasks.md` task T-PR. Owner comments IC_kwDOQltU8c8AAAABeBAB8Q and IC_kwDOQltU8c8AAAABhZRUIg. | The brief names a closing keyword for the pull request. The owner requires issue 4277 to stay open. | Use `Refs #4277` (research D-2). The orchestrator confirms the choice. | Resolved in plan. Orchestrator confirmation is needed. |
| A-002 | Label | Low | Issue 4277 labels. `.github\copilot-instructions.md` line 439. | Issue 4277 carries the scope label `tools`. The documented scope set omits `tools`. | Replace `tools` with `docs` (research D-9). | Resolved in the label decision. |
| A-003 | Conflict | Medium | `.specify\memory\constitution.md` line 409. `changelog.d\README.md` line 58. | The constitution says each change adds one fragment. The README exempts an internal-only change. | Follow the README (research D-8). The owner may amend the constitution wording. | Decided. Owner action is open. |
| A-004 | Policy | Medium | `.specify\memory\constitution.md` line 175. | The constitution says no standalone Git operation exists. The owner ran standalone preservation steps, dated 2026-10-17. | Document the owner actions (research D-12). Add no standalone operation to the primary checkout. | Documented. Owner decision is open. |
| A-005 | Verification | Low | PR 4404 and issue 4280. Comments of 2026-11-09. | Issue 4280 closed on 2026-11-13, when PR 4404 merged. The 2026-11-09 comments describe an unpublished privacy repair at head `6e197710`. The merged head is `85086493`. | Use the merged head as the authority (research R-03 and R-04). Record the equivalence gap in U-001. | Documented. |
| A-006 | Recovery | High | Cited commits `7d16297d`, `3cf37c7c`, and `d8900984`. | The three commits are absent from GitHub and from the primary object store. | Record U-001. Rebuild nothing (research D-7). | Open (U-001). |
| A-007 | Recovery | High | Primary checkout, five modified entries. | The primary checkout holds five uncommitted modifications. The issue requires preservation before any update. | Keep copies and a patch (task T007, research D-13). | Open (U-003). |
| A-008 | Publication | High | Repository visibility (research L-14). Local-only heads (research L-04). | The repository is public. A push of a local-only ref publishes private work. | Publish nothing (research D-4). | Decided. |
| A-009 | Evidence | Medium | Owner comment IC_kwDOQltU8c8AAAABc1wR8A. | The owner backup figures cannot be checked from the repository. | Record the figures as owner-reported (UV-01). Run V-05 after the owner supplies the bundle path. | Unverified. |
| A-010 | Risk | Medium | Owner comment IC_kwDOQltU8c8AAAABeBAB8Q. | The owner accepted same-disk storage with a 24-hour recovery window. | Record the window in FR-005 and U-002. | Accepted by owner. |
| A-011 | Evidence | Low | PR 4404 review entries. | GitHub returned no review entries for PR 4404. The owner account merged it. Issue 4280 requires human review for the repaired class. | The owner records the review decision (U-009). | Open (U-009). |
| A-012 | Drift | Low | Issue 4280 comments and PR 4404 heads. | The PR head moved from `3ead4ec4` (2026-10-30) to `6e197710` (2026-11-09 draft) to `85086493` (merged). Older comments name older heads. | Use the merged head. Keep the older SHAs as history (research R-05 and R-06). | Documented. |
| A-013 | Drift | Low | Issue 4277 body and research L-04. | The issue cites 313 local branches. The count on 2026-11-26 is 330. | Use the current count in the register. Record both counts. | Documented. |
| A-014 | Debt | Medium | `specs\` direct children (research L-11). | The `specs\` folder holds 813 direct children. This exceeds the five-child rule, as grandfathered debt. | Record remediation action RA-1. The owner files a separate issue. This record adds no direct child to `specs\`. | Recorded. |
| A-015 | Structure | Low | `specs\numbered\0\0\1\1` (research L-11). | The level holds five children and is full. | The route uses its existing child `4`. No child is added. | Verified. |
| A-016 | Governance | Low | `.github\copilot-instructions.md` line 473. | Steps 10 to 12 of the deployment pipeline apply to a product image. This record changes no product file. | Mark steps 10 to 12 as not triggered (research D-11). | Decided. |
| A-017 | Gate | Low | `.github\copilot-instructions.md` line 74 and `AGENTS.md` line 40. | The local STE row names fixed files. `AGENTS.md` requires each Markdown file to score 80 or above. | Run STE on each new Markdown file (task T-LOCAL-GATES). | Resolved in tasks. |
| A-018 | Verification | Low | Tasks T-REMOTE-CI and T-MERGE. | The local gates table has no command for a remote check watch. | Use `gh pr checks --watch` from `AGENTS.md` line 229. | Documented. |
| A-019 | Scope | Low | `.spec-context.json` at the repository root. | The file describes issue 1823, a paused feature. It does not relate to issue 4277. | Not used. The owner reviews it outside this record. | Documented. |
| A-020 | Scope | Low | Issue 4707. | An open defect causes refused endpoints to produce empty configuration. This record does not repair it. | Keep it out of scope. Recovery item U-007 tracks it. | Documented. |
| A-021 | Evidence | Low | Owner baseline comments. | The owner lists the causes of skipped tests but not each skipped test. | Record as UV-07. A current run gives the current list. | Unverified. |
| A-022 | Evidence | Low | `refs/copilot` and `refs/agents`. | The repository does not document the meaning of these namespaces. | Record as UV-06. The counts are recorded. | Unverified. |
| A-023 | Dependency | Low | mistapi pin and installed SDK (research R-49, R-50). | The installed SDK is 0.64.1, which meets the pin. The owner notes that a vendored index describes 0.64.0. | Record the installed version. No code in this record relies on the index. | Verified. |

## Coverage Summary

Each functional requirement maps to at least one task and at least one verification test.

| Requirement | Tasks | Verification test |
| - | - | - |
| FR-001 | T001 | V-01 |
| FR-002 | T002 | V-02 |
| FR-003 | T003 | V-03 |
| FR-004 | T004 | V-04 |
| FR-005 | T005 | V-05 |
| FR-006 | T006 | V-06 |
| FR-007 | T007 | V-07 |
| FR-008 | T008 | V-08 |
| FR-009 | T009, T010 | V-09 |
| FR-010 | T011 | V-10 |
| FR-011 | T012 | V-11 |
| FR-012 | T015, T-LOCAL-GATES | V-12 |
| FR-013 | T013 | V-13 |
| FR-014 | T014 | V-14 |
| FR-015 | T-PR, T-REMOTE-CI, T-MERGE | V-15 |

## Constitution Alignment

No rule fails. Two rules pass with a recorded note. Rule IV keeps the standalone Git note (A-004). The release-note rule keeps the wording note (A-003). The plan table lists each rule.

## Unmapped Tasks

Each task maps to at least one requirement. No task is unmapped.

## Metrics

- Functional requirements: 15. Success criteria: 6. Tasks: 19 (15 numbered tasks and 4 delivery tasks).
- Verification tests: 15. Remote checks in `research.md`: 50. Decisions: 13. Recovery items: 9.
- Local heads measured on 2026-11-26: 330. Findings: 23.

## Unresolved Items

The unresolved items are recovery items U-001, U-003, U-004, U-005, U-006, U-007, U-008, and U-009, as listed in `design\contracts\recovery-register.md`. Item U-002 has the status `accepted`, because the owner accepted the risk. Its close condition is not yet met.

## Convergence After Implementation

- Replace each `not-run` row in `design\contracts\validation-report.md` with a `pass` or `fail` result and its cause.
- Set each recovery item to its final status, with its evidence.
- Confirm that the register holds one row for each local head counted at run time.
- Recheck each remote row in `design\research.md`. If GitHub main moved, record the new head, the new counts, and the reason.
- Confirm that the remote check count, the research row count, and the summary count still match at 50.
