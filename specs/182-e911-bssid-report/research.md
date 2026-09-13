# Research: E911 BSSID Compliance Report

**Feature**: 182-e911-bssid-report
**Date**: 2026-04-07

## R1: BSSID Derivation from Radio Base MAC

**Decision**: Enumerate last nibble of radio base MAC from 0x0 to 0xF to produce 16 BSSIDs per radio.

**Rationale**: This is documented in the Mist OpenAPI spec (`ap_radio_stat.mac` description: "Radio (base) mac, it can have 16 bssids (e.g. 5c5b350001a0-5c5b350001af)") and confirmed by `listOrgApsMacs` endpoint documentation which states: "Each radio MAC can have 16 BSSIDs (enumerate the last octet from 0-F)".

**Alternatives considered**:
- Query per-radio BSSID list from device stats: Not available — the API only returns base MACs, not enumerated BSSIDs.
- Use `radio_stat` from `listOrgDevicesStats` instead of `listOrgApsMacs`: Would require parsing nested `band_24/band_5/band_6` objects. `listOrgApsMacs` is purpose-built for E911 and returns a flat `radio_macs` array — simpler and authoritative.

## R2: API Endpoint Selection for Radio MACs

**Decision**: Use `listOrgApsMacs` (`GET /api/v1/orgs/{org_id}/devices/radio_macs`) as the primary data source.

**Rationale**: This endpoint is explicitly documented for E911 use cases. It returns `{mac, radio_macs[]}` per AP in a single org-level call. The `radio_macs` array contains all radio base MACs without needing to parse nested band objects.

**Alternatives considered**:
- `listOrgDevicesStats` with `radio_stat` parsing: Returns band-specific objects (`band_24.mac`, `band_5.mac`, `band_6.mac`). More complex to parse, and the stat endpoint may not include radios that are administratively disabled but still have BSSIDs. The `radio_macs` endpoint is authoritative.

**SDK method**: `mistapi.api.v1.orgs.devices.listOrgApsMacs(apisession, org_id, limit=1000)`

## R3: AP-to-Site and AP-to-Map Resolution

**Decision**: Use `listOrgDevicesStats` with `type="ap"` to resolve AP MAC → {name, site_id, map_id}.

**Rationale**: Org-level device stats returns `mac`, `name`, `site_id`, `map_id` for all APs in a single paginated call. This avoids per-site queries for device inventory.

**Alternatives considered**:
- `getOrgInventory`: Returns inventory with `mac`, `site_id`, `name`, but does NOT include `map_id`. Cannot resolve floor assignment.
- Per-site `listSiteDevices`: Would require N API calls (one per site). Not scalable for large orgs.

**SDK method**: `mistapi.api.v1.orgs.stats.listOrgDevicesStats(apisession, org_id, type="ap", limit=1000)`

## R4: Map Name Resolution

**Decision**: Call `listSiteMaps` per-site only for sites that contain APs (deduplicated from device stats).

**Rationale**: Maps are site-scoped — no org-level "list all maps" endpoint exists. By deduplicating site_ids from the device stats lookup, we minimize API calls to only sites with APs.

**SDK method**: `mistapi.api.v1.sites.maps.listSiteMaps(apisession, site_id, limit=1000)`

## R5: Site Address Resolution

**Decision**: Use `listOrgSites` to build `site_id → {name, address}` lookup.

**Rationale**: Org-level sites list returns `name` and `address` for all sites in one paginated call. Standard MistHelper pattern (used by OfflineDeviceReporter, GatewayExportUtils, etc.).

**SDK method**: `mistapi.api.v1.orgs.sites.listOrgSites(apisession, org_id, limit=1000)`

## R6: BSSID MAC Formatting

**Decision**: Format as colon-separated lowercase (e.g., `5c:5b:35:00:00:40`).

**Rationale**: E911 systems commonly expect colon-separated format. MistHelper already has `normalize_mac_address()` that produces this format. Consistent with industry standard.

**Alternatives considered**:
- Hyphen-separated (`5c-5b-35-00-00-40`): Less common in E911 systems.
- No separator (`5c5b35000040`): Harder to read, less compatible.

## R7: Existing MistHelper Patterns to Follow

**Decision**: Model the class after `OfflineDeviceReporter` (Menu 158) — same pattern of static methods, org-level prefetch, in-memory join, CSV output.

**Key patterns from OfflineDeviceReporter**:
1. Class with `@staticmethod execute()` entry point
2. `ConfigUtils.get_cached_or_prompted_org_id()` for org_id
3. `mistapi.get_all()` for pagination
4. `DataExporter.write_with_format_selection()` for dual output
5. `OperationRegistry._REGISTRY["160"] = {"category": "safe"}`
6. `menu_actions["160"] = (E911BSSIDReportGenerator.execute, "E911 BSSID Compliance Report")`
7. Primary key strategy in `ENDPOINT_PRIMARY_KEY_STRATEGIES`

## R8: Pagination Strategy

**Decision**: Use `mistapi.get_all()` for all paginated endpoints.

**Rationale**: This is the standard MistHelper pattern. `mistapi.get_all()` handles page iteration internally and returns the complete dataset. Already used for `listOrgSites`, `listOrgDevicesStats`, and other org-level calls throughout the codebase.
