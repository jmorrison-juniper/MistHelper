# Data Model: Bulk RADIUS WLAN Configuration

**Feature**: 001-radius-wlan-config
**Date**: 2026-03-03

## Entities

### WLANConfig (Runtime)

Represents a WLAN's RADIUS authentication configuration as retrieved from the Mist API.

| Field | Type | Description |
|-------|------|-------------|
| id | str | Mist WLAN UUID |
| ssid | str | WLAN name (displayed to user) |
| site_id | str | Associated site UUID (may be None for org-level) |
| site_name | str | Human-readable site name |
| template_id | str | WLAN template UUID if template-managed |
| inheritance_level | str | "site" \| "site_template" \| "org_wlan_with_template" |
| auth_servers_timeout | int | Current timeout value (seconds, default: 5) |
| auth_servers_retries | int | Current retry count (default: 2) |
| fast_dot1x_timers | bool | Current fast 802.1X timer setting |

**Source**: `mistapi.api.v1.orgs.wlans.listOrgWlans` response

### TargetConfig (Configuration)

Target values loaded from `.env` file at runtime.

| Field | Type | Default | Env Variable |
|-------|------|---------|--------------|
| timeout | int | 3 | `RADIUS_AUTH_TIMEOUT` |
| retries | int | 2 | `RADIUS_AUTH_RETRIES` |
| fast_dot1x | bool | true | `RADIUS_FAST_DOT1X` |

### ChangeRecord (Audit)

Before/after snapshot for CSV export.

| Field | Type | Description |
|-------|------|-------------|
| wlan_id | str | WLAN UUID |
| ssid | str | WLAN SSID name |
| site_name | str | Site name (or "Org-Level") |
| inheritance_level | str | Where WLAN is defined |
| before_timeout | int | Previous timeout value |
| after_timeout | int | New timeout value |
| before_retries | int | Previous retries value |
| after_retries | int | New retries value |
| before_fast_dot1x | bool | Previous fast timer setting |
| after_fast_dot1x | bool | New fast timer setting |
| status | str | "success" \| "skipped" \| "failed" |
| error_message | str | Error details if status is "failed" |
| timestamp | str | ISO 8601 timestamp |

**Output**: `data/RadiusWLANBulkConfig_YYYYMMDD_HHMMSS.csv`

## Relationships

```
TargetConfig (1) ─────applies─to────> (*) WLANConfig
     │                                      │
     │                                      │
     └──────────produces───────> (*) ChangeRecord
```

## Validation Rules

1. **WLANConfig**: Only WLANs passing RADIUS detection filter are included
2. **TargetConfig.timeout**: Must be 1-30 seconds (per Mist API constraints)
3. **TargetConfig.retries**: Must be 0-10 (per Mist API constraints)
4. **Selection input**: Must resolve to valid indices (1-based) within WLAN list

## State Transitions

```
[Start] -> Scan -> Filter -> Display -> Select -> Preview -> Confirm -> Apply -> Export -> [End]
                     │                    │         │          │
                     v                    v         v          v
                  (no matches)      (cancel)   (cancel)    (partial fail)
                     │                    │         │          │
                     v                    v         v          v
                 [Graceful Exit]      [Exit]    [Exit]    [Continue + Report]
```
