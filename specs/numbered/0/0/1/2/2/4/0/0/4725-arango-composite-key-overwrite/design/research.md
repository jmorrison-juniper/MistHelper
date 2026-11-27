# Research: ArangoDB Identity Keys for Declared Multi-Field Primary Keys

This file holds the decisions for issue #4725, the research notes, the remote verification table, the ownership check, the sources, and the Unverified list. Each code, test, configuration, document, and upstream claim cites one row in the remote table (RC-01 to RC-124). Local-only evidence appears only with its remote row.

## Decisions

Each decision names the alternatives, the chosen option, the reason, and the risk. Only D-7 requires a human decision.

### D-1 Identity key format

- **Decision**: Store `identity_` followed by the SHA-256 hex digest of the typed JSON array of the declared key values, in declared order.
- **Alternatives**: (a) join raw values with a delimiter. (b) keep the first field and add a collision guard. (c) store the full tuple and use a UUID key.
- **Chosen**: The digest.
- **Reason**: ArangoDB keys do not allow `/`, spaces, or `|`, and they advise against `:` (RC-121). A digest has a fixed length and a safe alphabet. The SLE identity uses the same pattern (RC-65). A guard alone (b) cannot prevent the loss. A UUID (c) creates a new document on every run.
- **Risk**: The key no longer shows the MAC address. Operators must query fields, not `_key`. T013 documents this.
- **Human decision**: No.

### D-2 Scope of the rule

- **Decision**: Apply the rule to each effective entry on the ArangoDB write path that declares two or more key fields. At main, that is 121 entries (RC-76). The SLE trend entries (RC-68) and the SLE window entries (RC-69) keep their identity functions.
- **Alternatives**: (a) only `searchSiteBgpStats` (RC-64). (b) every multi-field entry with no exemption. (c) every multi-field entry with an audited exemption table.
- **Chosen**: (c).
- **Reason**: (a) leaves 120 entries with the same defect, and the issue asks for a repair of most composite strategies (RC-76). (b) changes keys for entries whose first field may already identify one record, and it creates duplicates without preventing any loss. (c) limits churn to entries without audited evidence.
- **Risk**: The audit (T002) must finish before the merge (T-MERGE).
- **Human decision**: No.

### D-3 Exemption rule

- **Decision**: Exempt a collection only when the OpenAPI response item documents its first declared key field as a unique identifier of one stored record. The exemption table starts empty.
- **Alternatives**: (a) exempt every first field named `id`. (b) no exemption table. (c) exemptions backed by audit evidence.
- **Chosen**: (c).
- **Reason**: A field name does not prove uniqueness per observation. The `device_event` schema documents no `id` (RC-49), so a name-based exemption is unsafe. An empty table keeps the default safe.
- **Risk**: The audit may find few exemptions, which keeps churn high. That result is safe.
- **Human decision**: No.

### D-4 Single-field entries

- **Decision**: Keep the legacy key for each single-field entry.
- **Alternatives**: (a) hash single values. (b) add fields to the strategy table.
- **Chosen**: Keep the legacy key.
- **Reason**: The legacy key already equals the declared value. Hashing changes every key with no gain. The strategy table is out of scope (FR-013, RC-124). Three effective single-field entries use the timestamp alone (RC-74).
- **Risk**: The timestamp-only identities remain and can collide. A follow-up issue is recommended (T018 c).
- **Human decision**: No.

### D-5 Value normalization

- **Decision**: Keep the value type in the identity payload. Strings compare exactly. Numbers normalize through `Decimal`, so `1` and `1.0` match. Booleans carry their own type tag.
- **Alternatives**: (a) `str(value)` for every value. (b) a JSON dump without type tags. (c) typed normalization.
- **Chosen**: (c).
- **Reason**: `str(1.0)` differs from `str(1)`. A type tag keeps the string `"1"` distinct from the number `1`. The SLE identity functions normalize values before they hash them (RC-65).
- **Risk**: The float representation can change between Python versions. Test 6 covers the integer and float case.
- **Human decision**: No.

### D-6 Missing or invalid key values

- **Decision**: For a missing, empty, null, non-finite, or non-scalar key value, store the record under a UUID key and count it in a warning.
- **Alternatives**: (a) reject the record. (b) convert `None` to text. (c) the UUID fallback.
- **Chosen**: (c).
- **Reason**: Rejection drops data. Text conversion (`str(None)`) creates a false identity. The fallback matches the legacy behavior when a field is absent (RC-57).
- **Risk**: Records with missing fields accumulate on each run. The warning count makes the condition visible (FR-006).
- **Human decision**: No.

