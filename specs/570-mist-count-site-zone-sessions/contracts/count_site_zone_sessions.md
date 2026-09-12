# Endpoint Contract: countSiteZoneSessions

**Feature**: 570-mist-count-site-zone-sessions
**Date**: 2026-06-29
**Source doc**: `documentation/api/sites/GET_sites_site_id_zone_type_count.md`

## HTTP Contract

| Property        | Value                                                          |
|-----------------|----------------------------------------------------------------|
| Method          | `GET`                                                          |
| URL Template    | `https://{MIST_HOST}/api/v1/sites/{site_id}/{zone_type}/count` |
| Auth Header     | `Authorization: Token {MIST_API_TOKEN}`                        |
| Accept Header   | `application/json`                                             |
| Content-Type    | n/a (no request body)                                          |
| Pagination      | Server-driven via `limit` (default 100); `page` is accepted but not used here |
| Rate Limit      | Standard Mist API 5000 calls per hour per token                |

### Required Path Parameters

| Name      | Type   | Validation                                              |
|-----------|--------|---------------------------------------------------------|
| site_id   | string | Mist UUID (`[0-9a-f]{8}-[0-9a-f]{4}-...`); enforced client-side before the call |
| zone_type | string | Closed enum: `zones` or `rssizones`; enforced client-side |

### Optional Query Parameters

| Name      | Type    | Default | Notes                                                            |
|-----------|---------|---------|------------------------------------------------------------------|
| distinct  | string  | (none)  | Grouping attribute; documented values include `zone_id`, `map_id`, `user`, `scope`, `scope_id` |
| user_type | string  | (none)  | User-type filter (Mist client classification)                    |
| user      | string  | (none)  | Client MAC / Asset MAC / SDK UUID                                |
| scope_id  | string  | (none)  | When `scope` is `map`, `zone`, or `rssizone`, the scope id       |
| scope     | string  | (none)  | Scope name                                                       |
| start     | string  | (none)  | Epoch seconds or relative string (`-1d`, `-1w`)                  |
| end       | string  | (none)  | Epoch seconds or relative string (`-2h`, `now`)                  |
| duration  | string  | `1d`    | Window grammar (`7d`, `2w`, etc.)                                |
| limit     | integer | 100     | Server-applied row cap on `results[]`                            |

### Required Headers (sent by `mistapi.APISession`)

| Header           | Value                                                                |
|------------------|----------------------------------------------------------------------|
| Authorization    | `Token {MIST_API_TOKEN}` -- never logged                             |
| User-Agent       | `mistapi-python/<version>` -- set automatically by the SDK           |
| Accept-Encoding  | `gzip, deflate` -- set automatically                                 |

## 200 Response Schema (verbatim from enriched doc)

```json
{
  "type": "object",
  "required": ["distinct", "end", "limit", "results", "start", "total"],
  "properties": {
    "distinct": { "type": "string" },
    "end":      { "type": "integer", "contentEncoding": "int32" },
    "limit":    { "type": "integer", "contentEncoding": "int32" },
    "start":    { "type": "integer", "contentEncoding": "int32" },
    "total":    { "type": "integer", "contentEncoding": "int32" },
    "results": {
      "type": "array",
      "uniqueItems": true,
      "items": {
        "title": "count_result",
        "type": "object",
        "required": ["count"],
        "properties": {
          "count": { "type": "integer", "contentEncoding": "int32" }
        },
        "additionalProperties": { "type": "string" }
      }
    }
  }
}
```

### Example Success Payload

```json
{
  "distinct": "zone_id",
  "start": 1751155200,
  "end":   1751241600,
  "limit": 100,
  "total": 3,
  "results": [
    { "count": 482, "zone_id": "11111111-2222-3333-4444-555555555555" },
    { "count": 117, "zone_id": "66666666-7777-8888-9999-aaaaaaaaaaaa" },
    { "count":  39, "zone_id": "bbbbbbbb-cccc-dddd-eeee-ffffffffffff" }
  ]
}
```

## Error Responses and MistHelper Handling

| Status | Server Meaning                                | MistHelper Handling                                                                 |
|--------|-----------------------------------------------|--------------------------------------------------------------------------------------|
| 400    | Bad Syntax (invalid `distinct`, `zone_type`, etc.) | Log `WARNING` with the offending parameter name; return 0; do not raise.            |
| 401    | Unauthorized (token expired or missing scope) | Log `ERROR` "API token unauthorized -- check MIST_API_TOKEN in .env"; return 0.     |
| 403    | Permission Denied                             | Log `ERROR` "Permission denied for site_id %s zone_type %s"; return 0.              |
| 404    | Site / zone_type not found                    | Log `WARNING` "Site %s zone_type %s not found"; return 0; matches Spec Edge Case #2. |
| 429    | Rate limit exceeded                           | Adaptive delay system (`delay_metrics.json` / `tuning_data.json`) backs off and retries; no operator action; covered by Spec Edge Case #3. |
| 5xx    | Mist Cloud server error                       | Log `ERROR` with status code; rely on `mistapi` retry-with-backoff; final failure returns 0 and logs via `logging.exception`. |

In all error paths the menu method returns `0` (rows written) so that `--test` and CI
treat the call as a non-fatal no-op rather than a process failure.

## Exact `mistapi` Python Call Signature

```python
import mistapi                                                               # SDK entrypoint.
import mistapi.api.v1.sites.count                                            # Submodule that owns this endpoint.

# self.apisession is a mistapi.APISession initialized at MistHelper startup
# from MIST_HOST and MIST_API_TOKEN in .env.
response: mistapi.APIResponse = mistapi.api.v1.sites.count.countSiteZoneSessions(
    self.apisession,                                                         # APISession -- authenticated transport.
    site_id,                                                                 # Required path param (Mist UUID).
    zone_type,                                                               # Required path param ("zones" or "rssizones").
    distinct=distinct,                                                       # Optional grouping attribute.
    user_type=None,                                                          # Optional user-type filter (not prompted).
    user=None,                                                               # Optional client identifier (not prompted).
    scope_id=None,                                                           # Optional scope id (not prompted).
    scope=None,                                                              # Optional scope name (not prompted).
    start=None,                                                              # Optional explicit window lower bound.
    end=None,                                                                # Optional explicit window upper bound.
    duration=duration,                                                       # Optional window grammar; default "1d".
    limit=limit,                                                             # Optional row cap; default 100.
)

# response.data is the deserialized JSON envelope described in the schema above.
# response.status_code carries the HTTP status code for error branching.
payload: dict = response.data or {}                                          # Normalize None to empty dict.
```

The signature is reproduced verbatim from the enriched doc at
`documentation/api/sites/GET_sites_site_id_zone_type_count.md` and the published
`mistapi.api.v1.sites.count` module. Any future drift in the SDK signature must be
reconciled here before the menu method ships.
