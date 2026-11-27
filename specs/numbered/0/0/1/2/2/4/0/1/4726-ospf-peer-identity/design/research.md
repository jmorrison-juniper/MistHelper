# Research: OSPF Peer Identity Keys

Each decision lists the chosen option, the rejected options, the reason, and the risk. Remote checks use `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` on 2026-11-26. The local working tree matches `main` for every file in the change map. The local blob hashes equal the remote blob SHAs.

## Issue Facts

- **Issue #4726**: State OPEN. Labels `bug` and `MistHelper.py`. Created 2026-11-09T23:32:01Z. Last updated 2026-11-10T13:17:32Z. Author is the repository owner.
- **Requirements from the body**: Menu 225 exports `searchSiteOspfStats`. The declared key `mac`, `peer_ip`, `timestamp` collapses when `peer_ip` is absent. Redis substitutes `unknown`. Each writer reports success. Preserve existing data before any migration. Coordinate with #4723, #4724, and #4725.
- **Reproduction steps from the body**: Eight steps. They load the strategy and writers, write two fixtures with one MAC and one timestamp and two neighbors, add a `peer_ip` record, repeat the Redis write, and run distinct-timestamp and legacy-`peer_ip` controls.
- **Error text from the body**: `SQLite: 2 neighbors supplied, writer returned success, 1 neighbor retained`. `SQLite primary key: mac, timestamp`. `Redis JSON: 2 neighbors supplied, 2 writes reported, 1 document retained`. `Redis JSON key: searchSiteOspfStats:020001c04668:unknown:1700000000`.
- **Comment 2026-11-09T23:36:22Z (owner)**: Shared file ownership. Coordinate with #4723, #4724, and #4725. Obtain each handoff before editing shared files.
- **Comment 2026-11-09T23:39:54Z (owner)**: `searchOrgOspfStats` uses `device_id`, which the schema does not define. Keep the organization mismatch in the same coordination slot.
- **Comment 2026-11-10T13:12:29Z (owner)**: Offline evidence at commit 7b7d540. A key of `mac`, `neighbor`, and `timestamp` loses records that differ only by VRF or port. Redis joins unescaped fields. A missing VRF and the literal `unknown` collide.
- **Comment 2026-11-10T13:17:32Z (owner)**: ArangoDB evidence at commit 7b7d540. Site records use the MAC alone as `_key`. Org records get a new key for each write when `device_id` is absent. The OSPF graph mappings require `id`.
- **Linked work**: `gh pr list --search 4726` with all states returned an empty list on 2026-11-26.
- **Related issues**: #4723 (OPEN, SQLite device events), #4724 (OPEN, Redis device events), and #4725 (OPEN, ArangoDB composite keys for BGP).
- **Cited commits**: 3964d21 (2026-11-09T08:56:50Z) and 7b7d540 (2026-11-10T12:34:48Z). Both exist on the remote (RV-80 and RV-81).

## Decisions

### D-1. Scope boundary

- **Decision**: Change keys for `searchSiteOspfStats` (menus 70 and 225) and `searchOrgOspfStats` (menu 55). Leave the count endpoints, `searchOrgBgpStats`, the device-event keys, and the generic writer functions unchanged.
- **Alternatives**: (a) Change the generic composite key builders for every endpoint. Rejected because #4723, #4724, and #4725 share those builders. (b) Change only the SQLite writer. Rejected because the Redis and ArangoDB legs keep the same defect.
- **Rationale**: The defect has three writer causes. Each cause needs a fix in its own leg. The searchOrgBgpStats entry uses the same tuple (RV-03), so the change must not touch it.
- **Risk**: The OSPF identity class holds knowledge that other endpoints might later need. Mitigation: the class is named for OSPF and its tests pin the boundary (test 15).
- **Human decision**: No.

### D-2. Identity components

