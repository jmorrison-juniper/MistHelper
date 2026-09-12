# Endpoint Contract: GetOrgLicenseAsyncClaimStatus

**Spec**: [../spec.md](../spec.md)
**Plan**: [../plan.md](../plan.md)
**Source doc**: `documentation/api/orgs/GET_orgs_org_id_claim_status.md`
**Date**: 2026-06-28

## HTTP Contract

| Attribute    | Value                                       |
|--------------|---------------------------------------------|
| **Method**   | `GET`                                       |
| **URL**      | `https://{mist_host}/api/v1/orgs/{org_id}/claim/status` |
| **Auth**     | `Authorization: Token {api_token}` header (provided automatically by `mistapi.APISession`) |
| **Tag**      | `Orgs Licenses`                             |
| **operationId** | `GetOrgLicenseAsyncClaimStatus`          |

### Path Parameters

| Name     | Type   | Required | Description                                          |
|----------|--------|----------|------------------------------------------------------|
| `org_id` | string (UUID) | Yes | Organization UUID. Validated client-side by MistHelper via `is_valid_uuid()` before the call. |

### Query Parameters

| Name     | Type    | Required | Default | Description |
|----------|---------|----------|---------|-------------|
| `detail` | boolean | No       | (absent) | When `true`, the response includes a `details` array with one entry per device in the claim job. When omitted or `false`, the `details` array is not present. |

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
  "status": "ongoing",
  "total": 120,
  "processed": 82,
  "succeed": 80,
  "failed": 2,
  "scheduled_at": 1719600000,
  "timestamp": 1719603612.123,
  "completed": ["aabbccddee01", "aabbccddee02"],
  "incompleted": ["aabbccddee03", "aabbccddee04"],
  "details": [
    {"mac": "aabbccddee01", "status": "succeeded", "timestamp": 1719600100.0},
    {"mac": "aabbccddee02", "status": "succeeded", "timestamp": 1719600200.0},
    {"mac": "aabbccddee03", "status": "failed",    "timestamp": 1719600300.0}
  ]
}
```

| Field           | Type     | Description |
|-----------------|----------|-------------|
| `status`        | string enum | `prepared`, `ongoing`, or `done`. |
| `total`         | int32    | Total devices included in the claim job. |
| `processed`     | int32    | Devices processed so far. |
| `succeed`       | int32    | Devices successfully claimed so far. |
| `failed`        | int32    | Devices that failed so far. |
| `scheduled_at`  | int32 (epoch seconds) | Time the job was scheduled. Stable across polls -- used as part of the MistHelper composite primary key. |
| `timestamp`     | number (epoch seconds) | Server-side response generation time. Read-only. |
| `completed`     | string[] | MAC addresses of devices already processed. |
| `incompleted`   | string[] | MAC addresses of devices still pending. |
| `details`       | object[] | Per-device records. Only present when `detail=true`. Each item: `{mac, status, timestamp}`. |

### Error Responses

| Status | Mist Description                                                   | MistHelper Handling |
|--------|--------------------------------------------------------------------|---------------------|
| 400    | Bad Syntax                                                         | Log `WARNING` ("Mist returned 400 -- check org_id format"), no traceback, return early. |
| 401    | Unauthorized                                                       | Log `ERROR` ("Mist 401 -- check MIST_API_TOKEN in .env"). Do not retry. Return early. |
| 403    | Permission Denied                                                  | Log `ERROR` ("Mist 403 -- token lacks read access to org %s", org_id). Return early. |
| 404    | Not found. Endpoint or resource does not exist                     | Log `WARNING` ("No async claim job for org %s", org_id). Treat as empty result and write zero rows. Return cleanly. |
| 429    | Too Many Requests (5000 calls/hour token threshold exceeded)       | Adaptive delay system (`delay_metrics.json` + `tuning_data.json`) backs off and retries automatically up to the configured retry cap. No user intervention. |

All non-200 responses are surfaced as ASCII log lines only. The API token is never
included in any log message, even at `DEBUG`.

## mistapi Python SDK Call Signature

```python
import mistapi
from mistapi.api.v1.orgs.claim import status as claim_status_module

apisession = mistapi.APISession(host=os.environ["MIST_HOST"],
                                apitoken=os.environ["MIST_API_TOKEN"])
apisession.login()

# Without per-device detail (summary only):
response = claim_status_module.getOrgLicenseAsyncClaimStatus(
    apisession,
    org_id="0a1b2c3d-1234-5678-9abc-def012345678",
)

# With per-device detail:
response = claim_status_module.getOrgLicenseAsyncClaimStatus(
    apisession,
    org_id="0a1b2c3d-1234-5678-9abc-def012345678",
    detail=True,
)

# Access the parsed body:
body = response.data           # dict matching the 200 OK schema above
http_status = response.status_code
```

Notes:

- The SDK module path mirrors the OpenAPI URL path (`/orgs/{org_id}/claim/status` ->
  `mistapi.api.v1.orgs.claim.status`). The enriched per-endpoint doc lists the SDK as
  `mistapi.api.v1.orgs.licenses.GetOrgLicenseAsyncClaimStatus()`, but adjacent endpoints
  under the same URL (`POST /orgs/{org_id}/claim` -> `mistapi.api.v1.orgs.claim`)
  confirm the URL-based path is canonical. Final verification happens at implementation
  via `python -c "from mistapi.api.v1.orgs.claim import status; help(status)"`.
- `response.data` is `None` only when the HTTP response had no body (rare). MistHelper
  normalizes this to `{}` before flattening.
- The `detail` parameter is passed as a Python `bool`. The SDK serializes `True` as the
  query string `?detail=true` and omits the parameter entirely when the value is `None`
  (preferred over passing `False`, which would still add `?detail=false` to the URL).

## Pagination

Not paginated. The endpoint returns a single JSON object per call. No `limit`/`page`
parameters apply.

## Rate Limiting

Standard Mist API rate limit: 5000 calls per token per hour. MistHelper's adaptive delay
system (`delay_metrics.json` per-endpoint state + `tuning_data.json` learning) governs
back-off automatically. No endpoint-specific tuning required for this contract.
