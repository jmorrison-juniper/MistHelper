# Implementation Plan: SSID Template Consolidation Rewrite (Menu 159)

**Spec**: 018-ssid-template-consolidation-v2
**Branch**: `feat/72-ssid-template-consolidation-rewrite`
**Date**: 2026-04-08

---

## Technical Context

| Aspect | Detail |
| - | - |
| Language | Python 3.13+ |
| Target file | `MistHelper.py` (~55K lines, monolith) |
| Pattern reference | `E911BSSIDReportGenerator` (line ~12945), `FirmwareManager` (line ~41113) |
| Menu slot | 159 (replacing broken `SSIDTemplateConsolidationLauncher`) |
| SDK | mistapi >= 0.59 |
| Output | CSV + SQLite via `DataExporter.write_with_format_selection()` |
| Input | `InputUtils.safe_input()` for all prompts, `"CONFIRM"` gate for writes |
| Org ID | `ConfigUtils.get_cached_or_prompted_org_id()` |
| Caching | JSON files in `data/` directory |
| Delete | `src/ssid_consolidation/` directory (old broken implementation) |

---

## Constitution Check

| Rule | Status | Notes |
| - | - | - |
| 5-Item Rule | PASS | Class has 5 phases + helpers, each phase is a method ≤25 lines with extracted helpers |
| Max 5 params per method | PASS | All methods use config dicts or self attributes, not long param lists |
| Max 25 lines per method | PASS | Each phase method orchestrates ~5 helper calls |
| No wrappers | PASS | All code in `SSIDTemplateConsolidationManager` class |
| Class-based design | PASS | Single class with `@staticmethod execute()` entry point |
| safe_input for all input | PASS | Uses `InputUtils.safe_input()` throughout |
| CONFIRM for writes | PASS | Phases 2-5 require exact `"CONFIRM"` string |
| Dual output (CSV + SQLite) | PASS | All reports use `DataExporter.write_with_format_selection()` |
| PK strategy defined | PASS | 6 new entries in `ENDPOINT_PRIMARY_KEY_STRATEGIES` |
| No sample data fallback | PASS | Empty results reported honestly |
| ASCII-only logging | PASS | No emoji in log messages |

---

## Gate Evaluation

| Gate | Result | Evidence |
| - | - | - |
| All FR-* addressed | PASS | 45 FRs mapped to tasks below |
| All user stories covered | PASS | 7 stories + edge cases → tasks |
| No unresolved NEEDS CLARIFICATION | PASS | 5 clarifications resolved in spec |
| Primary key strategies defined | PASS | See data-model.md |
| API methods verified | PASS | All 5 org-level calls confirmed in research.md |

---

## Architecture Overview

### Class Structure

```
SSIDTemplateConsolidationManager
├── execute()                      # Static entry point (menu 159)
├── __init__(org_id, target_ssid)  # Sets up state
├── run_phase_menu()               # Phase selector sub-menu
│
├── Phase 1: Read-Only Audit
│   ├── phase1_audit()             # Orchestrator
│   ├── _fetch_all_org_data()      # 5-7 paginated API calls
│   ├── _build_matrix()            # Cross-reference into rows
│   ├── _classify_site()           # PSK/anomaly/eligible
│   ├── _analyze_deviations()      # Per-cluster param comparison
│   └── _save_cache()              # JSON + CSV + SQLite
│
├── Phase 2: Site Variables
│   ├── phase2_site_variables()    # Orchestrator
│   ├── _compute_variable_plan()   # Deviation → variable mapping
│   ├── _display_variable_summary()# Confirmation table
│   └── _write_site_variables()    # API writes with progress
│
├── Phase 3: Site Groups
│   ├── phase3_site_groups()       # Orchestrator
│   ├── _compute_group_plan()      # Cluster → group mapping
│   ├── _ensure_groups_exist()     # Create missing groups
│   └── _assign_sites_to_groups()  # API writes with progress
│
├── Phase 4: Templates
│   ├── phase4_templates()         # Orchestrator
│   ├── _resolve_deviations()      # Interactive per-param resolution
│   ├── _build_template_config()   # Construct WLAN with var refs
│   └── _create_or_update_templates() # API writes
│
├── Phase 5: Disable Old SSIDs
│   ├── phase5_disable_old()       # Orchestrator
│   ├── _build_disable_plan()      # Identify SSIDs to disable
│   └── _disable_ssids()           # API writes with progress
│
└── Shared Helpers
    ├── _load_cache()              # Read Phase 1 cache
    ├── _load_phase_results(N)     # Read phase N results
    ├── _check_prerequisite(N)     # Verify phase N-1 complete
    ├── _save_phase_results(N)     # Write results JSON
    ├── _offer_resume(N, results)  # Detect partial, offer resume
    └── _confirm_or_cancel(msg)    # CONFIRM gate helper
```