- **Decision**: The identity uses `mac`, `vrf_name`, `port_id`, `neighbor`, and `timestamp`.
- **Alternatives**: (a) Keep `mac`, `peer_ip`, and `timestamp`. Rejected because `peer_ip` is deprecated (RV-51) and absent from valid records. (b) Use `mac`, `neighbor`, and `timestamp`. Rejected because the issue reproduces collisions between records that differ only by VRF or port. (c) Use a row number. Rejected because a natural key is required (RV-70, RV-76).
- **Rationale**: An OSPF adjacency belongs to one routing instance and one interface. The local skill states this for interfaces and for routing instances (`juniper-ospf` files `02-interfaces-and-adjacency/01-interface-types.md` and `06-security-instances-and-vpn/03-routing-instances-and-multi-instance.md`). The schema names `vrf_name` (RV-53) and `port_id` (RV-52).
- **Risk**: When the API omits a scope field for some records, one adjacency can appear under two keys. The result is a duplicate, not a loss.

### D-3. Required and scope rules

- **Decision**: Reject the whole batch when a required component is missing or invalid. Encode an absent or empty scope value as JSON null.
- **Alternatives**: (a) Use the text `unknown`. Rejected because it collides with a literal `unknown`, as the issue shows. (b) Skip invalid records and write the rest. Rejected because the operator gets no failure signal. (c) Reject records that lack scope fields. Rejected because the schema permits absence (RV-49).
- **Rationale**: The constitution forbids a success report before a verified durable write (RV-77). A rejected batch keeps the store free of ambiguous keys.
- **Risk**: Caution: A live payload without `neighbor` blocks its batch. The error names the missing component. Unverified item U-01 covers this risk.

### D-4. Neighbor fallback

- **Decision**: Use `neighbor` as the neighbor component. Use `peer_ip` only when `neighbor` is absent or empty.
- **Alternatives**: (a) Require `neighbor` only. Rejected because a payload with only `peer_ip` would fail completely. (b) Prefer `peer_ip`. Rejected because the schema deprecates it (RV-51).
- **Rationale**: The schema names `neighbor` as the replacement (RV-50 and RV-51).
- **Risk**: A batch that mixes both payload shapes can store one adjacency under two keys. A duplicate never replaces another record.

### D-5. Timestamp text

- **Decision**: Write `timestamp` as fixed-point decimal text with trailing zeros removed. Reject a negative value, a boolean, text, or a non-finite value.
- **Alternatives**: (a) Use the Python float text. Rejected because `1700000000` and `1700000000.0` would produce two keys. (b) Truncate to whole seconds. Rejected because the API can distinguish samples inside one second.
- **Rationale**: The schema defines `timestamp` as an epoch number in seconds with format double (RV-54).
- **Risk**: Very long fractions produce long keys. The keys stay distinct for each sample.

### D-6. Key encoding

- **Decision**: The key is `ospf_` followed by the SHA-256 hexadecimal digest of a canonical JSON array. The array holds the five component values in fixed order.
- **Alternatives**: (a) Join raw values with colons. This is the current behavior. Rejected because the join is ambiguous (RV-15 and RV-16). (b) Percent-encode each value and join. Rejected because null needs a reserved marker, and the keys become long. (c) Use a surrogate integer. Rejected because it is an artificial identifier (RV-70).
- **Rationale**: The SLE identity classes use the same digest pattern with the `sle_` prefix (RV-04). The ArangoDB key sanitizer replaces slash and colon (RV-23), so a readable key can collide after sanitizing. A digest avoids that path.
- **Risk**: The key is opaque. The five components stay stored as columns and fields. The digest encodes natural components only, so it is not an artificial identifier under RV-76.

### D-7. SQLite storage

- **Decision**: Write OSPF rows to `<legacy name>_v2`. Its primary key is `misthelper_ospf_peer_key`. Check the primary key of an existing `_v2` table before any write.
- **Alternatives**: (a) Rebuild the legacy table in place. Rejected because it changes operator data and merged rows cannot be split. (b) Keep the legacy name and add a unique index on the key. Rejected because the legacy primary key still merges rows. The writer keeps that key during an ALTER (RV-11). The SLE precedent covers surrogate-key tables only (RV-08 to RV-10). (c) Keep the legacy name and write plain inserts. Rejected because the legacy primary key still rejects new neighbors.
- **Rationale**: A table keeps its primary key during an ALTER (RV-11). A new table leaves the legacy table untouched.
- **Risk**: Operators query a different table name. Mitigation: task T009 documents each name.

