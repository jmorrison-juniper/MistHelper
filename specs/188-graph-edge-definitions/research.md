# Research: Complete ArangoDB Graph Edge Definitions

**Date**: 2026-04-26  
**Spec**: specs/188-graph-edge-definitions/spec.md

## R1: OpenAPI FK Field Catalog

### Decision
Analyzed all 156 org-level collection endpoints (220 total GET paths) from `documentation/mist-api-openapi31json.json`. Identified `_id` / `_ids` foreign-key fields in response schemas for every endpoint.

### Key findings

**List endpoints with FK fields (28 of 64)**:
- `listOrgSites` → `org_id`, `alarmtemplate_id`, `aptemplate_id`, `gatewaytemplate_id`, `networktemplate_id`, `rftemplate_id`, `routertemplate_id`, `secpolicy_id`, `sitegroup_ids`, `sitetemplate_id`
- `getOrgInventory` → `org_id`, `site_id`, `deviceprofile_id`
- `listOrgWlans` → `org_id`, `site_id`, `template_id`, `mxtunnel_id`, `mxtunnel_ids`, `wxtag_ids`, `wxtunnel_id`, `ap_ids`
- `listOrgNetworks` → `org_id`, `vlan_id`
- `listOrgVpns` → `org_id`
- `listOrgServices` → `org_id`
- `listOrgPsks` → `org_id`, `site_id`, `admin_sso_id`
- `listOrgNacRules` → `org_id`, `matching.site_ids`, `matching.sitegroup_ids`
- `listOrgNacTags` → `org_id`, `nacportal_id`
- `listOrgTemplates` → `org_id`, `applies.site_ids`, `applies.sitegroup_ids`, `deviceprofile_ids`
- `listOrgMxEdges` → `org_id`, `site_id`, `mxcluster_id`
- `listOrgMxTunnels` → `org_id`, `site_id`, `anchor_mxtunnel_ids`, `mxcluster_ids`
- `listOrgAssets` → `org_id`, `site_id`, `map_id`, `tag_id`
- `listOrgWebhooks` → `org_id`, `site_id`, `assetfilter_ids`
- `listOrgSiteGroups` → `org_id`, `site_ids`
- `listOrgDeviceProfiles` → `org_id`, `site_id`, `router_id`
- `listOrgWxRules` → `org_id`, `site_id`, `template_id`
- `listOrgWxTags` → `org_id`, `site_id`
- `listOrgAlarmTemplates` → `org_id`
- `listOrgSecPolicies` → `org_id`, `site_id`
- `listOrgMxEdgeClusters` → `org_id`, `site_id`
- `listOrgAAMWProfiles` → `org_id`, `site_id`
- `listOrgAntivirusProfiles` → `org_id`, `site_id`
- `listOrgIdpProfiles` → `org_id`
- `listOrgEvpnTopologies` → `org_id`, `site_id`
- `listOrgGatewayTemplates` → `org_id`, `router_id`
- `listOrgAssetFilters` → `org_id`, `site_id`
- `listOrgGuestAuthorizations` → `wlan_id`

**Search endpoints with FK fields (28 of 36)**:
- `searchOrgWirelessClients` → `mac`, `ap`, `site_id`, `wlan_id`, `psk_id`, `org_id`
- `searchOrgWiredClients` → `mac`, `device_mac`, `site_id`, `port_id`, `org_id`
- `searchOrgWanClients` → `org_id`, `site_id`
- `searchOrgDevices` → `mac`, `site_id`, `org_id`, `evpntopo_id`, `mxedge_id`
- `searchOrgDeviceEvents` → `mac`, `ap`, `site_id`, `org_id`, `audit_id`, `port_id`
- `searchOrgAlarms` → `site_id`, `org_id`, `ack_admin_id`
- `searchOrgNacClients` → `mac`, `ap`, `device_mac`, `site_id`, `nacrule_id`, `org_id`
- `searchOrgNacClientEvents` → `mac`, `ap`, `device_mac`, `site_id`, `nacrule_id`, `mxedge_id`, `org_id`
- `searchOrgMistEdgeEvents` → `mac`, `device_id`, `mxcluster_id`, `mxedge_id`, `org_id`, `audit_id`
- `searchOrgMxEdges` → `mxcluster_id`, `mxedge_id`, `site_id`, `org_id`
- `searchOrgBgpStats` → `mac`, `site_id`, `org_id`
- `searchOrgOspfStats` → `mac`, `site_id`, `port_id`, `org_id`
- `searchOrgSwOrGwPorts` → `mac`, `site_id`, `port_id`, `org_id`
- `searchOrgPeerPathStats` → `mac`, `site_id`, `port_id`, `peer_site_id`, `peer_port_id`, `org_id`
- `searchOrgTunnelsStats` → `mac`, `ap`, `mxcluster_id`, `mxedge_id`, `mxtunnel_id`, `site_id`, `org_id`
- `searchOrgWirelessClientEvents` → `ap`, `wlan_id`
- `searchOrgWirelessClientSessions` → `mac`, `ap`, `site_id`, `wlan_id`, `org_id`
- `searchOrgGuestAuthorization` → `mac`, `wlan_id`
- `searchOrgPskPortalLogs` → `psk_id`, `pskportal_id`, `org_id`

### Rationale
The OpenAPI spec is the single source of truth for FK fields. Manually inspecting response schemas ensures completeness rather than guessing.

