# Feature Specification: Complete ArangoDB Graph Edge Coverage

**Feature Branch**: `feat/169-complete-edge-coverage`  
**Created**: 2026-04-27  
**Status**: Draft  
**Input**: GitHub Issue #169 - Complete ArangoDB graph edge coverage for all org-level endpoints

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Core Entity Relationships (Priority: P1)

A network operator runs MistHelper's "Collect All Org Data" operation (Menu 165), which populates ArangoDB with org-level data. When they query the graph, they can traverse from any high-value entity (device, PSK, alarm, MxCluster, NAC portal, MxTunnel, guest, audit log) to its related entities via graph edges. For example: "Show me all alarms for device X", "Which WLANs use this PSK?", "Which sites does this alarm template cover?"

**Why this priority**: These 7 missing Tier 1 edges represent the highest-value relationships that network operators need for day-to-day troubleshooting. Without them, the graph has blind spots in the most commonly queried paths.

**Independent Test**: Can be fully tested by running Menu 165 against a Mist org, then executing AQL traversal queries to verify edges exist between entities.

**Acceptance Scenarios**:

1. **Given** org data is collected via Menu 165, **When** a site has an alarmtemplate_id, **Then** an `AlarmTemplateAssignedToSite` edge exists linking the alarm template to the site (already partially implemented -- verify `SiteUsesAlarmTemplate` exists or equivalent)
2. **Given** org data is collected, **When** a PSK has a wlan_id, **Then** a `PSKBelongsToWlan` edge links the PSK to its WLAN
3. **Given** org data is collected, **When** an alarm has a device_id, **Then** an `AlarmOnDevice` edge links the alarm to the device
4. **Given** org data is collected, **When** an MxCluster has a site_id, **Then** an `MxClusterBelongsToSite` edge exists (requires new edge definition)
5. **Given** org data is collected, **When** a NAC portal has sitegroup_ids, **Then** `NacPortalServesSiteGroup` edges link the portal to each site group
6. **Given** org data is collected, **When** an MxTunnel has mxcluster_ids, **Then** `MxTunnelUsesCluster` edges link the tunnel to each cluster
7. **Given** org data is collected, **When** a guest authorization has a wlan_id, **Then** a `GuestAuthorizedOnWlan` edge links the guest to the WLAN

---

### User Story 2 - Event/Search Entity Traversals (Priority: P2)

A NOC engineer investigating a client connectivity issue queries the graph for all events related to a specific site or device. The graph contains edges linking WAN client events, client events, sessions, NAC events, and MxEdge events to their respective sites and devices, enabling multi-hop traversal from site -> events -> devices.

**Why this priority**: Event correlation across entities is the second-most common graph query pattern. Without these edges, operators cannot traverse from a site to all its related events in a single query.

**Independent Test**: Run Menu 165, then query AQL: `FOR v, e IN 1..2 OUTBOUND 'sites/<site_id>' GRAPH 'mist_graph' FILTER IS_SAME_COLLECTION(e, 'ClientEventBelongsToSite') OR IS_SAME_COLLECTION(e, 'SessionBelongsToSite') RETURN v`

**Acceptance Scenarios**:

1. **Given** org data is collected, **When** client events have site_id and device_mac fields, **Then** `ClientEventBelongsToSite` and `ClientEventOnDevice` edges exist
2. **Given** org data is collected, **When** client sessions have site_id, wlan_id, and device_mac, **Then** `SessionBelongsToSite`, `SessionOnWlan`, and `SessionOnDevice` edges exist
3. **Given** org data is collected, **When** NAC/WAN/MxEdge events have site_id, **Then** corresponding `*BelongsToSite` edges exist
4. **Given** org data is collected, **When** sessions and NAC/WAN events reference client MACs, **Then** `SessionForClient`, `NacEventForClient`, `WanEventForClient` edges exist

---

### User Story 3 - Stats/Telemetry Graph Traversal (Priority: P3)

A network capacity planner queries the graph to correlate device statistics, BGP/OSPF neighbor data, peer paths, port utilization, and tunnel metrics with their owning sites and devices. This enables queries like "Show me all BGP stats for devices in site X" via graph traversal.

**Why this priority**: Telemetry edges enable capacity planning and trend analysis workflows. These are read-heavy, analytics-oriented queries.

**Independent Test**: After Menu 165 collection, verify that `DeviceStatsBelongsToSite`, `BgpStatsBelongsToSite`, `PortBelongsToDevice` edges exist by running AQL traversals from a known site vertex.

**Acceptance Scenarios**:

1. **Given** device stats are collected, **When** stats have site_id and mac fields, **Then** `DeviceStatsBelongsToSite` and `DeviceStatsForDevice` edges exist
2. **Given** BGP/OSPF stats are collected, **When** stats have site_id, **Then** `BgpStatsBelongsToSite` and `OspfStatsBelongsToSite` edges exist
3. **Given** port data is collected, **When** ports have site_id and device_mac, **Then** `PortBelongsToSite` and `PortBelongsToDevice` edges exist
4. **Given** tunnel/peer path data is collected, **When** data has site_id, **Then** `TunnelBelongsToSite` and `PeerPathBelongsToSite` edges exist

