# Feature Specification: mistapi 0.57.2 → 0.62.0 Full Alignment

**Feature Branch**: `feat/260-mistapi-upgrade-alignment`
**GitHub Issue**: #260
**Created**: 2026-03-29
**Revamped**: 2026-05-07
**Status**: Ready for Implementation
**Changelog Reference**: `data/mistapi-changelog-0.57.2-to-0.62.0.md`

---

## Overview

MistHelper has been upgraded from mistapi 0.57.2 to 0.62.0 (13 releases, Dec 2025 – May 2026).
A thorough code audit was performed: every mistapi call in MistHelper.py (~38,000 lines) was
located and cross-referenced against actual 0.62.0 module signatures using `inspect.signature()`.

This spec is a ground-up rewrite. It replaces the prior shallow draft with confirmed findings.

---

## Audit Methodology

All function calls were located via grep. Existence verified with `hasattr(module, name)`.
Signatures verified with `inspect.signature()`. Three categories:

1. **Confirmed runtime breaks** — AttributeError will crash the menu
2. **Dead parameters** — silently ignored by mistapi but will cause confusion
3. **New capabilities** — verified as present in the installed 0.62.0 library

---

## SECTION 1 — CONFIRMED RUNTIME BREAKAGES  (P0: Must fix before merge)

These are `AttributeError` crashes. The function names were renamed in mistapi and the
old names no longer exist in 0.62.0.

### Break 1 — `searchOrgBgpPeers` → `searchOrgBgpStats`

**Line**: ~16191 in MistHelper.py
**Current**: `api_call=mistapi.api.v1.orgs.stats.searchOrgBgpPeers`
**Fix**: `api_call=mistapi.api.v1.orgs.stats.searchOrgBgpStats`
**Verified**: `hasattr(orgs.stats, 'searchOrgBgpPeers')` = False; `searchOrgBgpStats` = True
**New signature**: `(mist_session, org_id, mac, neighbor_mac, site_id, vrf_name, limit,
  start, end, duration, sort, search_after)` — same logical params, new name

---

### Break 2 — `searchOrgTunnels` → `searchOrgTunnelsStats`

**Line**: ~16198 in MistHelper.py
**Current**: `api_call=mistapi.api.v1.orgs.stats.searchOrgTunnels`
**Fix**: `api_call=mistapi.api.v1.orgs.stats.searchOrgTunnelsStats`
**Verified**: `hasattr(orgs.stats, 'searchOrgTunnels')` = False; `searchOrgTunnelsStats` = True

---

### Break 3 — `listOrgSitesStats` → `listOrgSiteStats`  (trailing 's' removed)

**Line**: ~16205 in MistHelper.py
**Current**: `api_call=mistapi.api.v1.orgs.stats.listOrgSitesStats`
**Fix**: `api_call=mistapi.api.v1.orgs.stats.listOrgSiteStats`
**Verified**: `hasattr(orgs.stats, 'listOrgSitesStats')` = False; `listOrgSiteStats` = True
**Note**: v0.61.2 also removed `start`/`end`/`duration` params from this function.
  MistHelper's generic `APIDataFetcher` does not pass those params, so no kwarg changes needed.

---

## SECTION 2 — INSIGHT METRICS (v0.61.2 path→query param change)

The changelog states `metrics` moved from path param to query param in v0.61.2.

### getSiteInsightMetrics (line ~17579)
```python
# CURRENT
mistapi.api.v1.sites.insights.getSiteInsightMetrics(apisession, site_id, metric)
```
0.62.0 signature: `(mist_session, site_id, metrics, ...)` — `metrics` is 3rd positional.
Current call passes local variable `metric` (singular) positionally. This WORKS because
positional order is unchanged. No runtime break. Variable name mismatch is cosmetic only.

### getSiteInsightMetricsForClient (line ~16785)
```python
# CURRENT
mistapi.api.v1.sites.insights.getSiteInsightMetricsForClient(
    apisession, site_id, normalized_client_mac, metrics=metric
)
```
Uses `metrics=` keyword already. **No change needed.**

