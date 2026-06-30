# Contract: getOrgJseInfo

**Feature**: 609-mist-get-org-jse-info
**Spec**: [../spec.md](../spec.md)
**Plan**: [../plan.md](../plan.md)
**Source reference**: `documentation/api/orgs/GET_orgs_org_id_setting_jse_info.md`
**Date**: 2026-06-30

This document is the authoritative HTTP + SDK contract MistHelper's new menu method
must satisfy. All field names, types, status codes, and handling behaviors below are
grounded in the enriched per-endpoint reference and the live `mistapi` 0.59+ SDK.

---

## 1. HTTP contract

| Attribute | Value |
|-----------|-------|
| **Method**         | `GET` |
| **URL template**   | `https://{MIST_HOST}/api/v1/orgs/{org_id}/setting/jse/info` |
| **OperationId**    | `getOrgJseInfo` |
| **OpenAPI tag**    | `Orgs Integration JSE` |
| **Authentication** | `Authorization: Token {MIST_API_TOKEN}` header (or `X-CSRFToken` cookie for browser-session auth). MistHelper always uses token auth via `mistapi.APISession`. |
| **Pagination**     | None. The endpoint returns a single JSON object. |
| **Rate limiting**  | Standard Mist API limits (5,000 calls / hour / token). Adaptive back-off handled by MistHelper's `delay_metrics.json` + `tuning_data.json`. |

### Path parameters

| Name     | In   | Type   | Required | Validation                          | Description |
|----------|------|--------|----------|-------------------------------------|-------------|
| `org_id` | path | string | Yes      | Mist UUID regex (8-4-4-4-12 lowercase hex) | Target organization UUID. |

### Query parameters

None. The endpoint has zero query parameters.

### Request headers

| Header          | Required | Value                                |
|-----------------|----------|--------------------------------------|
| `Authorization` | Yes      | `Token {MIST_API_TOKEN}` (from `.env`) |
| `Accept`        | Yes      | `application/json` (set by SDK)      |
| `User-Agent`    | Yes      | Set by `mistapi` SDK (do not override) |

### Request body

None. (HTTP GET, body forbidden.)

---

## 2. Response contract -- 200 OK

Single JSON object. Schema (from the enriched docs file):

```json
{
  "type": "object",
  "properties": {
    "cloud_name": {
      "type": "string",
      "examples": ["devcentral.juniperclouds.net"]
    },
    "org_names": {
      "uniqueItems": true,
      "type": "array",
      "items": {"type": "string"}
    },
    "username": {
      "type": "string",
      "examples": ["john@abc.com"]
    }
  }
}
```

### Field semantics

| Field        | Type                   | Nullable | MistHelper persistence column        |
|--------------|------------------------|----------|--------------------------------------|
| `cloud_name` | string                 | Yes      | `org_jse_info.cloud_name` (TEXT)     |
| `org_names`  | array<string> (unique) | Yes      | Flattened to `org_jse_info.org_names` (sorted, comma-joined TEXT) plus `org_jse_info.org_names_count` (INTEGER) |
| `username`   | string                 | Yes      | `org_jse_info.username` (TEXT)       |

The caller-supplied `org_id` and the read-time `fetched_at` ISO 8601 UTC timestamp
are injected by the MistHelper method into the persistence row (they are not part of
the upstream response). See [../data-model.md](../data-model.md) for the full DDL.

### Example 200 payload

```json
{
  "cloud_name": "devcentral.juniperclouds.net",
  "org_names": ["acme-prod", "acme-lab"],
  "username": "ops@acme.com"
}
```

### Example MistHelper row after flatten

```json
{
  "org_id": "203d3d02-0000-0000-0000-000000000000",
  "cloud_name": "devcentral.juniperclouds.net",
  "org_names": "acme-lab,acme-prod",
  "org_names_count": 2,
  "username": "ops@acme.com",
  "fetched_at": "2026-06-30T19:12:34.567890+00:00"
}
```

---

## 3. Error responses and MistHelper handling

