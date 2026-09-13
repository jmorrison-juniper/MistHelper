# Tasks: Complete ArangoDB Graph Edge Definitions

**Input**: Design documents from `/specs/188-graph-edge-definitions/`
**Prerequisites**: plan.md, spec.md, data-model.md, research.md, quickstart.md
**Target File**: `src/db/arango_writer.py` (single-file change)
**Tests**: Not requested — verification via `py_compile` and `--menu 165` runs

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (N/A for this feature — all edits target one file)
- **[Story]**: US1=Client-to-WLAN, US2=Events/Alarms, US3=Config Hierarchy, US4=Full Traversal

---

## Phase 1: Setup

**Purpose**: No new project structure needed — all changes are additions to existing constants and one new method in `src/db/arango_writer.py`.

*No tasks in this phase.*

---

## Phase 2: Foundational (Edge Definitions + Nested Field Support)

**Purpose**: Register all 20 new edge collections in `EDGE_DEFINITIONS` and add dot-path FK resolution. ALL user stories depend on these edge definitions existing before `COLLECTION_VERTEX_MAP` entries can reference them.

**CRITICAL**: No user story work can begin until this phase is complete.

### Edge Definitions (append to `EDGE_DEFINITIONS` list starting at line 27)

- [ ] T001 Add edge definitions batch 1a — core entity relationships (5 edges) in src/db/arango_writer.py

  Append these 5 entries to the `EDGE_DEFINITIONS` list after the existing `ConfigSnapshotForEntity` entry (line ~86):
  ```python
  {"edge_collection": "ClientConnectedToWlan", "from_vertex_collections": ["clients"], "to_vertex_collections": ["wlans"]},
  {"edge_collection": "ClientBelongsToSite", "from_vertex_collections": ["clients"], "to_vertex_collections": ["sites"]},
  {"edge_collection": "NetworkBelongsToOrg", "from_vertex_collections": ["networks"], "to_vertex_collections": ["orgs"]},
  {"edge_collection": "ServiceBelongsToOrg", "from_vertex_collections": ["services"], "to_vertex_collections": ["orgs"]},
  {"edge_collection": "VpnBelongsToOrg", "from_vertex_collections": ["vpns"], "to_vertex_collections": ["orgs"]},
  ```
  **Acceptance**: `python -m py_compile src/db/arango_writer.py` passes. `EDGE_DEFINITIONS` list has 16 entries (was 11).

- [ ] T002 Add edge definitions batch 1b — events and alarms (3 edges) in src/db/arango_writer.py

  Append after batch 1a:
  ```python
  {"edge_collection": "AlarmBelongsToSite", "from_vertex_collections": ["alarms"], "to_vertex_collections": ["sites"]},
  {"edge_collection": "EventBelongsToSite", "from_vertex_collections": ["events"], "to_vertex_collections": ["sites"]},
  {"edge_collection": "EventOccurredOnDevice", "from_vertex_collections": ["events"], "to_vertex_collections": ["devices"]},
  ```
  **Acceptance**: `EDGE_DEFINITIONS` list has 19 entries. `py_compile` passes.

- [ ] T003 Add edge definitions batch 1c — security and NAC (4 edges) in src/db/arango_writer.py

  Append after batch 1b:
  ```python
  {"edge_collection": "NACRuleMatchesSite", "from_vertex_collections": ["nac_rules"], "to_vertex_collections": ["sites"]},
  {"edge_collection": "NACRuleMatchesSiteGroup", "from_vertex_collections": ["nac_rules"], "to_vertex_collections": ["sitegroups"]},
  {"edge_collection": "NACTagBelongsToPortal", "from_vertex_collections": ["nac_tags"], "to_vertex_collections": ["nac_portals"]},
  {"edge_collection": "SecurityPolicyBelongsToOrg", "from_vertex_collections": ["security_policies"], "to_vertex_collections": ["orgs"]},
  ```
  **Acceptance**: `EDGE_DEFINITIONS` list has 23 entries. `py_compile` passes.

