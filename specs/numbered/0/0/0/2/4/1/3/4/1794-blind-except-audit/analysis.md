# Specification Analysis Report: Blind Except Handler Audit (issue 1794)

## Summary

This review checks the spec, plan, and tasks against each other and against GitHub `main`. The verified commit is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. The review found four consistency gaps (C-21 to C-24), and this revision fixes each one. It finds 24 defects in the three legacy records and in the coordination state. Each defect has an action in this record or an owner in the unresolved list. No human decision is required (`human_decision_required` is false for all decisions).

The remote verification covers 129 rows (research.md). Of these, 98 are present, 24 stale, 2 partial, and 5 absent. The 35 existing-record rows give 18 present, 16 stale (partial counts as stale), and 1 absent.

## Consistency review

| ID | Check | Result | Evidence |
| - | - | - | - |
| C-1 | Requirement count in spec and STATUS | PASS | 38 requirements (FR-001 to FR-038). STATUS `requirements` is 38. |
| C-2 | Task count in tasks and STATUS | PASS | 36 numbered tasks and 4 final tasks, 40 in all. STATUS `tasks` is 40. |
| C-3 | Remote row count in research and STATUS | PASS | 129 rows. Path, ref, blob, result, and line match row for row. |
| C-4 | Decision count in research and STATUS | PASS | 14 decisions. STATUS `decisions` has 14, all with `human_decision_required` false. |
| C-5 | Site total in the plan equals the research clusters | PASS | 678 sites across S01 to S23 (research cluster totals). |
| C-6 | Each slice holds at most 40 sites (FR-017) | PASS | Largest slices S07, S13, S19, and S20 hold exactly 40. |
| C-7 | Excluded-tree counts agree | PASS | 23 + 26 + 32 + 68 = 149 sites (research, plan, tasks T005 and T033). |
| C-8 | Slice follow-up issues agree with the slice count | PASS | 23 slices plus one final gate give 24 issues (T032). |
| C-9 | Tests planned agree with the test rule | PASS | Each slice names three test cases: operational path, propagation, and redaction (FR-021). Each outcome row names one of them. S24 adds one case (FR-026). Twenty-three slices times three, plus one, gives 70. STATUS `tests_planned` is 70. |
| C-10 | Final gate lines agree | PASS | Comment lines 588 to 593, disable line 594, select line 209 (RC-002, RC-003, spec FR-023, plan S24, tasks T031). |
| C-11 | Closing keywords agree with FR-029 | PASS with a risk | Slices use `Refs`. The final gate closes #1794. The record pull request closes #1794 because the brief requires it (D-12, A-13). |
| C-12 | Legacy-record handling agrees | PASS | Supersede, do not delete (D-11, FR-030, T036). |
| C-13 | Pylint scope agrees | PASS | CI reads `SRC_PATH` (RC-014). The plan and research use the same root. |
| C-14 | Route agrees | PASS | `specs/numbered/0/0/0/2/4/1/3/4/` in spec, plan, research (RC-096), and tasks T006. |
| C-15 | Gate command forms agree with CI | PASS | The quickstart uses the CI forms: `bandit -c pyproject.toml -r .` (ci.yml line 451, RC-015), `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70` (ci.yml lines 101 and 127, RC-010), and `radon cc` piped to `complexity-gate --max 10` (ci.yml line 549, RC-016). |
| C-16 | Python version agrees | PASS | 3.15 in spec (FR-038), plan, and research (RC-005). |
| C-17 | Changelog names agree with the README | PASS | `issue-<child>-<slug>.md` in plan and tasks, matching the README rule (RC-025). |
| C-18 | Held commit owners agree | PASS | The plan table names one owner for each of the 14 commits that have one. Commits c3d0f769 and 8a700b2b have none because squash commits supersede them (RC-103, RC-105). Task T034 applies to all 14 owned commits. |
| C-19 | S11 covers `running_version.py` | PASS | Added to plan S11 and task T018 after this review. The file has no candidate site, so the site total stays at 678. |
| C-20 | Plan and spec use the same outcome order | PASS | Delete, then narrow, then keep (FR-008, D-3). |
| C-21 | FR-038 has a task | FIXED | FR-038 had no task row. Rule 1 and T-LOCAL-GATES now name it. |
| C-22 | Unverified items have an owner | FIXED | U-6, U-10, U-11, and U-12 had no task text. Rule 9 and tasks T018, T032, and T035 now name them. |
| C-23 | Style rules hold | FIXED | plan.md and tasks.md held semicolons, and this file held an ellipsis. Each instance is replaced. |
| C-24 | Quickstart numbers agree | FIXED | T001 cited Q-2 and Q-3 for the counts. It now cites Q-3 and Q-7 (pylint). |