### File Locations

| File | Purpose |
| - | - |
| `data/ssid_consolidation_cache.json` | Phase 1 bulk data + matrix |
| `data/ssid_consolidation_phase2_results.json` | Phase 2 per-site results |
| `data/ssid_consolidation_phase3_results.json` | Phase 3 per-site results |
| `data/ssid_consolidation_phase4_results.json` | Phase 4 template results |
| `data/ssid_consolidation_phase5_results.json` | Phase 5 disable results |
| `data/ssid_consolidation_matrix.csv` | Phase 1 matrix report (CSV) |
| `data/ssid_consolidation_deviations.csv` | Phase 1 deviation report (CSV) |

---

## Implementation Tasks

### Task 0: Cleanup — Delete Old Implementation

**Effort**: Small
**Files**: `src/ssid_consolidation/` (delete), `MistHelper.py` (remove old launcher)
**FR**: FR-003

1. Delete `src/ssid_consolidation/` directory entirely.
2. Remove `SSIDTemplateConsolidationLauncher` class (lines ~12862–12943).
3. Update menu 159 registration to point to `SSIDTemplateConsolidationManager.execute`.
4. Remove the `from src.ssid_consolidation...` import block in the old launcher.

**Verification**: `python -m py_compile MistHelper.py` passes. Menu 159 shows new description.

---

### Task 1: Primary Key Strategies

**Effort**: Small
**Files**: `MistHelper.py` (ENDPOINT_PRIMARY_KEY_STRATEGIES dict, line ~3281)
**FR**: FR-043

Add 6 entries to `ENDPOINT_PRIMARY_KEY_STRATEGIES`:

```python
'ssidConsolidationMatrix': {
    'type': 'composite_pk',
    'primary_key': ['site_id', 'ssid_id'],
    'indexes': ['site_name', 'template_id', 'mxtunnel_id', 'target_group'],
    'unique_constraints': [],
    'description': 'SSID consolidation matrix - one row per site per target SSID',
},
'ssidConsolidationDeviation': {
    'type': 'composite_pk',
    'primary_key': ['cluster_id', 'parameter'],
    'indexes': ['cluster_name'],
    'unique_constraints': [],
    'description': 'SSID parameter deviations within cluster groups',
},
'ssidConsolidationSiteVars': {
    'type': 'composite_pk',
    'primary_key': ['site_id', 'variable_name'],
    'indexes': ['site_name', 'status'],
    'unique_constraints': [],
    'description': 'Site variable assignments for SSID consolidation',
},
'ssidConsolidationSiteGroups': {
    'type': 'composite_pk',
    'primary_key': ['site_id', 'group_id'],
    'indexes': ['group_name', 'status'],
    'unique_constraints': [],
    'description': 'Site group assignments for SSID consolidation',
},
'ssidConsolidationTemplates': {
    'type': 'composite_pk',
    'primary_key': ['template_id', 'ssid_name'],
    'indexes': ['template_name', 'group_name', 'status'],
    'unique_constraints': [],
    'description': 'Consolidated template creation results',
},
'ssidConsolidationDisable': {
    'type': 'composite_pk',
    'primary_key': ['site_id', 'ssid_id'],
    'indexes': ['old_template_id', 'status'],
    'unique_constraints': [],
    'description': 'Old SSID disable results for SSID consolidation',
},
```

**Verification**: No syntax errors. Existing PK strategies unaffected.

---

### Task 2: Class Skeleton — SSIDTemplateConsolidationManager

**Effort**: Medium
**Files**: `MistHelper.py` (insert new class near E911BSSIDReportGenerator, ~line 12945)
**FR**: FR-001, FR-002, FR-004, FR-005, FR-006, FR-007, FR-008, FR-041, FR-045

