# Research: Rogue client exports use the client endpoint name

This file holds the decisions, the remote verification table, the sources, and the Unverified list. The remote evidence comes from `gh api` on `main`. The `main` head is commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, which equals the local checkout HEAD. For each cited file, the blob SHA on `main` equals the local blob SHA. Local line numbers therefore hold on `main`.

Method note: In this session, the contents request with `?ref=main` returned HTTP 404 for every file, including `AGENTS.md`. The request with `?ref=refs/heads/main` returned the same blob SHA as the tree. Every remote file in this record uses `refs/heads/main`.

## D-1. Endpoint name transport

- **Decision**: Pass the endpoint name to `_export_rogues` as a keyword-only parameter `api_function_name: str`. Each caller states its own name.
- **Alternatives**: (a) Keep the literal and choose the name from the label text. (b) Read the name from the collector callable at run time. (c) Pass a configuration object that holds the label, the file name, and the endpoint name.
- **Chosen**: Option (a) is rejected because the label text is not a stable key. Option (b) is rejected because the test doubles hide the callable name. The keyword parameter keeps the signature at four parameters and needs no new class.
- **Risk**: A future caller can pass the wrong name. TST-01, TST-03, TST-05, TST-07, and TST-08 cover both current callers.
- **Human decision**: Not required.

## D-2. Phasing of the fix

- **Decision**: Phase 1 changes the route and the tests now. Phase 2 repairs existing tables after decisions D-3, D-4, and D-10 and the coordination in `T-HOLD-COORD`.
- **Alternatives**: (a) One change that changes the route and repairs the tables. (b) Change the route and close the issue. (c) Defer all work until Phase 2 is ready.
- **Chosen**: Option (a) conflicts with the shared-writer hold and with the unverified migration rule in issue comment 3. Option (b) hides the existing-table limit that comment 3 describes. Option (c) keeps the defect for new tables.
- **Risk**: An operator with an existing table sees no change until Phase 2 ships. The changelog Caution and the PR body state this limit (FR-013).
- **Human decision**: Not required for the phasing. D-10 decides the closing scope.

## D-3. Repair policy for existing SQLite tables

HUMAN-DECISION-REQUIRED

- **Decision**: The recommended option stops the SQLite write before any insert when a key differs. The write reports both keys. No stored row changes. A new table is created only after an operator approves a naming plan.
- **Alternatives**: (a) Stop the write and report both keys. (b) Create a new table with the client key and keep the old table. (c) Rebuild the table in place with `INSERT OR REPLACE`.
- **Chosen**: Option (a) is recommended. Option (c) is rejected. Warning: `INSERT OR REPLACE` removes the existing row that has the same key. Issue comment 3 gives the same warning. Option (b) is valid, but it changes the table name that operators read. That change is visible to users, so a human must approve it.
- **Risk**: Option (a) blocks new client rows in an affected table until a repair ships. The stopped write reports the failure, so the failure is not silent. No stored row changes.
- **Human decision**: Required. Every option affects production data.

## D-4. Stale AP-keyed rows in ArangoDB and Redis

HUMAN-DECISION-REQUIRED

- **Decision**: The recommended option keeps the rows. No task in this record deletes or rewrites them.
- **Alternatives**: (a) Keep the rows and add a read-only report. (b) Delete the affected documents. (c) Rewrite the affected documents from stored data.
- **Chosen**: Option (a) is recommended. The lookback window is 168 hours in normal mode (`org_client_security_exporter.py:81`). The Mist API returns no older observation, so an earlier replaced document cannot return through a later run. Warning: Options (b) and (c) cannot undo a mistake without a backup.
- **Risk**: Stale documents stay in graph queries until an approved plan changes them.
- **Human decision**: Required. Deletion or rewrite changes production data.

## D-5. Cache-hit assertions

- **Decision**: Both cache-hit tests assert that the export writer receives no call.
- **Alternatives**: (a) Keep the collector-only assertions. (b) Add a call counter to production code.
- **Chosen**: Option (a) cannot detect a write. Option (b) changes production code only for a test. Issue comment 1 shows that an assertion on the writer rejects an injected write at the intended point.
- **Risk**: None beyond test maintenance.
- **Human decision**: Not required.

## D-6. Placement of the Phase 1 tests

