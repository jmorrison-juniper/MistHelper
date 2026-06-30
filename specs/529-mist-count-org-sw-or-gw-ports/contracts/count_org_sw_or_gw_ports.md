# Contract: countOrgSwOrGwPorts

**Source spec**: [../spec.md](../spec.md)  **Plan**: [../plan.md](../plan.md)
**Endpoint doc**: `documentation/api/orgs/GET_orgs_org_id_stats_ports_count.md`

## HTTP Contract

| Aspect       | Value                                                                          |
|--------------|--------------------------------------------------------------------------------|
| Method       | `GET`                                                                          |
| URL template | `https://{MIST_HOST}/api/v1/orgs/{org_id}/stats/ports/count`                   |
| Tag          | `Orgs Stats - Ports`                                                           |
| operationId  | `countOrgSwOrGwPorts`                                                          |
| Auth         | `Authorization: Token {MIST_API_TOKEN}` header (or `X-CSRFToken` cookie).      |
| Content type | Response `application/json`. No request body.                                  |
| Pagination   | Supports `limit` (default 100). The MistHelper menu accepts the SDK default.   |
| Idempotent   | Yes -- pure read.                                                              |

### Required Path Parameters

| Name     | Type   | Notes                                                            |
|----------|--------|------------------------------------------------------------------|
| `org_id` | string | UUID of the Mist organisation. Validated client-side by regex.   |

### Query Parameters (full list from OpenAPI)

| Name                  | Type    | Required | Default | Description                                                                 |
|-----------------------|---------|----------|---------|-----------------------------------------------------------------------------|
| `distinct`            | string  | No       |         | Grouping attribute. MistHelper prompts for it as a required field.          |
| `full_duplex`         | boolean | No       |         | Indicates full or half duplex.                                              |
| `mac`                 | string  | No       |         | Device identifier.                                                          |
| `neighbor_mac`        | string  | No       |         | Chassis identifier of the chassis type listed.                              |
| `neighbor_port_desc`  | string  | No       |         | Description supplied by the system on the interface.                        |
| `neighbor_system_name`| string  | No       |         | Name supplied by the system on the interface.                               |
| `poe_disabled`        | boolean | No       |         | True if POE configured not to be disabled.                                  |
| `poe_mode`            | string  | No       |         | POE mode depending on class, e.g. `802.3at`.                                |
| `poe_on`              | boolean | No       |         | True if the device is attached to POE.                                      |
| `port_id`             | string  | No       |         | Interface name.                                                             |
| `port_mac`            | string  | No       |         | Interface MAC address.                                                      |
| `power_draw`          | number  | No       |         | Power used by the interface at execution time, in watts.                    |
| `tx_pkts`             | integer | No       |         | Output packets.                                                             |
| `rx_pkts`             | integer | No       |         | Input packets.                                                              |
| `rx_bytes`            | integer | No       |         | Input bytes.                                                                |
| `tx_bps`              | integer | No       |         | Output rate.                                                                |
| `rx_bps`              | integer | No       |         | Input rate.                                                                 |
| `tx_mcast_pkts`       | integer | No       |         | Multicast output packets.                                                   |
| `tx_bcast_pkts`       | integer | No       |         | Broadcast output packets.                                                   |
| `rx_mcast_pkts`       | integer | No       |         | Multicast input packets.                                                    |
| `rx_bcast_pkts`       | integer | No       |         | Broadcast input packets.                                                    |
| `speed`               | integer | No       |         | Port speed.                                                                 |
| `stp_state`           | string  | No       |         | Valid if `up == true`.                                                      |
| `stp_role`            | string  | No       |         | Valid if `up == true`.                                                      |
| `auth_state`          | string  | No       |         | Valid if `up == true` and port has Authenticator role.                      |
| `up`                  | boolean | No       |         | True if interface is up. Prompted by MistHelper.                            |
| `site_id`             | string  | No       |         | Site UUID filter. Prompted by MistHelper.                                   |
| `start`               | string  | No       |         | Window start (epoch seconds or relative, e.g. `-1d`).                       |
| `end`                 | string  | No       |         | Window end (epoch seconds or relative, e.g. `now`).                         |
| `duration`            | string  | No       | `1d`    | Duration string, e.g. `7d`, `2w`. Prompted by MistHelper.                   |
| `limit`               | integer | No       | `100`   | Page size. MistHelper accepts the API default.                              |