Create the class with:
- Class-level constants: `CACHE_FILE`, `PHASE_RESULT_FILES`, `CACHE_FRESHNESS_MINUTES`, `PILOT_PATTERN`, `PSK_AUTH_TYPES`, `METADATA_FIELDS`, `CONFIRM_KEYWORD`
- `__init__(self, org_id: str, target_ssid: str)` — stores org_id, target_ssid, initializes empty state dicts
- `execute()` — static entry point: prompts for SSID (reads `MIST_TARGET_SSID`), gets org_id, creates instance, calls `run_phase_menu()`
- `run_phase_menu()` — displays phase sub-menu (1-5 + Run All), validates prerequisites, dispatches
- `_confirm_or_cancel(summary: str) -> bool` — displays summary, reads `"CONFIRM"`, returns bool
- `_check_prerequisite(phase: int) -> bool` — checks cache/results files exist for prior phase
- `_load_cache() -> dict | None` — reads cache JSON, checks freshness
- `_save_phase_results(phase: int, results: list) -> None` — writes results JSON
- `_load_phase_results(phase: int) -> dict | None` — reads results JSON
- `_offer_resume(phase: int, results: dict) -> tuple[bool, list]` — detects partial run, offers resume

**Verification**: Class compiles. `execute()` shows SSID prompt and phase menu. No API calls yet.

---

### Task 3: Phase 1 — Data Collection

**Effort**: Large
**Files**: `MistHelper.py` (SSIDTemplateConsolidationManager methods)
**FR**: FR-009, FR-010, FR-011, FR-017, FR-044

Implement `_fetch_all_org_data()`:

```python
def _fetch_all_org_data(self) -> dict[str, Any]:
    """Fetch all org data using bulk API calls (5-7 total)."""
    # 1. listOrgTemplates → all WLAN templates
    # 2. listOrgWlans → all org WLANs (for template WLAN details)
    # 3. listOrgSites → all sites with vars, sitegroup_ids
    # 4. listOrgMxTunnels → all Edge clusters
    # 5. listOrgSiteGroups → existing site groups
    # Each uses mistapi.get_all() for pagination
    # Returns dict with all 5 datasets
```

Pattern follows `E911BSSIDReportGenerator._fetch_org_bulk_data()`:
- Use `mistapi.api.v1.orgs.templates.listOrgTemplates(apisession, org_id)`
- Use `mistapi.api.v1.orgs.wlans.listOrgWlans(apisession, org_id, limit=DEFAULT_API_PAGE_LIMIT)`
- Use `mistapi.api.v1.orgs.sites.listOrgSites(apisession, org_id, limit=DEFAULT_API_PAGE_LIMIT)`
- Use `mistapi.api.v1.orgs.mxtunnels.listOrgMxTunnels(apisession, org_id)`
- Use `mistapi.api.v1.orgs.sitegroups.listOrgSiteGroups(apisession, org_id)`
- All results via `mistapi.get_all(response=response, mist_session=apisession)`

Implement cache logic:
- Check if `data/ssid_consolidation_cache.json` exists and is fresh
- If fresh: offer to reuse or refresh
- Save collected data with timestamp

**CRITICAL**: No per-site API calls. All queries are org-level bulk.

**Verification**: Phase 1 fetches data with ≤10 API calls. Cache file created. Re-run offers cached data.

---

### Task 4: Phase 1 — Matrix Builder

**Effort**: Large
**Files**: `MistHelper.py` (SSIDTemplateConsolidationManager methods)
**FR**: FR-012, FR-013, FR-016

Implement `_build_matrix()`:

1. Build lookups:
   - `mxtunnel_lookup: dict[str, str]` — cluster_id → cluster_name
   - `template_lookup: dict[str, dict]` — template_id → template object (with WLANs)
2. For each site from `listOrgSites`:
   a. Find assigned template via cross-referencing (site's `sitetemplate_id` or template's `applies.site_ids`)
   b. Within that template, find the WLAN matching `target_ssid` by name
   c. Extract auth type, VLAN, mxtunnel_ids
   d. Call `_classify_site()` — returns psk_detected, anomaly, anomaly_reason
   e. Resolve cluster via `mxtunnel_ids[0]` → `mxtunnel_lookup`
   f. Determine `target_group` (pilot pattern match → "pilot", else cluster name)
   g. Build row dict, append to matrix

Implement `_classify_site()`:
- PSK check: `auth_type in self.PSK_AUTH_TYPES`
- Anomaly checks: SSID count != 2, target SSID not found, no cluster mapping, no template

Output matrix to CSV + SQLite via `DataExporter.write_with_format_selection()`.