## Coverage matrix

Each requirement maps to at least one task and at least one check. The checks are quickstart commands (Q-n), named tests, or a named CI step. Quickstart defines Q-1 to Q-23.

| FR | Tasks | Check |
| - | - | - |
| FR-001 | T001 | Q-2 (pins), Q-3 (ruff counts) |
| FR-002 | T001 | Q-7 (pylint W0718 count) |
| FR-003 | T001 | Q-9 (roots named in the reconciliation) |
| FR-004 | T002 | Q-9 (reconciliation) |
| FR-005 | T001 | Q-3 (`--ignore-noqa` count is the scope metric) |
| FR-006 | T003 | Q-13 (growth guard test) |
| FR-007 | T008 to T030 | Q-4 (site list), outcome table (`contracts/outcome-table.md`) |
| FR-008 | T008 to T030 | Outcome order in `contracts/outcome-table.md` |
| FR-009 | T008 to T030 | Delete-path test per slice (FR-021) and caller column (`contracts/outcome-table.md`) |
| FR-010 | T008 to T030 | Propagation test per slice (FR-021), Q-22 |
| FR-011 | T018 | Test: `tests/unit/firmware/test_running_version.py` |
| FR-012 | T008 to T030 | Log test per slice (`contracts/log-record.md`) |
| FR-013 | T008 to T030 | Log test per slice (`contracts/log-record.md`) |
| FR-014 | T008 to T030 | Q-20 (changed-line comment scan) |
| FR-015 | T004, T008 to T030 | Q-11 (pylint disable inventory), Q-12 (no new `noqa`) |
| FR-016 | T008 to T030 | Redaction test per slice through the real handler chain (RC-061) |
| FR-017 | T008 to T030 | Q-4 (site count per slice) |
| FR-018 | T008 to T030, T-PR | Q-19 (outcome rows in the pull request body) |
| FR-019 | T008 to T030 | Q-14 (baseline reduction) |
| FR-020 | T008 to T030, T-REMOTE-CI | Q-23 (rebase check), CI run |
| FR-021 | T008 to T030 | Three tests per slice, run by Q-6 |
| FR-022 | T031 | Q-15 (final gate configuration) |
| FR-023 | T031 | Q-15 (comment lines), Q-16 (pylint score) |
| FR-024 | T031, T-MERGE | Q-19 (pull request body) |
| FR-025 | T031 | Q-15 (`extend-exclude` unchanged) |
| FR-026 | T031 | Q-13 (stored-baseline test with an empty baseline) |
| FR-027 | T007, T034 | Q-17 (held commit ancestry) |
| FR-028 | T035, T-MERGE | Q-17 (presence and replacement) |
| FR-029 | T032, T-PR | Q-19 (closing and reference keywords) |
| FR-030 | T036 | Review of this file (A-1 to A-24) |
| FR-031 | T006 | Q-18 (route) |
| FR-032 | T005, T033 | Q-10 (excluded-tree counts) |
| FR-033 | T029, T030 | Q-4 with the test paths, and the tests of each slice |
| FR-034 | T-LOCAL-GATES | Q-21 (STE score) |
| FR-035 | T-PR | CI changelog guard (`ci.yml` line 298) and `changelog.d/README.md` (RC-025) |
| FR-036 | T008 to T030 | Q-20 (changed-line comment scan) |
| FR-037 | T-LOCAL-GATES | Q-6 (local gate list) |
| FR-038 | T-LOCAL-GATES | Q-2 (Python 3.15), Q-6 (mypy and pytest in `.venv`) |

## Defects in existing work