| Status | Meaning (per docs)                                   | MistHelper handling |
|--------|------------------------------------------------------|---------------------|
| `400`  | Bad Syntax                                           | Should never occur for a well-formed UUID; if encountered, log `ERROR` with the request id and exit the method (do not retry). |
| `401`  | Unauthorized -- token invalid or expired              | Log `ERROR` ("Mist API token rejected; check MIST_API_TOKEN in .env") and exit 1 from the menu method. The token is never echoed. |
| `403`  | Permission Denied -- token lacks read scope on org    | Log `ERROR` ("Token lacks read access to org %s for getOrgJseInfo") and return cleanly to the menu. |
| `404`  | Not found -- endpoint or resource does not exist      | Most commonly: JSE integration not configured for the org. Log `WARNING` ("getOrgJseInfo returned no payload for org %s (HTTP 404)") and return 0 -- this is the documented "Gotcha", not a defect. |
| `429`  | Too Many Requests -- 5,000 calls/hour cap hit         | Adaptive delay system (`delay_metrics.json` + `tuning_data.json`) increases inter-call back-off automatically; the method itself does not retry inline. The next invocation observes the new delay. |
| `5xx`  | Mist Cloud server error                              | Caught by the existing top-level menu exception handler; logged via `logging.exception` (full traceback, ASCII only) and the menu returns to the prompt loop. |

The MistHelper method only handles the JSE-specific cases (401/403/404/429) inline;
all generic transport errors bubble up to the global handler exactly as they do for
every other menu item in the Safe Org Exports cluster.

---

## 4. SDK call signature

Exact Python invocation MistHelper uses inside the new menu method:

```python
import mistapi                                                  # top-level SDK package

response = mistapi.api.v1.orgs.integration_jse.getOrgJseInfo(   # documented canonical SDK path
    self.apisession,                                            # APISession built from .env at startup
    org_id,                                                     # validated UUID from safe_input()
)
```

Notes:

1. The enriched documentation file lists the SDK module as
   `mistapi.api.v1.orgs.integration_jse`. The spec.md derived the alternative path
   `mistapi.api.v1.orgs.setting.jse.info` directly from the OpenAPI URL. The
   `/speckit.tasks` step confirms the actual import name against the installed
   `mistapi` 0.59+ wheel via
   `python -c "from mistapi.api.v1.orgs.integration_jse import getOrgJseInfo"` and
   uses whichever import succeeds. The Mist SDK convention groups by OpenAPI tag
   (`Orgs Integration JSE` -> `integration_jse`), so the docs-file path is the
   expected canonical form.
2. `self.apisession` is the existing `mistapi.APISession` instance built once at
   MistHelper startup from `MIST_HOST` and `MIST_API_TOKEN`. The menu method does
   not construct sessions of its own.
3. The SDK returns an `APIResponse` object. The JSON body is on `.data`; the HTTP
   status is on `.status_code`. The menu method reads `.data` only; status
   inspection is delegated to the existing global error handler unless inline
   handling is required (404 case above).
4. No keyword arguments are passed -- the endpoint has zero query parameters and
   the SDK function signature reflects that.

---

## 5. Idempotency and side effects

- **HTTP idempotency**: Yes (RFC 9110 -- GET is idempotent and safe).
- **Mist Cloud side effects**: None. The endpoint is strictly read.
- **MistHelper side effects**: Writes one row to `data/org_jse_info_<org_id>.csv`
  and one row (UPSERT) to the `org_jse_info` SQLite table per invocation. Repeated
  invocations for the same `org_id` overwrite the CSV and UPSERT the SQLite row in
  place -- no duplicates accumulate.

---

## 6. Related contracts

- `documentation/api/orgs/GET_orgs_org_id_setting_jse_setup.md` -- JSE integration
  setup (separate operationId; future spec).
- `documentation/api/sites/GET_sites_site_id_setting_jse_info.md` -- site-scoped
  counterpart (separate spec / menu item; do not conflate with this org-scoped
  endpoint).
- `documentation/api/orgs/GET_orgs_org_id_setting.md` -- full org settings (a
  superset that includes JSE config among many other fields; intentionally out of
  scope for this feature).