### D-8. Redis and ArangoDB storage

- **Decision**: Keep the endpoint namespaces. The identity key becomes the Redis key suffix and the ArangoDB `_key`.
- **Alternatives**: (a) Rename the endpoints. Rejected because the graph mapping and the collection names use endpoint names (RV-22). (b) Create new collections. Rejected for the same reason and because it adds more change.
- **Rationale**: The router and the writers already build keys from the strategy primary key (RV-17 and RV-19). The identity key fits that path without writer code changes.
- **Risk**: Old and new documents coexist in one collection. Legacy Redis keys expire by the TTL default of 7 days (RV-18). Legacy ArangoDB documents remain until an operator acts (D-9).

### D-9. Legacy data disposition

- **Decision**: Keep every legacy table, key, and document unchanged. Do not migrate automatically. Do not purge. A purge needs a separate human decision.
- **Alternatives**: (a) Copy legacy rows into `_v2` tables automatically. Rejected because merged legacy rows cannot be split, and the copy writes production data without approval. (b) Purge the legacy tables, keys, and documents now. Rejected because the API cannot rebuild the removed data. (c) Keep everything. Chosen.
- **Rationale**: The issue requires an explicit preservation and migration plan (issue body). Keeping data is the only option that needs no approval.
- **Risk**: Legacy rows keep merged or duplicated content. Operators must read them as history.
- **HUMAN-DECISION-REQUIRED**: Approve or refuse a purge or a copy of legacy OSPF rows after review. The recommended option is refuse.
- Warning: A purge deletes rows that the API cannot rebuild.

### D-10. Write-path placement

- **Decision**: Attach keys in `SQLiteDatabaseWriter._process_data` for the SQLite leg. Attach keys in `DatabaseRouter.write` for the Redis JSON and ArangoDB legs. Leave the CSV leg unchanged.
- **Alternatives**: (a) Attach keys in `DataExporter.write_with_format_selection`. Rejected because the attach would add a column to CSV output or block the CSV leg. (b) Attach keys inside each backend writer. Rejected because it adds logic to noncompliant classes and repeats the logic.
- **Rationale**: The SQLite writer resolves the API name inside `write` (RV-06). The table rename must follow that resolution, so `_process_data` is the correct hook (RV-09).
- **Risk**: A future caller might bypass the router. The router is the only polyglot entry (RV-31), so no other OSPF path reaches these writers.

### D-11. Module placement

- **Decision**: Add the package `src/foundation/persistence/identity/` with the class `OspfPeerIdentity`.
- **Alternatives**: (a) Add the class to `endpoint_primary_key_strategies.py`. Rejected because that file is a hot file for batch integration pull requests (RV-74). (b) Add methods to `SQLiteDatabaseWriter` or `DatabaseRouter`. Rejected because both are noncompliant classes, and the constitution forbids new children there. (c) Add a package under `src/foundation/persistence/db/`. Rejected because `db` already holds six children (RV-90).
- **Rationale**: `src/foundation/persistence/` holds three children (RV-89). Adding `identity` keeps it at four, which is compliant.
- **Risk**: An import cycle could form. The new package imports only the standard library.

### D-12. Strategy catalog change

- **Decision**: The two strategy entries name `misthelper_ospf_peer_key` as their `primary_key`.
- **Alternatives**: (a) Keep the component list as `primary_key` and compute the key elsewhere. Rejected because the Redis and ArangoDB writers read `primary_key` fields (RV-15 and RV-19), so the catalog would name the wrong stored key. (b) Add a second catalog. Rejected because the constitution requires the one catalog (RV-76).
- **Rationale**: The catalog names the stored key, which keeps the writers and the catalog consistent.
- **Risk**: The declared index contract test might reject the change. Task T005 names the contingency.

