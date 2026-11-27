# Specification Analysis Report: Stranded branch preservation

This review checks the specification, the plan, the tasks, the research, and the remote code against each other. It also lists the defects in the existing work. The evidence IDs in the Evidence column refer to the remote verification table in `design/research.md`.

## Findings

| ID | Finding | Evidence | Impact | Action |
| - | - | - | - | - |
| F-01 | The report names 248 tips that a PR head commit already holds. | RC-05, RC-08, RC-09, RC-10 | The report over-reports these rows. Their commits have a PR ref. | Upstream request in T013. Decision D-3 tags all rows anyway. |
| F-02 | The report matches branch names with PR head names. A PR with a different name does not protect the tip. | RC-06, RC-66, RC-67, RC-68 | The report misses commit-level protection. | Upstream request in T013. |
| F-03 | Five open tracking issues share the report title. The shared workflow promises one open issue. | RC-21, RC-64, RC-65 | Older tables stop receiving updates. The cause is unverified (U-04). | T012 closes the four duplicates with a link. |
| F-04 | The contribution guide says a PR is the only durable copy. `AGENTS.md` accepts a pushed tag as a preservation proof. | RC-25, RC-26, RC-27, RC-28 | Maintainers follow a rule that conflicts with `AGENTS.md`. | T009 and FR-010 correct the guide. |
| F-05 | The issue body asks for one PR for each named branch. Each PR starts the CI workflow, which has 28 job keys. One of those jobs opens issues for failed gates. | RC-45, RC-46, RC-47, RC-48, RC-49, RC-50, RC-51, RC-52 to RC-55 | 257 new PRs start CI for each branch. A failed gate opens an issue for each PR. | Decision D-2 replaces the PR rule with tags. |
| F-06 | The standard record pull request step names `Closes #<issue>`. A merge with that keyword closes the linked issue. | RC-43, RC-44 | Issue 4911 closes while 505 rows remain. The next weekly run opens a new tracking issue. | Decision D-7 and FR-011 use `Refs #4911` until the report names no row. |
| F-07 | Exemplar B adds `specs/3158-wip-controls/` outside the managed roots. | RC-19, RC-36 | A merge as it stands breaks constitution rule I. | Decision D-12. The owner decides the branch disposition. |
| F-08 | The changelog rule allows no fragment for an internal change. The constitution requires one fragment for each change. | RC-33, RC-34, RC-35 | The two rules conflict for this record. | Decision D-10 follows the constitution. The owner decides the wording of the README. |
| F-09 | The ignore prefix in the report tool is `dependabot/`. Archive names that start with `archive/laptop-20261121/` do not match it. | RC-66, and 16 table rows that contain `dependabot` | Bot branches appear in the report. | The upstream request in T013 can cover it. This finding does not block the change. |
| F-10 | The local tool pin differs from the reusable workflow pin. | RC-40, RC-42 | The local command and the weekly report can differ. | Unverified (U-09). FR-016 keeps both pins. |
| F-11 | The report holds no tip commit IDs. | Report body in issue 4911 | A rewrite after the report is not visible in the report. | Edge case in the spec. Unverified (U-10). |
| F-12 | No row of the Local gates table covers refs. | RC-29, RC-30, RC-31 | Tasks T004 to T008 have no table gate. | Recorded in the verification gap of `tasks.md`. |
| F-13 | `changelog.d` holds 335 children. `specs` holds 813 direct children. | Local folder counts on 2026-11-26 | Folder debt. The constitution requires a record and an action. | Plan section Folder Debt. T015 and FR-017. |
| F-14 | Exemplar A is held by closed PR 3954. The report treats it as stranded. | RC-08, RC-09, RC-10, RC-11 | The first row of the table is a false positive. | Covered by F-01. |
| F-15 | The report ages were measured on 2026-11-23. | Report date in issue 4911 | The ages change every day. | The spec and the quickstart use row counts, not ages. |

## Coverage Summary

