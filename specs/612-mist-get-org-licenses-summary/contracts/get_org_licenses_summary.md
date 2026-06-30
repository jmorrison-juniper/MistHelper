# Contract: getOrgLicensesSummary

**Spec**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md) | **Source doc**: `documentation/api/orgs/GET_orgs_org_id_licenses.md`

## HTTP

| Field | Value |
|-------|-------|
| Method | `GET` |
| URL template | `https://{MIST_HOST}/api/v1/orgs/{org_id}/licenses` |
| Auth | `Authorization: Token {MIST_API_TOKEN}` header (or `X-CSRFToken` cookie) |
| Content-Type (request) | n/a (no body) |
| Accept (response) | `application/json` |
| Pagination | None. Single full response. |
| Idempotency | Safe, idempotent, read-only. |

### Path parameters

| Name | Type | Required | Source | Description |
|------|------|----------|--------|-------------|
| `org_id` | UUID string | Yes | `safe_input()` prompt, falling back to `MIST_ORG_ID` from `.env` | The org whose license summary is being read. |

### Query parameters

_None._ The endpoint accepts no query parameters.

### Request headers

| Header | Value | Source |
|--------|-------|--------|
| `Authorization` | `Token <MIST_API_TOKEN>` | Loaded by `mistapi.APISession` from `.env`; never logged. |
| `Accept` | `application/json` | Set by `mistapi` SDK. |

### Request body

_None._

## Response (200 OK)

Top-level shape (full schema in `documentation/api/orgs/GET_orgs_org_id_licenses.md`):

```json
{
  "amendments": [
    {
      "id": "53f10664-3ce8-4c27-b382-0ef66432349f",
      "subscription_id": "SUB-...",
      "type": "SUB-MAN",
      "quantity": 10,
      "start_time": 1717200000,
      "end_time": 1748736000,
      "created_time": 1717200000.0,
      "modified_time": 1717200000.0
    }
  ],
  "entitled":      { "SUB-MAN": 100, "SUB-VNA": 25 },
  "fully_loaded":  { "SUB-MAN": 150, "SUB-VNA": 30 },
  "summary":       { "SUB-MAN": 80,  "SUB-VNA": 12 },
  "usages":        { "SUB-MAN": 20,  "SUB-VNA": 13 },
  "licenses": [
    {
      "id": "53f10664-3ce8-4c27-b382-0ef66432349f",
      "org_id": "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61",
      "type": "SUB-MAN",
      "subscription_id": "SUB-...",
      "order_id": "ORD-...",
      "quantity": 100,
      "remaining_quantity": 20,
      "start_time": 1700000000,
      "end_time": 1731536000,
      "created_time": 1700000000.0,
      "modified_time": 1700000000.0
    }
  ]
}
```

### Field reference

| Path | Type | Description |
|------|------|-------------|
| `amendments[]` | array of `license_amendment` | Adjustments applied to a subscription. Each item carries a stable UUID. |
| `amendments[].id` | UUID string | Amendment identifier (natural PK for `org_licenses_amendments`). |
| `amendments[].subscription_id` | string | The subscription the amendment modifies. |
| `amendments[].type` | string | License type code being amended. |
| `amendments[].quantity` | int32 | Quantity delta from the amendment. |
| `amendments[].start_time` | int32 (epoch s) | Amendment term start. |
| `amendments[].end_time` | int32 (epoch s) | Amendment term end. |
| `amendments[].created_time` | number (epoch s) | When Mist created the amendment. |
| `amendments[].modified_time` | number (epoch s) | Last modification time. |
| `entitled` | map[string, int32] | Total licenses entitled per license type. Source for `org_licenses_usage_counts` with `metric='entitled'`. |
| `fully_loaded` | map[string, int32] | Maximum licenses needed if the service were enabled on all org devices. Source for `org_licenses_usage_counts` with `metric='fully_loaded'`. |
| `summary` | map[string, int32] | Currently consumed licenses per type. Source for `org_licenses_summary_counts.consumed_count`. |
| `usages` | map[string, int32] | Available licenses per type. Source for `org_licenses_usage_counts` with `metric='usages'`. |
| `licenses[]` | array of `license_sub` | Active subscription records. Each item carries a stable UUID. |
| `licenses[].id` | UUID string | Subscription identifier (natural PK for `org_licenses_subscriptions`). |
| `licenses[].org_id` | UUID string | Owning org UUID. |
| `licenses[].type` | string | License type code (e.g. `SUB-MAN`). |
| `licenses[].subscription_id` | string | External subscription identifier. |
| `licenses[].order_id` | string | External order identifier. |
| `licenses[].quantity` | int32 | Total devices entitled under this subscription. |
| `licenses[].remaining_quantity` | int32 | Unconsumed devices on this subscription. |
| `licenses[].start_time` | int32 (epoch s) | License term start. |
| `licenses[].end_time` | int32 (epoch s) | License term end. |
| `licenses[].created_time` | number (epoch s) | When Mist created the subscription record. |
| `licenses[].modified_time` | number (epoch s) | Last modification time. |

