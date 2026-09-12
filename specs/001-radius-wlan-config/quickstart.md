# Quickstart: Bulk RADIUS WLAN Configuration (Menu 122)

**Feature**: 001-radius-wlan-config
**Date**: 2026-03-03

## Overview

Menu 122 allows NOC engineers to configure RADIUS authentication timing settings across all WLANs in an organization with a single operation.

## Prerequisites

1. MistHelper authenticated with a valid API session
2. API token with WLAN write permissions
3. Organization context set (auto-prompted if not cached)

## Configuration (Optional)

Add to `.env` to customize target values:

```bash
# RADIUS WLAN Bulk Configuration Defaults
RADIUS_AUTH_TIMEOUT=3      # Seconds (1-30), default: 3
RADIUS_AUTH_RETRIES=2      # Count (0-10), default: 2
RADIUS_FAST_DOT1X=true     # true/false, default: true
```

## Usage

### Interactive Mode

```bash
python MistHelper.py
# Select menu option 122
```

### Direct Invocation

```bash
python MistHelper.py --menu 122
```

## Workflow

1. **Startup**: Displays loaded `.env` values

   ```
   RADIUS Configuration:
     auth_servers_timeout: 3 seconds
     auth_servers_retries: 2
     fast_dot1x_timers: true
   ```

2. **Scan**: Lists all RADIUS-enabled WLANs in the organization

   ```
   Found 15 RADIUS WLANs:
   [1] Corp-WiFi (Site: HQ-Building-A, Level: site)
   [2] Guest-Secure (Site: HQ-Building-A, Level: org_wlan_with_template)
   [3] IoT-Enterprise (Site: Branch-01, Level: site_template)
   ...
   ```

3. **Select**: Enter WLANs to configure

   ```
   Select WLANs (all, 1, 1-5, 1,3,5-10): all
   ```

4. **Preview**: Shows current vs target values

   ```
   Changes to apply:
   - Corp-WiFi: timeout 5->3, retries 3->2, fast_dot1x false->true
   - Guest-Secure: timeout 5->3, retries 2->2, fast_dot1x false->true
   - IoT-Enterprise: (no changes - already configured)
   ```

5. **Confirm**: Requires explicit "APPLY" confirmation

   ```
   Type 'APPLY' to proceed: APPLY
   ```

6. **Apply**: Updates each WLAN, shows progress

7. **Export**: Saves audit trail to `data/RadiusWLANBulkConfig_YYYYMMDD_HHMMSS.csv`

## Selection Syntax

| Input | Effect |
|-------|--------|
| `all` | Select all listed WLANs |
| `3` | Select only WLAN #3 |
| `1,3,5` | Select WLANs #1, #3, and #5 |
| `1-5` | Select WLANs #1 through #5 |
| `1,3,5-10,15` | Select #1, #3, #5-#10, and #15 |

## Output Files

| File | Location | Purpose |
|------|----------|---------|
| Audit CSV | `data/RadiusWLANBulkConfig_YYYYMMDD_HHMMSS.csv` | Before/after change record |

## Related Operations

- **Menu 102**: Site-level RADIUS timer management (individual WLAN selection)
- **Menu 48**: Export WLAN configuration for organization (read-only)
