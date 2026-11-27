# Specification Analysis Report: Rogue client exports use the client endpoint name

This report compares `spec.md`, `plan.md`, `tasks.md`, and the remote code on `main`. Each finding cites a path and a line. Each remote line matches the blob SHA in `design/research.md`.

## Findings

| ID | Severity | Finding | Evidence | Resolution |
| - | - | - | - | - |
| F-01 | High | Menu 29 writes client rows with the AP endpoint name. `_export_rogues` hardcodes `listSiteRogueAPs` for every label. | `src/operations/exporting/export/org_client_security_exporter.py:216`. The collector uses the client endpoint at line 88 (R-04, R-07). | T004, T005, T007, T008. |
| F-02 | Medium | Both cache-hit tests check the collector only. A writer call on a cache hit would still pass. | `tests/unit/export/test_org_client_security_exporter.py:298` and `:331` (R-11, R-12). | T014 and FR-008. |
| F-03 | Medium | The helper test pins the AP endpoint name for the generic helper. Two normal-flow tests pin three-argument calls. | Test file lines 275, 321, and 355 (R-08, R-10). | T007, T011, T012, and T013. |
| F-04 | Low | The SDK page names `mistapi.api.v1.sites.rogues`. The installed mistapi defines the function in `insights.py`. The page also says MistHelper does not use the endpoint. | Doc lines 136 and 153 (R-30, R-31). `.venv\Lib\site-packages\mistapi\api\v1\sites\insights.py:495` (R-36). `rogues.py` defines no `listSiteRogueClients`. | T016 and FR-010. |
| F-05 | High (held) | The ArangoDB rogue client vertex key uses `client_mac` only. One client on two BSSIDs keeps one document. | `src/foundation/persistence/db/writers/arango_writer.py:1846` (R-26). Issue comment 3 reports the same result. | Phase 2 `T-P2-ARANGO` after #4725 coordination (FR-016). |
| F-06 | High (held) | An existing SQLite table keeps its primary key. `CREATE TABLE IF NOT EXISTS` does not change a key. The writer adds columns only. `INSERT OR REPLACE` replaces a row that has the same key. | `src/foundation/persistence/db/database_schema_utils.py:149` (R-18). `src/foundation/support/refactors/sqlite_database_writer.py:288` (R-19) and `:368` (R-20). | Caution in Phase 1 (FR-013). Phase 2 `T-P2-SQLITE` and `T-P2-REPORT` after D-3 (FR-014, FR-015). |
| F-07 | Medium | The menu 24 combined export writes AP rows and client rows under `listSiteRogueClients`. | `src/foundation/support/refactors/serial_cc/security_events.py:287` and `:293` (R-29). | A new issue (D-9, T019). Not changed in this record. |
| F-08 | High (held) | Documents that earlier runs replaced in ArangoDB and Redis stay in place. No task in this record removes them. | Issue comment 3 reports the replacement. | FR-017 and `T-P2-CLEANUP` after D-4 approval. |
| F-09 | Medium | The preserved branch `preservation/2746-pr3011-turn0` is absent on the remote (R-51). This checkout also holds no such local ref. The issue says the branch lives on the author machine. | `git for-each-ref` on this checkout returns no `preservation/2746-pr3011-turn0`. | Listed under Unverified in `design/research.md`. The record does not touch the branch. T002 rechecks it. |
| F-10 | Low | Open PR #4813 changes `src/operations/exporting/export/data_exporter.py`. | `gh pr list --state open --json files` (R-55). | Phase 1 changes no line in that file. Rebase before `T-PR`. |
| F-11 | Info | The issue states the strategy keys. Both keys match `main`. | `endpoint_primary_key_strategies.py:1298` and `:1305` (R-13, R-14). | None. |
| F-12 | Info | The issue states the ArangoDB collection mapping. The mapping matches `main`. | `arango_writer.py:1120` (R-25). | None. |
| F-13 | Low | `_export_rogues` logs the same success message twice. | `org_client_security_exporter.py:217` and `:219`. | Not changed. Out of scope for this issue. |