**Site → template resolution**: WLAN templates use `applies.site_ids` and/or `applies.sitegroup_ids`. The matrix builder iterates templates and checks if each site is in the template's applies scope. Alternatively, sites may have a `sitetemplate_id` field. Check both paths.

**Verification**: Output CSV has ~170 rows. PSK sites flagged. Anomaly sites flagged with reason codes.

---

### Task 5: Phase 1 — Deviation Analysis

**Effort**: Medium
**Files**: `MistHelper.py` (SSIDTemplateConsolidationManager methods)
**FR**: FR-014, FR-015, FR-018

Implement `_analyze_deviations()`:

1. Group eligible (non-PSK, non-anomaly) sites by `target_group` (cluster name).
2. For each group, collect all matched SSID configs (full WLAN JSON dicts).
3. Build set of all keys across all SSIDs. Exclude `METADATA_FIELDS` = `{id, org_id, site_id, template_id, created_time, modified_time}`.
4. For each key, collect all values. If >1 unique value → deviation.
5. For each deviation: `{parameter, values: [{value, sites: [site_names], count}]}`.
6. Identify canonical value = majority (most sites).

Implement cross-cluster drift:
1. For each parameter, get canonical value per cluster.
2. If canonical values differ across clusters → drift.

Output deviation report to CSV + SQLite.

**Verification**: At least one deviation detected (VLAN or tunnel reference expected). Cross-cluster section populated.

---

### Task 6: Phase 2 — Site Variable Configuration

**Effort**: Large
**Files**: `MistHelper.py` (SSIDTemplateConsolidationManager methods)
**FR**: FR-018, FR-019, FR-020, FR-021, FR-037, FR-038, FR-039, FR-040

Implement `phase2_site_variables()`:

1. `_check_prerequisite(2)` — verify Phase 1 cache exists.
2. `_load_cache()` — get matrix + deviations.
3. `_offer_resume(2, ...)` — if partial results exist.
4. `_compute_variable_plan()`:
   - For each deviation parameter → site variable name (e.g., `MISTHELPER_VLAN_ID`)
   - For each eligible site → proposed value from its current SSID config
   - Compare with existing `vars` from cached site data
   - Status: `pending`, `already_configured`, `conflict`
5. `_display_variable_summary()` — table: site_name, var_name, proposed, current, status
6. `_confirm_or_cancel()` — require "CONFIRM"
7. `_write_site_variables()`:
   - For each pending site: `updateSiteInfo(session, site_id, body={"vars": merged_vars})`
   - Merge: GET current vars, add new keys, PUT
   - Track success/failure per site
   - Save progress after each batch (resume support)
8. Save results to CSV + SQLite + JSON.

**Variable naming**: `MISTHELPER_<UPPERCASE_PARAM>` prefix avoids conflicts with existing variables.

**Verification**: Run Phase 2. Variables written to test sites. Re-run shows "already configured". Partial resume works.

---

### Task 7: Phase 3 — Site Group Assignment

**Effort**: Medium
**Files**: `MistHelper.py` (SSIDTemplateConsolidationManager methods)
**FR**: FR-022, FR-023, FR-024, FR-025, FR-037, FR-039, FR-040

Implement `phase3_site_groups()`:

1. `_check_prerequisite(3)` — verify Phase 2 results exist.
2. `_compute_group_plan()`:
   - 4 production groups: `misthelper_prod_<cluster_name>` for each Edge cluster
   - 1 pilot group: `misthelper_pilot`
   - Map each eligible site to its group
3. `_ensure_groups_exist()`:
   - Check existing groups from cache (`listOrgSiteGroups` data)
   - Create missing groups via `createOrgSiteGroup`
   - Record group IDs
4. Display plan: group name, cluster mapping, site count, site list.
5. `_confirm_or_cancel()`.
6. `_assign_sites_to_groups()`:
   - For each group: GET current `site_ids`, merge new sites, PUT via `updateOrgSiteGroup`
   - Track per-site success/failure
7. Save results.

**Verification**: 5 site groups exist. Each eligible site in exactly one group. Re-run shows "already assigned".

---

### Task 8: Phase 4 — Template Creation

**Effort**: Large
**Files**: `MistHelper.py` (SSIDTemplateConsolidationManager methods)
**FR**: FR-026, FR-027, FR-028, FR-029, FR-030, FR-031, FR-032, FR-037, FR-039

Implement `phase4_templates()`:

