# Endpoint Contract: countSiteDiscoveredSwitches

**Spec**: [../spec.md](../spec.md)
**Plan**: [../plan.md](../plan.md)
**Source doc**: `documentation/api/sites/GET_sites_site_id_stats_discovered_switches_count.md`
**Date**: 2026-06-29

## HTTP Contract

| Attribute       | Value                                                                |
|-----------------|----------------------------------------------------------------------|
| **Method**      | `GET`                                                                |
| **URL**         | `https://{mist_host}/api/v1/sites/{site_id}/stats/discovered_switches/count` |
| **Auth**        | `Authorization: Token {api_token}` header (provided automatically by `mistapi.APISession`) |
| **Tag**         | `Sites Stats - Discovered Switches`                                  |
| **operationId** | `countSiteDiscoveredSwitches`                                        |

### Path Parameters

| Name      | Type          | Required | Description                                                       |
|-----------|---------------|----------|-------------------------------------------------------------------|
| `site_id` | string (UUID) | Yes      | Site UUID. Validated client-side by MistHelper via `is_valid_uuid()` before the call. |

### Query Parameters

| Name       | Type    | Required | Default | Description |
|------------|---------|----------|---------|-------------|
| `distinct` | string  | No       | (absent) | Attribute to group the count by (e.g. `vendor`, `model`, `version`). When omitted, the response contains a single `results` entry with `count = total`. |
| `start`    | string  | No       | (absent) | Start of the counted window. Epoch seconds (e.g. `1719600000`) or relative (`-1d`, `-1w`). |
| `end`      | string  | No       | (absent) | End of the counted window. Epoch seconds or relative (`-1d`, `-2h`, `now`). Not prompted in MistHelper; supplied via `MIST_DISCOVERED_SWITCHES_END` env var. |
| `duration` | string  | No       | `1d`    | Window duration when `start` / `end` are not absolute (`1d`, `7d`, `2w`). |
| `limit`    | integer | No       | `100`   | Maximum number of `results` array entries to return. |

### Request Headers

| Header           | Value                  | Notes |
|------------------|------------------------|-------|
| `Authorization`  | `Token <api_token>`    | Injected by `mistapi.APISession` from `.env`. Never logged. |
| `Accept`         | `application/json`     | Default for the mistapi SDK. |
| `User-Agent`     | `mistapi/<version>`    | Set by the SDK. |

### Request Body

None. This is a GET.

## Response Contract

### 200 OK

```json
{
  "distinct": "vendor",
  "start":    1719000000,
  "end":      1719604000,
  "limit":    100,
  "total":    42,
  "results": [
    {"count": 30, "vendor": "juniper"},
    {"count":  9, "vendor": "cisco"},
    {"count":  3, "vendor": "arista"}
  ]
}
```

| Field      | Type      | Description |
|------------|-----------|-------------|
| `distinct` | string    | Echoed grouping attribute. Empty string when no grouping was requested. |
| `start`    | int32 (epoch seconds) | Start of the counted window. |
| `end`      | int32 (epoch seconds) | End of the counted window. |
| `limit`    | int32     | Echoed limit applied to the `results` array (default 100). |
| `total`    | int32     | Total count of discovered switches across all groups. |
| `results`  | array of `count_result` objects | Per-group counts. `count_result.count` is required (int32); additional string properties carry the resolved value of the distinct attribute (e.g. `"vendor": "juniper"`). |

The OpenAPI schema marks `distinct`, `end`, `limit`, `results`, `start`, and `total` as
required on the envelope. The `count_result` schema marks `count` as required and
permits arbitrary additional string properties per group. MistHelper's flatten helper
must enumerate `dict.items()` rather than hard-coding field names so unknown distinct
attributes flow through verbatim into the `extra_attrs_json` column documented in
`data-model.md`.

### Error Responses

