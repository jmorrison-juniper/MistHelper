# Contract: getOrgJuniperDevicesCommand

Single source of truth for the HTTP and SDK contract that MistHelper menu 58
must honor.

Authoritative upstream doc:
`documentation/api/orgs/GET_orgs_org_id_ocdevices_outbound_ssh_cmd.md`.

## HTTP Contract

| Aspect | Value |
|---|---|
| Method | `GET` |
| URL template | `https://{MIST_HOST}/api/v1/orgs/{org_id}/ocdevices/outbound_ssh_cmd` |
| Required path params | `org_id` (string, UUID) |
| Query params | `site_id` (string, UUID, optional) |
| Request body | None |
| Auth header | `Authorization: Token <MIST_API_TOKEN>` (sourced from `.env`; never logged) |
| Alternative auth | `X-CSRFToken` cookie (browser flow; not used by MistHelper) |
| Pagination | None (single GET; non-paginated) |
| Idempotency | Idempotent (read-only) |
| Rate limiting | Standard 5000-calls-per-hour-per-token Mist limit applies |

### Path Parameters

| Name | Type | Required | Validation (client-side) | Description |
|---|---|---|---|---|
| `org_id` | string | Yes | `^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$` | The Mist organization UUID. |

### Query Parameters

| Name | Type | Required | Default | Validation (client-side) | Description |
|---|---|---|---|---|---|
| `site_id` | string | No | (omitted) | Same UUID regex as `org_id`; on failure MistHelper drops the parameter and proceeds without site context | Site context Mist uses for proxy-config check and automatic site assignment of the resulting OC device. |

## Response

### 200 OK -- Success Schema

```json
{
  "type": "object",
  "properties": {
    "cmd": { "type": "string" }
  },
  "required": ["cmd"]
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `cmd` | string | Yes | The multi-line Junos CLI snippet to paste on the device to enable outbound SSH + NETCONF phone-home to Mist. May be 100-1000+ characters depending on org config. |

Concrete example shape (body content varies per org -- not reproduced
verbatim here to avoid embedding org-sensitive material in this repo):

```json
{
  "cmd": "set system services outbound-ssh client mist ...\nset system services outbound-ssh client mist device-id <ID>\nset system services outbound-ssh client mist secret <SECRET>\nset system services outbound-ssh client mist services netconf\nset system services outbound-ssh client mist <host>:port <HOST>:<PORT>\ncommit and-quit\n"
}
```

### Error Responses

| Status | Meaning | MistHelper Handling |
|---|---|---|
| 400 | Bad Syntax (malformed `org_id` or `site_id` reached the API) | Logged at `WARNING`; method returns 0 (recoverable user input). Client-side UUID validation should normally prevent this. |
| 401 | Unauthorized (missing or invalid token) | Logged at `ERROR` with `logging.exception` (no token text); method returns non-zero so `--test` flags the failure. |
| 403 | Permission Denied (token lacks org access) | Logged at `WARNING`; method returns 0 so menu loop continues; user-facing message advises checking token org scope. |
| 404 | Not Found (org doesn't exist, or OC feature disabled) | Logged at `WARNING`; method returns 0; no row written. |
| 429 | Too Many Requests (rate-limited) | The existing adaptive-delay layer (`delay_metrics.json` + `tuning_data.json`) handles back-off and retry transparently; no per-menu handling required. |
| 5xx | Mist Cloud server-side failure | Logged at `ERROR` with `logging.exception`; method returns non-zero. |

No response is logged with the `cmd` body. Length-only debug log:
`logging.debug("Received cmd payload: length=%d", len(cmd))`.

## mistapi SDK Call Signature

Canonical (path-mirrored) import and call:

```python
from mistapi.api.v1.orgs.ocdevices import outbound_ssh_cmd as ocdevices_outbound_ssh_cmd  # path-mirrored module

response = ocdevices_outbound_ssh_cmd.getOrgJuniperDevicesCommand(   # operationId == function name
    self.apisession,                                                  # the org-wide mistapi.APISession bootstrap
    org_id,                                                           # required path param; UUID-validated client-side
    site_id=(site_id or None),                                        # optional query param; None drops it from the request
)

cmd_value = response.data.get("cmd", "")                              # response.data is the parsed JSON object
```

### SDK call contract

| Aspect | Value |
|---|---|
| Module path (canonical) | `mistapi.api.v1.orgs.ocdevices.outbound_ssh_cmd` |
| Module path (legacy alias) | `mistapi.api.v1.orgs.devices` (some doc generators surface this; canonical path-mirrored module is preferred) |
| Function | `getOrgJuniperDevicesCommand` |
| Positional args | `(apisession, org_id)` |
| Keyword args | `site_id=<str | None>` |
| Returns | `mistapi.APIResponse` with `.status_code` (int), `.data` (dict), `.headers` (dict) |
| Raises | Network / auth errors propagate as `requests.exceptions.*`; MistHelper wraps with `logging.exception`. |

### Pre-call validation (MistHelper-side)

1. `org_id` must match the Mist UUID regex; otherwise warn-and-return.
2. `site_id`, if non-empty, must match the same regex; otherwise reset to
   empty string and proceed.

### Post-call validation (MistHelper-side)

1. `response.status_code == 200` is required; non-200 routes through the
   error table above.
2. `response.data` must contain the `cmd` key (per the 200 schema's
   `required` list); a missing `cmd` is logged at `WARNING` and treated as
   empty content.

### Concrete output row contract

After the call, exactly one row is written to the active backend with the
shape defined in `data-model.md`:

```python
{
    "org_id":        "<echoed input>",
    "site_id":       "<echoed input or ''>",
    "cmd":           "<response.data['cmd']>",
    "cmd_length":    <len(cmd)>,
    "retrieved_at":  "<ISO-8601 UTC at fetch time>",
}
```

Single-row payloads are still passed as a one-element list to
`DataExporter.write_with_format_selection`, matching the convention used
throughout MistHelper's exporters.
