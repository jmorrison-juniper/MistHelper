# Research: SQLite Device Event Identity

## Findings

- The defect is on main. The strategy entry for `searchOrgDeviceEvents` lists `id`, `device_id`, and `timestamp` (R5). The writer keeps only the key columns that exist in the batch (R8). For the documented shape, the key becomes `timestamp` (R8 and R73).
- The writer counts a replacing insert as a success (R10 and R11). The batch returns True when one insert succeeds (R12). The count check logs the table total and does not compare it with the batch (R13).
- Three menus write this key into SQLite: menu 97 (R21), menu 21 (R26), and menu 153 (R30 and R32). Menus 21 and 153 do not stop on a False result.
- Main is 88 commits ahead of `3964d21` and has no commit behind it (S-7). The strategy entry is unchanged since `3964d21` (R6). The menu 97 exporter changed through merged pull request #4834 (R25).
- No record exists for issue 4723 locally or on main (R3 and R4). No pull request references issue 4723 (S-2).
- The issue names `DataProcessingUtils`. The class flattens rows and returns the union of keys that the writer uses for columns (R84, lines 66 and 148).

## Decisions

### D-1 Row identity for SQLite device events

- Alternatives: (a) documented key `org_id`, `timestamp`, `type`. (b) Current composite key with present columns only. (c) Content fingerprint with `org_id`. (d) Append-only table without a key.
- Chosen: (c).
- Reason: The documented schema requires only `org_id`, `timestamp`, and `type` (R72 and R73). Option (a) still collides when two events share a type and a timestamp. Option (b) is the defect (R8 and R10). Option (d) duplicates each rerun and breaks FR-006 and the rule in R43.
- Risk: Identical stored values merge into one row. A new Mist field changes the fingerprint, so one rerun can add a row for an older event.
- Human decision: false.

### D-2 Scope of the identity contract

- Alternatives: (a) every SQLite write for `searchOrgDeviceEvents`. (b) Menu 97 only. (c) Every endpoint that uses a composite key.
- Chosen: (a).
- Reason: One key feeds menus 97, 21, and 153 (R21, R26, R30, R32). The table names come from the filename, and the `.csv` suffix is dropped (R20). Menu 21 writes `OrgDeviceEvents`, and menu 153 writes `OrgDeviceevents`. SQLite treats both names as one table (S-6). Option (b) leaves menus 21 and 153 with the defect. Option (c) widens the change to endpoints that the issue does not report.
- Risk: The migration covers two tables. Menu 153 still reports success after a False result (D-9).
- Human decision: false.

### D-3 Shared strategy entry and the Redis and ArangoDB keys

- Alternatives: (a) keep the catalog entry and branch in the SQLite writer. (b) Change the catalog entry to a fingerprint key. (c) Add a per-backend override in the router.
- Chosen: (a).
- Reason: The data exporter passes the catalog to the polyglot router (S-13). Issues #4724 and #4725 own the Redis and ArangoDB keys (S-1). Option (b) changes two backends without their owners. Option (c) creates two sources for one endpoint.
- Risk: The SQLite key and the polyglot key differ until #4724 and #4725 decide. The strategy catalog keeps a description that claims uniqueness (R5, line 270).
- Human decision: false.

### D-4 File placement

- Alternatives: (a) new package `src/foundation/persistence/device_events/`. (b) `src/foundation/persistence/db/`. (c) `scripts/`. (d) `src/foundation/persistence/db/writers/`.
- Chosen: (a).
- Reason: Constitution Principle I forbids a new child in a noncompliant folder (R49). Option (b) already has six children (R67). Option (c) has 53 children (R69). Option (d) is not a writer folder. `src/foundation/persistence/` has three children (R66), so one package fits.
- Risk: The migration is a module run with `python -m`, not a script in `scripts/`.
- Human decision: false.

### D-5 Write verification

- Alternatives: (a) transactional presence check for each submitted key after `INSERT OR IGNORE`. (b) Count of changed rows only. (c) Row count before and after the batch.
- Chosen: (a).
- Reason: REPLACE deletes the older row and does not change the change counter (S-5). Option (b) counts inserts, not stored keys. Option (c) cannot separate a new row from a replaced row. The presence check proves that each submitted key is stored before COMMIT.
- Risk: One extra SELECT for each batch. Chunks of 500 keys keep the statement within the SQLite variable limit.
- Human decision: false.

### D-6 Existing databases

