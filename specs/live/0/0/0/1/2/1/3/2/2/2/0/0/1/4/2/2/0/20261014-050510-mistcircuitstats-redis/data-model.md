# Data Model: MistCircuitStats Redis Dashboard Migration

**Status**: Model for the existing #4252 dashboard, cache, and fail-closed worker.

## Entities

### Organization

| Field | Type | Rule |
|---|---|---|
| `org_id` | Mist organization identifier | Required. Use the active MistHelper organization. |
| `display_name` | Text | Optional. Use a value returned by an authorized source. |

An organization owns sites, gateways, and refresh state. A request cannot select an organization outside the active MistHelper context.

### Site

| Field | Type | Rule |
|---|---|---|
| `site_id` | Mist site identifier | Required. Must belong to the active organization. |
| `org_id` | Mist organization identifier | Required. Must match the active organization. |
| `display_name` | Text | Optional. Use a value returned by Mist. |

The worker reads sites through the existing `listOrgSites` SDK operation.

### Gateway

| Field | Type | Rule |
|---|---|---|
| `gateway_id` | Mist device identifier | Required. Use the stable identifier returned by Mist. |
| `site_id` | Mist site identifier | Required when returned. Must match the gateway record. |
| `org_id` | Mist organization identifier | Required. Must match the active organization. |
| `display_name` | Text | Optional. Do not substitute a MAC address for the gateway identifier. |
| `device_type` | Text | Required when returned. Must identify an eligible gateway. |

The worker reads gateway statistics and inventory through the existing bulk SDK operations.

### WAN Port Observation

| Field | Type | Rule |
|---|---|---|
| `org_id` | Mist organization identifier | Required for authorization and organization isolation. |
| `site_id` | Mist site identifier | Required when returned. Must match the gateway. |
| `gateway_id` | Mist device identifier | Required when returned. Must match the source gateway. |
| `port_id` | Mist port identifier | Required when returned. Do not infer it from display text. |
| `metric_name` | Text | Required when returned. Preserve the source field name. |
| `value` | Number or missing | Preserve missing values as unknown. Do not replace them with zero. |
| `unit` | Text or missing | Preserve the source unit. Do not infer a unit. |
| `observed_at` | UTC timestamp or missing | Preserve a source timestamp. Do not invent one. |
| `collected_at` | UTC timestamp | Required. Record when the worker collects the data. |

The worker reads port records through the existing organization-wide paginated `searchOrgSwOrGwPorts` operation. It selects WAN rows after it reads the bulk pages.

### Snapshot

| Field | Type | Rule |
|---|---|---|
| `schema_version` | Integer | Use the existing #4252 cache schema. Do not create a second versioned namespace. |
| `org_id` | Mist organization identifier | Required. |
| `site_id` | Mist site identifier or organization scope | Preserve the existing cache key scope. |
| `record_type` | Existing cache type | Use the current dashboard cache contract. |
| `record_id` | Mist natural identifier or stable tuple | Use the source identifier. Do not generate a random identifier. |
| `state` | Enumerated text | Use the existing state contract for current, stale, unavailable, or synthetic data. Never publish a partial snapshot. |
| `data_source` | Enumerated text | New worker snapshots use `live`. A synthetic example is not a cache snapshot. |
| `collected_at` | UTC timestamp | Required for live data. |
| `expires_at` | UTC timestamp | Preserve the existing 300-, 600-, or 86,400-second TTL by record type. |
| `records` | List of observations | Validate shape and ownership before publication. |

The worker publishes one schema-versioned envelope at `wan-dashboard:v1:overview:<org_id>:last-success`. The envelope holds the complete overview and its UTC collection time. The worker uses one atomic Redis operation to update the snapshot and matching status. Do not add the historical `misthelper:wan:mcsr:v1:` candidate prefix. The worker may retain a complete process-local memory snapshot for Redis outage reads. It must mark that snapshot stale and enforce the 86,400-second maximum age. Do not add local file storage.

### Refresh Request

| Field | Type | Rule |
|---|---|---|
| `org_id` | Mist organization identifier | Required. Use the active organization. |
| `queued` | Boolean | One Redis queue key represents at most one pending follow-up. |
| `requested_at` | UTC timestamp or missing | Set when the queue accepts a new request. Coalesced requests do not add entries. |

The Refresh control queues work for the single worker. The route does not make a Mist request or write a snapshot. The queue key has a bounded expiry and uses the existing cache namespace.

### Worker Status

| Field | Type | Rule |
|---|---|---|
| `status` | Enumerated text | `disabled`, `unavailable`, `queued`, `running`, `complete`, `stale`, or `failed`. |
| `current_phase` | Bulk-read name or missing | Show the active approved read without raw response data. |
| `completed_pages` | Map of bulk-read name to non-negative integer | Count validated pages completed for each approved read. |
| `requested_at` | UTC timestamp or missing | Show the most recent queue request accepted by this process. |
| `started_at` | UTC timestamp or missing | Show the most recent worker start time. |
| `finished_at` | UTC timestamp or missing | Show the most recent successful or failed run time. |
| `last_complete_at` | UTC timestamp or missing | Time of the last complete snapshot. |
| `next_scheduled_at` | UTC timestamp or missing | Set from the unapproved interval only when the worker is enabled. |
| `safe_error` | Safe code or missing | Use a bounded status code. Never include credentials or raw responses. |
| `stale` | Boolean | True during failure or Redis outage. |
| `queued_follow_up` | Boolean | True when one follow-up is pending. |

## Relationships

- One organization owns many sites.
- One site owns many gateways.
- One gateway may have zero or more WAN port observations.
- One snapshot contains validated records for one organization and its declared scope.
- One refresh request is handled by the single worker.
- One refresh result may publish zero or more complete snapshots.

## Validation and State Rules

1. Validate identifiers before they enter cache keys or SDK arguments.
2. Confirm that each site and gateway belongs to the active organization.
3. Use only the four approved bulk reads and the shared pagination path.
4. Deduplicate records by source natural keys.
5. Preserve missing values as unknown.
6. Publish only after all required pages pass validation.
7. On a rate limit, failed page, incomplete dataset, Redis error, or lease error, preserve the last complete snapshot as stale, show a safe error, and publish no partial data.
8. Keep one active refresh and at most one queued follow-up. Coalesce further requests into that follow-up.
9. Keep portal reads cache-only. On Redis outage, use only an unexpired complete process-local snapshot as stale when available. Otherwise report unavailable data. Do not make a fallback Mist request.
10. Show refresh state, current bulk-read phase, completed page counts, timestamps, and safe error status.
11. Enforce 86,400 seconds as the maximum age, including for process-local memory.
12. Preserve the existing cache namespace and TTLs.
13. Keep per-port Insights parity out of this model. Issue #4330 tracks that work.
14. Keep `WAN_DASHBOARD_LOAD_TEST_APPROVED` false, and leave the refresh interval and renewable worker lease unset until the production-scale load test.
15. Run the production-scale load test during a scheduled maintenance window. Keep collection disabled before that test.
