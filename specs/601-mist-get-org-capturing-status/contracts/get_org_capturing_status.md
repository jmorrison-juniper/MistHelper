# Endpoint Contract: getOrgCapturingStatus

**Spec**: [../spec.md](../spec.md)
**Plan**: [../plan.md](../plan.md)
**Source doc**: `documentation/api/utilities/GET_orgs_org_id_pcaps_capture.md`
**Date**: 2026-06-30

## HTTP Contract

| Attribute       | Value                                                              |
|-----------------|--------------------------------------------------------------------|
| **Method**      | `GET`                                                              |
| **URL**         | `https://{mist_host}/api/v1/orgs/{org_id}/pcaps/capture`           |
| **Auth**        | `Authorization: Token {api_token}` header (injected automatically by `mistapi.APISession`) |
| **Tag**         | `Utilities PCAPs`                                                  |
| **operationId** | `getOrgCapturingStatus`                                            |

### Path Parameters

| Name     | Type          | Required | Description                                                                |
|----------|---------------|----------|----------------------------------------------------------------------------|
| `org_id` | string (UUID) | Yes      | Organization UUID. Validated client-side by MistHelper via `is_valid_uuid()` before the call. |

### Query Parameters

None. The endpoint takes no query parameters.

### Request Headers

| Header          | Value                  | Notes                                                                |
|-----------------|------------------------|----------------------------------------------------------------------|
| `Authorization` | `Token <api_token>`    | Injected by `mistapi.APISession` from `.env`. Never logged.          |
| `Accept`        | `application/json`     | Default for the mistapi SDK.                                         |
| `User-Agent`    | `mistapi/<version>`    | Set by the SDK.                                                      |

### Request Body

None. This is a GET.

## Response Contract

### 200 OK

A single JSON object describing the currently-active org-level packet capture.
Required fields per schema: `id`, `type`. Example payload (synthesized from the
enriched per-endpoint doc examples):

```json
{
  "id": "53f10664-3ce8-4c27-b382-0ef66432349f",
  "type": "wireless",
  "format": "stream",
  "ap_mac": null,
  "client_mac": "60a10a773412",
  "ssid": null,
  "duration": 300,
  "started_time": 1435080709,
  "max_num_packets": 1000,
  "max_pkt_len": 128,
  "num_packets": 1283,
  "includes_mcast": true,
  "aps": ["5c5b35000010", "5c5b35000011"],
  "ok": ["5c5b35000010"],
  "failed": ["5c5b35000011"],
  "switches": [],
  "gateways": [],
  "mxedges": [],
  "tcpdump_expression": "ether host 60:a1:0a:77:34:12",
  "radiotap_tcpdump_expression": "",
  "scan_tcpdump_expression": "",
  "wired_tcpdump_expression": "",
  "wireless_tcpdump_expression": "type mgt subtype probe-req",
  "tzsp_host": "",
  "tzsp_port": 0,
  "pcap_aps": {
    "5c5b35000010": {
      "band": 6,
      "bandwidth": 20,
      "channel": 133,
      "tcpdump_expression": null
    }
  }
}
```

| Field             | Type               | Description |
|-------------------|--------------------|-------------|
| `id`              | string (UUID, readOnly, REQUIRED) | Unique capture instance ID. Used as the MistHelper natural primary key for the summary table. |
| `type`            | string enum (REQUIRED) | One of `client`, `gateway`, `new_assoc`, `radiotap`, `radiotap,wired`, `wired`, `wireless`. |
| `format`          | string             | `stream` (to Mist cloud) or `tzsp` (UDP TZSP packets to remote Wireshark host). |
| `ap_mac`          | string / null      | Specific AP being captured (client / new_assoc types). |
| `client_mac`      | string / null      | Target client MAC (e.g., `60a10a773412`). |
| `ssid`            | string / null      | SSID filter. |
| `duration`        | int32 (seconds)    | Configured capture duration. |
| `started_time`    | int32 (epoch seconds) | Time capture started. |
| `max_num_packets` | int32              | User-configured packet cap. |
| `max_pkt_len`     | int32              | Max bytes captured per packet. |
| `num_packets`     | int32              | Total packets captured by all APs. Not applicable for `type=client` / `new_assoc`. |
| `includes_mcast`  | boolean            | Whether multicast frames are included. |
| `aps`             | string[]           | Target AP MACs configured to capture. |
| `ok`              | string[]           | Subset of `aps` successfully configured. |
| `failed`          | string[]           | Subset of `aps` whose configuration attempt failed. |
| `switches`        | string[]           | Switch IDs in scope (gateway capture types). |
| `gateways`        | string[]           | Gateway IDs in scope. |
| `mxedges`         | string[]           | Mxedge IDs in scope. |
| `tcpdump_expression` | string          | Common tcpdump filter. |
| `radiotap_tcpdump_expression` | string | When `type=radiotap`, the radiotap filter provided by the user. |
| `scan_tcpdump_expression` | string     | When `type=scan`, the scan filter provided by the user. |
| `wired_tcpdump_expression` | string    | When `type=wired`, the wired filter. |
| `wireless_tcpdump_expression` | string | When `type=wireless`, the wireless filter. |
| `tzsp_host`       | string             | Required when `format=tzsp`. Remote host (mxedge-reachable) that receives TZSP packets. |
| `tzsp_port`       | int (1-65535)      | Required when `format=tzsp`. Receiver port. |
| `pcap_aps`        | object             | Map keyed by AP MAC -> `{band, bandwidth, channel, tcpdump_expression}`. Flattened by MistHelper into the per-AP detail table. |

