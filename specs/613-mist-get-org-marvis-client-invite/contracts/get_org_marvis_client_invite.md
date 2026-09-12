# Endpoint Contract: getOrgMarvisClientInvite

**Feature**: 613-mist-get-org-marvis-client-invite
**Date**: 2026-06-30
**Source**: `documentation/api/orgs/GET_orgs_org_id_marvisinvites_marvisinvite_id.md`

## HTTP Contract

| Field         | Value                                                              |
|---------------|--------------------------------------------------------------------|
| Method        | `GET`                                                              |
| URL template  | `https://{MIST_HOST}/api/v1/orgs/{org_id}/marvisinvites/{marvisinvite_id}` |
| Auth          | `Authorization: Token <MIST_API_TOKEN>` header (injected by `mistapi.APISession`) |
| Content-Type  | `application/json` (response only -- this endpoint has no request body) |
| Request body  | None                                                               |
| Pagination    | Not paginated -- response is a single JSON object                  |
| Rate limits   | Standard Mist limit: 5000 calls per API token per hour             |

### Required path parameters

| Name              | Type           | Description                                                       |
|-------------------|----------------|-------------------------------------------------------------------|
| `org_id`          | UUID (string)  | Mist organization that owns the Marvis invite                     |
| `marvisinvite_id` | UUID (string)  | Marvis Client Invite resource ID                                  |

### Query parameters

None.

### Required request headers

| Header          | Value                                       | Set by              |
|-----------------|---------------------------------------------|---------------------|
| `Authorization` | `Token <MIST_API_TOKEN>`                    | `mistapi.APISession`|
| `Accept`        | `application/json`                          | `mistapi.APISession`|
| `User-Agent`    | `mistapi/<version>`                         | `mistapi.APISession`|

## Response: 200 OK

### Body schema

```json
{
  "type": "object",
  "properties": {
    "disabled": {
      "type": "boolean",
      "default": false
    },
    "id": {
      "type": "string",
      "description": "Unique ID of the object instance in the Mist Organization",
      "contentEncoding": "uuid",
      "readOnly": true
    },
    "name": {
      "type": "string"
    },
    "provision_url": {
      "type": "string",
      "description": "In MDM, add `--provision_url <provision_url>` to the install command",
      "readOnly": true
    }
  }
}
```

### Example success body

```json
{
  "id": "53f10664-3ce8-4c27-b382-0ef66432349f",
  "name": "Handhelds",
  "disabled": false,
  "provision_url": "https://api.mist.com/path/to/url"
}
```

### Field reference

| JSON field      | Type    | `readOnly` | MistHelper handling                                                          |
|-----------------|---------|------------|------------------------------------------------------------------------------|
| `id`            | UUID    | Yes        | SQLite primary key; column 1 of CSV                                          |
| `name`          | string  | No         | SQLite indexed column; column 2 of CSV                                       |
| `disabled`      | boolean | No         | Stored as `0`/`1` integer in SQLite (project convention); column 3 of CSV    |
| `provision_url` | string  | Yes        | Stored verbatim; never written to a log statement (treated as sensitive URL) |

The method also injects `org_id` (path parameter) into the row before export
so SQLite reports can join back to org-scoped tables.

## Error Responses

| Status | Description (Mist API)                                                                                 | MistHelper handling                                                                                                            |
|--------|--------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------|
| 400    | Bad Syntax                                                                                             | `logging.warning("Mist API 400 -- bad request shape for getOrgMarvisClientInvite")` and return non-zero exit                   |
| 401    | Unauthorized (invalid / expired `MIST_API_TOKEN`)                                                      | `logging.error("Mist API 401 -- token invalid or expired")` and return non-zero exit                                           |
| 403    | Permission Denied                                                                                      | `logging.error("Mist API 403 -- token lacks permission on org %s", org_id)` and return non-zero exit                           |
| 404    | Resource does not exist (bad `marvisinvite_id` or wrong `org_id`)                                      | `logging.warning("Mist API 404 -- invite %s not found in org %s", marvisinvite_id, org_id)` and exit 0 with no row written     |
| 429    | Rate limit (5000 calls/hour exceeded)                                                                  | Adaptive delay system absorbs the back-off using `delay_metrics.json` + `tuning_data.json`; method retries per existing policy |

Unexpected exceptions are caught at the outer dispatch boundary and reported
with `logging.exception(...)` so the full traceback is in
`data/script.log` but never printed to stdout.

## Exact mistapi Python call signature

```python
import mistapi
from mistapi.api.v1.orgs.marvis_invites import getOrgMarvisClientInvite

apisession = mistapi.APISession(                                     # Loads MIST_HOST + MIST_API_TOKEN from .env
    host=os.environ["MIST_HOST"],                                    # Cloud region host
    apitoken=os.environ["MIST_API_TOKEN"],                           # Read-only token is sufficient
)
apisession.login()                                                   # Validates the token before any call

response = getOrgMarvisClientInvite(                                 # The endpoint under contract
    apisession,                                                      # Authenticated session
    org_id,                                                          # Path param 1 (UUID string)
    marvisinvite_id,                                                 # Path param 2 (UUID string)
)
invite = response.data                                               # dict, or {} if API returned empty
```

`response` is a `mistapi.APIResponse` instance. Useful attributes:

- `response.status_code` -- HTTP status (200 on success).
- `response.data` -- the parsed JSON body (dict for this endpoint).
- `response.headers` -- HTTP headers (do **not** log; may contain
  rate-limit / request-id values that should stay in `data/script.log` only).

## Conformance Checklist

The implementing PR must satisfy:

- [ ] Routes through `mistapi.api.v1.orgs.marvis_invites.getOrgMarvisClientInvite`
      -- no direct `requests` call.
- [ ] Validates both `org_id` and `marvisinvite_id` against the Mist UUID
      shape before invoking the SDK.
- [ ] Uses `safe_input()` for both prompts with explicit `context=` strings.
- [ ] Persists output via
      `DataExporter.write_with_format_selection([invite], "org_marvis_client_invite", api_function_name="getOrgMarvisClientInvite")`.
- [ ] Registers the operation in `ENDPOINT_PRIMARY_KEY_STRATEGIES` exactly
      as documented in `data-model.md`.
- [ ] Emits ASCII-only `INFO` log before the SDK call and ASCII-only `DEBUG`
      log after with a safe field summary (no `provision_url`, no token).
- [ ] Annotates every executable line in the new method with an inline
      comment per Constitution Principle VI.
- [ ] Passes `python -m py_compile MistHelper.py`,
      `python -m ruff check MistHelper.py`, and
      `python -m black --check MistHelper.py`.
