# Endpoint Contract: countOrgTickets

**Spec**: [../spec.md](../spec.md)
**Plan**: [../plan.md](../plan.md)
**Source doc**: `documentation/api/orgs/GET_orgs_org_id_tickets_count.md`
**Date**: 2026-06-29

## HTTP Contract

| Attribute    | Value                                                            |
|--------------|------------------------------------------------------------------|
| **Method**   | `GET`                                                            |
| **URL**      | `https://{mist_host}/api/v1/orgs/{org_id}/tickets/count`         |
| **Auth**     | `Authorization: Token {api_token}` header (provided automatically by `mistapi.APISession`) |
| **Tag**      | `Orgs Tickets`                                                   |
| **operationId** | `countOrgTickets`                                             |

### Path Parameters

| Name     | Type          | Required | Description                                                                 |
|----------|---------------|----------|-----------------------------------------------------------------------------|
| `org_id` | string (UUID) | Yes      | Organization UUID. Validated client-side by MistHelper via `is_valid_uuid()` before the call. |

### Query Parameters

| Name       | Type    | Required | Default | Enum | Description |
|------------|---------|----------|---------|------|-------------|
| `distinct` | string  | No       | (server-chosen) | --   | Field name used to group ticket counts (e.g., `status`, `type`, `created_by`). When omitted, the Mist API selects its server-side default. MistHelper records the literal sentinel `"__server_default__"` in the PK so re-polls upsert. |
| `limit`    | integer | No       | `100`   | --   | Maximum number of distinct buckets to return in the `results` array. MistHelper coerces the prompt input with `int()` inside a try/except guard; non-numeric input logs a `WARNING` and falls back to `100`. |

### Request Headers

| Header           | Value                  | Notes                                                          |
|------------------|------------------------|----------------------------------------------------------------|
| `Authorization`  | `Token <api_token>`    | Injected by `mistapi.APISession` from `.env`. Never logged.    |
| `Accept`         | `application/json`     | Default for mistapi SDK.                                       |
| `User-Agent`     | `mistapi/<version>`    | Set by SDK.                                                    |

### Request Body

None. This is a GET.

## Response Contract

### 200 OK

Result of Count. Single JSON object with an embedded `results` array bounded by
`limit`.

```json
{
  "distinct": "status",
  "start": 1719500000,
  "end":   1719600000,
  "limit": 100,
  "total": 4,
  "results": [
    {"count": 42, "status": "open"},
    {"count": 18, "status": "in_progress"},
    {"count":  7, "status": "pending_customer"},
    {"count": 91, "status": "closed"}
  ]
}
```

| Field      | Type                | Description                                                                                |
|------------|---------------------|--------------------------------------------------------------------------------------------|
| `distinct` | string              | Echo of the distinct field used for grouping. May differ from the client request when the server applied its default. |
| `start`    | int32 (epoch sec)   | Start of the result window the server applied.                                             |
| `end`      | int32 (epoch sec)   | End of the result window the server applied.                                               |
| `limit`    | int32               | Echo of the limit the server actually applied.                                             |
| `total`    | int32               | Total number of distinct buckets matched. May exceed `len(results)` when the server truncates to `limit`. |
| `results`  | object[] (unique)   | One entry per bucket. Each item: `{"count": <int>}` plus open-ended `additionalProperties` of type string holding the bucket key (e.g., `"status": "open"`). |

Per the OpenAPI schema, `distinct`, `end`, `limit`, `results`, `start`, and `total`
are all required; `results` items require `count` and allow additional string
properties whose key is the value of `distinct`.

### Error Responses

| Status | Mist Description                                                   | MistHelper Handling |
|--------|--------------------------------------------------------------------|---------------------|
| 400    | Bad Syntax                                                         | Log `WARNING` ("Mist returned 400 -- check distinct/limit values"), no traceback, return early. |
| 401    | Unauthorized                                                       | Log `ERROR` ("Mist 401 -- check MIST_API_TOKEN in .env"). Do not retry. Return early. |
| 403    | Permission Denied                                                  | Log `ERROR` ("Mist 403 -- token lacks read access to org %s", org_id). Return early. |
| 404    | Not found. Endpoint or resource does not exist                     | Log `WARNING` ("No tickets visible for org %s", org_id). Treat as empty result and write zero result rows; the summary row still records `total_buckets=0`. Return cleanly. |
| 429    | Too Many Requests (5000 calls/hour token threshold exceeded)       | Adaptive delay system (`delay_metrics.json` + `tuning_data.json`) backs off and retries automatically up to the configured retry cap. No user intervention. |

All non-200 responses surface as ASCII log lines only. The API token is never
included in any log message, even at `DEBUG`.

## mistapi Python SDK Call Signature

```python
import mistapi
from mistapi.api.v1.orgs import tickets as tickets_module

apisession = mistapi.APISession(host=os.environ["MIST_HOST"],
                                apitoken=os.environ["MIST_API_TOKEN"])
apisession.login()

# Server-chosen default distinct field, default limit (100):
response = tickets_module.countOrgTickets(
    apisession,
    org_id="0a1b2c3d-1234-5678-9abc-def012345678",
)

# Explicit distinct field and higher limit:
response = tickets_module.countOrgTickets(
    apisession,
    org_id="0a1b2c3d-1234-5678-9abc-def012345678",
    distinct="status",
    limit=500,
)

# Access the parsed body:
body = response.data            # dict matching the 200 OK schema above
http_status = response.status_code
```

Notes:

- The SDK module path mirrors the OpenAPI URL path
  (`/orgs/{org_id}/tickets/count` -> `mistapi.api.v1.orgs.tickets.countOrgTickets`).
  Final verification happens at implementation via
  `python -c "from mistapi.api.v1.orgs import tickets; help(tickets.countOrgTickets)"`.
- `response.data` is `None` only when the HTTP response had no body (rare).
  MistHelper normalizes this to `{}` before flattening so downstream code never
  has to special-case `None`.
- The `distinct` parameter is passed as a Python `str` or `None`. The SDK omits the
  query parameter entirely when the value is `None`, which is the desired
  behavior when the caller wants the server-side default.
- The `limit` parameter is passed as a Python `int`. The Mist API defaults it to
  `100` server-side when omitted; MistHelper passes a value explicitly to make the
  effective limit visible in the response echo.

## Pagination

Not paginated by `page`. The endpoint returns a single JSON object per call with
the `results` array bounded by `limit`. The enriched doc mentions a `page` query
parameter, but the schema does not declare one, and the canonical pagination knob
is `limit`. If a future schema revision adds explicit pagination, this contract
will be updated and the PK strategy revisited.

## Rate Limiting

Standard Mist API rate limit: 5000 calls per token per hour. MistHelper's adaptive
delay system (`delay_metrics.json` per-endpoint state + `tuning_data.json`
learning) governs back-off automatically. No endpoint-specific tuning required for
this contract.
