# Data Model: Redis device event identity

This model covers the entities that the fix reads or writes. The Mist fields come from the local OpenAPI file, and the remote copy matches it (RC-24, RC-25).

## DeviceEvent (documented, read only)

The source is one row of `searchOrgDeviceEvents`. The schema forbids extra properties and defines no `id` and no `device_id` (RC-24).

| Field | Type | Constraint |
| - | - | - |
| `org_id` | identifier text | Required. Names the organization. |
| `timestamp` | time value | Required. Names the time of the event. |
| `type` | text | Required. Names the device event type. |
| `mac` | text | Optional. Names the device MAC address. Used by the strategy index and the device edge. |
| `site_id` | identifier text | Optional. Names the site. Used by the strategy index and the site edge. |

Natural key: none in the documented schema.

## DeviceEventRecord (router copy)

The router copies each DeviceEvent and adds one field. The copy goes to both backends. The caller's row does not change (FR-003, RC-11).

| Field | Type | Constraint |
| - | - | - |
| `record_id` | text | Exactly 64 lowercase hexadecimal characters. The SHA-256 digest of the canonical JSON of the received row. |
| All DeviceEvent fields | As received | Unchanged. |

Natural key: `record_id`. It is computed from the Mist payload. It is not a Mist identifier (RC-66 exception in plan.md).

## RedisDocument

| Part | Value | Source |
| - | - | - |
| Key | `searchOrgDeviceEvents:<record_id>:<org_id>:<timestamp>` | Strategy order (RC-01 changes to this order). |
| Value | JSON document holding the DeviceEventRecord | Written with the root path `$` (RC-05). |
| TTL | Seven days by default | `REDIS_JSON_TTL_DAYS` (RC-07). |

State transitions:

1. Absent to present: the first write creates the document.
2. Present to present: a write with the same key replaces the document. The digest makes the replacement identical.
3. Present to absent: the TTL ends. This change adds no delete operation.

## ArangoDocument (device event collection)

| Part | Value | Source |
| - | - | - |
| `_key` | The `record_id` value | First key field rule (RC-13). |
| Other fields | The DeviceEventRecord fields | Written by the existing writer path. |

State transitions:

1. Absent to present: the first write creates the document.
2. Present to present: a write with the same `_key` replaces the document.
3. No transition to absent occurs in this change.

## Graph vertex and edges (device events)

| Part | Value | Source |
| - | - | - |
| Vertex key | `record_id` | Map key field (RC-15 changes to `record_id`). |
| Site edge | From the vertex by `record_id` to the site by `site_id` | Edge source changes from `id` (RC-16). |
| Device edge | From the vertex by `record_id` to the device by `mac` lookup | Lookup on `mac` (RC-17). |

Vertices without a key field are skipped (RC-14). This change gives every record with `record_id` a vertex.

## WriteResult and DualWriteResult

| Field | Meaning | Source |
| - | - | - |
| `success` | True only when every backend result succeeds | RC-12 |
| `records_written` | Count of successful writes | RC-06 |
| `records_failed` | Count of rejected rows and failed writes | Decision D-3 |
| `backend` | Name of the write path, such as `redis_json`, `arangodb`, or `dual` | Dataclass in `src/foundation/persistence/db/__init__.py` (RC-12) |

State transitions: none. A result is a value, and the router builds a new value for each write.
