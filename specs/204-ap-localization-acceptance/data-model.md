# Data Model: AP Localization Acceptance (Menu 204)

## Entities

### 1. `LocalizationAcceptanceRequest`

*Runtime value object — collects and validates operator inputs before execution.*

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `site_id` | str | Yes | Non-empty, stripped; UUID format recommended but not enforced at input layer |
| `map_id` | str | Yes | Non-empty, stripped |
| `for_type` | str | Yes | Must be `"placement"` or `"orientation"` (case-insensitive normalised to lower) |
| `accept` | bool | Yes | Derived from operator choice; never defaults |
| `macs` | list[str] | No | Empty list → full-map scope; each entry stripped, no format enforcement (API validates) |

**Validation rules**:
- `site_id` empty → block execution, prompt to retry
- `map_id` empty → block execution, prompt to retry
- `for_type` not in `{"placement", "orientation"}` → block execution, prompt to retry
- `accept` must be explicitly set by operator choice (no silent default)

**State transitions**:
```
INPUTS_PENDING → INPUTS_VALID → AWAITING_CONFIRMATION → CONFIRMED → EXECUTING → COMPLETE
                              ↘                        ↘
                               VALIDATION_FAILED        CONFIRMATION_FAILED
                               (cancelled)              (cancelled)
```

---

### 2. `LocalizationAcceptanceResult`

*Outcome payload of an attempted acceptance action.*

| Field | Type | Source |
|-------|------|--------|
| `http_status` | int or `"n/a"` | `response.status_code` or exception path |
| `success` | bool | `http_status == 200` |
| `error_detail` | str | Exception message or `""` on success |

---

### 3. `LocalizationAcceptanceAuditRecord`

*Exportable audit artifact written by `DataExporter.write_with_format_selection`.*  
*Exported to `confirmSiteApLocalizationData` table/file.*

| Field | Type | Notes |
|-------|------|-------|
| `timestamp` | str (ISO 8601 UTC) | `datetime.utcnow().isoformat()` |
| `menu_operation` | str | `"204"` (literal, for audit filtering) |
| `site_id` | str | From `LocalizationAcceptanceRequest` |
| `map_id` | str | From `LocalizationAcceptanceRequest` |
| `for_type` | str | `"placement"` or `"orientation"` |
| `action` | str | `"accept"` or `"reject"` |
| `macs_scope` | str | Comma-joined MACs or `"full_map"` if empty list |
| `http_status` | str | Response status code or `"n/a"` |
| `outcome` | str | `"executed"` or `"cancelled"` |
| `cancel_reason` | str | `"validation_failed"`, `"confirmation_failed"`, or `""` |

**Primary key strategy**: `auto_increment_with_unique`  
**Unique constraint**: `(timestamp, site_id, map_id, for_type, action)`  
**SQLite table name**: `confirmSiteApLocalizationData`  
**CSV filename**: `confirmSiteApLocalizationData_{timestamp}.csv`

---

## Relationships

```
LocalizationAcceptanceRequest ──creates──► LocalizationAcceptanceResult
LocalizationAcceptanceRequest + LocalizationAcceptanceResult ──produces──► LocalizationAcceptanceAuditRecord
```

---

## `ENDPOINT_PRIMARY_KEY_STRATEGIES` Entry

```python
'confirmSiteApLocalizationData': {
    'type': 'auto_increment_with_unique',
    'primary_key': ['misthelper_internal_id'],
    'unique_constraints': ['timestamp', 'site_id', 'map_id', 'for_type', 'action'],
    'description': 'AP localization acceptance audit records - action-level, no stable UUID returned by API'
},
```

This entry is added to the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dict in `MistHelper.py`
alongside the existing auto-increment entries (e.g., `getOrgLicensesSummary`).
