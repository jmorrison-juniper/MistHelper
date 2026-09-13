# Implementation Plan: SSID Template Consolidation

**Branch**: `018-ssid-template-consolidation` | **Date**: 2025-07-02 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/018-ssid-template-consolidation/spec.md`

## Summary

Consolidate ~170 per-site WLAN templates into 5 shared templates (4 production mapped 1:1 to Mist Edge clusters + 1 pilot/test) using site variables for per-site configuration and site groups for template assignment. Implemented as a new class-based menu option (159) in MistHelper.py with a 5-phase guided workflow: (1) read-only audit and deviation analysis, (2) site variable configuration, (3) site group assignment, (4) consolidated template creation with SSID variable references, and (5) old SSID disablement. Each modification phase requires typed "CONFIRM" confirmation. The workflow targets one SSID at a time; running it twice covers both SSIDs. All data is exported in CSV + SQLite dual format. The feature reuses existing caching, retry/backoff, safe_input, and DataExporter patterns from the codebase.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: mistapi 0.59+ (Mist API SDK by Thomas Munzer), python-dotenv, structlog (or stdlib logging)
**Storage**: CSV files in `data/` directory + SQLite (`data/mist_data.db`) — dual output per constitution
**Testing**: `python -m py_compile MistHelper.py` (syntax validation); manual testing against live org per existing patterns
**Target Platform**: Windows 11 (local dev), Linux containers (production), SSH sessions
**Project Type**: CLI tool (single-file monolith — MistHelper.py ~28K lines)
**Performance Goals**: Complete full 5-phase workflow for ~170 sites in under 60 minutes including engineer review time
**Constraints**: Mist API rate limit of 5000 calls/hour; all operations must be idempotent; zero modifications to PSK sites
**Scale/Scope**: ~170 sites, ~170 templates, ~340 WLANs, 4 Mist Edge clusters, 5 target site groups, 5 target templates

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Gate (PASS)

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Five-Item Rule | **PASS** | Main orchestrator has 5 children (one per phase + manage entry point). Each phase class is self-contained. Functions will follow max 25 lines / 5 params / 5 blocks limits. |
| II. Class-Based Architecture | **PASS** | All functionality in `SSIDTemplateConsolidationManager` and 5 phase-specific helper classes. No standalone wrapper functions. Full variable names throughout. |
| III. Safety-First (NON-NEGOTIABLE) | **PASS** | All inputs via `InputUtils.safe_input()` with context logging. Typed "CONFIRM" confirmation for every modification phase. PSK sites never touched. Secrets never logged. |
| IV. Full Deployment Pipeline (NON-NEGOTIABLE) | **PASS** | Will follow syntax validation → commit → push → CI build → pull → restart → verify pipeline. |
| V. Observability & Logging | **PASS** | ASCII-only logging. Debug for API responses, Info for user-facing progress, Error for exceptions. Per-site results logs for every modification phase. |
| Technology Constraints | **PASS** | Python 3.13+, mistapi SDK (no direct HTTP), `os.path.join()` for paths, dual CSV+SQLite output via DataExporter, natural PKs in ENDPOINT_PRIMARY_KEY_STRATEGIES, all output to `data/`. |
| Adding New Menu Operations | **PASS** | Follows the 7-step sequence: API Discovery → PK Strategy → Flatten → Dual Output → README → Version → Pipeline. |

### Post-Design Gate (PASS)

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Five-Item Rule | **PASS** | Class hierarchy: 1 orchestrator + 5 phase classes (5 children at top level). Each phase class has ≤5 public methods. Helper methods extracted to keep all functions ≤25 lines. |
| II. Class-Based Architecture | **PASS** | 6 classes total: `SSIDTemplateConsolidationManager`, `SSIDConsolidationDataCollector`, `SSIDConsolidationVariableWriter`, `SSIDConsolidationGroupAssigner`, `SSIDConsolidationTemplateCreator`, `SSIDConsolidationDisabler`. No wrappers. |
| III. Safety-First | **PASS** | Phase dependency chain enforced in code. Resume-after-interruption via results log. Every write preceded by read + confirmation. Variable conflict detection before overwrite. |
| V. Observability | **PASS** | 8 output artifacts (matrix, deviations, drift, per-phase results). All confirmation entries timestamped. Phase completion tracker for cross-session state. |

## Project Structure

### Documentation (this feature)

```text
specs/018-ssid-template-consolidation/
├── plan.md              # This file
├── research.md          # Phase 0 output — all research findings
├── data-model.md        # Phase 1 output — entity definitions
├── quickstart.md        # Phase 1 output — developer/user guide
├── contracts/
│   ├── menu-contract.md # CLI menu interface contract
│   └── api-contract.md  # Mist API interaction contract
└── tasks.md             # Phase 2 output (generated by /speckit.tasks)
```

### Source Code (repository root)

```text
MistHelper.py              # All new code added here (single-file monolith)
├── SSIDTemplateConsolidationManager      # Main orchestrator class
│   ├── SSIDConsolidationDataCollector    # Phase 1: audit + deviation analysis
│   ├── SSIDConsolidationVariableWriter   # Phase 2: site variable configuration
│   ├── SSIDConsolidationGroupAssigner    # Phase 3: site group assignment
│   ├── SSIDConsolidationTemplateCreator  # Phase 4: template creation
│   └── SSIDConsolidationDisabler         # Phase 5: old SSID disablement
├── ENDPOINT_PRIMARY_KEY_STRATEGIES       # New entries for consolidation data
└── menu_actions["159"]                   # Menu registration