### D-7 Legacy ArangoDB documents

- **Decision**: The change deletes nothing and rewrites nothing. Legacy documents stay. A migration requires a verified backup, a dry run, and an approved policy. HUMAN-DECISION-REQUIRED: the operator decides whether legacy documents stay, merge into identity documents, or are removed.
- **Alternatives**: (a) delete legacy documents in this change. (b) rekey legacy documents in place. (c) keep legacy documents and gate any migration.
- **Chosen**: (c).
- **Reason**: Warning: Deletion cannot be undone without a backup (`plan.md`, Rollback and Migration). Warning: A legacy key can already hide a replaced record, and no migration restores that record. The policy changes stored production data, so the operator decides.
- **Risk**: Duplicate documents stay until the policy runs. T015 counts them.
- **Human decision**: Yes.

### D-8 SQLite and Redis legs

- **Decision**: Change no SQLite writer and no Redis writer in this issue.
- **Alternatives**: (a) fix the SQLite and Redis keys here. (b) track them in #4723 and #4724.
- **Chosen**: (b).
- **Reason**: Redis JSON already builds its key from every declared field (RC-83). The SQLite composite primary key uses every declared field that the response contains (RC-84). The open issues own the device-event identity questions.
- **Risk**: The two legs can differ until those issues close. The summary names both legs.
- **Human decision**: No.

### D-9 Shared files and ownership

- **Decision**: Do not edit the strategy table. Edit the writer only after T001 records the handoffs.
- **Alternatives**: (a) edit the strategy table to add fields. (b) edit the writer now.
- **Chosen**: Do not edit the table. Wait for the handoffs before the writer edit.
- **Reason**: The integration pull request of a batch owns the strategy table (RC-124). The issue asks for handoffs before an edit (RC-123). The open pull request check found no conflicting pull request (A-16 in `analysis.md`).
- **Risk**: The handoff may take time. T010, T013, and T014 run first because they touch other files.
- **Human decision**: No.

### D-10 The `searchOrgDeviceEvents` preservation expectation

- **Decision**: Change the expected key at `test_preservation.py` line 36 to the identity key of the record. The expectation computes the digest with `hashlib` in the test, not with the writer code. The changelog names the change.
- **Alternatives**: (a) exempt `searchOrgDeviceEvents`. (b) keep `record-1` and skip the rule for this collection. (c) change the expectation.
- **Chosen**: (c).
- **Reason**: The `device_event` schema documents no `id` (RC-49). An exemption needs documented evidence (D-3). The fixture supplies an `id` that the documented record does not contain. Keeping `record-1` would hide the new rule.
- **Risk**: A reviewer may read the change as a weaker test. The independent hash in the test prevents circular proof.
- **Human decision**: No.

### D-11 Out-of-scope defects

- **Decision**: Record the duplicate strategy names (A-2), the BGP graph key (A-4), and the timestamp-only identities (A-6) as follow-up issues. Do not fix them in this issue.
- **Alternatives**: (a) fix them here. (b) file follow-up issues.
- **Chosen**: (b).
- **Reason**: The repository rule is one issue for one concern (`AGENTS.md`, Issue First, RC-02). The strategy table is a shared file (RC-124). The graph defect needs its own test design.
- **Risk**: The defects stay until the follow-up work lands. T018 prepares the drafts.
- **Human decision**: No.

### D-12 Result counts

- **Decision**: Keep `records_written` as the driver reports it, which counts created and updated documents (RC-54). Add batch logs.
- **Alternatives**: (a) count distinct keys. (b) count replacements as failures. (c) keep the driver semantics.
- **Chosen**: (c).
- **Reason**: The count feeds `WriteResult` and the router contract. Existing tests expect the current counts (RC-92). Distinct records no longer share a key, so the count no longer hides their loss.
- **Risk**: Identical records in one batch still count twice. The batch log reports the counts (FR-014).
- **Human decision**: No.

### D-13 Documentation and changelog

- **Decision**: Update the Source of Truth section of `documentation/diagrams/core/database-strategy.md`. Add one changelog fragment. Leave `documentation/operator-guide.md` and `documentation/architecture.md` unchanged.
- **Alternatives**: (a) update the operator guide. (b) update the database strategy page only.
- **Chosen**: (b).
- **Reason**: The operator guide and the architecture page contain no ArangoDB key rule (RC-36, RC-37). The database strategy page already describes composite identity (RC-38) and names the router mapping (RC-39). The rule belongs there.
- **Risk**: Operators who read only the operator guide miss the change. The changelog fragment names it.
- **Human decision**: No.

