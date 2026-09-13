# Endpoint Contract: countSiteGuestAuthorizations

**Spec**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md)
**Source doc**: `documentation/api/sites/GET_sites_site_id_guests_count.md`

## HTTP

| Field        | Value                                                |
|--------------|------------------------------------------------------|
| **Method**   | `GET`                                                |
| **URL**      | `https://{MIST_HOST}/api/v1/sites/{site_id}/guests/count` |
| **operationId** | `countSiteGuestAuthorizations`                    |
| **Tag**      | `Sites Guests`                                       |
| **Authentication** | `Authorization: Token {MIST_API_TOKEN}` header (Mist SDK injects this automatically) |
| **Content-Type request** | (none -- GET, no body)                   |
| **Content-Type response** | `application/json`                      |

## Path parameters

| Name      | Type   | Required | Description                                |
|-----------|--------|----------|--------------------------------------------|
| `site_id` | string (UUID) | Yes | The Mist site to count authorized guests for. Must be a valid Mist UUID. Validated client-side before the call. |

## Query parameters

| Name       | Type    | Required | Default | Description |
|------------|---------|----------|---------|-------------|
| `distinct` | string  | No       | `wlan_id` (per Mist UI default; the OpenAPI schema does not specify a default) | The attribute to group counts by. Common values observed in production: `ssid`, `wlan_id`, `auth_method`, `hostname`. Free-text accepted by the API. |
| `start`    | string  | No       | (omitted) | Start of window. Epoch seconds (e.g. `1719600000`) or relative string (`-1d`, `-1w`). If provided together with `end`, `duration` is ignored by the API. |
| `end`      | string  | No       | (omitted) | End of window. Epoch seconds or relative string (`-1h`, `now`). |
| `duration` | string  | No       | `1d`    | Convenience window length used when `start`/`end` are omitted. Examples: `1d`, `7d`, `2w`. |
| `limit`    | integer | No       | `100`   | Maximum number of distinct buckets returned in `results[]`. |

MistHelper's menu prompts expose only `site_id`, `distinct`, and `duration` (with the
defaults shown above). `start` / `end` / `limit` use API defaults. See `research.md`
Task 5 for rationale.

## Request headers

| Header          | Value                                       |
|-----------------|---------------------------------------------|
| `Authorization` | `Token <MIST_API_TOKEN>` (injected by SDK)  |
| `Accept`        | `application/json` (injected by SDK)        |
| `User-Agent`    | `mistapi-python/<version>` (set by SDK)     |

## Request body

None (HTTP GET).

## Response: 200 OK

Single JSON object with all of `distinct`, `start`, `end`, `limit`, `total`, `results`
required.

```json
{
  "distinct": "wlan_id",
  "start":    1719600000,
  "end":      1719686400,
  "limit":    100,
  "total":    873,
  "results": [
    { "count": 412, "wlan_id": "1c7d2c0a-1234-5678-9abc-aaaa00000001" },
    { "count": 287, "wlan_id": "1c7d2c0a-1234-5678-9abc-bbbb00000002" },
    { "count": 174, "wlan_id": "<unknown>" }
  ]
}
```

### Top-level fields

| Field      | JSON type | Notes                                                     |
|------------|-----------|-----------------------------------------------------------|
| `distinct` | string    | Echoes the request's `distinct` argument.                 |
| `start`    | integer (int32) | Epoch seconds. Window start.                        |
| `end`      | integer (int32) | Epoch seconds. Window end.                          |
| `limit`    | integer (int32) | Bucket cap actually applied (defaults to 100).      |
| `total`    | integer (int32) | Sum of `count` across all buckets in the window.    |
| `results`  | array of `count_result` | Unique items; see below.                  |

### `count_result` item schema

| Field       | JSON type | Required | Notes                                                |
|-------------|-----------|----------|------------------------------------------------------|
| `count`     | integer   | Yes      | Number of authorized guests in this bucket.          |
| `<distinct>`| string    | Implied  | Key name equals the value of the request's `distinct` argument. May be missing if the bucket represents guests with no value for that attribute -- MistHelper flattens this to literal `<unknown>`. |

`additionalProperties: { type: string }` -- the API may return extra string fields per
bucket in the future; MistHelper preserves them via DataExporter's generic flatten.

## Error responses

| Status | Meaning                                                        | MistHelper handling |
|--------|----------------------------------------------------------------|---------------------|
| 400    | Bad Syntax (malformed `distinct`, bad `start`/`end` format)    | `logging.warning("Bad request for site %s: %s", site_id, exc)` and return. |
| 401    | Unauthorized (token missing / expired)                         | `logging.error(...)` with redacted detail; surface a "Check MIST_API_TOKEN in .env" hint to the operator. |
| 403    | Permission Denied (token lacks scope for this site)            | `logging.error("Permission denied for site %s", site_id)` and return. |
| 404    | Site not found                                                 | `logging.warning("Site %s not found", site_id)` and return. |
| 429    | Rate limit exceeded (5000 calls/hour)                          | Caught by `mistapi` retry layer + MistHelper's adaptive delay (`delay_metrics.json`, `tuning_data.json`); no operator action required. Logged at `INFO`. |

Unexpected exceptions are caught at the menu boundary and logged via
`logging.exception(...)` -- the menu returns to the main loop without crashing.

## Exact mistapi Python call signature

```python
import mistapi.api.v1.sites.guests.count as _mist_csga

response = _mist_csga.countSiteGuestAuthorizations(
    mist_session,            # mistapi.APISession; bootstrapped from .env at startup.
    site_id,                 # str: validated UUID.
    distinct=distinct,       # str | None: e.g. "wlan_id". None lets the API default apply.
    start=start,             # str | int | None: epoch seconds or relative string.
    end=end,                 # str | int | None: epoch seconds or relative string.
    duration=duration,       # str | None: e.g. "1d". Ignored if start+end provided.
    limit=limit,             # int | None: bucket cap. None lets the API default apply.
)

# response is a mistapi APIResponse:
status_code = response.status_code   # 200 on success.
payload     = response.data          # dict shaped per the schema above.
raw_url     = response.url           # for debugging; NEVER logged in production.
```

MistHelper invokes this through the `OrgSiteExporter.count_site_guest_authorizations`
method (see `quickstart.md` for the full skeleton). The call site:

```python
response = mistapi.api.v1.sites.guests.count.countSiteGuestAuthorizations(
    apisession,
    site_id,
    distinct=distinct,
    duration=duration,
)
```

`start`, `end`, and `limit` are intentionally omitted at the call site -- they fall
back to API defaults to keep the menu prompt count within the 5-Item Rule.

## Pagination

Not applicable. The endpoint returns a single aggregate object; `limit` caps bucket
cardinality, not pages. MistHelper does NOT call `mistapi.get_all()` on this response.

## Rate limiting

Subject to the standard Mist API limit of 5000 calls per hour per token. The adaptive
delay system (`delay_metrics.json` + `tuning_data.json`) governs back-off identically
to all other menu items; no per-endpoint tuning is required.

## Security notes

- API token is loaded from `.env` and held only in the `mistapi.APISession` instance.
- The token is never logged, never written to `data/`, and never echoed to the operator.
- The full request URL (which would expose `site_id` in a log aggregator) is logged at
  `DEBUG` only and only when log level is explicitly raised; default `INFO` runs do not
  emit it.
- No PII is returned by this endpoint -- only counts and a distinct-attribute value
  (typically a WLAN UUID or SSID name).
