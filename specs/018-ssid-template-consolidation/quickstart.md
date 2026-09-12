# Quickstart: SSID Template Consolidation

**Feature Branch**: `018-ssid-template-consolidation`
**Date**: 2025-07-02

---

## What This Feature Does

Consolidates ~170 per-site WLAN templates down to 5 shared templates using Mist site variables, site groups, and a guided 5-phase workflow. Each phase shows exactly what will change and requires explicit confirmation before any modifications.

## Prerequisites

1. MistHelper is running and authenticated to the Mist organization
2. The `.env` file has `MIST_ORG_ID` or `ORG_ID` set
3. Optionally, set `MIST_TARGET_SSID=CorpSecure` in `.env` for a default target SSID

## Running the Workflow

1. Select **menu option 159** from the main menu
2. At the SSID prompt, press Enter to accept the default or type a different SSID name
3. Select a phase (1-5) or "A" to run all phases sequentially

### Phase Guide

| Phase | What It Does | Modifies Mist? | Typical Duration |
|-------|-------------|-----------------|------------------|
| 1 — Discover & Audit | Collects all template/SSID data, generates matrix report | No (read-only) | 1-3 minutes |
| 2 — Site Variables | Writes site-specific values (VLAN, Edge cluster) to each site | Yes | 3-5 minutes |
| 3 — Site Groups | Creates 5 groups and assigns sites by Edge cluster | Yes | < 1 minute |
| 4 — Create Templates | Creates 5 consolidated templates with the target SSID | Yes | < 1 minute |
| 5 — Disable Old SSIDs | Disables the matching SSID in all old per-site templates | Yes | 3-5 minutes |

### Running for Both SSIDs

The workflow targets one SSID at a time. To consolidate both the secured and open/guest SSIDs:

1. Run phases 1-5 with `MIST_TARGET_SSID=CorpSecure` (or enter "CorpSecure" at the prompt)
2. Run phases 1-5 again with target SSID set to `GuestOpen` (or whatever the open SSID is named)

Phase 4 detects existing templates from the first run and appends the second SSID without disturbing the first.

## Output Files

All output is saved to the `data/` directory:

- `ssid_consol_phase1_matrix_{ssid}.csv` — Full site audit matrix
- `ssid_consol_phase1_deviations_{ssid}.csv` — Settings deviation analysis
- `ssid_consol_results_phase{N}_{ssid}.csv` — Per-phase operation results

## Key Safety Features

- **Read-only Phase 1**: No changes are made during the audit phase
- **PSK sites excluded**: Sites using PSK authentication are automatically skipped
- **Anomaly detection**: Templates with unusual SSID counts are flagged and excluded
- **Typed confirmation**: Every modification phase requires typing "CONFIRM" before proceeding
- **Idempotent operations**: Re-running any phase does not create duplicates
- **Resumable**: If interrupted, re-running a phase detects completed sites and offers to resume

## For Developers

### Class Structure

```
SSIDTemplateConsolidationManager (main orchestrator)
  ├── SSIDConsolidationDataCollector    (Phase 1)
  ├── SSIDConsolidationVariableWriter   (Phase 2)
  ├── SSIDConsolidationGroupAssigner    (Phase 3)
  ├── SSIDConsolidationTemplateCreator  (Phase 4)
  └── SSIDConsolidationDisabler         (Phase 5)
```

### Adding Primary Key Strategies

Before implementing, add entries to `ENDPOINT_PRIMARY_KEY_STRATEGIES` for:
- `listOrgTemplates` — natural_pk on `id`
- `listOrgSiteGroups` — natural_pk on `id`
- `ssidConsolidationMatrix` — natural_pk on `site_id`
- `ssidConsolidationResults` — composite_pk on `site_id` + `phase_number`