### D-13. Tests and fakes

- **Decision**: Write each failing test before its code. Use `tmp_path` for SQLite, the fake Redis pipeline, and fake ArangoDB collections. Make no live request.
- **Alternatives**: (a) Run live Mist tests. Rejected because the brief forbids live calls and production credentials. (b) Mock each writer. Rejected because the mocks hide the defect.
- **Rationale**: The issue reproduction used the same kind of fakes. The fakes can prove the fix in the same way.
- **Risk**: Fakes differ from the real servers. Unverified item U-05 records the gap.

### D-14. Documentation and changelog

- **Decision**: Add a paragraph after the SQLite row in `documentation/operator-guide.md` (RV-62). Add `changelog.d/issue-4726-ospf-peer-identity.md`.
- **Alternatives**: (a) Edit only `documentation/architecture.md` (RV-63). Rejected because operators read the operator guide. (b) Edit the README. Rejected because the change alters no menu count and no menu title.
- **Rationale**: The change renames tables that operators query. The changelog name follows the issue-only rule (RV-75).
- **Risk**: The paragraph becomes stale. It names patterns and the legacy rule, not counts.

### D-15. Follow-up issues

- **Decision**: File two new issues. One covers the OSPF graph mapping (RV-20 and RV-21). The other covers the stale suggestion script (RV-79). The orchestrator files both.
- **Alternatives**: (a) Fix both in this change. Rejected because each issue holds one concern (RV-72). (b) Leave both unrecorded. Rejected because the defects would have no owner.
- **Rationale**: The graph defect changes vertex creation, which is a separate concern from the key defect.
- **Risk**: No risk to this change.

### D-16. Labels, size, and relations

- **Decision**: Add the label `in-progress`. Keep the labels `bug` and `MistHelper.py`. Use size M. Name #4723, #4724, and #4725 as related issues. Name no dependency.
- **Alternatives**: (a) Use size L. Rejected because the change touches three legs, one new package, and ten files. (b) Name #4725 as a dependency. Rejected because this change leaves the generic ArangoDB key builder unchanged.
- **Rationale**: The change size is medium. The related issues share writer code but not a required order.
- **Risk**: Coordination with the related issues can delay merge. Preconditions in `plan.md` cover the check.

## Remote Verification

The table has 102 rows. The STATUS file holds the same 102 checks in the same order. Blob values show twelve characters. The STATUS file holds the full values. A result of `absent` means the claim is false on `main`. A result of `stale` means the claim is true but conflicts with the current catalog.