- **Decision**: Keep the Phase 1 tests in the reserved file `tests/unit/export/test_org_client_security_exporter.py`, including the two DDL identity tests.
- **Alternatives**: (a) Add the DDL tests to `tests/unit/db/test_database_schema_utils.py`. (b) Add a new test file.
- **Chosen**: Comment 2 reserves only the exporter test file. The database test file lies on a shared database path that the #4723 to #4726 coordination covers. A new file adds an extra child to `tests/unit/export/`.
- **Risk**: The reserved file grows. The growth comes only from the tests in T007 to T014.
- **Human decision**: Not required.

## D-7. Changelog fragment name

- **Decision**: Name the fragment `changelog.d/issue-4732-rogue-client-endpoint.md`.
- **Alternatives**: (a) `pr-<number>.md`. (b) `<YYYY-MM-DD>-<slug>.md`.
- **Chosen**: No pull request exists yet, so `changelog.d/README.md:27` requires the issue form. The README also says to keep the first name after the pull request opens (`changelog.d/README.md:32`). Option (a) cannot be used before the pull request exists. Option (b) is not the rule for an issue.
- **Risk**: None known.
- **Human decision**: Not required.

## D-8. SDK documentation correction

- **Decision**: Correct the module path and the MistHelper note on the SDK page.
- **Alternatives**: (a) Leave the page unchanged. (b) Remove the SDK section.
- **Chosen**: The installed mistapi 0.64.1 defines `listSiteRogueClients` at `insights.py:495` (R-36). `rogues.py` defines no such function. `AGENTS.md:336` requires documentation updates in the same change. Option (b) removes correct information.
- **Risk**: None. The change edits two lines of text.
- **Human decision**: Not required.

## D-9. Menu 24 combined export

- **Decision**: File a separate issue for the combined export in `security_events.py` (lines 287 and 293). Do not change it in this record.
- **Alternatives**: (a) Change it in this change. (b) Leave it without a record.
- **Chosen**: `AGENTS.md:185` states that one issue holds one subject. The defect sits in another file and another operation. Option (b) hides a known defect.
- **Risk**: The defect remains until the new issue ships.
- **Human decision**: Not required.

## D-10. Closing scope of issue #4732

HUMAN-DECISION-REQUIRED

- **Decision**: The recommended option keeps `Closes #4732` in the Phase 1 pull request. The new Phase 2 issue from T019 tracks the held scope.
- **Alternatives**: (a) Keep #4732 open until Phase 2 ships and use `Refs #4732`. (b) Close #4732 without a follow-up issue.
- **Chosen**: Option (a) is recommended. `close-linked-issues.yml` closes the issue that a merged pull request names (`.github/copilot-instructions.md:472`). Option (b) would hide the held scope from the queue. The choice sets the product priority, so a human must decide it.
- **Risk**: With option (a), the issue stays open for a longer time.
- **Human decision**: Required. The choice sets the product priority.

## Remote verification