### Error Responses

| Status | Mist Description                                                          | MistHelper Handling |
|--------|---------------------------------------------------------------------------|---------------------|
| 400    | Bad Syntax                                                                | Log `WARNING` ("Mist returned 400 -- check org_id format"). No traceback. Return early with zero rows written. |
| 401    | Unauthorized                                                              | Log `ERROR` ("Mist 401 -- check MIST_API_TOKEN in .env"). Do not retry. Return early. |
| 403    | Permission Denied                                                         | Log `ERROR` ("Mist 403 -- token lacks read access to org %s", org_id). Return early. |
| 404    | Not found. Endpoint or resource does not exist                            | Per the enriched doc's Gotchas: "Returns 404 if no capture is currently active." Treated as a benign no-op. Log `WARNING` ("No active capture for org %s (404)"). Write zero rows. Exit 0. |
| 429    | Too Many Requests (5000 calls / hour / token threshold exceeded)          | Adaptive delay system (`delay_metrics.json` + `tuning_data.json`) backs off and retries automatically up to the configured retry cap. No user intervention. |

All non-200 responses surface as ASCII log lines only. The API token is never
included in any log message, even at `DEBUG`. Request URLs are not logged either,
to avoid leaking org UUIDs from shell-history-piped log captures.

## mistapi Python SDK Call Signature

```python
import os
import mistapi
from mistapi.api.v1.orgs.pcaps import capture as capture_module

apisession = mistapi.APISession(
    host=os.environ["MIST_HOST"],                 # e.g., "api.mist.com"
    apitoken=os.environ["MIST_API_TOKEN"],
)
apisession.login()

# Single call -- no query parameters supported.
response = capture_module.getOrgCapturingStatus(
    apisession,
    org_id="0a1b2c3d-1234-5678-9abc-def012345678",
)

# Access the parsed body and HTTP status.
body = response.data           # dict matching the 200 OK schema above, or None
http_status = response.status_code
```

Notes:

- The SDK module path mirrors the OpenAPI URL path
  (`/orgs/{org_id}/pcaps/capture` -> `mistapi.api.v1.orgs.pcaps.capture`).
  The enriched per-endpoint doc shows the function under
  `mistapi.api.v1.utilities.pcaps.getOrgCapturingStatus()` (the OpenAPI tag
  `Utilities PCAPs`), but adjacent endpoints on the same URL
  (`POST /api/v1/orgs/{org_id}/pcaps/capture` ->
  `mistapi.api.v1.orgs.pcaps.capture`; `DELETE /api/v1/orgs/{org_id}/pcaps/capture`
  -> same) confirm the URL-based path is canonical. Final verification at
  implementation time:
  `python -c "from mistapi.api.v1.orgs.pcaps import capture; help(capture)"`.
- `response.data` is `None` when the HTTP response had no body (e.g., 404).
  MistHelper normalizes this to `{}` before flattening.
- There are no optional or query parameters; the SDK signature is positional
  `(apisession, org_id)`.
- The `pcap_aps` value may be absent or an empty dict if Mist has not yet
  populated per-AP detail. MistHelper writes the per-AP CSV / SQLite table only
  when this map is non-empty.

## Pagination

Not paginated. The endpoint returns a single JSON object per call. No
`limit`/`page` parameters apply.

## Rate Limiting

Standard Mist API rate limit: 5000 calls per token per hour. MistHelper's adaptive
delay system (`delay_metrics.json` per-endpoint state + `tuning_data.json` learning)
governs back-off automatically. No endpoint-specific tuning required for this
contract -- the response is small and the call is cheap.
