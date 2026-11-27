# Tasks: Rogue client exports use the client endpoint name

**Input**: Numeric record at `specs/numbered/0/0/1/2/2/4/1/2/4732-rogue-client-endpoint/`.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, `design/data-model.md`, `design/contracts/`.

**Format**: `- [ ] ID [P?] [Story] Description`. `[P]` marks a task that touches no file another open task touches. `[Story]` maps a task to a user story in `spec.md`.

**Status values**: `open`, `verified-present`, `partial`, or `absent`. A status of `absent` means the change is not on `main` yet.

**Test IDs**: `TST-nn` names a pytest function. `CHK-nn` names a check command in the Checks section.

## Phase 1: Preconditions

**Purpose**: Confirm the holds and claim the work before any file changes.

- [ ] T001 Claim issue #4732 and create the branch in a worktree. FR-012. Status: open.
  - Files: `src/operations/exporting/export/org_client_security_exporter.py`, `tests/unit/export/test_org_client_security_exporter.py`, `documentation/api/sites/GET_sites_site_id_insights_rogues_clients.md`, and `changelog.d/issue-4732-rogue-client-endpoint.md`. This task changes none of them. The worktree root is `..\MistHelper-4732`.
  - Acceptance: The issue carries `in-progress`. Branch `fix/4732-rogue-client-endpoint` starts from `origin/main`.
  - Verify: `gh issue view 4732 -R jmorrison-juniper/MistHelper --json labels`

- [ ] T002 [P] Recheck the holds and the file overlap. FR-009, FR-012. Status: open.
  - Files: `src/operations/exporting/export/org_client_security_exporter.py`, `tests/unit/export/test_org_client_security_exporter.py`, `documentation/api/sites/GET_sites_site_id_insights_rogues_clients.md`, and `changelog.d/issue-4732-rogue-client-endpoint.md`. This task changes none of them.
  - Acceptance: Issue comments 2 and 3 still stand. No open pull request changes a Phase 1 file.
  - Verify: CHK-01

- [ ] T003 [P] Confirm the endpoint strategies on `main`. FR-005. Status: verified-present.
  - Files: `src/foundation/support/refactors/endpoint_primary_key_strategies.py` (lines 1296-1309).
  - Acceptance: `listSiteRogueAPs` uses `["bssid", "ap_mac"]` at line 1298. `listSiteRogueClients` uses `["client_mac", "bssid"]` at line 1305.
  - Verify: `python -m pytest tests/unit/export/test_org_client_security_exporter.py -q -k PrimaryKeys` after T010, before T004.

## Phase 2: Foundational (endpoint name transport)

**Purpose**: Make the endpoint name an explicit input of the export helper.

- [ ] T004 Add keyword-only `api_function_name: str` to `_export_rogues`. FR-003. Status: absent.
  - Files: `src/operations/exporting/export/org_client_security_exporter.py` (lines 210-216).
  - Acceptance: The helper passes `api_function_name` to the export writer. No endpoint literal remains in the helper.
  - Verify: `python -m pytest tests/unit/export/test_org_client_security_exporter.py -q`. TST-01, TST-05, TST-07, and TST-08 fail until T007, T011, T012, and T013 land.

- [ ] T005 Pass the endpoint name at both callers. FR-001, FR-002. Status: absent.
  - Files: `src/operations/exporting/export/org_client_security_exporter.py` (lines 94 and 117).
  - Acceptance: Line 94 passes `api_function_name="listSiteRogueClients"`. Line 117 passes `api_function_name="listSiteRogueAPs"`.
  - Verify: `python -m pytest tests/unit/export/test_org_client_security_exporter.py -q -k "rogue_clients or rogue_aps"`

- [ ] T006 Add action logs and inline comments to `_export_rogues`. FR-007. Status: absent.
  - Files: `src/operations/exporting/export/org_client_security_exporter.py` (lines 210-224).
  - Acceptance: An info log names the count, label, endpoint name, and file name before the export writer call. A debug log names the returned status after it. Every changed line has an inline comment. Log text is ASCII.
  - Verify: TST-07 after T012.

