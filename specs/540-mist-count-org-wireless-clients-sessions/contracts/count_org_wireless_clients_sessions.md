# Phase 1 Contract: countOrgWirelessClientsSessions

**Spec**: [spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md) | **Date**: 2026-06-29

Source of truth: `documentation/api/orgs/GET_orgs_org_id_clients_sessions_count.md`.

## HTTP Contract

- **Method**: `GET`
- **URL Template**: `https://{MIST_HOST}/api/v1/orgs/{org_id}/clients/sessions/count`
- **Authentication**: `Authorization: Token {MIST_API_TOKEN}` header (or
  `X-CSRFToken` cookie for browser-session auth). Token loaded from `.env`
  by `mistapi.APISession`; never logged by MistHelper.
- **Content-Type (request)**: not applicable -- no request body.
- **Accept (response)**: `application/json`.

### Path Parameters

| Name    | Type   | Required | Description                                              |
|---------|--------|----------|----------------------------------------------------------|
| org_id  | string | YES      | Mist organization UUID. Validated as UUID before call.   |

### Query Parameters

| Name                | Type    | Required | Default | Notes                                                                  |
|---------------------|---------|----------|---------|------------------------------------------------------------------------|
| distinct            | string  | no       | ssid    | MistHelper-default ssid. Accepted: `ssid`, `ap`, `band`, `client_family`, `client_manufacture`, `client_model`, `client_os`, `wlan_id`. |
| ap                  | string  | no       | -       | AP MAC filter (not exposed in v1 prompt).                              |
| band                | string  | no       | -       | 802.11 band filter (not exposed in v1 prompt).                         |
| client_family       | string  | no       | -       | Filter on family (e.g. "Mac", "iPhone"). Not exposed in v1 prompt.     |
| client_manufacture  | string  | no       | -       | Filter on manufacture (e.g. "Apple"). Not exposed in v1 prompt.        |
| client_model        | string  | no       | -       | Filter on model. Not exposed in v1 prompt.                             |
| client_os           | string  | no       | -       | Filter on OS. Not exposed in v1 prompt.                                |
| ssid                | string  | no       | -       | Filter on SSID (vs `distinct=ssid` which buckets ON it).               |
| wlan_id             | string  | no       | -       | Filter on WLAN UUID. Not exposed in v1 prompt.                         |
| start               | string  | no       | -       | Epoch seconds OR relative string ("-1d", "-1w"). Not exposed v1.       |
| end                 | string  | no       | -       | Epoch seconds OR relative string ("-1d", "-2h", "now"). Not exposed v1.|
| duration            | string  | no       | 1d      | Time window (e.g. `7d`, `2w`). Exposed at the prompt.                  |
| limit               | integer | no       | 100     | Server-side cap; MistHelper passes `1000` to capture wider results.    |

### Required Headers

```http
Authorization: Token {MIST_API_TOKEN}
Accept: application/json
User-Agent: mistapi/0.59+ python-requests/...
```

## Response Schema (200)

JSON object with the following required keys:

```json
{
  "distinct": "ssid",
  "start": 1719600000,
  "end": 1719686400,
  "limit": 100,
  "total": 12,
  "results": [
    { "count": 245, "ssid": "Corp-Guest" },
    { "count":  88, "ssid": "Corp-Internal" }
  ]
}
```

| Field      | Type    | Required | Notes                                                                 |
|------------|---------|----------|-----------------------------------------------------------------------|
| distinct   | string  | YES      | Echoes the requested attribute name.                                  |
| start      | integer | YES      | Epoch seconds, window start.                                          |
| end        | integer | YES      | Epoch seconds, window end.                                            |
| limit      | integer | YES      | Echoes the requested page size.                                       |
| total      | integer | YES      | Total bucket count (may exceed `len(results)` if paging is engaged).  |
| results    | array   | YES      | Unique items. Each item is a `count_result` object (see below).       |

### count_result Object

```json
{ "count": 245, "<distinct_attr>": "<bucket_value>" }
```

| Field                | Type    | Required | Notes                                                                                                 |
|----------------------|---------|----------|-------------------------------------------------------------------------------------------------------|
| count                | integer | YES      | Number of sessions in this bucket.                                                                    |
| _(additional)_       | string  | YES      | Exactly one extra string property whose key is the value of `distinct` (e.g. `ssid`) and whose value is the bucket label. MistHelper stores the value in column `bucket_value` and discards the key (it already lives in column `distinct`). |

## Error Responses

| Status | Mist Description                                                                                  | MistHelper Handling                                                                                                                                                              |
|--------|---------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 400    | Bad Syntax -- malformed query string (e.g. invalid `duration`).                                   | Log `WARNING` with the rejected parameter name; do NOT log token or full URL. Return early without writing rows.                                                                 |
| 401    | Unauthorized -- token missing, malformed, or revoked.                                             | Surface via the existing `mistapi.APISession` error path. MistHelper logs an `ERROR` and re-raises so the menu loop can exit cleanly.                                            |
| 403    | Permission Denied -- token lacks org-level read access.                                           | Log `WARNING` "Permission denied for org %s" (no token in the line) and return.                                                                                                  |
| 404    | Not found -- endpoint missing OR resource (org) missing.                                          | Log `WARNING` "Org %s not found or endpoint unavailable" and return without writing rows. No traceback.                                                                          |
| 429    | Too Many Requests -- 5000 calls/hour token budget exhausted.                                      | The adaptive delay system (`delay_metrics.json`, `tuning_data.json`) backs off automatically. MistHelper retries per the standard retry budget; no manual user action required.  |

All error paths preserve exit code 0 on the menu loop (the menu item is
non-destructive) -- a failure logs and returns, never raises into the menu
dispatcher.

## mistapi Python Call Signature

```python
import mistapi.api.v1.orgs.clients.sessions.count as _sessions_count

response = _sessions_count.countOrgWirelessClientsSessions(
    self.apisession,                  # mistapi.APISession bound to MIST_HOST + MIST_API_TOKEN
    org_id,                           # path param -- string UUID
    distinct=distinct,                # query param -- enum string, default "ssid"
    ap=None,                          # query param -- not exposed at the prompt in v1
    band=None,                        # query param -- not exposed at the prompt in v1
    client_family=None,               # query param -- not exposed at the prompt in v1
    client_manufacture=None,          # query param -- not exposed at the prompt in v1
    client_model=None,                # query param -- not exposed at the prompt in v1
    client_os=None,                   # query param -- not exposed at the prompt in v1
    ssid=None,                        # filter (distinct from "distinct=ssid"); not exposed v1
    wlan_id=None,                     # query param -- not exposed at the prompt in v1
    start=None,                       # query param -- omitted in favour of duration
    end=None,                         # query param -- omitted in favour of duration
    duration=duration,                # query param -- string, default "1d"
    limit=1000,                       # query param -- raised from API default 100 for broader coverage
)
# response.data is the JSON object documented above.
```

The return type follows the standard `mistapi.APIResponse` envelope:

- `response.status_code` -- HTTP status (200 on success)
- `response.data` -- parsed JSON body (the response object documented above)
- `response.headers` -- response headers (including rate-limit hints)
- `response.next` / `response.previous` -- pagination URLs when applicable

MistHelper inspects `response.data` only; status-code-driven branching is
handled inside the `mistapi` SDK (it raises typed exceptions for 4xx/5xx that
propagate through the existing menu-level error handler).