| Requirement | Tasks | Verification |
| - | - | - |
| FR-001 | T001, T002, T003 | quickstart Steps 1, 2, and 3 |
| FR-002 | T005, T007 | quickstart Steps 5 to 9 |
| FR-003 | T005, T007 | quickstart Step 9 checks the named branch names |
| FR-004 | T004 | quickstart Step 4 |
| FR-005 | T002, T007 | quickstart Steps 2 and 8 read the tips in one session |
| FR-006 | T005, T007 | quickstart Steps 5 and 8 |
| FR-007 | T007, T008 | quickstart Steps 6, 8, and 9 |
| FR-008 | T006 | quickstart Step 7 |
| FR-009 | T009 | quickstart Step 10 |
| FR-010 | T009 | quickstart Step 10 searches the guide for the removed claim |
| FR-011 | T-PR | `gh pr view` reads the body |
| FR-012 | T014 | Issue link in issue 4911 |
| FR-013 | T010 | quickstart Step 10 runs the fragment guard |
| FR-014 | T013 | Issue link in issue 4911 |
| FR-015 | T012 | quickstart Step 12 |
| FR-016 | T-PR | quickstart Step 10 checks the file list of the branch |
| FR-017 | T015 | Issue link in issue 4911 |
| SC-001 | T008 | quickstart Step 9 |
| SC-002 | T007, T008 | quickstart Step 9 |
| SC-003 | T-LOCAL-GATES, T-REMOTE-CI | quickstart Step 10 and `gh pr checks` |
| SC-004 | T006 | quickstart Step 7 |
| SC-005 | T012 | quickstart Step 12 |
| SC-006 | T011 | quickstart Step 11 |

Every requirement maps to at least one task and one verification command.

## Consistency Checks

- The file change map in `plan.md` lists the same paths as tasks T009, T010, and T011.
- Requirement FR-011 and task T-PR use the same closing keyword rule.
- The spec names 17 requirements. The tasks file names 19 tasks. The STATUS file repeats both counts.
- The spec names six success criteria. Each criterion has one verification step in the quickstart.
- Exemplar A and exemplar B appear in the spec, the research, and the data model with the same tip IDs.
- The route `0/0/1/2/4/1/2/1` matches the base-5 result for 4911. The formula appears in `spec-route.ps1` (RC-38, RC-39).

## Constitution Alignment

- Rule I passes. The feature root holds five children. The new route parents hold one child each. The folder debt of `changelog.d` and `specs` is recorded and tracked (F-13).
- Rule III passes. No deletion appears in the procedure. The rollback removes only preservation tags.
- Rule IV passes. The record pull request runs the local gates, CI, and a squash merge.
- Rules II, VI, and VII do not apply, because the change adds no code.

## Unmapped Tasks

None. Each task maps to at least one requirement.

## Metrics

- Named rows: 505. Named branch names on origin: 505 of 505.
- Tips held by a PR head commit: 248. Tips not held: 257.
- Commits above `main` in the named rows: 1,616. Commits above `main` in the not held rows: 1,059.
- PR records: 2,396. Remote branches: 598.
- Preservation tags to push: 505. Batches: one pilot of 5 refs, then 10 batches of 50 refs.
- Requirements: 17. Success criteria: 6. Tasks: 19. Decisions: 12.

## Unresolved Items

- U-01: GitHub documentation for tag and branch filters was not readable through the fetch tool. The pilot verifies the behavior (T006).
- U-02: `refs/pull/<n>/head` persistence after a branch deletion is a repository claim. The tags do not depend on it.
- U-03: The ancestry of the 257 not held tips in PR heads is sampled, not complete. No decision depends on it.
- U-04: The cause of the five open tracking issues is not verified.
- U-05: The `2026-11-21` date in the archive prefix is inferred from the name.
- U-06: Gate outcomes for a PR on each named branch were not measured, because no PR was opened.
- U-07: GitHub acceptance of 50 tags in one push was not tested.
- U-08: The tracking issue comment format is a convention of this record, not a repository rule.
- U-09: The local tool pin and the workflow pin may differ in behavior.
- U-10: The report holds no tip commit IDs, so a rewrite after the report is not visible.

Human decisions: none. No decision in this record falls in the four human decision categories.

## Convergence After Implementation

- After T008, 505 preservation tags exist on origin. The named branches remain.
- The report still names 505 rows until the upstream rule changes. The tracking issue stays open.
- After T012, one tracking issue stays open with the report title.
- After T013 and a pin change, the report should stop naming the held rows. The pin change is a separate pull request.
- After T014, a later issue can delete a named branch. Each deletion needs its verified tag.