The table holds 55 rows. `STATUS.json` holds the same 55 rows in the same order.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| R-01 | Remote `main` head equals the local checkout HEAD | git/ref/heads/main | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| R-02 | Issue commit 3964d21 exists | commits/3964d21d03f9f5717cb8eafb7272ecff21f5362a | main | 3964d21d03f9f5717cb8eafb7272ecff21f5362a | present | 0 |
| R-03 | Issue test commit 7b7d540 exists | commits/7b7d5406ca7b95a96edf42702ee0049e0c7c2d64 | main | 7b7d5406ca7b95a96edf42702ee0049e0c7c2d64 | present | 0 |
| R-04 | Menu 29 collector uses `listSiteRogueClients` | src/operations/exporting/export/org_client_security_exporter.py | main | 237936c7a612a0d9a5cb6030b94f339dac4ec6fc | present | 88 |
| R-05 | Menu 29 passes the label `rogue clients` to `_export_rogues` | src/operations/exporting/export/org_client_security_exporter.py | main | 237936c7a612a0d9a5cb6030b94f339dac4ec6fc | present | 94 |
| R-06 | `_export_rogues` has no endpoint parameter | src/operations/exporting/export/org_client_security_exporter.py | main | 237936c7a612a0d9a5cb6030b94f339dac4ec6fc | present | 210 |
| R-07 | `_export_rogues` hardcodes `listSiteRogueAPs` for every label | src/operations/exporting/export/org_client_security_exporter.py | main | 237936c7a612a0d9a5cb6030b94f339dac4ec6fc | present | 216 |
| R-08 | The test pins the AP endpoint name for `_export_rogues` | tests/unit/export/test_org_client_security_exporter.py | main | 48db2d8daa56d31364378273b0a0f72a853311d4 | present | 275 |
| R-09 | The test keeps the list-type assertion for the loader | tests/unit/export/test_org_client_security_exporter.py | main | 48db2d8daa56d31364378273b0a0f72a853311d4 | present | 143 |
| R-10 | The client normal-flow test asserts a three-argument call | tests/unit/export/test_org_client_security_exporter.py | main | 48db2d8daa56d31364378273b0a0f72a853311d4 | present | 321 |
| R-11 | The client cache-hit test asserts no export writer call | tests/unit/export/test_org_client_security_exporter.py | main | 48db2d8daa56d31364378273b0a0f72a853311d4 | absent | 298 |
| R-12 | The AP cache-hit test asserts no export writer call | tests/unit/export/test_org_client_security_exporter.py | main | 48db2d8daa56d31364378273b0a0f72a853311d4 | absent | 331 |
| R-13 | The client strategy primary key is `client_mac` and `bssid` | src/foundation/support/refactors/endpoint_primary_key_strategies.py | main | 3547991028bdbe955e1ba6c8a6bf3082240f2af8 | present | 1305 |
| R-14 | The AP strategy primary key is `bssid` and `ap_mac` | src/foundation/support/refactors/endpoint_primary_key_strategies.py | main | 3547991028bdbe955e1ba6c8a6bf3082240f2af8 | present | 1298 |
| R-15 | A configured strategy wins over the derived default | src/foundation/persistence/db/database_schema_utils.py | main | 5374c1b1ffc90e756e15dd19d2ddc4a859c3a6fc | present | 80 |
| R-16 | The composite DDL builder names the primary key columns | src/foundation/persistence/db/database_schema_utils.py | main | 5374c1b1ffc90e756e15dd19d2ddc4a859c3a6fc | present | 172 |
| R-17 | Primary key columns are declared `NOT NULL` | src/foundation/persistence/db/database_schema_utils.py | main | 5374c1b1ffc90e756e15dd19d2ddc4a859c3a6fc | present | 125 |
| R-18 | The DDL uses `CREATE TABLE IF NOT EXISTS` | src/foundation/persistence/db/database_schema_utils.py | main | 5374c1b1ffc90e756e15dd19d2ddc4a859c3a6fc | present | 149 |
| R-19 | The SQLite writer adds columns and keeps the existing primary key | src/foundation/support/refactors/sqlite_database_writer.py | main | 8931ee6b705bb351a45a9b2f8a046fc18ec43ccd | present | 288 |
| R-20 | The SQLite writer uses `INSERT OR REPLACE` for keyed strategies | src/foundation/support/refactors/sqlite_database_writer.py | main | 8931ee6b705bb351a45a9b2f8a046fc18ec43ccd | present | 368 |
| R-21 | The SQLite table name is the file name without `.csv` | src/operations/exporting/export/data_exporter.py | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 381 |
| R-22 | The polyglot write passes the endpoint name to the router | src/operations/exporting/export/data_exporter.py | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 333 |
| R-23 | The export writer signature requires `api_function_name` | src/operations/exporting/export/data_exporter.py | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 156 |
| R-24 | The router selects the strategy by endpoint name | src/foundation/persistence/db/router.py | main | e1a65c5b72ef7b8006e3e6e6775e92ff5bbae7a1 | present | 368 |
| R-25 | The ArangoDB mapping sends `listSiteRogueClients` to `rogue_clients` | src/foundation/persistence/db/writers/arango_writer.py | main | 3db01f97a21de021213bb4d8a8f7300b530cc82a | present | 1120 |
| R-26 | The ArangoDB client vertex key is `client_mac` only | src/foundation/persistence/db/writers/arango_writer.py | main | 3db01f97a21de021213bb4d8a8f7300b530cc82a | present | 1846 |
| R-27 | The menu 29 handler is `OrgClientSecurityExporter.rogue_clients` | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 4051 |
| R-28 | The menu 29 category is `safe` | src/foundation/support/utils/operation_registry.py | main | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | present | 692 |
| R-29 | The menu 24 combined export writes `listSiteRogueClients` for all rows | src/foundation/support/refactors/serial_cc/security_events.py | main | f43ce3aa1fff795da92db6cb3a70fe016c374a60 | present | 293 |
| R-30 | The SDK page names the `rogues` module | documentation/api/sites/GET_sites_site_id_insights_rogues_clients.md | main | 249686f8a0c17018937ad5d8050a6c6e2b758bd1 | stale | 136 |
| R-31 | The SDK page says MistHelper does not use the endpoint | documentation/api/sites/GET_sites_site_id_insights_rogues_clients.md | main | 249686f8a0c17018937ad5d8050a6c6e2b758bd1 | stale | 153 |
| R-32 | The OpenAPI file defines operationId `listSiteRogueClients` | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 32833 |
| R-33 | The OpenAPI `insight_rogue_client` schema requires `client_mac` and `bssid` | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 81858 |
| R-34 | The OpenAPI `insight_rogue_ap` schema requires `bssid` and `ap_mac` | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 81826 |
| R-35 | The OpenAPI `limit` parameter sets no maximum | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 59742 |
| R-36 | The installed mistapi defines `listSiteRogueClients` | .venv\Lib\site-packages\mistapi\api\v1\sites\insights.py | local | 07bebe3875161acd22eb72554e8b7b5033e2bdd7 | present | 495 |
| R-37 | The installed mistapi defines `listSiteRogueAPs` | .venv\Lib\site-packages\mistapi\api\v1\sites\insights.py | local | 07bebe3875161acd22eb72554e8b7b5033e2bdd7 | present | 434 |
| R-38 | The installed mistapi 0.64.1 satisfies the pin | .venv\Lib\site-packages\mistapi-0.64.1.dist-info\METADATA | local | 86b3b7003d569a1311af4085e7e269a52decd795 | present | 3 |
| R-39 | The changelog rule names the issue fragment form | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 27 |
| R-40 | The route uses base 5 | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| R-41 | The `MYPY_PATHS` variable includes `src/` | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| R-42 | The `test_quality_gate` job exists | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 602 |
| R-43 | The changelog guard step runs the guardrail test | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 298 |
| R-44 | The local gates table exists | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| R-45 | The writing style rule exists | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| R-46 | The database keys rule exists | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 322 |
| R-47 | The reference record for shape exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 1 |
| R-48 | No legacy record matches 4732 in the tree | specs (tree search for 4732) | main | none | absent | 0 |
| R-49 | The target route folder is absent | specs/numbered/0/0/1/2/2/4/1/2/ | main | none | absent | 0 |
| R-50 | The route parent holds one child, `4` | specs/numbered/0/0/1/2/2/4/1/ | main | none | present | 0 |
| R-51 | The preservation branch exists on the remote | branches/preservation/2746-pr3011-turn0 | main | none | absent | 0 |
| R-52 | The changelog guard test exists | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 1 |
| R-53 | The STE linter configuration exists | .ste-linter.toml | main | d9f28ef8faf4a4c36a4e967d5b978f96eb306253 | present | 1 |
| R-54 | The process folder baseline exists | tests/guardrails/process_folder_baseline.json | main | f3eb8a7b6c62f3154ac6fa867a8948504818798b | present | 0 |
| R-55 | No open pull request changes a Phase 1 file | open pull requests (Phase 1 files) | main | none | present | 0 |

