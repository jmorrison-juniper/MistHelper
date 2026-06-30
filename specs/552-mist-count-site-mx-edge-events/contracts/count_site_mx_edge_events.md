# Endpoint Contract: countSiteMxEdgeEvents

**Feature**: 552-mist-count-site-mx-edge-events
**Source documentation**:
`documentation/api/sites/GET_sites_site_id_mxedges_events_count.md`

## HTTP Contract

| Field             | Value                                                         |
|-------------------|---------------------------------------------------------------|
| **Method**        | `GET`                                                         |
| **URL template**  | `https://{MIST_HOST}/api/v1/sites/{site_id}/mxedges/events/count` |
| **OpenAPI tag**   | `Sites MxEdges`                                               |
| **OperationId**   | `countSiteMxEdgeEvents`                                       |
| **Authentication**| `Authorization: Token {MIST_API_TOKEN}` header (mistapi-managed) |
| **Idempotent**    | Yes -- read-only count                                         |
| **Side effects**  | None                                                          |

### Path Parameters (required)

| Name      | Type   | Notes                                            |
|-----------|--------|--------------------------------------------------|
| `site_id` | string (UUID) | Site to query. Required. Validated against the Mist UUID shape before the SDK call. |

### Query Parameters (all optional)

| Name           | Type    | Default | Description                                                                                  |
|----------------|---------|---------|----------------------------------------------------------------------------------------------|
| `distinct`     | string  | (none)  | Attribute to group by. Common values: `type`, `service`, `mxedge_id`, `mxcluster_id`.        |
| `mxedge_id`    | string  | (none)  | Mist Edge id filter.                                                                         |
| `mxcluster_id` | string  | (none)  | Mist Edge cluster id filter.                                                                 |
| `type`         | string  | (none)  | Event type filter. See Mist `listDeviceEventsDefinitions` constants.                         |
| `service`      | string  | (none)  | Service name filter (`mxagent`, `tunterm`, etc.).                                            |
| `start`        | string  | (none)  | Window start. Epoch seconds, or relative like `-1d`, `-1w`. Mutually exclusive with `duration`. |
| `end`          | string  | (none)  | Window end. Epoch seconds, or relative like `now`, `-2h`. Mutually exclusive with `duration`.   |
| `duration`     | string  | `1d`    | Relative window such as `7d`, `2w`. Mutually exclusive with `start`/`end`.                   |
| `limit`        | integer | `100`   | Maximum number of buckets returned in `results[]`.                                           |

### Headers

| Header           | Value                                  | Source                                  |
|------------------|----------------------------------------|-----------------------------------------|
| `Authorization`  | `Token {MIST_API_TOKEN}`               | mistapi.APISession (from `.env`)        |
| `Accept`         | `application/json`                     | mistapi.APISession default              |
| `User-Agent`     | `mistapi/{version}`                    | mistapi.APISession default              |

### Request Body

None (GET request).

## Response Schema (200 OK)

Single JSON object. Source:
`documentation/api/sites/GET_sites_site_id_mxedges_events_count.md` lines 49-103.

```json
{
  "type": "object",
  "required": ["distinct", "end", "limit", "results", "start", "total"],
  "properties": {
    "distinct": {
      "type": "string",
      "description": "Grouping attribute echoed by the API (same as the request param)."
    },
    "end": {
      "type": "integer",
      "contentEncoding": "int32",
      "description": "Window end as epoch seconds."
    },
    "limit": {
      "type": "integer",
      "contentEncoding": "int32",
      "description": "Bucket cap echoed from the request."
    },
    "start": {
      "type": "integer",
      "contentEncoding": "int32",
      "description": "Window start as epoch seconds."
    },
    "total": {
      "type": "integer",
      "contentEncoding": "int32",
      "description": "Total event count across all buckets."
    },
    "results": {
      "type": "array",
      "uniqueItems": true,
      "description": "One entry per distinct value, with its count.",
      "items": {
        "title": "count_result",
        "type": "object",
        "required": ["count"],
        "properties": {
          "count": {
            "type": "integer",
            "contentEncoding": "int32",
            "description": "Event count for this bucket."
          }
        },
        "additionalProperties": {
          "type": "string",
          "description": "Dynamic key whose name equals the `distinct` request value and whose value is the observed grouping value (e.g. `type: MXEDGE_TUNTERM_CONNECTED`)."
        }
      }
    }
  }
}
```