## Research Notes

- **R-1 Code path.** Menu 217 calls `SiteSearchExporter.bgp_stats` (RC-89). That method calls `DataExporter.write_with_format_selection` (RC-88, RC-86). `DataExporter` calls `DatabaseRouter.write` (RC-87). The router sends `composite_pk` to both legs (RC-78, RC-82). The ArangoDB leg calls `ArangoDBWriter.write` (RC-52), which calls `_batch_import` (RC-53, RC-54) and `_prepare_document` (RC-55). The key is set in `_compute_key` (RC-56, RC-57).
- **R-2 Effective table.** The table holds 612 entries for 595 names (RC-70). Python keeps the last value for a repeated key. The effective counts are: 126 composite entries, 122 of them multi-field, and 121 affected entries on the ArangoDB path (RC-76). The pinned commit has 136 raw composite lines and 125 effective entries (RC-75). The count method is a last-definition parse of the blob. The parse reads the full blob, which has 4,537 lines at main. Each entry name and key list was read from its block.
- **R-3 Identity evidence.** The BGP item schema declares `mac`, `neighbor`, and `timestamp` (RC-45, RC-46, RC-47). It declares no `id` (RC-48). The response wrapper maps its results to `bgp_stats` items (RC-44). The `device_event` schema declares no `id` (RC-49). The `searchOrgDeviceEvents` results map to `device_events`, whose items are `device_event` (RC-50, RC-51).
- **R-4 Key rules.** ArangoDB keys are 1 to 254 bytes, use a fixed character set, and are unique per collection (RC-121). The python-arango `import_bulk` method sends `onDuplicate` (RC-119). The `replace` value replaces an existing document (RC-120).
- **R-5 Other legs.** The Redis JSON key uses every declared field, joined with colons and an `unknown` sentinel (RC-83). The SQLite composite primary key uses the declared fields that are present (RC-84). The SQLite refactor writer uses `INSERT OR REPLACE` for keyed tables (RC-85).
- **R-6 Existing tests.** The fake collection enforces `on_duplicate` equal to `replace` (RC-93). The preservation test pins the key and the replace kwargs (RC-94, RC-95, RC-96). The SLE preservation tests and identity tests exist (RC-97, RC-98). The SLE guard exists (RC-99). The site search parameter test exists (RC-100). No test calls `_compute_key` or `_prepare_document` (RC-63).
- **R-7 Gates and governance.** The local gates table (RC-04) and the CI path values (RC-23 to RC-26) define the commands in `quickstart.md`. The changelog naming rule (RC-21, RC-22) defines the fragment name. The container rule (RC-34) governs any container run. The changelog policy guard exists (RC-122).
- **R-8 Reference record shape.** The 4920 record holds spec, plan, tasks, analysis, and a `design/` folder (RC-104 to RC-111). Its spec holds clarifications, user stories with priorities, functional requirements, success criteria, assumptions, and non-goals. Its tasks are grouped in phases. Its research file holds numbered decisions R1 to R17. Its quickstart holds numbered scenarios. This record uses the same layout at a smaller size, because the change touches one writer path.
- **R-9 SDK and API.** The SDK method is `searchSiteBgpStats` in `mistapi/api/v1/sites/stats.py` at line 532, in mistapi 0.64.1 (RC-116, RC-117). The OpenAPI operation is `GET /api/v1/sites/{site_id}/stats/bgp_peers/search` at line 39175 (RC-43, RC-42, RC-41).
- **R-10 Deletion path.** `mark_absent_as_deleted` has no production caller (RC-62). The change therefore does not trigger soft deletes.
- **R-11 Ownership.** The open pull request check ran on 7 open pull requests. None changes `arango_writer.py` or the strategy table. The check is a read of pull request files at record time. It is not a path claim, so it has no row in the table. The branch-level claims in issue comment RC-123 remain unverified (U-1).
- **R-12 Linked work.** A search for `4725` in pull requests returned no pull request. The issue has no linked pull request.
- **R-13 Skills.** No skill was loaded. The brief allows a skill for Podman or Juniper device questions. None is open for this issue.

## Remote Verification Table

Rows: 124. Results: 117 present, 7 absent. The results column uses the brief vocabulary. `absent` means the claimed item is missing. `main` is the remote branch. `local` means a third-party package in `.venv`, which is not part of the repository tree.

