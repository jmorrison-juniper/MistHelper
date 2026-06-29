# Endpoint Contract: countOrgWirelessClients

**Spec**: [../spec.md](../spec.md)
**Plan**: [../plan.md](../plan.md)
**Source doc**: `documentation/api/orgs/GET_orgs_org_id_clients_count.md`
**Date**: 2026-06-29

## HTTP Contract

| Attribute       | Value                                                                       |
|-----------------|-----------------------------------------------------------------------------|
| **Method**      | `GET`                                                                       |
| **URL**         | `https://{mist_host}/api/v1/orgs/{org_id}/clients/count`                    |
| **Auth**        | `Authorization: Token {api_token}` header (provided automatically by `mistapi.APISession`) |
| **Tag**         | `Orgs Clients - Wireless`                                                   |
| **operationId** | `countOrgWirelessClients`                                                   |

### Path Parameters

| Name     | Type          | Required | Description                                                                                  |
|----------|---------------|----------|----------------------------------------------------------------------------------------------|
| `org_id` | string (UUID) | Yes      | Organization UUID. Validated client-side by MistHelper via `is_valid_uuid()` before the call.|

### Query Parameters

| Name       | Type    | Required | Default | Description |
|------------|---------|----------|---------|-------------|
| `distinct` | string  | No       | (none)  | Grouping attribute. MistHelper whitelist: `ssid`, `hostname`, `os`, `device`, `model`, `ap`, `vlan`, `ip`, `mac`, or omitted. When omitted, the API returns one aggregate bucket. |
| `mac`      | string  | No       | (none)  | Partial / full client MAC address filter. |
| `hostname` | string  | No       | (none)  | Partial / full client hostname filter. |
| `device`   | string  | No       | (none)  | Device type filter (e.g. `Mac`, `Nvidia`, `iPhone`). |
| `os`       | string  | No       | (none)  | OS filter (e.g. `Sierra`, `Yosemite`, `Windows 10`). |
| `model`    | string  | No       | (none)  | Model filter (e.g. `MBP 15 late 2013`, `6`, `6s`, `8+ GSM`). |
| `ap`       | string  | No       | (none)  | AP MAC where the client is connected. |
| `vlan`     | string  | No       | (none)  | VLAN ID filter. |
| `ssid`     | string  | No       | (none)  | SSID name filter. |
| `ip`       | string  | No       | (none)  | Client IP address filter. |
| `start`    | string  | No       | (none)  | Inclusive start of time window. Epoch seconds or relative string (`-1d`, `-1w`). |
| `end`      | string  | No       | (none)  | Exclusive end of time window. Epoch seconds or relative string (`-2h`, `now`). |
| `duration` | string  | No       | `1d`    | Duration window when `start`/`end` are omitted (e.g. `7d`, `2w`). |
| `limit`    | integer | No       | `100`   | Maximum bucket rows returned in `results`. |

MistHelper menu 96 surfaces only `distinct`, `duration`, and `limit` in its prompts to
keep the junior-NOC workflow short. The remaining filters are reachable via the SDK
keyword arguments and can be enabled by a follow-up spec without changing this contract.

### Request Headers

| Header           | Value                  | Notes |
|------------------|------------------------|-------|
| `Authorization`  | `Token <api_token>`    | Injected by `mistapi.APISession` from `.env`. Never logged. |
| `Accept`         | `application/json`     | Default for mistapi SDK. |
| `User-Agent`     | `mistapi/<version>`    | Set by SDK. |

### Request Body

None. This is a GET.

## Response Contract

### 200 OK

```json
{
  "distinct": "ssid",
  "start": 1719000000,
  "end": 1719604800,
  "limit": 100,
  "total": 3,
  "results": [
    {"count": 142, "ssid": "Corp-Employee"},
    {"count":  47, "ssid": "Corp-Guest"},
    {"count":   6, "ssid": "Corp-IoT"}
  ]
}
```

| Field      | Type     | Description |
|------------|----------|-------------|
| `distinct` | string   | Echoes the grouping attribute the caller requested. Blank when no `distinct` was supplied. |
| `start`    | int32 (epoch seconds) | Inclusive start of the time window the API actually used. |
| `end`      | int32 (epoch seconds) | Exclusive end of the time window the API actually used. |
| `limit`    | int32    | Maximum bucket rows returned in `results` (default 100). |
| `total`    | int32    | Total distinct buckets matched -- may exceed `limit`. |
| `results`  | array of `count_result` | Bucket rows. Each item has a required `count` integer plus a string-valued additional property whose key matches the `distinct` value (e.g. `ssid` when `distinct=ssid`). When `distinct` is blank, `results` is typically a single object with `count` only. |

