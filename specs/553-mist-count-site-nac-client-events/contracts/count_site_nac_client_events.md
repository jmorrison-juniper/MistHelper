# Endpoint Contract: countSiteNacClientEvents

Source-of-truth doc:
`documentation/api/sites/GET_sites_site_id_nac_clients_events_count.md`.

## HTTP Contract

| Field | Value |
|-------|-------|
| Method | `GET` |
| URL template | `https://{MIST_HOST}/api/v1/sites/{site_id}/nac_clients/events/count` |
| Required path params | `site_id` (string, UUID) |
| Required headers | `Authorization: Token {MIST_API_TOKEN}` (or `X-CSRFToken` cookie for web sessions) |
| Request body | None (GET) |
| Idempotent | Yes (read-only) |
| Pagination | Supported via `limit` and `page` query params |

### Query Parameters

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `distinct` | string | No | (server default) | NAC event field to group on (e.g. `type`, `nas_vendor`, `auth_type`, `ssid`, `vlan`). MistHelper default in code: `type`. |
| `type` | string | No | (none) | Filter to a specific NAC event type. See `listNacEventsDefinitions` for valid values. |
| `start` | string | No | (none) | Start time, epoch seconds or relative string (`-1d`, `-1w`). |
| `end` | string | No | (none) | End time, epoch seconds or relative string (`now`, `-1h`). |
| `duration` | string | No | `1d` | Window like `7d`, `2w`. Ignored if `start` and `end` are both supplied. |
| `limit` | integer | No | `100` | Max distinct buckets returned. |

## Successful Response (200)

Single envelope JSON object. Required keys: `distinct`, `end`, `limit`, `results`,
`start`, `total`.

```json
{
  "distinct": "type",
  "start": 1719600000,
  "end":   1719686400,
  "limit": 100,
  "total": 42,
  "results": [
    { "count": 30, "type": "NAC_CLIENT_PERMIT" },
    { "count":  8, "type": "NAC_CLIENT_DENY"   },
    { "count":  4, "type": "NAC_SESSION_END"   }
  ]
}
```

### Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `distinct` | string | Echo of the request `distinct` query param. |
| `start` | integer (int32) | Window start, epoch seconds. |
| `end` | integer (int32) | Window end, epoch seconds. |
| `limit` | integer (int32) | Echo of the request `limit` query param. |
| `total` | integer (int32) | Total NAC events counted across all buckets. |
| `results` | array of objects | Bucket list (`uniqueItems: true`). Each item has a required `count` field plus one additional property whose key is the value of `distinct` and whose value is the bucket label. |

## Error Responses

| Status | Mist API Meaning | MistHelper Handling |
|--------|------------------|---------------------|
| 400 | Bad Syntax (malformed query param) | `logging.warning("Bad request to countSiteNacClientEvents: %s", err)`; method returns 1; no traceback. |
| 401 | Unauthorized (invalid / expired token) | `logging.error("Mist API rejected token -- check MIST_API_TOKEN in .env")`; method returns 2. Re-raise is suppressed to keep the menu loop alive. |
| 403 | Permission Denied (token lacks site scope) | `logging.error("Token lacks permission for site %s", site_id)`; method returns 3. |
| 404 | Not found (unknown `site_id` or endpoint disabled) | `logging.warning("Site %s not found (404)", site_id)`; method returns 0 with a "no data returned" message -- per edge case in spec.md. |
| 429 | Too Many Requests (5000/hour token cap) | Adaptive delay system in `delay_metrics.json` / `tuning_data.json` engages automatically (existing transport layer); on persistent 429 the method returns 4 after the configured retry budget exhausts. |

All error paths use `logging.exception` for unexpected exceptions (catch-all), with the
API token never appearing in any log line.

## mistapi Python Call Signature

```python
import mistapi
import mistapi.api.v1.sites.nac_clients.events.count as count_endpoint

# mist_session is the existing module-level APISession built from .env at startup.
api_response = count_endpoint.countSiteNacClientEvents(
    mist_session,                # APISession; carries MIST_HOST + MIST_API_TOKEN
    site_id,                     # string UUID, required path param
    distinct="type",             # optional, MistHelper default
    type=None,                   # optional, no filter
    start=None,                  # optional, omitted in favour of duration
    end=None,                    # optional, omitted in favour of duration
    duration="1d",               # optional, MistHelper default
    limit=100,                   # optional, MistHelper default
)

# api_response is a mistapi.APIResponse.
# api_response.status_code -> int (200 on success)
# api_response.data        -> dict matching the 200 schema above
envelope = api_response.data
total_events = envelope["total"]
buckets = envelope["results"]
```

### Notes on the SDK Import Path

The enriched doc lists the legacy spelling
`mistapi.api.v1.sites.clients_-_nac.countSiteNacClientEvents()`. In `mistapi` 0.59+
this resolves through the canonical, importable Python path
`mistapi.api.v1.sites.nac_clients.events.count`, which is the path other
`/api/v1/sites/{site_id}/nac_clients/events/*` SDK functions live under (for example
`searchSiteNacClientEvents`). The canonical import path is what the new MistHelper
method uses.
