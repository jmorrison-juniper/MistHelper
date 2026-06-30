# Endpoint Contract: getOrgNacCrl

**Spec**: [../spec.md](../spec.md)
**Plan**: [../plan.md](../plan.md)
**Source doc**: `documentation/api/orgs/GET_orgs_org_id_setting_mist_nac_crls.md`
**Date**: 2026-06-30

## HTTP Contract

| Attribute       | Value                                                                  |
|-----------------|------------------------------------------------------------------------|
| **Method**      | `GET`                                                                  |
| **URL**         | `https://{mist_host}/api/v1/orgs/{org_id}/setting/mist_nac_crls`       |
| **Auth**        | `Authorization: Token {api_token}` header (injected by `mistapi.APISession`) |
| **Tag**         | `Orgs NAC CRL`                                                         |
| **operationId** | `getOrgNacCrl`                                                         |

### Path Parameters

| Name     | Type          | Required | Description                                                                                              |
|----------|---------------|----------|----------------------------------------------------------------------------------------------------------|
| `org_id` | string (UUID) | Yes      | Organization UUID. Validated client-side by MistHelper via `is_valid_uuid()` before the call is issued.  |

### Query Parameters

None. The endpoint takes no query parameters.

### Request Headers

| Header           | Value                  | Notes |
|------------------|------------------------|-------|
| `Authorization`  | `Token <api_token>`    | Injected by `mistapi.APISession` from `.env`. Never logged. |
| `Accept`         | `application/json`     | mistapi SDK default. |
| `User-Agent`     | `mistapi/<version>`    | Set by SDK. |

### Request Body

None. This is a GET.

## Response Contract

### 200 OK

```json
{
  "results": [
    {
      "id": "a1ca26f3-44dd-4833-9a7b-97bbb2ab5230",
      "name": "SampleCertificateSigner",
      "url": "http://url/to/crl_file",
      "created_time": 1719600000,
      "modified_time": 1719603612
    }
  ]
}
```

| Field                     | Type     | Description |
|---------------------------|----------|-------------|
| `results`                 | object[] | Array of uploaded CRL file records for the org. May be empty. |
| `results[].id`            | string (UUID) | Stable Mist-side UUID for the CRL file. Read-only. The MistHelper primary key. |
| `results[].name`          | string   | Issuer name for the CRL file (e.g., `SampleCertificateSigner`). Human-readable; set on upload. |
| `results[].url`           | string   | Download URL for the uploaded CRL file. |
| `results[].created_time`  | number (epoch seconds) | When the file was uploaded. Read-only. |
| `results[].modified_time` | number (epoch seconds) | When the file was last modified. Read-only. |

The response always includes the `results` key (even when no CRLs are uploaded
the value is an empty array). MistHelper treats a missing key defensively and
falls back to `[]`.

### Error Responses

| Status | Mist Description                                                  | MistHelper Handling |
|--------|-------------------------------------------------------------------|---------------------|
| 400    | Bad Syntax                                                        | Log `WARNING` ("Mist returned 400 -- check org_id format"). No traceback. Return early. |
| 401    | Unauthorized                                                      | Log `ERROR` ("Mist 401 -- check MIST_API_TOKEN in .env"). Do not retry. Return early. |
| 403    | Permission Denied                                                 | Log `ERROR` ("Mist 403 -- token lacks read access to org %s", org_id). Return early. |
| 404    | Not found. Endpoint or resource does not exist                    | Log `WARNING` ("No NAC CRL settings for org %s", org_id). Treat as empty result and write zero rows. Return cleanly. |
| 429    | Too Many Requests (5000 calls/hour per token)                     | Adaptive delay system (`delay_metrics.json` + `tuning_data.json`) backs off and retries up to the configured cap. No user intervention. |

All non-200 responses are surfaced as ASCII log lines only. The API token is
never included in any log message at any level, even `DEBUG`.

## mistapi Python SDK Call Signature

```python
import os
import mistapi
from mistapi.api.v1.orgs.setting import mist_nac_crls as nac_crl_module

apisession = mistapi.APISession(
    host=os.environ["MIST_HOST"],
    apitoken=os.environ["MIST_API_TOKEN"],
)
apisession.login()

response = nac_crl_module.getOrgNacCrl(
    apisession,
    org_id="0a1b2c3d-1234-5678-9abc-def012345678",
)

# Access the parsed body:
body = response.data            # dict matching the 200 OK schema above
http_status = response.status_code
results = body.get("results", []) or []
```

Notes:

- The SDK module path mirrors the OpenAPI URL path
  (`/orgs/{org_id}/setting/mist_nac_crls` ->
  `mistapi.api.v1.orgs.setting.mist_nac_crls`), which is also the path named by
  `spec.md`. The enriched per-endpoint doc hints at
  `mistapi.api.v1.orgs.nac_crl` as a possible alternative location; the
  implementation task confirms with
  `python -c "from mistapi.api.v1.orgs.setting import mist_nac_crls; help(mist_nac_crls)"`
  and switches to the alternative path only if the SDK actually exposes the
  function there.
- `response.data` is `None` only when the HTTP response has no body (rare).
  MistHelper normalizes this to `{}` and then the `results` array to `[]` before
  flattening, so the menu item exits cleanly with "0 rows" rather than raising
  an `AttributeError`.
- This call signature takes no keyword arguments beyond `org_id` because the
  endpoint accepts no query parameters.

## Pagination

Not paginated. The endpoint returns a single JSON object per call. No
`limit`/`page` parameters apply. The `results` array length equals the number
of CRL files uploaded to the org (typically <=10).

## Rate Limiting

Standard Mist API rate limit: 5000 calls per token per hour. MistHelper's
adaptive delay system (`delay_metrics.json` per-endpoint state +
`tuning_data.json` learning) governs back-off automatically. No
endpoint-specific tuning is required for this contract -- the response is small
and the call is infrequent (operators check CRLs only when investigating 802.1X
auth failures).
