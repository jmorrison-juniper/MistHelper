# Endpoint Contract: getOrgSecPolicy

**Feature**: 636-mist-get-org-sec-policy
**Date**: 2026-06-30
**Enriched source**:
`documentation/api/orgs/GET_orgs_org_id_secpolicies_secpolicy_id.md`

## HTTP Contract

| Attribute      | Value                                                              |
|----------------|--------------------------------------------------------------------|
| Method         | `GET`                                                              |
| URL template   | `{MIST_HOST}/api/v1/orgs/{org_id}/secpolicies/{secpolicy_id}`      |
| Authentication | `Authorization: Token <MIST_API_TOKEN>` header (from `.env`)       |
| Content-Type   | `application/json` (response); no request body                     |
| Idempotent     | Yes (GET)                                                          |
| Paginated      | No -- returns a single object                                      |
| Rate limit     | Standard Mist 5000 calls/hour; adaptive delay applies per project defaults |

### Path Parameters

| Name           | Type   | Required | Description                                             |
|----------------|--------|----------|---------------------------------------------------------|
| `org_id`       | string | Yes      | Mist organization UUID (v4).                            |
| `secpolicy_id` | string | Yes      | Security policy UUID (v4) inside the given organization.|

### Query Parameters

None.

### Request Headers (added by mistapi.APISession)

- `Authorization: Token <token>`
- `Accept: application/json`
- `User-Agent: mistapi-python/<version>`

### Request Body

None (GET).

## Response 200 (Success)

The response is a single JSON object representing the security policy. Full schema
(shape reproduced from the enriched doc, with wide sub-arrays truncated for
readability -- see `documentation/api/orgs/GET_orgs_org_id_secpolicies_secpolicy_id.md`
for the authoritative expansion):

```json
{
  "id": "53f10664-3ce8-4c27-b382-0ef66432349f",
  "org_id": "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61",
  "site_id": "441a1214-6928-442a-8e92-e1d34b8ec6a6",
  "name": "corp-wan-policy",
  "created_time": 1717959123.0,
  "modified_time": 1719345678.0,
  "wlans": [
    {
      "ssid": "corp-secure",
      "enabled": true,
      "acct_immediate_update": false,
      "acct_interim_interval": 0,
      "acct_servers": [
        { "host": "1.2.3.4", "port": 1813, "secret": "..." }
      ],
      "auth_servers": [
        { "host": "1.2.3.4", "port": 1812, "secret": "..." }
      ]
    }
  ]
}
```

### Response Field Reference (top-level)

| Field           | Type    | Notes                                                                |
|-----------------|---------|----------------------------------------------------------------------|
| `id`            | string  | UUID; readOnly; stable server-issued key.                            |
| `org_id`        | string  | UUID; readOnly; owning organization.                                 |
| `site_id`       | string  | UUID; readOnly; optional site scope (may be absent for org-wide).    |
| `name`          | string  | Human label.                                                         |
| `created_time`  | number  | Epoch seconds; readOnly.                                             |
| `modified_time` | number  | Epoch seconds; readOnly.                                             |
| `wlans`         | array   | Zero or more `wlan` objects with `ssid` required (see child table).  |

### Response Field Reference (wlans[] element -- selected columns)

The `wlan` sub-schema in the OpenAPI spec is very wide (RADIUS auth/acct servers,
802.1X, dynamic VLAN, CoA, etc.). The MistHelper flattener promotes the following
scalars to CSV/SQLite columns; every other field is preserved verbatim in the
`raw_json` column for schema-drift resilience.

| Field                    | Type    | Notes                                              |
|--------------------------|---------|----------------------------------------------------|
| `ssid`                   | string  | Required per schema; part of composite PK.         |
| `enabled`                | boolean | Whether the WLAN entry is active.                  |
| `acct_immediate_update`  | boolean | RADIUS coa-immediate-update flag.                  |
| `acct_interim_interval`  | integer | 0-65535; interim accounting cadence in seconds.    |
| `acct_servers`           | array   | RADIUS accounting server records.                  |
| `auth_servers`           | array   | RADIUS auth server records.                        |

## Error Responses

| Status | Meaning per Mist doc                                        | MistHelper handling                                                                                                       |
|--------|-------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------|
| 400    | Bad Syntax                                                  | Log `ERROR` with the offending field name (never the raw value); return exit 0; user re-runs with corrected input.        |
| 401    | Unauthorized (bad or missing token)                         | Log `ERROR` "Auth failed; check MIST_API_TOKEN in .env"; return exit 0. Never echo the token to logs.                     |
| 403    | Permission Denied                                           | Log `ERROR` "Permission denied for org %s; token lacks read scope"; return exit 0.                                        |
| 404    | Not Found (endpoint or resource does not exist)             | Log `WARNING` "No security policy %s in org %s"; skip DataExporter call; return exit 0.                                   |
| 429    | Too Many Requests (5000/hour reached)                       | The existing adaptive delay system (`delay_metrics.json` + `tuning_data.json`) backs off; mistapi retries with exponential delay; no user intervention. |
| 5xx    | Upstream Mist error                                         | Log `ERROR` via `logging.exception` with the traceback; return exit 0. User may re-run after Mist status recovers.        |

All error paths return exit code 0 from the menu so that automated test sweeps
(`python MistHelper.py --test`) continue past this item; the underlying issue is
communicated through the log record, not through a non-zero exit.

## Exact mistapi Python Call Signature

Import statement:

```python
import mistapi                                                  # Registers the mistapi.api.v1.* tree via side-effect.
```

Call site (inside `OrgTemplateExporter.export_org_sec_policy`):

```python
response = mistapi.api.v1.orgs.secpolicies.getOrgSecPolicy(     # Single non-paginated GET; may raise HTTPError.
    apisession,                                                 # Cached APISession loaded once from .env.
    org_id,                                                     # Path param 1: organization UUID.
    secpolicy_id,                                               # Path param 2: security policy UUID.
)
policy_dict = response.data or {}                               # APIResponse.data is the parsed JSON dict; empty on 404.
```

### Compatibility Note (SDK module path)

The enriched doc narrative names the SDK module `mistapi.api.v1.orgs.security_policies`,
while the URL path token and existing MistHelper references (see line 4761 of
`MistHelper.py`) all use `secpolicies`. The `mistapi` package mirrors URL paths
verbatim, so `secpolicies` is authoritative. Implementation must:

1. Import from `mistapi.api.v1.orgs.secpolicies` first.
2. On `AttributeError`, fall back to `mistapi.api.v1.orgs.security_policies`, log a
   `WARNING` naming the actual module used, and open a follow-up issue to reconcile
   the naming across the enriched documentation set.

### Return Type

`mistapi.APIResponse` -- a thin dataclass exposing:

- `.data` -- parsed JSON (dict for this endpoint; not a list, not paginated).
- `.status_code` -- HTTP status (200 on success, 4xx / 5xx on error).
- `.headers` -- response headers dict.
- `.next` -- pagination cursor (always `None` for this endpoint).
- `.raw_data` -- the raw JSON string for debugging.

The MistHelper method only reads `.data`; error status codes surface as raised
exceptions from within `mistapi` and are caught by the enclosing try/except in the
menu dispatcher (which converts them to the log lines documented in the error table
above).
