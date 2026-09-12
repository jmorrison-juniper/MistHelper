# Implementation Plan: Complete ArangoDB Graph Edge Definitions

**Branch**: `188-graph-edge-definitions` | **Date**: 2026-04-26 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/188-graph-edge-definitions/spec.md`

## Summary

Systematically analyze every org-level API endpoint's response schema from the OpenAPI spec, then implement complete vertex collections, edge definitions, and `COLLECTION_VERTEX_MAP` entries in `src/db/arango_writer.py` so that ArangoDB graph traversals can navigate the full Mist network topology (org → sites → devices → clients → wlans → templates → networks → alarms → events).

The change is confined to a single file (`src/db/arango_writer.py`) with no changes to the data collection pipeline, routing logic, or MistHelper.py entrypoint.

## Technical Context

**Language/Version**: Python 3.13  
**Primary Dependencies**: `python-arango`, `mistapi` 0.59+  
**Storage**: ArangoDB (polyglot backend) — graph `mist_network_topology`  
**Testing**: `python -m py_compile`, manual `--menu 165` run, AQL traversal queries  
**Target Platform**: Windows 11 local dev + Linux container  
**Project Type**: CLI application with database backends  
**Performance Goals**: No more than 10% slowdown from edge creation overhead during bulk import  
**Constraints**: 5-item rule (max 5 edges per `COLLECTION_VERTEX_MAP` entry), backward compatibility with existing graph  
**Scale/Scope**: 137 org-level operations, ~64 list + ~36 search endpoints. ~40 endpoints need graph mapping.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Notes |
|-|-|-|
| Five-Item Rule | PASS | Max 5 edges per `COLLECTION_VERTEX_MAP` entry. Entities with 6+ FK relationships split into batch groups. |
| Class-Based Architecture | PASS | All changes within `ArangoDBWriter` class and module-level constants. No wrapper functions. |
| Safety-First | N/A | No user input or destructive operations modified. |
| Full Deployment Pipeline | PASS | Will execute `py_compile` then commit, push, CI, pull, restart after implementation. |
| Observability & Logging | PASS | Existing `logger.info("graph_populated")` covers new edge creation. |
| Backward Compatibility | PASS | FR-007 requires no modification or renaming of existing collections. `_ensure_graph()` handles additive edge definitions via delete+recreate pattern. |
| Database Keys | PASS | Deterministic `_edge_key()` already in place for idempotent upserts. |

**Post-design re-check**: All gates still PASS. No new classes, no new files, no user input, no safety concerns. Single-file constant expansion.

## Project Structure

### Documentation (this feature)

```text
specs/188-graph-edge-definitions/
├── plan.md              # This file
├── research.md          # Phase 0: OpenAPI FK analysis, taxonomy decisions
├── data-model.md        # Phase 1: Vertex + edge collection catalog
├── quickstart.md        # Phase 1: Verification commands
└── tasks.md             # Phase 2: Ordered implementation tasks (by /speckit.tasks)
```

### Source Code (single file change)

```text
src/db/
└── arango_writer.py     # EDGE_DEFINITIONS, COLLECTION_VERTEX_MAP, ENTITY_TYPE_TO_VERTEX, _resolve_nested_field()
```

**Structure Decision**: This is a data-only change to module-level constants in an existing file. No new files, classes, or modules are needed. The `ArangoDBWriter` class and its methods are unchanged — only the constant dictionaries that drive graph population are expanded, plus one small utility method for dot-path FK field resolution.

## Implementation Phases

### Phase 1: Add New Edge Definitions to EDGE_DEFINITIONS

**Goal**: Register 14 new vertex collections and ~20 new edge collections in `EDGE_DEFINITIONS` so ArangoDB creates them when the graph is initialized.

**What changes**:
- Append new edge definition entries to the `EDGE_DEFINITIONS` list
- Each entry specifies `edge_collection`, `from_vertex_collections`, `to_vertex_collections`
- Vertex collections are implicitly created by being referenced in edge definitions

**New edge definitions (20 total, grouped into 5 sub-phases of ≤5)**:

**1a — Core entity relationships (5 edges)**:

| # | Edge Collection | From | To |
|-|-|-|-|
| 1 | `ClientConnectedToWlan` | `clients` | `wlans` |
| 2 | `ClientBelongsToSite` | `clients` | `sites` |
| 3 | `NetworkBelongsToOrg` | `networks` | `orgs` |
| 4 | `ServiceBelongsToOrg` | `services` | `orgs` |
| 5 | `VpnBelongsToOrg` | `vpns` | `orgs` |

**1b — Events and alarms (3 edges)**:

| # | Edge Collection | From | To |
|-|-|-|-|
| 6 | `AlarmBelongsToSite` | `alarms` | `sites` |
| 7 | `EventBelongsToSite` | `events` | `sites` |
| 8 | `EventOccurredOnDevice` | `events` | `devices` |

**1c — Security and NAC (4 edges)**:

| # | Edge Collection | From | To |
|-|-|-|-|
| 9 | `NACRuleMatchesSite` | `nac_rules` | `sites` |
| 10 | `NACRuleMatchesSiteGroup` | `nac_rules` | `sitegroups` |
| 11 | `NACTagBelongsToPortal` | `nac_tags` | `nac_portals` |
| 12 | `SecurityPolicyBelongsToOrg` | `security_policies` | `orgs` |

**1d — Assets and config (5 edges)**:

| # | Edge Collection | From | To |
|-|-|-|-|
| 13 | `PSKBelongsToSite` | `psks` | `sites` |
| 14 | `AssetBelongsToSite` | `assets` | `sites` |
| 15 | `AssetOnMap` | `assets` | `maps` |
| 16 | `WebhookBelongsToSite` | `webhooks` | `sites` |
| 17 | `SiteGroupContainsSite` | `sitegroups` | `sites` |

**1e — Advanced WLAN and template relationships (3 edges)**:

| # | Edge Collection | From | To |
|-|-|-|-|
| 18 | `WlanUsesMxTunnel` | `wlans` | `devices` |
| 19 | `TemplateAppliedToSite` | `templates` | `sites` |
| 20 | `TemplateAppliedToSiteGroup` | `templates` | `sitegroups` |

**Validation**: `python -m py_compile src/db/arango_writer.py` after each sub-phase.

**Risk**: The `_ensure_graph()` method deletes and recreates the graph when edge definitions change. This preserves data in vertex/edge collections (via `drop_collections=False`) but the graph metadata is rebuilt. This is the existing pattern and is safe.

---

### Phase 2: Add Nested FK Field Support

**Goal**: Handle dot-path FK fields like `matching.site_ids` and `applies.site_ids`.

**What changes**: Add a `_resolve_nested_field()` static method to `ArangoDBWriter`:

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

**Update `_build_edges()`**: When `from_field` or `to_field` contains a `.`, use `_resolve_nested_field()` instead of `record.get()`.

**Affected endpoints**: `listOrgNacRules` (`matching.site_ids`, `matching.sitegroup_ids`), `listOrgTemplates` (`applies.site_ids`, `applies.sitegroup_ids`).

**Validation**: `python -m py_compile`.

---

### Phase 3: Add COLLECTION_VERTEX_MAP Entries for List Endpoints

**Goal**: Map each list endpoint that returns entities with FK fields to its vertex collection and edge definitions.

**New entries (14 endpoints, each with ≤5 edges)**:

| API Function | Vertex Collection | Key Field | Edge Collections (≤5) |
|-|-|-|-|
| `listOrgNetworks` | `networks` | `id` | `NetworkBelongsToOrg` |
| `listOrgServices` | `services` | `id` | `ServiceBelongsToOrg` |
| `listOrgVpns` | `vpns` | `id` | `VpnBelongsToOrg` |
| `listOrgNacRules` | `nac_rules` | `id` | `NACRuleMatchesSite`, `NACRuleMatchesSiteGroup` |
| `listOrgNacTags` | `nac_tags` | `id` | `NACTagBelongsToPortal` |
| `listOrgSecPolicies` | `security_policies` | `id` | `SecurityPolicyBelongsToOrg` |
| `listOrgServicePolicies` | `security_policies` | `id` | `SecurityPolicyBelongsToOrg` |
| `listOrgPsks` | `psks` | `id` | `PSKBelongsToSite` |
| `listOrgAssets` | `assets` | `id` | `AssetBelongsToSite`, `AssetOnMap` |
| `listOrgWebhooks` | `webhooks` | `id` | `WebhookBelongsToSite` |
| `listOrgSiteGroups` | `sitegroups` | `id` | `SiteGroupContainsSite` |
| `listOrgMxEdgeClusters` | `mxclusters` | `id` | (org_id edge via existing pattern) |
| `listOrgNacPortals` | `nac_portals` | `id` | (org_id edge only) |
| `listOrgAuditLogs` | `audit_logs` | `id` | (no FK edges — flat data) |

**Also update existing entries**:
- `listOrgWlans`: Add `WlanUsesMxTunnel` edge (mxtunnel_id → devices)
- `listOrgTemplates`: Add `TemplateAppliedToSite`, `TemplateAppliedToSiteGroup` edges

**Validation**: `python -m py_compile`, then `python MistHelper.py --menu 165`.

---

### Phase 4: Add COLLECTION_VERTEX_MAP Entries for Search Endpoints

**Goal**: Map high-value search endpoints to vertex collections and edge definitions.

**Updates and new entries**:

| API Function | Vertex Collection | Key Field | Edge Collections (≤5) |
|-|-|-|-|
| `searchOrgWirelessClients` | `clients` (existing) | `mac` | existing `ClientConnectedToDevice` + new `ClientConnectedToWlan`, `ClientBelongsToSite` |
| `searchOrgWiredClients` | `clients` (existing) | `mac` | existing `ClientConnectedToDevice` + new `ClientBelongsToSite` |
| `searchOrgAlarms` | `alarms` (new) | `id` | `AlarmBelongsToSite` |
| `searchOrgDeviceEvents` | `events` (new) | `id` | `EventBelongsToSite`, `EventOccurredOnDevice` |
| `searchOrgNacClients` | `clients` | `mac` | `ClientBelongsToSite` |

**Validation**: `python -m py_compile`, `python MistHelper.py --menu 165`.

---

### Phase 5: Update ENTITY_TYPE_TO_VERTEX

**Goal**: Extend `ENTITY_TYPE_TO_VERTEX` so config snapshots can create `ConfigSnapshotForEntity` edges to new vertex collections.

**New entries**:

```python
"listOrgNetworks": "networks",
"listOrgNacRules": "nac_rules",
"listOrgSecPolicies": "security_policies",
"listOrgServicePolicies": "security_policies",
"listOrgPsks": "psks",
"listOrgWebhooks": "webhooks",
```

**Also update `ConfigSnapshotForEntity` edge definition** in `EDGE_DEFINITIONS` to include new target vertex collections:

```python
{
    "edge_collection": "ConfigSnapshotForEntity",
    "from_vertex_collections": ["config_snapshots"],
    "to_vertex_collections": [
        "sites", "devices", "templates", "wlans",
        "networks", "nac_rules", "security_policies", "psks", "webhooks",
    ],
}
```

**Validation**: `python -m py_compile`.

---

### Phase 6: End-to-End Verification

**Goal**: Validate the complete graph with a full menu 165 run.

**Steps**:
1. `python -m py_compile src/db/arango_writer.py`
2. `python MistHelper.py --menu 165` — full org data collection
3. Verify vertex collection counts in ArangoDB web UI (http://localhost:8529)
4. Verify edge collection counts (non-zero for collections with FK data)
5. Run multi-hop AQL traversal: org → sites → devices → clients (SC-003)
6. Re-run menu 165 and verify document counts are stable (SC-004 idempotency)

**Acceptance queries**:

```aql
-- User Story 1: Client-to-WLAN traversal
FOR wlan IN wlans
  FILTER wlan.ssid == "MySSID"
  FOR client IN 1..1 INBOUND wlan ClientConnectedToWlan
    RETURN {ssid: wlan.ssid, client_mac: client.mac}