- [ ] T004 Add edge definitions batch 1d — assets and config (5 edges) in src/db/arango_writer.py

  Append after batch 1c:
  ```python
  {"edge_collection": "PSKBelongsToSite", "from_vertex_collections": ["psks"], "to_vertex_collections": ["sites"]},
  {"edge_collection": "AssetBelongsToSite", "from_vertex_collections": ["assets"], "to_vertex_collections": ["sites"]},
  {"edge_collection": "AssetOnMap", "from_vertex_collections": ["assets"], "to_vertex_collections": ["maps"]},
  {"edge_collection": "WebhookBelongsToSite", "from_vertex_collections": ["webhooks"], "to_vertex_collections": ["sites"]},
  {"edge_collection": "SiteGroupContainsSite", "from_vertex_collections": ["sitegroups"], "to_vertex_collections": ["sites"]},
  ```
  **Acceptance**: `EDGE_DEFINITIONS` list has 28 entries. `py_compile` passes.

- [ ] T005 Add edge definitions batch 1e — WLAN and template relationships (3 edges) in src/db/arango_writer.py

  Append after batch 1d:
  ```python
  {"edge_collection": "WlanUsesMxTunnel", "from_vertex_collections": ["wlans"], "to_vertex_collections": ["devices"]},
  {"edge_collection": "TemplateAppliedToSite", "from_vertex_collections": ["templates"], "to_vertex_collections": ["sites"]},
  {"edge_collection": "TemplateAppliedToSiteGroup", "from_vertex_collections": ["templates"], "to_vertex_collections": ["sitegroups"]},
  ```
  **Acceptance**: `EDGE_DEFINITIONS` list has 31 total entries (11 existing + 20 new). `py_compile` passes.

### Nested FK Field Support

- [ ] T006 Add `_resolve_nested_field()` static method to `ArangoDBWriter` class in src/db/arango_writer.py

  Add this method to the `ArangoDBWriter` class (after `_edge_key()` or before `_build_edges()`):
  ```python
  @staticmethod
  def _resolve_nested_field(record: dict, field_path: str) -> Any:
      """Resolve dot-separated field paths (e.g., 'matching.site_ids')."""
      parts = field_path.split(".")
      value = record
      for part in parts:
          if isinstance(value, dict):
              value = value.get(part)
          else:
              return None
      return value
  ```
  **Acceptance**: `py_compile` passes. Method is callable as `ArangoDBWriter._resolve_nested_field({"matching": {"site_ids": ["a"]}}, "matching.site_ids")` → `["a"]`.

- [ ] T007 Update `_build_edges()` to use `_resolve_nested_field()` for dot-path fields in src/db/arango_writer.py

  In `_build_edges()` (line ~430), replace the two `record.get()` calls for `from_field`/`to_field` with dot-path-aware logic:
  ```python
  # Before (line ~430-431):
  from_value = record.get(from_field)
  to_raw = record.get(to_field)

  # After:
  from_value = (
      self._resolve_nested_field(record, from_field)
      if "." in from_field
      else record.get(from_field)
  )
  to_raw = (
      self._resolve_nested_field(record, to_field)
      if "." in to_field
      else record.get(to_field)
  )
  ```
  **Acceptance**: `py_compile` passes. Dot-path fields like `matching.site_ids` are resolved correctly. Non-dot fields (existing behavior) are unchanged.

- [ ] T008 Compile validation checkpoint for Phase 2 foundation

  Run: `python -m py_compile src/db/arango_writer.py`
  **Acceptance**: Zero errors. `EDGE_DEFINITIONS` has 31 entries. `_resolve_nested_field()` exists. `_build_edges()` handles dot-paths.

**Checkpoint**: Foundation ready — all 20 new edge definitions registered, dot-path FK support in place. User story implementation can now begin.

---

## Phase 3: User Story 1 — Traverse Client-to-WLAN Relationships (Priority: P1) MVP

**Goal**: Enable AQL traversal from a WLAN vertex to find all connected wireless clients, and from clients to their site.

**Independent Test**: After `--menu 165`, run AQL: `FOR wlan IN wlans FOR client IN 1..1 INBOUND wlan ClientConnectedToWlan LIMIT 5 RETURN {ssid: wlan.ssid, mac: client.mac}` — should return results.

### Implementation for User Story 1

