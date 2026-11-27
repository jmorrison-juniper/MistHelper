# Specification Analysis Report: Site export write results

## Findings

Severity meanings: high blocks closure or breaks a non-negotiable rule. Medium needs a task. Low is a note with no blocking effect.

| ID | Severity | Type | Finding | Evidence | Resolution |
| - | - | - | - | - | - |
| F-01 | high | Defect, Principle VI | Six statement lines in the persistence methods lack inline comments: lines 58, 67, and 68 in each exporter. | `design/research.md` rows 1 and 2, quickstart Q-06 | T007 and T008 |
| F-02 | high | Defect, Principle VI | 27 statement lines in `TestSiteWriteOutcomes` lack inline comments: lines 337, 340, 344, 347 to 355, 366, 369, 389 to 391, 394 to 397, 410, 414, 426, 431, 434, and 435. | `design/research.md` row 3, quickstart Q-06 | T009 |
| F-03 | high | Gap, closure | The route check with `Resolve-SpecFeaturePath` did not run. The owner named it as a gap on 2026-11-10. PR #4847 merged with the gap open. | Issue #4717 comment at 2026-11-10T10:07:35Z, and PR #4847 body, "Known gap" | T011 |
| F-04 | medium | Gap, FR-009 | No offline guard exists in the repository. The claim of zero socket, DNS, and SQLite attempts has no repository evidence. | `design/research.md` row 23, and E-11 and E-13 | T010 |
| F-05 | medium | Stale draft | The draft status "Publication is authorized" and requirement FR-007 predate the merge. | E-01 and E-15 | Replaced by T012 |
| F-06 | low | Stale draft | The draft Feature Branch name does not match the merged branch `fix/4717-site-export-writes`. | E-02 | Replaced by T012 |
| F-07 | medium | Stale draft and rule conflict | PR #4918 removed the menu text from `README.md`. The constitution Documentation section, line 400, says the README MUST change for each operation change. The two sources disagree. | `design/research.md` row 10, E-38, constitution lines 398-413 | Decision R-5. The owner resolves the conflict. No change in this issue. |
| F-08 | low | Stale draft | The draft counts 27 open pull requests. Seven are open now. | E-28 and E-36 | Replaced by T012 |
| F-09 | medium | Unverifiable draft | Draft tasks T001 to T007 are marked complete. Their evidence lies in session artifacts outside the repository. | E-30a, E-31, E-32, and E-39 | Replaced by T012. The claims stay absent. |
| F-10 | low | Documentation drift | The brief and `.github/copilot-instructions.md` line 21 state `mistapi>=0.64.0,<0.65`. `pyproject.toml` line 29 states `>=0.64.1,<0.65`. `requirements.txt` line 129 pins 0.64.1. | `design/research.md` rows 24, 25, and 27 | Decision R-11. A later docs change. |
| F-11 | medium | Governance | The 2026-11-09 and 2026-11-10 issue comments name a hold until the route and README gaps close. The owner account merged PR #4847 on 2026-11-19. The route gap stayed open. No issue comment after 2026-11-10 lifts the hold. | Issue #4717 comments, PR #4847 metadata | Decision R-8. T-MERGE needs orchestrator authorization. |
| F-12 | medium | Pre-existing debt, Principle I | The shared test module holds more than five top-level names. PR #4847 added the class `TestSiteWriteOutcomes`. | E-25, `design/research.md` row 3 | Complexity Tracking in `plan.md`. A separate remediation issue. |
| F-13 | low | Pre-existing gap, outside scope | In `application_list` and `system_events`, line 89 (`try:`) lacks a comment. The `mistapi.get_all` call (line 94 in both files) has no DEBUG log after it. The repair does not touch these methods. | Exporter lines 82-98 | Out of scope. Record for a separate issue. |
| F-14 | medium | Limit | Caution: the database mirror can drop a write after a successful file write. The writer still returns `True`, so the site exports report success. | `data_exporter.py` lines 176-198, `design/contracts/writer-result.md` | Out of scope. U-8. |
| F-15 | medium | Scope | Other callers of the writer can ignore the result. No audit exists. | U-9 | A separate audit issue, linked to #1794. |
| F-16 | low | Design note | The application list uses `auto_increment_with_unique` with `misthelper_internal_id` (lines 483-489). The constitution Technology section prefers natural keys. The response fields were not checked. | `endpoint_primary_key_strategies.py` lines 483-489, U-6 | Out of scope. |
| F-17 | low | Gate note | `symbol-diff` exits with code 1 when a name is added. The PR #4847 author reports this result against the pre-PR base. Against `origin/main`, comment-only edits exit 0. | PR #4847 validation evidence, item 15, U-12 | Quickstart Q-07 uses `origin/main`. |
| F-18 | low | Style note | The changelog bullet does not use bold. The example in `changelog.d/README.md` uses bold. The guard does not enforce bold. | `changelog.d/README.md` example, `test_changelog_fragment_policy.py` lines 192-197 | No action. |
| F-19 | low | Git note | The candidate commit `5501a141` lives on an archive branch. The branch diverges from `main`. The issue thread calls the candidate unpublished. | `design/research.md` row 30, U-11 | Record only. Do not merge the archive branch. |

