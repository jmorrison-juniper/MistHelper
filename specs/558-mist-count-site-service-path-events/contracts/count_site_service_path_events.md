# Endpoint Contract: countSiteServicePathEvents

**Spec**: [../spec.md](../spec.md)
**Plan**: [../plan.md](../plan.md)
**Source doc**: `documentation/api/sites/GET_sites_site_id_services_events_count.md`
**Date**: 2026-06-29

## HTTP Contract

| Attribute       | Value                                                              |
|-----------------|--------------------------------------------------------------------|
| **Method**      | `GET`                                                              |
| **URL**         | `https://{mist_host}/api/v1/sites/{site_id}/services/events/count` |
| **Auth**        | `Authorization: Token {api_token}` header (provided automatically by `mistapi.APISession`) |
| **Tag**         | `Sites Services`                                                   |
| **operationId** | `countSiteServicePathEvents`                                       |

### Path Parameters

| Name      | Type          | Required | Description                                                                |
|-----------|---------------|----------|----------------------------------------------------------------------------|
| `site_id` | string (UUID) | Yes      | Site UUID. Validated client-side by MistHelper via `is_valid_uuid()` before the call. |

### Query Parameters

| Name        | Type    | Required | Default | Enum / Format | Description |
|-------------|---------|----------|---------|---------------|-------------|
| `distinct`  | string  | No       | (server default) | `type`, `vpn_name`, `vpn_path`, `policy`, `port_id`, `model`, `version`, `mac` | Field to group counts by. MistHelper prompts the user and validates against this enum before the call. |
| `type`      | string  | No       | --      | e.g. `GW_SERVICE_PATH_DOWN`, `GW_SERVICE_PATH_UP` | Filter to a single event type. Not prompted in v1 of this menu. |
| `text`      | string  | No       | --      | free text     | Filter on the human-readable event description. Not prompted in v1. |
| `vpn_name`  | string  | No       | --      | --            | Filter by peer name. Not prompted in v1. |
| `vpn_path`  | string  | No       | --      | --            | Filter by peer path name. Not prompted in v1. |
| `policy`    | string  | No       | --      | --            | Filter by service policy associated with the path. Not prompted in v1. |
| `port_id`   | string  | No       | --      | --            | Filter by network interface. Not prompted in v1. |
| `model`     | string  | No       | --      | --            | Filter by device model. Not prompted in v1. |
| `version`   | string  | No       | --      | --            | Filter by device firmware version. Not prompted in v1. |
| `timestamp` | number  | No       | --      | epoch seconds | Alternative single-point time anchor. Not prompted in v1. |
| `mac`       | string  | No       | --      | --            | Filter by device MAC. Not prompted in v1. |
| `start`     | string  | No       | --      | epoch seconds OR relative (`-1d`, `-1w`) | Window start. Prompted; blank passes `None` to SDK. |
| `end`       | string  | No       | --      | epoch seconds OR relative (`now`, `-1h`) | Window end. Prompted; blank passes `None` to SDK. |
| `duration`  | string  | No       | `1d`    | e.g. `7d`, `2w` | Used by server when both `start` and `end` are omitted. MistHelper accepts the server default for v1. |
| `limit`     | integer | No       | `100`   | --            | Server-side cap on number of buckets returned. MistHelper accepts the server default for v1. |

### Request Headers

| Header           | Value                  | Notes                                                              |
|------------------|------------------------|--------------------------------------------------------------------|
| `Authorization`  | `Token <api_token>`    | Injected by `mistapi.APISession` from `.env`. Never logged.        |
| `Accept`         | `application/json`     | Default for mistapi SDK.                                           |
| `User-Agent`     | `mistapi/<version>`    | Set by SDK.                                                        |

### Request Body

None. This is a GET.

## Response Contract

### 200 OK

Result of Count.

```json
{
  "distinct": "type",
  "start": 1719000000,
  "end": 1719604800,
  "limit": 100,
  "total": 152,
  "results": [
    { "count": 87, "type": "GW_SERVICE_PATH_DOWN" },
    { "count": 60, "type": "GW_SERVICE_PATH_UP" },
    { "count": 3,  "type": "GW_SERVICE_PATH_DEGRADED" },
    { "count": 2,  "type": "GW_SERVICE_PATH_RECONFIG" }
  ]
}
```

| Field      | Type     | Required | Description |
|------------|----------|----------|-------------|
| `distinct` | string   | Yes      | Echoes the grouping field used (`type`, `vpn_name`, etc.). Becomes `distinct_field` in MistHelper output. |
| `start`    | int32 (epoch seconds) | Yes | Window start the server evaluated. Part of MistHelper composite PK. |
| `end`      | int32 (epoch seconds) | Yes | Window end the server evaluated. Part of MistHelper composite PK. |
| `limit`    | int32    | Yes      | The `limit` the server applied. |
| `total`    | int32    | Yes      | Total events across all buckets in the window. |
| `results`  | object[] (unique) | Yes | One element per distinct bucket. Each element has the required integer field `count` plus an extra string field whose key equals the value of `distinct` and whose value is the bucket label. |