---

### User Story 4 - WxLAN Policy Graph (Priority: P3)

A wireless policy administrator queries the graph to understand WxLAN rule relationships: which rules belong to which templates, which WxTags are used as source/destination allow/deny filters. This enables policy audit and impact analysis.

**Why this priority**: WxLAN policy edges are important for policy auditing but are queried less frequently than entity or event edges.

**Independent Test**: After collecting WxRule and WxTag data, verify `WxRuleBelongsToTemplate`, `WxRuleMatchesSrcTag`, `WxRuleAllowsDstTag`, `WxRuleDeniesDstTag` edges exist.

**Acceptance Scenarios**:

1. **Given** WxRules are collected, **When** a rule has a template_id, **Then** a `WxRuleBelongsToTemplate` edge links it to the template
2. **Given** WxRules are collected, **When** a rule has src_wxtags, **Then** `WxRuleMatchesSrcTag` edges link it to each source tag
3. **Given** WxRules are collected, **When** a rule has dst_allow_wxtags/dst_deny_wxtags, **Then** `WxRuleAllowsDstTag`/`WxRuleDeniesDstTag` edges link it to destination tags

---

### User Story 5 - Unmapped Entity Vertex Coverage (Priority: P4)

All remaining org-level API endpoints (admins, API tokens, licenses, EVPN topologies, tickets, packet captures, etc.) have proper COLLECTION_VERTEX_MAP entries so their data lands in named vertex collections rather than a generic bucket. Where foreign key fields exist (e.g., site_id on tickets), edges are also created.

**Why this priority**: Completeness. These entities are queried less frequently but having them properly mapped ensures the graph is a complete representation of the org topology.

**Independent Test**: After Menu 165, verify that every API endpoint collected has data in a named vertex collection (not dropped), and that entities with site_id or other FK fields have corresponding edges.

**Acceptance Scenarios**:

1. **Given** ticket data is collected, **When** tickets have site_id, **Then** `TicketBelongsToSite` edges exist
2. **Given** packet capture data is collected, **When** captures have site_id, **Then** `PacketCaptureBelongsToSite` edges exist
3. **Given** EVPN topology data is collected, **When** topologies have site_id, **Then** `EvpnBelongsToSite` edges exist
4. **Given** other device data is collected, **When** entries have site_id, **Then** `OtherDeviceBelongsToSite` edges exist

---

### User Story 6 - Template Name Bug Fix (Priority: P1)

The COLLECTION_VERTEX_MAP and ENTITY_TYPE_TO_VERTEX dictionaries use consistent API function names that match what org_data_collector.py actually calls. If `listOrgWlanTemplates` was used but the collector calls `listOrgTemplates`, the mismatch means template edges never populate.

**Why this priority**: This is a correctness bug that silently prevents edges from being created. It must be fixed alongside edge additions.

**Independent Test**: After Menu 165, verify that WLAN template data ends up in the `templates` vertex collection and that `TemplateAssignedToSite` / `WlanUsesTemplate` edges exist.

**Acceptance Scenarios**:

1. **Given** the COLLECTION_VERTEX_MAP contains a key for the templates API function, **When** org_data_collector.py calls that function, **Then** the function name matches exactly
2. **Given** template data is collected, **When** templates have site assignment fields, **Then** `TemplateAssignedToSite` edges are created

---

### Edge Cases

- What happens when a foreign key field is null or missing from the API response? (Edge should not be created; no crash)
- What happens when a foreign key references an entity not yet collected? (`_ensure_target_vertices` should create a stub vertex)
- What happens when a multi-value FK field (like `sitegroup_ids`) contains an empty list? (No edges created; no crash)
- What happens when an entity has a self-referential FK (e.g., `connected_device_id` on devices)? (Edge should connect device to device correctly)
- What happens when the graph is recreated after adding new edge definitions? (Existing data preserved; new edge definitions added)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST create `MxClusterBelongsToSite` edges linking MxClusters to their sites via `site_id`
- **FR-002**: System MUST create edges for all Tier 2 event entities (client events, sessions, NAC events, WAN events, MxEdge events) linking them to sites and devices
- **FR-003**: System MUST create edges for all Tier 3 stats entities (device stats, BGP stats, OSPF stats, peer paths, ports, tunnels, MxEdge stats) linking them to sites and devices
- **FR-004**: System MUST create edges for Tier 4 WxLAN policy relationships (WxRules to templates, WxRules to source/destination WxTags)
- **FR-005**: System MUST have COLLECTION_VERTEX_MAP entries for all Tier 5 entities (tickets, packet captures, EVPN topologies, other devices, alarm templates, device profiles) with edges where FK fields exist
- **FR-006**: System MUST use API function names in COLLECTION_VERTEX_MAP and ENTITY_TYPE_TO_VERTEX that exactly match the function names used by org_data_collector.py
- **FR-007**: System MUST gracefully handle null, missing, or empty FK fields without creating invalid edges or raising exceptions
- **FR-008**: System MUST use `_ensure_target_vertices` to create stub vertices for FK targets not yet collected
- **FR-009**: All new edge definitions MUST have corresponding entries in EDGE_DEFINITIONS, COLLECTION_VERTEX_MAP, and (where applicable) ENTITY_TYPE_TO_VERTEX
- **FR-010**: System MUST maintain backward compatibility with existing edge definitions and graph data

