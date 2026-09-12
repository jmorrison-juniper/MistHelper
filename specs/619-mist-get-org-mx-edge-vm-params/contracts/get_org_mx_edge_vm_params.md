# Endpoint Contract: getOrgMxEdgeVmParams

**Spec**: [../spec.md](../spec.md)
**Plan**: [../plan.md](../plan.md)
**Source doc**: `documentation/api/orgs/GET_orgs_org_id_mxedges_mxedge_id_vm_params.md`
**Date**: 2026-06-30

## HTTP Contract

| Attribute       | Value                                                                       |
|-----------------|-----------------------------------------------------------------------------|
| **Method**      | `GET`                                                                       |
| **URL**         | `https://{mist_host}/api/v1/orgs/{org_id}/mxedges/{mxedge_id}/vm_params`    |
| **Auth**        | `Authorization: Token {api_token}` header (provided automatically by `mistapi.APISession`) |
| **Tag**         | `Orgs MxEdges`                                                              |
| **operationId** | `getOrgMxEdgeVmParams`                                                      |

### Path Parameters

| Name        | Type          | Required | Description                                                                 |
|-------------|---------------|----------|-----------------------------------------------------------------------------|
| `org_id`    | string (UUID) | Yes      | Organization UUID. Validated client-side by MistHelper via `is_valid_uuid()` before the call. |
| `mxedge_id` | string (UUID) | Yes      | Mist Edge appliance UUID. Validated client-side by MistHelper via `is_valid_uuid()` before the call. |

### Query Parameters

None.

### Request Headers

| Header           | Value                  | Notes                                                                |
|------------------|------------------------|----------------------------------------------------------------------|
| `Authorization`  | `Token <api_token>`    | Injected by `mistapi.APISession` from `.env`. Never logged.          |
| `Accept`         | `application/json`     | Default for mistapi SDK.                                             |
| `User-Agent`     | `mistapi/<version>`    | Set by SDK.                                                          |

### Request Body

None. This is a GET.

## Response Contract

### 200 OK

```json
{
  "model": "ME-VM",
  "name": "edge-vm-lab1",
  "user_data": "I2Nsb3VkLWNvbmZpZwphdXRvX2luc3RhbGw6IHRydWUKLi4u"
}
```

| Field        | Type   | Description                                                                                                                                          |
|--------------|--------|------------------------------------------------------------------------------------------------------------------------------------------------------|
| `model`      | string | VM SKU. Example: `ME-VM`. Currently the only known value; MistHelper stores the raw string without enum validation so future SKUs flow through.       |
| `name`       | string | Optional user-supplied display name for the VM. May be absent or empty.                                                                              |
| `user_data`  | string | Base64-encoded cloud-init user data used by the Mist Edge VM on first boot. **Sensitive**: may contain bootstrap credentials. Never logged in full. |

The response is a single JSON object (not a list, not paginated, no envelope).

### Error Responses

| Status | Mist Description                                                              | MistHelper Handling                                                                                                                                              |
|--------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 400    | Bad Syntax                                                                    | Log `WARNING` ("Mist returned 400 -- check org_id / mxedge_id format"), no traceback, return early.                                                              |
| 401    | Unauthorized                                                                  | Log `ERROR` ("Mist 401 -- check MIST_API_TOKEN in .env"). Do not retry. Return early.                                                                            |
| 403    | Permission Denied                                                             | Log `ERROR` ("Mist 403 -- token lacks read access to mxedge %s in org %s", mxedge_id, org_id). Return early.                                                     |
| 404    | Not found. Endpoint or resource does not exist                                | Log `WARNING` ("No VM params for mxedge %s in org %s (404)", mxedge_id, org_id). Treat as empty result and write zero rows. Return cleanly.                      |
| 429    | Too Many Requests (5000 calls/hour token threshold exceeded)                  | Adaptive delay system (`delay_metrics.json` + `tuning_data.json`) backs off and retries automatically up to the configured retry cap. No user intervention.      |

All non-200 responses are surfaced as ASCII log lines only. The API token is
never included in any log message, even at `DEBUG`. The raw `user_data`
field is never included in any log message at any level -- only its length
and a 6-character SHA-256 prefix.

## mistapi Python SDK Call Signature

```python
import os
import mistapi
from mistapi.api.v1.orgs.mxedges import vm_params as vm_params_module

apisession = mistapi.APISession(host=os.environ["MIST_HOST"],
                                apitoken=os.environ["MIST_API_TOKEN"])
apisession.login()

response = vm_params_module.getOrgMxEdgeVmParams(
    apisession,
    org_id="0a1b2c3d-1234-5678-9abc-def012345678",
    mxedge_id="4e5f6a7b-89ab-cdef-0123-456789abcdef",
)

body = response.data           # dict matching the 200 OK schema above
http_status = response.status_code
```

Notes:

- The SDK module path mirrors the OpenAPI URL path
  (`/orgs/{org_id}/mxedges/{mxedge_id}/vm_params` ->
  `mistapi.api.v1.orgs.mxedges.vm_params`). The enriched per-endpoint doc
  lists the shorter form `mistapi.api.v1.orgs.mxedges.getOrgMxEdgeVmParams()`,
  which is retained as a fallback import if the deeper module is not
  exposed in the installed `mistapi` version. Final verification at
  implementation time via
  `python -c "from mistapi.api.v1.orgs.mxedges import vm_params; help(vm_params)"`.
- `response.data` is `None` only when the HTTP response had no body (rare).
  MistHelper normalizes this to `{}` before flattening.
- This SDK call takes positional path parameters (`org_id`, `mxedge_id`).
  There are no keyword-only query parameters because the endpoint has none.

## Pagination

Not paginated. The endpoint returns a single JSON object per call. No
`limit` / `page` / `start` / `end` parameters apply.

## Rate Limiting

Standard Mist API rate limit: 5000 calls per token per hour. MistHelper's
adaptive delay system (`delay_metrics.json` per-endpoint state +
`tuning_data.json` learning) governs back-off automatically. No
endpoint-specific tuning required for this contract because each invocation
is a single small GET.

## Security Notes

- `user_data` is the cloud-init payload used to bootstrap a Mist Edge VM.
  Cleartext cloud-init data routinely contains SSH keys, root passwords, or
  IPsec PSKs. The base64 wrapper is *encoding*, not encryption, and offers
  no confidentiality on its own.
- MistHelper persists the base64 string verbatim in the configured output
  backend (CSV / SQLite / ArangoDB+Redis) so operators retain operational
  fidelity, but **never** writes the content to a `logging` stream. The
  `user_data_sha256` column in the data model serves as a non-sensitive
  change indicator for audit dashboards that should not display the
  payload itself.
- Downstream tooling that decodes the base64 to inspect cleartext is the
  responsibility of the operator and is out of scope for this menu item.
