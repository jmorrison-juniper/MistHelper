# Endpoint Contract: countSiteDeviceConfigHistory

**Spec**: [../spec.md](../spec.md)
**Plan**: [../plan.md](../plan.md)
**Source doc**: `documentation/api/sites/GET_sites_site_id_devices_config_history_count.md`
**Date**: 2026-06-29

## HTTP Contract

| Attribute       | Value                                                                                  |
|-----------------|----------------------------------------------------------------------------------------|
| **Method**      | `GET`                                                                                  |
| **URL**         | `https://{mist_host}/api/v1/sites/{site_id}/devices/config_history/count`              |
| **Auth**        | `Authorization: Token {api_token}` header (injected automatically by `mistapi.APISession`) |
| **Tag**         | `Sites Devices`                                                                        |
| **operationId** | `countSiteDeviceConfigHistory`                                                         |

### Path Parameters

| Name      | Type          | Required | Description                                                                                                       |
|-----------|---------------|----------|-------------------------------------------------------------------------------------------------------------------|
| `site_id` | string (UUID) | Yes      | Site UUID. Validated client-side by MistHelper via `is_valid_uuid()` before the call; invalid input returns early. |

### Query Parameters

| Name       | Type    | Required | Default | Description                                                                                       |
|------------|---------|----------|---------|---------------------------------------------------------------------------------------------------|
| `distinct` | string  | No       | (none)  | Field name to group the count by (e.g., `mac`). Determines the dynamic key inside each `results[]` item.   |
| `mac`      | string  | No       | (none)  | Optional filter: restrict the count to a single device MAC address.                               |
| `start`    | string  | No       | (none)  | Window start. Epoch seconds, or relative string like `-1d`, `-1w`.                                |
| `end`      | string  | No       | (none)  | Window end. Epoch seconds, or relative string like `-1d`, `-2h`, `now`.                           |
| `duration` | string  | No       | `1d`    | Convenience window like `7d`, `2w`. Used when explicit `start`/`end` are not supplied.            |
| `limit`    | integer | No       | `100`   | Maximum number of result buckets returned.                                                        |

### Request Headers

| Header           | Value                       | Notes                                                              |
|------------------|-----------------------------|--------------------------------------------------------------------|
| `Authorization`  | `Token <api_token>`         | Injected by `mistapi.APISession` from `.env`. Never logged.        |
| `Accept`         | `application/json`          | Default for mistapi SDK.                                           |
| `User-Agent`     | `mistapi/<version>`         | Set by the SDK.                                                    |

### Request Body

None. This is a GET.

## Response Contract

### 200 OK

Result body is a single JSON object (per the OpenAPI schema, all six
top-level fields are required: `distinct`, `start`, `end`, `limit`,
`results`, `total`).

```json
{
  "distinct": "mac",
  "start": 1719013200,
  "end": 1719618000,
  "limit": 100,
  "total": 42,
  "results": [
    { "mac": "aabbccddee01", "count": 12 },
    { "mac": "aabbccddee02", "count": 8 },
    { "mac": "aabbccddee03", "count": 1 }
  ]
}
```

| Field      | Type           | Description                                                                                                                                                 |
|------------|----------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `distinct` | string         | Echo of the requested `distinct` query parameter. Identifies which property name will appear inside each `results[]` item.                                  |
| `start`    | int32 (epoch s)| Lower bound of the resolved time window.                                                                                                                    |
| `end`      | int32 (epoch s)| Upper bound of the resolved time window.                                                                                                                    |
| `limit`    | int32          | Echo of the `limit` query parameter actually applied (default 100).                                                                                         |
| `total`    | int32          | Total number of distinct values matched. May exceed `len(results)` if more distinct values exist than `limit` allowed to be returned.                       |
| `results`  | array (unique) | Aggregated buckets. Each item is `{ <distinct>: <string value>, "count": <int32> }`. Additional string-valued properties may appear per the schema's `additionalProperties: {type: string}` clause; MistHelper captures any extras into the `extra_fields_json` column for forward compatibility. |

### Error Responses