All six top-level fields (`distinct`, `start`, `end`, `limit`, `total`, `results`) are
marked `required` in the OpenAPI schema. MistHelper still defends against `body=None`
(rare) by normalizing to `{}` and against `results=None` by normalizing to `[]`.

### Error Responses

| Status | Mist Description                                                   | MistHelper Handling |
|--------|--------------------------------------------------------------------|---------------------|
| 400    | Bad Syntax                                                         | Log `WARNING` ("Mist returned 400 -- check org_id and distinct value"), no traceback, return early. |
| 401    | Unauthorized                                                       | Log `ERROR` ("Mist 401 -- check MIST_API_TOKEN in .env"). Do not retry. Return early. |
| 403    | Permission Denied                                                  | Log `ERROR` ("Mist 403 -- token lacks read access to org %s", org_id). Return early. |
| 404    | Not found. Endpoint or resource does not exist                     | Log `WARNING` ("countOrgWirelessClients 404 for org %s -- check org_id", org_id). Treat as empty result and write zero result rows (envelope still written with `bucket_count=0`). Return cleanly. |
| 429    | Too Many Requests (5000 calls/hour token threshold exceeded)       | Adaptive delay system (`delay_metrics.json` + `tuning_data.json`) backs off and retries automatically up to the configured retry cap. No user intervention. |

All non-200 responses surface as ASCII-only log lines. The API token is never included
in any log message, even at `DEBUG`. Full URLs containing the org UUID are logged only
at `DEBUG` level and only the first 8 hex characters of the UUID are emitted.

## mistapi Python SDK Call Signature

```python
import os
import mistapi
from mistapi.api.v1.orgs.clients import count as wireless_count_module

apisession = mistapi.APISession(
    host=os.environ["MIST_HOST"],
    apitoken=os.environ["MIST_API_TOKEN"],
)
apisession.login()

# Minimal call -- no grouping, default 1d window, default limit 100:
response = wireless_count_module.countOrgWirelessClients(
    apisession,
    org_id="0a1b2c3d-1234-5678-9abc-def012345678",
)

# Grouped by SSID over the last 7 days, top 100 buckets:
response = wireless_count_module.countOrgWirelessClients(
    apisession,
    org_id="0a1b2c3d-1234-5678-9abc-def012345678",
    distinct="ssid",
    duration="7d",
    limit=100,
)

# Grouped by AP MAC with an explicit window:
response = wireless_count_module.countOrgWirelessClients(
    apisession,
    org_id="0a1b2c3d-1234-5678-9abc-def012345678",
    distinct="ap",
    start="-2h",
    end="now",
    limit=200,
)

# Access the parsed body:
body = response.data           # dict matching the 200 OK schema above
http_status = response.status_code
```

Notes:

- The SDK module path mirrors the OpenAPI URL path
  (`/orgs/{org_id}/clients/count` -> `mistapi.api.v1.orgs.clients.count`). The enriched
  per-endpoint doc records the SDK as
  `mistapi.api.v1.orgs.clients_-_wireless.countOrgWirelessClients()`, but that string
  is not a legal Python identifier and reflects the OpenAPI *tag* rather than the URL
  path. Adjacent endpoints under `/orgs/{org_id}/clients/...` (e.g.
  `searchOrgWirelessClients`) confirm that mistapi organizes modules by URL. Final
  verification at implementation time via `python -c "from mistapi.api.v1.orgs.clients
  import count; help(count)"`; if the SDK actually places the function elsewhere, the
  import line is corrected and the rest of the contract holds unchanged.
- `response.data` is `None` only when the HTTP response had no body (rare). MistHelper
  normalizes this to `{}` before flattening.
- Optional query parameters are passed as Python keyword arguments. The SDK omits the
  parameter from the URL when the value is `None`. MistHelper deliberately converts a
  blank `distinct` to `None` (instead of `""`) to avoid sending `?distinct=` on the
  wire.

## Pagination

Not paginated in the search sense. The endpoint returns a single JSON object per call
with at most `limit` bucket rows. `total` reports the full match count regardless of
`limit`. Callers that need the full bucket set increase `limit` (subject to Mist API
quotas) rather than walk a cursor.

## Rate Limiting

Standard Mist API rate limit: 5000 calls per token per hour. MistHelper's adaptive
delay system (`delay_metrics.json` per-endpoint state + `tuning_data.json` learning)
governs back-off automatically. No endpoint-specific tuning required for this contract.