## Coverage Summary

| Requirement | Tasks | Test or check | Status |
| - | - | - | - |
| FR-001 | T001, T002, T-LOCAL-GATES | Four failed-write cases in `TestSiteWriteOutcomes` | Present on `main`. Comments open (F-01). |
| FR-002 | T001, T002, T003 | Failed-write cases assert no `persisted` or `exported` text | Present |
| FR-003 | T001, T002 | Failed-write cases assert the filename and the endpoint | Present |
| FR-004 | T003 | Four success cases | Present |
| FR-005 | T003 | Four empty cases | Present |
| FR-006 | T003 | Four exception cases | Present |
| FR-007 | T003 | `result is None` assertions in all four tests | Present |
| FR-008 | T006, T-LOCAL-GATES | `symbol-diff`, plus the existing `TestApplicationList` and `TestSystemEvents` | Present |
| FR-009 | T010 | Harness self-test (three cases) and the module run under the harness | Absent (F-04) |
| FR-010 | T007, T008, T009 | Quickstart Q-06 scan | Absent (F-01 and F-02) |
| FR-011 | T004 | Menu reference gate and operator guide line 120 | Present |
| FR-012 | T005 | Changelog guard `test_changelog_fragment_policy.py` | Present |
| FR-013 | T011 | `test_spec_route_contract.py` and quickstart Q-05 | Partial (F-03) |
| FR-014 | T012 | `test_process_folder_structure.py` | Partial (draft) |
| FR-015 | T-PR, T-REMOTE-CI, T-MERGE | Remote CI and merge state | Open |

Success criteria: SC-001 is present (four cases). SC-002 is present (12 cases). SC-003 is absent (F-04). SC-004 is absent (F-01 and F-02). SC-005 is present (`design/research.md` rows 1 to 3). SC-006 is partial (F-03). SC-007 is open.

## Unmapped Tasks

None. Each task maps to at least one requirement. The final tasks map to FR-015, and T-LOCAL-GATES maps to FR-001 to FR-012.

## Constitution Alignment

| Principle | Result | Note |
| - | - | - |
| I. Five-Item Rule | Pass with debt | F-12. The repair adds no top-level name to the shared module. |
| II. Class-based design | Pass | The repair adds no wrapper. |
| III. Safety-first | Pass | No keyboard read and no destructive path. |
| IV. Deployment pipeline | Open | The final tasks run the pipeline. |
| V. Observability | Pass | Messages are ASCII. |
| VI. Inline comments | Fail | F-01 and F-02. T007 to T009 repair them. |
| VII. Action logging | Pass for touched blocks | F-13 lists untouched gaps. |
| Technology | Pass | SDK only. No owned transport. |
| Testing | Pass | Test code does not change. Only comments change. |
| Documentation | Pass with conflict | F-07. |
| Multi-agent git | Open | T-PR uses a worktree and a new branch. |

## Metrics

- Functional requirements: 15.
- Success criteria: 7.
- Tasks: 16. Twelve numbered tasks and four final tasks.
- Tests planned: 19. The count is 16 existing cases in `TestSiteWriteOutcomes` and 3 harness self-test cases.
- Statement lines to comment: 33. The count is 6 in the persistence methods and 27 in the test class.
- Decisions: 15. Human decisions: 0.
- Remote and local evidence rows in `design/research.md`: 30.
- Draft claims verdicts: 41. Of those, 20 are verified, 8 are stale, and 13 are absent.
- High-severity findings: 3 (F-01, F-02, and F-03).

## Convergence After Implementation

After T007 to T012 and the final tasks run, these statements must hold.

1. Each statement line in the touched code carries an inline comment. The quickstart Q-06 scan prints no statement line.
2. The offline harness reports zero socket, DNS, and SQLite attempts (SC-003).
3. `Resolve-SpecFeaturePath` returns the record path for number 4717 (SC-006).
4. The record folder holds the files listed in `plan.md`. Each directory holds five children or fewer (FR-014).
5. The pull request body names `Closes #4717`, and the merge closes the issue (SC-007).
6. The draft verdict table in `design/research.md` stays as the audit trail. Each stale claim names its replacement.