### Worked Example (200)

Request:
```text
GET /api/v1/sites/4ac1d65b-1234-4def-89ab-4f8e9b21a113/mxedges/events/count
    ?distinct=type&duration=1d&limit=100
```

Response:
```json
{
  "distinct": "type",
  "start": 1719360000,
  "end":   1719446400,
  "limit": 100,
  "total": 4218,
  "results": [
    {"count": 2031, "type": "MXEDGE_TUNTERM_CONNECTED"},
    {"count": 1130, "type": "MXEDGE_TUNTERM_DISCONNECTED"},
    {"count":   57, "type": "MXEDGE_AUTH_FAILURE"}
  ]
}
```

MistHelper flattens this into one row for
`site_mxedge_events_count_summary` plus three rows for
`site_mxedge_events_count_buckets`, keyed as documented in `data-model.md`.

## Error Responses and MistHelper Handling

| Status | Mist Meaning                                                          | MistHelper Handling                                                                                  |
|--------|-----------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| 400    | Bad Syntax (malformed query parameters)                                | Log `WARNING "400 Bad Syntax: %s"`; return 0; do not retry. Indicates a programmer error.            |
| 401    | Unauthorized (invalid / missing token)                                 | Log `ERROR "Authentication failed -- check MIST_API_TOKEN"`; return non-zero; never log the token.   |
| 403    | Permission Denied (token lacks read scope for the site)                | Log `WARNING "403 Permission Denied for site %s"`; return 0; advise checking token scope.            |
| 404    | Site UUID does not exist under the authenticated org                   | Log `WARNING "Site %s not found"`; return 0; no traceback (treated as benign).                       |
| 429    | Rate limit exceeded (5000 API calls / hour)                            | Trigger the existing adaptive delay (`delay_metrics.json` + `tuning_data.json`) and retry up to the configured cap; respect `--fast` retry ceiling. |
| 5xx    | Mist Cloud server error                                                | Log `ERROR` with status code; retry per existing back-off; surface failure if retries exhausted.     |

All log lines are ASCII-only and use `%s` formatting; no secrets are logged.

## Exact mistapi Python Call Signature

The enriched per-endpoint doc lists the callable as
`mistapi.api.v1.sites.mxedges.countSiteMxEdgeEvents()`. The canonical mistapi
0.59 module layout mirrors the OpenAPI path; the import used by MistHelper is:

```python
# Import path matches the OpenAPI path tokens.
from mistapi.api.v1.sites.mxedges.events import count as count_mod
```

Call shape:

```python
response = count_mod.countSiteMxEdgeEvents(            # Returns mistapi.APIResponse
    api_session,                                       # Authenticated mistapi.APISession
    site_id,                                           # Required path parameter (UUID string)
    distinct=None,                                     # Optional grouping attribute (str)
    mxedge_id=None,                                    # Optional Mist Edge filter (str)
    mxcluster_id=None,                                 # Optional Mist Edge cluster filter (str)
    type=None,                                         # Optional event-type filter (str)
    service=None,                                      # Optional service filter (str)
    start=None,                                        # Optional window start (str: epoch or relative)
    end=None,                                          # Optional window end (str: epoch or relative)
    duration="1d",                                     # Default window if start/end omitted
    limit=100,                                         # Default bucket cap
)
envelope = response.data                               # Parsed JSON object (dict)
status   = response.status_code                        # HTTP status (int)
```

Return type: `mistapi.APIResponse`. `response.data` is the parsed JSON envelope
(`dict`). `response.status_code` is the HTTP status. No additional pagination
plumbing is required for this endpoint -- a single GET returns the full count
slice in one envelope, bounded by `limit`.

## Implementation-Side Notes

- `mistapi.APISession` is constructed once at MistHelper startup from
  `MIST_HOST` and `MIST_API_TOKEN` in `.env`. The new menu method does not
  create its own session.
- The `distinct` request value is echoed in `response.data["distinct"]`; the
  flattener stores both copies for clarity and safe round-tripping.
- The `results[].<distinct>` key name is dynamic; MistHelper persists it as
  the generic `bucket_key` / `bucket_value` pair (see `data-model.md`).
- The endpoint does NOT require `org_id` in the path; the session's
  authenticated org is implicit. No `org_id` prompt is needed.