### getSiteInsightMetricsForDevice (line ~17690)
```python
# CURRENT
mistapi.api.v1.sites.insights.getSiteInsightMetricsForDevice(
    apisession, site_id, metric, normalized_device_mac
)
```
0.62.0 signature: `(mist_session, site_id, metric, device_mac, port_id, ...)` — positional
order unchanged, `port_id` is a new optional trailing param. **No change needed.**

---

## SECTION 3 — AUTHENTICATION EXCEPTION HANDLING (v0.59.5)

**Status: Already implemented.** Lines ~2669–2682 in `initialize_mist_session_interactive()`
catch `ConnectionError` and `ValueError` explicitly. The `except SystemExit` blocks at
lines ~2514 and ~2527 are for `safe_input()` EOF handling, not mistapi. No action required.

---

## SECTION 4 — DEPRECATED FUNCTIONS

### SLE Summary Functions (deprecated v0.59.2, removal planned ~v0.65.0)

| Deprecated | Replacement |
| - | - |
| `sites.sle.getSiteSleSummary()` | `sites.sle.getSiteSleSummaryTrend()` |
| `sites.sle.getSiteSleClassifierDetails()` | `sites.sle.getSiteSleClassifierSummaryTrend()` |

**Audit result**: Neither deprecated function is called anywhere in MistHelper.py.
If SLE summary menus are added in a future spec, use the `Trend` variants from the start.

### `getOrg128TRegistrationCommands` (deprecated v0.59.1)

**Audit result**: Not called anywhere in MistHelper.py.
Replacement: `getOrgSsrRegistrationCommands`. Verify during implementation (FR-012).

### `searchOrgJsiAssetsAndContracts` — Parameter rename (v0.60.0 / v0.60.4)

Old params `eol_duration`, `eos_duration` removed.
New params: `eol_after`, `eol_before`, `eos_after`, `eos_before`, `version_eos_after`,
`version_eos_before`, `sirt_id`, `pbn_id`.

**Audit result**: Only appears in `ENDPOINT_PRIMARY_KEY_STRATEGIES` dict (line ~4523),
not in any live API call. No runtime impact. Update PK strategy entry comments if JSI
menus are added.

### `addOrgMxEdgeImage` → `addOrgMxEdgeImageFile` (renamed v0.60.0)

**Audit result**: Not called anywhere in MistHelper.py. No action required.

---

## SECTION 5 — ENHANCED PARAMETERS (Additive; low risk)

### 5.1 Alarm Search — New Filters (v0.59.5)

`searchOrgAlarms()` and `searchSiteAlarms()` gained: `group`, `severity`,
`ack_admin_name`, `acked`, `search_after`.

MistHelper line ~13284 already passes `acked=False`. The new `group` and `severity`
params could be added as interactive prompts for filtered alarm exports. Low priority.

### 5.2 `search_after` Cursor Pagination (v0.59.1)

Added to 40+ search functions. `APIDataFetcher` does not currently pass `search_after`
from page N into page N+1. Adding this would make all large exports more reliable.
Tracked as FR-013 (see below) but scoped as P3 — architectural improvement.

### 5.3 New `port_id` on Insight Metrics (v0.61.3)

`getSiteInsightMetricsForDevice`, `ForGateway`, `ForMxEdge`, `ForSwitch` all gained
optional `port_id`. Additive; no action unless port-level metric menus are desired.

### 5.4 WebSocket reconnect parameters (v0.61.2 / v0.61.4)

`mistapi.websockets.*` gained `auto_reconnect`, `max_reconnect_attempts`,
`reconnect_backoff`, `max_reconnect_backoff`, `queue_maxsize`.
MistHelper uses raw `websocket.WebSocketApp`, not `mistapi.websockets`. Not applicable.

---

## SECTION 6 — NEW MODULES (P3: Architecture — separate specs)

### 6.1 `mistapi.websockets` (v0.61.0)

Provides 12 real-time channels with auto-reconnect, bounded queues, thread safety,
and header redaction. MistHelper's `WebSocketManager` and `PacketCaptureManager` use
raw `websocket.WebSocketApp`. Migration would eliminate custom WebSocket plumbing.

