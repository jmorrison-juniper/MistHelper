# Endpoint Contract: getOrgStats

**Spec**: [../spec.md](../spec.md)
**Plan**: [../plan.md](../plan.md)
**Source doc**: `documentation/api/orgs/GET_orgs_org_id_stats.md`
**Date**: 2026-07-01

## HTTP Contract

| Attribute       | Value                                                    |
|-----------------|----------------------------------------------------------|
| **Method**      | `GET`                                                    |
| **URL**         | `https://{mist_host}/api/v1/orgs/{org_id}/stats`         |
| **Auth**        | `Authorization: Token {api_token}` header (provided automatically by `mistapi.APISession`) |
| **Tag**         | `Orgs Stats`                                             |
| **operationId** | `getOrgStats`                                            |

### Path Parameters

| Name     | Type          | Required | Description                                     |
|----------|---------------|----------|-------------------------------------------------|
| `org_id` | string (UUID) | Yes      | Organization UUID. Validated client-side by MistHelper via `is_valid_uuid()` before the call. |

### Query Parameters

| Name       | Type    | Required | Default  | Description |
|------------|---------|----------|----------|-------------|
| `start`    | string  | No       | (absent) | Start of time range. Epoch seconds or relative string (`-1d`, `-1w`). Mutually exclusive with `duration`. Not exposed in the MistHelper prompt. |
| `end`      | string  | No       | (absent) | End of time range. Epoch seconds or relative string (`now`, `-1h`). Mutually exclusive with `duration`. Not exposed in the MistHelper prompt. |
| `duration` | string  | No       | `1d`     | Duration window (e.g. `7d`, `2w`). Passed through verbatim from the MistHelper prompt. |
| `limit`    | integer | No       | `100`    | Advertised pagination limit. Response is a single JSON object, so this parameter has no observable effect. Not exposed in the MistHelper prompt. |
| `page`     | integer | No       | `1`      | Advertised pagination page number. Response is a single JSON object, so this parameter has no observable effect. Not exposed in the MistHelper prompt. |

### Request Headers

| Header          | Value                       | Notes |
|-----------------|-----------------------------|-------|
| `Authorization` | `Token <api_token>`         | Injected by `mistapi.APISession` from `.env`. Never logged. |
| `Accept`        | `application/json`          | Default for mistapi SDK. |
| `User-Agent`    | `mistapi/<version>`         | Set by SDK. |

### Request Body

None. This is a GET.

## Response Contract

### 200 OK

```json
{
  "id": "53f10664-3ce8-4c27-b382-0ef66432349f",
  "name": "Acme Networks",
  "msp_id": "b9d42c2e-88ee-41f8-b798-f009ce7fe909",
  "alarmtemplate_id": "0a1b2c3d-4444-5555-6666-777788889999",
  "allow_mist": true,
  "orggroup_ids": [
    "11111111-2222-3333-4444-555555555555"
  ],
  "session_expiry": 86400,
  "num_sites": 42,
  "num_inventory": 512,
  "num_devices": 310,
  "num_devices_connected": 305,
  "num_devices_disconnected": 5,
  "created_time": 1610000000,
  "modified_time": 1719600000.123,
  "sle": [
    {"path": "wifi",  "user_minutes": {"ok": 12345.0, "total": 12500.0}},
    {"path": "wan",   "user_minutes": {"ok":  9800.0, "total":  9820.0}},
    {"path": "wired", "user_minutes": {"ok":  7654.0, "total":  7654.0}}
  ]
}
```

| Field                       | Type            | Description |
|-----------------------------|-----------------|-------------|
| `id`                        | string (UUID)   | Org UUID. Required. Read-only. |
| `name`                      | string          | Human-readable org name. Required. |
| `msp_id`                    | string (UUID)   | Parent MSP UUID if any. Required. Read-only. |
| `alarmtemplate_id`          | string (UUID)   | Active alarm template UUID. Required. |
| `allow_mist`                | boolean         | Whether Mist is allowed to access support diagnostics. Required. |
| `orggroup_ids`              | string[] (UUID) | Org-group memberships. Required (may be empty array). |
| `session_expiry`            | int64           | UI session expiry in seconds. Required. |
| `num_sites`                 | int32           | Total site count. Required. |
| `num_inventory`             | int32           | Total inventory item count. Required. |
| `num_devices`               | int32           | Total device count. Required. |
| `num_devices_connected`     | int32           | Currently-connected device count. Required. |
| `num_devices_disconnected`  | int32           | Currently-disconnected device count. Required. |
| `created_time`              | number (epoch)  | Org creation epoch seconds. Required. Read-only. |
| `modified_time`             | number (epoch)  | Last-modified epoch seconds. Required. Read-only. |
| `sle`                       | object[]        | Per-path SLE health. Required. Unique on `path`. Each element `{path, user_minutes: {ok, total}}`. |

