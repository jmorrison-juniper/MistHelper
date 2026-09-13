# Contract: countOrgNacClientEvents

**Feature**: `521-mist-count-org-nac-client-events`
**Source endpoint doc**: `documentation/api/orgs/GET_orgs_org_id_nac_clients_events_count.md`

This contract is the authoritative HTTP and SDK-level specification consumed
by the MistHelper menu 195 implementation. Any deviation between this file and
the runtime behavior of the `mistapi` SDK is a defect.

## 1. HTTP Contract

| Aspect          | Value                                                         |
|-----------------|---------------------------------------------------------------|
| Method          | `GET`                                                         |
| URL template    | `https://{MIST_HOST}/api/v1/orgs/{org_id}/nac_clients/events/count` |
| Auth header     | `Authorization: Token {MIST_API_TOKEN}`                       |
| Accept          | `application/json`                                            |
| Content-Type    | None (no request body)                                        |
| Request body    | None                                                          |

### 1.1 Path parameters

| Name     | Type   | Required | Description                                                    |
|----------|--------|----------|----------------------------------------------------------------|
| `org_id` | string | Yes      | Organization UUID. Validated against the Mist UUID regex before the SDK call. |

### 1.2 Query parameters

| Name       | Type    | Required | Default | Allowed values                                                                | Description                                                                  |
|------------|---------|----------|---------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| `distinct` | string  | No       | (none)  | `type`, `nas_vendor`, `vlan`, `ssid`, `port_type`, `auth_type` (allow-list)   | Attribute to group counts by. MistHelper validates against the allow-list.   |
| `type`     | string  | No       | (none)  | Any NAC event type from `listNacEventsDefinitions`                            | Filter to only count events of this exact type.                              |
| `start`    | string  | No       | (none)  | Epoch seconds or relative string (`-1d`, `-1w`, `-2h`)                        | Window start. Mutually compatible with `end` (range mode).                   |
| `end`      | string  | No       | (none)  | Epoch seconds or relative string (`-1d`, `-2h`, `now`)                        | Window end.                                                                  |
| `duration` | string  | No       | `1d`    | e.g. `1h`, `1d`, `7d`, `2w`                                                   | Rolling window length anchored to `now`. Used when `start`/`end` are absent. |
| `limit`    | integer | No       | `100`   | Positive integer                                                              | Maximum number of group rows returned in `results`.                          |

### 1.3 Response headers

Standard Mist API response headers including `Content-Type: application/json`,
`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`. The
adaptive delay system in `delay_metrics.json` consumes the rate-limit headers
automatically through the `mistapi` SDK.

## 2. 200 Success Response Schema

Schema (excerpted verbatim from
`documentation/api/orgs/GET_orgs_org_id_nac_clients_events_count.md`):

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

Example 200 body for `distinct=type, duration=1d`:

```json
{
  "distinct": "type",
  "start": 1719504000,
  "end":   1719590400,
  "limit": 100,
  "total": 1487,
  "results": [
    { "type": "NAC_CLIENT_PERMIT",       "count": 1102 },
    { "type": "NAC_CLIENT_DENY",         "count":  254 },
    { "type": "NAC_CLIENT_SESSION_END",  "count":  131 }
  ]
}
```

Notes on `results[i]`:

- `count` is always present and is the event count for the group.
- The second key on each item is the value of the `distinct` field passed in
  the request (here `type`). Its key name is therefore dynamic; MistHelper
  reads it via `row.get(distinct_field)` and stores it in the SQLite column
  `distinct_value`.
- Additional string-valued properties are permitted by the schema's
  `additionalProperties` clause but are not currently emitted by the Mist API
  for this endpoint. If they appear in future, MistHelper preserves only the
  documented columns; extras are dropped with a `DEBUG` log line.

## 3. Error Responses and MistHelper Handling

| HTTP | Mist meaning                                                                    | MistHelper behavior                                                                          |
|------|---------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| 400  | Bad syntax (e.g. unknown `distinct` field or malformed `start`)                 | Log `WARNING` with the parameter set; return early; menu prompts user to retry.               |
| 401  | Unauthorized (missing or invalid token)                                         | Log `ERROR`; raise to the main loop which prints "Check MIST_API_TOKEN in .env" and exits 2.  |
| 403  | Permission denied (token lacks NAC read scope on this org)                      | Log `ERROR`; return early; menu prints "Token does not have NAC read access on org <id>".     |
| 404  | Org not found or endpoint missing                                               | Log `WARNING`; return early with "No data" message; do not write an empty CSV.                |
| 429  | Rate limit hit (5000 calls / hour per token)                                    | Adaptive delay system in `delay_metrics.json` backs off and retries up to `MAX_RETRIES`.      |

All five error branches use `logging.warning` / `logging.error` with ASCII-only
messages and never log the API token or the full request URL (which carries the
token in the `Authorization` header but not the URL itself; defensive policy).

## 4. mistapi Python Call Signature

```python
import mistapi
from mistapi.api.v1.orgs.nac_clients.events.count import countOrgNacClientEvents

response = countOrgNacClientEvents(
    mist_session,            # mistapi.APISession created from .env at startup
    org_id,                  # str, validated UUID
    distinct=distinct_field, # one of the allow-listed values; pass None to omit
    type=event_type_filter,  # str or None
    start=start_epoch,       # int (epoch s) or str (relative) or None
    end=end_epoch,           # int (epoch s) or str (relative) or None
    duration=duration_str,   # str like "1d", default "1d"
    limit=row_limit,         # int, default 100
)

assert response.status_code == 200, f"Expected 200, got {response.status_code}"
payload = response.data  # dict matching the schema in section 2
```

Return type: `mistapi.APIResponse` with attributes:

- `.status_code` -- HTTP status integer.
- `.data` -- parsed JSON body (dict for this endpoint).
- `.headers` -- response headers (used by the adaptive delay system).
- `.url` -- final URL (logged at `DEBUG` only, never `INFO`).

## 5. Idempotency and Side Effects

- **Idempotent**: Yes. The same query produces the same `total` and the same
  `results` set (modulo new events arriving in the window).
- **Side effects on Mist Cloud**: None. Read-only.
- **Side effects in MistHelper**: One upsert per group row into
  `org_nac_client_events_count` (SQLite) plus one CSV file written and
  optional ArangoDB document upserts via `DataExporter`.