**Decision**: Separate spec required. Touches `WebSocketManager`, `PacketCaptureManager`,
Menus 5–8, 87–89. Too broad for this pass. **OUT OF SCOPE.**

### 6.2 `mistapi.device_utils` (v0.61.0 / v0.61.1)

High-level AP/EX/SRX/SSR diagnostic utilities returning `UtilResponse`.

Available in installed 0.62.0:
- `device_utils.ap`: `ping`, `traceroute`, `retrieveArpTable`
- `device_utils.ex`: `ping`, `traceroute`, `bouncePort`, `cableTest`, `clearBpduError`,
  `clearDot1xSessions`, `clearHitCount`, `clearLearnedMac`, `clearMacTable`,
  `createShellSession`, `interactiveShell`, `monitorTraffic`, `releaseDhcpLeases`,
  `retrieveArpTable`, `retrieveBgpSummary`, `retrieveDhcpLeases`, `retrieveMacTable`,
  `topCommand`

Migration would replace device command handlers (Menus 88–89 / device utility WebSocket
commands). High value but architecturally broad. **OUT OF SCOPE for this pass.**
Track as separate spec.

### 6.3 `mistapi.arun()` Async Helper (v0.61.1)

Wraps sync calls in `asyncio.to_thread()`. MistHelper has no async code. Not applicable.

---

## SECTION 7 — NEW API ENDPOINTS (P2: Add as new menu operations)

All verified present in installed mistapi 0.62.0 via `inspect.signature()`.

### 7.1 E911 Report Management (v0.62.0)

Module: `mistapi.api.v1.orgs.exports`
- `getOrgE911Report(mist_session, org_id)` → APIResponse
- `enableOrgE911Report(mist_session, org_id)` → APIResponse
- `disableOrgE911Report(mist_session, org_id)` → APIResponse

Proposed: New read-only export menu for `getOrgE911Report`. The enable/disable
operations are writes — defer to a separate spec. PK: `auto_increment_with_unique`.

### 7.2 NAC Change of Authorization (v0.62.0)

- `orgs.nac_clients.sendOrgNacClientCoA(mist_session, org_id, client_mac, body)`
- `sites.nac_clients.sendSiteNacClientCoA(mist_session, site_id, client_mac, body)`

These are write/action operations affecting live clients. Must use safe_input confirmation.
PK: N/A (no data export). Proposed as utility action menus, not export menus.
Requires `client_mac` prompt and CoA body input. Add to Menus 90–100 range.

### 7.3 MxEdge Upgrade Lifecycle (v0.62.0)

Read-only (safe to add now):
- `sites.mxedges.listSiteMxEdgeUpgrades(mist_session, site_id)` → APIResponse
- `sites.mxedges.getSiteMxEdgeUpgrade(mist_session, site_id, upgrade_id)`
- Org equivalents via `orgs.mxedges`

Write operations (defer): `updateOrgMxEdgeUpgrade`, `cancelOrgMxEdgeUpgrade`,
`upgradeSiteMxEdges`, `updateSiteMxEdgeUpgrade`, `cancelSiteMxEdgeUpgrade`

Proposed: New export menu — List MxEdge Upgrade Status (site-level).
PK: `natural_pk` with `(id)` if upgrade record has UUID, else `auto_increment_with_unique`.

### 7.4 Site Auto-Map Assignment (v0.62.0)

Read-only:
- `sites.auto_map_assignment.getSiteAutoMapAssignmentStatus(mist_session, site_id)`

Write operations (defer separately): `startSiteAutoMapAssignment`, `cancelSiteAutoMapAssignment`,
`applySiteAutoMapAssignment`, `clearSiteAutoMapAssignment`

Proposed: New export menu — Get Auto-Map Assignment Status.
PK: `auto_increment_with_unique` (site_id indexed).

### 7.5 JSI PBN and SIRT Search (v0.60.0 + v0.62.0 enhancements)

PK strategies already defined in `ENDPOINT_PRIMARY_KEY_STRATEGIES`. No live calls yet.

- `orgs.jsi.searchOrgJsiPbn(mist_session, org_id, ...)` → search PBN data
- `orgs.jsi.searchOrgJsiSirt(mist_session, org_id, ...)` → v0.62.0 adds
  `updated_after`, `updated_before`, `published_after`, `published_before`, `text`, `sort`