- [ ] T009 [US1] Update existing `searchOrgWirelessClients` entry in `COLLECTION_VERTEX_MAP` to add `ClientConnectedToWlan` and `ClientBelongsToSite` edges in src/db/arango_writer.py

  The existing entry (line ~171) has 1 edge (`ClientConnectedToDevice`). Add 2 more edges to its `edges` list:
  ```python
  {
      "edge_col": "ClientConnectedToWlan",
      "from_col": "clients",
      "from_field": "mac",
      "to_col": "wlans",
      "to_field": "wlan_id",
  },
  {
      "edge_col": "ClientBelongsToSite",
      "from_col": "clients",
      "from_field": "mac",
      "to_col": "sites",
      "to_field": "site_id",
  },
  ```
  **Acceptance**: Entry has 3 edges total (≤5 limit). `py_compile` passes.

- [ ] T010 [US1] Update existing `searchOrgWiredClients` entry in `COLLECTION_VERTEX_MAP` to add `ClientBelongsToSite` edge in src/db/arango_writer.py

  The existing entry (line ~158) has 1 edge (`ClientConnectedToDevice`). Add:
  ```python
  {
      "edge_col": "ClientBelongsToSite",
      "from_col": "clients",
      "from_field": "mac",
      "to_col": "sites",
      "to_field": "site_id",
  },
  ```
  **Acceptance**: Entry has 2 edges total. `py_compile` passes.

- [ ] T011 [US1] Add `COLLECTION_VERTEX_MAP` entry for `searchOrgNacClients` in src/db/arango_writer.py

  Add new entry to `COLLECTION_VERTEX_MAP`:
  ```python
  "searchOrgNacClients": {
      "vertex": "clients",
      "key_field": "mac",
      "edges": [
          {
              "edge_col": "ClientConnectedToDevice",
              "from_col": "clients",
              "from_field": "mac",
              "to_col": "devices",
              "to_field": "device_mac",
              "to_key_lookup": "mac",
          },
          {
              "edge_col": "ClientBelongsToSite",
              "from_col": "clients",
              "from_field": "mac",
              "to_col": "sites",
              "to_field": "site_id",
          },
      ],
  },
  ```
  **Acceptance**: New entry exists with 2 edges. `py_compile` passes.

- [ ] T012 [US1] Update existing `listOrgWlans` entry in `COLLECTION_VERTEX_MAP` to add `WlanUsesMxTunnel` edge in src/db/arango_writer.py

  The existing entry (line ~189) has 2 edges (`WlanBelongsToSite`, `WlanUsesTemplate`). Add:
  ```python
  {
      "edge_col": "WlanUsesMxTunnel",
      "from_col": "wlans",
      "from_field": "id",
      "to_col": "devices",
      "to_field": "mxtunnel_id",
  },
  ```
  **Acceptance**: Entry has 3 edges total (≤5 limit). `py_compile` passes.

- [ ] T013 [US1] Compile and verify client-to-WLAN traversal

  Run:
  1. `python -m py_compile src/db/arango_writer.py`
  2. If ArangoDB is available: `python MistHelper.py --menu 165` then verify AQL traversal:
     ```aql
     FOR wlan IN wlans
       FILTER wlan.ssid != null
       FOR client IN 1..1 INBOUND wlan ClientConnectedToWlan
         LIMIT 5
         RETURN {ssid: wlan.ssid, client_mac: client.mac}
     ```
  **Acceptance**: Compile passes. If data exists, traversal returns client-WLAN pairs.

**Checkpoint**: User Story 1 complete — clients are linked to WLANs and sites via graph edges.

---

## Phase 4: User Story 2 — Navigate Event and Alarm Relationships (Priority: P2)

**Goal**: Enable AQL traversal from a device vertex to find all related events and alarms.

**Independent Test**: After `--menu 165`, run AQL: `FOR device IN devices FOR event IN 1..1 INBOUND device EventOccurredOnDevice LIMIT 5 RETURN {device: device.name, event_type: event.type}` — should return results.

### Implementation for User Story 2

- [ ] T014 [US2] Add `COLLECTION_VERTEX_MAP` entry for `searchOrgAlarms` in src/db/arango_writer.py

  Add new entry:
  ```python
  "searchOrgAlarms": {
      "vertex": "alarms",
      "key_field": "id",
      "edges": [
          {
              "edge_col": "AlarmBelongsToSite",
              "from_col": "alarms",
              "from_field": "id",
              "to_col": "sites",
              "to_field": "site_id",
          },
      ],
  },
  ```
  **Acceptance**: New entry with 1 edge. `py_compile` passes.