- [ ] T015 Keep the import lines and the list-type assertion unchanged. FR-009. Status: verified-present.
  - Files: `tests/unit/export/test_org_client_security_exporter.py` (lines 21-25 and 138-143).
  - Acceptance: `git diff` shows no change at those lines.
  - Verify: TST-11, `python -m pytest tests/unit/export/test_org_client_security_exporter.py -q -k test_success`

## Phase 3: User Story 1 - Client rows use the client endpoint name (Priority: P1)

**Goal**: Menu 29 sends `listSiteRogueClients` to the export writer and the collector.

**Independent Test**: TST-01, TST-03, TST-04, TST-09, and TST-10 run with mocks.

- [ ] T007 [US1] Update `TestRogueClients.test_normal_flow_exports` to the four-argument call. FR-001, FR-003. Status: absent.
  - Files: `tests/unit/export/test_org_client_security_exporter.py` (lines 311-321).
  - Acceptance: The assertion expects `api_function_name="listSiteRogueClients"` in the helper call.
  - Verify: `python -m pytest tests/unit/export/test_org_client_security_exporter.py -q -k "TestRogueClients and test_normal_flow_exports"` (TST-01)

- [ ] T008 [US1] Add `TestRogueClients.test_writes_client_endpoint_name` after line 321. FR-001. Status: absent.
  - Files: `tests/unit/export/test_org_client_security_exporter.py`.
  - Acceptance: Two synthetic client rows with the same `bssid` and `ap_mac` and different `client_mac` reach the export writer with `api_function_name="listSiteRogueClients"`.
  - Verify: `python -m pytest tests/unit/export/test_org_client_security_exporter.py -q -k writes_client_endpoint_name` (TST-03)

- [ ] T009 [US1] Add `TestRogueClients.test_fetches_client_endpoint`. FR-004. Status: absent.
  - Files: `tests/unit/export/test_org_client_security_exporter.py`.
  - Acceptance: The collector receives `ocse.mistapi.api.v1.sites.insights.listSiteRogueClients` as its first argument.
  - Verify: `python -m pytest tests/unit/export/test_org_client_security_exporter.py -q -k fetches_client_endpoint` (TST-04)

- [ ] T010 [US1] Add class `TestRogueEndpointPrimaryKeys` before line 358 with two DDL tests. FR-005. Status: absent.
  - Files: `tests/unit/export/test_org_client_security_exporter.py`.
  - Acceptance: The DDL for the client endpoint contains `PRIMARY KEY (client_mac, bssid)`. The DDL for the AP endpoint contains `PRIMARY KEY (bssid, ap_mac)`.
  - Verify: `python -m pytest tests/unit/export/test_org_client_security_exporter.py -q -k PrimaryKeys` (TST-09 and TST-10)

**Checkpoint**: User Story 1 passes its tests on the changed code.

## Phase 4: User Story 2 - AP export and fast-mode cache hits (Priority: P1)

**Goal**: Menu 30 keeps `listSiteRogueAPs`. A cache hit writes nothing.

**Independent Test**: TST-02, TST-05, TST-06, TST-07, and TST-08 run with mocks.

- [ ] T011 [US2] Update `TestRogueAps.test_normal_flow_exports` to the four-argument call. FR-002. Status: absent.
  - Files: `tests/unit/export/test_org_client_security_exporter.py` (lines 345-355).
  - Acceptance: The helper call expects `api_function_name="listSiteRogueAPs"`.
  - Verify: `python -m pytest tests/unit/export/test_org_client_security_exporter.py -q -k "TestRogueAps and test_normal_flow_exports"` (TST-05)

- [ ] T012 [US2] Update `TestExportRogues.test_writes_when_rogues_present`. FR-002, FR-007. Status: absent.
  - Files: `tests/unit/export/test_org_client_security_exporter.py` (lines 264-277).
  - Acceptance: The call passes the endpoint name as a keyword. The writer receives `listSiteRogueAPs`. The info log names `listSiteRogueAPs`.
  - Verify: `python -m pytest tests/unit/export/test_org_client_security_exporter.py -q -k writes_when_rogues_present` (TST-07)