| ID | Defect | Evidence | Severity | Action |
| - | - | - | - | - |
| A-1 | Record A narrows the firmware resolver to `RuntimeError`. The REST wrapper catches transport faults and returns an `APIResponse`. The request module raises `RuntimeError` only inside token rotation. The claimed behavior and its test do not match the SDK. | RC-037, RC-093, RC-094 | HIGH | D-4. S11 and T018 replace the catch with a response check. |
| A-2 | Records A, B, and C state Python 3.13 (`plan.md` line 13 in records A and C, line 19 in record B). The repository requires 3.15, and the ruff target is `py315`. | RC-006, RC-005 | MEDIUM | D-10 and FR-038. |
| A-3 | Record A names `tests/unit/firmware/test_firmware_manager_ssr.py`, which moved. Its fragment `changelog.d/issue-1794-blind-except.md` is consumed into `CHANGELOG.md` line 1091. | RC-039, RC-040 | LOW | Superseded by D-11. |
| A-4 | Record B says "Specification only. No code change exists yet." It also says issue #1792 must land first. Both statements are stale. #1792 is closed, and RUF100 is selected. | RC-035, GitHub state | HIGH | Slices start from the current state of main. T001 and T007 confirm it. |
| A-5 | Record B counts are stale. Its spec.md (line 66) gives 500 as the true count, and its plan.md (line 53) lists 412, 500, and 493. It states 33 handlers in `MistHelper.py`, 11 handlers in `const_definitions_exporter.py`, and 8 handlers in `starlink_dashboard.py`. The root file is absent. Its `pyproject.toml` line references (164 in tasks.md T032, 475 in RC-002, and 481 in tasks.md T033) are stale. | RC-001, RC-002, RC-054, RC-057, RC-058 | HIGH | T001 measures the counts again. D-1. |
| A-6 | Record B pins are stale. It names pylint 4.0.6 and ruff 0.16.0. The pins are 4.1.4 and 0.17.6. | RC-007, RC-008 | MEDIUM | D-10. T001 records the pins. |
| A-7 | Record B gate commands differ from CI. Its tasks.md T005 and T006 read `MistHelper.py` and `src` for pylint, and its T037 uses `vulture src/ --min-confidence 80`. CI reads `SRC_PATH` (`src/`) with a vulture confidence of 70 (ci.yml lines 78 and 127). The local gates table names `bandit -c pyproject.toml -r <package> -q` (copilot-instructions line 67), but CI runs `bandit -c pyproject.toml -r .` (ci.yml line 451). | RC-010, RC-013, RC-015 | MEDIUM | The quickstart uses the CI forms. |
| A-8 | Record B SC-011 requires a second person to read three `keep` comments. An agent cannot run that step. | Record B spec.md line 251 (SC-011) and tasks.md T041 | LOW | Restated as a pull request review step (spec SC-004 and the Assumptions section). |
| A-9 | Record C names test paths `tests/unit/test_bulk_switch_upgrader.py` and `tests/unit/test_site_auto_upgrade.py`, which moved. Its fragment is consumed into `CHANGELOG.md` line 1057. | RC-047, RC-048, RC-053 | MEDIUM | Superseded by D-11. The moved paths are in research.md. |
| A-10 | Records A and C check T001 to T012 and leave T013 and T014 open. Record B leaves all 42 tasks unchecked. The records do not describe the merged state. | Legacy tasks files | MEDIUM | Superseded by D-11. T036 records the supersession. |
| A-11 | Child issues #2833, #2834, #2835, #2836, and #2926 closed while the local counts still show sites. #2833 closed as COMPLETED on 2026-09-18. The firmware area holds 53 sites, export holds 94, and the upgrade portal holds 131. | GitHub state, Local evidence | HIGH | D-7. T032 opens new issues and leaves the children closed. |
| A-12 | Record B's area table (spec.md lines 84 to 96) predates the current tree. Its counts differ from the counts measured at main. The top-level `src` directories on main are `foundation`, `interfaces`, `mist`, and `operations`. | research.md Measured state, Record B spec.md lines 84 to 96, git ls-tree at the verified commit | MEDIUM | The plan uses the current paths and the measured counts. |
| A-13 | A closing keyword closes #1794 when a pull request merges. The auto-close workflow closed the issue twice (issue comments 8 and 10). The record pull request body follows the brief and contains `Closes #1794`. | RC-023, issue comments 8 and 10 | HIGH | D-12 and T-PR. The orchestrator reopens #1794 after the merge if the umbrella must stay open. |
| A-14 | The stored-baseline test requires at least one entry in the baseline. A zero-debt final state fails that test. | RC-032, ratchet test at line 445 | MEDIUM | FR-026 and T031 update the test in the final pull request. |
| A-15 | The growth guard and ruff disagree on scope. The baseline excludes only `tests` (RC-033, line 6). Ruff includes tests. Ruff excludes `src/interfaces/visualization/maps/`, and the guard does not. | RC-033, RC-004 | MEDIUM | D-8 and FR-033. |
| A-16 | Held commits are not on main. Their bases changed, and their test paths moved. The address-normalization base conflicts with PR #4503. | RC-104, RC-106, RC-112 to RC-125, RC-065, RC-067, RC-070, RC-073, RC-074 | HIGH | D-6, FR-027, T034. |
| A-17 | Earlier held slices leaked tracebacks that contained a synthetic token. The owners changed them to log only the exception type. Main now redacts `exc_text` through `SensitiveFilter`. | Issue comments 17, 18, 20, RC-060, RC-061 | MEDIUM | D-5 and FR-016. Each slice has a redaction test. |
| A-18 | The working-tree copy of `logger_utils.py` differs from main. | Local evidence (git hash-object) | LOW | This record uses only main. tasks.md rule 9 requires a clean worktree for each slice. |
| A-19 | The repository holds 57 inline pylint disables. Each kept site that pylint flags needs one. The final gate depends on them. | Local evidence | MEDIUM | D-13 and FR-015. |
| A-20 | The pylint score is 9.53 against a 9.5 floor. The final gate can lower the score. | RC-128, RC-129 | MEDIUM | FR-023 and T031 run the pylint gate before merge. |
| A-21 | The CSV-template changes in `file_path_utils.py` are uncommitted, and the session that owns them was archived. Their availability is not verified. | Issue comment 61, U-7 | HIGH | S16 restores the session before it changes the file. This record treats the work as recoverable, not lost. |
| A-22 | The issue title and body state 412. The last reported ruff count is 524. | Measured state (research.md), issue comment 9 | MEDIUM | T001 measures the count (Q-3). |
| A-23 | The growth guard counts only blind handlers, which are broad handlers whose name stays unused. A broad handler that logs can grow until the final gate. | RC-032 docstring | LOW | D-2. The final gate closes the gap. |
| A-24 | Issue comments quote a baseline run of 29,818 passing unit tests (comment 5, 2026-10-29). The count is old. | Issue comment 5 | LOW | T001 records the current count. |

