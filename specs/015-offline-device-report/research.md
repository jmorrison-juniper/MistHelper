# Research: Offline Device Report

**Date**: 2026-03-28
**Status**: Complete (all unknowns resolved during clarify phase)

## R1: API Endpoint Selection

**Decision**: `listOrgDevicesStats` (`/api/v1/orgs/{org_id}/stats/devices`)

**Rationale**: Only org-level endpoint with both `status` filter parameter (`connected`/`disconnected`/`all`) AND response fields `last_seen`, `status`, `name`, `serial`, `mac`, `model`, `type`, `site_id`.

**Alternatives considered**:
- `searchOrgDevices`: Rejected -- lacks `status` filter parameter; response schema (`ap_search`) does not include `last_seen`, `status`, `name`, or `serial` fields. Returns `timestamp` and `uptime` instead.
- `getOrgDeviceStats` (per-device): Rejected -- not an org-level bulk endpoint, would require N API calls.

**Evidence**: OpenAPI spec at `documentation/mist-api-openapi31json.json`; mistapi library inspection (`mistapi.api.v1.orgs.stats`).

## R2: Multi-Type Query Strategy

**Decision**: Single `listOrgDevicesStats` call with `type="all"`

**Rationale**: Confirmed working in production. Already used in MistHelper:
- Line 12058: `OrgDeviceStatsExporter.device_stats()` uses `type="all"`
- Lines 40445/42501: `SiteInventoryHealthAnalyzer` uses `type="all"`
- OpenAPI spec shows `type` parameter is a string with default `"ap"` but no strict enum restriction

**Alternatives considered**:
- Three separate calls per type (`ap`, `switch`, `gateway`): Rejected -- unnecessary complexity, 3x API calls, no benefit.

## R3: Pagination Strategy

**Decision**: Use `mistapi.get_all(response=resp, mist_session=apisession)` with `limit=1000`

**Rationale**: Standard MistHelper pagination pattern. The `mistapi.get_all()` function handles multi-page responses automatically. Used by `APICoreFetchUtils.all_sites_with_limit()` and `SiteInventoryHealthAnalyzer._fetch_org_stats()`.

**Evidence**: Line 42501-42503 shows the exact pattern:
```python
stats_resp = mistapi.api.v1.orgs.stats.listOrgDevicesStats(
    apisession, self.org_id, type="all", fields="*", limit=1000
)
org_stats = mistapi.get_all(response=stats_resp, mist_session=apisession)
```

## R4: Site Name Resolution

**Decision**: Pre-fetch `listOrgSites` once, build `{site_id: site_name}` lookup dict, join in-memory

**Rationale**: Standard MistHelper pattern used by multiple classes:
- `SiteInventoryHealthAnalyzer._fetch_site_lookup()` (line 42520-42530)
- `OrgDeviceStatsExporter` via `APICoreFetchUtils.all_sites_with_limit()`
- `OrgInventoryExporter.inventory_with_site_info()` (line 11790+)

**Implementation**: Use `APICoreFetchUtils.all_sites_with_limit(org_id)` which returns `list[dict]`. Build lookup:
```python
sites = APICoreFetchUtils.all_sites_with_limit(org_id)
site_lookup = {site["id"]: site.get("name", "Unknown Site") for site in sites}
```

## R5: Screen Display Pattern

**Decision**: PrettyTable with column truncation, max 50 rows displayed, full count shown

**Rationale**: PrettyTable is the standard MistHelper display library. Multiple existing operations limit screen output while noting total count (consistent UX for large datasets).

## R6: CSV Output Pattern

**Decision**: `DataExporter.write_with_format_selection()` for dual CSV/SQLite output

**Rationale**: Required by constitution (Technology Constraints: Dual Output). The method handles file path construction, data directory enforcement, and format selection based on `OUTPUT_FORMAT` global.

**CSV filename**: `OfflineDeviceReport_YYYYMMDD_HHMMSS.csv` (timestamped, no overwrite)
**API function name for PK strategy**: `listOrgDevicesStats` (existing composite PK: `device_id`, `timestamp`)

## R7: Class Placement in MistHelper.py

**Decision**: New class `OfflineDeviceReporter` placed near other org-level reporting classes (after `OrgDeviceStatsExporter`, before `MapsManagerLauncher`)

**Rationale**: Follows convention -- org-level operations grouped together. The class handles its own API calls, data processing, display, and CSV export. No standalone wrapper functions.
