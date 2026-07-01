# Contract: getOrgSsrRegistrationCommands

**Feature**: `645-mist-get-org-ssr-registration-commands`
**Source**: `documentation/api/orgs/GET_orgs_org_id_ssr_register_cmd.md`

## HTTP Contract

| Attribute            | Value                                                                 |
|----------------------|-----------------------------------------------------------------------|
| Method               | `GET`                                                                 |
| URL template         | `https://{MIST_HOST}/api/v1/orgs/{org_id}/ssr/register_cmd`           |
| Authentication       | `Authorization: Token {MIST_API_TOKEN}` header (loaded from `.env`)   |
| Content-Type (req)   | Not applicable (no request body)                                      |
| Content-Type (resp)  | `application/json`                                                    |
| Pagination           | None -- single-object response                                        |
| Rate limiting        | Standard Mist API (5000 calls / hour / token); 429 triggers back-off  |

### Path parameters

| Name     | Type         | Required | Description                        | Validation                              |
|----------|--------------|----------|------------------------------------|-----------------------------------------|
| `org_id` | string (UUID)| Yes      | Organization to fetch commands for | Must match UUID v4 shape                |

### Query parameters

| Name        | Type            | Required | Default              | Description                                                                                       |
|-------------|-----------------|----------|----------------------|---------------------------------------------------------------------------------------------------|
| `ttl`       | integer (secs)  | No       | `31536000` (1 year)  | Validity of the returned registration code. MistHelper enforces `1 <= ttl <= 31536000`.           |
| `asset_ids` | array of UUIDs  | No       | (none = general)     | Restricts registration to the listed assets only. Doc recommends body transport for long lists.   |

### Headers

| Name             | Required | Value                                | Notes                                          |
|------------------|----------|--------------------------------------|------------------------------------------------|
| `Authorization`  | Yes      | `Token {MIST_API_TOKEN}`             | Injected by `mistapi.APISession`               |
| `Accept`         | No       | `application/json`                   | `mistapi` sets this automatically              |
| `User-Agent`     | No       | `mistapi-python/<version>`           | Set by the SDK                                 |

### Request body

None. This is a GET.

## Response 200 (Success)

Content-Type: `application/json`. Response body is a single object (not an array).

```json
{
  "type": "object",
  "properties": {
    "conductor_cmd":     { "type": "string" },
    "registration_code": { "type": "string" },
    "router_shell_cmd":  { "type": "string" }
  }
}
```

### Field semantics

| Field               | Purpose                                                                                                                        |
|---------------------|--------------------------------------------------------------------------------------------------------------------------------|
| `conductor_cmd`     | Command run on the Mist Conductor / control-plane side to accept the incoming SSR registration.                                |
| `registration_code` | Short-lived, single-use registration secret. Embedded in `router_shell_cmd`. **Treat as a credential.** Never log the value.   |
| `router_shell_cmd`  | Complete shell command the NOC engineer pastes into the SSR CLI to complete adoption into Mist.                                |

All three fields are strings; any may be present or omitted depending on org configuration.
MistHelper stores `None` / SQL NULL for absent fields.

## Error responses

| Status | Meaning                                | MistHelper handling                                                                                     |
|--------|----------------------------------------|---------------------------------------------------------------------------------------------------------|
| 400    | Bad Syntax                             | Log `ERROR` with the response body summary; return early; menu 95 exits with no data written.           |
| 401    | Unauthorized                           | Log `ERROR` "Invalid or expired MIST_API_TOKEN"; return early. Token is never logged.                    |
| 403    | Permission Denied                      | Log `WARNING` "Token lacks org read permission for %s"; return early.                                    |
| 404    | Not Found (bad org_id or missing SSR)  | Log `WARNING` "Org %s has no SSR registration endpoint enabled"; return early. Not treated as fatal.    |
| 429    | Too Many Requests                      | `mistapi` and MistHelper's adaptive delay system handle back-off automatically per `delay_metrics.json`.|
| 5xx    | Server error                           | `mistapi` retry policy applies; on exhaustion, log `ERROR` and re-raise so the outer menu exits non-0.  |

Every error path logs at ASCII-only, uses `%s` formatting, and omits the API token,
`registration_code`, and full command strings (Principle V).

## `mistapi` Python SDK call signature

```python
import mistapi                                                              # SDK import (already global in MistHelper.py)
import mistapi.api.v1.orgs.ssr.register_cmd as mist_ssr_register_cmd        # Path aliased for readability

# apisession is the shared mistapi.APISession instance bootstrapped from .env
response = mist_ssr_register_cmd.getOrgSsrRegistrationCommands(
    apisession,                                                             # Authenticated APISession
    org_id="11111111-2222-3333-4444-555555555555",                          # Path param
    ttl=None,                                                               # Optional int, None = SDK default (1 year)
    asset_ids=None,                                                         # Optional list[str], None = general token
)                                                                           # ...

# response is a mistapi.APIResponse
payload = response.data or {}                                               # dict, may be empty on 4xx handled paths
conductor_cmd = payload.get("conductor_cmd")                                # Optional str
registration_code = payload.get("registration_code")                        # Optional str -- treat as secret
router_shell_cmd = payload.get("router_shell_cmd")                          # Optional str
status_code = response.status_code                                          # int, exposed for logging/branching
```

### SDK behavior notes

- The SDK sets the `Authorization` header from the `APISession` -- callers never pass it
  directly.
- `ttl=None` and `asset_ids=None` are omitted from the outgoing query string entirely (as
  opposed to being sent as `ttl=` / `asset_ids=`), so the server-side defaults apply.
- The SDK swallows and logs transport-level exceptions; MistHelper's calling code still
  wraps the invocation in a `try / except` to convert unexpected exceptions into
  operator-friendly log lines and non-zero menu exit codes.
- The SDK is thread-safe when each thread uses its own `APISession`, but menu 95 is a
  single-request operation and does not need parallelism.

## Related endpoints

- `GET /api/v1/orgs/{org_id}/128routers/register_cmd` -- 128T (legacy name for the same
  family) registration command. Cataloged in spec 014.
- `GET /api/v1/orgs/{org_id}/inventory` -- List of claimable / claimed assets whose UUIDs
  can be passed as `asset_ids` here.
