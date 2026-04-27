# Feature Specification: Complete ArangoDB Graph Edge Definitions

**Feature Branch**: `188-graph-edge-definitions`  
**Created**: 2026-04-26  
**Status**: Draft  
**Input**: User description: "Systematically analyze every org-level readonly API endpoint response schema and create complete ArangoDB graph vertex collections and edge definitions"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Traverse Client-to-WLAN Relationships (Priority: P1)

A NOC engineer queries ArangoDB to find all wireless clients connected to a specific SSID. Today, clients and WLANs are stored but not linked by edges, so the engineer must manually correlate `wlan_id` fields. After this feature, the engineer traverses the graph: start at a WLAN vertex, follow `ClientConnectedToWlan` edges, and get all connected clients instantly.

**Why this priority**: Client-to-WLAN is the most frequently asked question in Mist operations ("who's on this SSID?") and demonstrates the core value of graph edges over flat document lookups.

**Independent Test**: Import wireless client data and WLAN data, then run an AQL graph traversal query from a WLAN vertex to verify client edges exist.

**Acceptance Scenarios**:

1. **Given** wireless client documents with `wlan_id` fields are imported, **When** the data is stored in ArangoDB, **Then** `ClientConnectedToWlan` edges link each client to its WLAN vertex.
2. **Given** a WLAN vertex exists in the `wlans` collection, **When** an AQL traversal query starts from that WLAN, **Then** all connected clients are returned without manual field matching.

---

### User Story 2 - Navigate Event and Alarm Relationships (Priority: P2)

A NOC engineer investigates a network incident and needs to see all events and alarms for a specific device or site. Today, events and alarms are stored as flat documents. After this feature, the engineer starts at a device vertex and traverses `EventOccurredOnDevice` and `AlarmTriggeredOnDevice` edges to find all related incidents.

**Why this priority**: Incident investigation is the second most common NOC workflow, and correlating events/alarms to devices/sites is the key bottleneck.

**Independent Test**: Import device event data and alarm data, then run AQL graph traversal from a device vertex and verify event/alarm edges are returned.

**Acceptance Scenarios**:

1. **Given** device event documents with `device_id` and `site_id` fields are imported, **When** stored in ArangoDB, **Then** edges link events to their respective device and site vertices.
2. **Given** alarm documents with `device_id` fields are imported, **When** stored in ArangoDB, **Then** edges link alarms to their respective device vertices.
3. **Given** a device vertex, **When** traversing outbound from the device through event and alarm edges, **Then** all related events and alarms are returned.

---

### User Story 3 - Explore Configuration Hierarchy (Priority: P3)

A NOC engineer needs to understand which templates, profiles, and policies are applied to which sites and devices. After this feature, the engineer can traverse edges like `NetworkBelongsToSite`, `DeviceProfileAppliedToDevice`, `NACRuleUsesNACTag`, and `PSKBelongsToSite` to visualize the full configuration hierarchy.

**Why this priority**: Configuration auditing is a periodic but high-value task. Understanding which config objects apply where prevents misconfiguration.

**Independent Test**: Import network, device profile, NAC rule, and PSK data, then verify edges connect them to their parent sites/devices/tags.

**Acceptance Scenarios**:

1. **Given** network documents with `site_id` fields, **When** stored in ArangoDB, **Then** `NetworkBelongsToSite` edges connect networks to sites.
2. **Given** NAC rule documents referencing NAC tags, **When** stored in ArangoDB, **Then** `NACRuleUsesNACTag` edges connect rules to tags.
3. **Given** PSK documents with `site_id` and `ssid` fields, **When** stored in ArangoDB, **Then** edges connect PSKs to their associated sites and WLANs.

---

### User Story 4 - Full Graph Traversal Across Entity Types (Priority: P4)

A NOC engineer performs a multi-hop traversal: starting from an organization, traversing through sites, to devices, to clients, to WLANs, to templates -- all in a single AQL query. This "six degrees of separation" capability enables complex network topology analysis that was previously impossible without multiple separate queries.

**Why this priority**: This is the ultimate validation that the complete graph is interconnected and traversable end-to-end.

**Independent Test**: After a full data import, run a multi-hop AQL traversal from the org vertex through sites, devices, clients, and WLANs, verifying edges connect all layers.

**Acceptance Scenarios**:

1. **Given** a full data import has completed, **When** running a 4-hop AQL traversal from org to sites to devices to clients, **Then** results include clients at the expected sites.
2. **Given** all edge definitions are registered in the named graph, **When** querying the graph metadata, **Then** all edge collections appear with correct from/to vertex references.

---

### Edge Cases

