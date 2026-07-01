# Endpoint Contract: getOrgSsoRole

**Feature**: 644-mist-get-org-sso-role
**Operation ID**: `getOrgSsoRole`
**Source of truth**: `documentation/api/orgs/GET_orgs_org_id_ssoroles_ssorole_id.md`

## HTTP Contract

| Field         | Value                                                       |
|---------------|-------------------------------------------------------------|
| Method        | `GET`                                                       |
| URL template  | `https://{MIST_HOST}/api/v1/orgs/{org_id}/ssoroles/{ssorole_id}` |
| Authentication| Header `Authorization: Token {MIST_API_TOKEN}` (or `X-CSRFToken` cookie for browser sessions) |
| Content-Type  | `application/json` (response); no request body              |
| Idempotency   | Safe -- pure GET, no side effects                           |
| Paginated     | No                                                          |
| Rate limit    | Standard Mist limit: 5000 API calls per hour per token      |

### Path parameters

| Name         | Type          | Required | Description                                       |
|--------------|---------------|----------|---------------------------------------------------|
| `org_id`     | string (UUID) | Yes      | Mist organization UUID (`contentEncoding: uuid`). |
| `ssorole_id` | string (UUID) | Yes      | SSO role UUID within the org.                     |

### Query parameters

_None._

### Request headers

| Header          | Required | Value                                                       |
|-----------------|----------|-------------------------------------------------------------|
| `Authorization` | Yes      | `Token {MIST_API_TOKEN}` -- injected by `mistapi.APISession`. |
| `Accept`        | No       | `application/json` (mistapi default).                       |

### Request body

None. This is a GET.

## Response Contract

### 200 OK

Content-Type: `application/json`. Body is a single `sso_role` object (not an array).

Schema (verbatim from the enriched endpoint doc):

```json
{
  "type": "object",
  "properties": {
    "created_time":  { "type": "number", "description": "Epoch created time",  "readOnly": true },
    "for_site":      { "type": "boolean", "readOnly": true },
    "id":            { "type": "string", "contentEncoding": "uuid", "readOnly": true,
                       "description": "Unique ID of the object instance in the Mist Organization",
                       "examples": ["53f10664-3ce8-4c27-b382-0ef66432349f"] },
    "modified_time": { "type": "number", "description": "Epoch modified time", "readOnly": true },
    "msp_id":        { "type": "string", "contentEncoding": "uuid", "readOnly": true,
                       "examples": ["b9d42c2e-88ee-41f8-b798-f009ce7fe909"] },
    "name":          { "type": "string" },
    "org_id":        { "type": "string", "contentEncoding": "uuid",
                       "examples": ["60f6bfdb-2f45-4022-8e2a-e00d977953fe"] },
    "privileges": {
      "type": "array",
      "minItems": 1,
      "uniqueItems": true,
      "items": {
        "title": "privilege_org",
        "type": "object",
        "required": ["role", "scope"],
        "properties": {
          "org_id":       { "type": "string", "contentEncoding": "uuid", "readOnly": true,
                            "description": "If `scope`==`org`" },
          "role":         { "type": "string",
                            "description": "enum: `admin`, `helpdesk`, `installer`, `read`, `write`" },
          "scope":        { "type": "string",
                            "description": "enum: `org`, `site`, `sitegroup`, `orgsites`" },
          "site_id":      { "type": "string", "contentEncoding": "uuid",
                            "description": "If `scope`==`site`" },
          "sitegroup_id": { "type": "string", "contentEncoding": "uuid",
                            "description": "If `scope`==`sitegroup`" },
          "view":         { "type": "string", "deprecated": true,
                            "description": "Use `views` instead" },
          "views": {
            "type": "array",
            "items": {
              "title": "admin_privilege_view",
              "type": "string",
              "enum": [
                "lobby_admin", "location", "marketing", "mxedge_admin",
                "reporting", "security", "super_observer", "switch_admin"
              ]
            }
          }
        }
      }
    }
  },
  "required": ["name", "privileges"],
  "description": "SSO Role response"
}
```