## Unresolved items

| Item | Owner or task | Next step |
| - | - | - |
| U-1 ruff BLE001 count on main | T001 | Measure with ruff 0.17.6 (Q-3). The last reported value is 524. |
| U-2 pylint W0718 count | T001 | Measure with pylint 4.1.4 (Q-7). The recorded 493 is stale. |
| U-3 ssh ruff count | T015 (S08) | Record the ruff counts for `src/operations/execution/ssh` with and without `--ignore-noqa`. The text count is 39. |
| U-4 pylint reports logged handlers that ruff exempts | T004 | Run pylint in the T004 verification. Issue comment 32 cites 80 exception log calls and 8 `exc_info` calls. |
| U-5 RUF100 behavior for an inert `noqa` | T001 | Check with a temporary file. The implementer deletes the file after the check. |
| U-6 working-tree `logger_utils.py` | tasks.md rule 9 | Start each slice from a clean worktree. This record does not use the local copy. |
| U-7 CSV-template changes | S16 (T023) | Recover the changes from the archived session before the file changes (issue comment 61). |
| U-8 effect of PR #1788 on the pylint scope | None | Not used by any decision (D-1 to D-14) or task. The PR title was read. The diff was not read. |
| U-9 B110 sites that spec 1032 covers | None | Not used by any decision or task. The site count was not read. |
| U-10 body of `listSiteDevicesStats` after line 1051 | T018 (S11) | Read the body before the response check is written. A `RuntimeError` inside it changes D-4. |
| U-11 closure reasons of the child issues and #1709 | T032 | Read the closing comments before the new issues open. |
| U-12 branches that hold the held commits | T035 | Read the branch names before the preservation check. |
| U-13 text matches in string literals in `tests/` | T029 (S22) | Exclude string literals from the handler count. The ratchet test keeps its guard logic. |
| U-14 effect of the final gate on the pylint score | T031 (S24) | Run the pylint gate before merge (Q-16). RC-129 records 9.53 before the change. |
| U-15 callers of `_next_apitoken` in mistapi | T018 (S11) | Read the callers before the response check. A caller without a catch can raise `RuntimeError` on a REST path. |

## Notes on the review

- This review reads GitHub main through `gh api` for every remote row. Local counts come from the git object store at the verified commit, which equals main.
- The review does not run ruff, pylint, mypy, or the tests (repository rule 2). Each command appears in the quickstart for the implementer.
- The 129 remote rows and the 35 existing-record rows match between research.md and `1794-STATUS.json`.