data/                      # Runtime output directory
├── ssid_consol_phase1_matrix_{ssid}.csv
├── ssid_consol_phase1_deviations_{ssid}.csv
├── ssid_consol_phase1_cross_cluster_drift_{ssid}.csv
├── ssid_consol_results_phase{N}_{ssid}.csv
└── mist_data.db           # SQLite tables for all above

tests/                     # Syntax validation (existing pattern)
```

**Structure Decision**: All new code is added to `MistHelper.py` following the existing single-file monolith pattern. New classes are defined inline alongside existing manager classes. This matches the established architecture (FirmwareManager, WebSocketManager, etc. are all in MistHelper.py). The 6 new classes respect the five-item rule by having the orchestrator delegate to exactly 5 phase classes.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| 6 classes for one feature | 5 phases + 1 orchestrator requires 6 classes | Combining phases into fewer classes would violate the 25-line function limit and 5-block limit given the complexity of each phase. The orchestrator + 5 children pattern is the natural decomposition that respects the five-item rule at each level. |
| Phase 2 reads ~340 API calls | Site variables require read-then-merge-then-write per site | Batch API does not exist for site settings; per-site calls are the only option. Retry/backoff mitigates rate limits. |

---

## Detailed Design

### Class Hierarchy

```
SSIDTemplateConsolidationManager
│
│   Responsibilities:
│   - Menu entry point (.manage())
│   - SSID selector with .env default
│   - Phase selection sub-menu
│   - Phase dependency enforcement
│   - Phase completion tracking
│
├── SSIDConsolidationDataCollector
│   │
│   │   Responsibilities:
│   │   - Fetch all templates, WLANs, sites, Edge clusters
│   │   - Build consolidation matrix (1 row per site)
│   │   - Detect PSK sites and anomalies
│   │   - Classify SSIDs (secured/open_guest)
│   │   - Run deviation analysis per cluster
│   │   - Run cross-cluster drift detection
│   │   - Cache all data with freshness tracking
│   │   - Export to CSV + SQLite
│   │
│   Methods:
│   ├── collect()              → runs full Phase 1
│   ├── _fetch_all_data()      → API calls, returns raw data
│   ├── _build_matrix()        → transforms raw data into matrix rows
│   ├── _analyze_deviations()  → per-cluster field-by-field comparison
│   └── _detect_drift()        → cross-cluster canonical value comparison
│
├── SSIDConsolidationVariableWriter
│   │
│   │   Responsibilities:
│   │   - Read Phase 1 matrix from cache
│   │   - Compute required site variables per site
│   │   - Detect conflicts with existing variables
│   │   - Display confirmation summary
│   │   - Write variables via API with retry
│   │   - Track results per site
│   │
│   Methods:
│   ├── configure()            → runs full Phase 2
│   ├── _compute_variables()   → derive vars from matrix data
│   ├── _build_summary()       → format confirmation display
│   ├── _write_variables()     → API calls with retry/resume
│   └── _log_results()         → save results CSV + SQLite
│
├── SSIDConsolidationGroupAssigner
│   │
│   │   Responsibilities:
│   │   - Map sites to groups by Edge cluster
│   │   - Create missing site groups
│   │   - Assign sites to groups (idempotent)
│   │   - Display confirmation summary
│   │
│   Methods:
│   ├── assign()               → runs full Phase 3
│   ├── _calculate_groups()    → cluster-to-group mapping
│   ├── _ensure_groups_exist() → create missing groups
│   ├── _build_summary()       → format confirmation display
│   └── _apply_assignments()   → API calls + results log
│
├── SSIDConsolidationTemplateCreator
│   │
│   │   Responsibilities:
│   │   - Create or update 5 WLAN templates
│   │   - Present deviation resolutions to engineer
│   │   - Present cross-cluster drift resolutions
│   │   - Build canonical WLAN config with variable refs
│   │   - Create org-level WLANs bound to templates
│   │   - Detect and handle second-SSID append scenario
│   │
│   Methods:
│   ├── create()               → runs full Phase 4
│   ├── _resolve_deviations()  → interactive deviation selection
│   ├── _build_wlan_config()   → construct WLAN JSON with vars
│   ├── _create_templates()    → API calls for template + WLAN creation
│   └── _log_resolutions()     → audit log of all deviation choices
│
└── SSIDConsolidationDisabler
    │
    │   Responsibilities:
    │   - Identify old SSIDs matching target name
    │   - Skip PSK and anomaly sites
    │   - Skip already-disabled SSIDs
    │   - Display confirmation summary
    │   - Disable via API with retry
    │
    Methods:
    ├── disable()              → runs full Phase 5
    ├── _identify_targets()    → find SSIDs to disable
    ├── _build_summary()       → format confirmation display
    ├── _apply_disables()      → API calls with retry/resume
    └── _log_results()         → save results CSV + SQLite
