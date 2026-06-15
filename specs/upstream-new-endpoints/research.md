# Research: Upstream New Endpoints

**Feature**: upstream-new-endpoints | **Date**: 2026-06-11

## R-001: mistapi SDK Endpoint Availability

**Decision**: All 13 endpoints confirmed available in installed mistapi SDK.

**Findings**:

| Endpoint | Module | Method | Confirmed |
| - | - | - | - |
| Channel Scores | `sites.rrm` | `getSiteChannelScores(session, site_id, band)` | YES |
| IoT Search | `sites.iotendpoints` | `searchSiteIotEndpoints(session, site_id, ...)` | YES |
| NAC CoA (Org) | `orgs.nac_clients` | `sendOrgNacClientCoA(session, org_id, client_mac)` | YES |
| NAC CoA (Site) | `sites.nac_clients` | `sendSiteNacClientCoA(session, site_id, client_mac)` | YES |
| Auto-Map Start | `sites.auto_map_assignment` | `startSiteAutoMapAssignment(session, site_id)` | YES |
| Auto-Map Status | `sites.auto_map_assignment` | `getSiteAutoMapAssignment(session, site_id)` | YES |
| Auto-Map Apply | `sites.apply_auto_map_assignment` | `applySiteAutoMapAssignment(session, site_id)` | YES |
| Auto-Map Clear | `sites.clear_auto_map_assignment` | `clearSiteAutoMapAssignment(session, site_id)` | YES |
| Zigbee Join | `sites.devices` | `enableSiteDeviceZigbeeJoin(session, site_id, device_id)` | YES |
| Delete Org SSO Admins | `orgs.ssos` | `deleteOrgSsoAdmins(session, org_id, sso_id)` | YES |
| Delete MSP SSO Admins | `msps.ssos` | `deleteMspSsoAdmins(session, msp_id, sso_id)` | YES |
| MxEdge Upgrade (Org) | `orgs.mxedges` | `upgradeOrgMxEdges / listOrgMxEdgeUpgrades / getOrgMxEdgeUpgrade / cancelOrgMxEdgeUpgrade / getOrgMxEdgeUpgradeInfo` | YES |
| MxEdge Upgrade (Site) | `sites.mxedges` | `upgradeSiteMxEdges / listSiteMxEdgeUpgrades / getSiteMxEdgeUpgrade / cancelSiteMxEdgeUpgrade` | YES |

**Alternatives considered**: Direct HTTP calls — rejected per constitution (mistapi SDK methods exist).

## R-002: Channel Scores API Shape

**Decision**: `getSiteChannelScores` takes `band` parameter (24, 5, 6). Implementation should iterate all bands or let user select.

**Rationale**: Different bands have independent channel score data. Exporting all bands in one call gives complete RF picture.

## R-003: Auto-Map Assignment Workflow

**Decision**: Four-step workflow: start → status → apply → clear. Each exposed as separate menu operation.

**Rationale**: Auto-map is asynchronous. Start initiates, status checks progress, apply commits results, clear discards. Separate menu items give NOC engineers fine-grained control.

**Alternatives considered**: Single menu with sub-prompts — rejected because it adds complexity and violates 5-Item Rule for the method body.

## R-004: NAC CoA Scope (Org vs Site)

**Decision**: Two separate menu operations: org-level (applies across all sites) and site-level (scoped to one site).

**Rationale**: Mirrors existing NAC client search pattern in MistHelper. Org-level useful for global policy pushes; site-level for targeted troubleshooting.

## R-005: MxEdge Upgrade Lifecycle

**Decision**: Single menu operation per scope (org/site) with sub-menu: list upgrades → start upgrade → check status → cancel. Follows existing firmware upgrade pattern (menu 154–157).

**Rationale**: MxEdge upgrade mirrors device firmware upgrade workflow. Reusing same UX pattern reduces learning curve for NOC engineers.

## R-006: SSO Admin Deletion Safety

**Decision**: Typed 'DELETE' confirmation required. List SSO providers first, select one, then list admins, select target, confirm.

**Rationale**: Destructive operation. Must follow NASA/JPL pattern per constitution Principle III.

## R-007: Primary Key Strategies

**Decision**: Define strategies for all new endpoints before implementation.

| Operation | Strategy Type | Primary Key | Indexes |
| - | - | - | - |
| getSiteChannelScores | composite_pk | `['ap_mac', 'band', 'channel']` | `['site_id']` |
| searchSiteIotEndpoints | natural_pk | `['mac']` | `['site_id', 'type']` |
| sendOrgNacClientCoA | auto_increment_with_unique | `['misthelper_internal_id']` | `['org_id', 'client_mac']` |
| sendSiteNacClientCoA | auto_increment_with_unique | `['misthelper_internal_id']` | `['site_id', 'client_mac']` |
| startSiteAutoMapAssignment | auto_increment_with_unique | `['misthelper_internal_id']` | `['site_id']` |
| getSiteAutoMapAssignment | auto_increment_with_unique | `['misthelper_internal_id']` | `['site_id']` |
| deleteOrgSsoAdmins | auto_increment_with_unique | `['misthelper_internal_id']` | `['org_id', 'sso_id']` |
| deleteMspSsoAdmins | auto_increment_with_unique | `['misthelper_internal_id']` | `['msp_id', 'sso_id']` |
| listOrgMxEdgeUpgrades | natural_pk | `['id']` | `['org_id', 'status']` |
| upgradeOrgMxEdges | auto_increment_with_unique | `['misthelper_internal_id']` | `['org_id']` |
| listSiteMxEdgeUpgrades | natural_pk | `['id']` | `['site_id', 'status']` |
| upgradeSiteMxEdges | auto_increment_with_unique | `['misthelper_internal_id']` | `['site_id']` |
