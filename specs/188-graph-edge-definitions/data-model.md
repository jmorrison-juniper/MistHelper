# Data Model: Complete ArangoDB Graph Edge Definitions

**Date**: 2026-04-26  
**Spec**: specs/188-graph-edge-definitions/spec.md

## Vertex Collections

### Existing (10, unchanged)

| Collection | Key Field | Source Endpoints |
|-|-|-|
| `orgs` | `org_id` | Auto-created from any record's `org_id` |
| `sites` | `id` | `listOrgSites`, `searchOrgSites` |
| `devices` | `id` | `getOrgInventory`, `listOrgMxEdges`, `searchOrgDevices` |
| `clients` | `mac` | `searchOrgWirelessClients`, `searchOrgWiredClients` |
| `wlans` | `id` | `listOrgWlans` |
| `templates` | `id` | `listOrgTemplates`, `listOrg*Templates`, `listOrgDeviceProfiles` |
| `sitegroups` | `id` | `listOrgSiteGroups` (stub from `sitegroup_ids`) |
| `mxclusters` | `id` | `listOrgMxEdgeClusters` (stub from `mxcluster_id`) |
| `ports` | `id` | From device port data |
| `config_snapshots` | `uuid` | `ArangoDBWriter.snapshot()` |

### New (14)

| Collection | Key Field | Source Endpoints |
|-|-|-|
| `networks` | `id` | `listOrgNetworks` |
| `services` | `id` | `listOrgServices` |
| `nac_rules` | `id` | `listOrgNacRules` |
| `nac_tags` | `id` | `listOrgNacTags` |
| `vpns` | `id` | `listOrgVpns` |
| `psks` | `id` | `listOrgPsks` |
| `alarms` | `id` | `searchOrgAlarms` |
| `events` | `id` | `searchOrgDeviceEvents`, other event searches |
| `audit_logs` | `id` | `listOrgAuditLogs` |
| `assets` | `id` | `listOrgAssets` |
| `maps` | `id` | Stub from `map_id` references |
| `webhooks` | `id` | `listOrgWebhooks` |
| `security_policies` | `id` | `listOrgSecPolicies`, `listOrgServicePolicies` |
| `nac_portals` | `id` | `listOrgNacPortals` |

## Edge Collections

### Existing (11, unchanged)

| Edge Collection | From | To | FK Field |
|-|-|-|-|
| `OrgContainsSite` | `orgs` | `sites` | `org_id` |
| `OrgContainsDevice` | `orgs` | `devices` | `org_id` |
| `SiteContainsDevice` | `sites` | `devices` | `site_id` |
| `TemplateAssignedToSite` | `templates` | `sites` | `*template_id` fields |
| `DeviceHasPort` | `devices` | `ports` | port data |
| `ClientConnectedToDevice` | `clients` | `devices` | `ap`/`device_mac` |
| `WlanBelongsToSite` | `wlans` | `sites` | `site_id` |
| `WlanUsesTemplate` | `wlans` | `templates` | `template_id` |
| `SiteBelongsToSiteGroup` | `sites` | `sitegroups` | `sitegroup_ids` |
| `MxEdgeBelongsToCluster` | `devices` | `mxclusters` | `mxcluster_id` |
| `ConfigSnapshotForEntity` | `config_snapshots` | `sites/devices/templates/wlans` | entity_id |

### New Edge Collections (Phase 1: Core Relationships)

| Edge Collection | From | To | FK Field | Source Endpoint |
|-|-|-|-|-|
| `ClientConnectedToWlan` | `clients` | `wlans` | `wlan_id` | `searchOrgWirelessClients` |
| `ClientBelongsToSite` | `clients` | `sites` | `site_id` | `searchOrgWirelessClients`, `searchOrgWiredClients` |
| `NetworkBelongsToOrg` | `networks` | `orgs` | `org_id` | `listOrgNetworks` |
| `ServiceBelongsToOrg` | `services` | `orgs` | `org_id` | `listOrgServices` |
| `VpnBelongsToOrg` | `vpns` | `orgs` | `org_id` | `listOrgVpns` |