| ID | Claim | Path | Blob | Result | Line |
| - | - | - | - | - | - |
| RV-01 | searchSiteOspfStats primary key is mac, peer_ip, timestamp | src/foundation/support/refactors/endpoint_primary_key_strategies.py | 3547991028bd | present | 363 |
| RV-02 | searchOrgOspfStats primary key is device_id, neighbor, timestamp | src/foundation/support/refactors/endpoint_primary_key_strategies.py | 3547991028bd | present | 1563 |
| RV-03 | searchOrgBgpStats has the same tuple (out of scope) | src/foundation/support/refactors/endpoint_primary_key_strategies.py | 3547991028bd | present | 2415 |
| RV-04 | SLE identity key uses SHA-256 with the sle_ prefix | src/foundation/support/refactors/endpoint_primary_key_strategies.py | 3547991028bd | present | 74 |
| RV-05 | Composite DDL keeps only primary key columns present in the batch | src/foundation/persistence/db/database_schema_utils.py | 5374c1b1ffc9 | present | 171 |
| RV-06 | SQLite write resolves the API name before processing | src/foundation/support/refactors/sqlite_database_writer.py | 8931ee6b705b | present | 88 |
| RV-07 | SQLite execution connects, creates, and inserts | src/foundation/support/refactors/sqlite_database_writer.py | 8931ee6b705b | present | 246 |
| RV-08 | SQLite table creation runs the schema step | src/foundation/support/refactors/sqlite_database_writer.py | 8931ee6b705b | present | 284 |
| RV-09 | SQLite processing normalizes rows | src/foundation/support/refactors/sqlite_database_writer.py | 8931ee6b705b | present | 178 |
| RV-10 | SLE precedent attaches an identity key to each row | src/foundation/support/refactors/sqlite_database_writer.py | 8931ee6b705b | present | 192 |
| RV-11 | Missing columns use ALTER and keep the primary key | src/foundation/support/refactors/sqlite_database_writer.py | 8931ee6b705b | present | 319 |
| RV-12 | Composite writes use INSERT OR REPLACE | src/foundation/support/refactors/sqlite_database_writer.py | 8931ee6b705b | present | 368 |
| RV-13 | Missing values become empty text | src/foundation/support/refactors/sqlite_database_writer.py | 8931ee6b705b | present | 442 |
| RV-14 | Database path is read from DATABASE_PATH at call time | src/foundation/support/refactors/sqlite_database_writer.py | 8931ee6b705b | present | 86 |
| RV-15 | Redis key builder substitutes unknown for a missing field | src/foundation/persistence/db/writers/redis_writer.py | 7b66735dab80 | present | 632 |
| RV-16 | Redis key builder joins fields with colons | src/foundation/persistence/db/writers/redis_writer.py | 7b66735dab80 | present | 633 |
| RV-17 | Redis JSON set overwrites the document at its key | src/foundation/persistence/db/writers/redis_writer.py | 7b66735dab80 | present | 603 |
| RV-18 | Redis documents expire after REDIS_JSON_TTL_DAYS, default 7 | src/foundation/persistence/db/writers/redis_writer.py | 7b66735dab80 | present | 36 |
| RV-19 | ArangoDB _compute_key uses the first primary key field | src/foundation/persistence/db/writers/arango_writer.py | 3db01f97a21d | present | 4067 |
| RV-20 | OSPF site graph mapping uses key_field id | src/foundation/persistence/db/writers/arango_writer.py | 3db01f97a21d | present | 2218 |
| RV-21 | OSPF org graph mapping uses key_field id | src/foundation/persistence/db/writers/arango_writer.py | 3db01f97a21d | present | 2905 |
| RV-22 | ArangoDB write names the collection by API function | src/foundation/persistence/db/writers/arango_writer.py | 3db01f97a21d | present | 3989 |
| RV-23 | ArangoDB key sanitizer replaces slash and colon | src/foundation/persistence/db/writers/arango_writer.py | 3db01f97a21d | present | 4295 |
| RV-24 | Graph vertices need the key field value | src/foundation/persistence/db/writers/arango_writer.py | 3db01f97a21d | present | 4108 |
| RV-25 | Router write resolves the strategy from the API name | src/foundation/persistence/db/router.py | e1a65c5b72ef | present | 241 |
| RV-26 | Router write sends composite_pk through the dual write | src/foundation/persistence/db/router.py | e1a65c5b72ef | present | 245 |
| RV-27 | Dual write fans out to Redis JSON and ArangoDB | src/foundation/persistence/db/router.py | e1a65c5b72ef | present | 351 |
| RV-28 | Redis JSON leg is _write_redis_json | src/foundation/persistence/db/router.py | e1a65c5b72ef | present | 335 |
| RV-29 | Router holds OSPF-specific logic (none found) | src/foundation/persistence/db/router.py | e1a65c5b72ef | absent | 0 |
| RV-30 | SQLite leg receives api_function_name | src/operations/exporting/export/data_exporter.py | f45fc71f8fd6 | present | 386 |
| RV-31 | Polyglot leg calls router write with api_function_name | src/operations/exporting/export/data_exporter.py | f45fc71f8fd6 | present | 306 |
| RV-32 | Menu 225 calls searchSiteOspfStats | src/operations/exporting/export/site_search_exporter.py | 49cdfbd29926 | present | 243 |
| RV-33 | Menu 225 filename is prefix plus site name | src/operations/exporting/export/site_search_exporter.py | 49cdfbd29926 | present | 93 |
| RV-34 | Menu 55 calls searchOrgOspfStats | src/operations/exporting/export/org_export_utils.py | cfe85d09447e | present | 703 |
| RV-35 | Org filename is Org plus data type | src/operations/exporting/export/org_export_utils.py | cfe85d09447e | present | 68 |
| RV-36 | Menu 70 calls searchSiteOspfStats | src/operations/exporting/export/site_export_utils.py | de9b901f90ad | present | 392 |
| RV-37 | Site export passes api_call.__name__ to the writer | src/operations/exporting/export/site_export_utils.py | de9b901f90ad | present | 337 |
| RV-38 | Site filename builder returns Site type plus site name | src/operations/exporting/export/site_export_utils.py | de9b901f90ad | present | 40 |
| RV-39 | APIDataFetcher passes its API name to the writer | src/mist/access/api/api_data_fetcher.py | 0dc12650d218 | present | 306 |
| RV-40 | Menu 225 entry binds SiteSearchExporter.ospf_stats | MistHelper.py | 98d7828479de | present | 4272 |
| RV-41 | Menu 55 entry binds OrgExportUtils.ospf_stats | MistHelper.py | 98d7828479de | present | 6240 |
| RV-42 | Menu 70 entry binds the site OSPF export | MistHelper.py | 98d7828479de | present | 6248 |
| RV-43 | Menu 70 category is interactive_safe | src/foundation/support/utils/operation_registry.py | ad30bc79d75f | present | 261 |
| RV-44 | Menu 225 category is interactive_safe | src/foundation/support/utils/operation_registry.py | ad30bc79d75f | present | 293 |
| RV-45 | Menu 55 category is safe | src/foundation/support/utils/operation_registry.py | ad30bc79d75f | present | 718 |
| RV-46 | searchOrgOspfStats operation exists | documentation/mist-api-openapi31yaml.yaml | b7fc2bfbe0aa | present | 21735 |
| RV-47 | searchSiteOspfStats operation exists | documentation/mist-api-openapi31yaml.yaml | b7fc2bfbe0aa | present | 40123 |
| RV-48 | OSPF item schema forbids additional properties | documentation/mist-api-openapi31yaml.yaml | b7fc2bfbe0aa | present | 91260 |
| RV-49 | OSPF item schema declares no required fields | documentation/mist-api-openapi31yaml.yaml | b7fc2bfbe0aa | present | 91259 |
| RV-50 | neighbor is the OSPF neighbor IP address | documentation/mist-api-openapi31yaml.yaml | b7fc2bfbe0aa | present | 91269 |
| RV-51 | peer_ip is deprecated in favor of neighbor | documentation/mist-api-openapi31yaml.yaml | b7fc2bfbe0aa | present | 91283 |
| RV-52 | port_id is the interface that learns the neighbor | documentation/mist-api-openapi31yaml.yaml | b7fc2bfbe0aa | present | 91287 |
| RV-53 | vrf_name is the instance name | documentation/mist-api-openapi31yaml.yaml | b7fc2bfbe0aa | present | 91307 |
| RV-54 | timestamp is an epoch number in seconds | documentation/mist-api-openapi31yaml.yaml | b7fc2bfbe0aa | present | 114345 |
| RV-55 | Partial composite test pins the generic DDL behavior | tests/unit/db/test_database_schema_utils.py | 5b6fa8181717 | present | 190 |
| RV-56 | OSPF graph mapping test pins the vertex mapping | tests/unit/config/standalone/foundation/persistence/arango_writer/test_arango_writer.py | 67c20abcd8f4 | present | 1374 |
| RV-57 | Site search test covers the OSPF tuple | tests/unit/export/test_site_search_exporter.py | 6c810aa688f9 | present | 39 |
| RV-58 | Site export test covers ospf_stats | tests/unit/export/test_site_export_utils_extended.py | ad89ef462d60 | present | 525 |
| RV-59 | Org export test covers ospf_stats | tests/unit/export/test_org_export_utils.py | 6ac423a11005 | present | 954 |
| RV-60 | Router test file exists | tests/unit/config/standalone/foundation/persistence/database/test_router.py | cddaf1d4a602 | present | 1 |
| RV-61 | SQLite writer test file exists | tests/unit/config/foundation/support/refactors/data/storage/test_sqlite_database_writer.py | 62f9c0c2cb72 | present | 1 |
| RV-62 | Operator guide SQLite output row | documentation/operator-guide.md | 60d28f9ea461 | present | 752 |
| RV-63 | Architecture SQLite row | documentation/architecture.md | b4cab54be36d | present | 168 |
| RV-64 | MYPY_PATHS variable | .github/workflows/ci.yml | d51efbc13c0f | present | 93 |
| RV-65 | VULTURE_PATHS variable | .github/workflows/ci.yml | d51efbc13c0f | present | 101 |
| RV-66 | PYDOCSTYLE_PATHS variable | .github/workflows/ci.yml | d51efbc13c0f | present | 104 |
| RV-67 | INTERROGATE_PATHS variable | .github/workflows/ci.yml | d51efbc13c0f | present | 107 |
| RV-68 | Route base is 5 | .specify/scripts/powershell/spec-route.ps1 | 37293a255f9b | present | 17 |
| RV-69 | Route width defaults to 8 | .specify/scripts/powershell/spec-route.ps1 | 37293a255f9b | present | 7 |
| RV-70 | Agents rule prefers a natural key | AGENTS.md | 44a9afffb5bd | present | 129 |
| RV-71 | Agents rule requires a backup before a destructive rewrite | AGENTS.md | 44a9afffb5bd | present | 130 |
| RV-72 | Agents rule requires a second issue for a second defect | AGENTS.md | 44a9afffb5bd | present | 186 |
| RV-73 | Project guide states INSERT OR REPLACE for keyed tables | .github/copilot-instructions.md | f1ec2a4694d0 | present | 208 |
| RV-74 | Project guide names the hot files | .github/copilot-instructions.md | f1ec2a4694d0 | present | 293 |
| RV-75 | Project guide names the changelog fragment pattern | .github/copilot-instructions.md | f1ec2a4694d0 | present | 452 |
| RV-76 | Constitution requires strategies in the catalog | .specify/memory/constitution.md | 4584997a264c | present | 323 |
| RV-77 | Constitution forbids success before a verified durable write | .specify/memory/constitution.md | 4584997a264c | present | 319 |
| RV-78 | Constitution permits one unique process record | .specify/memory/constitution.md | 4584997a264c | present | 46 |
| RV-79 | Suggestion script says no stable key for searchSiteOspfStats | scripts/pk_strategy_suggestions.py | 619e2cd03aca | stale | 2486 |
| RV-80 | Issue commit 3964d21 exists on the remote | commits/3964d21d03f9f5717cb8eafb7272ecff21f5362a | 3964d21d03f9 | present | 0 |
| RV-81 | Issue commit 7b7d540 exists on the remote | commits/7b7d5406ca7b95a96edf42702ee0049e0c7c2d64 | 7b7d5406ca7b | present | 0 |
| RV-82 | Main head is f03c6c9 | refs/heads/main | f03c6c9b36d6 | present | 0 |
| RV-83 | Installed mistapi defines searchSiteOspfStats | .venv\Lib\site-packages\mistapi\api\v1\sites\stats.py | bce91c2c8ff2 | present | 1868 |
| RV-84 | Installed mistapi defines searchOrgOspfStats | .venv\Lib\site-packages\mistapi\api\v1\orgs\stats.py | 247e45260053 | present | 867 |
| RV-85 | Installed mistapi version is 0.64.1 | .venv\Lib\site-packages\mistapi-0.64.1.dist-info\METADATA | n/a | present | 3 |
| RV-86 | Identity package exists on main | src/foundation/persistence/identity/ | n/a | absent | 0 |
| RV-87 | Identity test file exists on main | tests/unit/db/test_ospf_peer_identity.py | n/a | absent | 0 |
| RV-88 | Changelog fragment exists on main | changelog.d/issue-4726-ospf-peer-identity.md | n/a | absent | 0 |
| RV-89 | Persistence folder holds three tracked children | src/foundation/persistence/ | n/a | present | 0 |
| RV-90 | Persistence db folder holds six tracked children (noncompliant) | src/foundation/persistence/db/ | n/a | present | 0 |
| RV-91 | Unit db folder holds two tracked children | tests/unit/db/ | n/a | present | 0 |
| RV-92 | Refactors folder holds 33 tracked children (noncompliant) | src/foundation/support/refactors/ | n/a | present | 0 |
| RV-93 | Exporting export folder holds 49 tracked children (noncompliant) | src/operations/exporting/export/ | n/a | present | 0 |
| RV-94 | Unit export folder holds 55 tracked children (noncompliant) | tests/unit/export/ | n/a | present | 0 |
| RV-95 | Project configuration file exists (mypy and black settings) | pyproject.toml | eca34c826ea4 | present | 1 |
| RV-96 | STE linter configuration file exists | .ste-linter.toml | d9f28ef8faf4 | present | 1 |
| RV-97 | Declared index contract test exists | tests/contract/test_arango_declared_indexes.py | 81563cecb321 | present | 1 |
| RV-98 | Endpoint catalog guardrail test exists | tests/guardrails/test_endpoint_catalog.py | e061f6624a69 | present | 1 |
| RV-99 | Mypy path package exists | scripts/mist_ideas_analyzer_pkg/__init__.py | 75189e765092 | present | 1 |
| RV-100 | SQLite leg derives the table name by dropping the csv suffix | src/operations/exporting/export/data_exporter.py | f45fc71f8fd6 | present | 381 |
| RV-101 | Response component OspfPeersStatsSearch is defined | documentation/mist-api-openapi31yaml.yaml | b7fc2bfbe0aa | present | 64492 |
| RV-102 | Search result schema ospf_peer_stats_search_result is defined | documentation/mist-api-openapi31yaml.yaml | b7fc2bfbe0aa | present | 91223 |