- What happens when a document references a vertex that hasn't been imported yet (e.g., a client references a `device_id` not in the `devices` collection)? Edge creation must skip gracefully with a debug log.
- What happens when a foreign-key field is null or empty (e.g., `site_id: null`)? No edge should be created.
- What happens when the same edge is imported twice (idempotency)? The second import must upsert, not duplicate.
- What happens when an API endpoint returns data with a foreign-key field pointing to a different org? The edge must not cross org boundaries.
- What happens when a vertex collection doesn't exist at edge creation time? The collection must be auto-created before inserting edges.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST create vertex collections for every distinct entity type returned by org-level API endpoints (networks, services, NAC rules, NAC tags, VPNs, PSKs, alarms, events, audit logs, admins, assets, maps, RF templates, device profiles, webhooks, licenses, gateway templates, security policies, and others identified in the OpenAPI spec).
- **FR-002**: System MUST define edge collections for every foreign-key relationship identified in API response schemas (e.g., `site_id` links to sites, `device_id` links to devices, `wlan_id` links to wlans, `template_id` links to templates).
- **FR-003**: System MUST register all new edge definitions in the `EDGE_DEFINITIONS` list with correct `from_vertex_collections` and `to_vertex_collections`.
- **FR-004**: System MUST add `COLLECTION_VERTEX_MAP` entries for every API endpoint that returns data with foreign-key references, mapping each endpoint to its vertex collection and up to 5 edge definitions per entry.
- **FR-005**: System MUST generate deterministic edge `_key` values derived from the source and target document keys to ensure idempotent upserts.
- **FR-006**: System MUST handle missing target vertices gracefully during edge creation (skip with debug log or create placeholder vertex).
- **FR-007**: System MUST NOT modify or rename any existing vertex collections, edge collections, or edge definitions (backward compatibility).
- **FR-008**: System MUST respect the 5-item rule: no more than 5 edge definitions per `COLLECTION_VERTEX_MAP` entry. Entities with more than 5 relationships must group edges into separate processing batches.
- **FR-009**: System MUST NOT create edges when the foreign-key field value is null, empty, or references a different organization.
- **FR-010**: System MUST register all vertex and edge collections in the ArangoDB named graph `MistHelperGraph`.

### Key Entities

- **Vertex Collections (existing, 10)**: `orgs`, `sites`, `devices`, `clients`, `wlans`, `templates`, `sitegroups`, `mxclusters`, `ports`, `config_snapshots`
- **Vertex Collections (new, to be identified from OpenAPI analysis)**: `networks`, `services`, `nac_rules`, `nac_tags`, `vpns`, `psks`, `alarms`, `events`, `audit_logs`, `admins`, `assets`, `maps`, `rf_templates`, `device_profiles`, `webhooks`, `licenses`, `gateway_templates`, `security_policies`, `wxtags`, `wxrules`, `mxtunnels`, `ap_templates`, `switch_templates`, `network_templates`
- **Edge Collections (existing, ~11)**: `OrgContainsSite`, `OrgContainsDevice`, `SiteContainsDevice`, `ClientConnectedToDevice`, `WlanBelongsToSite`, `WlanUsesTemplate`, `TemplateAssignedToSite`, `SiteBelongsToSiteGroup`, `MxEdgeBelongsToCluster`, `DeviceHasPort`, `ConfigSnapshotForEntity`
- **Edge Collections (new, examples)**: `ClientConnectedToWlan`, `ClientBelongsToSite`, `NetworkBelongsToSite`, `AlarmTriggeredOnDevice`, `AlarmTriggeredAtSite`, `EventOccurredOnDevice`, `EventOccurredAtSite`, `NACRuleUsesNACTag`, `PSKBelongsToSite`, `PSKBelongsToWlan`, `DeviceProfileAppliedToDevice`, `RFTemplateAssignedToSite`, `GatewayTemplateAssignedToSite`, `MapBelongsToSite`, `WebhookBelongsToSite`, `VPNConnectsSite`, `AuditLogByAdmin`, `AssetBelongsToSite`, `LicenseBelongsToOrg`, `ServicePolicyAppliedToSite`

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every org-level API endpoint that returns data containing foreign-key reference fields has at least one corresponding edge definition in `COLLECTION_VERTEX_MAP`.
- **SC-002**: The total number of vertex collections covers all distinct entity types identified in the OpenAPI spec's org-level endpoint response schemas.
- **SC-003**: Graph traversal queries can navigate at least 4 hops across different entity types (org to site to device to client) without encountering missing edge definitions.
- **SC-004**: Re-importing the same dataset produces zero duplicate edges (idempotency verified by stable document counts before and after re-import).
- **SC-005**: The full bulk data collection completes within the existing performance envelope (no more than 10% slowdown from edge creation overhead).
- **SC-006**: All modified source files compile clean with `python -m py_compile`.
- **SC-007**: Existing graph data and edge collections remain intact and functional after the schema additions.

## Assumptions

- The OpenAPI spec at `documentation/mist-api-openapi31json.json` contains accurate response schemas for all org-level endpoints.
- Foreign-key relationships are expressed as fields ending in `_id` (e.g., `site_id`, `device_id`, `wlan_id`, `template_id`) or as array fields containing IDs (e.g., `applies.site_ids`, `device_ids`).
- The `mistapi` Python library function names in `src/org_data_collector.py` map 1:1 to OpenAPI endpoint paths.
- Edge creation during import can be done inline (same write pass) without requiring a separate post-processing step.
- Placeholder vertices (if used for missing targets) will be updated with real data when that entity's endpoint is eventually imported.
