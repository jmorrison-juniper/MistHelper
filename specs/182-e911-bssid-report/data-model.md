# Data Model: E911 BSSID Compliance Report

**Feature**: 182-e911-bssid-report
**Date**: 2026-04-07

## Entities

### APRadioMacs (from `listOrgApsMacs`)

| Field | Type | Source | Description |
| - | - | - | - |
| mac | string | API | AP base MAC address (e.g., `5c5b35000001`) |
| radio_macs | list[string] | API | Radio base MACs (e.g., `["5c5b35000040", "5c5b35000050"]`) |

### APDeviceInfo (from `listOrgDevicesStats`, type=ap)

| Field | Type | Source | Description |
| - | - | - | - |
| mac | string | API | AP base MAC (join key to APRadioMacs) |
| name | string | API | AP display name |
| site_id | string (uuid) | API | Site assignment |
| map_id | string (uuid) or null | API | Map/floor assignment (null = unassigned) |

### Site (from `listOrgSites`)

| Field | Type | Source | Description |
| - | - | - | - |
| id | string (uuid) | API | Site unique ID (join key) |
| name | string | API | Site display name |
| address | string or empty | API | Physical address |

### Map (from `listSiteMaps`)

| Field | Type | Source | Description |
| - | - | - | - |
| id | string (uuid) | API | Map unique ID (join key) |
| name | string | API | Map/floor display name |
| site_id | string (uuid) | API | Parent site |

### BSSID (derived)

| Field | Type | Source | Description |
| - | - | - | - |
| bssid | string | Computed | Colon-separated MAC (e.g., `5c:5b:35:00:00:40`) |
| radio_base_mac | string | APRadioMacs.radio_macs | Source radio base MAC |
| ap_mac | string | APRadioMacs.mac | Parent AP base MAC |

## Relationships

```text
Site (1) ──── (*) Map
Site (1) ──── (*) APDeviceInfo
APDeviceInfo (*) ──── (0..1) Map
APDeviceInfo (1) ──── (1) APRadioMacs [join on mac]
APRadioMacs (1) ──── (2..3) radio_macs
radio_mac (1) ──── (16) BSSID [derived by nibble enumeration]
```

## Lookup Dictionaries (In-Memory)

1. **site_lookup**: `dict[str, dict[str, str]]` — `{site_id: {"name": str, "address": str}}`
2. **ap_lookup**: `dict[str, dict[str, str]]` — `{ap_mac: {"name": str, "site_id": str, "map_id": str}}`
3. **map_lookup**: `dict[str, str]` — `{map_id: map_name}`

## Output Schema (CSV Row)

| Column | Type | Source | Sort Order |
| - | - | - | - |
| Site Name | string | site_lookup[site_id]["name"] | Primary (ascending) |
| Site Address | string | site_lookup[site_id]["address"] | — |
| Map Name | string | map_lookup[map_id] or "Unassigned" | Secondary (ascending) |
| AP Name | string | ap_lookup[mac]["name"] | Tertiary (ascending) |
| BSSID | string | Derived (colon-separated) | Quaternary (ascending) |

## SQLite Primary Key Strategy

```python
"generateE911BSSIDReport": {
    "type": "natural_pk",
    "primary_key": ["bssid"],
    "indexes": ["site_name", "ap_name", "map_name"],
    "unique_constraints": [],
    "description": "E911 BSSID compliance report - one row per BSSID with location context",
}
```

## BSSID Derivation Algorithm

```text
Input:  radio_base_mac = "5c5b35000040" (12 hex chars, no separators)
Output: 16 BSSIDs

Step 1: Parse base as integer
  base_int = int("5c5b35000040", 16)  # = 101597241565248

Step 2: Enumerate last nibble (0x0 through 0xF)
  for offset in range(16):
    bssid_int = (base_int & 0xFFFFFFFFFFF0) | offset
    bssid_hex = format(bssid_int, '012x')
    bssid_formatted = ":".join(bssid_hex[i:i+2] for i in range(0, 12, 2))
    # Yields: "5c:5b:35:00:00:40" through "5c:5b:35:00:00:4f"
```

## Compliance Gap Tracking

| Gap Type | Detection | Display |
| - | - | - |
| AP without map | `ap_lookup[mac]["map_id"]` is null/empty | Map Name = "Unassigned" |
| AP without site | `ap_lookup[mac]["site_id"]` is null/empty | Site Name = "Unassigned", Site Address = "", Map Name = "Unassigned" |
| AP in radio_macs but not in device stats | mac not in ap_lookup | AP Name = "Unknown", flagged as data discrepancy |
| map_id not found in map_lookup | map_id not in map_lookup | Map Name = "Unknown Map" |
