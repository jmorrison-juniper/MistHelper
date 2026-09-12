# Endpoint Contract: countSiteRogueEvents

Phase 1 contract record. Authoritative source:
`documentation/api/sites/GET_sites_site_id_rogues_events_count.md` (enriched per-endpoint
doc generated from the Mist OpenAPI 3 spec).

## HTTP Contract

| Field           | Value                                                       |
|-----------------|-------------------------------------------------------------|
| Method          | `GET`                                                       |
| URL template    | `https://{MIST_HOST}/api/v1/sites/{site_id}/rogues/events/count` |
| Required header | `Authorization: Token {MIST_API_TOKEN}`                     |
| Content type    | `application/json` (request body N/A; response JSON)        |
| Idempotent      | Yes                                                         |
| Cacheable       | No (live aggregation; respects standard Mist cache headers) |

### Path parameters

| Name      | Type   | Required | Description                                |
|-----------|--------|----------|--------------------------------------------|
| `site_id` | string | Yes      | UUID of the target site (Mist UUID shape). |

### Query parameters

| Name          | Type    | Required | Default | Description                                                                  |
|---------------|---------|----------|---------|------------------------------------------------------------------------------|
| `distinct`    | string  | No       | `type`  | Attribute to group counts by (`type`, `ssid`, `bssid`, `ap_mac`, `channel`, `seen_on_lan`). |
| `type`        | string  | No       | --      | Filter: rogue category (`honeypot`, `lan`, `others`, `spoof`).               |
| `ssid`        | string  | No       | --      | Filter: SSID of detected threat network.                                     |
| `bssid`       | string  | No       | --      | Filter: BSSID of detected threat network.                                    |
| `ap_mac`      | string  | No       | --      | Filter: MAC of reporting AP with strongest signal.                           |
| `channel`     | string  | No       | --      | Filter: channel on which the AP heard the rogue.                             |
| `seen_on_lan` | boolean | No       | --      | Filter: rogue observed on LAN side.                                          |
| `start`       | string  | No       | --      | Window start (epoch seconds or relative like `-1d`, `-1w`).                  |
| `end`         | string  | No       | --      | Window end (epoch seconds or relative like `now`, `-2h`).                    |
| `duration`    | string  | No       | `1d`    | Window length (e.g. `7d`, `2w`). Mutually compatible with start/end per Mist server-side resolution. |
| `limit`       | integer | No       | `100`   | Max distinct-value buckets in the response.                                  |

### Request body

None.

## Response Contract

### 200 OK -- Result of Count

```json
{
  "distinct": "type",
  "end": 1719676800,
  "limit": 100,
  "results": [
    {"count": 42, "type": "honeypot"},
    {"count": 17, "type": "lan"},
    {"count": 0,  "type": "others"}
  ],
  "start": 1719590400,
  "total": 59
}
```

Top-level schema (required: `distinct`, `end`, `limit`, `results`, `start`, `total`):

| Field      | Type    | Required | Notes                                            |
|------------|---------|----------|--------------------------------------------------|
| `distinct` | string  | Yes      | Echo of the requested or defaulted grouping key. |
| `end`      | integer | Yes      | Epoch seconds (int32) window end.                |
| `limit`    | integer | Yes      | Echo of the requested or defaulted limit.        |
| `results`  | array   | Yes      | Unique-itemed array of `count_result` objects.   |
| `start`    | integer | Yes      | Epoch seconds (int32) window start.              |
| `total`    | integer | Yes      | Total rogue events across all buckets.           |

`count_result` (required: `count`; `additionalProperties: string`):

| Field            | Type    | Required | Notes                                                              |
|------------------|---------|----------|--------------------------------------------------------------------|
| `count`          | integer | Yes      | Number of rogue events in this bucket (int32).                     |
| `<distinct attr>`| string  | No       | One additional property whose name equals the `distinct` value. For `distinct=type` the key is `type` with value `"honeypot"` / `"lan"` / etc.; for `distinct=ssid` the key is `ssid` with the SSID string; and so on. The schema models this via `additionalProperties: {"type": "string"}`. |

## Error Responses

| Status | Meaning                  | MistHelper handling                                                                                  |
|--------|--------------------------|------------------------------------------------------------------------------------------------------|
| 400    | Bad Syntax               | Logged at WARNING with the offending query params; method returns non-zero exit (`1`); no retry.     |
| 401    | Unauthorized             | Logged at ERROR ("API token invalid or expired"); user prompted to refresh `.env`; method returns 2. |
| 403    | Permission Denied        | Logged at ERROR ("Token lacks scope for site %s"); method returns 3; no retry.                       |
| 404    | Not Found                | Logged at WARNING ("Site %s not found or no data"); method returns 0 with empty output; no traceback.|
| 429    | Too Many Requests        | Adaptive delay subsystem (`delay_metrics.json`, `tuning_data.json`) handles back-off and retry; the method does not implement a per-call retry loop. |

All error paths preserve the inline-comment-on-every-line and before/after action
logging contracts; no traceback escapes to the user.

## mistapi SDK Call

```python
# Import path (matches the SDK module hierarchy as of mistapi 0.59+)
from mistapi.api.v1.sites.rogues.events.count import countSiteRogueEvents

# Example invocation (kwargs match the OpenAPI query parameter names exactly)
response = countSiteRogueEvents(
    mist_session,                                 # Existing mistapi.APISession instance
    site_id,                                      # Path parameter (UUID string)
    distinct="type",                              # Grouping attribute (API default)
    duration="1d",                                # Window length (API default)
    # Optional filters -- only pass the ones the user opted into:
    # type="honeypot",
    # ssid="GuestNet",
    # bssid="aa:bb:cc:dd:ee:ff",
    # ap_mac="aabbccddeeff",
    # channel="36",
    # seen_on_lan=True,
    # start="-1d",
    # end="now",
    # limit=100,
)

# response is a mistapi.APIResponse with:
#   response.status_code   -> HTTP status (200 on success)
#   response.data          -> dict matching the 200 schema above
#   response.headers       -> raw response headers (used by the adaptive-delay subsystem)
```

The SDK signature matches the OpenAPI query parameter list one-for-one. The SDK
function name `countSiteRogueEvents` is exposed both at the deep module path
`mistapi.api.v1.sites.rogues.events.count` and (per the enriched doc) at the
shorter alias `mistapi.api.v1.sites.rogues.countSiteRogueEvents`. MistHelper imports
the deep path to keep the SDK surface explicit and unambiguous.

## Pagination

The endpoint accepts `limit` and (per the doc) `page` query parameters; the default
`limit=100` is sufficient because no `distinct` attribute supported by this endpoint
has cardinality approaching 100 in practice (rogue `type` has 4 values; `channel`
covers the 2.4/5/6 GHz channel set). MistHelper therefore does not implement
pagination for this call; if a future use case requires it, the existing
`adaptive_paginate` helper on `RogueDataProcessor` can wrap the SDK call without
schema changes.

## Rate Limiting

Standard Mist API limits apply (5000 calls/hour per token). The adaptive-delay
subsystem reads the `X-RateLimit-Remaining` and `X-RateLimit-Reset` response
headers and adjusts the per-endpoint delay in `delay_metrics.json`. No per-call
sleep is added inside the new method.
