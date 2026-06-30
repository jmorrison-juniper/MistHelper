# Endpoint Contract: countSiteWanClients

**Feature**: 563-mist-count-site-wan-clients
**Spec**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md)
**Authoritative doc**:
`documentation/api/sites/GET_sites_site_id_wan_clients_count.md`

This contract is the single source of truth for the HTTP and SDK behavior MistHelper
must honor. Any drift between this file and the linked endpoint doc must be reconciled
before implementation begins.

---

## 1. HTTP Contract

| Field | Value |
|---|---|
| **Method** | `GET` |
| **URL template** | `https://{MIST_HOST}/api/v1/sites/{site_id}/wan_clients/count` |
| **Auth** | `Authorization: Token {MIST_API_TOKEN}` header (or `X-CSRFToken` cookie). Loaded from `.env`; never logged. |
| **Content-Type (request)** | n/a (no request body) |
| **Accept (response)** | `application/json` |
| **Pagination** | Supports `limit` query parameter; the response is a single envelope so multi-page traversal is not required for this catalog feature. |
| **Rate limit** | Standard Mist API limit (5000 calls / hour / token). The shared adaptive-delay machinery (`delay_metrics.json`, `tuning_data.json`) governs back-off. |

### 1.1 Path Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `site_id` | string (UUID) | Yes | Mist site identifier. Validated against the 8-4-4-4-12 hex UUID shape before the SDK call. |

### 1.2 Query Parameters

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `distinct` | string | No | (empty) | The attribute to group counts by (e.g. `mac`, `hostname`, `ip`, `port_id`). When omitted the API returns a single bucket equal to `total`. |
| `start` | string | No | (empty) | Window start: epoch seconds (`1719600000`) or relative (`-1d`, `-1w`). |
| `end` | string | No | (empty) | Window end: epoch seconds or relative. |
| `duration` | string | No | `1d` | Lookback length (e.g. `1d`, `7d`, `2w`). Ignored when both `start` and `end` are set. |
| `limit` | integer | No | `100` | Maximum number of buckets returned in `results`. MistHelper UI caps user input at 1000. |

### 1.3 Request Headers (set by mistapi)

| Header | Value |
|--------|-------|
| `Authorization` | `Token <MIST_API_TOKEN>` |
| `Accept` | `application/json` |
| `User-Agent` | `mistapi/<version>` (set by SDK) |

No additional headers are added by MistHelper.

### 1.4 Request Body

None. This is a GET request.

---

## 2. Response Contract

### 2.1 200 OK -- Success

`Content-Type: application/json`

JSON schema (from `documentation/api/sites/GET_sites_site_id_wan_clients_count.md`):

```json
{
  "type": "object",
  "required": ["distinct", "end", "limit", "results", "start", "total"],
  "properties": {
    "distinct": { "type": "string" },
    "start":    { "type": "integer", "contentEncoding": "int32" },
    "end":      { "type": "integer", "contentEncoding": "int32" },
    "limit":    { "type": "integer", "contentEncoding": "int32" },
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

Example payload (illustrative):

```json
{
  "distinct": "mac",
  "start":    1719360000,
  "end":      1719446400,
  "limit":    100,
  "total":    37,
  "results": [
    { "count": 12, "mac": "aabbccddeeff" },
    { "count":  8, "mac": "001122334455" },
    { "count":  5, "mac": "5cb35a0e0001" }
  ]
}
```

The `additionalProperties` rule means every bucket carries exactly one extra string
field whose key equals the `distinct` value; MistHelper extracts that field as
`distinct_value` (see [../data-model.md](../data-model.md)).

### 2.2 Error Responses

| Status | Description | MistHelper Handling |
|--------|-------------|---------------------|
| `400` Bad Syntax | Malformed query parameter (e.g. `limit=abc`). | `logging.warning("Mist API 400 for countSiteWanClients: %s", body)`; return early. Do not retry. |
| `401` Unauthorized | Missing / invalid `MIST_API_TOKEN`. | `logging.error("Mist API 401 -- check MIST_API_TOKEN in .env")`; return early. **Never** log the token. |
| `403` Permission Denied | The token lacks read scope on the supplied site. | `logging.warning("Mist API 403 for site %s -- token lacks read access", site_id)`; return early. |
| `404` Not Found | `site_id` does not exist or endpoint is unavailable. | `logging.warning("Mist API 404 for site %s -- skipping", site_id)`; return early. No traceback. |
| `429` Too Many Requests | Token exceeded the 5000-calls-per-hour threshold. | Surfaced by `mistapi` retry layer; adaptive-delay back-off engages automatically. The new method does not implement its own retry. |
| `5xx` | Mist Cloud transient failure. | `mistapi` retries per its own policy; on terminal failure `logging.exception("...")` records the traceback and the method returns early. |

For every error path the method exits with code 0 from the menu loop -- the user is
returned to the main menu rather than being shown a stack trace, in line with
Constitution Principle III (Safety-First, NON-NEGOTIABLE).

---

## 3. mistapi SDK Call Signature

Authoritative SDK location:

```
mistapi.api.v1.sites.wan_clients.count.countSiteWanClients
```

### 3.1 Python signature

```python
def countSiteWanClients(
    mist_session,              # mistapi.APISession instance
    site_id,                   # required path param, UUID string
    distinct=None,             # optional facet name, string
    start=None,                # optional window start, int or relative string
    end=None,                  # optional window end, int or relative string
    duration="1d",             # optional lookback, default "1d"
    limit=100,                 # optional bucket cap, default 100
):
    """Returns mistapi.APIResponse.

    response.status_code -> int HTTP status
    response.data        -> dict matching the schema in section 2.1
    response.url         -> str the absolute URL hit (do NOT log -- contains site_id)
    """
