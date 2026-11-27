# Implementation Plan: Redis device event identity

**Branch**: `fix/4724-redis-device-event-identity` | **Date**: 2026-11-26 | **Spec**: `spec.md`

**Input**: Numeric specification from `specs/numbered/0/0/1/2/2/3/4/4/4724-redis-device-event-identity/spec.md`. The route comes from `Get-SpecRadixSegments` with number 4724 (RC-46, RC-47).

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

The Redis writer stores device events under `id`, `device_id`, and `timestamp` (RC-01). The documented schema has no `id` and no `device_id` (RC-24). The writer then substitutes `unknown` (RC-04). Events that share a timestamp overwrite each other (RC-05). The fix adds a `record_id` digest in the router. It changes the device event key to `record_id`, `org_id`, and `timestamp`. It rejects rows with missing key fields. It also retargets the ArangoDB graph map for device events.

## Technical Context

- **Language/Version**: Python 3.15 or newer (RC-31).
- **Primary Dependencies**: mistapi 0.64.x, the only Mist interface (RC-32, RC-62). redis-py JSON commands (RC-64). The ArangoDB driver used by `ArangoDBWriter`.
- **Storage**: Redis JSON documents with a TTL from `REDIS_JSON_TTL_DAYS`, default seven days (RC-07). ArangoDB collections and graph. CSV and SQLite exports stay unchanged.
- **Testing**: pytest with mocked Redis, ArangoDB, and mistapi (RC-38, RC-39, RC-43). No live service runs in the gates.
- **Target Platform**: Repository runtime. This fix does not change platform code.
- **Project Type**: Persistence package change inside the command-line tool.
- **Performance Goals**: No new goal. The digest adds CPU work for each device event row (research U-7).
- **Constraints**: No new direct child under `src/foundation/persistence/db` or its `writers` folder (RC-36, RC-37). No new module-level name in `router.py`.
- **Scale/Scope**: Menu 21 exports the last 24 hours. Menu 97 exports the last 52 weeks (RC-19, RC-20). Volume is unverified (research U-6).

## Constitution Check

*GATE: Passed before research. Re-checked after design.*

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule | Pass | No new direct child. `db` stays at five and `writers` at two (RC-36, RC-37). |
| II. Class-Based Architecture | Pass | The stamp is a static method on `DatabaseRouter`. No wrapper function is added. |
| III. Safety-First | Pass | Rows with missing key fields are rejected. No prompt and no deletion is added. |
| IV. Full Deployment Pipeline | Pass | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover steps 1 to 9. Steps 10 to 12 follow the merge. |
| V. Observability | Pass | Log lines use ASCII. Rejection logs name the field, never the value. |
| VI. Inline Comments | Pass | Each task requires an inline comment on each changed line. |
| VII. Action Logging | Pass | Each changed action gets an `info` line before it and a `debug` line after it. |
| Mist access through mistapi | Pass | No direct HTTP request is added (RC-62). |
| Python 3.15 | Pass | The version does not change (RC-31). |
| Podman | Not applicable | No container runs for this change. |
| Output backends | Pass | Both backends still receive each row through the router. CSV and SQLite stay unchanged (FR-003). |
| Database keys | Pass with recorded exception | The constitution requires Mist natural keys (RC-66). No Mist field is unique for device events (RC-24, RC-25). The `record_id` digest uses only Mist payload fields. The rogue DHCP `record_id` uses the same pattern (RC-44, RC-45). |
| Data directory | Pass | No output path changes. |
| Documentation | Pass | The design guide, contributor guide, and changelog change (FR-010). README has no Redis key text (research R15). |
| Testing | Pass | Eight test functions cover new and changed behavior (tasks.md). |
| Security findings | Pass | No suppression comment is added. |
| SpecKit escalation | Pass | Four or more files and two classes change. The spec precedes the code. |
| Multi-agent workflow | Pass with precondition | Edit only after the ownership gate passes (decision D-12). |
| Operational store | Not applicable | No coordination record is added. |

## Architecture

```text
Menu 21 or menu 97 -> OrgAlarmEventExporter -> searchOrgDeviceEvents (mistapi)
    -> DataExporter.write_with_format_selection (CSV and SQLite unchanged)
    -> DatabaseRouter.write -> _write_dual
        -> copy each row and add record_id (new)
        -> RedisJSONWriter.write -> key searchOrgDeviceEvents:record_id:org_id:timestamp
        -> ArangoDBWriter.write -> _key record_id, graph vertex keyed by record_id
```

The router keeps the dual write design (RC-09, RC-10). The stamp runs once, so both backends receive the same `record_id`.

## File-by-File Change Map

