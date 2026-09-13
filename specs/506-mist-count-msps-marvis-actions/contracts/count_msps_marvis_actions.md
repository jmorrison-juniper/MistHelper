# Endpoint Contract: countMspsMarvisActions

**Feature**: 506-mist-count-msps-marvis-actions
**Source doc**: `documentation/api/msps/GET_msps_msp_id_suggestion_count.md`
**OperationId**: `countMspsMarvisActions`

## HTTP Contract

| Attribute        | Value                                                              |
|------------------|--------------------------------------------------------------------|
| Method           | `GET`                                                              |
| URL template     | `https://{MIST_HOST}/api/v1/msps/{msp_id}/suggestion/count`        |
| Content-Type     | `application/json` (response only; no request body)                |
| Authentication   | `Authorization: Token {MIST_API_TOKEN}` header                     |
| Idempotent       | Yes                                                                |
| Side effects     | None (read-only)                                                   |
| Pagination       | `limit` query parameter; default 100, max 1000                     |
| Rate limit       | Standard Mist API quota (5000 calls/hour per token)                |

### Path Parameters

| Name     | Type   | Required | Pattern                                | Description                          |
|----------|--------|----------|----------------------------------------|--------------------------------------|
| `msp_id` | string | yes      | Mist UUID v4                           | MSP identifier                       |

### Query Parameters

| Name       | Type    | Required | Default | Description                                              |
|------------|---------|----------|---------|----------------------------------------------------------|
| `distinct` | string  | no       | -       | Attribute to group counts by (`status`, `category`, ...) |
| `limit`    | integer | no       | 100     | Maximum buckets returned (1-1000)                        |

### Request Headers

| Header             | Required | Value                                           |
|--------------------|----------|-------------------------------------------------|
| `Authorization`    | yes      | `Token {MIST_API_TOKEN}`                        |
| `Accept`           | optional | `application/json` (defaulted by `mistapi`)     |
| `X-CSRFToken`      | n/a      | Cookie-auth alternative; not used by MistHelper |

### Request Body

None.

## Response: 200 OK

Schema (abbreviated from
`documentation/api/msps/GET_msps_msp_id_suggestion_count.md`):

```json
{
  "type": "object",
  "properties": {
    "distinct": {"type": "string", "examples": ["status"]},
    "limit":    {"type": "integer", "examples": [100]},
    "total":    {"type": "integer", "examples": [3]},
    "results":  {
      "type": "array",
      "items": {
        "title": "response_count_marvis_actions_result",
        "type": "object",
        "properties": {
          "count": {"type": "integer", "examples": [24]}
        },
        "additionalProperties": {"type": "string"}
      }
    }
  }
}
```

### Concrete example (`distinct=status`)

```json
{
  "distinct": "status",
  "limit": 100,
  "total": 3,
  "results": [
    {"count": 24, "status": "002e176a-0000-000-1111-002e208b20e1"},
    {"count": 12, "status": "2d3f176a-0000-000-2222-002e208f176a"},
    {"count": 15, "status": "08b2176a-0000-000-3333-002e208b2d3f"}
  ]
}
```

### Field semantics

- `distinct` -- echoes the request query parameter; informational.
- `limit` -- effective cap applied server-side after default fallback.
- `total` -- the number of distinct buckets (equals `len(results)` when
  `total <= limit`).
- `results[i].count` -- pending suggestion count for that bucket.
- `results[i].<distinct>` -- dynamic key whose name matches the
  `distinct` field; value is a string identifier or label.

## Error Responses

| Status | Mist Description                                | MistHelper Handling                                                       |
|--------|--------------------------------------------------|---------------------------------------------------------------------------|
| 400    | Bad Syntax                                       | `logging.warning("400 bad request: %s", reason)`; return 0.               |
| 401    | Unauthorized                                     | `logging.error("401 -- check MIST_API_TOKEN")`; return 0; do not retry.   |
| 403    | Permission Denied (Marvis license missing, etc.) | `logging.warning("403 -- Marvis subscription or MSP scope missing")`; return 0. |
| 404    | Not Found (msp_id wrong)                         | `logging.warning("404 -- msp_id not found: %s", msp_id)`; return 0.       |
| 429    | Too Many Requests                                | Defer to adaptive delay system (`delay_metrics.json`); SDK retries once.  |
| 5xx    | Mist upstream error                              | `logging.exception(...)`; return non-zero only when CI test harness asks. |

For 401/403/404/empty payload the method writes nothing to `data\` and exits
0 so re-running is safe.

## mistapi Python Call Signature

```python
import mistapi
import mistapi.api.v1.msps.suggestion.count as _count_module

session = mistapi.APISession(env_file=".env")                              # Loads MIST_HOST + MIST_API_TOKEN
session.login()                                                            # No-op for token auth

response = _count_module.countMspsMarvisActions(                           # SDK call
    session,                                                               # APISession instance
    msp_id="00000000-aaaa-bbbb-cccc-1234567890ab",                         # Path parameter
    distinct="status",                                                     # Optional query param; pass None to omit
    limit=100,                                                             # Optional query param; SDK default 100
)

assert response.status_code == 200                                         # Returned by SDK as APIResponse
payload = response.data                                                    # Parsed JSON dict
```

### Notes

- The SDK function name is `countMspsMarvisActions`; the module path
  `mistapi.api.v1.msps.suggestion.count` mirrors the OpenAPI URL.
- Passing `distinct=None` omits the query parameter entirely so the server
  applies its own default.
- The SDK does not auto-paginate this endpoint -- the response is a single
  document capped by `limit`. For larger sweeps, callers must re-issue the
  request with a higher `limit` (max 1000) or slice client-side.
- `response.next` is unset for this endpoint; MistHelper should not assume a
  generator pattern.
