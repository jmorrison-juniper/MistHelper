# Data Model: mistapi Upgrade Alignment

**Feature**: 017-mistapi-upgrade-alignment

## Entity Map

### Entity 1: Insights Metric Call Sites

Calls to `mistapi.api.v1.sites.insights.*` that may be affected by parameter renames.

| Menu | Function | Line | Current Positional Args | Status |
| - | - | - | - | - |
| 68 | getSiteInsightMetrics | ~14980 | (apisession, site_id, metric) | SAFE - positional matches `metrics` |
| 69 | getSiteInsightMetricsForClient | ~14235 | (apisession, site_id, client_mac, metric) | SAFE - positional matches `metrics` |
| 81 | getSiteInsightMetricsForDevice | ~15078 | (apisession, site_id, metric, device_mac) | SAFE - param still named `metric` |

**Validation Rules**: All use positional args. No keyword `metric=` usage detected.
**State Transitions**: None — no code change needed unless adding new `port_id` parameter.

### Entity 2: SLE Call Sites

Calls to org-level SLE functions. Site-level deprecated functions NOT used.

| Menu | Function | Lines | Status |
| - | - | - | - |
| 53 | listSiteSlesMetrics | varies | SAFE - not deprecated |
| 53 | getOrgSitesSle | ~13383, 13470, 13526, 13790, 13853 | SAFE - not deprecated |
| 53 | getOrgSle | ~13503, 13824 | SAFE - not deprecated |

**Validation Rules**: No deprecated function calls found in codebase.
**State Transitions**: None.

### Entity 3: Alarm Search Call Sites

| Menu | Function | Line | Current Params | New Params Available |
| - | - | - | - | - |
| 1 | searchOrgAlarms | ~11430 | site_id, type, start, end, duration, limit | group, severity, ack_admin_name, acked, search_after |

**Validation Rules**: New params are optional kwargs.
**State Transitions**: Can enhance filtering in future. No breaking change.

### Entity 4: Device Utility Command Call Sites

Commands migrable to `mistapi.device_utils.*`:

| Menu | Current API Function | Line | Target device_utils | Device Types |
| - | - | - | - | - |
| 87 | ping (via WebSocket) | WebSocketCommands | ap.ping / ex.ping / srx.ping / ssr.ping | all |
| 123 | tracerouteFromDevice | ~19234 | ap.traceroute / ex.traceroute / srx.traceroute / ssr.traceroute | all |
| 124 | showSiteGatewayOspfNeighbors | ~19260 | srx.retrieveOspfNeighbors / ssr.retrieveOspfNeighbors | gateway |
| 125 | showSiteGatewayOspfInterfaces | ~19286 | srx.retrieveOspfInterfaces / ssr.retrieveOspfInterfaces | gateway |
| 126 | showSiteGatewayOspfDatabase | ~19312 | srx.retrieveOspfDatabase / ssr.retrieveOspfDatabase | gateway |
| 127 | showSiteGatewayOspfSummary | ~19335 | srx.retrieveOspfSummary / ssr.retrieveOspfSummary | gateway |
| 128 | showSiteSsrAndSrxSessions | varies | srx.retrieveSessions / ssr.retrieveSessions | gateway |
| 129 | showSiteSsrServicePath | varies | ssr.showServicePath | ssr |
| 130 | (BGP summary) | varies | ex.retrieveBgpSummary / srx.retrieveBgpSummary / ssr.retrieveBgpSummary | switch/gateway |
| 131 | (ARP table) | varies | ap.retrieveArpTable / ex.retrieveArpTable / srx.retrieveArpTable / ssr.retrieveArpTable | all |
| 132 | (DHCP leases) | varies | ex.retrieveDhcpLeases / srx.retrieveDhcpLeases / ssr.retrieveDhcpLeases | switch/gateway |
| 136 | monitorTraffic | varies | ex.monitorTraffic / srx.monitorTraffic | switch/gateway |
| 137 | (top command) | varies | ex.topCommand / srx.topCommand | switch/gateway |
| 140 | bounceDevicePort | ~19620 | ex.bouncePort / srx.bouncePort / ssr.bouncePort | switch/gateway |
| 141 | cableTestFromSwitch | ~19641 | ex.cableTest | switch |
| 149 | clearSiteDeviceSession | ~19854 | srx.clearSessions / ssr.clearSessions | gateway |
| 150 | clearSiteDeviceMacTable | ~19877 | ex.clearMacTable | switch |
| 151 | clearSiteDeviceBpduError | varies | ex.clearBpduError | switch |
| 152 | clearSiteDeviceLearnedMacs | varies | ex.clearLearnedMac | switch |
| 153 | clearSiteDeviceHitCount | ~19961 | ex.clearHitCount | switch |
| 154 | releaseSiteDeviceDhcpLease | varies | ex.releaseDhcpLeases | switch |
| 155 | releaseSiteSsrDhcpLease | varies | srx.releaseDhcpLeases / ssr.releaseDhcpLeases | gateway |

**Commands WITHOUT device_utils equivalent** (keep raw API):
- Menu 133: 802.1X table (show) — only `clearDot1xSessions` exists (clear, not show)
- Menu 134: EVPN database
- Menu 135: DNS resolve
- Menu 138/139: locate/unlocate device
- Menu 147: clear ARP cache
- Menu 148: clear BGP routes

### Entity 5: WebSocket Connection Points

| Component | Line | Current Implementation | Target |
| - | - | - | - |
| WebSocketManager | ~3970-4013 | Raw `websocket.WebSocketApp` | `mistapi.websockets.sites.DeviceCmdEvents` |
| PacketCaptureManager | ~24579 | Raw `websocket.WebSocketApp` | `mistapi.websockets.sites.PcapEvents` |

### Entity 6: Session Initialization

| Component | Lines | Current | Target |
| - | - | - | - |
| initialize_mist_session | ~2300-2500 | No exception handling for new exceptions | Catch `ConnectionError`, `ValueError` from mistapi |

## Relationships

```text
DeviceUtilityCommands --[uses]--> WebSocketManager --[connects via]--> WebSocket
DeviceUtilityCommands --[migrates to]--> device_utils --[uses internally]--> websockets module
PacketCaptureManager --[connects via]--> WebSocket
PacketCaptureManager --[migrates to]--> websockets.sites.PcapEvents
Session Init --[may throw]--> ConnectionError, ValueError
```

## Migration Priority Matrix

| Priority | Entity | Reason |
| - | - | - |
| P0 | Session Init (Entity 6) | Exception handling prevents crashes |
| P1 | requirements.txt version pin | Foundation for all other changes |
| P1 | Insights calls (Entity 1) | Verify no breaking changes (should be safe) |
| P2 | Device Utilities (Entity 4) | Largest impact, most menu options affected |
| P2 | SLE validation (Entity 2) | Confirm no deprecated calls |
| P3 | WebSocket migration (Entity 5) | Highest complexity, requires testing |
| P3 | Alarm enhancements (Entity 3) | Optional additive feature |
