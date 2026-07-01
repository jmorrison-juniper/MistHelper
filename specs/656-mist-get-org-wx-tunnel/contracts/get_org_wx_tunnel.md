# Endpoint Contract: getOrgWxTunnel

**Spec**: [../spec.md](../spec.md)
**Plan**: [../plan.md](../plan.md)
**Source doc**: `documentation/api/orgs/GET_orgs_org_id_wxtunnels_wxtunnel_id.md`
**Date**: 2026-07-01

## HTTP Contract

| Attribute       | Value                                                                          |
|-----------------|--------------------------------------------------------------------------------|
| **Method**      | `GET`                                                                          |
| **URL**         | `https://{mist_host}/api/v1/orgs/{org_id}/wxtunnels/{wxtunnel_id}`             |
| **Auth**        | `Authorization: Token {api_token}` header (provided automatically by `mistapi.APISession`) |
| **Tag**         | `Orgs WxTunnels`                                                               |
| **operationId** | `getOrgWxTunnel`                                                               |

### Path Parameters

| Name          | Type          | Required | Description                                                        |
|---------------|---------------|----------|--------------------------------------------------------------------|
| `org_id`      | string (UUID) | Yes      | Organization UUID. Validated client-side by MistHelper via `is_valid_uuid()` before the call. |
| `wxtunnel_id` | string (UUID) | Yes      | WxLAN Tunnel UUID. Validated client-side by MistHelper via `is_valid_uuid()` before the call. |

### Query Parameters

None. The OpenAPI contract does not define any query parameters for this operation.

### Request Headers

| Header           | Value                       | Notes |
|------------------|-----------------------------|-------|
| `Authorization`  | `Token <api_token>`         | Injected by `mistapi.APISession` from `.env`. Never logged. |
| `Accept`         | `application/json`          | Default for mistapi SDK. |
| `User-Agent`     | `mistapi/<version>`         | Set by SDK. |

### Request Body

None. This is a GET.

## Response Contract

### 200 OK

```json
{
  "id": "53f10664-3ce8-4c27-b382-0ef66432349f",
  "org_id": "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61",
  "site_id": "441a1214-6928-442a-8e92-e1d34b8ec6a6",
  "name": "hq-tunnel-a",
  "for_mgmt": false,
  "for_site": false,
  "is_static": false,
  "hello_interval": 60,
  "hello_retries": 7,
  "hostname": "%H",
  "router_id": "10.1.1.1",
  "secret": "",
  "mtu": 0,
  "peers": ["10.20.30.40", "10.20.30.41"],
  "udp_port": 1701,
  "use_udp": true,
  "dmvpn": {
    "enabled": false,
    "holding_time": 600,
    "host_routes": []
  },
  "ipsec": {
    "enabled": true,
    "psk": "<redacted-in-logs>"
  },
  "sessions": [
    {
      "remote_id": "session-a",
      "local_session_id": 1,
      "remote_session_id": 1001,
      "ethertype": "ethernet",
      "enable_cookie": true,
      "pseudo_802.1ad_enabled": false,
      "use_ap_as_session_ids": false,
      "ap_as_session_id": null,
      "comment": "north DC"
    },
    {
      "remote_id": "session-b",
      "local_session_id": 2,
      "remote_session_id": 1002,
      "ethertype": "vlan",
      "enable_cookie": false,
      "pseudo_802.1ad_enabled": true,
      "use_ap_as_session_ids": false,
      "ap_as_session_id": null,
      "comment": "south DC"
    }
  ],
  "created_time": 1717000000,
  "modified_time": 1717600000
}
```

| Field            | Type                | Description |
|------------------|---------------------|-------------|
| `id`             | string (UUID)       | WxTunnel UUID. Natural primary key for MistHelper. Read-only. |
| `org_id`         | string (UUID)       | Organization UUID. Read-only. |
| `site_id`        | string (UUID)       | Site UUID when the tunnel is site-scoped. Read-only. |
| `name`           | string              | Human-readable tunnel name. **Required** by schema. |
| `for_mgmt`       | bool                | Management-tunnel marker. Immutable after create. |
| `for_site`       | bool                | Read-only site-scope flag. |
| `is_static`      | bool                | Static / unmanaged tunnel marker. Immutable after create. |
| `hello_interval` | int (1..300)        | Heartbeat interval in seconds. Default 60. |
| `hello_retries`  | int (2..30)         | Retries before declaring peer dead. Default 7. |
| `hostname`       | string              | SCCRQ hostname override. `%H` / `%M` substitution supported. |
| `router_id`      | string              | SCCRQ router-id override. |
| `secret`         | string              | L2TP auth secret; empty when no auth. Treated as sensitive; logged as `<redacted>`. |
| `mtu`            | int (0..1500)       | 0 = PMTU discovery, 552..1500 = starting MTU. |
| `peers`          | string[]            | List of remote peer IPs / hostnames. |
| `udp_port`       | int                 | UDP port when `use_udp=true`. |
| `use_udp`        | bool                | UDP transport instead of raw IP proto 115. |
| `dmvpn`          | object              | DMVPN sub-config: `{enabled, holding_time, host_routes[]}`. |
| `ipsec`          | object              | IPSec sub-config: `{enabled, psk}`. **`psk` is a secret and MUST be redacted in logs** (see plan.md / data-model.md). |
| `sessions`       | object[]            | Zero-or-more session records. See sub-schema below. |
| `created_time`   | number (epoch sec)  | Read-only creation time. |
| `modified_time`  | number (epoch sec)  | Read-only last-modified time. |

