# Research: Mist API Documentation Enrichment

**Feature**: 009-api-docs-enrichment
**Date**: 2026-03-06

## R1: Enrichment Content Derivation Strategy

**Decision**: AI-agent enrichment. The AI agent reads each endpoint file, researches all available sources (OpenAPI spec, MistHelper.py, agents.md, web resources), and writes substantive domain-knowledge content for each of the 4 enrichment sections. No algorithmic script.

**Rationale**: The placeholder text "*To be enriched by AI agent.*" was a design signal for AI-quality content. Algorithmic derivation cannot produce the domain knowledge (correct gotchas, workflow context, best practices) that makes these files uniquely valuable over the raw OpenAPI spec. AI enrichment — processing files in category batches — delivers actionable guidance.

**Alternatives considered**:
- Script-generated (algorithmic): Fast and consistent but produces generic filler ("Use this endpoint to list resources...") that adds no value beyond the raw spec
- Hybrid (script for mappings, AI for prose): Extra complexity for marginal benefit — the AI agent can do both in a single pass
- Manual enrichment by human: Too slow for 4,052 sections

## R2: Usage Context Derivation

**Decision**: Derive Usage Context from the endpoint's HTTP method, URL path, and existing Description section. The HTTP method implies the action pattern:

| Method | Pattern |
|--------|---------|
| GET (no ID) | List/search resources |
| GET (with ID) | Retrieve a specific resource |
| POST | Create a resource or trigger an action |
| PUT | Update/replace a resource |
| DELETE | Remove a resource |

Additional context comes from the path segments (e.g., `/orgs/{org_id}/sites` → "site management at the org level").

**Rationale**: The HTTP method + path + description contain sufficient information to generate accurate, actionable usage context. This data is already present in each endpoint file's header sections.

**Alternatives considered**:
- External documentation scraping: Unreliable, copyright concerns
- LLM-generated context per file: Would require 1,013 API calls, expensive and slow

## R3: Gotchas Identification

**Decision**: Source gotchas from structural inference AND multi-source research:
1. **Structural inference**: Required fields, enum constraints, deprecated status, pagination parameters, `duration` defaults, timestamp format requirements
2. **Known patterns in agents.md**: Device type filtering (`type=all`), Dash 3.x API changes, pagination defaults
3. **Common Mist API patterns**: Rate limiting on search endpoints, `limit`/`page` pagination, `start`/`end` time window parameters
4. **Web research**: Mist API documentation, Juniper knowledge base, community forums, GitHub repositories for domain-specific gotchas

Reserve "No known gotchas for this endpoint." only for trivially simple endpoints with no parameters and no request body.

**Rationale**: Combining structural analysis with web research maximizes coverage. Structural inference catches parameter-level pitfalls; web research reveals domain-specific issues (e.g., eventual consistency, API version differences, undocumented behaviors).

**Alternatives considered**:
- Conservative approach ("No known gotchas" for most endpoints): Wastes the enrichment opportunity for 886 not-in-MistHelper endpoints
- Only document gotchas for MistHelper-used endpoints: Leaves 886 files with no useful information

## R4: Related Endpoints Identification

**Decision**: Full relationship graph — link all related endpoints comprehensively:
1. **CRUD siblings**: All operations on the same resource (GET list, GET by ID, POST create, PUT update, DELETE)
2. **Parent resource**: The enclosing resource endpoint (e.g., `getSiteInfo` for `listSiteDevices`)
3. **Sub-resource endpoints**: Child resources (e.g., site → site devices, site → site maps)
4. **Cross-scope equivalents**: Org-level and site-level versions of similar operations (e.g., `listOrgDevices` ↔ `listSiteDevices`)

**Cross-reference link format**: Relative paths using `../` for cross-category links:
- Same category: `[GET_sites_site_id.md](GET_sites_site_id.md)`
- Different category: `[GET_orgs_org_id_sites.md](../orgs/GET_orgs_org_id_sites.md)`

**Rationale**: Full graph provides maximum navigability for AI agents and developers. An agent working on a device firmware upgrade workflow needs to discover not just the upgrade endpoint but also the status check, device listing, and version listing endpoints.

