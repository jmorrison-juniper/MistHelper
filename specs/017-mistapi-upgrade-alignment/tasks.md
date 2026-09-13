# Implementation Tasks: mistapi 0.57.2 → 0.62.0 Alignment

**Branch**: `feat/260-mistapi-upgrade-alignment`
**Issue**: #260
**Spec**: `specs/017-mistapi-upgrade-alignment/spec.md`
**Last Updated**: 2026-05-07

All tasks executed in this order. P0 tasks are blocking — do not proceed to P1+ until P0 passes `py_compile` and `ruff check`.

---

## PHASE 1 — P0: Runtime Break Fixes

### T-001: Fix `searchOrgBgpPeers` → `searchOrgBgpStats`

**File**: `MistHelper.py` line ~16191
**Action**: Single attribute rename in `api_call=` argument
**How to find**: `grep -n "searchOrgBgpPeers" MistHelper.py`
**Change**:
  - Before: `api_call=mistapi.api.v1.orgs.stats.searchOrgBgpPeers`
  - After:  `api_call=mistapi.api.v1.orgs.stats.searchOrgBgpStats`
**Verify**: `python -m py_compile MistHelper.py`

---

### T-002: Fix `searchOrgTunnels` → `searchOrgTunnelsStats`

**File**: `MistHelper.py` line ~16198
**Action**: Single attribute rename
**How to find**: `grep -n "searchOrgTunnels\b" MistHelper.py`
**Change**:
  - Before: `api_call=mistapi.api.v1.orgs.stats.searchOrgTunnels`
  - After:  `api_call=mistapi.api.v1.orgs.stats.searchOrgTunnelsStats`
**Verify**: `python -m py_compile MistHelper.py`

---

### T-003: Fix `listOrgSitesStats` → `listOrgSiteStats`

**File**: `MistHelper.py` line ~16205
**Action**: Single attribute rename (remove trailing 's')
**How to find**: `grep -n "listOrgSitesStats" MistHelper.py`
**Change**:
  - Before: `api_call=mistapi.api.v1.orgs.stats.listOrgSitesStats`
  - After:  `api_call=mistapi.api.v1.orgs.stats.listOrgSiteStats`
**Verify**: `python -m py_compile MistHelper.py`; `python -m ruff check MistHelper.py`

---

### T-004: Phase 1 gate check

**Actions**:
1. `python -m py_compile MistHelper.py` — must produce no output
2. `python -m ruff check MistHelper.py` — must produce no violations
3. `python -m black --check MistHelper.py` — if violations, run `python -m black MistHelper.py`

**Do not proceed to Phase 2 until all three pass clean.**

---

## PHASE 2 — P1: Security Hardening and Requirements

### T-005: Add `LogSanitizer` to root logger

**File**: `MistHelper.py` — find the existing `logging.basicConfig(...)` or logger
setup block near the top of the file.

**Action**:
1. Find: `grep -n "logging.basicConfig\|logging.getLogger\|LOGGER = " MistHelper.py | head -20`
2. After the existing logger initialization, add:
   ```python
   from mistapi.__logger import LogSanitizer
   logging.getLogger().addFilter(LogSanitizer())
   ```
   If `LogSanitizer` is already imported elsewhere, just add the `addFilter` call.
3. Verify: `python -c "import MistHelper"` does not raise ImportError
4. Verify: `python -m py_compile MistHelper.py`

---

### T-006: Update `requirements.txt` mistapi version pin

**File**: `requirements.txt`
**Action**: Change the mistapi line from `mistapi==0.57.2` (or whatever it says)
to `mistapi>=0.62.0`
**How to find**: `grep -n "mistapi" requirements.txt`
**Verify**: `grep mistapi requirements.txt` shows `mistapi>=0.62.0`

---

### T-007: Verify `getOrg128TRegistrationCommands` not called