All response fields are `readOnly: true` per the OpenAPI schema. No POST/PUT/PATCH/DELETE counterparts are invoked by this menu item.

## Error responses

| Status | Meaning | MistHelper handling |
|--------|---------|---------------------|
| 400 | Bad Syntax (malformed `org_id` shape rejected by the API) | UUID is validated locally before the call; if the API still returns 400, log `ERROR` with the request URL pattern (no token) via `logging.exception` and return without writing any output. |
| 401 | Unauthorized (invalid or expired API token) | Log `ERROR "Mist API rejected the token (401). Refresh MIST_API_TOKEN in .env."` and return. Do not log the token. |
| 403 | Permission Denied (token lacks read-licenses scope for this org) | Log `WARNING "Token has no license read scope for org %s"` and return. |
| 404 | Not Found (org UUID is well-formed but does not exist for this token) | Log `WARNING "Org %s not found"` and return. No traceback. |
| 429 | Too Many Requests (rate limit of 5000 calls/hour exceeded) | Adaptive delay system (`delay_metrics.json` + `tuning_data.json`) records the throttle, applies exponential back-off, and retries. The menu method itself does not implement custom retry logic. |
| 5xx | Mist Cloud server error | Log `ERROR` via `logging.exception` (includes traceback) and return. The user is told to rerun later. |

## mistapi SDK call

### Module path

`mistapi.api.v1.orgs.licenses.getOrgLicensesSummary`

### Python signature

```python
# Signature exposed by mistapi 0.59+
def getOrgLicensesSummary(
    mist_session: mistapi.APISession,         # authenticated session loaded from .env
    org_id: str,                              # required path parameter; UUID string
) -> mistapi.APIResponse:                     # .data carries the JSON dict described above
    ...
```

### Invocation pattern used in the menu method

```python
# Exact call site in LicenseExportUtils.export_org_licenses_summary
resp = mistapi.api.v1.orgs.licenses.getOrgLicensesSummary(           # sole permitted SDK entry
    self.apisession,                                                 # APISession loaded at startup
    org_id,                                                          # validated UUID from safe_input()
)
body = resp.data or {}                                               # SDK wraps the JSON body in .data
```

### Response object

`mistapi.APIResponse` exposes:

| Attribute | Type | Notes |
|-----------|------|-------|
| `.data` | dict | The parsed JSON object documented above. May be `{}` for empty orgs. |
| `.status_code` | int | HTTP status. The SDK raises for transport-level errors; HTTP error statuses surface via `.status_code` and `.data`. |
| `.url` | str | Final URL after host resolution. **Not logged.** |
| `.next` | str \| None | Always `None` for this endpoint (non-paginated). |

## Side effects

- One CSV / SQLite write per row set (four total) via
  `DataExporter.write_with_format_selection(..., api_function_name="getOrgLicensesSummary")`.
- One pair of action log lines (`INFO` before, `DEBUG` after) per phase:
  prompt, API call, flatten, and each of the four writes.
- No mutation of Mist Cloud state. No file writes outside `data/`. No state
  written back to `.env`.
