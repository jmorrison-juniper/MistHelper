# Endpoint Contract: getOrgIdpProfile

**Spec**: [../spec.md](../spec.md)
**Plan**: [../plan.md](../plan.md)
**Source doc**: `documentation/api/orgs/GET_orgs_org_id_idpprofiles_idpprofile_id.md`
**Date**: 2026-06-30

## HTTP Contract

| Attribute       | Value                                                              |
|-----------------|--------------------------------------------------------------------|
| **Method**      | `GET`                                                              |
| **URL**         | `https://{mist_host}/api/v1/orgs/{org_id}/idpprofiles/{idpprofile_id}` |
| **Auth**        | `Authorization: Token {api_token}` header (provided automatically by `mistapi.APISession`) |
| **Tag**         | `Orgs IDP Profiles`                                                |
| **operationId** | `getOrgIdpProfile`                                                 |

### Path Parameters

| Name            | Type          | Required | Description |
|-----------------|---------------|----------|-------------|
| `org_id`        | string (UUID) | Yes      | Organization UUID. Validated client-side by MistHelper via `is_valid_uuid()` before the call. |
| `idpprofile_id` | string (UUID) | Yes      | IDP profile UUID. Validated client-side by MistHelper via `is_valid_uuid()` before the call. |

### Query Parameters

None. This endpoint takes no query parameters.

### Request Headers

| Header           | Value                              | Notes |
|------------------|------------------------------------|-------|
| `Authorization`  | `Token <api_token>`                | Injected by `mistapi.APISession` from `.env`. Never logged. |
| `Accept`         | `application/json`                 | Default for mistapi SDK. |
| `User-Agent`     | `mistapi/<version>`                | Set by SDK. |

### Request Body

None. This is a GET.

## Response Contract

### 200 OK

```json
{
  "id": "53f10664-3ce8-4c27-b382-0ef66432349f",
  "org_id": "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61",
  "name": "relaxed",
  "base_profile": "standard",
  "created_time": 1719600000,
  "modified_time": 1719603612.123,
  "overwrites": [
    {
      "name": "ignore-low-severity-from-trusted",
      "action": "alert",
      "matching": {
        "attack_name": ["SCAN:NMAP:FIN", "SCAN:NMAP:XMAS"],
        "dst_subnet": ["10.0.0.0/8"],
        "severity": ["minor", "info"]
      }
    },
    {
      "name": "drop-critical-from-internet",
      "action": "drop",
      "matching": {
        "attack_name": [],
        "dst_subnet": ["0.0.0.0/0"],
        "severity": ["critical"]
      }
    }
  ]
}
```

| Field           | Type     | Description |
|-----------------|----------|-------------|
| `id`            | string (UUID) | Server-assigned profile UUID. Stable across reads. Used by MistHelper as the natural primary key for the summary table. Read-only. |
| `org_id`        | string (UUID) | Owning organization UUID. Echoed from the URL. Read-only. |
| `name`          | string   | Human-readable profile label (e.g. `"relaxed"`). |
| `base_profile`  | string enum | One of `critical`, `standard`, `strict`. Defines the baseline IDP rule set the overwrites layer on top of. |
| `created_time`  | number (epoch seconds) | Profile creation timestamp. Read-only. |
| `modified_time` | number (epoch seconds) | Last modification timestamp. Read-only. |
| `overwrites`    | array of object | Per-rule customizations. May be empty. Each item conforms to the `idp_profile_overwrite` schema below. |

#### `idp_profile_overwrite` (item schema)

| Field      | Type     | Description |
|------------|----------|-------------|
| `name`     | string   | Overwrite rule name. Unique within the parent profile -- used by MistHelper as part of the composite PK for the overwrites table. |
| `action`   | string enum | One of `alert` (default), `drop` (silently drop packets), `close` (notify client/server to close connection). |
| `matching` | object   | Selector for which attacks the overwrite applies to. See `idp_profile_matching` below. |

#### `idp_profile_matching`

| Field         | Type     | Description |
|---------------|----------|-------------|
| `attack_name` | string[] | List of specific attack names (Mist signature identifiers). May be empty. |
| `dst_subnet`  | string[] | List of destination CIDRs the rule applies to. May be empty. |
| `severity`    | string[] | Subset of `critical`, `info`, `major`, `minor`. May be empty. |

