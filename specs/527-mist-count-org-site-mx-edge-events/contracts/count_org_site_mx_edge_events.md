# Contract: countOrgSiteMxEdgeEvents

**Spec**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md) |
**Data Model**: [../data-model.md](../data-model.md)

This contract documents the HTTP, SDK, response, and error surface for the Mist API
endpoint that the new menu item wraps. All facts below are drawn from
`documentation/api/orgs/GET_orgs_org_id_mxedges_events_count.md` (the enriched
per-endpoint doc generated from the Mist OpenAPI 3 specification).

---

## HTTP Contract

| Property | Value |
|----------|-------|
| Method | `GET` |
| URL template | `https://{MIST_HOST}/api/v1/orgs/{org_id}/mxedges/events/count` |
| Auth header | `Authorization: Token {api_token}` (or `X-CSRFToken` cookie) |
| Request body | None |
| Pagination | Bounded by `limit` query parameter (no cursor). No paginated loop. |
| Rate limiting | Standard Mist API 5000 calls/hour per token; 429 honored by adaptive delay. |

### Required Path Parameters

| Name | Type | Format | Notes |
|------|------|--------|-------|
| `org_id` | string | UUID v4 | Mist organization identifier. Validated client-side before the call. |

### Optional Query Parameters

| Name | Type | Default | Notes |
|------|------|---------|-------|
| `distinct` | string | (server default) | Attribute to bucket counts by. Common values: `type`, `service`, `mxedge_id`, `mxcluster_id`. |
| `mxedge_id` | string (UUID) | omitted | Filter to a single Mist Edge. |
| `mxcluster_id` | string (UUID) | omitted | Filter to a single Mist Edge cluster. |
| `type` | string | omitted | Event type name. See Mist `listDeviceEventsDefinitions` constants. |
| `service` | string | omitted | Service running on the mxedge (e.g. `mxagent`, `tunterm`). |
| `start` | string | omitted | Window start. Epoch seconds OR relative string (`-1d`, `-1w`). |
| `end` | string | omitted | Window end. Epoch seconds OR relative string (`-1d`, `-2h`, `now`). |
| `duration` | string | `1d` | Shorthand window like `7d` or `2w`. Mutually exclusive with explicit `start` / `end`. |
| `limit` | integer | `100` | Maximum number of distinct buckets to return. |

### Required Request Headers

| Header | Value |
|--------|-------|
| `Authorization` | `Token {MIST_API_TOKEN}` |
| `Accept` | `application/json` (set by mistapi SDK) |
| `User-Agent` | mistapi-generated (set by SDK; never overridden by MistHelper) |

---

## Response Contract (HTTP 200)

The body is a single JSON object. All six top-level fields are required by the
OpenAPI schema.

```json
{
  "distinct": "type",
  "start": 1751145216,
  "end":   1751231616,
  "limit": 100,
  "total": 842,
  "results": [
    { "count": 412, "type": "reboot" },
    { "count": 188, "type": "config_changed" },
    { "count":  97, "type": "service_restart" }
  ]
}
```

### Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `distinct` | string | yes | Which attribute the counts are grouped by. Echoes the query parameter or the server default when omitted. |
| `start` | integer (epoch seconds) | yes | Server-resolved window start. |
| `end` | integer (epoch seconds) | yes | Server-resolved window end. |
| `limit` | integer | yes | Server-honored max bucket count. |
| `total` | integer | yes | Sum of `count` across all buckets in the window (NOT bounded by `limit`). |
| `results` | array<object> | yes | Unique array of count buckets. Empty array when no events match the filters. |

### `results[]` Element (`count_result`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `count` | integer | yes | Number of events in this bucket. |
| `<distinct_field>` | string | yes (dynamic) | Bucket key; the field name matches the requested `distinct` value (e.g. `type`, `service`, `mxedge_id`, `mxcluster_id`). |
| `<extra_property>` | string | no | The OpenAPI schema marks `additionalProperties: type=string`; the server MAY return composite-bucket fields beyond the primary distinct key. MistHelper preserves these in the `extra_properties_json` column (see `data-model.md`). |

---

## Error Response Contract