| # | Claim | Path | Ref | Blob or tree SHA | Result | Line |
| - | - | - | - | - | - | - |
| RC-01 | AGENTS.md writing style rule | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| RC-02 | AGENTS.md safety and secrets rules | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 157 |
| RC-03 | AGENTS.md specifications trigger | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 345 |
| RC-04 | copilot-instructions local gates table | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 55 |
| RC-05 | copilot-instructions mistapi pin wording 0.64.0 | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 21 |
| RC-06 | copilot-instructions primary key types | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 196 |
| RC-07 | copilot-instructions safe sweep scope | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 227 |
| RC-08 | copilot-instructions containers and ports | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 354 |
| RC-09 | constitution principle I five-item rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| RC-10 | constitution principle IV pipeline | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 143 |
| RC-11 | constitution principle VI inline comments | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 204 |
| RC-12 | constitution principle VII action logging | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 235 |
| RC-13 | constitution mistapi constraint wording 0.59 plus | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 279 |
| RC-14 | constitution database keys constraint | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 322 |
| RC-15 | spec template headings | .specify/templates/spec-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 1 |
| RC-16 | plan template headings | .specify/templates/plan-template.md | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 1 |
| RC-17 | tasks template format | .specify/templates/tasks-template.md | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 1 |
| RC-18 | checklist template format | .specify/templates/checklist-template.md | main | 806657da09d1058823923e346a323b633114971a | present | 1 |
| RC-19 | base-5 eight-level route formula | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| RC-20 | pull request template | .github/PULL_REQUEST_TEMPLATE.md | main | ed03e8f36f20962d9c7bbd74cde192d5adfdcc77 | present | 1 |
| RC-21 | changelog fragment naming rule | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 19 |
| RC-22 | changelog keep first name after pull request opens | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 32 |
| RC-23 | CI MYPY_PATHS value | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| RC-24 | CI VULTURE_PATHS value | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| RC-25 | CI PYDOCSTYLE_PATHS value | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| RC-26 | CI INTERROGATE_PATHS value | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| RC-27 | pyproject Python version requirement | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 23 |
| RC-28 | pyproject mistapi pin 0.64.1 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 29 |
| RC-29 | pyproject python-arango pin | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 76 |
| RC-30 | pyproject ruff rule selection includes F | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 209 |
| RC-31 | requirements mistapi exact pin | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 129 |
| RC-32 | requirements python-arango exact pin | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 197 |
| RC-33 | quality gates mypy command at line 248 lists paths that differ from ci.yml MYPY_PATHS, and line 252 names ci.yml as the source | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 248 |
| RC-34 | container test rule compose group and naming | documentation/container-deployment.md | main | f06228bc6bbe77cc009f956403872a06462466ea | present | 141 |
| RC-35 | development setup new worktree bootstrap note | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 40 |
| RC-36 | architecture document has no ArangoDB key rule | documentation/architecture.md | main | b4cab54be36d223b7eba879ca99b838f508938ce | absent | 0 |
| RC-37 | operator guide has no ArangoDB key rule | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | absent | 0 |
| RC-38 | database strategy composite flow to INSERT OR REPLACE by composite | documentation/diagrams/core/database-strategy.md | main | 90a5e03e789ce27de79ce2ac208c2cf727c8919f | present | 120 |
| RC-39 | database strategy router mapping to ArangoDB and Redis JSON | documentation/diagrams/core/database-strategy.md | main | 90a5e03e789ce27de79ce2ac208c2cf727c8919f | present | 175 |
| RC-40 | data model INSERT OR REPLACE statement | documentation/wiki/Data-Model.md | main | a5f3bd61f1bf773215d8ddc7f318d25de71d075a | present | 19 |
| RC-41 | MIST API GET coverage row for searchSiteBgpStats | documentation/MIST_API_GET_ENDPOINTS.md | main | 6281c11b46f22b9814a1948a96df9be4945fb8fd | present | 1508 |
| RC-42 | BGP GET documentation method and path | documentation/api/sites/GET_sites_site_id_stats_bgp_peers_search.md | main | 4fdfa5a77c72fe5b925f804c9e61b95d54eb18c0 | present | 7 |
| RC-43 | OpenAPI searchSiteBgpStats operationId | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 39175 |
| RC-44 | OpenAPI BGP search results items reference bgp_stats | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 93377 |
| RC-45 | OpenAPI bgp_stats declares mac | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 71997 |
| RC-46 | OpenAPI bgp_stats declares neighbor | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 72005 |
| RC-47 | OpenAPI bgp_stats declares timestamp | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 72048 |
| RC-48 | OpenAPI bgp_stats schema declares no id property | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | absent | 71979 |
| RC-49 | OpenAPI device_event schema declares no id property | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | absent | 76341 |
| RC-50 | OpenAPI searchOrgDeviceEvents response results reference device_events | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 94043 |
| RC-51 | OpenAPI device_events items reference device_event | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 76463 |
| RC-52 | ArangoDB writer write method | src/foundation/persistence/db/writers/arango_writer.py | main | 3db01f97a21de021213bb4d8a8f7300b530cc82a | present | 3987 |
| RC-53 | ArangoDB batch import uses on_duplicate replace | src/foundation/persistence/db/writers/arango_writer.py | main | 3db01f97a21de021213bb4d8a8f7300b530cc82a | present | 4034 |
| RC-54 | ArangoDB counts created plus updated as writes | src/foundation/persistence/db/writers/arango_writer.py | main | 3db01f97a21de021213bb4d8a8f7300b530cc82a | present | 4043 |
| RC-55 | ArangoDB prepare document assigns _key | src/foundation/persistence/db/writers/arango_writer.py | main | 3db01f97a21de021213bb4d8a8f7300b530cc82a | present | 4052 |
| RC-56 | ArangoDB compute key SLE branch | src/foundation/persistence/db/writers/arango_writer.py | main | 3db01f97a21de021213bb4d8a8f7300b530cc82a | present | 4061 |
| RC-57 | ArangoDB compute key first declared field fallback | src/foundation/persistence/db/writers/arango_writer.py | main | 3db01f97a21de021213bb4d8a8f7300b530cc82a | present | 4067 |
| RC-58 | ArangoDB collection named by endpoint argument | src/foundation/persistence/db/writers/arango_writer.py | main | 3db01f97a21de021213bb4d8a8f7300b530cc82a | present | 3971 |
| RC-59 | ArangoDB BGP graph mapping key_field is id | src/foundation/persistence/db/writers/arango_writer.py | main | 3db01f97a21de021213bb4d8a8f7300b530cc82a | present | 2199 |
| RC-60 | ArangoDB vertex builder skips records without key field | src/foundation/persistence/db/writers/arango_writer.py | main | 3db01f97a21de021213bb4d8a8f7300b530cc82a | present | 4099 |
| RC-61 | ArangoDB sanitize key replaces slash and colon | src/foundation/persistence/db/writers/arango_writer.py | main | 3db01f97a21de021213bb4d8a8f7300b530cc82a | present | 4293 |
| RC-62 | mark absent as deleted has no production caller | src/foundation/persistence/db/writers/arango_writer.py | main | 3db01f97a21de021213bb4d8a8f7300b530cc82a | absent | 4297 |
| RC-63 | no test references compute key or prepare document | tests | main | n/a | absent | 0 |
| RC-64 | strategy entry searchSiteBgpStats composite_pk with mac neighbor timestamp | src/foundation/support/refactors/endpoint_primary_key_strategies.py | main | 3547991028bdbe955e1ba6c8a6bf3082240f2af8 | present | 354 |
| RC-65 | SLE trend identity key function | src/foundation/support/refactors/endpoint_primary_key_strategies.py | main | 3547991028bdbe955e1ba6c8a6bf3082240f2af8 | present | 68 |
| RC-66 | SLE window identity class | src/foundation/support/refactors/endpoint_primary_key_strategies.py | main | 3547991028bdbe955e1ba6c8a6bf3082240f2af8 | present | 99 |
| RC-67 | strategy dictionary start | src/foundation/support/refactors/endpoint_primary_key_strategies.py | main | 3547991028bdbe955e1ba6c8a6bf3082240f2af8 | present | 141 |
| RC-68 | SLE trend entries are composite_pk | src/foundation/support/refactors/endpoint_primary_key_strategies.py | main | 3547991028bdbe955e1ba6c8a6bf3082240f2af8 | present | 4275 |
| RC-69 | SLE window entries are auto_increment_with_unique | src/foundation/support/refactors/endpoint_primary_key_strategies.py | main | 3547991028bdbe955e1ba6c8a6bf3082240f2af8 | present | 4282 |
| RC-70 | duplicate strategy name shadows earlier composite definition listSiteSleImpactedChassis | src/foundation/support/refactors/endpoint_primary_key_strategies.py | main | 3547991028bdbe955e1ba6c8a6bf3082240f2af8 | present | 2599 |
| RC-71 | ExHardwareInventory composite_pk entry with three key fields | src/foundation/support/refactors/endpoint_primary_key_strategies.py | main | 3547991028bdbe955e1ba6c8a6bf3082240f2af8 | present | 3506 |
| RC-72 | siteVariableAudit natural_pk entry with four key fields | src/foundation/support/refactors/endpoint_primary_key_strategies.py | main | 3547991028bdbe955e1ba6c8a6bf3082240f2af8 | present | 3460 |
| RC-73 | searchOrgDeviceEvents composite_pk entry keys id device_id timestamp | src/foundation/support/refactors/endpoint_primary_key_strategies.py | main | 3547991028bdbe955e1ba6c8a6bf3082240f2af8 | present | 265 |
| RC-74 | timestamp-only composite_pk entries listSiteAnomalyEvents searchSiteDeviceConfigHistory searchSiteDeviceLastConfigs at lines 562 570 577 | src/foundation/support/refactors/endpoint_primary_key_strategies.py | main | 3547991028bdbe955e1ba6c8a6bf3082240f2af8 | present | 562 |
| RC-75 | pinned strategy table has 136 raw composite_pk lines and 125 effective entries | src/foundation/support/refactors/endpoint_primary_key_strategies.py | 3964d21d03f9f5717cb8eafb7272ecff21f5362a | fb1fb1329e15af5debb7a4a3c4cda5d1478bdc36 | present | 0 |
| RC-76 | main strategy table has 137 raw composite_pk lines 126 effective and 121 affected entries | src/foundation/support/refactors/endpoint_primary_key_strategies.py | main | 3547991028bdbe955e1ba6c8a6bf3082240f2af8 | present | 0 |
| RC-77 | ArangoDB writer unchanged between pinned commit and main | src/foundation/persistence/db/writers/arango_writer.py | 3964d21d03f9f5717cb8eafb7272ecff21f5362a | 3db01f97a21de021213bb4d8a8f7300b530cc82a | present | 0 |
| RC-78 | router composite_pk dual write dispatch | src/foundation/persistence/db/router.py | main | e1a65c5b72ef7b8006e3e6e6775e92ff5bbae7a1 | present | 33 |
| RC-79 | router timeseries_pk routes to Redis TimeSeries | src/foundation/persistence/db/router.py | main | e1a65c5b72ef7b8006e3e6e6775e92ff5bbae7a1 | present | 34 |
| RC-80 | router snapshot list excludes searchSiteBgpStats | src/foundation/persistence/db/router.py | main | e1a65c5b72ef7b8006e3e6e6775e92ff5bbae7a1 | present | 50 |
| RC-81 | router snapshot path uses first primary key field | src/foundation/persistence/db/router.py | main | e1a65c5b72ef7b8006e3e6e6775e92ff5bbae7a1 | present | 279 |
| RC-82 | router dual write leg ArangoDB and Redis JSON | src/foundation/persistence/db/router.py | main | e1a65c5b72ef7b8006e3e6e6775e92ff5bbae7a1 | present | 351 |
| RC-83 | Redis JSON key built from every primary key field | src/foundation/persistence/db/writers/redis_writer.py | main | 7b66735dab8091d32a98cd3d2040db8745c55229 | present | 630 |
| RC-84 | SQLite composite primary key uses present strategy fields | src/foundation/persistence/db/database_schema_utils.py | main | 5374c1b1ffc90e756e15dd19d2ddc4a859c3a6fc | present | 171 |
| RC-85 | SQLite refactor writer keyed upsert uses INSERT OR REPLACE | src/foundation/support/refactors/sqlite_database_writer.py | main | 8931ee6b705bb351a45a9b2f8a046fc18ec43ccd | present | 362 |
| RC-86 | DataExporter write_with_format_selection entry point | src/operations/exporting/export/data_exporter.py | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 153 |
| RC-87 | DataExporter calls router write with api function name | src/operations/exporting/export/data_exporter.py | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 306 |
| RC-88 | site search exporter persists through DataExporter | src/operations/exporting/export/site_search_exporter.py | main | 49cdfbd299267e5721ca30f19b59beb04ff2faaf | present | 94 |
| RC-89 | site search exporter BGP stats calls mistapi searchSiteBgpStats | src/operations/exporting/export/site_search_exporter.py | main | 49cdfbd299267e5721ca30f19b59beb04ff2faaf | present | 163 |
| RC-90 | menu 217 registration handler and title | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 4208 |
| RC-91 | menu 217 category interactive_safe | src/foundation/support/utils/operation_registry.py | main | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | present | 285 |
| RC-92 | writer natural key test asserts _key value | tests/unit/config/standalone/foundation/persistence/arango_writer/test_arango_writer.py | main | 67c20abcd8f4ec1fb2e3347035c423bae29b2a06 | present | 106 |
| RC-93 | fake collection import_bulk enforces replace and tracks keys | tests/unit/config/foundation/persistence/storage/arango_indexes/fakes.py | main | 01a817bce3ad8a0fc7cbe16f0c8b22798de2e12c | present | 60 |
| RC-94 | preservation test parametrized with searchOrgDeviceEvents | tests/unit/config/foundation/persistence/storage/arango_indexes/test_preservation.py | main | 9033032abc92def11ede1df9fe53115c9d6ef372 | present | 22 |
| RC-95 | preservation test expects record-1 key for the write contract | tests/unit/config/foundation/persistence/storage/arango_indexes/test_preservation.py | main | 9033032abc92def11ede1df9fe53115c9d6ef372 | present | 36 |
| RC-96 | preservation test asserts on_duplicate replace kwargs | tests/unit/config/foundation/persistence/storage/arango_indexes/test_preservation.py | main | 9033032abc92def11ede1df9fe53115c9d6ef372 | present | 40 |
| RC-97 | SLE legacy preservation tests for ArangoDB documents | tests/unit/db/sle_window_summary/test_backend_preservation.py | main | 38670362f1e2629a6630b6b0065cc251df117c4d | present | 124 |
| RC-98 | SLE window identity export tests | tests/unit/db/sle_window_summary/test_export_identity.py | main | 74f8c1ec8f6ea5e45619f266af89d643873cc111 | present | 22 |
| RC-99 | SLE primary key measurement guard | tests/guardrails/test_endpoint_catalog.py | main | e061f6624a69cbfc7947275c076523c3c8d85fcd | present | 186 |
| RC-100 | site search exporter parametrized operation names | tests/unit/export/test_site_search_exporter.py | main | 6c810aa688f906e374eae376cefc3bfe562daaa5 | present | 26 |
| RC-101 | writers directory has three children | src/foundation/persistence/db/writers | main | tree 5f0c0ace8fbec6b46555f16d0b32b9d28907adf2 | present | 0 |
| RC-102 | arango writer test directory has three children | tests/unit/config/standalone/foundation/persistence/arango_writer | main | tree 5f0c0ace8fbec6b46555f16d0b32b9d28907adf2 | present | 0 |
| RC-103 | arango indexes test directory has five children at limit | tests/unit/config/foundation/persistence/storage/arango_indexes | main | tree 5f0c0ace8fbec6b46555f16d0b32b9d28907adf2 | present | 0 |
| RC-104 | reference record 4920 spec.md shape | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 1 |
| RC-105 | reference record 4920 plan.md shape | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/plan.md | main | 686c89f85ee7c094526bafaf782d4398f6c523ff | present | 1 |
| RC-106 | reference record 4920 tasks.md shape | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/tasks.md | main | 72bd85483706269fdf809322b2dca38a0e1d5698 | present | 1 |
| RC-107 | reference record 4920 analysis.md shape | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/analysis.md | main | b5db89b9d0d0a4f8e725ad8e0e746c34fa1a24e7 | present | 1 |
| RC-108 | reference record 4920 design research shape | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/design/research.md | main | 2e4aaa714e56fff7f96a2af9e686e9f5c06224a7 | present | 1 |
| RC-109 | reference record 4920 design data model shape | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/design/data-model.md | main | 616fe0e47fb17a4eec28b31e5525e9a7992fbed1 | present | 1 |
| RC-110 | reference record 4920 design quickstart shape | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/design/quickstart.md | main | a972d6ba342213bbc7a33713516aa73db8a75f65 | present | 1 |
| RC-111 | reference record 4920 checklist shape | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/design/checklists/requirements.md | main | 4a53b89939bb523902efeaaffd1d7b12221c717b | present | 1 |
| RC-112 | PK probe heuristic treats id plus timestamp as composite | scripts/probe_pk_strategy.py | main | 991e56c43e381c2cb655387261b68bb6a6222198 | present | 21 |
| RC-113 | pinned commit exists | commits/3964d21d03f9f5717cb8eafb7272ecff21f5362a | 3964d21d03f9f5717cb8eafb7272ecff21f5362a | tree b89d20f534a27dfa39cdf8fdb4bf6afe10e4d2d6 | present | 0 |
| RC-114 | main head commit is f03c6c9b | commits/main | main | tree 5f0c0ace8fbec6b46555f16d0b32b9d28907adf2 | present | 0 |
| RC-115 | no legacy 4725 record exists in the tree | specs | main | none | absent | 0 |
| RC-116 | installed mistapi version 0.64.1 | .venv\Lib\site-packages\mistapi-0.64.1.dist-info | local | n/a | present | 0 |
| RC-117 | installed mistapi searchSiteBgpStats signature | .venv\Lib\site-packages\mistapi\api\v1\sites\stats.py | local | n/a | present | 532 |
| RC-118 | installed python-arango version 8.3.7 | .venv\Lib\site-packages\python_arango-8.3.7.dist-info | local | n/a | present | 0 |
| RC-119 | python-arango import_bulk method | .venv\Lib\site-packages\arango\collection.py | local | n/a | present | 2303 |
| RC-120 | python-arango on_duplicate meanings | .venv\Lib\site-packages\arango\collection.py | local | n/a | present | 2344 |
| RC-121 | ArangoDB document key rules upstream | https://docs.arango.ai/arangodb/stable/concepts/data-structure/documents/ | n/a | n/a | present | 0 |
| RC-122 | changelog fragment policy guard reads changelog.d and the policy file | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 0 |
| RC-123 | issue 4725 ownership comment requires handoff before any edit to shared files | https://github.com/jmorrison-juniper/MistHelper/issues/4725#issuecomment-6753824761 | n/a | n/a | present | 0 |
| RC-124 | copilot-instructions hot files section names the strategy table as owned by the integration pull request | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 293 |

