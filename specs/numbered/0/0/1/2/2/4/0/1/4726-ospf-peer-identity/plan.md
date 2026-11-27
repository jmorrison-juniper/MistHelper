# Implementation Plan: OSPF Peer Identity Keys

**Branch**: `fix/4726-ospf-peer-identity` (proposed) | **Date**: 2026-11-26 | **Spec**: `spec.md` in this record

**Input**: Numeric record `specs/numbered/0/0/1/2/2/4/0/1/4726-ospf-peer-identity/`. The route matches base-5 encoding of 4726 in eight digits. See `design/research.md`, RV-68 and RV-69.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Supporting artifacts sit under `design/`.

## Summary

Three writers key OSPF peer records with fields that are absent or reused. The SQLite primary key drops absent fields. The Redis JSON key substitutes `unknown`. The ArangoDB `_key` uses only the first key field. This change adds one identity key for each OSPF peer record. It writes new SQLite rows to a `_v2` table. It writes new Redis and ArangoDB values under the identity key. Legacy data stays unchanged.

## Technical Context

**Language/Version**: Python 3.15 or newer, as stated in `.github/copilot-instructions.md`, section "Language and environment".

**Primary Dependencies**: `mistapi` 0.64.1, pinned by `mistapi>=0.64.0,<0.65`. The change uses the standard library modules `hashlib`, `json`, and `decimal`. It adds no package.

**Storage**: SQLite file `data/mist_data.db`, Redis JSON with the ReJSON module, and ArangoDB collections. The writers are `SQLiteDatabaseWriter`, `RedisJSONWriter`, and `ArangoDBWriter`.

**Testing**: pytest with `tmp_path` for SQLite, a fake Redis pipeline, and fake ArangoDB collections. No live Mist request and no production credential appear in any test.

**Target Platform**: Windows 11, macOS, and Linux. The tool runs in a Podman container in production.

**Project Type**: Python command-line tool with a menu, exporters, and writers.

**Performance Goals**: No new target. The identity computation is one pass over each batch. It adds one SHA-256 digest for each record.

**Constraints**: No change to CSV output. No change to legacy data. No change to the primary key of any other endpoint.

**Scale/Scope**: Two endpoints, three menus (55, 70, and 225), and three writer legs.

## Constitution Check

Each rule has a result and a reason. Every result is pass.

| Rule | Result | Reason |
| - | - | - |
| I. Five-item rule | pass | The new package `src/foundation/persistence/identity/` raises `src/foundation/persistence/` from three to four tracked children (RV-89). `tests/unit/db/` rises from two to three (RV-91). No new direct child enters a noncompliant parent (RV-90, RV-92, RV-93, RV-94). |
| I. Existing violations touched | pass | `SQLiteDatabaseWriter` and `DatabaseRouter` are noncompliant classes. This change adds no method to either class. It edits three existing methods. See Complexity Tracking. |
| I. Process records | pass | One changelog fragment is a required unique process record (RV-78). |
| II. Class-based architecture | pass | The new behavior lives in class `OspfPeerIdentity`. No wrapper function is added. |
| III. Safety first | pass | Each identity input is validated before use. No destructive operation is added. Logs carry component names and counts, not identity values. |
| III. Secrets | pass | The change adds no credential. The key holds MAC, neighbor, and timestamp values, which are device data and not secrets. |
| IV. Full deployment pipeline | pass | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover the pipeline. |
| V. ASCII logging | pass | Each new log message uses ASCII text only. |
| VI. Inline comments | pass | Each new executable line gets an inline comment. Each changed line in an existing method gets one too. |
| VII. Action logging | pass | Each attach action logs an info line before it and a debug line after it. Each rejection logs an error line with the component name. |
| Mist Cloud: mistapi only | pass | The change uses existing mistapi calls. It adds no direct HTTP request. |
| Mist Cloud: owned WebSocket | pass | The change adds no owned WebSocket transport. |
| Container runtime | pass | No container is started. Tests use fake backends. |
| Test containers | pass | Not applicable. No test starts a container. |
| File paths | pass | The new code builds no path string. Existing paths stay unchanged. |
| Output backends | pass | The SQLite and polyglot legs keep their entry points, `SQLiteDatabaseWriter` and `DatabaseRouter.write`. |
| Database keys | pass | The identity key is a SHA-256 digest of natural components. The components stay stored as columns or fields. See research D-6. |
| Primary key strategy | pass | The two strategy entries name the stored key (FR-013). See research D-12. |
| Data directory | pass | The database path stays `data/mist_data.db`. |
| Zscaler and push | pass | No registry push is part of this change. |
| Specification escalation | pass | This change alters a database schema and a primary key strategy. A specification is required. |