Notes on required fields:
- `name` and `privileges` are the only response-level required fields.
- Inside `privileges[]`, `role` and `scope` are required; the scope-specific id
  (`org_id` / `site_id` / `sitegroup_id`) is required only when the corresponding
  `scope` value is set. When `scope == "orgsites"`, no scope-specific id is
  required (privileges apply to all sites under the org).

### Error responses

| Status | Meaning                                          | MistHelper handling                                                                                                                                |
|--------|--------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| 400    | Bad Syntax                                       | `logging.warning("Bad request to getOrgSsoRole: %s", ...)`. Return without writing. Should never trigger since MistHelper validates UUIDs pre-call. |
| 401    | Unauthorized (bad or missing token)              | `logging.error("Authentication failed for getOrgSsoRole; check MIST_API_TOKEN")`. Return without writing. Exit code stays 0 for interactive sessions.|
| 403    | Permission Denied                                | `logging.warning("Permission denied for org %s ssorole %s", org[:8], role[:8])`. Return without writing.                                            |
| 404    | Not Found (org or ssorole does not exist)        | `logging.warning("SSO role %s not found under org %s", role[:8], org[:8])`. Return without writing. No traceback -- clean exit per spec Edge Case.  |
| 429    | Too Many Requests (5000/hr per token exceeded)   | Adaptive delay in `delay_metrics.json` handles back-off transparently. On terminal failure, `logging.error(...)` and return.                        |

All error paths log ASCII-only messages that never contain the API token, and use
`%s`-style formatting so that logging remains structured.

## mistapi SDK Call

**Exact signature (from Thomas Munzer's mistapi 0.59+)**:

```python
mistapi.api.v1.orgs.sso_roles.getOrgSsoRole(
    mist_session: mistapi.APISession,
    org_id: str,
    ssorole_id: str,
) -> mistapi.APIResponse
```

**Return type**: `mistapi.APIResponse`. Callers read `.data` for the JSON payload
(a single dict for this endpoint), `.status_code` for the HTTP status, and
`.headers` for pagination / rate-limit metadata.

**Example call (as it appears in MistHelper)**:

```python
response = mistapi.api.v1.orgs.sso_roles.getOrgSsoRole(   # Only permitted Mist transport
    self.apisession, org_id, ssorole_id                    # Positional args per SDK signature
)
role = response.data or {}                                 # Guard against None on error paths
```

**SDK module path caveat**: the OpenAPI tag is `Orgs SSO Roles` and the URL segment
is `ssoroles` (no separator), but the Python module uses `sso_roles` (with
underscore) per PEP 8. This is the convention used across `mistapi.api.v1.orgs.*`
and matches how the enriched endpoint doc names the SDK path.

## Related endpoints (out of scope for this spec)

- `GET /api/v1/orgs/{org_id}/ssoroles` (`listOrgSsoRoles`) -- list all roles. A
  future menu wrapper may call this first to drive an interactive picker for the
  role id, but that belongs in a separate spec.
- `PUT /api/v1/orgs/{org_id}/ssoroles/{ssorole_id}` (`updateOrgSsoRole`) -- write
  operation, deliberately out of scope per the spec's Out of Scope section.
- `DELETE /api/v1/orgs/{org_id}/ssoroles/{ssorole_id}` -- write operation, out of
  scope.

## Conformance checklist for the implementer

- [ ] Call routed through `mistapi.api.v1.orgs.sso_roles.getOrgSsoRole` (no raw
      `requests.get`).
- [ ] Both path params validated via `ValidationUtils` before the call.
- [ ] `safe_input()` collects both UUIDs (contexts
      `org_sso_role:org_id` and `org_sso_role:ssorole_id`).
- [ ] `DataExporter.write_with_format_selection(..., api_function_name="getOrgSsoRole")`
      handles the write for both tables.
- [ ] `ENDPOINT_PRIMARY_KEY_STRATEGIES['getOrgSsoRole']` registered per
      `data-model.md`.
- [ ] All 5 error statuses in the table above have explicit handlers -- no bare
      `except Exception: pass`.
- [ ] Inline comment on every new executable line (Principle VI).
- [ ] Before/after `logging` pair on every meaningful action (Principle VII).
- [ ] ASCII-only log strings, `%s` formatting, no token material.
