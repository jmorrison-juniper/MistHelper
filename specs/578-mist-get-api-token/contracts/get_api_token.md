# Contract: GET /api/v1/self/apitokens/{apitoken_id}

**Spec**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md)
**operationId**: `getApiToken` | **Tag**: Self API Token
**Enriched source**: `documentation/api/self/GET_self_apitokens_apitoken_id.md`

## HTTP Contract

| Element            | Value                                                              |
|--------------------|--------------------------------------------------------------------|
| Method             | `GET`                                                              |
| URL template       | `https://{MIST_HOST}/api/v1/self/apitokens/{apitoken_id}`          |
| Authentication     | `Authorization: Token {MIST_API_TOKEN}` (header). Cookie auth with `X-CSRFToken` is also accepted but unused by MistHelper. |
| Content negotiation| Request: none (no body). Response: `application/json`.             |
| Pagination         | None -- the endpoint returns a single object.                      |

### Path Parameters (required)

| Name          | Type            | Required | Description                                            |
|---------------|-----------------|----------|--------------------------------------------------------|
| `apitoken_id` | string (uuid)   | Yes      | UUID of the API token to inspect. Must belong to the authenticated admin; otherwise the API returns 404. |

### Query Parameters

_None._

### Request Headers

| Header           | Required | Value                                  |
|------------------|----------|----------------------------------------|
| `Authorization`  | Yes      | `Token {MIST_API_TOKEN}` (from `.env`) |
| `Accept`         | No       | `application/json` (set by `mistapi`)  |

### Request Body

_None._ This is a GET request.

## Response: 200 OK

A single JSON object with the following shape (verbatim from
`documentation/api/self/GET_self_apitokens_apitoken_id.md`):

```json
{
  "type": "object",
  "properties": {
    "created_time": {
      "type": "number",
      "description": "When the object has been created, in epoch",
      "readOnly": true
    },
    "id": {
      "type": "string",
      "description": "Unique ID of the object instance in the Mist Organization",
      "contentEncoding": "uuid",
      "readOnly": true,
      "examples": ["53f10664-3ce8-4c27-b382-0ef66432349f"]
    },
    "key": {
      "type": "string",
      "readOnly": true,
      "examples": ["1qkb...QQCL"]
    },
    "last_used": {
      "type": ["integer", "null"],
      "contentEncoding": "int32",
      "readOnly": true,
      "examples": [1690115110]
    },
    "name": {
      "type": "string",
      "description": "Name of the token",
      "examples": ["org_token_xyz"]
    }
  },
  "description": "User API Token"
}
```

### Field Notes

- `key` is a redacted fingerprint (e.g. `1qkb...QQCL`). The full secret is NEVER
  returned -- it is shown exactly once at token creation time via a separate endpoint.
- `last_used` may be `null` for tokens that have been created but never exercised.
- `created_time` is a fractional epoch (seconds with optional microseconds).
- `id` is the Mist UUID and is the natural primary key recorded in
  `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

### Example 200 payload

```json
{
  "id": "53f10664-3ce8-4c27-b382-0ef66432349f",
  "name": "org_token_xyz",
  "key": "1qkb...QQCL",
  "created_time": 1690000000.0,
  "last_used": 1690115110
}
```

## Error Responses & MistHelper Handling

| Status | Mist Meaning                                                                  | MistHelper Behavior                                                                                            |
|--------|-------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------|
| 400    | Bad Syntax (e.g. malformed UUID slipped past local validation)                | `logging.warning("Bad syntax for apitoken_id %s", apitoken_id)`; early return; exit code 0 (validation error, not crash). |
| 401    | Unauthorized -- token missing or invalid                                       | `logging.error("Authentication failed -- check MIST_API_TOKEN in .env")`; exit code 2.                          |
| 403    | Permission Denied -- caller is not allowed to inspect this token              | `logging.warning("Permission denied for apitoken_id %s", apitoken_id)`; early return; exit code 0.              |
| 404    | Not Found -- token id does not exist or belongs to another admin              | `logging.warning("API token %s not found", apitoken_id)`; write zero rows; exit code 0.                         |
| 429    | Too Many Requests -- 5000 calls/hour threshold reached                        | Adaptive delay system in `delay_metrics.json` / `tuning_data.json` backs off and retries up to the configured cap; `logging.info("Rate limited; backing off")`. |
| 5xx    | Mist Cloud server error                                                        | `logging.exception("Mist API server error")`; let `mistapi`'s retry policy run; exit code 1 on final failure.   |

All log lines are ASCII-only. The bearer token is never included in any log message,
URL, or exception traceback.

## mistapi Python Call Signature

```python
# mistapi >= 0.59
import mistapi
from mistapi.api.v1.self import api_token as self_api_token

# apisession is the existing module-level mistapi.APISession instance
# bound to MIST_HOST + MIST_API_TOKEN from .env at process start.
response = self_api_token.getApiToken(
    apisession,                  # mistapi.APISession -- carries auth + transport
    apitoken_id,                 # str (UUID) -- validated locally before this call
)

# response is a mistapi.APIResponse
# response.status_code -> int
# response.data        -> dict (single token object) on 200
# response.headers     -> dict
```

### Calling convention notes

- The function is called positionally; `mistapi` does not require named arguments here.
- No `apisession.mist_get_all(...)` is needed -- there is no pagination.
- The function raises no exception on non-2xx; the caller must inspect
  `response.status_code` and branch on the error table above. MistHelper's adaptive
  delay decorator handles 429 transparently before the caller sees it.

## Related Endpoints (out of scope for this spec)

- `GET /api/v1/self/apitokens` -- list all API tokens
  (`listApiTokens`, `documentation/api/self/GET_self_apitokens.md`)
- `PUT /api/v1/self/apitokens/{apitoken_id}` -- update token metadata
- `DELETE /api/v1/self/apitokens/{apitoken_id}` -- revoke token

Each lives behind its own feature spec.