- [ ] T015 [US2] Add `COLLECTION_VERTEX_MAP` entry for `searchOrgDeviceEvents` in src/db/arango_writer.py

  Add new entry:
  ```python
  "searchOrgDeviceEvents": {
      "vertex": "events",
      "key_field": "id",
      "edges": [
          {
              "edge_col": "EventBelongsToSite",
              "from_col": "events",
              "from_field": "id",
              "to_col": "sites",
              "to_field": "site_id",
          },
          {
              "edge_col": "EventOccurredOnDevice",
              "from_col": "events",
              "from_field": "id",
              "to_col": "devices",
              "to_field": "mac",
              "to_key_lookup": "mac",
          },
      ],
  },
  ```
  **Acceptance**: New entry with 2 edges. `py_compile` passes.

- [ ] T016 [US2] Compile and verify device-to-events traversal

  Run:
  1. `python -m py_compile src/db/arango_writer.py`
  2. If ArangoDB is available: verify AQL traversal:
     ```aql
     FOR device IN devices
       LIMIT 1
       FOR event IN 1..1 INBOUND device EventOccurredOnDevice
         LIMIT 5
         RETURN {device: device.name, event_type: event.type}
     ```
  **Acceptance**: Compile passes. If data exists, traversal returns device-event pairs.

**Checkpoint**: User Story 2 complete — events and alarms are linked to devices and sites.

---

## Phase 5: User Story 3 — Explore Configuration Hierarchy (Priority: P3)

**Goal**: Enable traversal of configuration objects (networks, NAC rules, PSKs, templates, security policies) to their parent sites, orgs, and related entities.

**Independent Test**: After `--menu 165`, run AQL: `FOR rule IN nac_rules FOR site IN 1..1 OUTBOUND rule NACRuleMatchesSite RETURN {rule: rule.name, site: site.name}` — should return results.

### Implementation for User Story 3

- [ ] T017 [US3] Add `COLLECTION_VERTEX_MAP` entries for `listOrgNetworks`, `listOrgServices`, `listOrgVpns` in src/db/arango_writer.py

  Add 3 new entries (org-level entities with simple `org_id` FK):
  ```python
  "listOrgNetworks": {
      "vertex": "networks",
      "key_field": "id",
      "edges": [
          {"edge_col": "NetworkBelongsToOrg", "from_col": "networks", "from_field": "id", "to_col": "orgs", "to_field": "org_id"},
      ],
  },
  "listOrgServices": {
      "vertex": "services",
      "key_field": "id",
      "edges": [
          {"edge_col": "ServiceBelongsToOrg", "from_col": "services", "from_field": "id", "to_col": "orgs", "to_field": "org_id"},
      ],
  },
  "listOrgVpns": {
      "vertex": "vpns",
      "key_field": "id",
      "edges": [
          {"edge_col": "VpnBelongsToOrg", "from_col": "vpns", "from_field": "id", "to_col": "orgs", "to_field": "org_id"},
      ],
  },
  ```
  **Acceptance**: 3 new entries, each with 1 edge. `py_compile` passes.

- [ ] T018 [US3] Add `COLLECTION_VERTEX_MAP` entries for `listOrgNacRules` and `listOrgNacTags` in src/db/arango_writer.py

  Add 2 new entries (security domain with nested FK fields):
  ```python
  "listOrgNacRules": {
      "vertex": "nac_rules",
      "key_field": "id",
      "edges": [
          {"edge_col": "NACRuleMatchesSite", "from_col": "nac_rules", "from_field": "id", "to_col": "sites", "to_field": "matching.site_ids"},
          {"edge_col": "NACRuleMatchesSiteGroup", "from_col": "nac_rules", "from_field": "id", "to_col": "sitegroups", "to_field": "matching.sitegroup_ids"},
      ],
  },
  "listOrgNacTags": {
      "vertex": "nac_tags",
      "key_field": "id",
      "edges": [
          {"edge_col": "NACTagBelongsToPortal", "from_col": "nac_tags", "from_field": "id", "to_col": "nac_portals", "to_field": "nacportal_id"},
      ],
      "ensure_target_vertices": [("nacportal_id", "nac_portals")],
  },
  ```
  **Note**: `listOrgNacRules` uses dot-path FK fields (`matching.site_ids`, `matching.sitegroup_ids`) which require the `_resolve_nested_field()` added in T006/T007.
  **Acceptance**: 2 new entries. NAC rules entry uses dot-path FK fields. `py_compile` passes.

