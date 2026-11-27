# Analysis: Hardware CLI failure reporting

This review checks the spec, the plan, the tasks, and the remote evidence against each other. It also lists defects in existing work and open items.

## 1. Consistency Matrix

| Requirement | Tasks | pytest cases | Verification check |
| - | - | - | - |
| FR-001 | T005, T008 | `never_retries[TypeError]` | C-4 and the clause review in T005. |
| FR-002 | T006, T008 | `never_retries[OSError]`, `never_retries[RuntimeError]` | Output text review against the contract. |
| FR-003 | T005, T008, T010 | `never_retries[NotImplementedError]`, `never_retries[RecursionError]`, `cancel_programming_error` | C-4 |
| FR-004 | T003, T008 | `start` call count of one in each case | Log and call review. |
| FR-005 | T003, T006, T008, T010 | Caution assertions in the never-retry cases and `poll_failure` | Text review against the contract. |
| FR-006 | T006, T007, T008 | Log assertion for `Admission state: uncertain` | Log review against the contract. |
| FR-007 | T003, T009 | `refuses[OSError]` | Text review. |
| FR-008 | T004, T010 | `reply_without_session` | Reply review. |
| FR-009 | T002, T-PR, T-MERGE | None | C-1 |
| FR-010 | T011 | None | C-3 |
| FR-011 | T-REMOTE-CI | None | C-2 |

Each functional requirement maps to at least one task and at least one pytest case or verification check. The pytest cases count as tests. The verification checks C-1 to C-4 cover the requirements that have no pytest case.

## 2. Spec, Plan, and Tasks Consistency

- The counts agree. The spec has 11 requirements, the tasks file has 15 tasks, and the record has 10 planned pytest cases.
- SC-002 names 10 cases. T008 changes 3 and adds 3. T009 adds 1. T010 adds 3. The total is 10.
- Each task names exact repository paths. Each task names one verification command from the local gates table.
- The status values follow the legend in `tasks.md`. Each status matches the remote and local evidence in `design/research.md`.
- The plan lists each Complexity Tracking row. Each row has an ID that appears once.
- The admission states match in the spec (Key Entities), the data model, the contract, and the tasks.

## 3. Remote Evidence Summary

- The remote check count is 43. The research table has 43 rows. The STATUS file has 43 entries. The summary states 43.
- Absent items: 15. Present items: 28. Partial items: 0. Stale items: 0.
- The remote `main` ref equals the local HEAD (R-43). Local-only evidence for the branch is labeled in `design/research.md` section 4.

## 4. Defects in Existing Work

