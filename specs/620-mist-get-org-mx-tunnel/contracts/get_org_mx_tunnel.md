# Endpoint Contract: getOrgMxTunnel

**Spec**: [../spec.md](../spec.md)
**Plan**: [../plan.md](../plan.md)
**Source doc**: `documentation/api/orgs/GET_orgs_org_id_mxtunnels_mxtunnel_id.md`
**Date**: 2026-06-30

## HTTP Contract

| Attribute       | Value                                                            |
|-----------------|------------------------------------------------------------------|
| **Method**      | `GET`                                                            |
| **URL**         | `https://{mist_host}/api/v1/orgs/{org_id}/mxtunnels/{mxtunnel_id}` |
| **Auth**        | `Authorization: Token {api_token}` header (provided automatically by `mistapi.APISession`) |
| **Tag**         | `Orgs MxTunnels`                                                 |
| **operationId** | `getOrgMxTunnel`                                                 |

### Path Parameters

| Name          | Type          | Required | Description |
|---------------|---------------|----------|-------------|
| `org_id`      | string (UUID) | Yes      | Organization UUID. Validated client-side by MistHelper via `is_valid_uuid()` before the call. |
| `mxtunnel_id` | string (UUID) | Yes      | Mxtunnel UUID. Validated client-side via `is_valid_uuid()` before the call. |

### Query Parameters

None. The endpoint accepts no query parameters.

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
  "id": "53f10664-3ce8-4c27-b382-0ef66432349f",
  "org_id": "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61",
  "site_id": "441a1214-6928-442a-8e92-e1d34b8ec6a6",
  "for_site": false,
  "name": "hq-tunnel-a",
  "protocol": "ip",
  "mtu": 0,
  "hello_interval": 60,
  "hello_retries": 7,
  "vlan_ids": [10, 20, 30, 40],
  "mxcluster_ids": [
    "00000000-0000-0000-0000-000000000001",
    "00000000-0000-0000-0000-000000000002"
  ],
  "anchor_mxtunnel_ids": [],
  "auto_preemption": {
    "enabled": true,
    "day_of_week": "sun",
    "time_of_day": "02:00"
  },
  "ipsec": {
    "enabled": true,
    "use_mxedge": true,
    "split_tunnel": false,
    "dns_servers": ["10.0.0.1", "10.0.0.2"],
    "dns_suffix": ["corp.example.com"],
    "extra_routes": [
      {"dest": "10.1.0.0/16", "next_hop": "10.0.0.254"},
      {"dest": "10.2.0.0/16", "next_hop": "10.0.0.254"}
    ]
  },
  "created_time": 1700000000.0,
  "modified_time": 1719600000.0
}
```

| Field                 | Type                       | Description |
|-----------------------|----------------------------|-------------|
| `id`                  | string (UUID), read-only   | Mxtunnel UUID. Natural primary key. |
| `org_id`              | string (UUID), read-only   | Owning organization UUID. |
| `site_id`             | string (UUID), read-only   | Owning site UUID; only meaningful when `for_site=true`. |
| `for_site`            | boolean, read-only         | True if the tunnel is scoped to a site rather than an org. |
| `name`                | string or null             | Human-readable name. |
| `protocol`            | string enum                | `ip` or `udp`. |
| `mtu`                 | integer 0-1500             | 0 enables PMTU; 552-1500 starts PMTU at a lower MTU. |
| `hello_interval`      | integer 1-300 (or null)    | Heartbeat in seconds. Default 60. |
| `hello_retries`       | integer 2-30 (or null)     | Missed-hello count before peer switch. Default 7. |
| `vlan_ids`            | int[]                      | VLAN IDs carried by the tunnel. |
| `mxcluster_ids`       | string (UUID)[]            | Mxclusters this tunnel deploys to. |
| `anchor_mxtunnel_ids` | string (UUID)[]            | Anchor mxtunnels for edge-to-edge tunneling. |
| `auto_preemption`     | object                     | `enabled` (bool, default false), `day_of_week` enum, `time_of_day` `any` or `HH:MM`. |
| `ipsec`               | object (`mxtunnel_ipsec`)  | IPSec config including `enabled`, `use_mxedge`, `split_tunnel`, `dns_servers`, `dns_suffix`, `extra_routes[]`. |
| `created_time`        | number (epoch seconds)     | Read-only. |
| `modified_time`       | number (epoch seconds)     | Read-only. |

The `ipsec.extra_routes` array is the only nested list whose elements MistHelper
flattens into a separate output table; the other arrays (`vlan_ids`, `mxcluster_ids`,
`anchor_mxtunnel_ids`, `ipsec.dns_servers`, `ipsec.dns_suffix`) are stored as
JSON-encoded TEXT columns alongside convenience `_count` integers (see `data-model.md`).

### Error Responses

| Status | Mist Description                                                   | MistHelper Handling |
|--------|--------------------------------------------------------------------|---------------------|
| 400    | Bad Syntax                                                         | Log `WARNING` ("Mist returned 400 -- check org_id / mxtunnel_id format"). No traceback. Return early. |
| 401    | Unauthorized                                                       | Log `ERROR` ("Mist 401 -- check MIST_API_TOKEN in .env"). Do not retry. Return early. |
| 403    | Permission Denied                                                  | Log `ERROR` ("Mist 403 -- token lacks read access to org %s", org_id). Return early. |
| 404    | Not found. Endpoint or resource does not exist                     | Log `WARNING` ("Mxtunnel %s not found in org %s", mxtunnel_id, org_id). Write zero rows. Return cleanly. |
| 429    | Too Many Requests (5000 calls/hour token threshold exceeded)       | Adaptive delay system (`delay_metrics.json` + `tuning_data.json`) backs off and retries automatically up to the configured retry cap. No user intervention. |

All non-200 responses are surfaced as ASCII log lines only. The API token is never
included in any log message, even at `DEBUG`.

## mistapi Python SDK Call Signature

```python
import os
import mistapi
from mistapi.api.v1.orgs import mxtunnels

# Bootstrap (handled once at startup by MistHelper).
apisession = mistapi.APISession(host=os.environ["MIST_HOST"],
                                apitoken=os.environ["MIST_API_TOKEN"])
apisession.login()

# Fetch a single mxtunnel by ID.
response = mxtunnels.getOrgMxTunnel(
    apisession,
    org_id="0a1b2c3d-1234-5678-9abc-def012345678",
    mxtunnel_id="53f10664-3ce8-4c27-b382-0ef66432349f",
)

# Access the parsed body and HTTP status.
body = response.data            # dict matching the 200 OK schema above
http_status = response.status_code
```

Notes:

- The SDK module path mirrors the OpenAPI URL path
  (`/orgs/{org_id}/mxtunnels/{mxtunnel_id}` -> `mistapi.api.v1.orgs.mxtunnels`). Final
  verification at implementation time: `python -c "from mistapi.api.v1.orgs import
  mxtunnels; help(mxtunnels.getOrgMxTunnel)"` inside the venv.
- `response.data` is `None` only when the HTTP response had no body (rare, e.g., a 404
  with empty payload). MistHelper normalizes this to `{}` before flattening.
- Both `org_id` and `mxtunnel_id` are positional in the SDK call; the SDK serializes
  them into the URL path segments. There are no query parameters to pass.

## Pagination

Not paginated. The endpoint returns a single JSON object per call. No `limit`/`page`
parameters apply.

## Rate Limiting

Standard Mist API rate limit: 5000 calls per token per hour. MistHelper's adaptive
delay system (`delay_metrics.json` per-endpoint state + `tuning_data.json` learning)
governs back-off automatically. No endpoint-specific tuning required for this contract.