Notes on the table:

- A `local` ref means the installed file under `.venv`. The `.venv` path is not a repository path.
- A `none` blob SHA means the claim concerns a folder, a branch, a search, or a pull request list.
- R-07 confirms the defect on `main`. It is not a claim that the fix exists.
- R-55 uses `gh pr list --state open --json number,headRefName,files`. Open PR #4813 changes `data_exporter.py`. No open PR changes a Phase 1 path.

## Sources

Repository files (read-only, verified on `main`):

- `src/operations/exporting/export/org_client_security_exporter.py` lines 74-95, 97-117, 158-185, 187-208, 210-224 (menu 29 and 30 exporters, fetch, collect, and export helper).
- `tests/unit/export/test_org_client_security_exporter.py` lines 21-25, 33, 138-143, 263-283, 291-321, 324-355, 358-363 (fixture, tests, and imports).
- `src/foundation/support/refactors/endpoint_primary_key_strategies.py` lines 141 and 1295-1310 (strategy catalog and rogue entries).
- `src/foundation/persistence/db/database_schema_utils.py` lines 69-85, 119-125, 166-172, 188 (strategy lookup and DDL builders).
- `src/foundation/support/refactors/sqlite_database_writer.py` lines 210-240, 284-290, 305-318, 319-332, 355-368 (strategy use, table creation, column addition, and insert mode).
- `src/operations/exporting/export/data_exporter.py` lines 136-150, 153-180, 300-333, 379-386 (dispatch, export writer, polyglot write, and SQLite table naming).
- `src/foundation/persistence/db/router.py` lines 232 and 366-369 (router write and strategy lookup).
- `src/foundation/persistence/db/writers/arango_writer.py` lines 1119-1121 and 1843-1862 (collection mapping and rogue vertex configuration).
- `MistHelper.py` lines 4049-4059 (menu 29 and menu 30 entries).
- `src/foundation/support/utils/operation_registry.py` lines 692-693 (menu categories).
- `src/foundation/support/refactors/serial_cc/security_events.py` lines 48-50, 287, 293, and 318 (combined rogue export, out of scope).
- `documentation/api/sites/GET_sites_site_id_insights_rogues_clients.md` lines 134-153 (SDK page).
- `documentation/mist-api-openapi31yaml.yaml` lines 32801-32833 (rogue operations), 59742-59749 (`limit` parameter), 62798 (`InsightRogueClients` response), 81788-81800 and 81826-81831 (`insight_rogue_ap`), and 81833-81866 (`insight_rogue_client`).
- `documentation/MIST_API_GET_ENDPOINTS.md` lines 1406-1407 (endpoint table for both rogue operations).
- `changelog.d/README.md` lines 27 and 32 (fragment naming).
- `.specify/scripts/powershell/spec-route.ps1` lines 4, 7, 17, and 34 (route calculation).
- `.github/copilot-instructions.md` lines 20, 50-75, 95, 472, 478, 483-489, 501, and 540 (language, gates, test ratchet, workflows, serial merge, PR titles, and pitfalls).
- `AGENTS.md` lines 40, 128, 185, 230, 336, and 345 (writing style, rate limit, issue scope, merge, documentation, and specifications).
- `.specify/memory/constitution.md` lines 38, 91, 113, 143, 182, 204, 235, 274, 278, 312, 322, 326, 361, 398, 453, 459, 476, 487, 496, and 516 (constitution rules).
- `documentation/architecture.md` line 168 and `documentation/operator-guide.md` line 752 (SQLite location in `data/`).

