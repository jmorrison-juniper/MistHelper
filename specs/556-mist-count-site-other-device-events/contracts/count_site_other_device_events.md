# Endpoint Contract: countSiteOtherDeviceEvents

**Spec**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md) | **Data Model**: [../data-model.md](../data-model.md)
**Source doc**: `documentation/api/sites/GET_sites_site_id_otherdevices_events_count.md`

This contract is the authoritative reference for what MistHelper sends, what
the Mist API returns, and how MistHelper handles each documented error
response. It is the source of truth for `/speckit.tasks` and for any future
review or audit of the menu 197 implementation.

## HTTP Contract

| Field | Value |
|-------|-------|
| Method | `GET` |
| URL template | `https://{MIST_HOST}/api/v1/sites/{site_id}/otherdevices/events/count` |
| Path params (required) | `site_id` (string, UUID) |
| Query params (all optional) | `distinct` (string), `type` (string), `start` (string, epoch s or relative like `-1d`), `end` (string, epoch s or relative like `now`), `duration` (string, default `1d`), `limit` (integer, default `100`) |
| Required headers | `Authorization: Token {MIST_API_TOKEN}` (managed by `mistapi.APISession`); `Accept: application/json` |
| Request body | None |
| Idempotent | Yes (safe to retry) |
| Pagination | Not used by MistHelper; `limit` caps the number of distinct groups returned in a single call, but the response is a single JSON object, not a paginated list |
| Rate limit | Standard Mist API rate limit (5000 calls/hour per token); 429 is handled by the existing adaptive delay system |

### Concrete example URL

```
GET https://api.mist.com/api/v1/sites/11111111-2222-3333-4444-555555555555/otherdevices/events/count?distinct=type&duration=1d&limit=100
```

## Success Response: 200 OK

Content-Type: `application/json`

Body schema (transcribed from
`documentation/api/sites/GET_sites_site_id_otherdevices_events_count.md`):

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

### Concrete example success body

```json
{
  "distinct": "type",
  "start": 1719600000,
  "end":   1719686400,
  "limit": 100,
  "total": 42,
  "results": [
    { "count": 30, "type": "OTHER_DEVICE_EVENT_FOO" },
    { "count": 12, "type": "OTHER_DEVICE_EVENT_BAR" }
  ]
}
```

Each item in `results` has exactly one numeric field (`count`) plus one or
more string-typed dynamic fields whose names match the `distinct` argument
the caller sent. MistHelper extracts the first non-`count` key/value as
`group_value` when flattening.

## Error Responses

| Status | API Meaning | MistHelper Handling |
|--------|-------------|---------------------|
| 400 | Bad Syntax (invalid query param combination) | Logged at `ERROR` with the offending parameter, no traceback. Method returns without writing output. The user is told (via stderr) to re-run with corrected inputs. |
| 401 | Unauthorized (missing or expired token) | Logged at `ERROR`. Method returns without writing output. The user is told to check `MIST_API_TOKEN` in `.env`. The token value itself is never logged. |
| 403 | Permission Denied (token lacks rights to this org or site) | Logged at `WARNING` with the site_id (never the token). Method returns without writing output. |
| 404 | Not Found (unknown site_id, or no events endpoint for this site) | Logged at `WARNING` with the site_id. Method returns without writing output. This is an expected condition when a user typos the site_id, not a crash. |
| 429 | Too Many Requests (5000 calls/hour exceeded) | Triggers the adaptive delay system already implemented in MistHelper (`delay_metrics.json` + `tuning_data.json`). The SDK call is retried with backoff; the user sees a single `INFO` line per retry. No manual intervention required. |
| 5xx | Server-side error | Caught by the existing global exception handler in the main menu loop. Logged at `ERROR` via `logging.exception` with full traceback. The menu returns to the prompt without exiting the program. |

MistHelper never converts an HTTP error into a traceback at the user prompt;
every documented status above is downgraded to a structured log line. Per
Constitution Principle III, an EOF on `safe_input()` during prompt collection
exits cleanly with code 0.

## Exact `mistapi` Python Call Signature

```python
import mistapi
import mistapi.api.v1.sites.otherdevices.events.count

# mist_session is a long-lived mistapi.APISession created at app start
# from MIST_HOST and MIST_API_TOKEN. It is reused across menu items.

response = mistapi.api.v1.sites.otherdevices.events.count.countSiteOtherDeviceEvents(
    mist_session,                          # positional: the APISession
    site_id,                               # positional: required path param, str UUID
    distinct="type",                       # keyword: optional, attribute to group by
    type=None,                             # keyword: optional, event type filter
    start=None,                            # keyword: optional, epoch s or relative like "-1d"
    end=None,                              # keyword: optional, epoch s or relative like "now"
    duration="1d",                         # keyword: optional, default "1d" per OpenAPI
    limit=100,                             # keyword: optional, default 100 per OpenAPI
)

# response.status_code -> int
# response.data        -> dict matching the 200 schema above
# response.headers     -> dict
```

Notes for the implementer:

- The dotted module path `mistapi.api.v1.sites.otherdevices.events.count` is
  the legal Python identifier form. The enriched API doc additionally lists
  the alias `mistapi.api.v1.sites.devices_-_others.countSiteOtherDeviceEvents()`,
  but that alias is illegal as a Python identifier (`-` is not allowed) and
  must not be used in `import` statements. If at implementation time the
  installed mistapi version exposes only the alias, file a follow-up issue;
  do not work around it with `importlib`.
- The SDK uses `requests` under the hood; transport errors (DNS, TCP, TLS)
  surface as `requests.exceptions.RequestException` subclasses. The existing
  global exception handler catches these.
- `response.data` is always a `dict` on a 200; on a 4xx/5xx the SDK still
  populates `.data` with whatever JSON body the server sent (often an error
  envelope). Callers should branch on `response.status_code` before
  dereferencing `response.data`.

## Conformance Checklist (re-derived from spec.md FRs)

- **FR-001**: The contract uses the exact `mistapi` SDK call shown above. PASS.
- **FR-002**: All prompts in the calling method go through `safe_input()` per
  research.md Task 5. PASS.
- **FR-003**: 429 handling uses the existing adaptive delay system. PASS.
- **FR-004**: Response is persisted via
  `DataExporter.write_with_format_selection(...)` with
  `api_function_name="countSiteOtherDeviceEvents"`. PASS.
- **FR-005**: `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry defined in data-model.md.
  PASS.
- **FR-006**: `INFO` before / `DEBUG` after, ASCII-only, per Principle VII.
  PASS.
- **FR-007**: Inline comments on every new executable line per Principle VI.
  PASS.
- **FR-008**: README.md menu table and CHANGELOG.md updated in the
  implementation PR (tracked by `/speckit.tasks`). PASS-on-implementation.
