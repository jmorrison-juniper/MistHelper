# Specification Analysis Report: Stranded Branch Preservation

This report checks `spec.md`, `plan.md`, `tasks.md`, and the remote evidence against each other. The RC and U IDs refer to `design/research.md`.

## Findings

| ID | Severity | Finding | Evidence | Resolution |
| - | - | - | - | - |
| F-1 | High | The brief framed one branch. The issue scope is 505 report rows, not one branch. | RC-38, RC-43 | Decision D-1. This record covers all 505 rows. |
| F-2 | High | The weekly report opens a new tracking issue each week. Its title search matches no issue, so it never reuses #4302. Five open issues now carry the title. | RC-23, RC-34, RC-35, RC-36, RC-37 | Decision D-11. A separate issue fixes the search (T020). |
| F-3 | High | Issue #4302 holds the 2026-10-19 snapshot. Its body has not changed since 2026-11-09. | Issue metadata | Use report #4911 for scope (D-1). The owner closes #4302 later (T021). |
| F-4 | High | Publication exposes content, because the repository is public. | RC-25 | Decisions D-3 and D-16. |
| F-5 | Medium | Owner comments carry stale ahead and behind counts. Example: `jmorrison-jnpr-snmp-fallback-delivery` is 562 behind now, not 411. | Annotated rows, RC-46 to RC-93 | Decision D-5. Use GitHub compare data only. |
| F-6 | Medium | An owner comment on 2026-10-30 names 38 candidate branches. The annotated table holds 48 rows. | Issue comments | Decision D-1. The table is the annotated scope. |
| F-7 | Medium | Two reserved refs cite closed issues. #3575 and #3700 are CLOSED. #3700 keeps a stale `in-progress` label. | RC-45 | Hold H2 stays in place until the owner confirms (D-8). |
| F-8 | Low | The owner first gave an unknown head for `recovery/3388`. The owner corrected it on 2026-10-30. The GitHub head is `ea0a7467b8`. | RC-76 | Resolved. |
| F-9 | Low | The owner first said `main` kept only a non-null assertion for `recovery/2708`. The owner corrected it on 2026-10-30. The blob `330fa9e3` is identical on `main`. | RC-81 | Resolved. |
| F-10 | Medium | `AGENTS.md` and the constitution require `Closes` in PR bodies. The owner keeps #4302 open. | `AGENTS.md`, constitution | Decision D-10 (human). |
| F-11 | Medium | The repository instructions limit changelog fragments to user-visible changes. The constitution requires one fragment for each change. | Repository instructions, constitution | Decision D-13 follows the constitution. |
| F-12 | High | Three holds (H1) touch the destructive upgrade path. Issues #2863 and #3222 carry `needs-human-review`. | RC-45, RC-49, RC-53 | Decision D-7 (human). |
| F-13 | Medium | The report matches branch names, so 248 PR-kept rows stay listed. Closure needs the title fix or a rule change. | RC-40, RC-41 | Decision D-4 and Decision D-11. |
| F-14 | Medium | The 257 unkept rows map to 251 distinct head commits. Example: `recovery/4208-original-before-review-fbb23f8` and `recovery/4208-pre-reconstruction-20261113` share head `fbb23f8a23`. | RC-42 | Decision D-3. A second row cites the first PR. |
| F-15 | Medium | Three owner-cited branches change paths that `main` no longer has, such as `src/api/` and `src/juniper_docs/`. | Annotated rows | Owner notes say do not replay these branches. This record keeps that rule. |
| F-16 | Low | The age column in the #4302 body was computed at creation. | Issue body | Use the age column of report #4911. |
| F-17 | Low | The report's quiet-period and bot-branch rules sit in the shared workflow. This record reads the lines that matter, but it does not run them. | U-6 | Unverified. TST-02 repeats the count. |

## Coverage Summary