```

### Data Flow

```
Phase 1 (Read-Only)
  listOrgTemplates → listOrgWlans → listOrgSites → listOrgMxTunnels
  → Build Matrix → Deviation Analysis → Cross-Cluster Drift
  → Export: matrix.csv + deviations.csv + drift.csv + SQLite tables
  → Update PhaseCompletionTracker

Phase 2 (Write — requires Phase 1)
  Read cached matrix → Compute variables per site
  → getSiteSetting per site → Merge vars → CONFIRM
  → updateSiteSettings per site → Results log
  → Update PhaseCompletionTracker

Phase 3 (Write — requires Phase 2)
  Read cached matrix → Calculate group assignments
  → listOrgSiteGroups → createOrgSiteGroup (if missing) → CONFIRM
  → updateOrgSiteGroup (batch per group) → Results log
  → Update PhaseCompletionTracker

Phase 4 (Write — requires Phase 3)
  Read cached matrix + deviations + drift
  → Resolve deviations interactively → Build canonical WLAN config → CONFIRM
  → createOrgTemplate + createOrgWlan per template → Results log
  → Log deviation resolutions → Update PhaseCompletionTracker

Phase 5 (Write — requires Phase 4)
  Read cached matrix → Identify old SSIDs to disable → CONFIRM
  → updateOrgWlan(enabled=false) per SSID → Results log
  → Update PhaseCompletionTracker
```

### API Call Optimization Strategy

Phase 1 is optimized to minimize API calls:

1. **Single paginated call** for `listOrgWlans` instead of per-template WLAN fetches
2. **Group WLANs by `template_id`** locally after fetching all org WLANs
3. **Single paginated call** for `listOrgSites` for site metadata
4. **Single call** for `listOrgMxTunnels` for Edge cluster discovery
5. **Single call** for `listOrgSiteGroups` for existing group state

This reduces Phase 1 from ~175 individual API calls to ~5 paginated calls.

### Confirmation Flow Pattern

Every modification phase (2-5) follows this exact pattern:

```python
# 1. Compute planned changes
changes = self._compute_changes(matrix_data)

# 2. Display summary
self._display_summary(changes)

# 3. Require typed confirmation
confirmation = InputUtils.safe_input(
    "  Type 'CONFIRM' to apply these changes: ",
    context=f"ssid_consolidation_phase{self.phase_number}"
)
if confirmation != "CONFIRM":
    print("  -> Operation cancelled - confirmation phrase did not match.")
    logging.warning(f"Phase {self.phase_number} cancelled by user")
    return

# 4. Log confirmation with timestamp
logging.info(
    f"User confirmed Phase {self.phase_number} at "
    f"{datetime.utcnow().isoformat()}Z"
)

# 5. Execute with per-site tracking
results = self._execute_changes(changes)

