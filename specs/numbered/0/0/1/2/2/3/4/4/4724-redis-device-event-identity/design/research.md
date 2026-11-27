# Research: Redis device event identity

This file holds the evidence for issue #4724. Each code claim cites a remote row (RC-nn) or a local SDK row. The remote table in section R14 lists each check. Its row count matches `STATUS.json`.

## R1. Issue facts

- Issue #4724 is open. Its labels are `bug` and `MistHelper.py`. The author is `jmorrison-juniper`. Source: https://github.com/jmorrison-juniper/MistHelper/issues/4724, read with `gh issue view` on 2026-11-26.
- The issue reports that `searchOrgDeviceEvents` keys use `id`, `device_id`, and `timestamp`. The documented schema defines neither `id` nor `device_id` (RC-24).
- The Redis JSON writer replaces each missing key field with `unknown` (RC-04). Two events with equal timestamps share one key. The fake pipeline kept one document, while the writer reported two successes.
- The reproduction used main commit `3964d21d03f9f5717cb8eafb7272ecff21f5362a` (RC-56). The issue body reports four collision and control cases. Its environment used Python 3.13.13, but the repository requires Python 3.15 (RC-31).
- Comment `IC_kwDOQltU8c8AAAABko2VSQ` names issue #4725. It is a separate ArangoDB BGP defect. It is not a device event collision.
- Comment `IC_kwDOQltU8c8AAAABko8vqQ` reports a shared-file scan. It names changes to `redis_writer.py`, `router.py`, and the shared endpoint strategy file.
- Comment `IC_kwDOQltU8c8AAAABkpdyOw` names issue #4726. The OSPF case needs its own ownership decision.
- The issue asks to preserve existing data before any migration (issue body, "What happened" section).

## R2. Linked work and open pull requests

- `gh pr list --search 4724` in all states returned no pull requests.
- A snapshot of open pull requests on 2026-11-26 returned seven pull requests. The check covered all twelve planned changed paths. No open pull request changes any of them.
- Related issues on 2026-11-26 are all open. Issue #4721 covers a 52-week device-event CSV overwrite. Issue #4722 covers a menu 97 SQLite success after a failed write. Issue #4723 covers a SQLite device-event overwrite. Issue #4725 covers an ArangoDB BGP key defect. Issue #4726 covers an OSPF export overwrite.
- The pinned commit exists on GitHub (RC-56). The main HEAD commit equals the local HEAD (RC-57).

## R3. Existing record