| Requirement | Tasks | Tests |
| - | - | - |
| FR-001 Inventory | T001 | TST-01, TST-02, TST-06, TST-07 |
| FR-002 Blob classes | T002 | TST-05 |
| FR-003 PR-kept classes | T003 | TST-02, TST-03 |
| FR-004 Visibility | T004 | TST-04 |
| FR-005 Authorization and scan | T007, T008, T009, T010, T022 | TST-14, TST-17 |
| FR-006 Draft PRs | T014, T015, T016 | TST-15 |
| FR-007 Holds | T011, T012, T013 | TST-18 |
| FR-008 No ref change | T017 | TST-16 |
| FR-009 Recount | T018 | TST-02 |
| FR-010 Route and folders | T005, T-LOCAL-GATES | TST-08, TST-09, TST-12 |
| FR-011 STE and links | T006, T-LOCAL-GATES | TST-10, TST-11, TST-21 |
| FR-012 PR title and body | T-PR, T-REMOTE-CI | TST-15, TST-19 |
| FR-013 Remote row count | T001, T-LOCAL-GATES | TST-20 |
| FR-014 No placeholders | T-LOCAL-GATES | TST-13 |
| FR-015 Issue stays open | T019, T-MERGE | TST-22, TST-24 |
| FR-016 Separate defect issue | T020, T021 | TST-23 |

## Constitution Alignment

No rule is violated. The result for each rule is in `plan.md`.

## Unmapped Tasks

None. Each task maps to at least one requirement and one test.

## Metrics

- Requirements: 16. Tasks: 26. Tests: 24. Decisions: 17, of which 3 need a human.
- Remote checks: 93. Annotated rows: 48. Report rows: 505.
- PR-kept rows: 248. Unkept rows: 257. Distinct unkept head commits: 251.

## Unresolved Items

- The human decisions D-3, D-7, and D-10 remain open. Each one appears in the decision table of `design/research.md`.
- Each scan result is open (T008 to T010). No scan has run.
- The holder releases for hold H2 are open (T013).
- The report defect has no issue yet (T020).
- Group N has 210 rows that have no owner selection (T022).

## Group N Named Rows

These 22 unkept rows sit outside the annotated table. Each one has its own head commit in the report. The 188 archive rows are not named here. TST-02 regenerates them.

- `recovery/stash-issue3699-local-refresh`
- `jmorrison-juniper-issue-4269-runtime-nested-feature-identity-in-speck-4a6090`
- `jmorrison-juniper-issue-2747-wan-probe-test-quality`
- `jmorrison-juniper-fix-4494-csrf-warning-prefix`
- `recovery/4358-pre-reconstruction-20261113`
- `jmorrison-juniper-local-build-revision`
- `recovery/4208-original-before-review-fbb23f8`
- `recovery/4208-pre-reconstruction-20261113`
- `recovery/4208-gateway-reviewed-ff9615`
- `recovery/4208-replacement-contracts-d202d480abee`
- `recovery/4208-observation-statistics-3a04afa6d35b`
- `recovery/4208-synthetic-horizon-481cc3b56aa5`
- `recovery/4208-observation-ranking-0bfe3e2`
- `recovery/4208-operator-declarations-36f72b0`
- `recovery/4208-projection-archives-035d065`
- `recovery/4208-pre-csrf-admission-b035341`
- `recovery/4208-reviewed-symbols-2037e9b`
- `recovery/issue4811/pr-4802-original`
- `recovery/issue4811/pr-4803-original`
- `recovery/issue4811/pr-4804-original`
- `recovery/issue4811/pr-4805-original`
- `recovery/issue4811/pr-4806-original`

Two more non-archive rows are PR-kept: `jmorrison-juniper-capture-lock-holder-test-isolation` and `recovery/4208-fixture-isolation-843be63`.

Two rows share the head commit `fbb23f8a23`: `recovery/4208-original-before-review-fbb23f8` and `recovery/4208-pre-reconstruction-20261113`.

## Convergence After Implementation

- Each published branch leaves report #4911 on the next run, because its PR uses the same branch name.
- The report still lists every unkept row in group N until the owner selects a batch or the report changes.
- The count of open tracking issues with the report title falls to one after T021.