MistHelper's first revision exposes `distinct`, `site_id`, `up`, and `duration` to the
user via `safe_input()` prompts. The remaining 25 parameters are reachable only by
direct edit in a follow-up enhancement; this is intentional and documented in
`research.md` Task 5.

### Required Headers

| Header          | Value                                  |
|-----------------|----------------------------------------|
| `Authorization` | `Token {MIST_API_TOKEN}`               |
| `Accept`        | `application/json`                     |

## 200 Response Schema

```json
{
  "type": "object",
  "required": ["distinct", "end", "limit", "results", "start", "total"],
  "properties": {
    "distinct": { "type": "string" },
    "end":      { "type": "integer", "contentEncoding": "int32" },
    "limit":    { "type": "integer", "contentEncoding": "int32" },
    "start":    { "type": "integer", "contentEncoding": "int32" },
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

The dynamic key inside each `results[]` item carries the bucket value. Its key name
equals the `distinct` query parameter the caller passed in -- for example with
`distinct=port_id`, each item is `{"count": 17, "port_id": "ge-0/0/1"}`.

## Error Responses and MistHelper Handling

| Status | OpenAPI Description                                                                 | MistHelper Handling                                                                                       |
|--------|-------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| 400    | Bad Syntax                                                                          | `logging.warning("Bad request: %s", err)` and return early without writing output.                        |
| 401    | Unauthorized                                                                        | `logging.error("Auth failed -- check MIST_API_TOKEN")` and exit cleanly with non-zero return code.        |
| 403    | Permission Denied                                                                   | `logging.error("Permission denied for org %s", org_id)` and return early.                                 |
| 404    | Not found (endpoint or resource does not exist)                                     | `logging.warning("Org %s not found or endpoint unavailable", org_id)` and return early.                   |
| 429    | Too Many Requests (5000 calls/hour exceeded)                                        | Hand off to the existing adaptive delay system in `delay_metrics.json` / `tuning_data.json`; auto-retry. |
| 5xx    | Server error                                                                        | Standard MistHelper retry-with-backoff up to the configured cap; surface final failure as `ERROR` log.    |

In every error path, no traceback is printed to stdout; the user sees a single ASCII
warning/error line and the menu returns control to the main loop. `safe_input()`
already covers `EOFError` for SSH/container disconnects.

## mistapi Python Call Signature

```python
import mistapi                                                # Top-level package
from mistapi.api.v1.orgs.stats_ports import countOrgSwOrGwPorts  # Per docs/api/

response = countOrgSwOrGwPorts(                               # SDK function
    apisession,                                               # mistapi.APISession built from .env
    org_id,                                                   # Path parameter (UUID string)
    distinct="port_id",                                       # Required group attribute
    site_id=None,                                             # Optional UUID filter or None
    up=None,                                                  # Optional boolean filter or None
    duration="1d",                                            # Window string
    limit=100,                                                # API default page size
)

payload = response.data                                       # Parsed JSON envelope
distinct_field = payload["distinct"]                          # Echo of caller input
results = payload["results"]                                  # List of {count, <distinct>:value}
start_epoch = payload["start"]                                # Window start (epoch sec)
end_epoch = payload["end"]                                    # Window end (epoch sec)
total = payload["total"]                                      # Server-side bucket count
```

The SDK module path matches the enriched endpoint doc and the established mistapi
0.59+ naming pattern (OpenAPI tag `Orgs Stats - Ports` -> Python module
`mistapi.api.v1.orgs.stats_ports`).
