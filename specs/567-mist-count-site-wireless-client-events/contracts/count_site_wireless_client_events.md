# Endpoint Contract: countSiteWirelessClientEvents

**operationId**: `countSiteWirelessClientEvents`
**Tag**: `Sites Clients - Wireless`
**Source doc**: `documentation/api/sites/GET_sites_site_id_clients_events_count.md`

---

## HTTP Contract

| Field | Value |
|-------|-------|
| Method | `GET` |
| URL template | `https://{MIST_HOST}/api/v1/sites/{site_id}/clients/events/count` |
| Authentication | `Authorization: Token {MIST_API_TOKEN}` header (Mist API token loaded from `.env`) |
| Request body | None |
| Content-Type (response) | `application/json` |
| Pagination | Supported via `limit` and implicit `page` query parameters |
| Rate limit | Standard Mist API limit -- 5000 calls per hour per token |

### Path parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `site_id` | string (UUID) | yes | Site under inspection; UUID format `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |

### Query parameters

| Name | Type | Required | Default | Notes |
|------|------|----------|---------|-------|
| `distinct` | string | no | (server-side default) | Attribute to group counts by. Recognized values include `type`, `ssid`, `ap`, `band`, `proto`, `wlan_id`, `reason_code`. |
| `type` | string | no | -- | Event type. See `listDeviceEventsDefinitions`. |
| `reason_code` | integer | no | -- | For assoc/disassoc events. |
| `ssid` | string | no | -- | SSID name. |
| `ap` | string | no | -- | AP MAC address. |
| `proto` | string | no | -- | Wireless protocol: `a` / `b` / `g` / `n` / `ac` / `ax`. |
| `band` | string | no | -- | 802.11 band: `2.4`, `5`, or `6`. |
| `wlan_id` | string | no | -- | WLAN identifier. |
| `start` | string | no | -- | Window start; epoch seconds or relative (`-1d`, `-1w`). |
| `end` | string | no | -- | Window end; epoch seconds or relative (`-1d`, `now`). |
| `duration` | string | no | `1d` | Window duration like `7d`, `2w`. Ignored when both `start` and `end` are supplied. |
| `limit` | integer | no | `100` | Buckets per page; MistHelper overrides to `DEFAULT_API_PAGE_LIMIT` (1000) and paginates internally. |

### Required request headers

- `Authorization: Token <MIST_API_TOKEN>` (added automatically by `mistapi.APISession`)
- `Accept: application/json` (added automatically by `mistapi`)

---

## 200 Success response schema

The endpoint returns a single JSON object. Required fields: `distinct`, `start`,
`end`, `limit`, `results`, `total`.

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

### Response field semantics

| Field | Meaning in MistHelper |
|-------|------------------------|
| `distinct` | Echoes the grouping attribute. Stored verbatim into the summary row and into every bucket row as part of the composite primary key. |
| `start` | Window start, epoch seconds (int32). Part of the composite primary key. |
| `end`   | Window end, epoch seconds (int32). Part of the composite primary key. |
| `limit` | Buckets per page actually applied by the API. |
| `total` | Sum of all bucket `count` values across the full result set. Useful as a sanity check after pagination. |
| `results[i].count` | Number of events in the bucket. |
| `results[i].<extra>` | Additional string-valued property whose **key** equals the `distinct` value and whose **value** is the bucket label. MistHelper extracts this into `bucket_key`. When no `distinct` is supplied, the array contains a single bucket with only `count`. |

---

## Error responses and MistHelper handling

| Status | Description | MistHelper behavior |
|--------|-------------|---------------------|
| 400 | Bad Syntax (malformed filter, invalid `distinct`, etc.) | `logging.warning("countSiteWirelessClientEvents 400: %s", error_body)`; return cleanly. No traceback. |
| 401 | Unauthorized (missing or invalid token) | `logging.error("Mist API rejected token (401) -- check MIST_API_TOKEN in .env")`; return without writing output. |
| 403 | Permission Denied | `logging.warning("countSiteWirelessClientEvents 403 for site %s -- token lacks site read scope", site_id)`; return cleanly. |
| 404 | Site not found, or endpoint missing | `logging.warning("Site %s not found (404)", site_id)`; return cleanly without writing output. |
| 429 | Rate limit (5000/hr) exceeded | Adaptive delay system (`delay_metrics.json` + `tuning_data.json`) extends back-off; the SDK retries; MistHelper logs `INFO` on each retry. No user intervention. |

