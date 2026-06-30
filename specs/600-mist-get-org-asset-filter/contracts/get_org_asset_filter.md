# Contract: GET /api/v1/orgs/{org_id}/assetfilters/{assetfilter_id}

**operationId**: `getOrgAssetFilter`
**Spec**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md)
**Source-of-truth doc**:
`documentation/api/orgs/GET_orgs_org_id_assetfilters_assetfilter_id.md`

## HTTP Contract

| Element        | Value                                                                |
|----------------|----------------------------------------------------------------------|
| Method         | `GET`                                                                |
| URL template   | `https://{MIST_HOST}/api/v1/orgs/{org_id}/assetfilters/{assetfilter_id}` |
| Auth           | `Authorization: Token {MIST_API_TOKEN}` header (or `X-CSRFToken` cookie when in a Mist UI session). |
| Content-Type   | n/a (request has no body).                                           |
| Idempotent     | Yes -- safe to retry on transient errors.                            |
| Paginated      | No -- single object response.                                        |

### Path parameters (both required)

| Name             | Type   | Format | Notes                                                  |
|------------------|--------|--------|--------------------------------------------------------|
| `org_id`         | string | UUID   | Mist organization ID. Supplied by user or `MIST_ORG_ID`. |
| `assetfilter_id` | string | UUID   | Mist asset-filter ID. Supplied by user (no env default). |

### Query parameters

None.

### Request headers (handled by `mistapi.APISession`)

- `Authorization: Token <MIST_API_TOKEN>`
- `Accept: application/json`
- `User-Agent: mistapi-python/<version>`

### Request body

None.

## 200 Success Response

The Mist API returns a single JSON object representing the Asset Filter. Field set
(per the OpenAPI schema, all optional except `name`):

```json
{
  "id":                       "53f10664-3ce8-4c27-b382-0ef66432349f",
  "org_id":                   "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61",
  "site_id":                  "441a1214-6928-442a-8e92-e1d34b8ec6a6",
  "name":                     "Visitor Tags",
  "disabled":                 false,
  "for_site":                 false,
  "ap_mac":                   "5c5b35000301",
  "beam":                     3,
  "rssi":                     -70,
  "mfg_company_id":           935,
  "service_uuid":             "0000fe6a-0000-1000-8000-0030459b3cfb",
  "ibeacon_uuid":             "f3f17139-704a-f03a-2786-0400279e37c3",
  "ibeacon_major":            1234,
  "eddystone_uid_namespace":  "2818e3868dec25629ede",
  "eddystone_url":            "https://www.abc.com",
  "created_time":             1717000000.0,
  "modified_time":            1717100000.0
}
```

Schema notes (verbatim from the source doc):

- `name` is the only **required** field.
- `id`, `org_id`, `site_id`, `for_site`, `created_time`, and `modified_time` are
  marked `readOnly` by Mist -- they are populated server-side and must not be sent
  back on a write.
- `ibeacon_uuid` and `ibeacon_major` are explicitly nullable.
- `ibeacon_major` has the constraint `1 <= value <= 65535`.
- Integer fields use `contentEncoding: int32`; epoch fields are `number` (float).

## Error Responses

| HTTP | Cause (Mist)                                | MistHelper handling                                                                                       |
|------|---------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| 400  | Bad Syntax (malformed UUID, etc.)            | Log `WARNING` with the offending parameter name; return early; do not retry.                              |
| 401  | Unauthorized (token missing / invalid)       | Log `ERROR` ("Mist API authentication failed -- check MIST_API_TOKEN in .env"); exit 1 from the menu loop.|
| 403  | Permission Denied (token lacks org scope)    | Log `ERROR` with the org_id (token is NEVER logged); return early; user fixes the token scope.            |
| 404  | Not Found (unknown org or asset filter)      | Log `WARNING` ("Asset filter %s not found in org %s", assetfilter_id, org_id); write nothing; exit 0.     |
| 429  | Too Many Requests (5000 calls/hour threshold)| Adaptive delay system in `delay_metrics.json` / `tuning_data.json` raises the back-off; mistapi retries.  |
| 5xx  | Mist Cloud upstream failure                  | Mistapi retries per its standard policy; on final failure log `logging.exception` with traceback.         |

No 200 response with an empty payload is documented for this endpoint; if mistapi
returns `None` (because the SDK normalised a 404), the export defaults to an empty
dict and `DataExporter` writes a zero-row update (no SQLite mutation).

## mistapi Python call signature

```python
import mistapi
from mistapi.api.v1.orgs import asset_filters as mist_asset_filters

# apisession is a long-lived mistapi.APISession constructed once from .env values.
response = mist_asset_filters.getOrgAssetFilter(
    apisession,                                  # mistapi.APISession instance
    org_id,                                      # str, UUID
    assetfilter_id,                              # str, UUID
)
record: dict = response.data or {}               # mistapi 0.59+ APIResponse.data
```

### Field-by-field mapping to SQLite columns

| API field                  | SQLite column            | Type      |
|----------------------------|--------------------------|-----------|
| `id`                       | `id` (PK)                | TEXT      |
| `org_id`                   | `org_id` (index)         | TEXT      |
| `site_id`                  | `site_id`                | TEXT NULL |
| `name`                     | `name` (NOT NULL, index) | TEXT      |
| `disabled`                 | `disabled`               | INTEGER   |
| `for_site`                 | `for_site`               | INTEGER   |
| `ap_mac`                   | `ap_mac`                 | TEXT      |
| `beam`                     | `beam`                   | INTEGER   |
| `rssi`                     | `rssi`                   | INTEGER   |
| `mfg_company_id`           | `mfg_company_id`         | INTEGER   |
| `service_uuid`             | `service_uuid`           | TEXT      |
| `ibeacon_uuid`             | `ibeacon_uuid`           | TEXT NULL |
| `ibeacon_major`            | `ibeacon_major`          | INTEGER NULL |
| `eddystone_uid_namespace`  | `eddystone_uid_namespace`| TEXT      |
| `eddystone_url`            | `eddystone_url`          | TEXT      |
| `created_time`             | `created_time`           | REAL      |
| `modified_time`            | `modified_time`          | REAL      |

The DataExporter call must use `api_function_name="getOrgAssetFilter"` so the PK
strategy registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES` is applied for the upsert.

## Related endpoints (out of scope for this spec)

- `GET /api/v1/orgs/{org_id}/assetfilters` (`getOrgAssetFilters`, list) -- separate
  spec when scheduled.
- `POST /api/v1/orgs/{org_id}/assetfilters` (create) -- write op, separate spec.
- `PUT /api/v1/orgs/{org_id}/assetfilters/{assetfilter_id}` (update) -- write op.
- `DELETE /api/v1/orgs/{org_id}/assetfilters/{assetfilter_id}` (delete) -- destructive
  op, lives in the 154-194 menu range when added.
