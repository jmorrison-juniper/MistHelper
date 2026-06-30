# Contract: countSiteDeviceLastConfig

Source of truth:
`documentation/api/sites/GET_sites_site_id_devices_last_config_count.md`.

## HTTP

- **Method**: `GET`
- **URL template**: `https://{MIST_HOST}/api/v1/sites/{site_id}/devices/last_config/count`
- **Authentication**: `Authorization: Token {MIST_API_TOKEN}` header (or
  `X-CSRFToken` cookie for web sessions). MistHelper supplies the header
  automatically through `mistapi.APISession`.

### Required path parameters

| Name      | Type   | Notes |
|-----------|--------|-------|
| `site_id` | string (UUID) | Mist site identifier; validated against the standard UUID pattern before the SDK call. |

### Optional query parameters

| Name       | Type    | Default | Notes |
|------------|---------|---------|-------|
| `distinct` | string  | (unset) | Field to group counts by (e.g. `hostname`, `version`, `device_type`). When unset, the response returns a single aggregate row. |
| `start`    | string  | (unset) | Epoch seconds or relative string (`-1d`, `-1w`). Mutually compatible with `end` / `duration`. |
| `end`      | string  | (unset) | Epoch seconds or relative string (`-1h`, `now`). |
| `duration` | string  | `1d`    | Convenience window (e.g. `7d`, `2w`). MistHelper exposes this prompt rather than the raw `start` / `end`. |
| `limit`    | integer | 100     | Max number of `results[]` entries. MistHelper clamps to `[1, 1000]` before the SDK call. |
| `page`     | integer | 1       | Used internally when `total > limit`; not exposed to the operator in v1. |

### Required request headers

- `Authorization: Token <MIST_API_TOKEN>` -- set by `mistapi.APISession`.
- `Accept: application/json` -- set by mistapi.
- `User-Agent: mistapi/<version>` -- set by mistapi.

No request body.

## Response

### 200 OK

```json
{
  "distinct": "hostname",
  "start": 1719600000,
  "end":   1719686400,
  "duration": "1d",
  "limit": 100,
  "total": 42,
  "results": [
    { "count": 14, "hostname": "switch-a" },
    { "count": 13, "hostname": "switch-b" },
    { "count": 15, "hostname": "switch-c" }
  ]
}
```

Schema (from the enriched documentation file):

| Field      | Type          | Required | Description |
|------------|---------------|----------|-------------|
| `distinct` | string        | yes      | Echoes the request `distinct` value (or empty string). |
| `start`    | integer (int32) | yes    | Resolved start epoch seconds. |
| `end`      | integer (int32) | yes    | Resolved end epoch seconds. |
| `limit`    | integer (int32) | yes    | Echoes the request `limit`. |
| `total`    | integer (int32) | yes    | Total matching config-history records in the window. |
| `results`  | array         | yes      | Per-group counts. Each element: `count` (integer, required) plus one free-form key whose name matches `distinct` and whose value is a string (`additionalProperties.type = "string"`). |

When `distinct` is unset, `results` typically contains zero or one element
(an aggregate count) and `total` carries the full count.

### Error responses

| Status | Meaning | MistHelper handling |
|--------|---------|---------------------|
| 400 Bad Syntax       | Malformed query (e.g. unparseable `duration`) | Log WARNING with the request-side parameters; return without writing output; do not raise. |
| 401 Unauthorized     | API token missing or expired                  | Log ERROR; instruct the operator to refresh `MIST_API_TOKEN` in `.env`; return without writing output. |
| 403 Permission Denied | Token lacks read access for this site        | Log ERROR with the site_id (no token); return without writing output. |
| 404 Not Found        | site_id does not exist                        | Log WARNING ("site_id %s not found"); return without writing output. |
| 429 Too Many Requests | Hourly 5000-call quota reached               | Hand off to the adaptive delay system (`delay_metrics.json` + `tuning_data.json`); single retry after back-off; on second 429, log WARNING and return. |
| 5xx                  | Mist server error                             | Log ERROR with the upstream status; rely on mistapi's built-in retry; return on persistent failure. |

All error paths preserve exit code 0 from the menu method itself; the caller
(menu loop) continues. Tracebacks are suppressed by catching the relevant
mistapi exception types and logging via `logging.exception()`.

## mistapi SDK call signature

```python
import mistapi
from mistapi.api.v1.sites.devices.last_config import count as _count_mod

response = _count_mod.countSiteDeviceLastConfig(           # Single SDK call per invocation
    apisession,                                            # mistapi.APISession created at MistHelper startup
    site_id=site_id,                                       # Required path param (UUID string)
    distinct=distinct or None,                             # None when operator left blank
    start=None,                                            # v1: not exposed to operator
    end=None,                                              # v1: not exposed to operator
    duration=duration,                                     # Default "1d" or operator override
    limit=limit,                                           # Clamped to [1, 1000] before this call
    page=1,                                                # Only altered when total > limit
)

body = response.data                                       # Decoded JSON dict (None on transport error)
```

`response.status_code` is consulted before `response.data` to map the error
table above. `response.headers` carries the rate-limit headers
(`X-RateLimit-Remaining`, `X-RateLimit-Reset`) that the adaptive delay
system reads.

## Idempotency and side effects

The endpoint is read-only. Repeated identical requests return identical
counts (subject to new device events arriving in the window). MistHelper's
`composite_pk` upsert pattern guarantees no SQLite duplicates across
repeated runs with the same (site_id, distinct, window_start, window_end)
tuple.
