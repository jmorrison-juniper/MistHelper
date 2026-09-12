# Endpoint Contract: getOrgUserMac

**Spec**: [../spec.md](../spec.md)
**Plan**: [../plan.md](../plan.md)
**Source doc**: `documentation/api/orgs/GET_orgs_org_id_usermacs_usermac_id.md`
**Date**: 2026-07-01

## HTTP Contract

| Attribute       | Value                                                             |
|-----------------|-------------------------------------------------------------------|
| **Method**      | `GET`                                                             |
| **URL**         | `https://{mist_host}/api/v1/orgs/{org_id}/usermacs/{usermac_id}`  |
| **Auth**        | `Authorization: Token {api_token}` header (provided automatically by `mistapi.APISession`) |
| **Tag**         | `Orgs User MACs`                                                  |
| **operationId** | `getOrgUserMac`                                                   |

### Path Parameters

| Name         | Type          | Required | Description                                                                                     |
|--------------|---------------|----------|-------------------------------------------------------------------------------------------------|
| `org_id`     | string (UUID) | Yes      | Organization UUID. Validated client-side by MistHelper via `is_valid_uuid()` before the call.   |
| `usermac_id` | string (UUID) | Yes      | User-MAC record UUID within the org. Validated client-side by `is_valid_uuid()` before the call.|

### Query Parameters

None. This endpoint has no query parameters.

### Request Headers

| Header          | Value                    | Notes                                                                        |
|-----------------|--------------------------|------------------------------------------------------------------------------|
| `Authorization` | `Token <api_token>`      | Injected by `mistapi.APISession` from `.env`. Never logged.                  |
| `Accept`        | `application/json`       | Default for mistapi SDK.                                                     |
| `User-Agent`    | `mistapi/<version>`      | Set by SDK.                                                                  |

### Request Body

None. This is a GET.

## Response Contract

### 200 OK

```json
{
  "id": "53f10664-3ce8-4c27-b382-0ef66432349f",
  "mac": "5684dae9ac8b",
  "name": "Printer2",
  "notes": "mac address refers to Canon printers",
  "labels": ["byod", "flr1"],
  "radius_group": "VIP",
  "vlan": "30"
}
```

| Field          | Type            | Required | Description |
|----------------|-----------------|----------|-------------|
| `id`           | string (UUID)   | No       | Unique ID of the user-MAC object instance in the Mist Organization. Read-only. Serves as the MistHelper natural primary key. |
| `mac`          | string          | **Yes**  | The user MAC address. Only non-local-admin MACs are accepted by Mist. This is the only field declared `required` in the 200 OK schema. |
| `name`         | string          | No       | Human-readable display name (e.g. `Printer2`). |
| `notes`        | string          | No       | Free-text notes (e.g. `mac address refers to Canon printers`). |
| `labels`       | string[]        | No       | Tag list (e.g. `["byod","flr1"]`). MistHelper flattens this to a pipe-delimited string plus a `labels_count` integer for SQL-friendly storage. |
| `radius_group` | string          | No       | RADIUS group name for policy assignment (e.g. `VIP`). |
| `vlan`         | string          | No       | VLAN ID stored as a string (e.g. `"30"`). MistHelper preserves the string type to match the API contract. |

### Error Responses

| Status | Mist Description                                                                                                  | MistHelper Handling |
|--------|-------------------------------------------------------------------------------------------------------------------|---------------------|
| 400    | Bad Syntax                                                                                                        | Log `WARNING` ("Mist returned 400 -- check org_id/usermac_id format"), no traceback, return early. |
| 401    | Unauthorized                                                                                                      | Log `ERROR` ("Mist 401 -- check MIST_API_TOKEN in .env"). Do not retry. Return early. |
| 403    | Permission Denied                                                                                                 | Log `ERROR` ("Mist 403 -- token lacks read access to org %s", org_id). Return early. |
| 404    | Not found. The API endpoint doesn't exist or resource doesn't exist                                               | Log `WARNING` ("No user MAC %s in org %s", usermac_id, org_id). Treat as empty result and write zero rows. Return cleanly. |
| 429    | Too Many Requests. The API Token used for the request reached the 5000 API Calls per hour threshold              | Adaptive delay system (`delay_metrics.json` + `tuning_data.json`) backs off and retries automatically up to the configured retry cap. No user intervention. |

All non-200 responses are surfaced as ASCII log lines only. The API token is
never included in any log message, even at `DEBUG`.

## mistapi Python SDK Call Signature

```python
import mistapi
from mistapi.api.v1.orgs import user_macs   # module path per enriched OpenAPI doc

apisession = mistapi.APISession(host=os.environ["MIST_HOST"],
                                apitoken=os.environ["MIST_API_TOKEN"])
apisession.login()

# Single-record fetch (only path parameters, no query, no body):
response = user_macs.getOrgUserMac(
    apisession,
    org_id="0a1b2c3d-1234-5678-9abc-def012345678",
    usermac_id="53f10664-3ce8-4c27-b382-0ef66432349f",
)

# Access the parsed body and status code:
body = response.data           # dict matching the 200 OK schema above (or None on empty body)
http_status = response.status_code
```

Notes:

- The enriched per-endpoint doc lists the SDK module path as
  `mistapi.api.v1.orgs.user_macs.getOrgUserMac()` (with an underscore --
  `user_macs`). The spec.md lists the module as `mistapi.api.v1.orgs.usermacs`
  as a human-readable summary; the enriched doc is the authoritative source
  for the SDK path. Final verification happens at implementation via
  `python -c "from mistapi.api.v1.orgs import user_macs; help(user_macs.getOrgUserMac)"`
  inside the venv.
- `response.data` is `None` only when the HTTP response had no body (rare).
  MistHelper normalizes this to `{}` before flattening.
- The two path parameters are positional after `apisession`. Passing them as
  keyword arguments (`org_id=...`, `usermac_id=...`) is preferred for
  readability.

## Pagination

Not paginated. The endpoint returns a single JSON object per call. No
`limit`, `page`, `start`, or `end` parameters apply.

## Rate Limiting

Standard Mist API rate limit: 5000 calls per token per hour. MistHelper's
adaptive delay system (`delay_metrics.json` per-endpoint state +
`tuning_data.json` learning) governs back-off automatically. No
endpoint-specific tuning required for this contract.
