# Contract: getOrgUiSetting

**Spec**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md) | **Date**: 2026-07-01

Source: `documentation/api/orgs/GET_orgs_org_id_uisettings_uisetting_id.md`.

## HTTP Contract

| Field            | Value                                                        |
|------------------|--------------------------------------------------------------|
| Method           | `GET`                                                        |
| URL template     | `https://{MIST_HOST}/api/v1/orgs/{org_id}/uisettings/{uisetting_id}` |
| Authentication   | `Authorization: Token {MIST_API_TOKEN}` header (loaded by `mistapi.APISession` from `.env`) |
| Content-Type     | `application/json` (response only; no request body)          |
| Idempotent       | Yes -- pure read                                             |
| Paginated        | No                                                           |

### Path Parameters

| Name           | Type   | Required | Description                                     |
|----------------|--------|----------|-------------------------------------------------|
| `org_id`       | string (UUID) | Yes | Target Mist organization UUID.             |
| `uisetting_id` | string (UUID) | Yes | Target databoard / UI-setting UUID.        |

### Query Parameters

None.

### Request Headers

Managed by `mistapi.APISession`. Do not construct manually.

| Header         | Value                                              |
|----------------|----------------------------------------------------|
| `Authorization`| `Token {MIST_API_TOKEN}`                           |
| `Accept`       | `application/json`                                 |
| `User-Agent`   | `mistapi-python/{version}` (mistapi SDK default)   |

### Request Body

None.

## Response

### 200 -- Success

Content-Type `application/json`. Single object matching the schema below. Only fields
observed in the enriched OpenAPI doc are listed; MistHelper flattens the top-level
into `org_ui_setting` and the `tiles[]` array into `org_ui_setting_tiles`.

```json
{
  "id": "53f10664-3ce8-4c27-b382-0ef66432349f",
  "org_id": "a97c1b22-a4e9-411e-9bfd-d8695a0f9e61",
  "site_id": "441a1214-6928-442a-8e92-e1d34b8ec6a6",
  "name": "AP Stats",
  "description": "This databoard shows AP stats",
  "purpose": "marvisdashboard",
  "for_site": false,
  "isCustomDataboard": true,
  "created_time": 1710000000.0,
  "modified_time": 1720000000.0,
  "tiles": [
    {
      "id": "53f10664-3ce8-4c27-b382-0ef66432349f",
      "name": "Top 10 APs by Bandwidth",
      "description": "This tile shows the top 10 APs by bandwidth",
      "nl_query": "List top 10 APs by bandwidth",
      "isAutoTitle": true,
      "position": {
        "col": 1,
        "row": 1,
        "colSpan": 5,
        "rowSpan": 2
      }
    }
  ]
}
```

### Field Reference (top level)

| Field               | Type    | Read-only | Notes                                       |
|---------------------|---------|-----------|---------------------------------------------|
| `id`                | UUID    | Yes       | Databoard UUID. Natural PK.                 |
| `org_id`            | UUID    | Yes       | Parent org.                                 |
| `site_id`           | UUID    | Yes       | Only present when `for_site` is true.       |
| `name`              | string  | No        | Display name.                               |
| `description`       | string  | No        | Free text.                                  |
| `purpose`           | string  | No        | Enum. Currently `marvisdashboard`.          |
| `for_site`          | boolean | Yes       | Whether the databoard is site-scoped.       |
| `isCustomDataboard` | boolean | No        | Whether the user created it.                |
| `created_time`      | number  | Yes       | Epoch seconds.                              |
| `modified_time`     | number  | Yes       | Epoch seconds.                              |
| `tiles`             | array   | No        | Ordered list; each entry flattened per row. |

### Field Reference (`tiles[]` element)

| Field         | Type    | Read-only | Notes                                            |
|---------------|---------|-----------|--------------------------------------------------|
| `id`          | UUID    | Yes       | Tile UUID. Natural PK.                           |
| `name`        | string  | No        | Tile display name.                               |
| `description` | string  | No        | Free text.                                       |
| `nl_query`    | string  | No        | Natural-language query text driving the tile.    |
| `isAutoTitle` | boolean | No        | Whether the title was auto-generated.            |
| `position`    | object  | No        | Grid coordinates; flattened to four INT columns. |
| `position.col`     | integer | No   | Grid column (int32).                             |
| `position.row`     | integer | No   | Grid row (int32).                                |
| `position.colSpan` | integer | No   | Column span (int32).                             |
| `position.rowSpan` | integer | No   | Row span (int32).                                |

## Error Responses and MistHelper Handling

| Status | Meaning                                                      | MistHelper Handling                                             |
|--------|--------------------------------------------------------------|-----------------------------------------------------------------|
| 400    | Bad Syntax -- malformed UUID or unexpected payload           | `logging.warning("Bad request for getOrgUiSetting: %s", ...)`; method returns without writing. |
| 401    | Unauthorized -- missing or invalid `MIST_API_TOKEN`          | `logging.error("Auth failure -- check MIST_API_TOKEN in .env")`; method returns; token never echoed. |
| 403    | Permission Denied -- token lacks read on this org/databoard  | `logging.warning("Permission denied on org %s uisetting %s", org_id, uisetting_id)`; method returns. |
| 404    | Not Found -- unknown `org_id` or `uisetting_id`              | `logging.warning("UI setting %s not found in org %s", uisetting_id, org_id)`; method returns; no traceback. |
| 429    | Too Many Requests -- 5000 calls/hour limit                   | Adaptive delay system (`delay_metrics.json` + `tuning_data.json`) backs off and retries; no manual handling in the menu method. |
| 5xx    | Upstream Mist API error                                      | `logging.exception("Upstream error calling getOrgUiSetting")`; method returns. |

All error branches follow the safety-first principle: no traceback surfaces to the
user, no secret is logged, and the method exits cleanly so the top-level menu loop
continues.

## mistapi Python Call Signature

```python
import mistapi
import mistapi.api.v1.orgs.ui_settings

# apisession is a module-level singleton built from .env values MIST_HOST and
# MIST_API_TOKEN at MistHelper startup.
response = mistapi.api.v1.orgs.ui_settings.getOrgUiSetting(
    apisession,           # mistapi.APISession -- shared auth + retry context
    org_id,               # str, UUID of the target organization
    uisetting_id,         # str, UUID of the target databoard / UI setting
)

# response is a mistapi.APIResponse.
# response.status_code -> int, HTTP status
# response.data        -> dict, the JSON body of the 200 response (see schema above)
# response.headers     -> dict, response headers
```

The SDK is the sole permitted interface to Mist Cloud per constitution
Technology & Compatibility Constraints. Do not build a raw `requests.get()` call.