- Alternatives: (a) change the primary key in place. (b) Rebuild the table in one transaction, with a checked backup and a kept legacy table. (c) Drop and recreate the table. (d) Write to a new table name.
- Chosen: (b).
- Reason: The rebuild is the standard method for a primary key change in SQLite (U-6). Option (c) destroys rows. Option (d) splits the store, and each reader then needs two names.
- Risk: The migration needs free disk space for the backup and the new table. Rows that the old key overwrote stay lost (Warning in the spec).
- Human decision: false.

### D-7 Writes into a legacy table

- Alternatives: (a) refuse the write and change no row. (b) Keep writing into the legacy table. (c) Migrate on the first write.
- Chosen: (a).
- Reason: Option (b) keeps overwriting rows (R10 and R11). Option (c) runs a destructive change without an operator (constitution Principle III, R51).
- Risk: Operators who skip the migration get no new rows. Menu 97 stops with its existing error. Menu 21 logs an error (D-9).
- Human decision: false.

### D-8 Migration entry point

- Alternatives: (a) module run by an operator with a dry run by default and the typed word `MIGRATE`. (b) Run at application start. (c) A new menu.
- Chosen: (a).
- Reason: Option (b) starts a destructive change with no review. Option (c) renumbers menus and changes `MistHelper.py`, which is a hot file (R28 and R83). The precedent script `scripts/migrate_sqlite_to_polyglot.py` uses a dry-run flag (R76).
- Risk: Operators can skip the migration. D-7 covers that case.
- Human decision: false.

### D-9 Result handling for menus 21 and 153

- Alternatives: (a) menu 21 checks the result for non-empty batches. Menu 153 moves to a follow-up issue. (b) Change the shared fetcher for every export now. (c) Change no caller.
- Chosen: (a).
- Reason: Menu 21 ignores the write result (R26). Menu 153 uses `APIDataFetcher`, which every export uses (R32). A change in the fetcher widens scope to all exports.
- Risk: Menu 153 can print a success line after a refused or failed write. Caution: the error line in the log is the only signal. A follow-up issue must own this gap.
- Human decision: false.

### D-10 Legacy table and backup retention

- Alternatives: (a) keep legacy tables and backup files. (b) Delete them after a verified migration.
- Chosen: (a).
- Reason: Deletion destroys the only copy of the old rows (FR-015). Keeping them costs disk space.
- Risk: Disk use grows until a person removes the files.
- Human decision: true. HUMAN-DECISION-REQUIRED. Recommended option: keep both until a person reviews the dry run report and approves deletion.

### D-11 Production migration run

- Alternatives: (a) an operator runs the migration once, after a dry run and a test run on a copy, with approval. (b) The migration runs during deployment. (c) The migration never runs, and the writer keeps refusing.
- Chosen: (a).
- Reason: The migration rebuilds production data. Option (b) skips review. Option (c) blocks every device event export on a legacy table.
- Risk: A failed rebuild needs the backup restore in the plan.
- Human decision: true. HUMAN-DECISION-REQUIRED. Recommended option: approve the production run only after the dry run and the copy test both pass.

### D-12 Constitution natural-key rule

- Alternatives: (a) accept the fingerprint key as a recorded exception. (b) Key on every documented field. (c) Amend the constitution.
- Chosen: (a).
- Reason: No documented field identifies an event (R72 and R73). Option (b) uses fields that the live API can omit. Option (c) changes a repository-wide rule and is outside this issue.
- Risk: A reviewer can reject the exception. The plan records it in Complexity Tracking.
- Human decision: false.

### D-13 Fingerprint method

- Alternatives: (a) SHA-256 over canonical JSON of the non-empty stored values. (b) MD5 or SHA-1. (c) A hash of the Python object `repr`.
- Chosen: (a).
- Reason: The repository already builds SLE identities with SHA-256 over canonical JSON (R7, lines 68 to 74). MD5 and SHA-1 can trigger Bandit findings. `repr` output can change between Python versions.
- Risk: A later change to the canonical form needs its own migration.
- Human decision: false.

### D-14 Test placement and fixtures

- Alternatives: (a) two unit test files in `tests/unit/db/`. (b) Integration tests in `tests/integration/`. (c) Tests in a large existing folder.
- Chosen: (a).
- Reason: `tests/unit/db/` has room for two files (R70). Integration tests need a live environment that this record does not use. Unit tests use `tmp_path` and mocked Mist responses.
- Risk: The unit tests do not exercise a live Mist response.
- Human decision: false.

### D-15 Metadata

