# MistHelper API Endpoint Usage Audit Summary

**Generated**: 2026-03-08T08:13:56Z  
**Branch**: `010-endpoint-usage-audit`  
**Report**: [audit-report.json](audit-report.json)

---

## Scope

| Metric | Value |
|--------|-------|
| Files audited | MistHelper.py, maps_manager.py, wsgi.py |
| Total API call sites | 370 |
| Unique API functions | 107 |
| Menu operations covered | 123 |
| Reference docs available | 1,013 |
| Call sites matched to docs | 363 / 370 (98.1%) |
| Coverage | 100% of call sites reviewed |

---

## Severity Breakdown

| Severity | Count | Tier: Incorrect | Tier: Suboptimal |
|----------|-------|-----------------|------------------|
| Critical | 1 | 1 | 0 |
| High | 3 | 3 | 0 |
| Medium | 4 | 3 | 1 |
| Low | 2 | 0 | 2 |
| **Total** | **10** | **7** | **3** |

---

## Category Breakdown

| Category | Count |
|----------|-------|
| pagination | 6 |
| parameter-usage | 4 |
| endpoint-selection | 0 |
| deprecation | 0 |
| best-practice | 0 |

---

## Top Findings

### F-001 | Critical | `getSiteSettings` typo causes AttributeError

**File**: MistHelper.py L42487  
**Function**: `mistapi.api.v1.sites.setting.getSiteSettings`  
**Menus affected**: 90 (AP Firmware)

`FirmwareManager._fetch_current_site_settings()` calls `getSiteSettings` (plural) but the SDK only exposes `getSiteSetting` (singular). This will raise `AttributeError` at runtime. All 5 other call sites use the correct singular form.

**Fix**: Replace `getSiteSettings` with `getSiteSetting` at line 42487.

---

### F-002 | High | `listSiteDevices` — 7 call sites skip pagination

**File**: MistHelper.py L9473, L9554, L9627, L10257, L10719, L12989, L14520  
**Function**: `mistapi.api.v1.sites.devices.listSiteDevices`  
**Menus affected**: 5, 6, 7, 8, 9, 12, 87-93

Seven device selection and export functions access `response.data` directly instead of using `mistapi.get_all()`. Sites with >1,000 devices will have silently truncated lists. All correctly pass the `type` parameter but skip pagination.

**Fix**: Wrap each call with `mistapi.get_all(response=response, mist_session=apisession)`.

---

### F-003 | High | `listOrgSites` — 3 call sites lack pagination

**File**: MistHelper.py L37611, L38228, L44890  
**Function**: `mistapi.api.v1.orgs.sites.listOrgSites`  
**Menus affected**: 90, 99, 100

Three firmware/upgrade site selection calls lack both `limit` and `get_all()`. Without `limit`, the API returns ~100 items. Organizations with >100 sites will have incomplete site lists during upgrade campaigns.

**Fix**: Add `limit=DEFAULT_API_PAGE_LIMIT` and wrap with `mistapi.get_all()`.

---

### F-004 | High | `getOrgInventory` — 4 call sites with pagination gaps

**File**: MistHelper.py L38410, L38534, L45105 (no limit + no get_all), L41576 (has limit, no get_all)  
**Function**: `mistapi.api.v1.orgs.inventory.getOrgInventory`  
**Menus affected**: 99, 100

SSR and switch firmware operations use `getOrgInventory` without proper pagination. Three call sites lack both `limit` and `get_all()`; one has `limit=1000` but no `get_all()`. Large organizations will have truncated device inventory during firmware upgrades.

**Fix**: Add `limit=DEFAULT_API_PAGE_LIMIT` and `mistapi.get_all()` to all four sites.

---

### F-005 | High | `listSiteDevicesStats` — type parameter missing in maps

**File**: MistHelper.py L31810, L33793, L34044, L36518  
**Function**: `mistapi.api.v1.sites.stats.listSiteDevicesStats`  
**Menus affected**: 55 (Maps)

Four maps calls omit `type='all'`, defaulting to AP-only results. The log at L31810 states "type=all" but the parameter is not passed. Maps will not display switches and gateways. Non-maps call sites at L13048, L36968, L38982 correctly pass `type='all'`.

**Fix**: Add `type='all'` to all four map-related calls.

---

### F-006 | Medium | `listOrgDevices` — missing type parameter