Proposed: New export menus for JSI PBN and JSI SIRT alongside existing JSI menus.

### 7.6 OSPF Stats Search (v0.59.1)

New endpoints not yet in MistHelper:
- `orgs.stats.countOrgOspfStats(mist_session, org_id, distinct, ...)`
- `orgs.stats.searchOrgOspfStats(mist_session, org_id, site_id, mac, peer_ip, ...)`
- `sites.stats.countSiteOspfStats(...)`
- `sites.stats.searchSiteOspfStats(...)`

Proposed: New export menus alongside existing BGP stats menus. PK strategy needed.
Composite: `(mac, peer_ip, timestamp)` or site-scoped auto_increment.

### 7.7 `LogSanitizer` Security Filter (v0.59.3)

`mistapi.__logger.LogSanitizer` is a Python logging filter that automatically redacts
sensitive fields from log messages. Verified available in installed 0.62.0.

```python
from mistapi.__logger import LogSanitizer
logging.getLogger().addFilter(LogSanitizer())
```

Attach to MistHelper's root logger during initialization. Defense-in-depth for any
accidentally-logged API tokens, passwords, or MAC addresses.

### 7.8 Zigbee Join Enable (v0.62.0)

`sites.devices.enableSiteDeviceZigbeeJoin(mist_session, site_id, device_id, body)`
This is a device action (write). Belongs in destructive menu range. Defer separately.

---

## SECTION 8 — FUNCTIONAL REQUIREMENTS

### P0 — Must fix before merge

| ID | Requirement | Line | Test |
| - | - | - | - |
| FR-001 | Rename `searchOrgBgpPeers` → `searchOrgBgpStats` | ~16191 | BGP stats menu must not AttributeError |
| FR-002 | Rename `searchOrgTunnels` → `searchOrgTunnelsStats` | ~16198 | Tunnel stats menu must not AttributeError |
| FR-003 | Rename `listOrgSitesStats` → `listOrgSiteStats` | ~16205 | Site stats menu must not AttributeError |

### P1 — Important hardening

| ID | Requirement | Notes |
| - | - | - |
| FR-004 | Add `LogSanitizer` filter to root logger at startup | After existing logging.basicConfig setup |
| FR-005 | Update `requirements.txt` to `mistapi>=0.62.0` | Was `mistapi>=0.57.2` or similar |
| FR-012 | Verify `getOrg128TRegistrationCommands` is not called | Grep; replace with `getOrgSsrRegistrationCommands` if found |

### P2 — New menus (high value, safe read operations)

| ID | Requirement | API Function | PK Strategy |
| - | - | - | - |
| FR-006 | Add E911 Report export menu | `orgs.exports.getOrgE911Report` | auto_increment_with_unique |
| FR-007 | Add JSI PBN search export menu | `orgs.jsi.searchOrgJsiPbn` | Already defined |
| FR-008 | Add JSI SIRT search export menu | `orgs.jsi.searchOrgJsiSirt` | Already defined |
| FR-009 | Add OSPF Stats menus (org + site) | `searchOrgOspfStats`, `searchSiteOspfStats` | composite_pk |
| FR-010 | Add MxEdge Upgrade Status menu (site) | `sites.mxedges.listSiteMxEdgeUpgrades` | natural_pk or auto_increment |
| FR-011 | Add Auto-Map Assignment Status menu | `sites.auto_map_assignment.getSiteAutoMapAssignmentStatus` | auto_increment_with_unique |

### P3 — Tracked for future specs (out of scope this pass)

| ID | Item | Future Spec |
| - | - | - |
| FR-013 | `search_after` cursor pagination in `APIDataFetcher` | Pagination improvement spec |
| FR-014 | Migrate `WebSocketManager` to `mistapi.websockets` | WebSocket refactor spec |
| FR-015 | Migrate device command menus to `mistapi.device_utils` | Device utils adoption spec |
| FR-016 | NAC CoA action menus (write, requires confirmation) | NAC operations spec |
| FR-017 | Zigbee join enable menu (write, destructive range) | Zigbee spec |
| FR-018 | MxEdge upgrade write operations | Firmware upgrade lifecycle spec |
| FR-019 | Port-level insight metrics with `port_id` | Metrics enhancement spec |

