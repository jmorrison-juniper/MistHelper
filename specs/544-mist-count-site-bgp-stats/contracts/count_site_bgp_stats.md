# Endpoint Contract: countSiteBgpStats

**Spec**: [../spec.md](../spec.md)
**Plan**: [../plan.md](../plan.md)
**Source doc**: `documentation/api/sites/GET_sites_site_id_stats_bgp_peers_count.md`
**Date**: 2026-06-29

## HTTP Contract

| Attribute       | Value                                                                |
|-----------------|----------------------------------------------------------------------|
| **Method**      | `GET`                                                                |
| **URL**         | `https://{mist_host}/api/v1/sites/{site_id}/stats/bgp_peers/count`   |
| **Auth**        | `Authorization: Token {api_token}` header (provided automatically by `mistapi.APISession`) |
| **Tag**         | `Sites Stats - BGP Peers`                                            |
| **operationId** | `countSiteBgpStats`                                                  |

### Path Parameters

| Name      | Type          | Required | Description |
|-----------|---------------|----------|-------------|
| `site_id` | string (UUID) | Yes      | Site UUID. Validated client-side by MistHelper via `is_valid_uuid()` before the call. |

### Query Parameters

| Name       | Type    | Required | Default        | Description |
|------------|---------|----------|----------------|-------------|
| `state`    | string  | No       | (absent)       | BGP peer state filter applied **before** counting (e.g. `Established`). When omitted the count covers all states. |
| `distinct` | string  | No       | server-side    | Attribute to group by (e.g. `state`, `neighbor_as`, `vrf_name`, `type`). The exact accepted values are determined by the API; MistHelper passes the user's string verbatim. The API echoes the chosen field back in the response top-level `distinct` key. |
| `limit`    | integer | No       | `100`          | Maximum number of bucket rows returned. MistHelper clamps user input to `[1, 1000]` before the SDK call. |

### Request Headers

| Header          | Value                | Notes |
|-----------------|----------------------|-------|
| `Authorization` | `Token <api_token>`  | Injected by `mistapi.APISession` from `.env`. Never logged. |
| `Accept`        | `application/json`   | Default for mistapi SDK. |
| `User-Agent`    | `mistapi/<version>`  | Set by SDK. |

### Request Body

None. This is a GET.

## Response Contract

### 200 OK

```json
{
  "distinct": "state",
  "start": 1719500000,
  "end": 1719600000,
  "limit": 100,
  "total": 4,
  "results": [
    {"state": "Established", "count": 12},
    {"state": "Idle",        "count": 1},
    {"state": "OpenConfirm", "count": 0},
    {"state": "Active",      "count": 2}
  ]
}
```