| Status | Mist Description                                                | MistHelper Handling |
|--------|-----------------------------------------------------------------|---------------------|
| 400    | Bad Syntax                                                      | Log `WARNING` ("Mist returned 400 -- check distinct/duration/limit values"); no traceback; return early. |
| 401    | Unauthorized                                                    | Log `ERROR` ("Mist 401 -- check MIST_API_TOKEN in .env"). Do not retry. Return early. |
| 403    | Permission Denied                                               | Log `ERROR` ("Mist 403 -- token lacks read access to site %s", site_id). Return early. |
| 404    | Not found. Endpoint or resource does not exist                  | Log `WARNING` ("No discovered switches stats for site %s", site_id). Treat as empty result and write zero group rows; still write a summary row with `total=0`. Return cleanly. |
| 429    | Too Many Requests (5000 calls/hour token threshold exceeded)    | Adaptive delay system (`delay_metrics.json` + `tuning_data.json`) backs off and retries automatically up to the configured retry cap. No user intervention. |

All non-200 responses are surfaced as ASCII log lines only. The API token is never
included in any log message, even at `DEBUG`.

## mistapi Python SDK Call Signature

```python
import os
import mistapi
from mistapi.api.v1.sites.stats.discovered_switches import count as count_module

apisession = mistapi.APISession(host=os.environ["MIST_HOST"],
                                apitoken=os.environ["MIST_API_TOKEN"])
apisession.login()

# Minimal call (no grouping, default 1d window, default limit 100):
response = count_module.countSiteDiscoveredSwitches(
    apisession,
    site_id="0a1b2c3d-1234-5678-9abc-def012345678",
)

# Grouped count over a 7-day window:
response = count_module.countSiteDiscoveredSwitches(
    apisession,
    site_id="0a1b2c3d-1234-5678-9abc-def012345678",
    distinct="vendor",
    duration="7d",
    limit=100,
)

# Absolute window using start + end (overrides duration on the server side):
response = count_module.countSiteDiscoveredSwitches(
    apisession,
    site_id="0a1b2c3d-1234-5678-9abc-def012345678",
    distinct="model",
    start="1719000000",
    end="1719604000",
    limit=50,
)

# Access the parsed body:
body = response.data            # dict matching the 200 OK schema above
http_status = response.status_code
```

Notes:

- The SDK module path mirrors the OpenAPI URL path
  (`/sites/{site_id}/stats/discovered_switches/count` ->
  `mistapi.api.v1.sites.stats.discovered_switches.count`). The enriched per-endpoint
  doc renders the path as `mistapi.api.v1.sites.stats_-_discovered_switches.*` due to a
  doc-generator artifact; the real SDK module follows the URL convention used by
  neighboring stats modules (`mistapi.api.v1.sites.stats.devices`,
  `mistapi.api.v1.sites.stats.clients`). Final verification at implementation time:
  `python -c "from mistapi.api.v1.sites.stats.discovered_switches import count; help(count)"`.
- `response.data` is `None` only when the HTTP response had no body (rare). MistHelper
  normalizes this to `{}` before flattening.
- The `distinct` parameter is passed as a Python string. The SDK omits the query
  parameter entirely when the value is `None` (preferred over the empty string, which
  some servers reject with 400).
- The `end` keyword argument is passed only when `MIST_DISCOVERED_SWITCHES_END` is set;
  otherwise the SDK omits the query parameter and the server applies `duration`.

## Pagination

Server-side `limit`-bounded only; no `page` cursor. The OpenAPI doc notes "Supports
pagination. Use `limit` and `page` query parameters", but the enriched schema does not
expose `page` and the response envelope has no continuation token. MistHelper treats
the call as a single request capped by `limit` (default 100) and surfaces the cap to
the user via the prompt; operators needing larger result sets raise `limit` explicitly.

## Rate Limiting

Standard Mist API rate limit: 5000 calls per token per hour. MistHelper's adaptive
delay system (`delay_metrics.json` per-endpoint state + `tuning_data.json` learning)
governs back-off automatically. No endpoint-specific tuning required for this contract.