### New Edge Collections (Phase 2: Events and Alarms)

| Edge Collection | From | To | FK Field | Source Endpoint |
|-|-|-|-|-|
| `AlarmBelongsToSite` | `alarms` | `sites` | `site_id` | `searchOrgAlarms` |
| `EventBelongsToSite` | `events` | `sites` | `site_id` | `searchOrgDeviceEvents` |
| `EventOccurredOnDevice` | `events` | `devices` | `mac` (device) | `searchOrgDeviceEvents` |

### New Edge Collections (Phase 3: Security and NAC)

| Edge Collection | From | To | FK Field | Source Endpoint |
|-|-|-|-|-|
| `NACRuleMatchesSite` | `nac_rules` | `sites` | `matching.site_ids` | `listOrgNacRules` |
| `NACRuleMatchesSiteGroup` | `nac_rules` | `sitegroups` | `matching.sitegroup_ids` | `listOrgNacRules` |
| `NACTagBelongsToPortal` | `nac_tags` | `nac_portals` | `nacportal_id` | `listOrgNacTags` |
| `SecurityPolicyBelongsToOrg` | `security_policies` | `orgs` | `org_id` | `listOrgSecPolicies` |

### New Edge Collections (Phase 4: Assets and Config)

| Edge Collection | From | To | FK Field | Source Endpoint |
|-|-|-|-|-|
| `PSKBelongsToSite` | `psks` | `sites` | `site_id` | `listOrgPsks` |
| `AssetBelongsToSite` | `assets` | `sites` | `site_id` | `listOrgAssets` |
| `AssetOnMap` | `assets` | `maps` | `map_id` | `listOrgAssets` |
| `WebhookBelongsToSite` | `webhooks` | `sites` | `site_id` | `listOrgWebhooks` |
| `SiteGroupContainsSite` | `sitegroups` | `sites` | `site_ids` | `listOrgSiteGroups` |

### New Edge Collections (Phase 5: Advanced WLANs and Templates)

| Edge Collection | From | To | FK Field | Source Endpoint |
|-|-|-|-|-|
| `WlanUsesMxTunnel` | `wlans` | `devices` | `mxtunnel_id` | `listOrgWlans` |
| `TemplateAppliedToSite` | `templates` | `sites` | `applies.site_ids` | `listOrgTemplates` |
| `TemplateAppliedToSiteGroup` | `templates` | `sitegroups` | `applies.sitegroup_ids` | `listOrgTemplates` |

## Relationships Diagram

```
orgs ──contains──> sites ──contains──> devices ──has──> ports
  │                  │                    │
  │                  │                    └──< clients (connected)
  │                  │                    └──< events (occurred on)
  │                  │
  │                  ├──< wlans (belongs to)
  │                  ├──< networks (belongs to -- future)
  │                  ├──< psks (belongs to)
  │                  ├──< assets (belongs to)
  │                  ├──< webhooks (belongs to)
  │                  ├──< alarms (belongs to)
  │                  └──< sitegroups (belongs to)
  │
  ├──contains──> networks
  ├──contains──> services
  ├──contains──> vpns
  ├──contains──> security_policies
  └──contains──> templates ──assigned to──> sites
                     └──used by──> wlans
```

## State Transitions

No state machines. All entities are imported as immutable snapshots. Edges reflect point-in-time relationships.

## Validation Rules

1. Edge `_from` and `_to` must reference existing vertex collections registered in the graph
2. Edge `_key` must be deterministic (SHA-256 of `from:to`)
3. Null or empty FK values must be skipped (no edge created)
4. Array FK fields produce one edge per non-null element
5. Cross-org FK references must be skipped (verify `org_id` matches)