**Action**: `grep -n "getOrg128T\|128T" MistHelper.py`
- If any live API call found: rename to `getOrgSsrRegistrationCommands`
- If only in comments or strings: no change needed; document result

---

## PHASE 3 — P2: New Export Menus

### T-008: Add PK strategies for all new menu endpoints

**File**: `MistHelper.py` — `ENDPOINT_PRIMARY_KEY_STRATEGIES` dict
**Find**: `grep -n "ENDPOINT_PRIMARY_KEY_STRATEGIES" MistHelper.py`

Add the following entries (before implementing any of T-009 through T-014):

```python
"getOrgE911Report": {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
    "indexes": ["org_id"],
},
"searchOrgOspfStats": {
    "type": "composite_pk",
    "primary_key": ["mac", "peer_ip", "timestamp"],
    "indexes": ["org_id", "site_id", "state"],
},
"searchSiteOspfStats": {
    "type": "composite_pk",
    "primary_key": ["mac", "peer_ip", "timestamp"],
    "indexes": ["site_id", "state"],
},
"listSiteMxEdgeUpgrades": {
    "type": "natural_pk",
    "primary_key": ["id"],
    "indexes": ["site_id", "status"],
},
"getSiteAutoMapAssignmentStatus": {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
    "indexes": ["site_id"],
},
```
Note: JSI PBN and SIRT strategies are already defined. Confirm before proceeding.
**Verify**: `python -m py_compile MistHelper.py`

---

### T-009: Add E911 Report export menu

**Spec ref**: FR-006
**API**: `mistapi.api.v1.orgs.exports.getOrgE911Report(apisession, org_id)`
**Pattern**: Org-level single-call export (no pagination, no site selector)
**Action**:
1. Find the org-level export menus section
2. Add a new menu option: "Export E911 Report"
3. Implement as a static method calling `getOrgE911Report` and passing to `DataExporter`
4. Add menu number to README.md and increment operation count
5. `python -m py_compile MistHelper.py`; `python -m ruff check MistHelper.py`

---

### T-010: Add JSI PBN search export menu

**Spec ref**: FR-007
**API**: `mistapi.api.v1.orgs.jsi.searchOrgJsiPbn(apisession, org_id, ...)`
**Pattern**: Org-level paginated search — use `APIDataFetcher`
**Action**:
1. Verify PK strategy for `searchOrgJsiPbn` already exists
2. Add menu alongside existing JSI asset export menus
3. Use `sort_key="id"` or available sort field
4. Add to README.md; increment count
5. `py_compile`; `ruff check`

---

### T-011: Add JSI SIRT search export menu

**Spec ref**: FR-008
**API**: `mistapi.api.v1.orgs.jsi.searchOrgJsiSirt(apisession, org_id, ...)`
Pass v0.62.0 new params: `updated_after`, `updated_before`, `published_after`,
`published_before`, `text`, `sort` as optional kwargs where available.
**Pattern**: Same as T-010; paginated search
**Action**: Same steps as T-010 but for SIRT

---

### T-012: Add OSPF Stats export menus (org + site)

**Spec ref**: FR-009
**APIs**:
  - `mistapi.api.v1.orgs.stats.searchOrgOspfStats(apisession, org_id, ...)`
  - `mistapi.api.v1.sites.stats.searchSiteOspfStats(apisession, site_id, ...)`
**Pattern**: Two new menus — one org-level, one site-level with `SiteSelector.get_site()`
**Action**:
1. Add org OSPF stats menu alongside BGP stats menu (they are thematically related)
2. Add site OSPF stats menu
3. PK strategies added in T-008
4. Add both to README.md; increment count by 2
5. `py_compile`; `ruff check`

---

### T-013: Add MxEdge Upgrade Status menu (site-level, read-only)

