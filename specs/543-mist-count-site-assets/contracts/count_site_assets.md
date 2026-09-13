# Contract: countSiteAssets

Phase 1 HTTP + SDK contract for the new menu item. Source of truth:
`documentation/api/sites/GET_sites_site_id_stats_assets_count.md`.

## HTTP Contract

- **Method**: `GET`
- **URL template**: `https://{MIST_HOST}/api/v1/sites/{site_id}/stats/assets/count`
- **Authentication**: `Authorization: Token {MIST_API_TOKEN}` (loaded from
  `.env` by `mistapi.APISession`). The token is never logged.
- **Content-Type**: not required for GET.
- **Request body**: none.

### Path Parameters

| Name    | Type   | Required | Notes                          |
|---------|--------|----------|--------------------------------|
| site_id | string | Yes      | Mist site UUID. Validated by MistHelper before the call. |

### Query Parameters

| Name     | Type    | Required | Default | Notes |
|----------|---------|----------|---------|-------|
| distinct | string  | No       | (SDK default) | Distinct attribute to group counts by (e.g. `map_id`, `floor_id`). Empty string treated as "use SDK default". |
| limit    | integer | No       | 100     | Page size; max 1000 enforced client-side by MistHelper. |

### Headers

| Header | Source | Notes |
|--------|--------|-------|
| Authorization | `.env` | `Token {MIST_API_TOKEN}` -- set by mistapi.APISession. |
| Accept | mistapi default | `application/json`. |
| User-Agent | mistapi default | Identifies the SDK version. |

## Response Schema (200 OK)

```json
{
  "type": "object",
  "required": ["distinct", "end", "limit", "results", "start", "total"],
  "properties": {
    "distinct": { "type": "string" },
    "start":    { "type": "integer", "contentEncoding": "int32" },
    "end":      { "type": "integer", "contentEncoding": "int32" },
    "limit":    { "type": "integer", "contentEncoding": "int32" },
    "total":    { "type": "integer", "contentEncoding": "int32" },
    "results": {
      "type": "array",
      "uniqueItems": true,
      "items": {
        "title": "count_result",
        "type": "object",
        "required": ["count"],
        "properties": {
          "count": { "type": "integer", "contentEncoding": "int32" }
        },
        "additionalProperties": { "type": "string" }
      }
    }
  }
}
```

Notes:

- `results[i]` always has a `count` field; the additional string properties are
  the distinct attribute key/value pairs (for example
  `{"count": 12, "map_id": "abc-uuid"}`). The MistHelper flattener emits the
  distinct value as the `bucket_value` column.
- An empty `results: []` is a valid 200 response and is logged at WARNING
  level by MistHelper ("countSiteAssets returned no buckets for site %s").

## Error Responses

| Status | Meaning | MistHelper Handling |
|--------|---------|---------------------|
| 400    | Bad Syntax | Log ERROR with the sanitized request summary (no token). Return without writing files. |
| 401    | Unauthorized | Log ERROR ("Mist API token rejected -- check .env"). Return; do not retry. |
| 403    | Permission Denied | Log ERROR ("Token lacks read on site %s"). Return. |
| 404    | Not Found | Log WARNING ("site %s not found"). Return without writing files. |
| 429    | Rate Limited | Adaptive delay system (delay_metrics.json + tuning_data.json) handles back-off; the SDK retries transparently per the existing retry policy. |
| 5xx    | Server error | Retry once with exponential back-off; on second failure log ERROR with `logging.exception` and return. |

All error paths exit the method with no traceback surfaced to the user; the menu
loop continues normally.

## mistapi Python Call Signature

```python
import mistapi
from mistapi.api.v1.sites.stats_-_assets import countSiteAssets

# self.apisession is the mistapi.APISession built from .env at startup.
response = countSiteAssets(
    self.apisession,
    site_id,                 # required path param (str, UUID)
    distinct=distinct,       # optional query param (str or None)
    limit=limit,             # optional query param (int, 1..1000)
)

# response is a mistapi.APIResponse. Access:
payload   = response.data           # dict matching the schema above
status    = response.status_code    # int (200, 401, etc.)
raw_resp  = response.raw_data       # original requests.Response if needed
```

The function call is the only network operation in the new menu method. All
flattening, validation, and persistence happen locally and do not perform
additional HTTP traffic.

## Pagination Behavior

The endpoint supports `limit` and `page`. For a count endpoint the total bucket
count is typically small (< 100), so MistHelper makes a single call with the
user-supplied or default `limit` and does not loop on `page`. If `payload.total
> payload.limit` the menu method logs a WARNING advising the user to raise
`limit` on the next run.

## Related Endpoints

- `listSiteAssets` (`GET /api/v1/sites/{site_id}/stats/assets`)
- `searchSiteAssets` (`GET /api/v1/sites/{site_id}/stats/assets/search`)

Both return per-asset records; `countSiteAssets` is the aggregate sibling.