Local evidence without a remote blob check, cited only for reading:

- `src/foundation/persistence/db/writers/redis_writer.py` lines 214 and 566 (Redis key prefix). This file is not in the remote table. See the Unverified list.

Issue and GitHub evidence (fetched with `gh issue view` or `gh pr list`):

- Issue #4732: body and three comments. Comment 1 at https://github.com/jmorrison-juniper/MistHelper/issues/4732#issuecomment-6761030785 (cache-hit control). Comment 2 at https://github.com/jmorrison-juniper/MistHelper/issues/4732#issuecomment-6764337050 (reservation for the test file). Comment 3 at https://github.com/jmorrison-juniper/MistHelper/issues/4732#issuecomment-6769151675 (storage identity evidence and holds).
- Related issues were all open when this record was written. Their last update dates are: #2711 on 2026-11-25, #2746 on 2026-11-17, #4723 and #4724 on 2026-11-09, and #4725 and #4726 on 2026-11-10.
- Linked pull requests for #4732: none (`gh pr list --state all --search 4732` returns an empty list).

Skills: No skill was loaded. The issue concerns Python export code and SQLite and ArangoDB keys. It does not concern Podman or Juniper device behavior.

Web sources: No web page was fetched. Every claim cites a local file or a GitHub record.

## Unverified

- U-A: The preservation branch `preservation/2746-pr3011-turn0` is not in this checkout. `git for-each-ref` shows no such ref. The remote shows none (R-51). The issue says the branch lives on the author's macOS checkout. T002 rechecks it.
- U-B: The live Mist API response to `listSiteRogueClients` with `limit=1000` is not checked. This record makes no live call. The OpenAPI file sets no maximum (R-35).
- U-C: The state of existing `OrgRogueClients` tables in operator databases is not known. No operator database is in scope. Phase 2 starts with a read-only check.
- U-D: The bundled rogue-client and rogue-AP schemas named in issue comment 3 were not found by the repository search. The OpenAPI schemas (R-33 and R-34) stand in for them.
- U-E: The Redis key format for the rogue endpoints is not verified on `main`. The Redis writer was not fetched for the remote table.
- U-F: The line coverage of the test module is not measured. The module docstring claims 100 percent coverage, and this record does not confirm it.
- U-G: The exact command line of `markdown-link-check` is not in the repository instructions. The check uses the tool name with the file path.
- U-H: The behavior of the polyglot write when the database layer is unavailable is read from `data_exporter.py` lines 300-333 only. It was not run.
- U-I: The runtime behavior of the menu 24 combined export is read from source only. It was not run.
- U-J: The number of existing installations with a rogue client table that keeps the AP key is unknown.