## Sources

- Local repository source, read at `main` (blob SHAs in the table above). Code claims cite the files and line numbers listed in RV-01 to RV-79.
- Mist API: `documentation\mist-api-openapi31yaml.yaml`, lines 21735, 40123, 91259 to 91310, and 114341 to 114346 (RV-46 to RV-54).
- SDK: `.venv\Lib\site-packages\mistapi\api\v1\sites\stats.py` line 1868 and `.venv\Lib\site-packages\mistapi\api\v1\orgs\stats.py` line 867. Both belong to mistapi 0.64.1 (RV-83 to RV-85).
- Skill: `juniper-ospf` (`C:\Users\jmorrison\.copilot\skills\juniper-ospf\SKILL.md`, `02-interfaces-and-adjacency\01-interface-types.md`, and `06-security-instances-and-vpn\03-routing-instances-and-multi-instance.md`). Used for D-2.
- Issue #4726 and its comments, read through `gh issue view`. The issue cites commits 3964d21 and 7b7d540 (RV-80 and RV-81).
- No web source was fetched. The `web_fetch` tool was not needed.

## Unverified

- U-01: Live Mist records always include `neighbor` for each OSPF neighbor. Reason: this record makes no live request, and the schema declares no required field (RV-49).
- U-02: Live records include `vrf_name` and `port_id` for most neighbors. Reason: the same as U-01. The schema marks neither field as required.
- U-03: The operator database holds the legacy primary key that the issue describes. Reason: this record cannot read `data/mist_data.db`. The code path is verified (RV-05 and RV-11).
- U-04: The deployed containers use the default Redis TTL of 7 days. Reason: the environment variable is not read. RV-18 verifies only the default.
- U-05: Behavior with the live Redis and ArangoDB servers. Reason: the record uses fake backends, as the issue does. Live servers are not contacted.
- U-06: One interface can carry two adjacencies with the same neighbor address in one instance. Reason: the local skill sources do not answer this question. The identity uses `port_id` to separate such cases when the API supplies it.