- Size: L. The change touches more than three files and changes a database schema (R53).
- Labels to add: `in-progress`. No label is removed.
- Related issues: #4721, #4722, #4724, #4725, #4726.
- Dependencies: none. The exporter guard from pull request #4834 is merged (S-4).
- Risk: The merge order with #4724 and #4725 needs coordination.
- Human decision: false.

## Remote Verification

Each row records one check. The count of rows equals `remote_checks` in the status file.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| R1 | Main head commit exists | commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` | main | not applicable (commit) | present | 0 |
| R2 | Reproduction commit exists | commit `3964d21d03f9f5717cb8eafb7272ecff21f5362a` | `3964d21d03f9f5717cb8eafb7272ecff21f5362a` | not applicable (commit) | present | 0 |
| R3 | No record folder for issue 4723 | `specs/numbered/0/0/1/2/2/3/4/3/4723-*` | main | not applicable | absent | 0 |
| R4 | Route parent holds no sibling record | `specs/numbered/0/0/1/2/2/3/4/` | main | not applicable | absent | 0 |
| R5 | Strategy entry for `searchOrgDeviceEvents` | `src/foundation/support/refactors/endpoint_primary_key_strategies.py` | main | 3547991028bdbe955e1ba6c8a6bf3082240f2af8 | present | 265 |
| R6 | Strategy entry identical at reproduction commit | `src/foundation/support/refactors/endpoint_primary_key_strategies.py` | 3964d21d03f9f5717cb8eafb7272ecff21f5362a | fb1fb1329e15af5debb7a4a3c4cda5d1478bdc36 | present | 265 |
| R7 | SLE identity classes with SHA-256 keys | `src/foundation/support/refactors/endpoint_primary_key_strategies.py` | main | 3547991028bdbe955e1ba6c8a6bf3082240f2af8 | present | 36 |
| R8 | Composite key builder keeps only present key columns | `src/foundation/persistence/db/database_schema_utils.py` | main | 5374c1b1ffc90e756e15dd19d2ddc4a859c3a6fc | present | 165 |
| R9 | Writer builds table DDL through the strategy | `src/foundation/support/refactors/sqlite_database_writer.py` | main | 8931ee6b705bb351a45a9b2f8a046fc18ec43ccd | present | 305 |
| R10 | Writer uses INSERT OR REPLACE for composite keys | `src/foundation/support/refactors/sqlite_database_writer.py` | main | 8931ee6b705bb351a45a9b2f8a046fc18ec43ccd | present | 355 |
| R11 | Per-row success counts a replacing insert | `src/foundation/support/refactors/sqlite_database_writer.py` | main | 8931ee6b705bb351a45a9b2f8a046fc18ec43ccd | present | 387 |
| R12 | Batch returns True after one successful insert | `src/foundation/support/refactors/sqlite_database_writer.py` | main | 8931ee6b705bb351a45a9b2f8a046fc18ec43ccd | present | 459 |
| R13 | Count check logs the table total, not batch proof | `src/foundation/support/refactors/sqlite_database_writer.py` | main | 8931ee6b705bb351a45a9b2f8a046fc18ec43ccd | present | 489 |
| R14 | Keyed index precedent for SLE windows | `src/foundation/support/refactors/sqlite_database_writer.py` | main | 8931ee6b705bb351a45a9b2f8a046fc18ec43ccd | present | 292 |
| R15 | Auto-increment fallback clears the table | `src/foundation/support/refactors/sqlite_database_writer.py` | main | 8931ee6b705bb351a45a9b2f8a046fc18ec43ccd | present | 369 |
| R16 | DataExporter writes SQLite and returns the writer result | `src/operations/exporting/export/data_exporter.py` | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 379 |
| R17 | Empty batch returns False | `src/operations/exporting/export/data_exporter.py` | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 354 |
| R18 | Loss warning covers polyglot writes only | `src/operations/exporting/export/data_exporter.py` | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 182 |
| R19 | `export_with_processing` passes the endpoint name | `src/operations/exporting/export/data_exporter.py` | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 490 |
| R20 | SQLite table name drops the csv suffix | `src/operations/exporting/export/data_exporter.py` | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 381 |
| R21 | Menu 97 table and endpoint constants | `src/operations/exporting/export/device_events_52w_exporter.py` | main | 97e574382993ca34d56108d6cbf660d047b74be4 | present | 18 |
| R22 | Menu 97 batch guard raises on False | `src/operations/exporting/export/device_events_52w_exporter.py` | main | 97e574382993ca34d56108d6cbf660d047b74be4 | present | 252 |
| R23 | Menu 97 SQLite completion message | `src/operations/exporting/export/device_events_52w_exporter.py` | main | 97e574382993ca34d56108d6cbf660d047b74be4 | present | 43 |
| R24 | Exporter docstring claims SQLite idempotence | `src/operations/exporting/export/device_events_52w_exporter.py` | main | 97e574382993ca34d56108d6cbf660d047b74be4 | present | 345 |
| R25 | Reproduction-commit exporter had no result check | `src/operations/exporting/export/device_events_52w_exporter.py` | 3964d21d03f9f5717cb8eafb7272ecff21f5362a | db6d6b1092be47feaddd7c8ac70d66e1d0254b7b | stale | 255 |
| R26 | Menu 21 ignores the writer result | `src/operations/exporting/export/org_alarm_event_exporter.py` | main | b46c4b156f1bccac870aa469375c90927bd4f9c9 | present | 140 |
| R27 | Menu 21 registration | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 3699 |
| R28 | Menu 97 registration | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 5227 |
| R29 | Menu 97 category resource_intensive | `src/foundation/support/utils/operation_registry.py` | main | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | present | 178 |
| R30 | Menu 153 device events operation | `src/operations/wan/org_data_collector.py` | main | be4b4a35082c0d796bd2a41aa8228032a8a86afc | present | 312 |
| R31 | Export filename derives from the data type | `src/operations/exporting/export/org_export_utils.py` | main | cfe85d09447ec3be6271f2a4cb8e5ea2dac5fb81 | present | 64 |
| R32 | Shared fetcher passes the endpoint name and logs success | `src/mist/access/api/api_data_fetcher.py` | main | 0dc12650d21839b664f53a0ea9bb7ac427b3a709 | present | 105 |
| R33 | Arango graph map keys on field `id` | `src/foundation/persistence/db/writers/arango_writer.py` | main | 3db01f97a21de021213bb4d8a8f7300b530cc82a | present | 1487 |
| R34 | Safe input helper class and method | `src/foundation/support/utils/input_utils.py` | main | 960c6ba244134982ec892df3a45232a157a2a853 | present | 34 |
| R35 | Test keeps partial composite key behavior | `tests/unit/db/test_database_schema_utils.py` | main | 5b6fa81817179472ff7ef448d813355c304cf3db | present | 190 |
| R36 | Test for three SQLite rows | `tests/unit/prod_readiness/standalone/operations/exporting/reports/test_exports.py` | main | a6da81f5622bccde7f3b09b02fcc6071d36ffdb0 | present | 57 |
| R37 | Writer verification logging test | `tests/unit/config/foundation/persistence/storage/db/test_sqlite_database_writer_logging.py` | main | 1187733345339971518dd7636ee86700251044fd | present | 47 |
| R38 | Menu 21 test class | `tests/unit/export/test_org_alarm_event_exporter.py` | main | c58874f36e18371499c1f84998edff556eda5894 | present | 148 |
| R39 | Upsert integration test | `tests/integration/test_menu_12_sqlite_upsert.py` | main | dddc6ff274da362797e5a3ddcffb43d056d38401 | present | 22 |
| R40 | Composite key integration test | `tests/integration/test_menu_13_sqlite_upsert.py` | main | 97ffaf3958457f2470b80ea65b44082fc5386afa | present | 95 |
| R41 | Strategy diagram row for the endpoint | `documentation/diagrams/core/database-strategy.md` | main | 90a5e03e789ce27de79ce2ac208c2cf727c8919f | present | 137 |
| R42 | Operator guide SQLite output row | `documentation/operator-guide.md` | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 752 |
| R43 | Instruction file primary key sentence | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 208 |
| R44 | Instruction file language and platform rules | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 8 |
| R45 | Instruction file local gates table | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| R46 | README paragraph anchor after line 18 | `README.md` | main | 331a4567f72156fe2a3e3ee91005d2cbbcaed6d0 | present | 18 |
| R47 | Changelog file naming rule | `changelog.d/README.md` | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 19 |
| R48 | Changelog precedent from merged pull request #4834 | `changelog.d/issue-4722-export-writes.md` | main | b5107fd476dddf383504d4ac9f8168be80e752af | present | 0 |
| R49 | Constitution five-item rule | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| R50 | Constitution database keys rule | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 322 |
| R51 | Constitution typed confirmation rule | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 113 |
| R52 | Constitution inline comment and action logging rules | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 204 |
| R53 | Constitution SpecKit escalation rule | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 420 |
| R54 | Agent instruction file writing rules | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 0 |
| R55 | Spec template headings | `.specify/templates/spec-template.md` | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 0 |
| R56 | Plan template headings | `.specify/templates/plan-template.md` | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 0 |
| R57 | Tasks template headings | `.specify/templates/tasks-template.md` | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 0 |
| R58 | Checklist template headings | `.specify/templates/checklist-template.md` | main | 806657da09d1058823923e346a323b633114971a | present | 0 |
| R59 | Route function and base 5 | `.specify/scripts/powershell/spec-route.ps1` | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 4 |
| R60 | Reference record spec shape | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md` | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| R61 | Reference record plan shape | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/plan.md` | main | 686c89f85ee7c094526bafaf782d4398f6c523ff | present | 0 |
| R62 | Reference record tasks shape | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/tasks.md` | main | 72bd85483706269fdf809322b2dca38a0e1d5698 | present | 0 |
| R63 | Reference record analysis shape | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/analysis.md` | main | b5db89b9d0d0a4f8e725ad8e0e746c34fa1a24e7 | present | 0 |
| R64 | Reference record research shape | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/design/research.md` | main | 2e4aaa714e56fff7f96a2af9e686e9f5c06224a7 | present | 0 |
| R65 | Reference record checklist shape | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/design/checklists/requirements.md` | main | 4a53b89939bb523902efeaaffd1d7b12221c717b | present | 0 |
| R66 | Folder children: `src/foundation/persistence` (3) | `src/foundation/persistence` | main | 72079a350aec479ed002db55d43bd9fc03c77fd5 | present | 0 |
| R67 | Folder children: `src/foundation/persistence/db` (6) | `src/foundation/persistence/db` | main | 9b43737e18dedb66b53b2b2cf95a7c0b1f4b7730 | present | 0 |
| R68 | Folder children: `src/foundation/support/refactors` (33) | `src/foundation/support/refactors` | main | f84f2ce1bc5c0085873725fac9a4fe07df261d65 | present | 0 |
| R69 | Folder children: `scripts` (53) | `scripts` | main | e773ca4fb588b3b46bb86346ea9f4c9802ee97fe | present | 0 |
| R70 | Folder children: `tests/unit/db` (2) | `tests/unit/db` | main | 06b95d6a9d6822c509e6e11d7ac75c272907e82f | present | 0 |
| R71 | Mist search operation and path | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 8667 |
| R72 | Mist `device_event` schema is closed | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 76341 |
| R73 | Mist `device_event` required fields | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 76455 |
| R74 | SDK search function, local installed file | `.venv\Lib\site-packages\mistapi\api\v1\orgs\devices.py` | mistapi 0.64.1 (local) | not applicable (installed file) | present | 259 |
| R75 | Database path constant | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 2541 |
| R76 | Migration precedent usage text | `scripts/migrate_sqlite_to_polyglot.py` | main | c8e22bc74d0d0fbf87220bbfb3da106e65ff5fc1 | present | 8 |
| R77 | Guardrail baseline file exists | `tests/guardrails/process_folder_baseline.json` | main | f3eb8a7b6c62f3154ac6fa867a8948504818798b | present | 0 |
| R78 | Writer converts each value to a string and stores None as empty | `src/foundation/support/refactors/sqlite_database_writer.py` | main | 8931ee6b705bb351a45a9b2f8a046fc18ec43ccd | present | 437 |
| R79 | CI path variables for type, lint, and docstring gates | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| R80 | Index names follow the `idx_<table>_<column>` rule | `src/foundation/persistence/db/database_schema_utils.py` | main | 5374c1b1ffc90e756e15dd19d2ddc4a859c3a6fc | present | 215 |
| R81 | Column names replace characters outside `[A-Za-z0-9_]` | `src/foundation/persistence/db/database_schema_utils.py` | main | 5374c1b1ffc90e756e15dd19d2ddc4a859c3a6fc | present | 114 |
| R82 | Writer adds each missing source column with ALTER TABLE | `src/foundation/support/refactors/sqlite_database_writer.py` | main | 8931ee6b705bb351a45a9b2f8a046fc18ec43ccd | present | 319 |
| R83 | Hot file rule for `MistHelper.py` | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 293 |
| R84 | Data-processing utility class with flatten and key helpers | `src/foundation/models/data/data_processing_utils.py` | main | f0e53336717eefbbe0bf7b4136b3e0d4f11f3847 | present | 27 |

Notes on the table:

- R3 and R4 use the remote tree query. The query matched no path that contains `4723` and no sibling path under `specs/numbered/0/0/1/2/2/3/4/`.
- R25 uses the blob at the reproduction commit. The blob calls the writer at lines 255 and 275 and has no result check.
- R74 is local. The file is part of the installed wheel, not a repository path. Its version matches the pin `mistapi>=0.64.0,<0.65`.
- R71 to R73 read the local copy of the OpenAPI file. The local blob equals the remote blob (S-8).
- Rows R54 to R65 use headings or whole files. No body line is cited for those rows.

## Sources

- S-1: GitHub issue #4723 body and comments, read with `gh issue view` (read-only) on 2026-11-26. The comments name issues #4721, #4722, #4724, #4725, and #4726, and they require shared-file handoff before an edit.
- S-2: `gh pr list --search 4723` returned an empty list on 2026-11-26.
- S-3: Open pull request #4813 changes `src/operations/exporting/export/data_exporter.py` and `tests/unit/export/test_data_exporter.py`.
- S-4: Merged pull request #4834 changes `changelog.d/issue-4722-export-writes.md`, `device_events_52w_exporter.py`, and `tests/unit/test_device_events_52w_exporter_extended.py`. Its body says `Refs #4721` and `Refs #4722`.
- S-5: SQLite documentation, https://www.sqlite.org/lang_conflict.html, fetched 2026-11-26. It states that IGNORE skips the row with the violation and returns no error. It states that REPLACE deletes the older row and does not increment the change counter.
- S-6: SQLite documentation, https://www.sqlite.org/lang_naming.html, fetched 2026-11-26. It states that schema names are case-insensitive, like other SQL identifiers.
- S-7: Git compare API for base `3964d21` and head `main` returned `ahead_by` 88 and `behind_by` 0. Blob IDs of the two commits differ for six watched files, and the strategy entry is the same at both.
- S-8: Local `git rev-parse HEAD` returned `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, which equals the main head. `git ls-tree HEAD` returned the same blob IDs as the remote tree for the files cited in this record.
- S-9: Local installed package `mistapi` version 0.64.1, from its dist-info folder.
- S-10: Reference record folder `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv`. Its headings set the shape of the record.
- S-11: Validation script in the meta folder. It was read and not run.
- S-12: Instruction files read in full: `AGENTS.md`, `.github/copilot-instructions.md`, and `.specify/memory/constitution.md`.
- S-13: `src/operations/exporting/export/data_exporter.py` lines 115 to 117 pass `ENDPOINT_PRIMARY_KEY_STRATEGIES` to the polyglot router (remote decode, blob f45fc71).
- S-14: Local documentation and templates use the same blob IDs as main (S-8). Their line numbers match the local copy.

## Unverified

- U-1: Live Mist responses can contain `id` or `device_id`. Reason: no API call was made. Only the documented schema was read (R72 and R73).
- U-2: The content of production `data/mist_data.db`. Reason: the rules forbid opening or changing production data. Decision D-11 covers the production run.
- U-3: Other repositories or tools that read `OrgDeviceEvents` and expect the old key. Reason: the search covered this repository only.
- U-4: Runtime behavior on the operator's installed SQLite version. Reason: no test ran. The SQLite documents in S-5 and S-6 describe the behavior.
- U-5: Row loss in the other composite endpoints, such as `searchSiteDeviceEvents` (`endpoint_primary_key_strategies.py` lines 513 to 519 on main). Reason: not tested.
- U-6: The standard SQLite method for a primary key change. Reason: the SQLite ALTER TABLE page was not fetched in this record. The rebuild path in D-6 follows the common method.
- U-7: Compatibility of `scripts/migrate_sqlite_to_polyglot.py` with an identity table. Reason: the script body was not read beyond lines 1 to 12 and the usage text (R76).
- U-8: Whether menu 153 prints a success line after a False result at runtime. Reason: the source path is read (R32). The runtime path was not run.

## Skills

No skill was loaded. The visible skill list covers Podman, Docker, and Juniper devices. None of the visible skills covers SQLite key design or the Mist API schema. No test in the plan starts a container.

## Pull Request and Branch Inventory

- Open pull requests: seven on 2026-11-26. Only pull request #4813 touches a file that this change names in a different way (S-3). This change does not edit `data_exporter.py`.
- Remote branch named for issue 4723: none found in the pull request list.
- Merged pull request #4834 changed the exporter and the fragment for issues #4721 and #4722 (S-4). Those issues remain open.