- [ ] T019 [US3] Add `COLLECTION_VERTEX_MAP` entries for `listOrgSecPolicies` and `listOrgServicePolicies` in src/db/arango_writer.py

  Add 2 new entries (both map to `security_policies` vertex):
  ```python
  "listOrgSecPolicies": {
      "vertex": "security_policies",
      "key_field": "id",
      "edges": [
          {"edge_col": "SecurityPolicyBelongsToOrg", "from_col": "security_policies", "from_field": "id", "to_col": "orgs", "to_field": "org_id"},
      ],
  },
  "listOrgServicePolicies": {
      "vertex": "security_policies",
      "key_field": "id",
      "edges": [
          {"edge_col": "SecurityPolicyBelongsToOrg", "from_col": "security_policies", "from_field": "id", "to_col": "orgs", "to_field": "org_id"},
      ],
  },
  ```
  **Acceptance**: 2 new entries sharing the same vertex collection. `py_compile` passes.

- [ ] T020 [US3] Add `COLLECTION_VERTEX_MAP` entries for `listOrgPsks` and `listOrgAssets` in src/db/arango_writer.py

  Add 2 new entries (site-level FK entities):
  ```python
  "listOrgPsks": {
      "vertex": "psks",
      "key_field": "id",
      "edges": [
          {"edge_col": "PSKBelongsToSite", "from_col": "psks", "from_field": "id", "to_col": "sites", "to_field": "site_id"},
      ],
  },
  "listOrgAssets": {
      "vertex": "assets",
      "key_field": "id",
      "edges": [
          {"edge_col": "AssetBelongsToSite", "from_col": "assets", "from_field": "id", "to_col": "sites", "to_field": "site_id"},
          {"edge_col": "AssetOnMap", "from_col": "assets", "from_field": "id", "to_col": "maps", "to_field": "map_id"},
      ],
      "ensure_target_vertices": [("map_id", "maps")],
  },
  ```
  **Acceptance**: 2 new entries. Assets entry has `ensure_target_vertices` for maps stubs. `py_compile` passes.

- [ ] T021 [US3] Add `COLLECTION_VERTEX_MAP` entries for `listOrgWebhooks` and `listOrgSiteGroups` in src/db/arango_writer.py

  Add 2 new entries:
  ```python
  "listOrgWebhooks": {
      "vertex": "webhooks",
      "key_field": "id",
      "edges": [
          {"edge_col": "WebhookBelongsToSite", "from_col": "webhooks", "from_field": "id", "to_col": "sites", "to_field": "site_id"},
      ],
  },
  "listOrgSiteGroups": {
      "vertex": "sitegroups",
      "key_field": "id",
      "edges": [
          {"edge_col": "SiteGroupContainsSite", "from_col": "sitegroups", "from_field": "id", "to_col": "sites", "to_field": "site_ids"},
      ],
  },
  ```
  **Note**: `listOrgSiteGroups` is a new entry — the `listOrgSites` entry already handles site→sitegroup edges via `SiteBelongsToSiteGroup`. This adds the reverse: sitegroup→site via `site_ids` array field.
  **Acceptance**: 2 new entries. `py_compile` passes.

- [ ] T022 [US3] Add `COLLECTION_VERTEX_MAP` entries for `listOrgMxEdgeClusters`, `listOrgNacPortals`, `listOrgAuditLogs` in src/db/arango_writer.py

  Add 3 new entries (remaining list endpoints):
  ```python
  "listOrgMxEdgeClusters": {
      "vertex": "mxclusters",
      "key_field": "id",
  },
  "listOrgNacPortals": {
      "vertex": "nac_portals",
      "key_field": "id",
  },
  "listOrgAuditLogs": {
      "vertex": "audit_logs",
      "key_field": "id",
  },
  ```
  **Note**: These have no FK edges (or only `org_id` handled elsewhere). They register vertex collections so data populates the graph as vertices.
  **Acceptance**: 3 new entries (vertex-only, no edges). `py_compile` passes.

