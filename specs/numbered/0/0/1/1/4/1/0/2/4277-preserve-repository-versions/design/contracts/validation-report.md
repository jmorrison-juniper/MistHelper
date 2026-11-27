# Contract: Validation Report

## Header

- Baseline commit: `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.
- Baseline worktree: `MistHelper-4277-baseline`, in the parent folder of the repository. Task T009 creates it, and task T014 removes it.
- Run time: the UTC start and end time for each row.

## Columns

| Column | Rule |
| - | - |
| validation_id | The letter `V`, a hyphen, and two digits, from `V-01` to `V-15`. This is the natural key. |
| requirement | The functional requirement that the check serves. |
| command | The quickstart scenario that holds the exact commands. |
| exit_code | The exit code of the main command, or `none` when the check reads state only. |
| summary_line | The summary line that the command prints, or `none`. |
| result | One of `pass`, `fail`, or `not-run`. |
| cause | The reason for a `fail` or a `not-run` result. The word `none` marks a `pass` result. |

## Rows

| validation_id | requirement | command | exit_code | summary_line | result | cause |
| - | - | - | - | - | - | - |
| V-01 | FR-001 | Quickstart scenario 1 | none | none | not-run | The authoring phase measured the value in research R-01 and R-02. The implementer repeats the command. |
| V-02 | FR-002 | Quickstart scenario 2 | none | none | not-run | The authoring phase measured the value in research L-01 and L-02. The implementer repeats the command. |
| V-03 | FR-003 | Quickstart scenario 3 | none | none | not-run | The authoring phase measured the value in research R-03, R-04, and L-19. The implementer repeats the command. |
| V-04 | FR-004 | Quickstart scenario 4 | none | none | not-run | The authoring phase measured the value in research R-05 to R-10 and L-06. The implementer repeats the loop. |
| V-05 | FR-005 | `git bundle verify` on the bundle file that the owner names in issue 4277 | not-run | not-run | not-run | The bundle path is absent from the repository. The owner supplies the path. |
| V-06 | FR-006 | Quickstart scenario 5 | none | none | not-run | The register file is not built yet (task T006). |
| V-07 | FR-007 | Quickstart scenario 6 | none | none | not-run | The preservation copies are not made yet (task T007). |
| V-08 | FR-008 | Quickstart scenario 7 | none | none | not-run | The before counts are measured in research L-04, L-05, and L-08. The after counts follow task T008. |
| V-09 | FR-009 | Quickstart scenario 8 | not-run | not-run | not-run | The baseline worktree does not exist yet (task T009). |
| V-10 | FR-010 | Quickstart scenario 9 | not-run | not-run | not-run | The baseline worktree does not exist yet (task T009). |
| V-11 | FR-011 | Quickstart scenario 10 | not-run | not-run | not-run | The baseline worktree does not exist yet (task T009). |
| V-12 | FR-012 | Quickstart scenario 12, guard command | not-run | not-run | not-run | The record worktree does not exist yet (task T015). |
| V-13 | FR-013 | Quickstart scenario 12, row count | not-run | 9 expected | not-run | The register rows exist. The count runs after task T013. |
| V-14 | FR-014 | Quickstart scenario 11 | not-run | none | not-run | The baseline worktree must run first (tasks T009 to T012). |
| V-15 | FR-015 | Quickstart scenario 14 | not-run | none | not-run | The pull request does not exist yet (task T-PR). |
