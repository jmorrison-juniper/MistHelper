# Research: mistapi v0.59.1-v0.62.0 Upgrade Alignment

**Date**: 2026-03-29  
**Updated**: 2026-06-16  
**Feature**: 017-mistapi-upgrade-alignment  
**GitHub Issue**: #260

## Addendum (2026-06-16): Post-release floor bump to mistapi 0.63.1

**Problem**: The original alignment work stopped at `mistapi>=0.62.0`, but upstream advanced to `0.63.1` with additive WebSocket/device-utils error reporting and refreshed generated bindings.

**Finding**: Live validation against a real `.env` session succeeded for `initialize_mist_session()`, `getSelf()`, `listOrgSites()`, `getOrgInventory()`, `searchOrgWirelessClients()`, `searchOrgAlarms()`, `searchOrgEvents()`, `listOrgTickets()`, `searchSiteWirelessClients()`, and `searchSiteWiredClients()`. No MistHelper code changes were required beyond restoring dependency floor alignment.

**Decision**: Raise the dependency floor again to `mistapi>=0.63.1` and keep `websocket-client>=1.8.0`. Treat `0.63.1` as a safe additive bump for current MistHelper read paths.

**Risk**: LOW — upstream changes exercised in live smoke were backward-compatible for current MistHelper usage.

## Decision 1: Insights API Parameter Migration

**Problem**: `getSiteInsightMetrics()` and `getSiteInsightMetricsForClient()` changed `metric` (path param) to `metrics` (query param) in v0.61.2. MistHelper currently passes `metric` as a positional arg.

**Finding**: Verified via `inspect.signature()` on installed mistapi v0.61.3:
- `getSiteInsightMetrics(mist_session, site_id, metrics, ...)` — 3rd positional arg is `metrics`
- `getSiteInsightMetricsForClient(mist_session, site_id, client_mac, metrics, ...)` — 4th positional arg is `metrics`
- `getSiteInsightMetricsForDevice(mist_session, site_id, metric, device_mac, ...)` — still uses `metric` (singular)
- `getSiteInsightMetricsForGateway(mist_session, site_id, device_id, metrics, ...)` — uses `metrics` (plural)
- `getSiteInsightMetricsForSwitch(mist_session, site_id, metric, device_mac, ...)` — still uses `metric` (singular)
- `getSiteInsightMetricsForMxEdge(mist_session, site_id, metric, device_mac, ...)` — still uses `metric` (singular)
- New: `getSiteInsightMetricsForAP(mist_session, site_id, device_id, metrics, ...)` — new function

**Decision**: Since MistHelper passes metrics as positional args (not keyword), the existing calls will work with the renamed parameter. However, we should add the new `port_id` parameter where available (Device, Switch, Gateway, MxEdge functions) and add support for the new `getSiteInsightMetricsForAP()` function.

**Impact on MistHelper**:
- Menu 68 (Site Insight Metrics): Uses `getSiteInsightMetrics(apisession, site_id, metric)` — positional, works unchanged
- Menu 69 (Client Insights): Uses `getSiteInsightMetricsForClient(apisession, site_id, client_mac, metric)` — positional, works unchanged
- Menu 81 (Device Insights): Uses `getSiteInsightMetricsForDevice(apisession, site_id, metric, device_mac)` — unchanged, but can add `port_id`
- New opportunity: Can add `getSiteInsightMetricsForAP()` for AP-specific metrics

**Risk**: LOW — positional args match. No breaking change for existing calls.

## Decision 2: SLE Function Deprecation Migration

**Problem**: `getSiteSleSummary` and `getSiteSleClassifierDetails` deprecated in v0.59.2, replaced by `getSiteSleSummaryTrend` and `getSiteSleClassifierSummaryTrend`. Removal planned for v0.65.0.

**Finding**: Both old and new functions exist with identical signatures:
- `getSiteSleSummary(mist_session, site_id, scope, scope_id, metric, start, end, duration)`
- `getSiteSleSummaryTrend(mist_session, site_id, scope, scope_id, metric, start, end, duration)`
- Same pattern for classifier functions

**Decision**: Replace deprecated calls with new function names. Same signatures — drop-in replacement.

**Impact on MistHelper**: MistHelper currently uses `getOrgSitesSle` and `getOrgSle` (org-level functions), NOT the deprecated site-level functions. However, `listSiteSlesMetrics` is used in Menu 53. No direct usage of `getSiteSleSummary` found in the code — the deprecation has no immediate impact but we should ensure future code uses the Trend variants.

**Risk**: NONE for current code. Preventive for future additions.