- [ ] T023 [US3] Update existing `listOrgTemplates` entry (or add new) in `COLLECTION_VERTEX_MAP` to add `TemplateAppliedToSite` and `TemplateAppliedToSiteGroup` edges in src/db/arango_writer.py

  If `listOrgTemplates` already exists in `COLLECTION_VERTEX_MAP`, add edges. Otherwise create:
  ```python
  "listOrgTemplates": {
      "vertex": "templates",
      "key_field": "id",
      "edges": [
          {"edge_col": "TemplateAppliedToSite", "from_col": "templates", "from_field": "id", "to_col": "sites", "to_field": "applies.site_ids"},
          {"edge_col": "TemplateAppliedToSiteGroup", "from_col": "templates", "from_field": "id", "to_col": "sitegroups", "to_field": "applies.sitegroup_ids"},
      ],
  },
  ```
  **Note**: Uses dot-path FK fields (`applies.site_ids`, `applies.sitegroup_ids`) requiring `_resolve_nested_field()`.
  **Acceptance**: Entry has 2 edges with dot-path FK fields. `py_compile` passes.

- [ ] T024 [US3] Add `ENTITY_TYPE_TO_VERTEX` entries for new vertex collections in src/db/arango_writer.py

  Append to the `ENTITY_TYPE_TO_VERTEX` dict (line ~88):
  ```python
  "listOrgNetworks": "networks",
  "listOrgNacRules": "nac_rules",
  "listOrgSecPolicies": "security_policies",
  "listOrgServicePolicies": "security_policies",
  "listOrgPsks": "psks",
  "listOrgWebhooks": "webhooks",
  ```
  **Purpose**: Enables `ConfigSnapshotForEntity` edges to link config snapshots to these new vertex types.
  **Acceptance**: 6 new entries in dict. `py_compile` passes.

- [ ] T025 [US3] Compile and verify config-to-site traversal

  Run:
  1. `python -m py_compile src/db/arango_writer.py`
  2. If ArangoDB is available: verify AQL traversal:
     ```aql
     FOR rule IN nac_rules
       FOR site IN 1..1 OUTBOUND rule NACRuleMatchesSite
         LIMIT 5
         RETURN {rule: rule.name, site: site.name}
     ```
  **Acceptance**: Compile passes. Config hierarchy traversals return linked data.

**Checkpoint**: User Story 3 complete — configuration objects (networks, NAC rules, PSKs, templates, security policies, assets, webhooks, sitegroups) are linked to their parent entities.

---

## Phase 6: User Story 4 — Full Graph Traversal Across Entity Types (Priority: P4)

**Goal**: Validate end-to-end graph connectivity. A multi-hop traversal from org through sites, devices, clients, and WLANs should work in a single AQL query.

**Independent Test**: Run 4-hop AQL traversal: org → sites → devices → clients → wlans.

### Implementation for User Story 4

- [ ] T026 [US4] Update `ConfigSnapshotForEntity` edge definition in `EDGE_DEFINITIONS` to include new target vertex collections in src/db/arango_writer.py

  Find the existing `ConfigSnapshotForEntity` entry (line ~83) and expand `to_vertex_collections`:
  ```python
  # Before:
  "to_vertex_collections": ["sites", "devices", "templates", "wlans"],

  # After:
  "to_vertex_collections": [
      "sites", "devices", "templates", "wlans",
      "networks", "nac_rules", "security_policies", "psks", "webhooks",
  ],
  ```
  **Acceptance**: `ConfigSnapshotForEntity` edge definition covers 9 vertex targets. `py_compile` passes.

- [ ] T027 [US4] Run full org data collection via `python MistHelper.py --menu 165`

  Execute a complete data collection run to populate all new vertex and edge collections.
  **Acceptance**: Menu 165 completes without errors. New vertex collections (networks, services, nac_rules, etc.) are populated. New edge collections have non-zero document counts for endpoints with FK data.