```

### 3.2 Canonical call in MistHelper

```python
from mistapi.api.v1.sites.wan_clients import count as wan_clients_count   # SDK import alias

response = wan_clients_count.countSiteWanClients(   # the only Mist call this menu item makes
    self.apisession,                                # injected APISession from the existing menu base
    site_id=site_id,                                # validated UUID from safe_input()
    distinct=distinct or None,                      # None when user pressed Enter at the prompt
    start=time_window.get("start"),                 # may be int epoch or relative string
    end=time_window.get("end"),                     # may be int epoch or relative string
    duration=time_window.get("duration", "1d"),     # mirrors API default
    limit=time_window.get("limit", 100),            # mirrors API default
)
```

Every line above carries an inline comment per Constitution Principle VI
(NON-NEGOTIABLE).

### 3.3 Response handling contract

1. `response.status_code == 200` -> proceed to flatten.
2. `response.data is None` -> treat as empty payload; write a summary row with
   `total=0, bucket_count=0`; do not write any bucket rows.
3. Any non-200 -> log per the table in section 2.2 and return without writing.
4. Never inspect `response.url` for logging; it contains the site UUID and is
   considered identifying.

---

## 4. Idempotency & Side Effects

- **Idempotent on the Mist side**: GET with identical query parameters within the same
  window returns the same body.
- **Idempotent on the MistHelper side**: the composite PK strategy registered in
  `ENDPOINT_PRIMARY_KEY_STRATEGIES['countSiteWanClients']` (see
  [../data-model.md](../data-model.md)) ensures `INSERT OR REPLACE` upserts on
  repeated runs; the only mutating column on repeat is `fetched_at`.
- **No write side effects** against Mist Cloud.

---

## 5. Out-of-Scope Behavior

- Search endpoint `GET /api/v1/sites/{site_id}/wan_clients/search` -- a separate
  feature spec covers per-client detail retrieval.
- WAN client events count endpoint -- separate spec, separate menu item.
- Any POST / PUT / PATCH / DELETE against the same path -- not part of this contract.

---

## 6. Verification Checklist

- [ ] SDK module path resolves at runtime: `python -c "from mistapi.api.v1.sites.wan_clients import count"`.
- [ ] A live invocation against a known site returns 200 and the documented envelope keys.
- [ ] `ENDPOINT_PRIMARY_KEY_STRATEGIES['countSiteWanClients']` exists with `type='composite_pk'`.
- [ ] Repeated invocations within the same window do not produce duplicate rows in either SQLite table.
- [ ] All five error statuses (400 / 401 / 403 / 404 / 429) are exercised in negative-path smoke tests without producing a Python traceback at the menu prompt.