## Decision 3: Exception-Based Error Handling (v0.59.5)

**Problem**: mistapi v0.59.5 replaced `sys.exit()` calls with proper exceptions:
- `ConnectionError` for proxy/connection errors
- `ValueError` for invalid API tokens (401 status)

**Finding**: MistHelper's `initialize_mist_session()` and `initialize_mist_session_interactive()` functions create `mistapi.APISession()` and call authentication methods. These could now throw exceptions instead of calling `sys.exit()`.

**Decision**: Wrap session initialization in try/except blocks catching `ConnectionError` and `ValueError`, displaying clear user-facing messages.

**Impact on MistHelper**: Session initialization code (around line 2300-2500) needs exception handling updates.

**Risk**: MEDIUM — if not handled, uncaught exceptions could crash with unhelpful tracebacks instead of the previous `sys.exit()` behavior.

## Decision 4: Alarm Search Enhancement (v0.59.5)

**Problem**: `searchOrgAlarms()` gained new parameters: `group`, `severity`, `ack_admin_name`, `acked`, `search_after`.

**Finding**: Verified signature:
```
searchOrgAlarms(mist_session, org_id, site_id=None, group=None, severity=None, 
                type=None, ack_admin_name=None, acked=None, start=None, end=None, 
                duration=None, limit=None, sort=None, search_after=None)
```

MistHelper Menu 1 calls `searchOrgAlarms` and exports all returned data fields. The new fields will automatically appear in exported data if the API returns them. The new filter parameters can be optionally passed but MistHelper exports ALL alarms (no filtering), so the main benefit is the response now including these fields.

**Decision**: No code change needed for Menu 1 — the new response fields are automatically captured. Consider adding `search_after` pagination for large alarm datasets.

**Risk**: NONE — additive fields are transparent.

## Decision 5: Device Utility Module Migration (v0.61.0)

**Problem**: MistHelper's `DeviceUtilityCommands` class (Menu 123-157) calls low-level `mistapi.api.v1.sites.devices.*` functions. The new `mistapi.device_utils` module provides high-level wrappers.

**Finding**: Available device_utils functions mapped to current DeviceUtilityCommands:

| Menu | Current API Call | device_utils Replacement | Module |
| - | - | - | - |
| 123 | tracerouteFromDevice | ap.traceroute / ex.traceroute / srx.traceroute / ssr.traceroute | ap/ex/srx/ssr |
| 124 | showSiteGatewayOspfNeighbors | srx.retrieveOspfNeighbors / ssr.retrieveOspfNeighbors | srx/ssr |
| 125 | showSiteGatewayOspfInterfaces | srx.retrieveOspfInterfaces / ssr.retrieveOspfInterfaces | srx/ssr |
| 126 | showSiteGatewayOspfDatabase | srx.retrieveOspfDatabase / ssr.retrieveOspfDatabase | srx/ssr |
| 127 | showSiteGatewayOspfSummary | srx.retrieveOspfSummary / ssr.retrieveOspfSummary | srx/ssr |
| 128 | showSiteSsrAndSrxSessions | srx.retrieveSessions / ssr.retrieveSessions | srx/ssr |
| 129 | showSiteSsrServicePath | ssr.showServicePath | ssr |
| 130 | (BGP summary) | ex.retrieveBgpSummary / srx.retrieveBgpSummary / ssr.retrieveBgpSummary | ex/srx/ssr |
| 131 | (ARP table) | ex.retrieveArpTable / srx.retrieveArpTable / ssr.retrieveArpTable / ap.retrieveArpTable | all |
| 132 | (DHCP leases) | ex.retrieveDhcpLeases / srx.retrieveDhcpLeases / ssr.retrieveDhcpLeases | ex/srx/ssr |
| 133 | (802.1X table) | ex.clearDot1xSessions (clear only, no show) | ex |
| 134 | (EVPN database) | No device_utils equivalent | N/A |
| 135 | (DNS resolve) | No device_utils equivalent | N/A |
| 136 | monitorTraffic | ex.monitorTraffic / srx.monitorTraffic | ex/srx |
| 137 | (top command) | ex.topCommand / srx.topCommand | ex/srx |
| 138 | startSiteLocateDevice | No device_utils equivalent | N/A |
| 139 | stopSiteLocateDevice | No device_utils equivalent | N/A |
| 140 | bounceDevicePort | ex.bouncePort / srx.bouncePort / ssr.bouncePort | ex/srx/ssr |
| 141 | cableTestFromSwitch | ex.cableTest | ex |
| 147 | clearSiteDeviceArpCache | No separate device_utils (use retrieveArpTable) | N/A |
| 148 | clearSiteDeviceBgpRoutes | No device_utils equivalent | N/A |
| 149 | clearSiteSsrAndSrxSession | srx.clearSessions / ssr.clearSessions | srx/ssr |
| 150 | clearSiteDeviceMacTable | ex.clearMacTable | ex |
| 151 | clearSiteDeviceBpduError | ex.clearBpduError | ex |
| 152 | clearSiteDeviceLearnedMacs | ex.clearLearnedMac | ex |
| 153 | clearSiteDeviceHitCount | ex.clearHitCount | ex |
| 154 | releaseSiteDeviceDhcpLease | ex.releaseDhcpLeases | ex |
| 155 | releaseSiteSsrDhcpLease | srx.releaseDhcpLeases / ssr.releaseDhcpLeases | srx/ssr |
| 87 | ping | ap.ping / ex.ping / srx.ping / ssr.ping | all |