**Spec ref**: FR-010
**API**: `mistapi.api.v1.sites.mxedges.listSiteMxEdgeUpgrades(apisession, site_id)`
**Pattern**: Site-level with `SiteSelector.get_site()`; simple list call
**Action**:
1. Add menu alongside existing MxEdge menus
2. PK strategy added in T-008
3. Add to README.md; increment count
4. `py_compile`; `ruff check`

---

### T-014: Add Auto-Map Assignment Status menu (site-level, read-only)

**Spec ref**: FR-011
**API**: `mistapi.api.v1.sites.auto_map_assignment.getSiteAutoMapAssignmentStatus(apisession, site_id)`
**Pattern**: Site-level with `SiteSelector.get_site()`; single-call status export
**Action**:
1. Add menu alongside existing site map menus (near Menu 51)
2. PK strategy added in T-008
3. Add to README.md; increment count
4. `py_compile`; `ruff check`

---

## PHASE 4 — Documentation and Final Gate

### T-015: Update CHANGELOG.md

Add version entry at top:
```
## [YY.MM.DD.HH.MM] - YYYY-MM-DD (UTC)

### Fixed
- FR-001: Renamed searchOrgBgpPeers to searchOrgBgpStats (mistapi 0.62.0 rename)
- FR-002: Renamed searchOrgTunnels to searchOrgTunnelsStats (mistapi 0.62.0 rename)
- FR-003: Renamed listOrgSitesStats to listOrgSiteStats (mistapi 0.62.0 rename)

### Security
- FR-004: Added LogSanitizer filter to root logger for automatic sensitive-field redaction

### Added
- FR-005: Updated requirements.txt to mistapi>=0.62.0
- FR-006: New menu — Export E911 Report (getOrgE911Report)
- FR-007: New menu — Export JSI PBN Data (searchOrgJsiPbn)
- FR-008: New menu — Export JSI SIRT Data (searchOrgJsiSirt)
- FR-009: New menus — Export OSPF Stats (org and site level)
- FR-010: New menu — Export MxEdge Upgrade Status (site)
- FR-011: New menu — Export Auto-Map Assignment Status (site)
```

---

### T-016: Final quality gate

**Actions** (all must pass clean):
1. `python -m py_compile MistHelper.py`
2. `python -m ruff check MistHelper.py`
3. `python -m black --check MistHelper.py`
4. `python MistHelper.py --test` (skip 14, 18, 63-65, 90-100)
5. Manually verify: BGP stats menu, tunnel stats menu, site stats menu — no AttributeError
6. Verify root logger has LogSanitizer: `python -c "import logging; import MistHelper; print([f for f in logging.getLogger().filters if 'Sanitize' in type(f).__name__])"`

---

## PHASE 5 — Git Workflow

### T-017: Create branch and commit

```powershell
# Worktree (preferred on Windows)
git worktree add ../MistHelper-260 -b feat/260-mistapi-upgrade-alignment main
cd ../MistHelper-260
# Copy over the modified MistHelper.py, requirements.txt, CHANGELOG.md, README.md
# Then:
git add MistHelper.py requirements.txt CHANGELOG.md README.md
git commit -m "feat(MistHelper.py): mistapi 0.57.2->0.62.0 alignment

- Fix 3 confirmed runtime breaks (searchOrgBgpStats, searchOrgTunnelsStats, listOrgSiteStats)
- Add LogSanitizer to root logger for sensitive-field redaction
- Update requirements.txt to mistapi>=0.62.0
- Add 6 new export menus: E911, JSI PBN, JSI SIRT, OSPF Stats (x2), MxEdge Upgrades, Auto-Map Status

Closes #260"
git push origin feat/260-mistapi-upgrade-alignment
```

### T-018: Create PR and wait for CI

```powershell
gh pr create --title "feat(MistHelper.py): mistapi 0.62.0 alignment" \
  --body "Closes #260" --base main
gh pr checks <pr-number> --watch
# Wait for ALL checks including CodeQL before adding auto-merge label
gh pr edit <pr-number> --add-label "auto-merge"
```