**Alternatives considered**:
- CRUD-only (max ~4 links): Misses important sub-resource and cross-scope relationships
- CRUD + parent only: Still misses sub-resources and cross-scope equivalents that are commonly used together

## R5: MistHelper Menu Mapping

**Decision**: Scan MistHelper.py for `mistapi.api.v1.{scope}.{resource}.{operationId}` call patterns. Map each call to its surrounding menu operation context by finding the nearest menu operation number comment or function name.

**Key finding**: 127 unique API operations are used by MistHelper out of 1,013 total endpoints. This means ~886 endpoints (87.5%) will get "Not currently used by MistHelper" in their MistHelper Notes section.

**Full inventory of used operations** (127 unique `mistapi.api.v1.*` calls):

### orgs scope (~67 operations)
- orgs.admins: listOrgAdmins
- orgs.alarms: searchOrgAlarms
- orgs.alarmtemplates: listOrgAlarmTemplates
- orgs.apitokens: listOrgApiTokens
- orgs.aptemplates: listOrgAptemplates
- orgs.clients: searchOrgWirelessClients
- orgs.deviceprofiles: assignOrgDeviceProfile, createOrgDeviceProfile, listOrgDeviceProfiles
- orgs.devices: listOrgAvailableDeviceVersions, listOrgDevices, searchOrgDeviceEvents
- orgs.events: searchOrgEvents
- orgs.gatewaytemplates: createOrgGatewayTemplate, getOrgGatewayTemplate, listOrgGatewayTemplates, updateOrgGatewayTemplate
- orgs.guests: searchOrgGuestAuthorization
- orgs.insights: getOrgSitesSle, getOrgSle
- orgs.inventory: getOrgInventory
- orgs.invites: listOrgInvites
- orgs.licenses: getOrgLicensesBySite
- orgs.logs: listOrgAuditLogs
- orgs.mxedges: listOrgMxEdges
- orgs.nac_clients: searchOrgNacClientEvents, searchOrgNacClients
- orgs.nacportals: listOrgNacPortals
- orgs.nacrules: listOrgNacRules
- orgs.nactags: listOrgNacTags
- orgs.networks: listOrgNetworks
- orgs.networktemplates: listOrgNetworkTemplates
- orgs.orgs: getOrg
- orgs.pcaps: listOrgPacketCaptures, startOrgPacketCapture
- orgs.psks: listOrgPsks
- orgs.rftemplates: createOrgRfTemplate, listOrgRfTemplates, updateOrgRfTemplate
- orgs.secintelprofiles: listOrgSecIntelProfiles
- orgs.secpolicies: listOrgSecPolicies
- orgs.servicepolicies: listOrgServicePolicies
- orgs.services: listOrgServices
- orgs.sites: createOrgSite, listOrgSites
- orgs.sitetemplates: getOrgSiteTemplate, listOrgSiteTemplates, updateOrgSiteTemplate
- orgs.ssos: listOrgSsos
- orgs.ssr: listOrgAvailableSsrVersions, listOrgSsrUpgrades, upgradeOrgSsrs
- orgs.stats: getOrgMxEdgeStats, listOrgDevicesStats, listOrgMxEdgesStats, listOrgSitesStats, searchOrgAssets, searchOrgBgpPeers, searchOrgPeerPathStats, searchOrgSwOrGwPorts, searchOrgTunnels
- orgs.templates: listOrgTemplates
- orgs.troubleshoot: troubleshootOrg
- orgs.webhooks: listOrgWebhooks
- orgs.wired_clients: searchOrgWiredClients
- orgs.wlans: listOrgWlans, updateOrgWlan