## Coverage Summary

| Requirement | Tasks | Tests or checks |
| - | - | - |
| FR-001 | T005, T007, T008 | TST-01, TST-03 |
| FR-002 | T005, T011, T012, T013 | TST-05, TST-07, TST-08 |
| FR-003 | T004 | TST-01, TST-03, TST-05, TST-07, TST-08 |
| FR-004 | T009 | TST-04 |
| FR-005 | T003, T010 | TST-09, TST-10 |
| FR-006 | T018 | CHK-01 |
| FR-007 | T006, T012 | TST-07 |
| FR-008 | T014 | TST-02, TST-06 |
| FR-009 | T015 | TST-11 |
| FR-010 | T016 | CHK-02 |
| FR-011 | T017 | CHK-03 |
| FR-012 | T001, T002, T018 | CHK-01 |
| FR-013 | T019, `T-PR` | CHK-04 |
| FR-014 | T-HOLD-COORD, T-P2-SQLITE | TST-12 |
| FR-015 | T-P2-REPORT | TST-13 |
| FR-016 | T-P2-ARANGO | TST-14 |
| FR-017 | T-P2-CLEANUP | CHK-05 |

## Constrained-Field Coverage

The field `api_function_name` accepts two values in Phase 1. Menu 29 uses `listSiteRogueClients`. Menu 30 uses `listSiteRogueAPs`. TST-01, TST-03, TST-05, TST-07, and TST-08 cover both values. TST-09 and TST-10 cover the key that each value selects.

## Constitution Alignment

`plan.md` lists each constitution rule with its result and its reason. The Phase 1 rules pass. The Phase 2 rules stay on hold until their decisions and coordination finish.

## Unmapped Tasks

None. Each task maps to at least one requirement in the Coverage Summary, or to a publication gate (`T-LOCAL-GATES`, `T-PR`, `T-REMOTE-CI`, or `T-MERGE`).

## Metrics

- Functional requirements: 17. Phase 1: 13. Phase 2 hold: 4.
- Tasks: 29. Phase 1: 19. Delivery: 4. Phase 2 hold: 6.
- New or changed test functions: 13. Phase 1: 10. Phase 2 hold: 3.
- Checks: 5.
- Decisions: 10. Human decisions: 3.
- Remote checks: 55. Each row appears in `design/research.md` and in `STATUS.json`.
- Findings by severity: High 4 (F-01, F-05, F-06, F-08). Medium 4 (F-02, F-03, F-07, F-09). Low 3 (F-04, F-10, F-13). Info 2 (F-11, F-12).

## Convergence After Implementation

After Phase 1, menu 29 sends the client endpoint name. A new SQLite table for rogue clients uses the client primary key. ArangoDB and Redis receive client rows under the client endpoint name. Cache hits write nothing. The SDK page names the installed module.

Phase 1 does not repair existing SQLite tables. A table that earlier runs created keeps its AP primary key. The changelog and the pull request body state this limit.

After Phase 2 with approvals, a mismatched existing table stops the write before any insert. A read-only report lists the conflicts first. The ArangoDB key includes `bssid`. Stale AP-keyed documents change only under an approved plan.

## Unresolved Items

- U-1: The state of existing tables in operator databases is unknown. Phase 2 starts with a read-only check (`design/quickstart.md`).
- U-2: The live Mist API behavior for `limit=1000` is not verified. The code already uses this value.
- U-3: The final content of PR #4813 is unknown. Rebase before `T-PR`.
- U-4: The menu 24 issue number is unknown until T019 creates the issue.
- U-5: The local preservation branch is not in this checkout. The orchestrator must confirm it still exists before any change to the reserved test file.
- U-6: The module coverage claim in the test file docstring is not measured in this record.