- **A-1 Issue text predates the committed fix.** The issue quotes the log text `Error type: OSError.`. The committed CLI prints `Cause: %s. Admitted: %s.` (`cli.py` line 79). The issue was created at 23:05:37 UTC. Commit `8140bb37c` followed at 23:51:08 UTC.
- **A-2 Completion claim without a push.** The #4773 record states that the #4779 repair passed (`tasks.md` lines 420 to 423). Issue 4779 remains open. GitHub has no commit `8140bb37c` (R-39).
- **A-3 Count conflict.** The #4773 record states 64 standalone CLI cases (`tasks.md` line 319). The same record states 66 cases (`tasks.md` line 423).
- **A-4 Branch name.** The branch `3999-transceiver-master-report` does not match issue 4773. `development-setup.md` lines 178 to 181 require a branch name that holds the type, the issue number, and a slug (R-27).
- **A-5 Changelog fragment layout.** The fragment has two headings named by change type, `### Added` and `### Fixed`. Its bullets name no issue. `changelog.d/README.md` lines 37 to 39 require one heading that names the change, and an issue number at the end of each bullet (R-25).
- **A-6 Unpublished dependencies.** The CLI imports `ExplicitSessionServices` (R-07). The CLI passes `raise_on_cancel` to `safe_input` (R-08). The package `operations/hardware/` is absent on `main` (R-04).
- **A-7 Missing action logs.** `_collect` writes no log before or after the preview and start requests (`cli.py` lines 89 to 103). Constitution Principle VII requires them.
- **A-8 Boolean admission.** The CLI passes `bool(workflow.session_id)` as `admitted`. An uncertain admission therefore logs `Admitted: False` (`cli.py` lines 71 and 79).
- **A-9 Programming errors under RuntimeError.** `NotImplementedError` and `RecursionError` subclass `RuntimeError`. Both clauses catch them (`cli.py` lines 70 and 243).
- **A-10 Five-children violations.** `operations/hardware/` holds six children. `tests/unit/websocket_streams/web/hardware/` holds six. `test_cli.py` holds seven top-level names (L-08 for the names, L-17 for the file counts).
- **A-11 Test-quality counts conflict.** The #4773 owner comment reports two retained findings. Issue 4783 lists five new findings in `test_normalization.py`, `test_report.py`, and `test_contracts.py`.
- **A-12 Menu blocker status.** The #4773 owner comment says the numbered menu is blocked by the #4607 entry-point request. Pull request #4607 merged on 2026-11-13T07:14:03Z.
- **A-13 Rebase overlap.** The base-to-branch and base-to-main diffs share ten file paths. They are `documentation/operator-guide.md`, `src/foundation/support/refactors/endpoint_primary_key_strategies.py`, `src/mist/realtime/websocket_streams/web/services/assembly/collaborators.py`, `src/mist/realtime/websocket_streams/web/services/assembly/factory.py`, `src/mist/realtime/websocket_streams/web/services/operations/artifacts.py`, `src/mist/realtime/websocket_streams/web/services/operations/sessions.py`, `src/mist/realtime/websocket_streams/web/static/websockets.js`, `src/mist/realtime/websocket_streams/web/templates/websockets_page.html`, `tests/e2e/websockets_tab/test_websockets_page.py`, and `tests/unit/websocket_streams/web/test_ws_web_services.py`. The rename of `hardware_xml.py` adds one more conflict source (L-19).
- **A-14 Format conflict.** `main` lists the formats `csv`, `master-xml`, and `csv-master-xml` (R-06, line 309). The branch lists only `xml`, `json`, and `both` (`preset.py` line 281). A plain take of the branch version removes the menu 309 formats from `main`.

## 5. Unresolved Items

- **U-1** The three regression cases have not run on the branch. Task T001 runs them.
- **U-2** The owner reports 358 passed tests and 93.98 percent hardware coverage. No run in this step confirms those values.
- **U-3** The test-quality finding count is unresolved (A-11). Task T-LOCAL-GATES records the actual count.
- **U-4** The status of the #4607 menu blocker is unresolved (A-12). The owner confirms it.
- **U-5** The rebase outcome is unknown. Task T002 records it.

## 6. Follow-Up Issues to File

The agent cannot create issues. The orchestrator files each item below.

- **F-1 Stop the admitted parent after an operational failure.** `cli.py` lines 212 to 233 return after a poll error without a stop. A stop changes the CLI outcome, so it needs its own issue.
- **F-2 Report publication hides programming errors.** The branch report path has broad catches at `report.py` lines 332 and 479. The portal uses the same path, and the native-preservation contract applies.
- **F-3 Malformed polling replies raise programming errors.** `cli.py` lines 220 to 223 read the summary reply with `payload.get`. A malformed external reply should be an operational failure.
- **F-4 Split the CLI package and tests.** Resolve A-10 and remove the five-children violations from `operations/hardware/`, `tests/unit/websocket_streams/web/hardware/`, and `test_cli.py`.

## 7. Deviations From the Brief

- **Publication branch name.** T-PR pushes the #4773 publication branch instead of a new branch named for issue 4779. The repair exists only on that branch (D-1 and D-2).
- **Remote task checks.** T-REMOTE-CI and T-MERGE cite a local gate command. The remote evidence comes from `gh pr checks` and the remote tree read. No local gate row covers the remote steps.
- **Test count definition.** `tests_planned` counts pytest cases only. Requirements FR-009 to FR-011 use verification checks C-1 to C-3 instead of pytest cases.