**Decision**: Migrate commands that have direct device_utils equivalents. Keep low-level API calls for commands without device_utils coverage (EVPN, DNS, locate/unlocate, clear ARP, clear BGP). The device_utils functions return `UtilResponse` objects with `.ws_data`, `.done`, `.wait()`, `.receive()` — this changes the data extraction pattern.

**Rationale**: device_utils handles WebSocket plumbing, retries, and response parsing automatically. Reduces ~200 lines of custom WebSocket management code.

**Alternatives Rejected**: 
- Keep all raw API calls: rejected because device_utils provides auto-reconnect, thread-safety, and structured responses that improve reliability.
- Migrate everything including unsupported commands: rejected because some commands have no device_utils equivalent.

## Decision 6: WebSocket Module Migration (v0.61.0, v0.61.2, v0.61.3)

**Problem**: MistHelper's `WebSocketManager` uses raw `websocket.WebSocketApp`. The new `mistapi.websockets` module provides managed WebSocket channels.

**Finding**: Available channels:
- `sites.DeviceCmdEvents` — device command results (replaces current cmd channel subscription)
- `sites.PcapEvents` — packet capture events
- `sites.DeviceStatsEvents` — device stats streaming

The current `WebSocketManager` (line 3945) handles: auth headers, channel subscription, message routing, command result collection. The new `mistapi.websockets` module handles all of this automatically plus: auto-reconnect, bounded message queues, thread-safety, header redaction.

**Decision**: Phase the migration:
1. **Phase A**: Add `auto_reconnect=True` and `queue_maxsize=1000` for new device_utils calls (these use websockets internally)
2. **Phase B**: Migrate `PacketCaptureManager` to use `sites.PcapEvents` channel
3. **Phase C**: Migrate `WebSocketCommands` (Menu 5-8) to use `sites.DeviceCmdEvents` channel

**Rationale**: Device utility commands (Phase A) automatically use the new module. Packet captures (Phase B) benefit most from auto-reconnect. WebSocket show commands (Phase C) are lowest priority since device_utils may replace them.

**Risk**: MEDIUM — WebSocket module migration changes connection lifecycle. Testing must verify no regressions in real-time streaming.

## Decision 7: search_after Pagination (v0.59.1)

**Problem**: All search endpoints gained `search_after` parameter for cursor-based pagination. Current MistHelper uses `mistapi.get_all()` which handles offset-based pagination.

**Finding**: `search_after` is a cursor token from the API response for efficient deep pagination. However, `mistapi.get_all()` already handles pagination automatically. The `search_after` parameter is useful when manually paginating or when offset-based pagination hits limits.

**Decision**: No immediate change to pagination strategy. `mistapi.get_all()` continues to work. Consider adding `search_after` support to the `APICoreFetchUtils` pagination helpers as an optimization for very large datasets (>10,000 records).

**Risk**: NONE — existing pagination works.

## Decision 8: Version Pinning Strategy

**Problem**: FR-009 requires `mistapi>=0.61.3` as minimum. FR-010 requires graceful fallback for older versions. These are contradictory.

**Decision**: Hard minimum with startup version check. Set `mistapi>=0.62.0` in `requirements.txt`. Add a version check at startup that prints upgrade instructions and exits gracefully if the installed version is too old. Remove FR-010 (no runtime fallback code). This avoids maintaining two code paths.

**Rationale**: MistHelper already requires Python 3.13+. A hard SDK minimum is consistent. Users with older mistapi get a clear error message telling them to upgrade. Dead fallback code is worse than a clean version gate.

---

## Discovery 9: v0.61.4 WebSocket Reconnect Hardening