All error logs are ASCII-only with `%s` formatting; the API token is never included.

---

## Exact mistapi Python call signature

```python
import mistapi
from mistapi.api.v1.sites.clients.events.count import countSiteWirelessClientEvents

api_session: mistapi.APISession = mistapi.APISession(env_file=".env")     # loads MIST_HOST and MIST_API_TOKEN
api_session.login()                                                       # establishes session

response = countSiteWirelessClientEvents(                                 # the SDK function
    mist_session=api_session,                                             # required, positional in practice
    site_id=site_id,                                                      # path parameter, UUID string
    distinct=distinct,                                                    # optional grouping attr
    type=event_type,                                                      # optional filter
    reason_code=reason_code,                                              # optional filter
    ssid=ssid,                                                            # optional filter
    ap=ap_mac,                                                            # optional filter
    proto=proto,                                                          # optional filter
    band=band,                                                            # optional filter
    wlan_id=wlan_id,                                                      # optional filter
    start=start,                                                          # optional window start
    end=end,                                                              # optional window end
    duration=duration,                                                    # optional, defaults to "1d"
    limit=limit,                                                          # optional, defaults to 100
)

payload: dict = response.data                                             # JSON body as Python dict
status_code: int = response.status_code                                   # HTTP status
```

### MistHelper invocation pattern

MistHelper does NOT pass `None` values to optional kwargs; instead it builds the
kwargs dict from prompts, dropping entries where the user gave blank input:

```python
sdk_kwargs = {                                                            # build kwargs dict
    "distinct": distinct,                                                 # required for grouping
}                                                                         # always include distinct
sdk_kwargs.update(                                                        # merge non-blank filters
    {k: v for k, v in filters_dict.items() if v not in (None, "")}        # drop blanks
)                                                                         # filters merged
sdk_kwargs.update(                                                        # merge non-blank window
    {k: v for k, v in time_window_dict.items() if v not in (None, "")}    # drop blanks
)                                                                         # window merged

response = countSiteWirelessClientEvents(                                 # single SDK call
    self.api_session,                                                     # APISession from .env
    site_id,                                                              # path param
    **sdk_kwargs,                                                         # only non-blank kwargs
)                                                                         # returns mistapi Response
```

This pattern ensures the Mist API applies its own defaults (`duration=1d`,
`limit=100`) for any field the user left blank, and never emits a query parameter
with an empty value.

---

## Idempotency and re-run safety

- The endpoint is `GET` and has no side effect on the Mist cloud.
- MistHelper writes the response through `DataExporter.write_with_format_selection`,
  which issues `INSERT OR REPLACE` against SQLite using the composite primary key
  `(site_id, distinct, bucket_key, start, end)`. Re-running the same query for the
  same window upserts in place -- no duplicate rows ever appear.
- Re-running with a different `distinct` value or a different window produces new
  rows alongside the existing ones (different primary key), enabling historical
  trend queries.

---

## Cross-references

- Related search endpoint:
  [GET_sites_site_id_clients_events_search.md](../../../documentation/api/sites/GET_sites_site_id_clients_events_search.md)
- Related client search:
  [GET_sites_site_id_clients_search.md](../../../documentation/api/sites/GET_sites_site_id_clients_search.md)
- ENDPOINT_PRIMARY_KEY_STRATEGIES entry: see `data-model.md` in this spec dir.
- Constitution principles referenced: I (5-Item Rule), II (Class-Based), III
  (Safety-First, NON-NEGOTIABLE), IV (Pipeline, NON-NEGOTIABLE), V (Observability),
  VI (Inline Comments, NON-NEGOTIABLE), VII (Action Logging, NON-NEGOTIABLE).