1. `_check_prerequisite(4)` — verify Phase 3 results exist.
2. Load deviations from cache.
3. `_resolve_deviations()`:
   - For each deviation parameter within each cluster:
     - Display all unique values with site counts
     - Prompt engineer to select canonical value (no default)
     - Log resolution: param, values, selected, timestamp
4. `_build_template_config()`:
   - Build WLAN config using site variable references for deviated params
   - E.g., `"vlan_id": "{{MISTHELPER_VLAN_ID}}"` instead of hardcoded value
   - Use canonical values for non-deviated params
5. Template naming: `misthelper_<group>_<basename>` where basename = `MIST_TEMPLATE_BASENAME` env var or SSID name
6. `_create_or_update_templates()`:
   - For each of 5 groups:
     - Check if template already exists (by name)
     - If exists and created by this tool → GET, verify first SSID intact, append new SSID, PUT
     - If exists but NOT created by this tool → warn, ask for confirmation
     - If doesn't exist → create with `createOrgTemplate`
     - Set `applies.sitegroup_ids = [group_id]`
7. Save results.

**Second SSID append logic**:
- Template created by this tool has `misthelper_` prefix → safe to append
- GET template, check existing WLANs, add new WLAN, PUT

**Verification**: 5 templates exist with correct names. SSIDs reference site variables. Site group associations correct.

---

### Task 9: Phase 5 — Disable Old SSIDs

**Effort**: Medium
**Files**: `MistHelper.py` (SSIDTemplateConsolidationManager methods)
**FR**: FR-033, FR-034, FR-035, FR-036, FR-037, FR-039, FR-040

Implement `phase5_disable_old()`:

1. `_check_prerequisite(5)` — verify Phase 4 results exist.
2. `_build_disable_plan()`:
   - For each eligible site in matrix:
     - Find old template → find matched SSID
     - If SSID already disabled → "already_disabled"
     - If site is PSK/anomaly → "skipped"
     - Else → "to_disable"
3. Display plan: site name, old template, SSID name, action.
4. `_confirm_or_cancel()`.
5. `_disable_ssids()`:
   - For each "to_disable":
     - GET template, find WLAN by ID, set `enabled: false`
     - PUT updated template via `updateOrgTemplate`
     - Track success/failure
   - Resume support via results log
6. Save results.

**CRITICAL**: Only the matched target SSID is disabled. All other SSIDs in the template are untouched (FR-034).

**Verification**: Old SSIDs show `enabled: false` in Mist dashboard. Non-target SSIDs unchanged. PSK sites untouched.

---

### Task 10: Menu Registration Update

**Effort**: Small
**Files**: `MistHelper.py` (menu dict, ~line 55952; category dict, ~line 56686)

Update menu 159 entry:
```python
"159": (SSIDTemplateConsolidationManager.execute, "SSID Template Consolidation (5-Phase Guided Workflow)"),
```

Category stays `"safe"` since Phase 1 is the default (read-only). Write phases have their own CONFIRM gates.

**Verification**: Menu shows updated description. Selecting 159 launches new class.

---

## Task Dependency Graph

```
Task 0 (cleanup) ──→ Task 2 (skeleton)
Task 1 (PK strategies) ──→ Task 3 (Phase 1 fetch)
Task 2 (skeleton) ──→ Task 3 (Phase 1 fetch)
Task 3 (Phase 1 fetch) ──→ Task 4 (Phase 1 matrix)
Task 4 (Phase 1 matrix) ──→ Task 5 (Phase 1 deviations)
Task 5 (Phase 1 deviations) ──→ Task 6 (Phase 2)
Task 6 (Phase 2) ──→ Task 7 (Phase 3)
Task 7 (Phase 3) ──→ Task 8 (Phase 4)
Task 8 (Phase 4) ──→ Task 9 (Phase 5)
Task 2 (skeleton) ──→ Task 10 (menu update)
```

