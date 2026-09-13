# Endpoint Contract: getOrgAosRegisterCmd

**Spec**: [../spec.md](../spec.md)
**Plan**: [../plan.md](../plan.md)
**Source doc**: `documentation/api/orgs/GET_orgs_org_id_aos_register_cmd.md`
**Date**: 2026-06-29

## HTTP Contract

| Attribute       | Value                                                                |
|-----------------|----------------------------------------------------------------------|
| **Method**      | `GET`                                                                |
| **URL**         | `https://{mist_host}/api/v1/orgs/{org_id}/aos/register_cmd`          |
| **Auth**        | `Authorization: Token {api_token}` header (injected by `mistapi.APISession`) |
| **Tag**         | `Orgs Devices - AOS`                                                 |
| **operationId** | `getOrgAosRegisterCmd`                                               |

### Path Parameters

| Name     | Type          | Required | Description                                                                                  |
|----------|---------------|----------|----------------------------------------------------------------------------------------------|
| `org_id` | string (UUID) | Yes      | Organization UUID. Validated client-side by MistHelper via `is_valid_uuid()` before the call. |

### Query Parameters

None. The endpoint accepts no query parameters per
`documentation/api/orgs/GET_orgs_org_id_aos_register_cmd.md`.

### Request Headers

| Header           | Value                | Notes                                                              |
|------------------|----------------------|--------------------------------------------------------------------|
| `Authorization`  | `Token <api_token>`  | Injected by `mistapi.APISession` from `.env`. **Never logged.**    |
| `Accept`         | `application/json`   | Default for the mistapi SDK.                                       |
| `User-Agent`     | `mistapi/<version>`  | Set by the SDK.                                                    |

### Request Body

None. This is a GET request with no body.

## Response Contract

### 200 OK

```json
{
  "cli_commands": "register-code abc123def456...\nset system services ssh\ncommit and-quit\n"
}
```

| Field          | Type   | Description                                                                                                                                                                                                                       |
|----------------|--------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `cli_commands` | string | AOS-specific CLI command block that can be pasted directly into an AOS (Aruba OS) device to register it with Mist. Includes the registration challenge token and the configuration commands. **Time-sensitive.** **Never logged.** |

Response is a single JSON object with exactly one top-level key. Not a list. Not
paginated. Not wrapped in an envelope.

### Error Responses

| Status | Mist Description                                                              | MistHelper Handling |
|--------|-------------------------------------------------------------------------------|---------------------|
| 400    | Bad Syntax                                                                    | Log `WARNING` ("Mist returned 400 -- check org_id format"). No traceback. Return early. |
| 401    | Unauthorized                                                                  | Log `ERROR` ("Mist 401 -- check MIST_API_TOKEN in .env"). Do not retry. Return early. |
| 403    | Permission Denied                                                             | Log `ERROR` ("Mist 403 -- token lacks read access to org %s", org_id). Return early. |
| 404    | Not found. Endpoint or resource does not exist                                | Log `WARNING` ("No AOS registration context for org %s", org_id). Treat as empty result; write zero rows. Return cleanly. |
| 429    | Too Many Requests (5000 calls/hour token threshold exceeded)                  | Adaptive delay system (`delay_metrics.json` + `tuning_data.json`) backs off and retries automatically up to the configured retry cap. No user intervention. |

All non-200 responses are surfaced as ASCII log lines only. The API token is
never included in any log message, even at `DEBUG`. The `cli_commands` field, if
ever present in an error response body, is **never** logged.

## mistapi Python SDK Call Signature

```python
import os
import mistapi
from mistapi.api.v1.orgs.aos import register_cmd as aos_register_cmd_module

apisession = mistapi.APISession(
    host=os.environ["MIST_HOST"],
    apitoken=os.environ["MIST_API_TOKEN"],
)
apisession.login()

# Single call signature -- one path param, no query params.
response = aos_register_cmd_module.getOrgAosRegisterCmd(
    apisession,
    org_id="0a1b2c3d-1234-5678-9abc-def012345678",
)

# Access the parsed body:
body = response.data            # dict matching the 200 OK schema above
cli_commands = body.get("cli_commands", "")
http_status = response.status_code
```

Notes:

- The SDK module path mirrors the OpenAPI URL path
  (`/orgs/{org_id}/aos/register_cmd` -> `mistapi.api.v1.orgs.aos.register_cmd`).
  The enriched per-endpoint doc lists the SDK as
  `mistapi.api.v1.orgs.devices_-_aos.getOrgAosRegisterCmd()`, but `devices_-_aos`
  is not a legal Python identifier -- that is the OpenAPI tag rendered in the
  doc, not an importable path. The URL-derived path is canonical and matches
  adjacent endpoints (e.g. `mistapi.api.v1.orgs.claim.status`,
  `mistapi.api.v1.orgs.sites`). Final verification at implementation via
  `python -c "from mistapi.api.v1.orgs.aos import register_cmd; help(register_cmd)"`.
- `response.data` is `None` only when the HTTP response had no body (rare).
  MistHelper normalizes this to `{}` before reading `cli_commands`.
- The function may be exported by the SDK with PascalCase (`GetOrgAosRegisterCmd`)
  or camelCase (`getOrgAosRegisterCmd`). The implementation step performs a
  one-line adjustment if introspection reveals a different casing -- no plan
  change required. The OpenAPI operationId is camelCase
  (`getOrgAosRegisterCmd`) per the source doc and the spec.

## Pagination

Not paginated. The endpoint returns a single JSON object with one string field per
call. No `limit` / `page` / `start` / `end` parameters apply.

## Rate Limiting

Standard Mist API rate limit: 5000 calls per token per hour. MistHelper's
adaptive delay system (`delay_metrics.json` per-endpoint state +
`tuning_data.json` learning) governs back-off automatically. No endpoint-specific
tuning required for this contract.

## Time-Sensitivity Note

Per the source doc Gotchas section: **the returned registration command is
time-sensitive.** Each invocation produces a fresh, distinct challenge. Operators
should paste the result into the target AOS device promptly. MistHelper archives
every invocation as a new row (per the `auto_increment_with_unique` PK strategy
in `data-model.md`) so audit history is preserved, but the practical value of any
given stored row decreases with time as the Mist Cloud expires the challenge.

## Persistence Contract (from data-model.md)

The single response row is persisted via
`DataExporter.write_with_format_selection()` with
`api_function_name="getOrgAosRegisterCmd"`, which looks up the
`ENDPOINT_PRIMARY_KEY_STRATEGIES` entry:

```python
'getOrgAosRegisterCmd': {
    'type': 'auto_increment_with_unique',
    'primary_key': ['misthelper_internal_id'],
    'unique_keys': ['org_id', 'generated_at_utc'],
    'indexes': ['org_id', 'generated_at_utc'],
    'table': 'org_aos_register_cmd',
}
```

The row fields written are:

`org_id`, `generated_at_utc`, `cli_commands`, `cli_commands_length`, `mist_host`,
`http_status_code`. The `misthelper_internal_id` is supplied by the SQLite
backend (or its analogue in ArangoDB / Redis).