### Error Responses

| Status | Mist Description                                                          | MistHelper Handling |
|--------|---------------------------------------------------------------------------|---------------------|
| 400    | Bad Syntax                                                                | Log `WARNING` ("Mist returned 400 -- check org_id and duration format"), no traceback, return early. |
| 401    | Unauthorized                                                              | Log `ERROR` ("Mist 401 -- check MIST_API_TOKEN in .env"). Do not retry. Return early. |
| 403    | Permission Denied                                                         | Log `ERROR` ("Mist 403 -- token lacks read access to org %s", org_id). Return early. |
| 404    | Not found. Endpoint or resource does not exist                            | Log `WARNING` ("Org %s not found or has no stats", org_id). Write zero rows. Return cleanly. |
| 429    | Too Many Requests (5000 calls/hour token threshold exceeded)              | Adaptive delay system (`delay_metrics.json` + `tuning_data.json`) backs off and retries automatically up to the configured retry cap. No user intervention. |

All non-200 responses are surfaced as ASCII log lines only. The API token is
never included in any log message, even at `DEBUG`.

## mistapi Python SDK Call Signature

```python
import mistapi
from mistapi.api.v1.orgs import stats as org_stats_module

apisession = mistapi.APISession(host=os.environ["MIST_HOST"],
                                apitoken=os.environ["MIST_API_TOKEN"])
apisession.login()

# Default 1-day window (MistHelper default prompt):
response = org_stats_module.getOrgStats(
    apisession,
    org_id="0a1b2c3d-1234-5678-9abc-def012345678",
)

# Explicit 7-day window:
response = org_stats_module.getOrgStats(
    apisession,
    org_id="0a1b2c3d-1234-5678-9abc-def012345678",
    duration="7d",
)

# Explicit epoch window (not exposed in the MistHelper prompt; available if
# invoked programmatically):
response = org_stats_module.getOrgStats(
    apisession,
    org_id="0a1b2c3d-1234-5678-9abc-def012345678",
    start=1719000000,
    end=1719600000,
)

# Access the parsed body:
body = response.data           # dict matching the 200 OK schema above
http_status = response.status_code
```

Notes:

- The SDK module path mirrors the OpenAPI URL path (`/orgs/{org_id}/stats` ->
  `mistapi.api.v1.orgs.stats`). Adjacent stats endpoints under the same URL
  (`GET /orgs/{org_id}/stats/sites` -> `mistapi.api.v1.orgs.stats.sites`,
  `GET /orgs/{org_id}/stats/devices` -> `mistapi.api.v1.orgs.stats.devices`)
  confirm the URL-based path is canonical. Final verification happens at
  implementation via
  `python -c "from mistapi.api.v1.orgs import stats; help(stats.getOrgStats)"`.
- `response.data` is `None` only when the HTTP response had no body (rare).
  MistHelper normalizes this to `{}` before flattening.
- Pass `duration` as a Python string. Do not pass `start`/`end` alongside
  `duration` in the same call -- the Mist API treats them as mutually exclusive
  and prefers `duration` when both are supplied.
- `limit` and `page` are accepted by the SDK but have no observable effect on
  this endpoint; MistHelper omits them.

## Pagination

Advertised in the OpenAPI doc (`limit`, `page`), but the 200 response schema is a
single JSON object rather than a paged array. MistHelper does not iterate pages
for this endpoint; a single call returns the full snapshot.

## Rate Limiting

Standard Mist API rate limit: 5000 calls per token per hour. MistHelper's
adaptive delay system (`delay_metrics.json` per-endpoint state +
`tuning_data.json` learning) governs back-off automatically. No endpoint-specific
tuning required for this contract.