- [ ] T013 [US2] Update `TestExportRogues.test_empty_rogues_logs_only` to the four-argument call. FR-002. Status: absent.
  - Files: `tests/unit/export/test_org_client_security_exporter.py` (lines 279-283).
  - Acceptance: The empty call still writes nothing.
  - Verify: `python -m pytest tests/unit/export/test_org_client_security_exporter.py -q -k empty_rogues_logs_only` (TST-08)

- [ ] T014 [US2] Assert zero export writer calls in both cache-hit tests. FR-008. Status: absent.
  - Files: `tests/unit/export/test_org_client_security_exporter.py` (lines 292-298 and 325-331).
  - Acceptance: Each cache-hit test asserts that `fake_mh.DataExporter.write_with_format_selection` is not called.
  - Verify: `python -m pytest tests/unit/export/test_org_client_security_exporter.py -q -k cache_hit` (TST-02 and TST-06)

**Checkpoint**: User Story 2 passes its tests, and the AP behavior is unchanged.

## Phase 5: User Story 4 - SDK documentation and release note (Priority: P3)

**Goal**: The SDK page names the installed module. The changelog holds one fragment.

- [ ] T016 [P] [US4] Correct the SDK page. FR-010. Status: absent.
  - Files: `documentation/api/sites/GET_sites_site_id_insights_rogues_clients.md` (lines 136 and 153).
  - Acceptance: Line 136 names `mistapi.api.v1.sites.insights.listSiteRogueClients()`. Line 153 names menu 29 and `OrgClientSecurityExporter.rogue_clients`.
  - Verify: CHK-02

- [ ] T017 [P] Add the changelog fragment. FR-011. Status: absent.
  - Files: `changelog.d/issue-4732-rogue-client-endpoint.md`.
  - Acceptance: One `###` heading. One **Fixed** bullet names issue #4732. The bullet holds the Caution about existing SQLite tables.
  - Verify: CHK-03

## Phase 6: Scope and follow-up issues

- [ ] T018 Confirm the file scope. FR-006, FR-012. Status: open.
  - Files: none.
  - Acceptance: Only the four Phase 1 paths and the record folder appear in the diff.
  - Verify: CHK-01

- [ ] T019 File the Phase 2 issue and the menu 24 issue. FR-013. Status: open.
  - Files: `specs/numbered/0/0/1/2/2/4/1/2/4732-rogue-client-endpoint/tasks.md` (the new issue numbers are written into the pull request body, not into this file).
  - Acceptance: Two new issue numbers exist. Each number appears in the pull request body. The Phase 2 issue lists FR-014 to FR-017.
  - Verify: `gh issue view <number> -R jmorrison-juniper/MistHelper --json title,state`

## Phase 7: Delivery

- [ ] T-LOCAL-GATES Run each applicable local gate on the changed files. FR-001 to FR-012. Status: open.
  - Files: `src/operations/exporting/export/org_client_security_exporter.py`, `tests/unit/export/test_org_client_security_exporter.py`, `documentation/api/sites/GET_sites_site_id_insights_rogues_clients.md`, `changelog.d/issue-4732-rogue-client-endpoint.md`, and the record Markdown files under `specs/numbered/0/0/1/2/2/4/1/2/4732-rogue-client-endpoint/`.
  - Acceptance: Each applicable gate in `design/quickstart.md` reports its expected result. Record each result for the pull request body.
  - Verify: the commands in `design/quickstart.md`.

- [ ] T-PR Commit, push, and open the pull request. FR-013. Status: open. Gated by the publication hold and D-10.
  - Files: `src/operations/exporting/export/org_client_security_exporter.py`, `tests/unit/export/test_org_client_security_exporter.py`, `documentation/api/sites/GET_sites_site_id_insights_rogues_clients.md`, `changelog.d/issue-4732-rogue-client-endpoint.md`, and the record folder `specs/numbered/0/0/1/2/2/4/1/2/4732-rogue-client-endpoint/`.
  - Acceptance: The subject is `fix(export): send the client endpoint name for rogue clients`. The body holds the closing line from D-10, the follow-up issue numbers, the Caution, the gate results, and a files summary. The commit carries the Co-authored-by trailer.
  - Verify: `gh pr view <number> -R jmorrison-juniper/MistHelper --json title,body`