**Finding**: v0.61.4 (April 1, 2026) added two important WebSocket improvements:

1. `max_reconnect_backoff` parameter — caps the exponential backoff delay to prevent multi-minute waits:
   ```python
   ws = mistapi.websockets.sites.PcapEvents(..., auto_reconnect=True, max_reconnect_backoff=60.0)
   ```
2. `max_reconnect_attempts=0` enables unlimited reconnection — suitable for long-running captures and menu sessions.

**Impact on MistHelper**:
- `PacketCaptureManager` should use `max_reconnect_attempts=0` and `max_reconnect_backoff=60.0` to survive transient cloud disconnects during captures that can run for hours.
- Device command WebSocket sessions (Menu 5-8) should use `max_reconnect_attempts=3` with `max_reconnect_backoff=30.0` — short commands do not need unlimited retries.
- `WebSocketManager` constructor should expose these as configurable parameters.

**Decision**: Update `PacketCaptureManager` WebSocket init to `max_reconnect_attempts=0, max_reconnect_backoff=60.0`. Update `WebSocketManager` to `max_reconnect_attempts=3, max_reconnect_backoff=30.0`.

**Risk**: LOW — additive parameters, defaults are backward-compatible.

---

## Discovery 10: v0.61.5 Privileges Fix (No Action Required)

**Finding**: v0.61.5 (April 22, 2026) fixed `Privileges.__init__()` to handle lists containing already-instantiated `_Privilege` objects instead of only raw dicts. This was a mistapi internal bug.

**Impact on MistHelper**: None. MistHelper does not instantiate `Privileges` directly — it receives privilege data from `mistapi.APISession` which handles instantiation internally. The fix resolves an edge case that could cause errors when re-using session objects across certain initialization patterns.

**Decision**: No code changes in MistHelper. Note the fix in the version pin (`mistapi>=0.62.0`) which includes this fix transitively.

**Risk**: NONE.

---

## Discovery 11: v0.62.0 New Endpoints — Prioritization

**Finding**: v0.62.0 (May 1, 2026) added the following endpoint groups. Prioritized by NOC value:

| Priority | Endpoint Group | New Functions | MistHelper Menu Target |
| - | - | - | - |
| HIGH | NAC CoA | `sendOrgNacClientCoA`, `sendSiteNacClientCoA` | New menu option under NAC operations |
| HIGH | MxEdge Upgrade Lifecycle | `updateOrgMxEdgeUpgrade`, `cancelOrgMxEdgeUpgrade`, `listSiteMxEdgeUpgrades`, `getSiteMxEdgeUpgrade`, `updateSiteMxEdgeUpgrade`, `cancelSiteMxEdgeUpgrade` | Extend existing MxEdge menus |
| MEDIUM | E911 Report Management | `getOrgE911Report`, `enableOrgE911Report`, `disableOrgE911Report` | New org export/compliance menu option |
| MEDIUM | Site Auto-Map Assignment | `startSiteAutoMapAssignment`, `getSiteAutoMapAssignmentStatus`, `cancelSiteAutoMapAssignment`, `applySiteAutoMapAssignment`, `clearSiteAutoMapAssignment` | New site maps operations menu |
| MEDIUM | Channel Scores | `getSiteChannelScores` | Extend RF/RRM data export |
| LOW | Zigbee Join | `enableSiteDeviceZigbeeJoin` | New IoT device management option |
| LOW | IoT Endpoint Search | `searchSiteIotEndpoints` | New IoT search option |
| LOW | SSO Admin Removal | `deleteOrgSsoAdmins`, `deleteMspSsoAdmins` | Destructive — needs explicit confirmation |

**Decision**: Implement HIGH and MEDIUM priority endpoints in the initial implementation. LOW priority endpoints deferred to follow-on PR. SSO admin removal requires additional safety review before exposing.

**Additional v0.62.0 improvements** (no new menu options needed, but code should use them):
- `countOrgInventory()` now supports `site_id`, `model`, `version`, `status` filters — update Menu 11 inventory export to pass these when provided by user
- `countOrgAuditLogs()` and `listOrgAuditLogs()` now map to corrected API paths — verify Menu 66 (audit logs) uses the updated functions
- Expanded band enum values (`5-dedicated`, `5-selectable`, `6-dedicated`, `6-selectable`) across wireless client and RRM APIs — no code change needed, values flow through transparently

**Risk**: LOW for read endpoints. MEDIUM for CoA and MxEdge lifecycle (side effects on live devices).

**Changelog reference**: `data/mistapi-changelog-0.57.2-to-0.62.0.md`