### Key Entities

- **Edge Definition**: A graph schema declaration specifying an edge collection name, source vertex collections, and target vertex collections. Lives in the `EDGE_DEFINITIONS` list.
- **Collection Vertex Map Entry**: A mapping from an API function name to its vertex collection, key field, edge creation rules, and target vertex stubs. Lives in `COLLECTION_VERTEX_MAP`.
- **Entity Type to Vertex**: A mapping from an API function name to its vertex collection name, used by the snapshot system. Lives in `ENTITY_TYPE_TO_VERTEX`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All Tier 1 edges (7 remaining + verify 3 existing) are fully functional -- verified by unit tests creating sample documents and checking edge existence
- **SC-002**: All Tier 2 event edges (~11 edges) are fully functional -- each event type's COLLECTION_VERTEX_MAP entry includes edge definitions for site_id and device_mac/mac references
- **SC-003**: All Tier 3 stats edges (~9 edges) are fully functional -- stats entities link to sites and devices via graph edges
- **SC-004**: All Tier 4 WxLAN edges (4 edges) are fully functional -- WxRules link to templates and WxTags
- **SC-005**: All Tier 5 entities have proper vertex collection mappings -- no org-level data falls into an unmapped bucket
- **SC-006**: Template name mismatch is verified fixed -- COLLECTION_VERTEX_MAP keys match org_data_collector.py function calls exactly
- **SC-007**: Unit test coverage for arango_writer.py edge-related code is at or above 90%
- **SC-008**: All existing tests continue to pass with no regressions
- **SC-009**: Graph traversal queries from any site can reach all related entities within 2 hops (verified by integration test)

## Current State Analysis

### What Already Exists (as of 2026-04-27)

**EDGE_DEFINITIONS**: The file contains ~60 unique edge definitions spanning:
- Org/site/device containment hierarchy (3 edges)
- Template and WLAN relationships (5 edges)
- Client connections (3 edges)
- Config snapshots (1 edge with many target collections)
- Org-level ownership (3 edges)
- Events and alarms (3 edges)
- NAC/security (4 edges)
- Assets and config (5 edges)
- Tier 1 relationships (8 edges) -- DeviceUsesProfile, PSKBelongsToWlan, AlarmOnDevice, NacPortalServesSiteGroup, MxTunnelUsesCluster, AuditLogBelongsToSite, GuestBelongsToSite, GuestAuthorizedOnWlan
- Tier 2 event edges (11 edges)
- Tier 3 stats edges (9 edges)
- Tier 4 WxLAN edges (4 edges)
- Tier 5 entity edges (4 edges)
- Additional relationship edges (9 edges)

**ENTITY_TYPE_TO_VERTEX**: 39 entries mapping API functions to vertex collections.

**COLLECTION_VERTEX_MAP**: Partial coverage -- some entries have full edge definitions, others are vertex-only with no edge rules.

### What's Missing

1. **MxClusterBelongsToSite**: Edge definition exists but no COLLECTION_VERTEX_MAP entry for `listOrgMxEdgeClusters` with this edge
2. **COLLECTION_VERTEX_MAP completeness**: Many API functions have ENTITY_TYPE_TO_VERTEX entries but no COLLECTION_VERTEX_MAP entries with edge rules
3. **Template name verification**: Need to confirm `listOrgTemplates` vs `listOrgWlanTemplates` alignment
4. **Tier 2-5 COLLECTION_VERTEX_MAP entries**: Edge definitions exist in EDGE_DEFINITIONS but corresponding COLLECTION_VERTEX_MAP entries may lack `edges` arrays to actually create the edges at write time

## Assumptions

- The existing EDGE_DEFINITIONS list structure is correct and will not change format
- All FK field names (site_id, device_id, wlan_id, etc.) follow the Mist API naming conventions consistently
- The `_ensure_target_vertices` mechanism is the correct approach for handling forward references
- Multi-value FK fields (arrays like `sitegroup_ids`, `mxcluster_ids`) are handled by iterating and creating one edge per value
- The `mac` field on devices serves as both a natural key and a FK target (via `to_key_lookup: "mac"`)
- No new vertex collections need to be created -- all target collections are already declared in EDGE_DEFINITIONS
