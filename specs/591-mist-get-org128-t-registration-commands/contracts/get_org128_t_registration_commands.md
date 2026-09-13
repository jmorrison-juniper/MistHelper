# Endpoint Contract: getOrg128TRegistrationCommands

**Spec**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md)
**Source doc**: `documentation/api/orgs/GET_orgs_org_id_128routers_register_cmd.md`
**Deprecation status**: DEPRECATED upstream -- may be removed in a future Mist release.

## HTTP Contract

| Item              | Value                                                                |
|-------------------|----------------------------------------------------------------------|
| Method            | `GET`                                                                |
| URL template      | `https://{MIST_HOST}/api/v1/orgs/{org_id}/128routers/register_cmd`   |
| Authentication    | `Authorization: Token {MIST_API_TOKEN}` header (Mist API token)     |
| Required headers  | `Accept: application/json`, `Authorization: Token <token>`           |
| Idempotent        | Yes (read-only GET; safe to retry)                                   |
| Paginated         | No                                                                   |
| Rate-limited      | Yes -- standard Mist API limit (5000 calls/hour per token); 429 emitted on excess |

### Path Parameters

| Name     | Type   | Required | Notes                                                          |
|----------|--------|----------|----------------------------------------------------------------|
| `org_id` | string | Yes      | Mist organization UUID. Must match the UUID4 shape before send. |

### Query Parameters

| Name        | Type    | Required | Default       | Notes                                                                                          |
|-------------|---------|----------|---------------|------------------------------------------------------------------------------------------------|
| `ttl`       | integer | No       | 31_536_000    | Token validity window in seconds (default = 1 year). MistHelper bounds to `60 <= ttl <= 31_536_000`. |
| `asset_ids` | array   | No       | _(none)_      | Comma-separated list at the wire level. When long, the SDK routes via HTTP body to dodge header-size limits. MistHelper passes a clean `list[str]` after splitting and trimming user input. |

### Request Body

None. Query parameters carry all optional input. Sending a body is rejected
by the upstream API.

## Success Response

**Status**: `200 OK`
**Content-Type**: `application/json`
**Pagination**: None.

### Schema (from the enriched per-endpoint doc)

```json
{
  "type": "object",
  "properties": {
    "conductor_cmd":      { "type": "string" },
    "registration_code":  { "type": "string" },
    "router_shell_cmd":   { "type": "string" }
  }
}
```

### Field Semantics

| Field               | Type   | Sensitivity | Description                                                                             |
|---------------------|--------|-------------|-----------------------------------------------------------------------------------------|
| `registration_code` | string | High        | Time-limited registration token used by the 128T/SSR to authenticate against Mist.       |
| `router_shell_cmd`  | string | High        | Full shell command run on the 128T/SSR to begin adoption. Embeds `registration_code`.    |
| `conductor_cmd`     | string | High        | Full shell command run on the customer-side conductor to register the adoption request.  |

All three fields are written to `data/` but **never** echoed to stdout
and **never** logged above DEBUG.

### Example (illustrative; field values redacted)

```json
{
  "conductor_cmd":     "ssr-conductor register --token=<REDACTED>",
  "registration_code": "<REDACTED-128-CHAR-STRING>",
  "router_shell_cmd":  "curl -sSL https://api.mist.com/ssr/bootstrap.sh | sudo bash -s -- --code <REDACTED>"
}
```

## Error Responses & MistHelper Handling

| Status | Meaning                                       | MistHelper Action                                                                                              |
|--------|-----------------------------------------------|----------------------------------------------------------------------------------------------------------------|
| 400    | Bad syntax (e.g., malformed `org_id` or invalid `ttl`) | `logging.warning("400 from getOrg128TRegistrationCommands for org %s", org_id)`; no row written; return cleanly. |
| 401    | Unauthorized (token missing or expired)       | `logging.error("401 Unauthorized -- check MIST_API_TOKEN")`; return cleanly; do not retry.                       |
| 403    | Permission denied (token lacks org scope)     | `logging.error("403 Forbidden -- token lacks scope for org %s", org_id)`; return cleanly.                        |
| 404    | Org not found / endpoint removed              | `logging.warning("404 from getOrg128TRegistrationCommands for org %s -- endpoint may be retired", org_id)`; return cleanly. |
| 429    | Rate limit hit (5000 calls/hour/token)        | Adaptive delay system in MistHelper (`delay_metrics.json` + `tuning_data.json`) auto-backs off and retries; no manual handling required at the menu method level. |

For any 5xx, the SDK's transport-layer retry kicks in (up to 3 attempts
with jitter). If retries exhaust, the wrapping
`logging.exception("Unhandled error in getOrg128TRegistrationCommands")`
captures a full traceback at ERROR level and the method returns cleanly
without raising into the menu loop.

## mistapi SDK Call Signature

The SDK module is located at
`mistapi.api.v1.orgs.128routers.register_cmd`. Because Python packages
cannot start with a digit, the published package name in `mistapi` is
prefixed with an underscore (`_128routers`) and the documented function
remains `getOrg128TRegistrationCommands`.

### Imports

```python
from mistapi.api.v1.orgs import _128routers as routers_128t_module  # alias around the digit-prefixed module
```

### Call

```python
response = routers_128t_module.register_cmd.getOrg128TRegistrationCommands(
    self.mist_session,        # active mistapi.APISession from .env-bootstrapped credentials
    org_id,                   # validated Mist org UUID (required path param)
    ttl=ttl_clean,            # int or None; None lets the server choose its default
    asset_ids=asset_ids_clean # list[str] or None; None means "no asset filter"
)
```

### Response Envelope

The SDK returns a `mistapi.APIResponse` object. The fields relevant to
this contract:

| Attribute            | Type        | Meaning                                                       |
|----------------------|-------------|---------------------------------------------------------------|
| `response.status_code` | `int`     | Echo of the HTTP status (200 on success).                     |
| `response.data`      | `dict`      | The 200-body object documented above.                         |
| `response.url`       | `str`       | Resolved URL (do not log -- includes the path param).         |
| `response.headers`   | `dict`      | Response headers; consulted by the adaptive delay subsystem.  |

MistHelper reads only `response.data`; everything else is consumed by
the shared transport instrumentation already in `MistHelper.py`.

## Conformance with This Contract

- The implementation MUST call exactly the function signature above.
- The implementation MUST NOT bypass `mistapi` and craft a raw
  `requests` call (constitution: `mistapi` is the sole permitted
  Mist Cloud interface).
- The implementation MUST treat `registration_code`, `router_shell_cmd`,
  and `conductor_cmd` as sensitive: write-to-`data/` only, never
  stdout, never log above DEBUG.
- The implementation MUST emit the deprecation `WARNING` on every
  invocation so operators continue to plan migration off this endpoint.
