# Contract: countOrgJsiAssetsAndContracts

**Spec**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md) | **Data model**: [../data-model.md](../data-model.md)
**Source doc**: `documentation/api/orgs/GET_orgs_org_id_jsi_inventory_count.md`
**OpenAPI tag**: `Orgs JSI`

## HTTP Contract

| Field           | Value                                                          |
|-----------------|----------------------------------------------------------------|
| Method          | `GET`                                                          |
| URL template    | `https://{MIST_HOST}/api/v1/orgs/{org_id}/jsi/inventory/count` |
| Auth header     | `Authorization: Token {MIST_API_TOKEN}` (set by `mistapi.APISession`)            |
| `Accept`        | `application/json`                                             |
| Request body    | None (GET)                                                     |

### Path parameters

| Name     | Type   | Required | Description                                | Validation in MistHelper                                  |
|----------|--------|----------|--------------------------------------------|-----------------------------------------------------------|
| `org_id` | string | Yes      | UUID of the target Mist org.               | Regex match `^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$` before the SDK call. |

### Query parameters

| Name       | Type    | Required | Default | Description                                                          | Validation in MistHelper                                          |
|------------|---------|----------|---------|----------------------------------------------------------------------|-------------------------------------------------------------------|
| `distinct` | string  | No       | (none)  | Field name to bucket counts by (e.g. `model`, `family`, `sku`).      | If supplied, must be non-empty after `.strip()`. No further validation -- the server accepts any field name and returns the unbucketed total when the value is unknown to it. |
| `limit`    | integer | No       | `100`   | Maximum number of buckets returned in `results[]`.                   | Clamped to `1..1000` by the menu method before the call.          |

### Request headers (sent by mistapi.APISession)

- `Authorization: Token <token>`
- `Accept: application/json`
- `User-Agent: mistapi-python/<sdk-version>`
- Cookies set by prior session handshake (cloud-specific).

## Response Contract

### 200 OK -- Result of Count

```json
{
  "type": "object",
  "properties": {
    "distinct": { "type": "string" },
    "end":      { "type": "integer", "contentEncoding": "int32" },
    "limit":    { "type": "integer", "contentEncoding": "int32" },
    "results": {
      "uniqueItems": true,
      "type": "array",
      "items": {
        "title": "count_result",
        "required": ["count"],
        "type": "object",
        "properties": {
          "count": { "type": "integer", "contentEncoding": "int32" }
        },
        "additionalProperties": { "type": "string" }
      }
    },
    "start": { "type": "integer", "contentEncoding": "int32" },
    "total": { "type": "integer", "contentEncoding": "int32" }
  },
  "required": ["distinct", "end", "limit", "results", "start", "total"]
}
```

**Field semantics**:

| Field      | Meaning                                                                             |
|------------|-------------------------------------------------------------------------------------|
| `distinct` | Echo of the requested bucketing field (empty string if no distinct was requested).  |
| `total`    | Total number of JSI inventory items the server considered before bucketing.         |
| `limit`    | Effective limit applied (echo of the request, capped by the server).                |
| `start`    | Window start epoch seconds (server-set).                                            |
| `end`      | Window end epoch seconds (server-set).                                              |
| `results`  | Array of `{count, <distinct>: <bucket_value>}` rows. May be empty.                  |

### Example 200 response body

```json
{
  "distinct": "model",
  "total":    421,
  "limit":    100,
  "start":    1718524800,
  "end":      1719129600,
  "results": [
    { "count": 240, "model": "EX4400-48P" },
    { "count": 137, "model": "EX2300-24P" },
    { "count":  44, "model": "SRX320" }
  ]
}
```

### Error responses

| Status | Mist meaning                                                                     | MistHelper handling                                                                                  |
|--------|----------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| `400`  | Bad Request -- no Juniper Account Linked                                         | `logging.warning("JSI count rejected: org %s has no Juniper account linked", org_id)`; return 0.     |
| `401`  | Unauthorized -- token missing/expired                                            | `logging.error("Mist API rejected token (401)")`; return non-zero so the caller can re-auth.         |
| `403`  | Permission Denied -- token lacks org scope                                       | `logging.error("Token denied access to org %s (403)", org_id)`; return non-zero.                     |
| `404`  | Org or endpoint not found                                                        | `logging.warning("Org %s not found (404)", org_id)`; return 0 (no traceback, edge case from spec).   |
| `429`  | Rate limit -- 5,000 API calls per token per hour                                 | Surfaces via `mistapi`'s adaptive back-off (driven by `delay_metrics.json`); the menu method does not retry manually -- the SDK does. |
| `5xx`  | Mist Cloud unavailable                                                           | `logging.exception("Unexpected error counting JSI inventory")`; return non-zero.                     |

The 400 + 404 cases are explicitly *not* tracebacks -- they exit the menu cleanly
per Constitution Principle III.

## Pagination

Per the source doc, the endpoint supports `limit` and `page` query parameters.
MistHelper does NOT paginate by default for count endpoints because the result is
already an aggregate bounded by `limit`. If a future need arises to enumerate
beyond `limit=1000`, page-walking is added on top in a separate spec; the current
contract intentionally locks in a single-page read.

## Rate Limiting

Standard Mist API limit: 5,000 API calls per token per hour. The `mistapi` SDK
handles 429 responses through MistHelper's adaptive delay system
(`delay_metrics.json` + `tuning_data.json`). The new menu method itself does
nothing special for rate limiting -- it issues exactly one SDK call per
invocation.

## Exact mistapi Python call signature

```python
import mistapi
import mistapi.api.v1.orgs.jsi as jsi  # source path per the enriched docs

apisession = mistapi.APISession()       # loads MIST_HOST + MIST_API_TOKEN from .env
apisession.login()                      # mistapi handshake (idempotent)

response = jsi.countOrgJsiAssetsAndContracts(
    apisession,                         # required first positional
    "11111111-2222-3333-4444-555555555555",  # org_id (path param)
    distinct="model",                   # optional, omit or pass None for unbucketed
    limit=100,                          # optional, server default = 100
)

assert response.status_code == 200
payload: dict = response.data           # see "200 OK" schema above
```

**Note on import path**: The enriched doc declares the canonical SDK entry as
`mistapi.api.v1.orgs.jsi.countOrgJsiAssetsAndContracts`. If the installed
`mistapi` version exposes the function under
`mistapi.api.v1.orgs.jsi.inventory.count` instead (older 0.59.x packaging), both
paths re-export the same function; the menu method uses the canonical
`mistapi.api.v1.orgs.jsi.countOrgJsiAssetsAndContracts` form for forward
compatibility, with a one-line `try/except ImportError` fallback to the
sub-module path if needed.

## Idempotency

The endpoint is a pure read. Repeated calls within the same window return
identical bodies (modulo `total` drifting as the JSI inventory changes). The
MistHelper persistence layer is upsert-only (`INSERT OR REPLACE` keyed by the
unique constraints in `data-model.md`), so re-runs do not duplicate rows.

## Security

- API token is loaded from `.env` and held only in the `mistapi.APISession`
  object. The token never appears in log messages, filenames, or stack traces.
- The `org_id` path parameter is logged at `INFO` level (operational data, not a
  secret).
- HTTPS is enforced by `mistapi.APISession` -- no plaintext fallback.
