# Endpoint Contract: countSiteSystemEvents

**Spec**: [../spec.md](../spec.md)
**Plan**: [../plan.md](../plan.md)
**Source doc**: `documentation/api/sites/GET_sites_site_id_events_system_count.md`
**Date**: 2026-06-29

## HTTP Contract

| Attribute       | Value                                                               |
|-----------------|---------------------------------------------------------------------|
| **Method**      | `GET`                                                               |
| **URL**         | `https://{mist_host}/api/v1/sites/{site_id}/events/system/count`    |
| **Auth**        | `Authorization: Token {api_token}` header (provided automatically by `mistapi.APISession`) |
| **Tag**         | `Sites Events`                                                      |
| **operationId** | `countSiteSystemEvents`                                             |

### Path Parameters

| Name      | Type          | Required | Description                                                                                            |
|-----------|---------------|----------|--------------------------------------------------------------------------------------------------------|
| `site_id` | string (UUID) | Yes      | Site UUID. Validated client-side by MistHelper via `is_valid_uuid()` before the call.                  |

### Query Parameters

| Name       | Type    | Required | Default  | Description |
|------------|---------|----------|----------|-------------|
| `distinct` | string  | No       | (server) | Attribute to bucket the count by (e.g., `type`, `device_type`, `model`). Echoed back in the response body. |
| `type`     | string  | No       | (none)   | Filter to a specific event type. Cross-reference List Device Events Definitions. |
| `start`    | string  | No       | (none)   | Start time. Epoch seconds OR relative shorthand like `-1d`, `-1w`. |
| `end`      | string  | No       | (none)   | End time. Epoch seconds OR relative shorthand like `-1h`, `now`. |
| `duration` | string  | No       | `1d`     | Window length shorthand like `7d`, `2w`. Ignored when both `start` and `end` are supplied. |
| `limit`    | integer | No       | `100`    | Maximum number of distinct-value buckets returned. |

### Request Headers

| Header           | Value                                  | Notes |
|------------------|----------------------------------------|-------|
| `Authorization`  | `Token <api_token>`                    | Injected by `mistapi.APISession` from `.env`. Never logged. |
| `Accept`         | `application/json`                     | Default for mistapi SDK. |
| `User-Agent`     | `mistapi/<version>`                    | Set by SDK. |

### Request Body

None. This is a GET.

## Response Contract

### 200 OK

```json
{
  "distinct": "type",
  "start": 1719513600,
  "end": 1719600000,
  "limit": 100,
  "total": 1487,
  "results": [
    { "type": "AP_RESTARTED",            "count": 412 },
    { "type": "AP_CONFIG_CHANGED",       "count": 380 },
    { "type": "GW_CONFIG_GENERATED",     "count": 295 },
    { "type": "SW_RESTARTED",            "count": 210 },
    { "type": "AP_DISCONNECTED",         "count": 190 }
  ]
}
```

| Field      | Type     | Description |
|------------|----------|-------------|
| `distinct` | string   | Echoes the `distinct` query parameter that was applied (the attribute name the count is grouped by). |
| `start`    | int32 (epoch seconds) | Start of the time window the count covers. |
| `end`      | int32 (epoch seconds) | End of the time window the count covers. |
| `limit`    | int32    | The bucket cap that was applied. |
| `total`    | int32    | Total events counted across all buckets in the window. |
| `results`  | object[] | One object per distinct-value bucket. Required field `count` (int32). Additional properties are strings -- the OpenAPI schema declares `additionalProperties: {type: string}`. The bucket's distinct-attribute value is carried as a dynamic property whose name equals the top-level `distinct` value (e.g., when `distinct=type`, each bucket has a `type` field carrying the event-type string). |

The `results` array is declared `uniqueItems: true`, so MistHelper does not need to
de-duplicate buckets within a single response.

### Error Responses

| Status | Mist Description                                                   | MistHelper Handling |
|--------|--------------------------------------------------------------------|---------------------|
| 400    | Bad Syntax                                                         | Log `WARNING` ("Mist returned 400 -- check distinct/type/window parameters"), no traceback, return early. |
| 401    | Unauthorized                                                       | Log `ERROR` ("Mist 401 -- check MIST_API_TOKEN in .env"). Do not retry. Return early. |
| 403    | Permission Denied                                                  | Log `ERROR` ("Mist 403 -- token lacks read access to site %s", site_id). Return early. |
| 404    | Not found. Endpoint or resource does not exist                     | Log `WARNING` ("No system-events count available for site %s", site_id). Treat as empty result, write zero rows, return cleanly. |
| 429    | Too Many Requests (5000 calls/hour token threshold exceeded)       | Adaptive delay system (`delay_metrics.json` + `tuning_data.json`) backs off and retries automatically up to the configured retry cap. No user intervention. |

All non-200 responses are surfaced as ASCII log lines only. The API token is never
included in any log message, even at `DEBUG`. Full request URLs (which would expose
the token only if mis-handled) are also never logged.

## mistapi Python SDK Call Signature

```python
import mistapi
from mistapi.api.v1.sites.events.system import count as count_module

apisession = mistapi.APISession(host=os.environ["MIST_HOST"],
                                apitoken=os.environ["MIST_API_TOKEN"])
apisession.login()

# Bucket by event type over the last 1 day (defaults):
response = count_module.countSiteSystemEvents(
    apisession,
    site_id="0a1b2c3d-1234-5678-9abc-def012345678",
)

# Bucket by device_type over the last 7 days, only AP_RESTARTED events:
response = count_module.countSiteSystemEvents(
    apisession,
    site_id="0a1b2c3d-1234-5678-9abc-def012345678",
    distinct="device_type",
    type="AP_RESTARTED",
    duration="7d",
    limit=50,
)

# Access the parsed body:
body = response.data           # dict matching the 200 OK schema above
http_status = response.status_code
```

Notes:

- The SDK module path mirrors the OpenAPI URL path
  (`/sites/{site_id}/events/system/count` ->
  `mistapi.api.v1.sites.events.system.count`) per the spec.md. The enriched
  per-endpoint doc shows the SDK function at the abbreviated path
  `mistapi.api.v1.sites.events.countSiteSystemEvents`; if the URL-derived path is
  not exposed at import time, the import statement is the single line that needs
  adjustment. Final verification at implementation via
  `python -c "from mistapi.api.v1.sites.events.system import count; help(count)"`.
- `response.data` is `None` only when the HTTP response had no body (rare).
  MistHelper normalizes this to `{}` before flattening.
- The SDK serializes Python `None` keyword arguments by *omitting* the corresponding
  query parameter, so `type=None` does not add `?type=` to the URL. MistHelper
  exploits this by translating a blank prompt answer to `None`.
- The `start` and `end` parameters are accepted as either Python `int` (epoch
  seconds) or `str` (relative shorthand). In the first iteration MistHelper passes
  only `duration` and leaves `start`/`end` unset.

## Pagination

The endpoint is technically paginated (per the doc footer) but in practice the
bucket count is capped by `limit` (default 100). MistHelper does not page through
additional bucket sets in the first iteration -- the dominant use case is a single
page of distinct values. If a larger `limit` is needed, the operator passes it via
the future `--limit` flag without changing the contract.

## Rate Limiting

Standard Mist API rate limit: 5000 calls per token per hour. MistHelper's adaptive
delay system (`delay_metrics.json` per-endpoint state + `tuning_data.json` learning)
governs back-off automatically. No endpoint-specific tuning required for this
contract.
