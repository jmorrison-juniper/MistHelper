# Data Model: Offline Device Report

**Date**: 2026-03-28

## Entities

### DeviceStats (API Response - from `listOrgDevicesStats`)

Source: Mist API `stats_ap` / `stats_switch` / `stats_gateway` response schemas.

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `id` | `str` (UUID) | API | Device unique ID |
| `name` | `str` | API | Device hostname/label |
| `mac` | `str` | API | MAC address |
| `serial` | `str` | API | Serial number |
| `model` | `str` | API | Hardware model (e.g., AP45, EX4100-48T) |
| `type` | `str` | API | `ap`, `switch`, or `gateway` |
| `status` | `str` | API | `connected` or `disconnected` |
| `last_seen` | `float` (epoch) | API | Unix timestamp of last check-in; 0 or null if never connected |
| `site_id` | `str` (UUID) | API | Site assignment UUID |

### SiteInfo (API Response - from `listOrgSites`)

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `id` | `str` (UUID) | API | Site unique ID |
| `name` | `str` | API | Human-readable site name |

### OfflineDeviceRecord (Derived - enriched for report output)

Constructed in-memory by joining DeviceStats with SiteInfo lookup.

| Field | Type | Derivation | Notes |
|-------|------|------------|-------|
| `Device Name` | `str` | `device["name"]` or `"(unnamed)"` | Display-friendly |
| `Device Type` | `str` | `device["type"]` capitalized | `AP`, `Switch`, `Gateway` |
| `Site Name` | `str` | `site_lookup[device["site_id"]]` | Resolved from lookup dict |
| `MAC Address` | `str` | `device["mac"]` | Raw MAC |
| `Serial Number` | `str` | `device["serial"]` | Raw serial |
| `Model` | `str` | `device["model"]` | Hardware model |
| `Last Seen` | `str` | Formatted from epoch | `YYYY-MM-DD HH:MM:SS` or `"Never Connected"` |
| `Offline Duration` | `str` | Computed from `now - last_seen` | `"3 days 12 hours"` or `"Never Connected"` |
| `Status` | `str` | `device["status"]` | Raw status value |

### Relationships

```text
DeviceStats.site_id --> SiteInfo.id  (many-to-one lookup)
DeviceStats + SiteInfo --> OfflineDeviceRecord  (enrichment join)
```

### Validation Rules

| Rule | Field | Constraint |
|------|-------|-----------|
| Threshold range | User input | 1 <= hours <= 8760 |
| Threshold type | User input | Must be numeric (int or float) |
| Never-connected handling | `last_seen` | If null, 0, or missing: treat as epoch 0 (always offline) |
| Name fallback | `name` | If null or empty: `"(unnamed)"` |
| Site fallback | `site_id` | If not in lookup: `"Unknown Site"` |

### State Transitions

This feature is stateless. No persistent state changes occur. The flow is:

```text
[User selects menu 158]
  --> [Prompt for threshold (default 48h)]
  --> [Fetch sites + device stats (2 API calls)]
  --> [Filter offline devices beyond threshold]
  --> [Sort by offline duration descending]
  --> [Display summary + table on screen]
  --> [Save CSV to data/ folder]
  --> [Return to menu]
```

## SQLite Strategy

Uses existing PK strategy from `ENDPOINT_PRIMARY_KEY_STRATEGIES`:

```python
"listOrgDevicesStats": {
    "type": "composite_pk",
    "primary_key": ["device_id", "timestamp"],
    "indexes": ["device_id", "timestamp", "org_id", "site_id", "type"],
}
```

The CSV path uses `api_function_name="listOrgDevicesStats"` for `DataExporter.write_with_format_selection()`.