### sites scope (~58 operations)
- sites.anomaly: getSiteAnomalyEventsForClient, getSiteAnomalyEventsForDevice, listSiteAnomalyEvents
- sites.beacons: listSiteBeacons, updateSiteBeacon
- sites.clients: searchSiteWirelessClients, searchSiteWirelessClientSessions
- sites.devices: convertSiteVirtualChassisToVirtualMac, createSiteDeviceShellSession, getSiteDevice, getSiteDeviceSyntheticTest, getSiteDeviceUpgrade, getSiteDeviceVirtualChassis, listSiteDevices, listSiteDeviceUpgrades, restartSiteDevice, servicePingFromSsr, showSiteSsrAndSrxRoutes, updateSiteDevice, upgradeSiteDevices
- sites.events: searchSiteFastRoamEvents, searchSiteSystemEvents
- sites.gatewaytemplates: listSiteGatewayTemplatesDerived
- sites.insights: getSiteInsightMetrics, getSiteInsightMetricsForClient, getSiteInsightMetricsForDevice, listSiteRogueAPs, listSiteRogueClients
- sites.maps: addSiteMapImageFile, createSiteMap, deleteSiteMap, getSiteMap, listSiteMaps, updateSiteMap
- sites.networks: listSiteNetworksDerived
- sites.pcaps: listSitePacketCaptures, startSitePacketCapture
- sites.servicepolicies: listSiteServicePoliciesDerived
- sites.setting: getSiteSetting, getSiteSettings, updateSiteSettings
- sites.sites: getSiteInfo, updateSiteInfo
- sites.sle: listSiteSlesMetrics
- sites.stats: getSiteClientsStats, getSiteDeviceStats, listSiteDevicesStats, listSiteWirelessClientsStats, searchSiteSwOrGwPorts
- sites.synthetic_test: searchSiteSyntheticTest
- sites.vbeacons: listSiteVBeacons, updateSiteVBeacon
- sites.wired_clients: searchSiteWiredClients
- sites.wlans: listSiteWlans, updateSiteWlan
- sites.zones: createSiteZone, deleteSiteZone, listSiteZones, updateSiteZone

### self scope (~1 operation)
- self.usage: getSelfApiUsage

### admins scope (0 operations used directly)
No MistHelper menu operations call admins endpoints directly (login/logout handled by mistapi SDK internally).

## R6: AI Agent Enrichment Workflow

**Decision**: No enrichment script. The AI agent processes files directly using tool calls (read_file, replace_string_in_file / multi_replace_string_in_file). The workflow per category:

1. **Pre-scan**: AI agent reads MistHelper.py to identify which endpoints in the current category are used and which menu operations call them
2. **Batch read**: AI agent reads endpoint files in the category to understand the endpoint structure
3. **Research**: AI agent uses web fetch tools to research domain-specific gotchas and best practices for the endpoint's resource type
4. **Enrich**: AI agent writes enrichment content for all 4 sections using file editing tools
5. **Checkpoint**: Git commit every ~50 files

**Rationale**: AI-agent enrichment produces higher-quality domain knowledge than algorithmic generation. The agent can understand endpoint semantics, identify non-obvious gotchas, and write context-specific guidance. No throwaway script code to maintain.

**Alternatives considered**:
- Python enrichment script (3 classes): Would produce generic filler content; the script itself becomes dead code after one use
- Hybrid (script + AI pass): Extra complexity for marginal benefit

## R7: Cross-Reference Link Validation

**Decision**: After enrichment, validate all `Related Endpoints` links by checking that each linked file exists on disk. Use the PowerShell link validation script defined in quickstart.md as a standalone validation pass.

**Rationale**: FR-006 requires all cross-reference links to resolve to existing files. Link validation is a separate concern from content generation.

**Alternatives considered**:
- Validate during enrichment: Interleaves concerns; better as a post-processing step
- Skip validation: Unacceptable per FR-006

## R8: Idempotency and Re-run Safety

**Decision**: The AI agent replaces content between section headers. It locates `## Usage Context` through the next `##` header and replaces everything in between (or to end of file for MistHelper Notes). This makes re-enrichment safe — previously enriched content is overwritten with newly generated content.

**Rationale**: Idempotency is critical because the generation script (`generate_api_docs.py`) may be re-run, resetting all files to placeholders. The AI agent must handle both placeholder and previously-enriched files identically.

**Alternatives considered**:
- Marker-based replacement (special comment tags): Adds noise to the output files
- Append-only mode: Would create duplicates on re-enrichment