- No folder under `specs\` starts with `4724-`. A recursive local search found none.
- No remote tree path contains `4724` (RC-58). No legacy record exists to verify or reuse.

## R4. Route calculation

- `Get-SpecRadixSegments` converts the number to base five with width eight (RC-46, RC-47). Its lines are 4 to 33 in `.specify/scripts/powershell/spec-route.ps1`.
- The arithmetic gives 4724 = 1 x 5^5 + 2 x 5^4 + 2 x 5^3 + 3 x 5^2 + 4 x 5 + 4. The eight digits are 0, 0, 1, 2, 2, 3, 4, 4.
- The route is `specs\numbered\0\0\1\2\2\3\4\4`. This matches the orchestrator route.
- The reference record 4920 uses digits 0, 0, 1, 2, 4, 1, 4, 0 by the same arithmetic. Its path exists on main (RC-61).
- `Assert-SpecFeatureDestination` rejects a missing child under a parent with five or more children (RC-65). On main, `specs/numbered/0/0/1/2/2/3` holds three children (RC-60). The child `4` is missing, so the check passes. No ancestor blocks allocation.

## R5. Defect path, from menu to write

- Menu 21 runs `OrgAlarmEventExporter.device_events` (RC-19). That export calls `searchOrgDeviceEvents` and stores rows under that name (RC-21, RC-22).
- Menu 97 runs `OrgAlarmEventExporter.device_events_52w` (RC-20). The 52-week exporter calls `searchOrgDeviceEvents` at line 160 (RC-23).
- `DataExporter.write_with_format_selection` passes rows to `DatabaseRouter.write` (RC-18).
- `DatabaseRouter.write` sends `composite_pk` rows to `_write_dual` (RC-09). `_write_dual` starts the Redis JSON write and the ArangoDB write (RC-10).
- A local search also found direct callers of `searchOrgDeviceEvents` outside the device events exporter. Their write paths were not traced (research U-11).

## R6. Redis key and write result

- `RedisJSONWriter._build_key` joins the endpoint and the key field values. A missing field becomes `unknown` (RC-04).
- `_pipeline_write_batch` sends `pipe.json().set(key, "$", record)` for each row. The root path `$` replaces the whole document (RC-05).
- `_tally_json_results` counts a row as written unless its reply is an exception (RC-06). A replaced document therefore counts as a success.
- The writer sets `success` to `failed == 0` (RC-06). Only exceptions increase `failed`.
- The Redis TTL default is seven days. `REDIS_JSON_TTL_DAYS` sets it (RC-07).
- The timeseries writer uses the same `unknown` pattern for entity identifiers (RC-08). That path stays out of scope.

## R7. ArangoDB leg

- `ArangoDBWriter._compute_key` uses the first key field as `_key`. It uses a UUID when that field is absent (RC-13). A device event without `id` gets a new UUID on each write, so repeat writes duplicate.
- `_build_vertices` skips a record without its key field (RC-14). A device event without `id` gets no vertex.
- The graph map for `searchOrgDeviceEvents` uses `id` for the vertex key (RC-15). The event edges start from `id` (RC-16).
- The device edge resolves the device by `mac` through `to_key_lookup` (RC-17). This lookup works after the change.

## R8. Schema and SDK facts

- The documented `device_event` schema forbids extra properties (RC-24). Its 34 properties include `mac`, `site_id`, `org_id`, `timestamp`, and `type`. No `id` property and no `device_id` property exists.
- The schema requires `org_id`, `timestamp`, and `type` (RC-25).
- The search operation is `searchOrgDeviceEvents` (RC-26). The coverage document lists the same operation (RC-27).
- The installed SDK sits at `.venv\Lib\site-packages\mistapi` (RC-62). The contributor guide pins the 0.64 line (RC-32).
- The mistapi function `searchOrgDeviceEvents` is defined at `devices.py` line 259 (RC-62). Its docstring gives `device_type` a default of `ap` (RC-63). That default may limit menu coverage (research U-10).
- The redis-py JSON `set` method accepts `nx` and `xx` options (RC-64). This change uses neither option.

## R9. Live field evidence and the suggestion script

- The suggestion script lists live response fields for `searchOrgDeviceEvents`. The list holds `ap`, `apfw`, `device_type`, `mac`, `org_id`, `site_id`, `text`, `timestamp`, and `type` (RC-34). It holds no `id` and no `device_id`.
- The same script proposes `["mac", "timestamp"]` (RC-35). That key fails when two events share one MAC and one timestamp but differ in type or text.
- This change does not change or run the generator. The probe date is not recorded (research U-1).

## R10. Structure rules and guards

- The guard pins the exact child counts. `src/foundation/persistence/db` must hold five children. `src/foundation/persistence/db/writers` must hold two children (RC-36, RC-37).
- The constitution requires numbered records under managed roots (RC-52).
- The constitution requires natural business keys from the Mist API and a primary key strategy for each endpoint (RC-66). The exception in the plan rests on this rule.
- The constitution forbids success reports before a verified durable write (RC-53).
- The decision to keep new code inside existing modules (D-8) follows from these pins.

## R11. Test surface

- The Redis writer test at line 72 uses `["id", "device_id"]` as key fields (RC-37). It checks the success result and the write count only. No test covers a collision.
- The router composite test at line 103 checks that each backend write runs once (RC-38). It does not check call arguments.
- The contract test at line 154 expects the Redis writer to receive the original rows (RC-39). Stamping changes those rows, so task T009 updates the assertion.
- The preservation test at line 36 expects the `_key` from `id` (RC-40). The strategy change needs `record_id` in the shared record (task T008).
- The declared index test at line 14 lists device events (RC-41). It checks counts, so it needs no change.
- The ArangoDB writer test module tests the vertex builder at line 770 (RC-42). Task T003 adds the graph test there.

## R12. Local gates

- The local gates table starts at line 50 of `.github/copilot-instructions.md` (RC-33).
- The path variables come from `ci.yml`. MYPY uses line 93. VULTURE uses line 101. PYDOCSTYLE uses line 104. INTERROGATE uses line 107 (RC-48 to RC-51).
- Applicable gates: Compile, Lint, Format, Types, Tests, Full tests, Safe sweep, and Coverage. Also applicable: Test quality, Complexity, Security lint, Code quality, Dead code, Docstrings, Menu reference, Symbols, and STE.
- Not applicable: Dependency audit (no manifest change), Ops portal, and Ops platform (no change under those folders).
- The Symbols gate reports a lost or changed module-level name. This change adds no module-level name (D-5).

## R13. Decisions

### D-1 Device event identity

- Options: (a) keep `id`, `device_id`, and `timestamp`. (b) Use `mac` and `timestamp`, as the suggestion script proposes (RC-35). (c) Use `org_id`, `site_id`, `mac`, `type`, and `timestamp`. (d) Use a SHA-256 digest of the full row.
- Chosen: option (d), stored as `record_id`. The key also holds `org_id` and `timestamp`.
- Reason: Option (a) uses fields the schema does not define (RC-24). Option (b) omits `org_id` and `type`, and `mac` is optional. Option (c) still collides when two events share every listed field and differ only in `text`. Option (d) separates every distinct payload. The rogue DHCP scanner also computes a `record_id` merge key (RC-44, RC-45).
- Risk: Caution: a changed payload for one event creates a second document. The duplicate stays until its Redis TTL ends, and it stays in ArangoDB (research U-2).

### D-2 Key order

- Options: (a) `record_id`, `org_id`, `timestamp`. (b) `org_id`, `timestamp`, `record_id`.
- Chosen: option (a).
- Reason: ArangoDB uses the first key field as `_key` (RC-13). Option (b) would store one ArangoDB document for each organization and timestamp. That would lose archived events. Option (a) keeps `_key` unique, so the ArangoDB rule needs no change. Issue #4725 is not a dependency.
- Risk: A later edit can reorder the key and lose archived events. The preservation test checks `_key` (task T008).

### D-3 Missing key field

- Options: (a) keep the `unknown` sentinel. (b) Drop the row without a failure. (c) Reject the row and report a failure.
- Chosen: option (c). The rule applies to every composite write in `RedisJSONWriter`.
- Reason: The sentinel causes the defect (RC-04). Option (b) hides data loss. The constitution forbids success before a verified write (RC-53). The rule applies to all composite writes because the sentinel is the root cause. Decision D-9 limits the stamp to device events.
- Risk: Other composite endpoints that lack a key field now fail in Redis (research U-9). Each rejection logs one line with the field name.

### D-4 Write mode

- Options: (a) `JSON.SET` overwrite. (b) `JSON.SET` with `nx`. (c) Overwrite, then read back each document.
- Chosen: option (a).
- Reason: The digest key makes an overwrite replace only an identical payload. Option (b) would count an identical repeat write as a failure. Option (c) doubles the round trips.
- Risk: The fix depends on the digest. The regression tests check distinct keys (task T001).

### D-5 Stamp location

- Options: (a) stamp in each writer. (b) Stamp in `DatabaseRouter` before both backend writes. (c) Stamp in every caller that writes device events.
- Chosen: option (b). The class attribute `DEVICE_EVENT_API` and the static method stay inside `DatabaseRouter`. The method reuses `_hash_payload` (RC-11).
- Reason: One stamp gives both backends the same key. Option (a) repeats the logic in two writers. Option (c) changes every caller, and some callers would drift. A static method avoids a module-level name, so the Symbols gate has nothing to flag.
- Risk: The router copies each device event row. Memory grows with batch size (research U-7).

### D-6 Graph mapping

- Options: (a) keep `id` (events are skipped). (b) Remove the device event graph map. (c) Use `record_id` for vertices and event edges. Keep the `mac` lookup and the `site_id` target.
- Chosen: option (c).
- Reason: The vertex builder skips records without the key field (RC-14). Option (b) removes the site edge and the device edge. The device edge already resolves by `mac` (RC-17).
- Risk: The vertex count grows (research U-6).

### D-7 Existing data

- Options: (a) leave existing data unchanged. (b) Purge the old colliding Redis keys now. (c) Migrate old ArangoDB documents to the new keys.
- Chosen: option (a). This is the recommended option.
- Reason: Redis documents expire by TTL (RC-07). Option (b) deletes cache data that the team cannot restore. Option (c) needs a migration plan. The issue asks to preserve data before any migration.
- Risk: Old documents stay visible until they expire. Warning: a later purge deletes cached events that Redis cannot restore.
- HUMAN-DECISION-REQUIRED: Approve or reject any purge of the existing `searchOrgDeviceEvents` Redis keys. The purge deletes production data.

### D-8 Structure

- Options: (a) Add the new logic in a new module under `src/foundation/persistence/db/writers`. (b) Add the logic to `router.py` and `redis_writer.py`.
- Chosen: option (b).
- Reason: The guard pins `writers` at two children and `db` at five (RC-36, RC-37). A new module breaks both pins.
- Risk: `router.py` grows. Each new method stays under 25 lines.

### D-9 Scope of the stamp

- Options: (a) Stamp `searchOrgDeviceEvents` only. (b) Stamp every composite endpoint. (c) Stamp device events and `searchOrgTunnelsStats`.
- Chosen: option (a). The tunnel statistics key (RC-03) becomes a follow-up after its schema check (research U-8).
- Reason: The issue scope is device events. Option (b) changes endpoints without evidence. Option (c) includes a schema this run did not check.

### D-10 Test approach

- Options: (a) Write failing unit tests first, with mocks and a fake pipeline. (b) Add live Redis integration tests. (c) Rely on the existing tests.
- Chosen: option (a). The regression test uses the production strategy and a fake pipeline that replaces root documents, as the issue reproduction does.
- Reason: The gates run without live services. Option (c) lacks a collision case (RC-37). Option (b) needs services the gates do not provide.

### D-11 Documentation

- Options: (a) Update the design guide, the contributor guide, and the changelog. (b) Update only the changelog. (c) Update `README.md`.
- Chosen: option (a).
- Reason: The design guide (RC-28, RC-29) and the contributor guide (RC-30) show the old key, and readers copy examples. The README has no Redis key text (research R15).
- Risk: Future edits can reintroduce the old key. The constitution rule on natural keys (RC-52 and the Database Keys section) guards this.

### D-12 Ownership gate

- Options: (a) Edit only when no open pull request touches a changed file. (b) Edit in parallel with open work. (c) Wait until issues #4721 to #4726 close.
- Chosen: option (a). Check the open pull request list before the first edit and before the push.
- Reason: The 2026-11-26 snapshot shows seven open pull requests and no overlap (R2). Option (c) delays unrelated work for an unknown time.
- Risk: A new pull request can touch a changed file during implementation. Rebase and recheck before the push.

## R14. Remote verification table

Each row records one check. `main` is the remote branch. `local-venv` marks an SDK file that is not in the repository tree.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| RC-01 | Device event primary key names `id` and `device_id` | src/foundation/support/refactors/endpoint_primary_key_strategies.py | main | 3547991028bdbe955e1ba6c8a6bf3082240f2af8 | present | 267 |
| RC-02 | Device event indexes include `device_id` | src/foundation/support/refactors/endpoint_primary_key_strategies.py | main | 3547991028bdbe955e1ba6c8a6bf3082240f2af8 | present | 268 |
| RC-03 | Tunnel statistics key uses `id` and `device_id` | src/foundation/support/refactors/endpoint_primary_key_strategies.py | main | 3547991028bdbe955e1ba6c8a6bf3082240f2af8 | present | 2643 |
| RC-04 | Redis key builder substitutes `unknown` for a missing field | src/foundation/persistence/db/writers/redis_writer.py | main | 7b66735dab8091d32a98cd3d2040db8745c55229 | present | 632 |
| RC-05 | Redis writer replaces the root document with JSON.SET | src/foundation/persistence/db/writers/redis_writer.py | main | 7b66735dab8091d32a98cd3d2040db8745c55229 | present | 603 |
| RC-06 | Redis failure count rises only on an exception reply | src/foundation/persistence/db/writers/redis_writer.py | main | 7b66735dab8091d32a98cd3d2040db8745c55229 | present | 618 |
| RC-07 | Redis TTL default comes from REDIS_JSON_TTL_DAYS | src/foundation/persistence/db/writers/redis_writer.py | main | 7b66735dab8091d32a98cd3d2040db8745c55229 | present | 36 |
| RC-08 | Timeseries writer substitutes `unknown` for an entity identifier | src/foundation/persistence/db/writers/redis_writer.py | main | 7b66735dab8091d32a98cd3d2040db8745c55229 | present | 489 |
| RC-09 | Router sends composite_pk writes to the dual write | src/foundation/persistence/db/router.py | main | e1a65c5b72ef7b8006e3e6e6775e92ff5bbae7a1 | present | 246 |
| RC-10 | Dual write method starts each backend write | src/foundation/persistence/db/router.py | main | e1a65c5b72ef7b8006e3e6e6775e92ff5bbae7a1 | present | 351 |
| RC-11 | Router already hashes canonical JSON in `_hash_payload` | src/foundation/persistence/db/router.py | main | e1a65c5b72ef7b8006e3e6e6775e92ff5bbae7a1 | present | 99 |
| RC-12 | Dual result succeeds only when both backends succeed | src/foundation/persistence/db/__init__.py | main | 11f8dd6d5f13d04c931e9888bf25c3e968df4173 | present | 221 |
| RC-13 | ArangoDB key takes the first key field or a UUID | src/foundation/persistence/db/writers/arango_writer.py | main | 3db01f97a21de021213bb4d8a8f7300b530cc82a | present | 4067 |
| RC-14 | ArangoDB vertex builder skips a record without its key | src/foundation/persistence/db/writers/arango_writer.py | main | 3db01f97a21de021213bb4d8a8f7300b530cc82a | present | 4109 |
| RC-15 | ArangoDB graph map keys device events on `id` | src/foundation/persistence/db/writers/arango_writer.py | main | 3db01f97a21de021213bb4d8a8f7300b530cc82a | present | 1489 |
| RC-16 | ArangoDB device event edges start from `id` | src/foundation/persistence/db/writers/arango_writer.py | main | 3db01f97a21de021213bb4d8a8f7300b530cc82a | present | 1501 |
| RC-17 | ArangoDB device edge resolves devices by MAC lookup | src/foundation/persistence/db/writers/arango_writer.py | main | 3db01f97a21de021213bb4d8a8f7300b530cc82a | present | 1504 |
| RC-18 | Data exporter writes rows through the router | src/operations/exporting/export/data_exporter.py | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 306 |
| RC-19 | Menu 21 runs the device events export | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 3701 |
| RC-20 | Menu 97 runs the 52-week device events export | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 5229 |
| RC-21 | Device events export calls the device events search | src/operations/exporting/export/org_alarm_event_exporter.py | main | b46c4b156f1bccac870aa469375c90927bd4f9c9 | present | 124 |
| RC-22 | Device events export stores rows under the search name | src/operations/exporting/export/org_alarm_event_exporter.py | main | b46c4b156f1bccac870aa469375c90927bd4f9c9 | present | 141 |
| RC-23 | 52-week exporter calls the device events search | src/operations/exporting/export/device_events_52w_exporter.py | main | 97e574382993ca34d56108d6cbf660d047b74be4 | present | 160 |
| RC-24 | Device event schema forbids extra properties and lists no `id` or `device_id` | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 76342 |
| RC-25 | Device event schema requires `org_id`, `timestamp`, and `type` | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 76455 |
| RC-26 | Search operation is `searchOrgDeviceEvents` | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 8672 |
| RC-27 | Coverage document lists the search operation | documentation/MIST_API_GET_ENDPOINTS.md | main | 6281c11b46f22b9814a1948a96df9be4945fb8fd | present | 507 |
| RC-28 | Design guide table lists `id`, `device_id`, and `timestamp` | documentation/diagrams/core/database-strategy.md | main | 90a5e03e789ce27de79ce2ac208c2cf727c8919f | present | 137 |
| RC-29 | Design guide ER block lists `id` and `device_id` as key parts | documentation/diagrams/core/database-strategy.md | main | 90a5e03e789ce27de79ce2ac208c2cf727c8919f | present | 43 |
| RC-30 | Contributor guide example lists `id` and `device_id` | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 205 |
| RC-31 | Contributor guide requires Python 3.15 or newer | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 20 |
| RC-32 | Contributor guide pins mistapi to the 0.64 line | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 21 |
| RC-33 | Contributor guide starts the Local gates section | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| RC-34 | Suggestion script records live device event fields without `id` | scripts/pk_strategy_suggestions.py | main | 619e2cd03aca82128ce70a0264a7ec65b61244ca | present | 2112 |
| RC-35 | Suggestion script proposes `mac` and `timestamp` as the key | scripts/pk_strategy_suggestions.py | main | 619e2cd03aca82128ce70a0264a7ec65b61244ca | present | 2115 |
| RC-36 | Structure guard pins the `db` directory at five children | tests/guardrails/test_persistence_package_structure.py | main | cbeb1beb33eef1099cf00991711ad1fadadfabf2 | present | 88 |
| RC-37 | Structure guard pins the `writers` directory at two children | tests/guardrails/test_persistence_package_structure.py | main | cbeb1beb33eef1099cf00991711ad1fadadfabf2 | present | 89 |
| RC-38 | Redis writer test uses `id` and `device_id` as key fields | tests/unit/config/standalone/foundation/persistence/redis/test_redis_json_writer.py | main | 9ac5ebcb426fe672f4a70a53f7be3a3e49db408e | present | 72 |
| RC-39 | Router composite test asserts the dual route | tests/unit/config/standalone/foundation/persistence/database/test_router.py | main | cddaf1d4a60241e36263b14156461796e16ceec8 | present | 103 |
| RC-40 | Contract test expects the Redis writer to receive the original rows | tests/contract/test_arango_declared_indexes.py | main | 81563cecb3216febc045ea483ff47a18c1708df5 | present | 154 |
| RC-41 | Preservation test derives the expected key from the `id` field | tests/unit/config/foundation/persistence/storage/arango_indexes/test_preservation.py | main | 9033032abc92def11ede1df9fe53115c9d6ef372 | present | 36 |
| RC-42 | Declared index test lists device events | tests/unit/config/foundation/persistence/storage/arango_indexes/test_declared_indexes.py | main | 75fa7d652871463c8efb94be905c186b51f37409 | present | 14 |
| RC-43 | ArangoDB writer test module tests the vertex builder | tests/unit/config/standalone/foundation/persistence/arango_writer/test_arango_writer.py | main | 67c20abcd8f4ec1fb2e3347035c423bae29b2a06 | present | 770 |
| RC-44 | Rogue DHCP stores a computed `record_id` merge key | src/operations/protection/security/rogue_dhcp/records.py | main | f28dd6e2ce63573df5bcc3ef32f5f8b511b80a25 | present | 59 |
| RC-45 | Rogue DHCP builds `record_id` from grouping fields | src/operations/protection/security/rogue_dhcp/records.py | main | f28dd6e2ce63573df5bcc3ef32f5f8b511b80a25 | present | 228 |
| RC-46 | Route algorithm starts from base five | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| RC-47 | Route width defaults to eight | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 7 |
| RC-48 | CI path variable for mypy | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| RC-49 | CI path variable for vulture | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| RC-50 | CI path variable for pydocstyle | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| RC-51 | CI path variable for interrogate | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| RC-52 | Constitution names managed numbered roots | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 57 |
| RC-53 | Constitution forbids success before verified durable writes | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 319 |
| RC-54 | AGENTS.md requires Simplified Technical English | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 42 |
| RC-55 | Changelog README names issue-only fragments | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 27 |
| RC-56 | Pinned commit 3964d21 exists | commit 3964d21d03f9f5717cb8eafb7272ecff21f5362a | commit | 3964d21d03f9f5717cb8eafb7272ecff21f5362a | present | 0 |
| RC-57 | Main HEAD commit equals the local checkout | commit f03c6c9b36d612a48d7b9652998c2fd87dd777ca | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| RC-58 | No issue 4724 record exists on main | specs tree, pattern `4724-` | main | none | absent | 0 |
| RC-59 | Route leaf for issue 4724 is absent on main | specs/numbered/0/0/1/2/2/3/4/4 | main | none | absent | 0 |
| RC-60 | Route parent `specs/numbered/0/0/1/2/2/3` has three children | specs/numbered/0/0/1/2/2/3 | main | d98eafc320dff5952d225f214b52e60c4e2dc7b4 | present | 0 |
| RC-61 | Reference record 4920 exists on main | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| RC-62 | Local mistapi defines `searchOrgDeviceEvents` | .venv\Lib\site-packages\mistapi\api\v1\orgs\devices.py | local-venv | not in repository tree | present | 259 |
| RC-63 | Local mistapi documents the `device_type` default of `ap` | .venv\Lib\site-packages\mistapi\api\v1\orgs\devices.py | local-venv | not in repository tree | present | 294 |
| RC-64 | Local redis-py defines the JSON `set` method | .venv\Lib\site-packages\redis\commands\json\commands.py | local-venv | not in repository tree | present | 485 |
| RC-65 | Route function `Assert-SpecFeatureDestination` checks each parent before allocation | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 76 |
| RC-66 | Constitution requires natural business keys from the Mist API | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 322 |

## R15. Skills, tools, and README search

- No skill loaded. The issue needs no Podman behavior and no Juniper device behavior.
- The deferred tool search showed GitHub, Mist, and browser tools. This run used `gh api` and `gh` reads, as the brief requires. No live Mist call ran. The brief requires local OpenAPI citations.
- `README.md` holds no text on Redis keys, composite keys, or Redis JSON (local search, 2026-11-26). The README rule therefore adds no change.
- The files `documentation/architecture.md`, `documentation/operator-guide.md`, `documentation/development-setup.md`, `documentation/container-deployment.md`, and `documentation/quality-gates.md` hold no Redis key format text (local search, 2026-11-26).

## R16. Sources

- Issue #4724 and comments: https://github.com/jmorrison-juniper/MistHelper/issues/4724 (read with `gh issue view` on 2026-11-26).
- Repository files: `AGENTS.md`, `.github/copilot-instructions.md`, `.specify/memory/constitution.md`, and `.specify/scripts/powershell/spec-route.ps1`. Each is cited in the table in R14.
- Templates read in full: `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, and `checklist-template.md`.
- Reference record shape: `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv`. Its files were read for shape only (RC-61).
- Validator read: `files\spec-drafts\_meta\validate-drafts.ps1`. It is read-only and writes no files.
- Mist API: `documentation\mist-api-openapi31yaml.yaml` (RC-24 to RC-26), with the coverage document (RC-27).
- SDK: `.venv\Lib\site-packages\mistapi` (RC-62, RC-63) and `.venv\Lib\site-packages\redis\commands\json\commands.py` (RC-64).

## Unverified

- U-1: Live device event rows. The schema requires `org_id`, `timestamp`, and `type` (RC-25). The probe that lists fields (RC-34) has no date. No live call ran, so `mac` presence is unverified.
- U-2: Frequency of changed payloads for one event. No production data was available.
- U-3: Number of existing Redis keys that contain `unknown`. No production Redis access was available.
- U-4: RedisJSON server behavior for root replacement at `$`. The client signature was verified (RC-64). Server behavior relies on the issue reproduction.
- U-5: External readers of the old key format. No JSON reader in the tracked code was found by a local search. External readers are unknown.
- U-6: Graph volume after the device vertex and edge change. No production data was available.
- U-7: Hashing cost for a 52-week export. The cost was not measured.
- U-8: The `searchOrgTunnelsStats` schema for `id` (RC-03). The OpenAPI properties were not checked in this run.
- U-9: Effect of rejected rows on other composite endpoints. The count was not measured.
- U-10: Effect of the mistapi default `device_type` of `ap` (RC-63) on menus 21 and 97. The effect was not measured.
- U-11: Other direct callers of `searchOrgDeviceEvents` exist. A local search found them in five code areas. Their write paths were not traced.