- [ ] T028 [US4] Verify vertex and edge collection counts in ArangoDB

  Connect to ArangoDB (http://localhost:8529) and verify:
  - All 14 new vertex collections exist: `networks`, `services`, `nac_rules`, `nac_tags`, `vpns`, `psks`, `alarms`, `events`, `audit_logs`, `assets`, `maps`, `webhooks`, `security_policies`, `nac_portals`
  - All 20 new edge collections exist and have expected document counts
  - Existing 10 vertex collections and 11 edge collections are unchanged
  **Acceptance**: Graph has 24 vertex collections and 31 edge definitions total.

- [ ] T029 [US4] Run multi-hop AQL traversal: org → sites → devices → clients → wlans

  Execute the 4-hop traversal from plan.md Phase 6:
  ```aql
  FOR site IN 1..1 OUTBOUND DOCUMENT("orgs/<org-id>") OrgContainsSite
    FOR device IN 1..1 OUTBOUND site SiteContainsDevice
      FOR client IN 1..1 INBOUND device ClientConnectedToDevice
        FOR wlan IN 1..1 OUTBOUND client ClientConnectedToWlan
          LIMIT 10
          RETURN {site: site.name, device: device.name, client: client.mac, wlan: wlan.ssid}
  ```
  **Acceptance**: Query returns results spanning 4 entity types. No "collection not found" errors.

- [ ] T030 [US4] Verify idempotency — re-run menu 165 and check stable document counts

  Run `python MistHelper.py --menu 165` a second time. Compare vertex and edge document counts before and after.
  **Acceptance**: Document counts are identical (±0) between runs. Deterministic `_edge_key()` prevents duplicates (SC-004).

**Checkpoint**: User Story 4 complete — full graph is interconnected and traversable end-to-end. Idempotency confirmed.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and documentation

- [ ] T031 Final `python -m py_compile src/db/arango_writer.py` validation

  Run compile check one final time to confirm no regressions from accumulated edits.
  **Acceptance**: Zero compile errors.

- [ ] T032 Run quickstart.md verification commands from specs/188-graph-edge-definitions/quickstart.md

  Execute all verification scripts in quickstart.md:
  1. Check graph edge definition count
  2. List vertex collections
  3. List edge collections
  4. Run sample AQL traversal
  **Acceptance**: All quickstart verification commands succeed. Edge definition count matches expected (31).

---

## Dependencies & Execution Order

### Phase Dependencies

```text
Phase 2 (Foundational)     <- BLOCKS everything
    |
Phase 3 (US1: Clients)     <- Can start after Phase 2
Phase 4 (US2: Events)      <- Can start after Phase 2 (independent of US1)
Phase 5 (US3: Config)      <- Can start after Phase 2 (independent of US1/US2)
    | (all converge)
Phase 6 (US4: Full Graph)  <- Depends on US1 + US2 + US3 all complete
    |
Phase 7 (Polish)            <- Depends on Phase 6
```

### User Story Dependencies

- **US1 (P1)**: Depends only on Phase 2. Modifies existing `searchOrgWirelessClients`, `searchOrgWiredClients`, `listOrgWlans` entries + adds `searchOrgNacClients`.
- **US2 (P2)**: Depends only on Phase 2. Adds new entries `searchOrgAlarms`, `searchOrgDeviceEvents`. No overlap with US1.
- **US3 (P3)**: Depends only on Phase 2. Adds 10 new entries + `ENTITY_TYPE_TO_VERTEX` updates. No overlap with US1/US2.
- **US4 (P4)**: Depends on US1 + US2 + US3 (needs complete graph for multi-hop traversal).

### Single-File Constraint

All tasks edit `src/db/arango_writer.py`. While US1/US2/US3 are logically independent, they cannot be parallelized across agents because they modify the same file. Execute sequentially in priority order: US1 → US2 → US3 → US4.

### Within Each Phase

- T001-T005: Sequential (each batch appends after the previous)
- T006-T007: Sequential (T007 depends on T006)
- T009-T012: Can be done in any order (different dict entries in same file)
- T017-T023: Can be done in any order (different dict entries)
- T027-T030: Strictly sequential (each depends on previous run's state)

---

## Summary

| Metric | Count |
|-|-|
| Total tasks | 32 |
| Phase 2 (Foundational) | 8 |
| Phase 3 (US1 — MVP) | 5 |
| Phase 4 (US2) | 3 |
| Phase 5 (US3) | 9 |
| Phase 6 (US4) | 5 |
| Phase 7 (Polish) | 2 |
| Parallel opportunities | Limited (single-file constraint) |
| New edge definitions | 20 |
| New COLLECTION_VERTEX_MAP entries | 14 |
| Updated COLLECTION_VERTEX_MAP entries | 4 |
| New ENTITY_TYPE_TO_VERTEX entries | 6 |
| New vertex collections (implicit) | 14 |
| Suggested MVP scope | Phase 2 + Phase 3 (US1) = 13 tasks |
