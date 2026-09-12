# Quickstart: E911 BSSID Compliance Report

**Feature**: 182-e911-bssid-report
**Date**: 2026-04-07

## What This Feature Does

Menu 160 generates a CSV report listing every BSSID (Basic Service Set Identifier)
across all AP radios in the Mist organization, enriched with site name, site address,
floor/map name, and AP name. This report is used for E911 compliance filing.

## How to Run

```bash
# Interactive menu
python MistHelper.py
# Select option 160

# Direct invocation
python MistHelper.py --menu 160

# Automated test mode
python MistHelper.py --test  # Menu 160 runs automatically (safe category)
```

## Output

**CSV file**: `data/E911_BSSID_Report_YYYYMMDD_HHMMSS.csv`

| Site Name | Site Address | Map Name | AP Name | BSSID |
| - | - | - | - | - |
| Building A | 123 Main St | Floor 1 | AP-Lobby-01 | 5c:5b:35:00:00:40 |
| Building A | 123 Main St | Floor 1 | AP-Lobby-01 | 5c:5b:35:00:00:41 |
| ... | ... | ... | ... | ... |

Rows are sorted by Site Name, then Map Name, then AP Name, then BSSID.

**On-screen summary**:

```text
--- E911 BSSID Compliance Report ---
  Sites processed: 42
  APs processed: 1,250
  BSSIDs generated: 60,000

--- Compliance Gaps ---
  APs without floor/map assignment: 3
    - AP-Storage-01 (Site: Building B)
    - AP-Temp-02 (Site: Building C)
    - AP-Unknown-03 (Site: Unassigned)
```

## API Calls Made

1. `listOrgApsMacs` — All AP radio base MACs (E911 endpoint)
2. `listOrgSites` — Site names and addresses
3. `listOrgDevicesStats` (type=ap) — AP names, site/map assignments
4. `listSiteMaps` — Map names (per site with APs)

## Key Design Decisions

- Uses Mist's purpose-built E911 endpoint (`radio_macs`) rather than parsing `radio_stat` from device stats
- Pre-fetches all lookup data before processing (no per-device API calls)
- 16 BSSIDs per radio MAC derived by enumerating last nibble 0x0-0xF
- APs without map assignment flagged as compliance gaps (not excluded)
- Colon-separated BSSID format for E911 system compatibility
