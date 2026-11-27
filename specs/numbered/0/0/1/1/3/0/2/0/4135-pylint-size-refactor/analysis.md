# Analysis: Consistency review for issue 4135

## Consistency review

### Spec, plan, and tasks

- Each functional requirement FR-001 to FR-018 maps to at least one task. The map appears in the list below.
- Each file in the change map in `plan.md` maps to at least one task. The map covers the new packages, the modified files, and the test files.
- Each task names exact repository paths and one verification command from the local gates table. Task T-PR and Task T-MERGE use the pull request checks instead of a table command, because the table has no such command.
- Each new test function appears in the task that adds it. The list has seven test functions.
- The tasks file has 33 tasks. Final tasks are `T-LOCAL-GATES`, `T-PR`, `T-REMOTE-CI`, and `T-MERGE`.

Requirement-to-task map:

| Requirement | Tasks | Test or gate |
| - | - | - |
| FR-001 | T013 | `test_user_facing_classification_branches` |
| FR-002 | T010, T011, T012, T001 | Registry hash test |
| FR-003 | T020, T021, T022 | Writer tests |
| FR-004 | T014, T015 | Portal tests and line count |
| FR-005 | T041 to T046 | Pylint explicit command, safe sweep |
| FR-006 | T030, T031 | Endpoint tests |
| FR-007 | T001, T030, T031, T032 | Endpoint order and value test |
| FR-008 | T001, T044 | Menu key order test |
| FR-009 | T010, T020, T049 | Import-cycle test |
| FR-010 | T042, T046 | Symbol gate with listed names |
| FR-011 | T047, T048 | Full test shards |
| FR-012 | T030, T040, T010, T014 | Ratchet test |
| FR-013 | T003, T-LOCAL-GATES | Ratchet test |
| FR-014 | T048, T-LOCAL-GATES | Safe sweep and portal tests |
| FR-015 | T002, T-LOCAL-GATES | Explicit Pylint command |
| FR-016 | All code tasks | Review check, no automated test |
| FR-017 | T050 | STE gate and the count check |
| FR-018 | T051 | Changelog policy test |

### Plan and remote code

- The plan states the counts from `design/research.md`. Each count matches a remote row. The row numbers are 1 to 62.
- The endpoint key count is 612 in the remote decode. The block sizes of 102 divide that count evenly.
- The menu count is 309. The four block sizes are 78, 77, 77, and 77, which sum to 309.
- The nested ratchet counts are 190, 33, and 236. They match the test string at line 177 of the nested test.

### Counts across meta files

- `STATUS.json` must hold 62 `remote_checks` rows, the same as `design/research.md`.
- `summary.md` must state 62 remote checks.
- The validator reports the same count from both files.

## Defects in existing work

1. The issue body names three source paths under pre-move roots and gives line numbers from an old commit. Remote evidence shows no path under those roots on `main` (row 61). The current paths hold the same blobs that the issue names.
2. The issue body reports R0801 at lines 99 to 109 of one workflow and lines 448 to 457 of the other. The current text at those lines is different code. The duplicated block is the `_write` method (row 20 and row 21).
3. The issue body reports R0913 and R0917 for one function of six arguments. No such signature exists on `main` (research, Findings on main).
4. The issue comment of 2026-11-08 states that pull request 4607 is open and owns `MistHelper.py`. The pull request merged on 2026-11-13 (row 58).
5. The issue comment of 2026-11-09 reports nine findings on commit 3964d21. The current findings differ (row 60).
6. The measured line count of `MistHelper.py` is 8,372 LF lines. The architecture table states 8,071 lines (row 38). The copilot instructions state 8,382 lines for 2026-10-04 (row 39).
7. A `Get-Content` count of `MistHelper.py` gave 7,738 lines. That method undercounts. The LF split gives 8,372 lines, which matches the grep line numbers. Use the LF method in every count.
8. The module `scripts/menu_api_map` is absent on `main` (row 54). The local gates table and the CI job `menu_reference_drift` both run it (row 62). A CI run of that job on `main` fails when the job runs. The repair issue in Task T053 covers this defect.
9. The CI Pylint job lints `src/` only (row 29). The issue names two files outside `src/`. The explicit Pylint command covers them. The CI gate does not.
10. The symbol comparator treats every removed module-level name as lost (row 50). The CI has no symbol job (row 32). The local gate table expects a clean result for each file. A deliberate move cannot meet that expectation.
11. The nested-package test asserts the exact message "33 violations, 236 total excess" (row 27). Any future count change requires an edit to that string.
12. The endpoint catalog test reads `MistHelper.py` text to find `menu_actions` (row 46). A move breaks that read. Task T048 changes the read.
13. `src/foundation/support/refactors/` holds 33 children (row 25). The file under that folder is the endpoint module. The change keeps the module path and adds no child.
14. The constitution requires a class-based design. The functions that move from `MistHelper.py` keep their module-level form. Task T052 records the remediation.
15. The constitution limits a function to 25 lines. `_build_registry` spans 507 lines before the change. The split removes that function. Other touched functions keep their length. Task T052 records the remediation.

## Conflicts and their resolution

- Symbol gate versus the no-shim rule. Resolution: D-10 in `design/research.md`. Moved names leave `MistHelper.py`. The pull request lists each name. The record makes no claim that the gate passed.
- Five-child rule with or without `__init__.py`. Resolution: Principle I names the nested-package guard as the enforcement point, and the guard excludes `__init__.py`. The change follows that count. Under a stricter count that includes `__init__.py`, `src/foundation/support` reaches six children. No other parent under `src/` fits the portal package and keeps a free slot under the stricter count. Task T052 records this as a remediation item.
- Branch type. Resolution: D-16. The constitution lists `fix`, `feat`, and `chore`. The branch uses `chore`, and the commit uses `refactor`.
- Fixture folder. Resolution: D-12. The constants live in existing test modules, because `tests/fixtures/` has many children.

## Unresolved items

1. Pylint has not run on `main`. Task T002 runs it before any code change. If R0913 or R0917 appears, a new task is needed.
2. The menu gate module is absent (row 54). Task T053 files the repair issue. Until the repair lands, the gate reports the blocked result.
3. The location of `GlobalImportManager.MenuEntry` is not known. Task T044 locates it before the menu move.
4. The remediation issue number is not known until Task T052 files the issue.
5. No automated test checks inline comments (FR-016). A reviewer checks each changed line. The pull request lists the reviewer check.
6. The Pylint similarity defaults for docstrings and signatures are not read. Task T002 confirms the R0801 result.
7. The test migration covers 805 matches in 108 files. Task T048 repeats the search before and after the migration.
8. A dictionary order dependency in another test is not ruled out. Task T048 runs the full shards.
