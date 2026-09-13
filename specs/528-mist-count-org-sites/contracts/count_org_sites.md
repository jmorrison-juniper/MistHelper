# Endpoint Contract: countOrgSites

**Spec**: [../spec.md](../spec.md)
**Plan**: [../plan.md](../plan.md)
**Source doc**: `documentation/api/orgs/GET_orgs_org_id_sites_count.md`

## HTTP Contract

| Item | Value |
|------|-------|
| **Method** | `GET` |
| **URL template** | `https://{MIST_HOST}/api/v1/orgs/{org_id}/sites/count` |
| **Tag** | `Orgs Sites` |
| **operationId** | `countOrgSites` |
| **Authentication** | `Authorization: Token {MIST_API_TOKEN}` header (loaded from `.env` by `mistapi.APISession`). Never logged. |
| **Pagination** | Single-page response. `limit` controls the number of buckets returned. |
| **Rate limiting** | Standard Mist API limit: 5000 calls per hour per token. Adaptive delay system applies. |

### Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `org_id` | string (UUID) | yes | Target organization ID. Validated against the UUID shape before the call. |

### Query Parameters

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `distinct` | string | no | (none) | Site field to aggregate on. Examples: `country_code`, `sitegroup_id`, `rftemplate_id`, `org_id`. MistHelper defaults to `country_code` when the user leaves the prompt empty. |
| `start` | string | no | (none) | Start of the query window. Epoch seconds or relative (`-1d`, `-1w`). Not exposed as a prompt; can be set by extending the method signature. |
| `end` | string | no | (none) | End of the query window. Epoch seconds or relative (`-1d`, `-2h`, `now`). Not exposed as a prompt. |
| `duration` | string | no | `1d` | Relative window. Format examples: `1d`, `7d`, `2w`. Exposed as a prompt. |
| `limit` | integer | no | `100` | Max number of buckets returned. Exposed as a prompt. Hard upper bound (Mist API): `1000`. |

### Request Body

None.

### Request Headers (set automatically by `mistapi`)

- `Authorization: Token {MIST_API_TOKEN}`
- `Accept: application/json`
- `User-Agent: mistapi/<version> python/<version>`

## Response

### 200 OK -- Successful Count

Content-type: `application/json`. Body matches the OpenAPI schema below (extracted
verbatim from the enriched per-endpoint doc).

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
      },
      "description": ""
    },
    "start": { "type": "integer", "contentEncoding": "int32" },
    "total": { "type": "integer", "contentEncoding": "int32" }
  },
  "required": ["distinct", "end", "limit", "results", "start", "total"]
}
```

Example body (`distinct=country_code`, `duration=1d`):

```json
{
  "distinct": "country_code",
  "start": 1748520000,
  "end":   1748606400,
  "limit": 100,
  "total": 42,
  "results": [
    { "country_code": "US", "count": 18 },
    { "country_code": "GB", "count": 9  },
    { "country_code": "DE", "count": 7  },
    { "country_code": "FR", "count": 4  },
    { "country_code": "JP", "count": 2  },
    { "country_code": "AU", "count": 1  },
    { "country_code": "CA", "count": 1  }
  ]
}
```

The `results[]` bucket schema has only `count` as a guaranteed key; the second
key is dynamic and reflects the requested `distinct` field (handled by the OpenAPI
`additionalProperties: { type: "string" }`). MistHelper captures this value into
the `bucket_key` column (see `data-model.md`).

## Error Responses

| Status | Mist meaning | MistHelper handling |
|--------|--------------|---------------------|
| **400 Bad Syntax** | Malformed parameter (e.g. unknown `distinct` field name). | Log `WARNING` with sanitized parameters; return non-zero exit code; surface the API message to the user; do NOT retry. |
| **401 Unauthorized** | Missing or invalid API token. | Log `ERROR` "API token rejected -- check .env"; never echo the token; return non-zero. Token loading is handled by `mistapi.APISession` so this is rare unless `.env` was tampered with mid-session. |
| **403 Permission Denied** | Token lacks read scope for the org. | Log `ERROR` "Token lacks read access to org %s"; never echo the token; return non-zero. |
| **404 Not Found** | Unknown `org_id`. | Log `WARNING` "Org %s not found"; print a friendly NOC-engineer message; exit code 0 so SSH session stays alive. |
| **429 Too Many Requests** | Hit 5000 calls/hour. | Let `mistapi`'s built-in retry + the adaptive delay system (`delay_metrics.json`, `tuning_data.json`) handle back-off. After exhausting retries, log `ERROR` and return non-zero. |
| **5xx** | Mist Cloud transient failure. | Same as 429: rely on SDK retry; surface failure via `logging.exception`. |

In every error path the operation exits without a Python traceback (constitution
Principle III) by virtue of running inside the existing menu-dispatcher
try/except.

## mistapi Python Call

### Import

```python
import mistapi
import mistapi.api.v1.orgs.sites
```

### Signature

```python
mistapi.api.v1.orgs.sites.countOrgSites(
    mist_session: mistapi.APISession,
    org_id: str,
    distinct: str | None = None,
    start: str | None = None,
    end: str | None = None,
    duration: str = "1d",
    limit: int = 100,
) -> mistapi.APIResponse
```

### Return value

`mistapi.APIResponse`. Useful attributes:

- `.status_code` -- HTTP status integer.
- `.data` -- parsed JSON envelope (dict matching the 200 schema above).
- `.headers` -- response headers (used by the adaptive delay system to read
  `X-Ratelimit-*` hints).
- `.url` -- final URL; logged at DEBUG only with the API token redacted.

### MistHelper invocation pattern

```python
response = mistapi.api.v1.orgs.sites.countOrgSites(
    self.apisession,
    org_id,
    distinct=distinct,
    duration=duration,
    limit=limit,
)
envelope = response.data or {}
```

`self.apisession` is the long-lived `mistapi.APISession` instance held by the
`SiteExportUtils` class (constructed once at startup from `.env`). It refreshes
its own auth and shares the rate-limit cache with every other menu item.

## Related Endpoints

These are listed for cross-reference only; this contract covers ONLY
`countOrgSites`.

- `GET /api/v1/orgs/{org_id}/sites` (operationId `listOrgSites`) -- full list.
- `GET /api/v1/orgs/{org_id}/sites/search` (operationId `searchOrgSites`) --
  filtered list with query params.

## Constitution conformance summary

| Principle | How this contract complies |
|-----------|----------------------------|
| I -- Five-Item Rule | Single SDK function, one envelope, one nested array. |
| II -- Class-Based | Called as a method on `SiteExportUtils`. |
| III -- Safety-First | GET-only, read-only, no destructive confirmation needed. |
| IV -- Pipeline | No deviation; standard build/lint/format/test/deploy applies. |
| V -- Observability | ASCII-only log lines documented in error table above. |
| VI -- Inline Comments | Implementation lines all carry inline `#` comments. |
| VII -- Action Logging | INFO before, DEBUG after every API call and flatten. |
