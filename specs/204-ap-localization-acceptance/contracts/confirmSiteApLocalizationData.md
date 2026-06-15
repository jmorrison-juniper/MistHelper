# Contract: `confirmSiteApLocalizationData`

**Module**: `mistapi.api.v1.sites.maps`  
**HTTP**: `POST /api/v1/sites/{site_id}/maps/{map_id}/use_auto_ap_values`  
**Mist API doc**: https://www.juniper.net/documentation/us/en/software/mist/api/http/api/sites/maps/auto-placement/confirm-site-ap-localization-data  
**mistapi version**: 0.63.0+

---

## Function Signature

```python
confirmSiteApLocalizationData(
    mist_session: mistapi.APISession,
    site_id: str,
    map_id: str,
    body: dict | list,
) -> mistapi.APIResponse
```

---

## Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `site_id` | UUID string | Yes | Site identifier |
| `map_id` | UUID string | Yes | Map identifier within the site |

---

## Request Body (`use_auto_ap_values`)

```json
{
  "accept": true,
  "for": "placement",
  "macs": ["aa:bb:cc:dd:ee:ff"]
}
```

| Field | Type | Required | Allowed Values | Description |
|-------|------|----------|----------------|-------------|
| `accept` | boolean | Yes | `true`, `false` | `true` = accept localization data; `false` = reject |
| `for` | string (enum) | Yes | `"placement"`, `"orientation"` | Selects placement or orientation localization data |
| `macs` | array of strings | No | AP MAC addresses | Scope to specific APs. Omit entirely for full-map scope. |

**Full-map scope example** (no `macs` field):

```json
{
  "accept": true,
  "for": "orientation"
}
```

---

## Responses

| Status | Body | Meaning |
|--------|------|---------|
| 200 | *(empty)* | Success — localization data accepted/rejected as requested |
| 400 | JSON error | Bad request — invalid parameters |
| 401 | JSON error | Unauthorized — session expired or invalid |
| 403 | JSON error | Forbidden — insufficient permissions |
| 404 | JSON error | Site or map not found |
| 429 | JSON error | Rate limited — retry after delay |

**Note**: A 200 response has an empty body. The caller must treat `status_code == 200`
as the sole success signal. Any non-200 status is a failure.

---

## MistHelper Usage Pattern

```python
import mistapi.api.v1.sites.maps as _maps_api

body = {
    "accept": True,                    # True = accept, False = reject
    "for": "placement",                # "placement" or "orientation"
    "macs": ["aa:bb:cc:dd:ee:ff"],     # omit for full-map scope
}
response = _maps_api.confirmSiteApLocalizationData(
    apisession, site_id, map_id, body
)
status = getattr(response, "status_code", "n/a")
success = (status == 200)
```

---

## Error Handling

Wrap in try/except to catch network errors and API errors:

```python
try:
    response = _maps_api.confirmSiteApLocalizationData(apisession, site_id, map_id, body)
    status = getattr(response, "status_code", "n/a")
except Exception as api_error:
    status = "n/a"
    logging.error("confirmSiteApLocalizationData failed: %s", api_error)
```

---

## Idempotency Note

The Mist API does not document this endpoint as idempotent. Submitting
the same acceptance request twice in a single session is treated as a
duplicate. The MistHelper audit record captures the outcome of each
individual call so operators can identify duplicate submissions.