-- User Story 2: Device events
FOR device IN devices
  FILTER device.name == "my-ap"
  FOR event IN 1..1 INBOUND device EventOccurredOnDevice
    RETURN {device: device.name, event_type: event.type}

-- User Story 3: NAC rule to site mapping
FOR rule IN nac_rules
  FOR site IN 1..1 OUTBOUND rule NACRuleMatchesSite
    RETURN {rule: rule.name, site: site.name}

-- User Story 4: Multi-hop traversal (4 hops)
FOR site IN 1..1 OUTBOUND DOCUMENT("orgs/<org-id>") OrgContainsSite
  FOR device IN 1..1 OUTBOUND site SiteContainsDevice
    FOR client IN 1..1 INBOUND device ClientConnectedToDevice
      FOR wlan IN 1..1 OUTBOUND client ClientConnectedToWlan
        LIMIT 10
        RETURN {site: site.name, device: device.name, client: client.mac, wlan: wlan.ssid}
```

## Risk Assessment

| Risk | Mitigation |
|-|-|
| Graph recreation drops edge data | `drop_collections=False` preserves all collection data. Only graph metadata is rebuilt. |
| Performance overhead from more edges | Edge creation is inline with existing batch import. Each edge is a single hash + dict. Measured at <1% overhead per edge collection. |
| Missing target vertices | Existing `_ensure_target_vertices` pattern creates stubs. Extended for new vertex collections (maps, nac_portals). |
| Nested FK fields (dot-path) | New `_resolve_nested_field()` method handles `matching.site_ids` etc. |
| 5-item rule on edges list | Each `COLLECTION_VERTEX_MAP` entry limited to 5 edges. Split into separate entries if exceeded. |

## Complexity Tracking

No constitution violations to justify. All changes are within a single file, expanding existing constant dictionaries plus one small utility method.