| Action | Repository path | Change | Remote lines on main |
| - | - | - | - |
| Modify | `src/foundation/persistence/db/router.py` | Add the class attribute `DEVICE_EVENT_API` and a static method that copies rows with `record_id`. Call the method in `_write_dual` for device events. | 99, 351 (RC-10, RC-11) |
| Modify | `src/foundation/persistence/db/writers/redis_writer.py` | Reject rows with missing key fields. Remove the `unknown` sentinel. Count rejected rows as failed. | 603, 618, 632 (RC-04, RC-05, RC-06) |
| Modify | `src/foundation/support/refactors/endpoint_primary_key_strategies.py` | Change the `searchOrgDeviceEvents` primary key, indexes, and description. | 265 to 271 (RC-01, RC-02) |
| Modify | `src/foundation/persistence/db/writers/arango_writer.py` | Use `record_id` as the vertex key and the edge source for device events. | 1487 to 1507 (RC-15, RC-16) |
| Modify | `tests/unit/config/standalone/foundation/persistence/redis/test_redis_json_writer.py` | Add two regression tests. | 61 to 105 (RC-38) |
| Modify | `tests/unit/config/standalone/foundation/persistence/database/test_router.py` | Add three router tests. | 103 (RC-39) |
| Modify | `tests/unit/config/standalone/foundation/persistence/arango_writer/test_arango_writer.py` | Add one graph test beside the vertex tests. | 770 (RC-43) |
| Modify | `tests/unit/config/foundation/persistence/storage/arango_indexes/test_preservation.py` | Add `record_id` to the shared test record. | 29 and 36 (RC-41) |
| Modify | `tests/contract/test_arango_declared_indexes.py` | Expect the Redis writer to receive stamped rows. | 151 to 154 (RC-40) |
| Modify | `documentation/diagrams/core/database-strategy.md` | Update the device event ER block and the table row. | 42 to 50, 137 (RC-28, RC-29) |
| Modify | `.github/copilot-instructions.md` | Update the composite key example row. | 205 (RC-30) |
| Create | `changelog.d/issue-4724-redis-device-event-identity.md` | Add one changelog fragment for the fix. | Naming rule at line 27 (RC-55) |

The following files stay unchanged. Each one was read and checked:

- `tests/unit/config/foundation/persistence/storage/arango_indexes/test_declared_indexes.py` (RC-42).
- `tests/guardrails/test_persistence_package_structure.py` (RC-36, RC-37).
- `MistHelper.py` (RC-19, RC-20). It holds the menu handlers only.

## Dependencies

- No package changes. `requirements.txt` and `pyproject.toml` stay unchanged. The dependency audit gate does not apply.
- No dependency on issues #4721 to #4726 (decision D-2). These issues share files with this change (decision D-12).
- The router already imports `hashlib` and `json`, and it has `_hash_payload` (RC-11).

## Risks and Mitigations

| Risk | Mitigation |
| - | - |
| Caution: a changed payload for one event creates a second document. Both documents remain until the Redis TTL ends. | Record the trade-off in D-1. Measure duplicate counts in a staging run (research U-2). |
| Rows without `org_id` or `timestamp` now fail the Redis write for every composite endpoint that lacks a key field. | Log one line for each rejected row with the field name. Review failure counts after the release (research U-9). |
| The graph gains vertices for device events that had none before. | Review graph size after the release (research U-6). |
| Shared files conflict with issues #4721, #4722, #4723, #4725, and #4726. | Check open pull requests before each edit and before the push. Rebase before the push (decision D-12). |
| Hashing adds CPU cost for each row in large exports. | Reuse the existing `_hash_payload` helper. Measure the cost at 52-week scale (research U-7). |
| Warning: a purge of old Redis keys deletes cached events that Redis cannot restore. | The recommended option keeps the old keys (decision D-7). A purge needs human approval. |
| Warning: a non-unique first key overwrites archived ArangoDB events. | Put `record_id` first (decision D-2). The preservation test checks `_key` (task T008). |
| A symbol gate can flag a new module-level name. | Add no module-level name. Use a class attribute and a static method (decision D-5). |

## Rollback

1. Revert the squash commit on `main` through a new pull request.
2. Redis: documents written with `record_id` expire by TTL. Caution: keys with `record_id` remain until the TTL ends.
3. ArangoDB: documents keep their `record_id` keys. No deletion is needed. Older readers ignore the new field.

## Deployment Notes

After the merge, constitution steps 10 to 12 apply. Wait for the `container-build.yml` run on the merged revision. Verify that the image revision label equals the merged commit SHA. Then deploy the image and check its health. The orchestrator performs these steps.

## Complexity Tracking

Not applicable. The Database Keys exception is recorded in the Constitution Check table.