| Status | Mist Description                                                  | MistHelper Handling                                                                                                          |
|--------|-------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------|
| 400    | Bad Syntax                                                        | Log `WARNING` ("Mist returned 400 -- check site_id and distinct field"). No traceback. Return early.                          |
| 401    | Unauthorized                                                      | Log `ERROR` ("Mist 401 -- check MIST_API_TOKEN in .env"). Do not retry. Return early.                                         |
| 403    | Permission Denied                                                 | Log `ERROR` ("Mist 403 -- token lacks read access to site %s", site_id). Return early.                                        |
| 404    | Not found. Endpoint or resource does not exist                    | Log `WARNING` ("No config history count for site %s", site_id). Treat as empty result and write a summary row with zero results. Return cleanly. |
| 429    | Too Many Requests (5000 calls/hour token threshold exceeded)      | Adaptive delay system (`delay_metrics.json` + `tuning_data.json`) backs off and retries automatically up to the configured retry cap. No user intervention. |

All non-200 responses are surfaced as ASCII log lines only. The API token is
never included in any log message, even at `DEBUG`.

## mistapi Python SDK Call Signature

```python
import os
import mistapi
from mistapi.api.v1.sites.devices.config_history import count as config_history_count_module

apisession = mistapi.APISession(
    host=os.environ["MIST_HOST"],
    apitoken=os.environ["MIST_API_TOKEN"],
)
apisession.login()

# Minimal call (defaults: distinct unset, duration=1d, limit=100):
response = config_history_count_module.countSiteDeviceConfigHistory(
    apisession,
    site_id="0a1b2c3d-1234-5678-9abc-def012345678",
)

# Typical NOC call (group by MAC, 7-day window, top 200 buckets):
response = config_history_count_module.countSiteDeviceConfigHistory(
    apisession,
    site_id="0a1b2c3d-1234-5678-9abc-def012345678",
    distinct="mac",
    duration="7d",
    limit=200,
)

# Filtered call (count history events for a single device):
response = config_history_count_module.countSiteDeviceConfigHistory(
    apisession,
    site_id="0a1b2c3d-1234-5678-9abc-def012345678",
    distinct="mac",
    mac="aabbccddeeff",
    start=1719013200,
    end=1719618000,
)

# Access the parsed body:
body = response.data           # dict matching the 200 OK schema above
http_status = response.status_code
```

Notes:

- The SDK module path mirrors the OpenAPI URL path
  (`/sites/{site_id}/devices/config_history/count` ->
  `mistapi.api.v1.sites.devices.config_history.count`). The enriched
  per-endpoint doc lists the SDK as
  `mistapi.api.v1.sites.devices.countSiteDeviceConfigHistory()` (a flat
  shorthand under the `devices` module); this is a common mistapi pattern
  for count/search endpoints. If the user's installed `mistapi` version
  exposes only the flat form, the implementation falls back to
  `mistapi.api.v1.sites.devices.countSiteDeviceConfigHistory(apisession, ...)`
  with identical behavior. Final verification at implementation time:

  ```powershell
  python -c "import mistapi; help(mistapi.api.v1.sites.devices.config_history.count.countSiteDeviceConfigHistory)"
  ```

- `response.data` is `None` only when the HTTP response had no body (rare).
  MistHelper normalizes this to `{}` before flattening.
- Optional parameters set to `None` are omitted from the URL by the SDK.
  This is the recommended way to skip `mac`, `start`, and `end` rather than
  passing empty strings (which would add `?mac=` etc. to the URL).

## Pagination

The endpoint exposes a `limit` parameter (default 100) but the schema does
not document a cursor/page mechanism. The `total` field reports the count
of distinct values matched, which may exceed `len(results)`. When
`total > limit`, the user is informed via a `WARNING` log line and advised
to increase `limit` if full coverage is required. MistHelper does not
attempt automatic paging for this endpoint.

## Rate Limiting

Standard Mist API rate limit: 5000 calls per token per hour. MistHelper's
adaptive delay system (`delay_metrics.json` per-endpoint state +
`tuning_data.json` learning) governs back-off automatically. No
endpoint-specific tuning required for this contract.