## Preconditions

Run this check before the branch exists. Repeat it in T-PR.

`gh pr list -R jmorrison-juniper/MistHelper --state open --json number,headRefName,files`

On 2026-11-26 the check returned seven open pull requests. None touches the files in the change map. The file `src/foundation/support/refactors/endpoint_primary_key_strategies.py` is a shared file. Record a handoff comment on #4726 before the branch exists. Coordinate with #4723, #4724, and #4725 first.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/2/4/0/1/4726-ospf-peer-identity/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      ospf-peer-identity.md
      storage-outputs.md
      mist-ospf-response.md
    checklists/
      requirements.md
      data-integrity.md
      gates.md
```

### Source Code (repository root)

```text
src/foundation/persistence/identity/__init__.py      (add)
src/foundation/persistence/identity/ospf_peer.py     (add)
src/foundation/support/refactors/endpoint_primary_key_strategies.py  (modify)
src/foundation/support/refactors/sqlite_database_writer.py           (modify)
src/foundation/persistence/db/router.py                              (modify)
tests/unit/db/test_ospf_peer_identity.py                             (add)
tests/unit/config/foundation/support/refactors/data/storage/test_sqlite_database_writer.py  (modify)
tests/unit/config/standalone/foundation/persistence/database/test_router.py                 (modify)
documentation/operator-guide.md                                       (modify)
changelog.d/issue-4726-ospf-peer-identity.md                          (add)
```

**Structure Decision**: The identity logic lives in a new package under `src/foundation/persistence/`. The package is a compliant location. Writer and strategy changes stay in existing modules. No file enters a noncompliant directory.

## Architecture

```text
Menu 55, 70, or 225
  -> mistapi SDK call (searchOrgOspfStats or searchSiteOspfStats)
  -> flatten and escape rows
  -> DataExporter.write_with_format_selection()
       CSV leg: unchanged
       SQLite leg: SQLiteDatabaseWriter._process_data
                   -> OspfPeerIdentity.storage_table_name (add _v2)
                   -> OspfPeerIdentity.attach (add misthelper_ospf_peer_key)
                   -> _create_table_and_indexes checks the primary key
                   -> INSERT OR REPLACE into <legacy name>_v2
       Polyglot leg: DatabaseRouter.write
                   -> OspfPeerIdentity.attach (reject on ValueError)
                   -> Redis JSON: key = endpoint + ":" + identity key
                   -> ArangoDB: _key = identity key
```

## File-by-File Change Map

| Action | Path | Change | Requirements |
| - | - | - | - |
| Add | `src/foundation/persistence/identity/__init__.py` | Package marker with a module docstring. | FR-001 |
| Add | `src/foundation/persistence/identity/ospf_peer.py` | Class `OspfPeerIdentity` with `applies`, `storage_table_name`, `identity_key`, `attach`, and `verify_primary_key`. Constants name the two endpoints and the key column. | FR-001 to FR-005, FR-006, FR-008, FR-015 |
| Modify | `src/foundation/support/refactors/endpoint_primary_key_strategies.py` | The `primary_key` of `searchSiteOspfStats` and `searchOrgOspfStats` becomes `["misthelper_ospf_peer_key"]`. Each `description` names the identity. | FR-013, FR-014 |
| Modify | `src/foundation/support/refactors/sqlite_database_writer.py` | `_process_data` renames the table to `<name>_v2` and attaches keys. `_create_table_and_indexes` calls `verify_primary_key` before the schema step. | FR-006 to FR-008, FR-015 |
| Modify | `src/foundation/persistence/db/router.py` | `write` attaches keys after the strategy lookup. A `ValueError` returns a failed write result before any leg runs. | FR-009 to FR-011, FR-003 |
| Add | `tests/unit/db/test_ospf_peer_identity.py` | Sixteen unit tests for the identity class and the strategy names. | FR-001 to FR-005, FR-013 to FR-015 |
| Modify | `tests/unit/config/foundation/support/refactors/data/storage/test_sqlite_database_writer.py` | Four SQLite storage tests added to the existing file. | FR-006 to FR-008, FR-018, SC-001, SC-003, SC-004 |
| Modify | `tests/unit/config/standalone/foundation/persistence/database/test_router.py` | Two router tests added to the existing file. | FR-009 to FR-011, SC-002 |
| Modify | `documentation/operator-guide.md` | A paragraph after the SQLite output row names the `_v2` tables and the legacy rule. | FR-016 |
| Add | `changelog.d/issue-4726-ospf-peer-identity.md` | One `### Fixed` heading and one bullet that names issue #4726. | FR-017 |