| Status | Cause | MistHelper Handling |
|--------|-------|---------------------|
| `400 Bad Syntax` | Malformed query parameter (e.g. invalid `duration`). | Log `WARNING` with the offending parameter name; do not retry; return without writing. |
| `401 Unauthorized` | Missing or invalid `MIST_API_TOKEN`. | Log `ERROR` once; abort the menu item; do not retry. Token never appears in the log message. |
| `403 Permission Denied` | Token lacks read scope on the org. | Log `ERROR` with the org_id; abort the menu item; do not retry. |
| `404 Not Found` | Unknown `org_id` or path. | Log `WARNING` with the org_id; return without writing; exit cleanly with code 0. |
| `429 Too Many Requests` | Hourly rate limit exceeded. | Surface to the adaptive delay system (`delay_metrics.json` + `tuning_data.json`); the SDK retry helper backs off and re-tries up to the configured cap. After exhaustion, log `ERROR` and return. |
| `5xx` | Mist upstream failure. | Log `ERROR` with status code; the SDK retry helper applies its exponential backoff; after exhaustion log `ERROR` and return. |

In all error cases the method exits the function cleanly (no traceback escapes to the
menu loop) and the menu loop continues to its next prompt. This satisfies User Story 1
Acceptance Scenario 2 ("EOF handled gracefully and the operation exits 0 without a
traceback").

---

## mistapi SDK Python Call Signature

The fully-qualified import path declared in `spec.md` is the authoritative module:

```python
import mistapi
from mistapi.api.v1.orgs.mxedges.events import count as mxedge_events_count_module

response = mxedge_events_count_module.countOrgSiteMxEdgeEvents(
    mist_session,            # mistapi.APISession built from MIST_HOST + MIST_API_TOKEN (.env)
    org_id,                  # required path parameter (UUID string)
    distinct=distinct,       # optional, default server-side
    mxedge_id=mxedge_id,     # optional, default omit
    mxcluster_id=mxcluster_id,  # optional, default omit
    type=event_type,         # optional, default omit
    service=service,         # optional, default omit
    start=start_epoch,       # optional, default omit (server defaults to now-duration)
    end=end_epoch,           # optional, default omit (server defaults to now)
    duration=duration,       # optional, default "1d"
    limit=limit,             # optional, default 100
)
body = response.data         # decoded JSON envelope dict
```

`mist_session` is the shared `mistapi.APISession` instance the surrounding class holds
on `self.mist_session`; it is constructed once at application startup from `.env`
values and never re-built per call. The `response` is a `mistapi.APIResponse` whose
`.data` attribute is the decoded JSON body.

### Equivalent Re-Exported Alias

The enriched documentation lists an alias path
`mistapi.api.v1.orgs.mxedges.countOrgSiteMxEdgeEvents()`. Both paths point at the same
generated function via mistapi's nested-module re-export. The implementation uses the
canonical path declared in `spec.md` for forward compatibility; an existing import in
`MistHelper.py` that happens to use the alias is acceptable but should be migrated to
the canonical path during this PR.

---

## Idempotency and Side Effects

- **Idempotency**: Repeated calls with identical inputs produce identical responses
  modulo new events occurring in the underlying window. Re-running the menu item
  upserts cleanly under the composite primary key registered in
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` (see `data-model.md`).
- **Side effects (server-side)**: None. The endpoint is read-only.
- **Side effects (client-side)**: Updates `data/org_mxedge_events_count_summary.*`,
  `data/org_mxedge_events_count_results.*`, the SQLite tables, optional ArangoDB
  collections, optional Redis cache, and `data/script.log`. No other files are
  touched.

---

## Acceptance Test Outline

The implementing PR adds (or extends) an integration test that:

1. Sets `distinct=type`, `duration=1d`, `limit=100` and a known org from `.env`.
2. Invokes the new menu method.
3. Asserts the call returned a dict with all six required top-level fields.
4. Asserts `len(body['results']) <= body['limit']`.
5. Asserts the SQLite row count in `org_mxedge_events_count_results` equals
   `len(body['results'])` after the run.
6. Re-runs the menu method with identical inputs and asserts the SQLite row count
   does NOT double (upsert verified).