## Ownership Check (not a path claim)

- **Method**: A read of open pull requests with their changed files. Command: `gh pr list -R jmorrison-juniper/MistHelper --state open --limit 300 --json number,title,headRefName,files`, filtered for the two shared files.
- **Result**: 7 open pull requests were checked. None changes `src/foundation/persistence/db/writers/arango_writer.py` or `src/foundation/support/refactors/endpoint_primary_key_strategies.py`.
- **Limit**: The issue comment (RC-123) reports changes on three refs for the writer and six refs for the strategy table. It also names a preserved local branch. Those refs and the branch are unverified (U-1).

## Sources

- Local repository files are listed in the remote table with their blob SHAs. Each local file that this record reads equals its remote blob. The check runs `git hash-object` on the local file and compares the result with the blob SHA in the table.
- Third-party code is in `.venv\Lib\site-packages`. Rows RC-116 to RC-120 cite it.
- Upstream: ArangoDB documents page, row RC-121. The page redirected from `docs.arangodb.com` to `docs.arango.ai`.
- GitHub: issue #4725 and its comments (row RC-123), commit `3964d21d03f9f5717cb8eafb7272ecff21f5362a` (row RC-113), and commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` (row RC-114).

## Unverified

- **U-1 Preserved local branch.** The issue names no branch. The record did not inspect local refs for the writer diff. The branch content and its owner are unverified.
- **U-2 Live BGP records.** No live Mist response was read. The schema and the example in RC-45 to RC-48 are the only evidence.
- **U-3 Ruff duplicate-key rule.** `pyproject.toml` selects `F` (RC-30). The record did not run ruff. Whether the rule reports the repeated keys in the strategy table is unverified. T-LOCAL-GATES must run the lint gate and record the result.
- **U-4 Runtime reachability.** The record did not confirm that every one of the 121 entries reaches `DataExporter` at run time. T002 checks each entry.
- **U-5 BGP graph effect.** The record did not run `_populate_graph` against the BGP mapping. The effect of RC-59 and RC-60 on vertices and edges is inferred from code and schema.
- **U-6 SQLite and Redis with missing fields.** The record did not test the two legs with absent fields. The effects in RC-83 and RC-84 are inferred.
- **U-7 Live device events.** The record did not check whether live `searchOrgDeviceEvents` records carry `id`. RC-49 covers the documented schema only.
- **U-8 Portal store path.** The record did not confirm whether `upgradeRunActions` (line 2969 in the strategy table) writes through `DataExporter`. T002 checks this.
- **U-9 Server version.** The record used the stable ArangoDB documents page (RC-121). It did not check the server version in the deployed container.
- **U-10 Count method.** The effective counts (RC-75, RC-76) come from a last-definition parse of the blob. The parse was not run by a repository script. The counts are reproducible from the listed lines.