| Field            | Type     | Description |
|------------------|----------|-------------|
| `distinct`       | string   | The attribute the API grouped by (echoes the request's `distinct` query parameter or the server-side default). |
| `start`          | int32 (epoch seconds) | Start of the time window the count covers. |
| `end`            | int32 (epoch seconds) | End of the time window the count covers. |
| `limit`          | int32    | The effective row limit applied to `results`. |
| `total`          | int32    | Total number of buckets available (may exceed `limit`). |
| `results`        | object[] | Bucket rows. `uniqueItems=true` per the OpenAPI schema. Each item: `{count: int32, <distinct_field>: string}` -- the bucket label is held under a property whose name equals the value of the top-level `distinct` field, plus any additional string properties the API chooses to attach. |
| `results[].count` | int32   | Required. The bucket count. |
| `results[].<distinct_field>` | string | The bucket label (e.g. `"Established"` when `distinct=state`). |

MistHelper extracts `<distinct_field>` generically: for each bucket dict, the single
non-`count` key is taken as `distinct_value`. This avoids hard-coding the set of
distinct fields the API might support.

### Error Responses

| Status | Mist Description                                                | MistHelper Handling |
|--------|-----------------------------------------------------------------|---------------------|
| 400    | Bad Syntax                                                      | Log `WARNING` ("Mist returned 400 -- check site_id / distinct / limit"), no traceback, return early. |
| 401    | Unauthorized                                                    | Log `ERROR` ("Mist 401 -- check MIST_API_TOKEN in .env"). Do not retry. Return early. |
| 403    | Permission Denied                                               | Log `ERROR` ("Mist 403 -- token lacks read access to site %s", site_id). Return early. |
| 404    | Not found. Endpoint or resource does not exist                  | Log `WARNING` ("No BGP stats for site %s (404)", site_id). Treat as empty result and write zero rows. Return cleanly. |
| 429    | Too Many Requests (5000 calls/hour token threshold exceeded)    | Adaptive delay system (`delay_metrics.json` + `tuning_data.json`) backs off and retries automatically up to the configured retry cap. No user intervention. |

All non-200 responses are surfaced as ASCII log lines only. The API token is never
included in any log message, even at `DEBUG`.

## mistapi Python SDK Call Signature

```python
import mistapi
from mistapi.api.v1.sites.stats.bgp_peers import count as bgp_count_module

apisession = mistapi.APISession(host=os.environ["MIST_HOST"],
                                apitoken=os.environ["MIST_API_TOKEN"])
apisession.login()

# Default count (groups by server-side default, state filter off, limit 100):
response = bgp_count_module.countSiteBgpStats(
    apisession,
    site_id="0a1b2c3d-1234-5678-9abc-def012345678",
)

# Explicit grouping by BGP state, no state filter, default limit:
response = bgp_count_module.countSiteBgpStats(
    apisession,
    site_id="0a1b2c3d-1234-5678-9abc-def012345678",
    distinct="state",
)

# Count only Established peers grouped by neighbor_as, capped at 50 rows:
response = bgp_count_module.countSiteBgpStats(
    apisession,
    site_id="0a1b2c3d-1234-5678-9abc-def012345678",
    state="Established",
    distinct="neighbor_as",
    limit=50,
)

# Access the parsed body:
body = response.data           # dict matching the 200 OK schema above
http_status = response.status_code
```

Notes:

- The SDK module path mirrors the OpenAPI URL path (`/sites/{site_id}/stats/bgp_peers/
  count` -> `mistapi.api.v1.sites.stats.bgp_peers.count`). The enriched per-endpoint doc
  lists the SDK as `mistapi.api.v1.sites.stats_-_bgp_peers.countSiteBgpStats()`; Python
  cannot import a module name containing `-`, so the runtime path is the URL-derived
  form. Final verification happens at implementation time via
  `python -c "from mistapi.api.v1.sites.stats.bgp_peers import count; help(count)"`
  inside the venv.
- `response.data` is `None` only when the HTTP response had no body (rare on a count
  endpoint). MistHelper normalizes this to `{}` before flattening.
- Pass `state=None` (the default) to omit the state filter. Pass an explicit Python
  string (e.g. `"Established"`) to filter.
- Pass `distinct=None` to use the API's server-side default grouping. Pass an explicit
  string to group by a specific attribute. MistHelper uses `"state"` as the prompt
  default.
- `limit` is sent as a Python int. MistHelper clamps user input to `[1, 1000]` before
  the call.

## Pagination

The endpoint's response carries `start`, `end`, `limit`, and `total` fields, and the
enriched doc notes pagination via `limit` / `page` is supported. In practice the count
endpoint returns a single page of bucket rows -- pagination only matters when the number
of distinct buckets exceeds `limit` (rare for BGP attributes). MistHelper's initial
implementation does not iterate pages; if a deployment observes `total > limit` in the
wild, a follow-up spec adds a `page` loop. The current contract bounds `limit` at 1000
which covers operational reality.

## Rate Limiting

Standard Mist API rate limit: 5000 calls per token per hour. MistHelper's adaptive delay
system (`delay_metrics.json` per-endpoint state + `tuning_data.json` learning) governs
back-off automatically. No endpoint-specific tuning required for this contract.