### `sessions[]` sub-schema (`wxlan_tunnel_session`)

| Field                        | Type              | Description |
|------------------------------|-------------------|-------------|
| `remote_id`                  | string            | Remote-id of the session, unique within the tunnel. Part of MistHelper composite key. |
| `local_session_id`           | int (1..2147483647) | Local L2TP session id. |
| `remote_session_id`          | int (1..2147483647) | Remote L2TP session id. |
| `ethertype`                  | string enum       | `ethernet` or `vlan`. |
| `enable_cookie`              | bool              | L2TP cookie toggle. |
| `pseudo_802.1ad_enabled`     | bool              | Optional pseudo-QinQ mode (renamed `pseudo_dot1ad_enabled` in SQLite for SQL-safety). |
| `use_ap_as_session_ids`      | bool              | Use last 4 bytes of AP MAC as session ids. |
| `ap_as_session_id`           | string            | Only meaningful when `use_ap_as_session_ids=true`. |
| `comment`                    | string            | Optional user comment. |

### Error Responses

| Status | Mist Description                                                   | MistHelper Handling |
|--------|--------------------------------------------------------------------|---------------------|
| 400    | Bad Syntax                                                         | Log `WARNING` ("Mist returned 400 -- check org_id / wxtunnel_id format"), no traceback, return early. |
| 401    | Unauthorized                                                       | Log `ERROR` ("Mist 401 -- check MIST_API_TOKEN in .env"). Do not retry. Return early. |
| 403    | Permission Denied                                                  | Log `ERROR` ("Mist 403 -- token lacks read access to org %s", org_id). Return early. |
| 404    | Not found. Endpoint or resource does not exist                     | Log `WARNING` ("No WxTunnel %s found in org %s", wxtunnel_id, org_id). Treat as empty result; do not write partial rows. Return cleanly. |
| 429    | Too Many Requests (5000 calls/hour token threshold exceeded)       | Adaptive delay system (`delay_metrics.json` + `tuning_data.json`) backs off and retries automatically up to the configured retry cap. No user intervention. |

All non-200 responses are surfaced as ASCII log lines only. The API token, the L2TP
`secret`, and the IPsec `psk` are never included in any log message, even at `DEBUG`.

## mistapi Python SDK Call Signature

```python
import mistapi
from mistapi.api.v1.orgs import wxtunnels as wxtunnels_module

apisession = mistapi.APISession(host=os.environ["MIST_HOST"],
                                apitoken=os.environ["MIST_API_TOKEN"])
apisession.login()

# Retrieve a single WxTunnel by UUID:
response = wxtunnels_module.getOrgWxTunnel(
    apisession,
    org_id="a97c1b22-a4e9-411e-9bfd-d8695a0f9e61",
    wxtunnel_id="53f10664-3ce8-4c27-b382-0ef66432349f",
)

# Access the parsed body:
body = response.data           # dict matching the 200 OK schema above
http_status = response.status_code
```

Notes:

- The SDK module path mirrors the OpenAPI URL path (`/orgs/{org_id}/wxtunnels/
  {wxtunnel_id}` -> `mistapi.api.v1.orgs.wxtunnels`). Final signature verification
  happens at implementation time via
  `python -c "from mistapi.api.v1.orgs import wxtunnels; help(wxtunnels.getOrgWxTunnel)"`.
- `response.data` is `None` only when the HTTP response had no body (rare on this
  endpoint). MistHelper normalizes this to `{}` before flattening.
- Both `org_id` and `wxtunnel_id` are positional path parameters. There are no query
  parameters and no request body.

## Pagination

Not paginated. The endpoint returns a single JSON object per call. No `limit` / `page`
parameters apply.

## Rate Limiting

Standard Mist API rate limit: 5000 calls per token per hour. MistHelper's adaptive
delay system (`delay_metrics.json` per-endpoint state + `tuning_data.json` learning)
governs back-off automatically. No endpoint-specific tuning is required for this
contract.
