# Implementation Plan: Upstream New Endpoints (mistapi v0.60–0.62)

**Branch**: `upstream-new-endpoints` | **Date**: 2026-06-11 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/upstream-new-endpoints/spec.md`

## Summary

Add 13 new menu operations to MistHelper covering mistapi v0.60–0.62 endpoints: RF channel score export, IoT endpoint search, NAC client CoA (org + site), auto-map assignment (start/status/apply/clear), Zigbee join enablement, SSO admin deletion (org + MSP), and MxEdge upgrade management (org + site). All endpoints confirmed in installed mistapi SDK. Implementation follows existing menu dispatch, `DataExporter`, and `safe_input()` patterns.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: mistapi 0.62+ (all endpoints confirmed: `orgs.nac_clients.sendOrgNacClientCoA`, `sites.nac_clients.sendSiteNacClientCoA`, `sites.rrm.getSiteChannelScores`, `sites.iotendpoints.searchSiteIotEndpoints`, `sites.auto_map_assignment`, `sites.apply_auto_map_assignment`, `sites.clear_auto_map_assignment`, `sites.devices.enableSiteDeviceZigbeeJoin`, `orgs.ssos.deleteOrgSsoAdmins`, `msps.ssos.deleteMspSsoAdmins`, `orgs.mxedges.listOrgMxEdgeUpgrades/upgradeOrgMxEdges/getOrgMxEdgeUpgrade/cancelOrgMxEdgeUpgrade/getOrgMxEdgeUpgradeInfo`, `sites.mxedges.listSiteMxEdgeUpgrades/upgradeSiteMxEdges/getSiteMxEdgeUpgrade/cancelSiteMxEdgeUpgrade`)
**Storage**: CSV, SQLite (via `DataExporter`), ArangoDB/Redis (polyglot output)
**Testing**: `python MistHelper.py --test` (safe operations only; destructive ops manual)
**Target Platform**: Windows 11 (local dev), Linux container (production)
**Project Type**: CLI tool (single-file `MistHelper.py`)
**Constraints**: All code in `MistHelper.py`; 5-Item Rule applies; inline comments + action logging mandatory

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| - | - | - |
| I. Five-Item Rule | PASS | Each new method ≤25 lines, ≤5 params. Batch operations may need helper extraction. |
| II. Class-Based Architecture | PASS | All new operations implemented as methods on existing MistHelper class or appropriate manager class. No wrappers. |
| III. Safety-First | PASS | All input via `safe_input()`. Destructive ops (SSO delete, MxEdge upgrade) require typed confirmation ('DELETE', 'UPGRADE'). |
| IV. Full Deployment Pipeline | PASS | Standard pipeline after implementation. |
| V. Observability & Logging | PASS | ASCII-only logging, structured entries. |
| VI. Inline Comments | PASS | Every executable line gets inline comment. |
| VII. Action Logging | PASS | `logging.info()` before, `logging.debug()` after every API call. |

## Project Structure

### Documentation (this feature)

```text
specs/upstream-new-endpoints/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (N/A — internal CLI, no external API)
├── checklists/          # Pre-existing checklist files
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
MistHelper.py            # All new operations added here (single-file project)
README.md                # Operation count + menu table updates
CHANGELOG.md             # Version entry for new operations
```

**Structure Decision**: Single-file project. All 13 operations added as methods to the existing class structure in `MistHelper.py`. No new files needed.

## Menu Number Allocation (Final)

| Menu # | Operation | Range | Type |
| - | - | - | - |
| 195 | Export Site RF Channel Scores | 1–59 (Safe Export) | Read-only |
| 196 | Search Site IoT Endpoints | 1–59 (Safe Export) | Read-only |
| 197 | Start Site Auto-Map Assignment | 60–96 (Interactive) | Write |
| 198 | Check Auto-Map Assignment Status | 60–96 (Interactive) | Read |
| 199 | Apply Auto-Map Assignment Results | 60–96 (Interactive) | Write |
| 200 | Clear Auto-Map Assignment Results | 60–96 (Interactive) | Write |
| 201 | Enable Zigbee Join on Site Devices | 60–96 (Interactive) | Write |
| 202 | Send NAC Client CoA (Org) | 124–150 (Interactive Mgmt) | Write |
| 203 | Send NAC Client CoA (Site) | 124–150 (Interactive Mgmt) | Write |
| 204 | Delete Org SSO Admins | 154+ (Destructive) | Destructive |
| 205 | Delete MSP SSO Admins | 154+ (Destructive) | Destructive |
| 206 | MxEdge Upgrade (Org) | 154+ (Destructive) | Destructive |
| 207 | MxEdge Upgrade (Site) | 154+ (Destructive) | Destructive |

**Note**: Menu numbers 195–207 extend the current max (194). Operations are logically grouped by category in the menu display even though sequential numbers don't match the original range definitions. The range column indicates the *conceptual category* for the operation.

## Complexity Tracking

No constitution violations. All operations follow established patterns.