---

## SECTION 9 — NON-GOALS (This Pass)

- WebSocketManager / PacketCaptureManager migration to mistapi.websockets
- Device command menu migration to mistapi.device_utils
- mistapi.arun() async adoption
- NAC CoA write operations
- MxEdge upgrade write/cancel operations
- Zigbee join enable
- `search_after` cursor support in APIDataFetcher
- alarm group/severity interactive prompts
- Port-level `port_id` insight metrics filtering

---

## SECTION 10 — CONSTRAINTS

- Python 3.13+, mistapi >= 0.62.0
- All new menus must have `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry before implementation
- No Unicode/emoji in log output — ASCII only
- New input prompts must use `InputUtils.safe_input()` with context label
- `safe_input()` must be used for all NAC CoA confirmations if added later
- New menus must be added to README.md operation count and table
- CHANGELOG.md updated with `YY.MM.DD.HH.MM` UTC format version

---

## SECTION 11 — ACCEPTANCE CRITERIA

### P0 — Required before any merge
- [ ] `python -m py_compile MistHelper.py` — no syntax errors
- [ ] `python -m ruff check MistHelper.py` — no violations
- [ ] `python -m black --check MistHelper.py` — no formatting issues
- [ ] BGP stats export menu runs without `AttributeError` (FR-001)
- [ ] Tunnel stats export menu runs without `AttributeError` (FR-002)
- [ ] Site stats export menu runs without `AttributeError` (FR-003)
- [ ] `requirements.txt` pins `mistapi>=0.62.0` (FR-005)
- [ ] `getOrg128TRegistrationCommands` not found in any live API call (FR-012)

### P1 — Security hardening
- [ ] Root logger has `LogSanitizer` filter attached at startup (FR-004)

### P2 — New menus
- [ ] E911 Report export menu exists and runs without error (FR-006)
- [ ] JSI PBN export menu exists and runs without error (FR-007)
- [ ] JSI SIRT export menu exists and runs without error (FR-008)
- [ ] OSPF Stats menus (org + site) exist and export data (FR-009)
- [ ] MxEdge Upgrade Status menu runs and exports data (FR-010)
- [ ] Auto-Map Assignment Status menu runs without error (FR-011)

### Documentation
- [ ] `python MistHelper.py --test` passes (skip 14, 18, 63–65, 90–100)
- [ ] CHANGELOG.md entry added
- [ ] README.md operation count updated

---

## SECTION 12 — IMPLEMENTATION HINTS

### Order of Implementation

1. P0 three-line attribute renames (FR-001–003) — verify immediately with py_compile
2. LogSanitizer (FR-004) — single import + addFilter call
3. requirements.txt pin (FR-005)
4. FR-012 grep check
5. New menus in order: E911 → JSI PBN → JSI SIRT → OSPF → MxEdge Status → Auto-Map Status

### Pattern: New Read-Only Export Menu

```python
@staticmethod
def export_e911_report() -> None:
    """Export E911 report for the organization."""
    response = mistapi.api.v1.orgs.exports.getOrgE911Report(apisession, org_id)
    DataExporter.write_with_format_selection(
        response.data,
        "E911_Report.csv",
        api_function_name="getOrgE911Report",
    )
```

### Pattern: Site-Level Export with Selector

```python
@staticmethod
def export_mxedge_upgrade_status() -> None:
    """Export MxEdge upgrade status for a selected site."""
    site_id, site_name = SiteSelector.get_site(apisession, org_id)
    if not site_id:
        return
    APIDataFetcher(
        title=f"MxEdge Upgrade Status - {site_name}",
        api_call=mistapi.api.v1.sites.mxedges.listSiteMxEdgeUpgrades,
        filename="MxEdge_Upgrade_Status.csv",
        sort_key="id",
        limit=1000,
    ).execute(site_id=site_id)
```

### PK Strategy Entries (add before implementing menus)

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