## Dependencies

No new package, service, or runtime dependency is added. The identity class uses `hashlib`, `json`, `decimal`, and `logging`. The existing SQLite writer, Redis writer, ArangoDB writer, and router keep their dependencies.

## Implementation Outline

1. Write the failing tests in T001, T002, and T003. Run them. Record the failures.
2. Add the identity class in T004. Its unit tests pass.
3. Change the two strategy entries in T005.
4. Attach the keys and the `_v2` table name in the SQLite writer in T006.
5. Attach the keys in the router in T007.
6. Run the existing export tests in T008. They must pass without any change.
7. Update the operator guide and add the changelog fragment in T009.
8. Run the local gates in T-LOCAL-GATES. Then open the pull request in T-PR.
9. Watch the remote CI in T-REMOTE-CI. Add the auto-merge label in T-MERGE only after the orchestrator authorizes the merge.

## Logic Notes

- The identity key is `ospf_` followed by SHA-256 hex of the canonical payload. The payload is a JSON array with mac, vrf_name or null, port_id or null, neighbor, and timestamp text.
- The timestamp text uses `Decimal` normalization in fixed-point form. The value `1700000000.0` becomes `1700000000`.
- The class checks table names with `sqlite_master` and a bound parameter before it builds a `PRAGMA` statement. It does not suppress a scanner finding.
- The SQLite primary key check reads `PRAGMA table_info`. It compares the primary key columns with `misthelper_ospf_peer_key`.

## Contracts

The folder `design/contracts/` holds three files. `ospf-peer-identity.md` defines the input and the key. `storage-outputs.md` defines the SQLite, Redis, and ArangoDB outputs. `mist-ospf-response.md` defines the API shape that the change reads.

## Complexity Tracking

| Violation or limit | Why needed | Simpler alternative rejected because |
| - | - | - |
| `SQLiteDatabaseWriter` remains a noncompliant class | The writer already owns the SQLite leg. | A new writer class duplicates the table and insert logic. |
| `DatabaseRouter.write` gains about seven lines | The router owns the polyglot dispatch. | A helper method adds a child to a noncompliant class, which the constitution forbids. |
| `DatabaseRouter.write` keeps five logical blocks | The new check adds one `if` and one `try`. | Moving the check into the Redis or ArangoDB writer repeats the check in each leg. |
| `endpoint_primary_key_strategies.py` stays large | The strategy catalog is one dictionary by design. | Splitting the catalog breaks the single source of truth. |

## Risks and Mitigations

| Risk | Mitigation |
| - | - |
| Caution: A live record lacks `neighbor`, so its batch fails. | The error names the component. The fallback to `peer_ip` covers older payloads. Unverified item U-01 records the open question. |
| The shared strategy file gains a conflict. | Run the Preconditions check again in T-PR. Keep the diff to two dictionary entries. |
| The `_v2` table name surprises an operator. | The operator guide names each table (FR-016). The changelog names the change (FR-017). |
| A legacy table with the old primary key receives a write. | The writer writes only to `_v2` tables. Test `test_ospf_legacy_table_is_unchanged_after_v2_write` checks the legacy schema. |
| Caution: A `_v2` table with a wrong primary key could merge rows. | `verify_primary_key` fails the write before any insert (FR-008). |
| The contract test for declared indexes rejects the strategy change. | The contingency adds `misthelper_ospf_peer_key` to the `indexes` list of both entries. Task T005 names the contingency. |
| A bandit finding appears for the `PRAGMA` statement. | Build the statement only from a name that `sqlite_master` returned. Do not suppress the finding. |
| Redis keys from the old format coexist with new keys. | The old keys do not match the new key format. They expire by the TTL (RV-18). |

## Rollback Steps

1. Revert the pull request commit on `main`. The old code writes the old keys again.
2. Do not drop any `_v2` table during a rollback unless the operator approves it. Warning: dropping a `_v2` table deletes every row that the new writer stored.
3. Redis keys with the identity suffix expire by the TTL. They need no action.
4. ArangoDB documents with `ospf_` keys remain. The operator decides whether to remove them.

## Follow-Up Items

The orchestrator files two new issues. Each issue gets one concern.

1. The OSPF graph mapping uses `id` as its key field (RV-20, RV-21). Records without `id` create no OSPF graph vertices.
2. The file `scripts/pk_strategy_suggestions.py` reports "no stable key" for `searchSiteOspfStats` (RV-79). The file is stale. Regenerate it or remove it.