### Alternatives considered
- Inspecting live API responses (slower, requires API key, misses optional fields)
- Reading mistapi source code (incomplete, doesn't document response schemas)

---

## R2: Vertex Collection Taxonomy

### Decision
Group all entity types into vertex collections. Use the entity's primary domain concept as the collection name.

**New vertex collections needed (14)**:
1. `networks` — from `listOrgNetworks`
2. `services` — from `listOrgServices`
3. `nac_rules` — from `listOrgNacRules`
4. `nac_tags` — from `listOrgNacTags`
5. `vpns` — from `listOrgVpns`
6. `psks` — from `listOrgPsks`
7. `alarms` — from `searchOrgAlarms`
8. `events` — from `searchOrgDeviceEvents`, `searchOrgWirelessClientEvents`, `searchOrgSystemEvents`, etc.
9. `audit_logs` — from `listOrgAuditLogs`
10. `assets` — from `listOrgAssets`
11. `maps` — from assets' `map_id` refs (stub vertices)
12. `webhooks` — from `listOrgWebhooks`
13. `security_policies` — from `listOrgSecPolicies`, `listOrgServicePolicies`
14. `nac_portals` — from `listOrgNacPortals`

**Existing vertex collections (10, unchanged)**: `orgs`, `sites`, `devices`, `clients`, `wlans`, `templates`, `sitegroups`, `mxclusters`, `ports`, `config_snapshots`

### Rationale
Each vertex collection represents a distinct first-class entity in the Mist API. Merging dissimilar entities (e.g., all events into `events`) keeps the graph navigable. Count-only and metadata endpoints (versions, summaries, counts) do not produce graph-worthy entities.

---

## R3: Edge Definition Design Patterns

### Decision
Three edge creation patterns handle all FK relationship types:

1. **Simple FK** — Record has a scalar `_id` field → single edge (e.g., `site_id` → edge to `sites`)
2. **Array FK** — Record has an array `_ids` field → one edge per array element (e.g., `sitegroup_ids` → N edges to `sitegroups`)
3. **Nested FK** — Record has a nested object with FK fields (e.g., `matching.site_ids`, `applies.site_ids`) → same as array FK but needs dot-path field access

All three patterns already exist in `_build_edges()` — pattern 2 is handled by the `isinstance(to_raw, list)` check. Pattern 3 requires adding dot-path field resolution.

### Rationale
Reusing the existing `_build_edges()` with minimal extension (dot-path support) avoids code duplication and keeps the edge-building logic centralized.

---

## R4: Endpoints Excluded from Graph Mapping

### Decision
The following operation types do NOT need `COLLECTION_VERTEX_MAP` entries:

- **Count operations** (31 total) — Return aggregate counts, no entities
- **Get single-object operations** (6 total) — `getOrg`, `getOrgStats`, `getOrgSettings`, etc. — org-level singletons already in `orgs` vertex
- **Metadata/version operations** — `listOrgAvailableDeviceVersions`, `listOrgAvailableSsrVersions`, `listOrgDeviceUpgrades`, `listOrgSsrUpgrades`, `listOrgMxEdgeUpgrades`, `listOrgApsMacs`, `listOrgDevicesSummary` — reference data, not first-class entities
- **SDK/invite operations** — `listSdkInvites`, `listSdkTemplates`, `listOrgMarvisClientInvites` — rarely used, no meaningful graph relationships
- **Log/portal operations** — `listOrgPskPortalLogs`, `searchOrgPskPortalLogs` — high-volume time-series, better in Redis
- **JSI operations** — `searchOrgJsiPbn`, `searchOrgJsiSirt`, `searchOrgJsiAssetsAndContracts`, `listOrgJsiDevices` — Juniper Support Insights, tangential to network topology
- **Misc** — `getOrgCapturingStatus`, `getOrgApplicationList`, `listOrgUiSettings`, `listOrgPmaDashboards`, `listOrgIssuedClientCertificates`, `listOrgCertificates`, `searchOrgVars`, `searchOrgDeviceLastConfigs`

### Rationale
Graph edges are only valuable for entities that participate in navigable relationships. Aggregate counts, version lists, and transient logs add noise without navigation value.

---

## R5: Idempotent Edge Key Strategy

### Decision
Continue using the existing `_edge_key()` pattern: SHA-256 hash of `"{from_id}:{to_id}"` truncated to 16 hex chars. This ensures:
- Same FK relationship always produces the same `_key`
- Re-import replaces (not duplicates) via `on_duplicate="replace"`
- No collision risk at 16 hex chars (64-bit space) for expected data volumes

### Rationale
Already proven in production with existing edges. No change needed.

---

## R6: 5-Item Rule Compliance for COLLECTION_VERTEX_MAP

### Decision
Each `COLLECTION_VERTEX_MAP` entry is limited to 5 edge definitions per the constitution's 5-item rule. Entities with more than 5 FK relationships will process edges in separate batches by splitting the `edges` list.

For example, `listOrgWlans` has FK fields: `site_id`, `template_id`, `mxtunnel_id`, `wxtag_ids`, `ap_ids` = exactly 5 edges. If more are added, split into a second processing pass.

### Rationale
Constitution Principle I (Five-Item Rule) explicitly caps children at 5 per level. Edge configs are children of a COLLECTION_VERTEX_MAP entry.