# 6. Save results
self._save_results(results)
```

### Resume-After-Interruption Pattern

```python
def _check_resume(self, target_sites):
    """Check if a previous run was interrupted and offer resume."""
    results_file = f"ssid_consol_results_phase{self.phase}__{self.ssid}.csv"
    results_path = os.path.join("data", results_file)

    if not os.path.exists(results_path):
        return target_sites  # No previous run, process all

    completed = self._parse_completed_sites(results_path)
    remaining = [s for s in target_sites if s["site_id"] not in completed]

    print(f"  Found {len(completed)}/{len(target_sites)} sites already processed.")
    choice = InputUtils.safe_input(
        "  Resume from where you left off? (Y/n): ",
        default_value="Y",
        context="resume_check"
    )

    if choice.upper() == "Y":
        print(f"  Resuming with {len(remaining)} remaining sites.")
        return remaining
    else:
        return target_sites  # Start fresh
```

### Cache Strategy

```python
# Cache file naming convention
CACHE_PREFIX = "ssid_consol"

def _get_cache_path(self, artifact, ssid_name):
    """Generate cache file path for a consolidation artifact."""
    safe_ssid = ssid_name.replace(" ", "_").replace("/", "_")
    filename = f"{CACHE_PREFIX}_{artifact}_{safe_ssid}.csv"
    return os.path.join("data", filename)

def _is_cache_fresh(self, cache_path):
    """Check if cached file is within freshness window."""
    if not os.path.exists(cache_path):
        return False
    file_mtime = datetime.fromtimestamp(os.path.getmtime(cache_path))
    age_minutes = (datetime.now() - file_mtime).total_seconds() / 60
    return age_minutes < CSV_FRESHNESS_MINUTES
```

### SSID Selector Pattern

```python
def _select_target_ssid(self):
    """Prompt for target SSID with .env default."""
    default = os.getenv("MIST_TARGET_SSID", "")
    display_default = default if default else "none"

    if default:
        ssid = InputUtils.safe_input(
            f"  Target SSID [{display_default}]: ",
            default_value=default,
            context="ssid_selector"
        )
    else:
        ssid = InputUtils.safe_input(
            f"  Target SSID [{display_default}]: ",
            allow_empty=False,
            context="ssid_selector"
        )

    if not ssid:
        print("  A target SSID name is required.")
        return None

    return ssid
```

### Phase Dependency Enforcement

```python
PHASE_DEPENDENCIES = {
    1: [],           # Phase 1 has no prerequisites
    2: [1],          # Phase 2 requires Phase 1
    3: [1, 2],       # Phase 3 requires Phases 1 and 2
    4: [1, 2, 3],    # Phase 4 requires Phases 1, 2, and 3
    5: [1, 2, 3, 4], # Phase 5 requires all previous phases
}

def _check_prerequisites(self, phase_number, target_ssid):
    """Verify all prerequisite phases are completed."""
    required = PHASE_DEPENDENCIES[phase_number]
    for req_phase in required:
        tracker_path = self._get_tracker_path(req_phase, target_ssid)
        if not self._is_phase_completed(tracker_path):
            print(
                f"  Phase {phase_number} requires Phase {req_phase} "
                f"to be completed first.\n"
                f"  Please run Phase {req_phase} before continuing."
            )
            return False
    return True