- [ ] T-REMOTE-CI Watch CI until every required check passes. SC-006. Status: open.
  - Files: `src/operations/exporting/export/org_client_security_exporter.py`, `tests/unit/export/test_org_client_security_exporter.py`, `documentation/api/sites/GET_sites_site_id_insights_rogues_clients.md`, and `changelog.d/issue-4732-rogue-client-endpoint.md` (the pull request diff).
  - Acceptance: Every required check passes on the latest commit, including CodeQL. Do not push during an in-flight run unless the push replaces that commit.
  - Verify: `gh pr checks <number> -R jmorrison-juniper/MistHelper --watch`

- [ ] T-MERGE Add `auto-merge` and merge in the serial slot. SC-006, FR-012. Status: open. Gated by green CI and orchestrator approval.
  - Files: `src/operations/exporting/export/org_client_security_exporter.py`, `tests/unit/export/test_org_client_security_exporter.py`, `documentation/api/sites/GET_sites_site_id_insights_rogues_clients.md`, and `changelog.d/issue-4732-rogue-client-endpoint.md` (the merged diff).
  - Acceptance: The merge is a squash merge. The branch and worktree are removed. `main` contains the squash commit.
  - Verify: `gh pr view <number> -R jmorrison-juniper/MistHelper --json state,mergedAt`

## Phase 8: Phase 2 repair (HOLD)

**Purpose**: Repair existing SQLite tables and ArangoDB documents. Do not start these tasks until the decisions and coordination finish.

- [ ] T-HOLD-DECIDE HUMAN-DECISION-REQUIRED: Record decisions D-3, D-4, and D-10 on the issue. FR-014, FR-015, FR-017. SC-008. Status: open.
  - Files: `specs/numbered/0/0/1/2/2/4/1/2/4732-rogue-client-endpoint/design/research.md` (decisions D-3, D-4, and D-10).
  - Acceptance: The issue holds one comment per decision, with the chosen option and the approver.
  - Verify: CHK-05

- [ ] T-HOLD-COORD Coordinate with the owners of #4723, #4724, #4725, and #4726. FR-014, FR-016. SC-008. Status: open.
  - Files: `src/foundation/support/refactors/sqlite_database_writer.py`, `src/foundation/persistence/db/database_schema_utils.py`, and `src/foundation/persistence/db/writers/arango_writer.py` (shared-writer files that wait for this coordination).
  - Acceptance: Each owner confirms the shared-writer change before any shared-writer file changes.
  - Verify: CHK-05

- [ ] T-P2-SQLITE Stop the SQLite write on a primary key mismatch. FR-014. Status: absent. HOLD.
  - Files: `src/foundation/support/refactors/sqlite_database_writer.py` (lines 284-290 and 305-318).
  - Acceptance: The writer reads the existing primary key before the insert. A mismatch stops the write and reports both keys.
  - Verify: TST-12 in `tests/unit/export/test_rogue_primary_key_repair.py`

- [ ] T-P2-REPORT Add the read-only candidate-key report and the backup step. FR-015. Status: absent. HOLD.
  - Files: `tests/unit/export/test_rogue_primary_key_repair.py` and `documentation/operator-guide.md` (line 752 region).
  - Acceptance: The report lists missing and duplicate candidate keys and changes no row. The backup step is documented.
  - Verify: TST-13 in `tests/unit/export/test_rogue_primary_key_repair.py`

- [ ] T-P2-ARANGO Use a composite vertex key for rogue clients. FR-016. Status: absent. HOLD.
  - Files: `src/foundation/persistence/db/writers/arango_writer.py` (lines 1844-1846).
  - Acceptance: The rogue client vertex key holds `client_mac` and `bssid`.
  - Verify: TST-14 in `tests/unit/export/test_rogue_primary_key_repair.py`

- [ ] T-P2-CLEANUP Remove or rewrite stale AP-keyed rows only with an approved plan. FR-017. Status: open. HOLD and HUMAN approval (D-4).
  - Files: `data/mist_data.db` and the ArangoDB and Redis volumes that `.github/copilot-instructions.md` names. No repository file changes in this task.
  - Acceptance: The approved plan names each row set and a backup. An operator runs it outside this record.
  - Verify: CHK-05

