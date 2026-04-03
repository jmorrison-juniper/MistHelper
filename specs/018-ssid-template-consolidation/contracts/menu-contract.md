# Menu Contract: SSID Template Consolidation

**Feature Branch**: `018-ssid-template-consolidation`
**Date**: 2025-07-02
**Type**: CLI Menu Interface

---

## Menu Registration

**Menu Number**: `159`
**Menu Description**: `"SSID Template Consolidation (5-Phase Workflow)"`
**Handler**: `SSIDTemplateConsolidationManager().manage`

```python
# In menu_actions dictionary
"159": (lambda: SSIDTemplateConsolidationManager().manage(), 
        "SSID Template Consolidation (5-Phase Workflow)")
```

---

## User Flow

### Entry Point (Menu 159)

```text
==================================================================
  SSID Template Consolidation Workflow
==================================================================

  This workflow consolidates ~170 per-site WLAN templates into
  5 shared templates using site variables and site groups.

  It runs in 5 sequential phases. Each modification phase shows
  you exactly what will change and asks you to type CONFIRM
  before any changes are made.

------------------------------------------------------------------
  Target SSID Configuration
------------------------------------------------------------------

  Target SSID [CorpSecure]: _

  (Press Enter to use the default, or type a different SSID name)
```

### Phase Selection Sub-Menu

```text
------------------------------------------------------------------
  Phase Selection
------------------------------------------------------------------

  Using target SSID: CorpSecure

  1. Phase 1 — Discover & Audit (read-only, generates matrix report)
  2. Phase 2 — Configure Site Variables (writes vars to site settings)
  3. Phase 3 — Organize Site Groups (assigns sites to 5 groups)
  4. Phase 4 — Create Consolidated Templates (creates/updates 5 templates)
  5. Phase 5 — Disable Old SSIDs (disables matching SSIDs in old templates)
  A. Run All Phases Sequentially (1 → 2 → 3 → 4 → 5)
  Q. Return to Main Menu

  Select phase [1-5, A, Q]: _
```

### Confirmation Pattern (Phases 2-5)

```text
------------------------------------------------------------------
  Phase 2 — Site Variable Configuration
------------------------------------------------------------------

  Summary of planned changes:

  Site: Building-A-Floor1
    SSID_CONSOL_VLAN_ID:      100 (new)
    SSID_CONSOL_MXTUNNEL:     cluster-east (new)

  Site: Building-B-Floor2
    SSID_CONSOL_VLAN_ID:      200 (current: 150 — OVERRIDE)
    SSID_CONSOL_MXTUNNEL:     cluster-west (new)

  [... more sites ...]

  Sites to modify:  168
  Sites skipped:      2 (PSK)

  Type 'CONFIRM' to apply these changes: _
```

### Results Log Output

```text
------------------------------------------------------------------
  Phase 2 Results
------------------------------------------------------------------

  [OK]   Building-A-Floor1 — 2 variables written
  [OK]   Building-B-Floor2 — 2 variables written
  [SKIP] Building-C-Lobby  — PSK site, excluded
  [FAIL] Building-D-Floor3 — API error: 429 Too Many Requests (will retry)
  [OK]   Building-D-Floor3 — 2 variables written (retry 1/3)

  Summary: 167 success, 1 skipped, 0 failed
  Results saved to: data/ssid_consol_results_phase2_CorpSecure.csv

  Press Enter to continue...
```

---

## .env Configuration

```bash
# Target SSID for consolidation workflow (default value for prompt)
MIST_TARGET_SSID=CorpSecure

# Existing variables used by the workflow:
# MIST_ORG_ID or ORG_ID — Organization ID
# CSV_FRESHNESS_MINUTES — Cache freshness window
# API_REQUEST_MAX_RETRIES — Retry count for failed API calls
# API_REQUEST_RETRY_DELAY — Base delay between retries
```

---

## Output Files

All files are written to the `data/` directory:

| File | Format | Phase | Description |
|------|--------|-------|-------------|
| `ssid_consol_phase1_matrix_{ssid}.csv` | CSV | 1 | Full site matrix report |
| `ssid_consol_phase1_deviations_{ssid}.csv` | CSV | 1 | Per-cluster deviation analysis |
| `ssid_consol_phase1_cross_cluster_drift_{ssid}.csv` | CSV | 1 | Cross-cluster drift report |
| `ssid_consol_results_phase{N}_{ssid}.csv` | CSV | 2-5 | Per-site operation results |
| `mist_data.db` (table: ssidConsolidationMatrix) | SQLite | 1 | Matrix in SQLite |
| `mist_data.db` (table: ssidConsolidationDeviations) | SQLite | 1 | Deviations in SQLite |
| `mist_data.db` (table: ssidConsolidationResults) | SQLite | 2-5 | Results in SQLite |

---

## Error Messages

| Condition | Message |
|-----------|---------|
| No target SSID provided | `"A target SSID name is required. Please enter one to continue."` |
| Phase dependency not met | `"Phase {N} requires Phase {N-1} to be completed first. Please run Phase {N-1} before continuing."` |
| No cached Phase 1 data | `"No audit data found. Please run Phase 1 first to collect the current configuration."` |
| API rate limit | `"API rate limit reached. Retrying in {delay} seconds... (attempt {n}/{max})"` |
| Confirmation mismatch | `"Operation cancelled — confirmation phrase did not match."` |
| All sites PSK | `"All sites use PSK authentication. No sites are eligible for consolidation."` |