```

### Primary Key Strategy Additions

Six new entries for `ENDPOINT_PRIMARY_KEY_STRATEGIES`:

```python
"listOrgTemplates": {
    "type": "natural_pk",
    "primary_key": ["id"],
    "indexes": ["name", "org_id"],
    "unique_constraints": [],
    "description": "Org WLAN templates keyed by Mist UUID"
},
"listOrgSiteGroups": {
    "type": "natural_pk",
    "primary_key": ["id"],
    "indexes": ["name"],
    "unique_constraints": [],
    "description": "Org site groups keyed by Mist UUID"
},
"listOrgMxTunnels": {
    "type": "natural_pk",
    "primary_key": ["id"],
    "indexes": ["name"],
    "unique_constraints": [],
    "description": "Org Mist Edge tunnels keyed by Mist UUID"
},
"ssidConsolidationMatrix": {
    "type": "natural_pk",
    "primary_key": ["site_id"],
    "indexes": ["site_name", "template_id", "consolidation_group"],
    "unique_constraints": [],
    "description": "SSID consolidation audit matrix, one row per site"
},
"ssidConsolidationDeviations": {
    "type": "composite_pk",
    "primary_key": ["consolidation_group", "field_name"],
    "indexes": ["is_unanimous"],
    "unique_constraints": [],
    "description": "Per-cluster SSID deviation analysis"
},
"ssidConsolidationResults": {
    "type": "composite_pk",
    "primary_key": ["site_id", "phase_number"],
    "indexes": ["status", "site_name"],
    "unique_constraints": [],
    "description": "Per-phase per-site operation results log"
}
```

---

## Research Artifacts

See [research.md](research.md) for complete findings on:

| Research ID | Topic | Status |
|-------------|-------|--------|
| R-001 | Template ↔ Site linkage via `applies.sitegroup_ids` | Resolved |
| R-002 | Site variables via `vars` dict in site settings | Resolved |
| R-003 | WLAN object structure and PSK detection via `auth.type` | Resolved |
| R-004 | Site Group CRUD via `mistapi.api.v1.orgs.sitegroups` | Resolved |
| R-005 | Mist Edge cluster discovery via `listOrgMxTunnels` | Resolved |
| R-006 | Caching strategy extending `CacheUtils` pattern | Resolved |
| R-007 | Existing MistHelper patterns to follow | Resolved |
| R-008 | Template WLAN ownership — org-level WLANs with `template_id` | Resolved |
| R-009 | Deviation analysis approach (full-object comparison) | Resolved |
| R-010 | Resume-after-interruption via results log parsing | Resolved |

---

## Design Artifacts

| Artifact | Path | Description |
|----------|------|-------------|
| Data Model | [data-model.md](data-model.md) | 9 entity definitions, relationships, validation rules, state transitions, PK strategies |
| Menu Contract | [contracts/menu-contract.md](contracts/menu-contract.md) | CLI interface: menu registration, user flows, .env config, output files, error messages |
| API Contract | [contracts/api-contract.md](contracts/api-contract.md) | All Mist API calls by phase, payloads, rate limit budget, variable reference syntax |
| Quickstart | [quickstart.md](quickstart.md) | Developer and user guide for running the workflow |

---

## Mist API Methods Used

| Module | Method | Phase | Purpose |
|--------|--------|-------|---------|
| `orgs.templates` | `listOrgTemplates` | 1, 4 | List all WLAN templates |
| `orgs.templates` | `getOrgTemplate` | 4 | Get template detail (verify existing) |
| `orgs.templates` | `createOrgTemplate` | 4 | Create consolidated template |
| `orgs.templates` | `updateOrgTemplate` | 4 | Update template (append SSID scenario) |
| `orgs.wlans` | `listOrgWlans` | 1, 4, 5 | List all org-level WLANs |
| `orgs.wlans` | `createOrgWlan` | 4 | Create WLAN in consolidated template |
| `orgs.wlans` | `updateOrgWlan` | 5 | Disable old SSIDs (`enabled: false`) |
| `orgs.sites` | `listOrgSites` | 1 | List all sites for metadata |
| `orgs.sitegroups` | `listOrgSiteGroups` | 1, 3 | List existing site groups |
| `orgs.sitegroups` | `createOrgSiteGroup` | 3 | Create consolidation site groups |
| `orgs.sitegroups` | `updateOrgSiteGroup` | 3 | Add sites to groups |
| `orgs.mxtunnels` | `listOrgMxTunnels` | 1 | Discover Mist Edge clusters |
| `sites.setting` | `getSiteSetting` | 2 | Read current site vars |
| `sites.setting` | `updateSiteSettings` | 2 | Write site vars |

---

## Key Design Decisions

| Decision | Rationale | Spec Reference |
|----------|-----------|----------------|
| `sitegroup_ids` only for template assignment | Cleaner than direct site_ids; adding/removing sites from group auto-updates template scope | FR-017, Clarification #2 |
| One SSID per workflow run | Simplifies deviation analysis and template append logic; engineer controls scope | FR-002, Clarification #4 |
| Identical base config across 4 production templates | Cross-cluster drift is resolved to single values; differences only via site variables | FR-016, Clarification #5 |
| Full-object WLAN comparison for deviations | Catches all divergence; no risk of missing a field | FR-010a, Clarification #3 |
| Results log as resume checkpoint | Simple, no extra infrastructure; results CSV is already required by FR-024 | FR-024a |
| Org-level WLANs with `template_id` for template binding | Mist API pattern for WLAN-in-template; not site-level WLANs | R-008 |
| Menu option 159 | Next available after existing highest (158) | agents.md menu numbering |
| `SSID_CONSOL_` prefix for site variables | Avoids collision with existing variables from other features | R-002 |
| Phase 3 batches site_ids per group update | Single PUT per group instead of per-site; ~5 calls vs ~170 | R-004, api-contract |