Warning: `INSERT OR REPLACE` removes an existing row that has the same key. Do not rebuild a table before D-3 approval.

## Dependencies and Execution Order

- T001 runs first. T002 and T003 run in parallel after T001.
- T010 runs before T003 verification and before T004. TST-09 and TST-10 must pass before any code change.
- T004 runs before T005 and T006. T007 to T014 update tests after T004 to T006.
- T015 runs at any time. It reads only.
- T016 and T017 run in parallel with the code tasks, because they touch other files.
- T018 runs after all code and documentation tasks. T019 runs before `T-PR`.
- `T-LOCAL-GATES` runs after T018. `T-PR` runs after `T-LOCAL-GATES` and the release of the publication hold.
- `T-REMOTE-CI` runs after `T-PR`. `T-MERGE` runs after `T-REMOTE-CI` and approval.
- Phase 8 starts after `T-HOLD-DECIDE` and `T-HOLD-COORD`. Run the `T-P2-*` tasks in this order: SQLITE, REPORT, ARANGO, then CLEANUP.

## Checks

Process tasks use GitHub CLI or git commands. The local gates table covers code gates only. The checks below name the command for each process task.

- **CHK-01 Scope and overlap**: Run `git diff --name-only origin/main`. Expect only Phase 1 paths and the record folder. Run `gh pr list -R jmorrison-juniper/MistHelper --state open --json number,headRefName,files` and compare the paths.
- **CHK-02 Documentation**: Run `ste-linter --config .ste-linter.toml --min-score 80 documentation/api/sites/GET_sites_site_id_insights_rogues_clients.md`. Run `markdown-link-check documentation/api/sites/GET_sites_site_id_insights_rogues_clients.md`.
- **CHK-03 Changelog**: Run `python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q`.
- **CHK-04 Pull request body**: Run `gh pr view <number> -R jmorrison-juniper/MistHelper --json body`. The body holds the closing line, the follow-up numbers, and the Caution.
- **CHK-05 Human approval**: Confirm a decision comment from the approver exists on issue #4732 for D-3, D-4, and D-10 before any Phase 8 task starts.

## Test Index

| ID | Test function | Task | Requirement | Phase |
| - | - | - | - | - |
| TST-01 | `TestRogueClients::test_normal_flow_exports` (changed) | T007 | FR-001 | 1 |
| TST-02 | `TestRogueClients::test_cache_hit_short_circuits` (changed) | T014 | FR-008 | 1 |
| TST-03 | `TestRogueClients::test_writes_client_endpoint_name` (new) | T008 | FR-001 | 1 |
| TST-04 | `TestRogueClients::test_fetches_client_endpoint` (new) | T009 | FR-004 | 1 |
| TST-05 | `TestRogueAps::test_normal_flow_exports` (changed) | T011 | FR-002 | 1 |
| TST-06 | `TestRogueAps::test_cache_hit_short_circuits` (changed) | T014 | FR-008 | 1 |
| TST-07 | `TestExportRogues::test_writes_when_rogues_present` (changed) | T012 | FR-002, FR-007 | 1 |
| TST-08 | `TestExportRogues::test_empty_rogues_logs_only` (changed) | T013 | FR-002 | 1 |
| TST-09 | `TestRogueEndpointPrimaryKeys::test_client_endpoint_primary_key_is_client_and_bssid` (new) | T010 | FR-005 | 1 |
| TST-10 | `TestRogueEndpointPrimaryKeys::test_ap_endpoint_primary_key_is_bssid_and_ap_mac` (new) | T010 | FR-005 | 1 |
| TST-11 | `TestLoadSiteList::test_success` (unchanged guard) | T015 | FR-009 | 1 |
| TST-12 | `test_existing_table_with_other_primary_key_stops_before_insert` (new) | T-P2-SQLITE | FR-014 | 2 |
| TST-13 | `test_candidate_key_report_is_read_only` (new) | T-P2-REPORT | FR-015 | 2 |
| TST-14 | `test_arango_rogue_client_key_includes_bssid` (new) | T-P2-ARANGO | FR-016 | 2 |

The count of new or changed test functions is 13. Ten belong to Phase 1, and three belong to Phase 2.