**Parallelizable**: Tasks 0 and 1 can run in parallel (they don't overlap in code location).

---

## FR Traceability

| FR | Task(s) | Notes |
| - | - | - |
| FR-001 | Task 2 | Class inside MistHelper.py |
| FR-002 | Task 10 | Menu 159 registration |
| FR-003 | Task 0 | Delete src/ssid_consolidation/ |
| FR-004 | Task 2 | MIST_TARGET_SSID env var |
| FR-005 | Task 2 | Runtime override prompt |
| FR-006 | Task 2 | Single SSID scope per run |
| FR-007 | Task 2 | Phase sub-menu |
| FR-008 | Task 2 | Phase dependency enforcement |
| FR-009 | Task 3 | 5 org-level API calls |
| FR-010 | Task 3 | ≤10 paginated calls |
| FR-011 | Task 4 | mxtunnel_ids cross-reference |
| FR-012 | Task 4 | auth.type PSK detection |
| FR-013 | Task 4 | Anomaly flagging |
| FR-014 | Task 5 | Deviation analysis |
| FR-015 | Task 5 | Cross-cluster drift |
| FR-016 | Task 4, 5 | CSV + SQLite output |
| FR-017 | Task 3 | Cache with freshness |
| FR-018 | Task 5, 6 | Auto-detect variable fields |
| FR-019 | Task 6 | Summary table + CONFIRM |
| FR-020 | Task 6 | Idempotent var writes |
| FR-021 | Task 6 | PSK/anomaly skip |
| FR-022 | Task 7 | 5 site groups |
| FR-023 | Task 7 | Create missing groups |
| FR-024 | Task 7 | Idempotent assignment |
| FR-025 | Task 7 | Summary + CONFIRM |
| FR-026 | Task 8 | 5 templates |
| FR-027 | Task 8 | Interactive deviation resolution |
| FR-028 | Task 8 | Resolution audit log |
| FR-029 | Task 8 | sitegroup_ids association |
| FR-030 | Task 8 | Second SSID append |
| FR-031 | Task 8 | Template naming convention |
| FR-032 | Task 8 | Naming conflict detection |
| FR-033 | Task 9 | Set enabled: false |
| FR-034 | Task 9 | Only target SSID touched |
| FR-035 | Task 9 | PSK/anomaly skip |
| FR-036 | Task 9 | Already disabled check |
| FR-037 | Task 6-9 | CONFIRM gate on all writes |
| FR-038 | Task 2 | Log confirmation with timestamp |
| FR-039 | Task 6-9 | Per-site results log |
| FR-040 | Task 6-9 | Resume support |
| FR-041 | Task 2 | safe_input() everywhere |
| FR-042 | Task 4-9 | Dual CSV + SQLite output |
| FR-043 | Task 1 | PK strategies |
| FR-044 | Task 3, 4 | No sample data fallback |
| FR-045 | All | Clear NOC engineer language |

---

## Risk Register

| Risk | Impact | Mitigation |
| - | - | - |
| Template → site resolution ambiguity | Matrix may miss sites if `applies` field is complex | Check both `applies.site_ids` and `applies.sitegroup_ids`; log unresolved sites as anomalies |
| `updateSiteInfo` replaces all vars | Existing variables lost | Always GET → merge → PUT, never blind overwrite |
| Rate limit during 170-site writes | Phase stalls at 429 | Existing retry/backoff via `API_REQUEST_MAX_RETRIES`; resume-from-checkpoint support |
| Second SSID append races with manual edits | Template state corrupted | CONFIRM gate makes operator aware; single-operator tool assumption |
| MxTunnel API field name uncertainty | Cluster mapping breaks | Research confirmed `mxtunnel_ids` is the correct WLAN field; `listOrgMxTunnels` returns id/name |
| Pilot pattern false positives | "Westminster" matches "test" | Using word-boundary regex `\b(pilot|test|lab)\b` to avoid substring matches |

---

## API Call Budget

| Phase | Operation | Call Count | Notes |
| - | - | - | - |
| 1 | listOrgTemplates | 1 | Paginated, all templates |
| 1 | listOrgWlans | 1-2 | Paginated with limit=1000 |
| 1 | listOrgSites | 1-2 | Paginated with limit=1000 |
| 1 | listOrgMxTunnels | 1 | Typically <100 clusters |
| 1 | listOrgSiteGroups | 1 | Typically <50 groups |
| **Phase 1 total** | | **5-7** | **Well under 10** |
| 2 | updateSiteInfo (per site) | ~140 | Non-PSK, non-anomaly sites |
| 3 | createOrgSiteGroup | 0-5 | Only missing groups |
| 3 | updateOrgSiteGroup | 5 | One per group |
| 4 | createOrgTemplate / updateOrgTemplate | 5 | One per template |
| 5 | updateOrgTemplate (per old template) | ~140 | Disable SSID per template |
| **Total (full run)** | | **~300** | **Well under 5000/hour** |