**File**: MistHelper.py L11101  
**Function**: `mistapi.api.v1.orgs.devices.listOrgDevices`  
**Menus affected**: (via APIDataFetcher)

APIDataFetcher initialization calls `listOrgDevices` without `type`, defaulting to AP-only results.

**Fix**: Add `type='all'` if multi-type data is intended, or add a code comment if AP-only is by design.

---

### F-007 | Medium | `getOrgInventory` — MSP portal single-page only

**File**: MistHelper.py L41576  
**Function**: `mistapi.api.v1.orgs.inventory.getOrgInventory`

MSP portal fetch has `limit=1000` but no `get_all()`, returning only the first page.

**Fix**: Add `mistapi.get_all()` after the API call.

---

### F-008 | Medium | `listSiteWirelessClientsStats` — limit=100 truncation

**File**: MistHelper.py L13803  
**Function**: `mistapi.api.v1.sites.stats.listSiteWirelessClientsStats`  
**Menus affected**: 17

Client hostname lookup uses `limit=100` without `get_all()`. High-density sites with >100 clients will have unreliable hostname resolution (defaults to "Unknown").

**Fix**: Use `get_all()` with `DEFAULT_API_PAGE_LIMIT`, or filter by specific client MAC.

---

### F-009 | Low | `listSiteMaps` — no explicit limit (20 call sites)

**File**: MistHelper.py, maps_manager.py  
**Function**: `mistapi.api.v1.sites.maps.listSiteMaps`  
**Menus affected**: 51, 55

All 20 `listSiteMaps` calls omit the `limit` parameter. Most sites have few maps, but very large campuses could experience truncation.

**Fix**: Add `limit=DEFAULT_API_PAGE_LIMIT` to performance-critical map paths.

---

### F-010 | Low | `listSiteDevicesStats` — maps pagination inconsistency

**File**: MistHelper.py L31810, L33793, L36518  
**Function**: `mistapi.api.v1.sites.stats.listSiteDevicesStats`  
**Menus affected**: 55

Three of four maps `listSiteDevicesStats` calls lack `get_all()`, while L34044 uses it correctly. An inconsistency suggesting oversight.

**Fix**: Add `get_all()` to L31810, L33793, L36518 to match L34044.

---

## Verified Clean Areas

The following areas were audited and found to be correct:

| Area | Call Sites | Status |
|------|-----------|--------|
| WebSocket operations (menus 5-8, 87-89) | 28+ | All correct — proper device validation, correct endpoints |
| SLE/Insight metrics (menus 53, 66-69, 81, 83) | 12+ | All correct — proper scope-level endpoints |
| Per-site iteration patterns | 14 loops | All justified — no org-level bulk alternatives exist |
| `searchOrgDeviceEvents` | 3 sites | All properly paginated with get_all() |
| `listSiteDevices` type parameter | 23 (MH) + 3 (MM) | All correctly pass type parameter |
| `updateSiteMap` | 7 sites | All calls correct |
| Firmware destructive confirmations | All | Proper "Type 'UPGRADE' to proceed" prompts |
| Virtual chassis confirmations | All | Proper confirmation + error handling |
| Deprecated `app.run_server()` | 0 | No deprecated Dash patterns found |
| Hardcoded API URLs | 11 | All justified for WebSocket/special I/O |

---

## Unmatched SDK Functions

Two SDK functions used in MistHelper.py could not be matched to enriched documentation:

| Function | Call Sites | Impact |
|----------|-----------|--------|
| `sites.listSites` | 6 | No enriched doc available — appears to be an undocumented or deprecated variant |
| `sites.stats.getSiteClientsStats` | 1 | No enriched doc available — possible legacy endpoint |

---

## Methodology

1. **Documentation Index**: Parsed `## mistapi SDK` sections from all 1,013 enriched API docs to build function-to-doc mappings
2. **Call Site Catalog**: Scanned all 3 source files for `mistapi.api.v1.*` invocations (370 total)
3. **Documentation Matching**: Three-step matching (exact → scope+function → manual mappings) achieved 98.1% coverage
4. **Menu Mapping**: Traced all 123 menu entries through `menu_actions` dict to identify affected operations
5. **Cross-Reference Audit**: Compared each call site's parameters and usage patterns against SDK signatures and enriched doc guidance
6. **Verification**: All findings verified by reading source code and inspecting SDK module signatures via `inspect.signature()`
