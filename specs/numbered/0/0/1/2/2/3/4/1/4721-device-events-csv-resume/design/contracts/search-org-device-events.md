# Contract: Mist device event search

## Request

The exporter calls the SDK method, not the REST endpoint directly.

```text
mistapi.api.v1.orgs.devices.searchOrgDeviceEvents(
    apisession,          # the authenticated session
    org_id,              # positional organization identifier
    device_type="all",   # _DEVICE_TYPE_ALL (line 21)
    limit=1000,          # _DEFAULT_LIMIT (line 24)
    duration="52w",      # _DEFAULT_DURATION (line 25)
    search_after=token,  # only when a checkpoint token exists
)
```

- The installed signature is at `.venv\Lib\site-packages\mistapi\api\v1\orgs\devices.py` line 259 (mistapi 0.64.1).
- The endpoint is `GET /api/v1/orgs/{org_id}/devices/events/search` (`documentation\mist-api-openapi31yaml.yaml` line 8667).
- The `search_after` query parameter is a string. Its description says Mist fills it from the `next` URL (lines 60227-60230).

## Response

The SDK stores the body in `APIResponse.data` (`__api_response.py` line 39). The exporter reads `data` as follows.

| Field | Source in code | Use |
| - | - | - |
| `results` or `data` | `_RESULT_KEYS` (line 30) | The rows of the page |
| `search_after` or `next` | `_TOKEN_KEYS` (line 29) | The next checkpoint token |

The OpenAPI schema `response_device_events_search` (lines 94028-94057) lists these fields as required: `results`, `start`, `end`, `limit`, and `total`. The field `next` is optional. Its description reads "Pagination cursor or URL" (lines 94038-94041).

## Open point

The live form of `next` is unverified (research U-1). If the live value is a URL, the resumed run cannot read the cursor from it. An owner must confirm the live form before merge. This change keeps the raw value (decision D-11).

## Error handling

- The preload calls `_fetch_page` once for each page with no retry (lines 207 and 157-164).
- The streaming loop retries each page up to three times with exponential backoff (lines 222-242).
- The SDK logs an error status at lines 60-64 of `__api_response.py`. The file contains no `raise` statement. The exporter therefore sees an error status only as a body without `results`.