Per-bucket shape:

| Field         | Type    | Required | Description |
|---------------|---------|----------|-------------|
| `count`       | int32   | Yes      | Number of events in this bucket within the window. |
| `<distinct>`  | string  | Yes (additionalProperty) | Bucket label whose key name equals the value of the top-level `distinct` field (e.g. with `distinct=type`, the key is `type` and the value might be `GW_SERVICE_PATH_DOWN`). |

### Error Responses

| Status | Mist Description                                                  | MistHelper Handling |
|--------|-------------------------------------------------------------------|---------------------|
| 400    | Bad Syntax                                                        | Log `WARNING` ("Mist returned 400 -- check site_id and distinct field"), no traceback, return early. |
| 401    | Unauthorized                                                      | Log `ERROR` ("Mist 401 -- check MIST_API_TOKEN in .env"). Do not retry. Return early. |
| 403    | Permission Denied                                                 | Log `ERROR` ("Mist 403 -- token lacks read access to site %s", site_id). Return early. |
| 404    | Not found. The API endpoint or resource does not exist            | Log `WARNING` ("No service-path events for site %s in window", site_id). Treat as empty result and write zero rows. Return cleanly. |
| 429    | Too Many Requests (5000 calls/hour token threshold exceeded)      | Adaptive delay system (`delay_metrics.json` + `tuning_data.json`) backs off and retries automatically up to the configured retry cap. No user intervention. |

All non-200 responses are surfaced as ASCII log lines only. The API token is
never included in any log message, even at `DEBUG`.

## mistapi Python SDK Call Signature

```python
import os
import mistapi
from mistapi.api.v1.sites.services.events import count as svc_path_count_module

apisession = mistapi.APISession(
    host=os.environ["MIST_HOST"],
    apitoken=os.environ["MIST_API_TOKEN"],
)
apisession.login()

# Minimal call (server defaults: distinct omitted -> server default, duration=1d, limit=100):
response = svc_path_count_module.countSiteServicePathEvents(
    apisession,
    site_id="0a1b2c3d-1234-5678-9abc-def012345678",
)

# Typical MistHelper invocation (distinct=type, last 7 days):
response = svc_path_count_module.countSiteServicePathEvents(
    apisession,
    site_id="0a1b2c3d-1234-5678-9abc-def012345678",
    distinct="type",
    start="-7d",
    end="now",
)

# Full filter example (advanced; not exposed in v1 of the menu):
response = svc_path_count_module.countSiteServicePathEvents(
    apisession,
    site_id="0a1b2c3d-1234-5678-9abc-def012345678",
    distinct="vpn_path",
    type="GW_SERVICE_PATH_DOWN",
    vpn_name="hub-east",
    start=1719000000,
    end=1719604800,
    limit=100,
)

# Access the parsed body:
body = response.data           # dict matching the 200 OK schema above
http_status = response.status_code
```

Notes:

- The SDK module path mirrors the OpenAPI URL path
  (`/sites/{site_id}/services/events/count` ->
  `mistapi.api.v1.sites.services.events.count`). The enriched per-endpoint
  doc lists the SDK signature as
  `mistapi.api.v1.sites.services.countSiteServicePathEvents()`, which is the
  shorter form used by some older mistapi releases. Final verification at
  implementation time uses
  `python -c "from mistapi.api.v1.sites.services.events import count;
  help(count)"`; if only the older path resolves in the installed mistapi
  version, the import statement and call site are adjusted before commit and
  this contract file is updated accordingly.
- `response.data` is `None` only when the HTTP response had no body (rare).
  MistHelper normalizes this to `{}` before reading `results`.
- Optional query parameters are omitted by passing `None` to the SDK -- this
  is preferred over passing empty strings, which would still serialize into
  the URL as `?start=&end=` and may trigger 400s on stricter parsers.
- The SDK accepts both integer epoch values and relative strings (`-1d`,
  `now`) for `start` / `end`; MistHelper passes the user's input through
  unmodified.

## Pagination

Officially documented as supporting `limit` and `page` parameters, but the
response is a pre-aggregated count envelope with a bounded `results[]` array
(one element per distinct bucket value, capped by `limit`). In practice
MistHelper does not paginate this endpoint in v1 -- a single call with
`limit` at the server default (100) covers every realistic distinct
cardinality (the largest distinct field, `mac`, is bounded by device count
at the site). If a future deployment exceeds 100 distinct values, a follow-up
spec adds explicit `page` iteration.

## Rate Limiting

Standard Mist API rate limit: 5000 calls per token per hour. MistHelper's
adaptive delay system (`delay_metrics.json` per-endpoint state +
`tuning_data.json` learning) governs back-off automatically. No
endpoint-specific tuning required for this contract.