### Error Responses

| Status | Mist Description                                                  | MistHelper Handling |
|--------|-------------------------------------------------------------------|---------------------|
| 400    | Bad Syntax                                                        | Log `WARNING` ("Mist returned 400 -- check org_id / idpprofile_id format"), no traceback, return early. |
| 401    | Unauthorized                                                      | Log `ERROR` ("Mist 401 -- check MIST_API_TOKEN in .env"). Do not retry. Return early. |
| 403    | Permission Denied                                                 | Log `ERROR` ("Mist 403 -- token lacks read access to org %s", org_id). Return early. |
| 404    | Not found. Endpoint or resource does not exist                    | Log `WARNING` ("IDP profile %s not found in org %s", idpprofile_id[:8], org_id[:8]). Treat as empty result and write zero rows. Return cleanly. |
| 429    | Too Many Requests (5000 calls/hour token threshold exceeded)      | Adaptive delay system (`delay_metrics.json` + `tuning_data.json`) backs off and retries automatically up to the configured retry cap. No user intervention. |

All non-200 responses are surfaced as ASCII log lines only. The API token is
never included in any log message, even at `DEBUG`. Only the first 8 hex
characters of UUIDs are logged in operational messages to keep shell history
clean.

## mistapi Python SDK Call Signature

```python
import mistapi
from mistapi.api.v1.orgs import idpprofiles as idp_profiles_module

apisession = mistapi.APISession(host=os.environ["MIST_HOST"],
                                apitoken=os.environ["MIST_API_TOKEN"])
apisession.login()

response = idp_profiles_module.getOrgIdpProfile(
    apisession,
    org_id="a97c1b22-a4e9-411e-9bfd-d8695a0f9e61",
    idpprofile_id="53f10664-3ce8-4c27-b382-0ef66432349f",
)

body = response.data           # dict matching the 200 OK schema above
http_status = response.status_code
```

Notes:

- The SDK module path mirrors the OpenAPI URL path
  (`/orgs/{org_id}/idpprofiles/{idpprofile_id}` ->
  `mistapi.api.v1.orgs.idpprofiles`). The enriched per-endpoint doc lists the
  SDK as `mistapi.api.v1.orgs.idp_profiles.getOrgIdpProfile()` (with an
  underscore) -- that is a doc-generator artifact (snake_case auto-
  conversion); the existing `listOrgIdpProfiles` PK strategy entry at line
  3923 of `MistHelper.py` confirms the canonical SDK name uses no underscore.
  Final verification happens at implementation via
  `python -c "from mistapi.api.v1.orgs import idpprofiles; help(idpprofiles)"`.
- `response.data` is `None` only when the HTTP response had no body (rare).
  MistHelper normalizes this to `{}` before flattening.
- Both `org_id` and `idpprofile_id` are positional `str` arguments. The SDK
  does not coerce them -- callers must pass canonical lowercase UUIDs (the
  `is_valid_uuid()` helper already enforces this shape upstream).
- There are no optional query parameters to pass.

## Pagination

Not paginated. The endpoint returns a single JSON object per call. No
`limit`/`page`/`start`/`end` parameters apply.

## Rate Limiting

Standard Mist API rate limit: 5000 calls per token per hour. MistHelper's
adaptive delay system (`delay_metrics.json` per-endpoint state +
`tuning_data.json` learning) governs back-off automatically. No
endpoint-specific tuning required for this contract -- the response is a
single small JSON object and a single call consumes one slot of the hourly
budget.

## Related Endpoints (out of scope for this spec)

| Method | Path                                                              | Notes |
|--------|-------------------------------------------------------------------|-------|
| GET    | `/api/v1/orgs/{org_id}/idpprofiles`                               | List all IDP profiles for an org. Already covered by existing PK strategy `listOrgIdpProfiles` at line 3923 of `MistHelper.py`. |
| PUT    | `/api/v1/orgs/{org_id}/idpprofiles/{idpprofile_id}`               | Update profile. Write operation -- separate spec required. |
| DELETE | `/api/v1/orgs/{org_id}/idpprofiles/{idpprofile_id}`               | Delete profile. Destructive -- separate spec required. |
