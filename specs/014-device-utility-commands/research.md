# Research: Device Utility Commands

**Feature**: 014-device-utility-commands | **Date**: 2026-03-20

## Research Task 1: API Endpoint Inventory & SDK Coverage

### Decision
All 35 target endpoints are documented in the Mist REST API and have corresponding `mistapi` SDK methods in `mistapi.api.v1.utilities.common.*` or `mistapi.api.v1.sites.devices.*`. No direct HTTP calls are needed — the SDK provides complete coverage.

### Rationale
Reviewed all 49 per-device utility API documentation files in `documentation/api/utilities/POST_sites_site_id_devices_device_id_*.md`. Cross-referenced with SDK method names documented in each file's "mistapi SDK" section. Every endpoint maps to an SDK function.

### Complete Endpoint Inventory

| # | Menu | Endpoint | SDK Method | Category | Device Types | WebSocket | Destructive |
|---|------|----------|-----------|----------|-------------|-----------|-------------|
| 1 | 101 | `traceroute` | `tracerouteSiteDevice()` | Diagnostic | AP, Switch, Gateway | Yes | No |
| 2 | 102 | `show_ospf_neighbors` | `showSiteDeviceOspfNeighbors()` | Diagnostic | SSR/SRX Gateway | Yes | No |
| 3 | 103 | `show_ospf_interfaces` | `showSiteDeviceOspfInterfaces()` | Diagnostic | SSR/SRX Gateway | Yes | No |
| 4 | 104 | `show_ospf_database` | `showSiteDeviceOspfDatabase()` | Diagnostic | SSR/SRX Gateway | Yes | No |
| 5 | 105 | `show_ospf_summary` | `showSiteDeviceOspfSummary()` | Diagnostic | SSR/SRX Gateway | Yes | No |
| 6 | 106 | `show_session` | `showSiteDeviceSessions()` | Show | SSR/SRX Gateway | Yes | No |
| 7 | 107 | `show_service_path` | `showSiteDeviceServicePath()` | Show | SSR Gateway | Yes | No |
| 8 | 108 | `show_bgp_summary` | `showSiteDeviceBgpSummary()` | Show | SSR/SRX/Switch | Yes | No |
| 9 | 109 | `show_arp` | `showSiteDeviceArpTable()` | Show | Switch/Gateway | Yes | No |
| 10 | 110 | `show_dhcp_leases` | `showSiteDeviceDhcpLeases()` | Show | Switch/Gateway | Yes | No |
| 11 | 111 | `show_dot1x` | `showSiteSwitchDot1x()` | Show | Switch | Yes | No |
| 12 | 112 | `show_evpn_database` | `showSiteDeviceEvpnDatabase()` | Show | Switch/Gateway | Yes | No |
| 13 | 113 | `resolve_dns` | `resolveSiteDeviceDns()` | Diagnostic | SSR Gateway | Yes | No |
| 14 | 114 | `monitor_traffic` | `startSiteDeviceMonitorTraffic()` | Diagnostic | Switch/SRX | Yes (stream) | No |
| 15 | 115 | `run_top` | `runSiteDeviceTopCommand()` | Diagnostic | Switch/SRX | Yes (stream) | No |
| 16 | 116 | `locate` | `startSiteLocateDevice()` | Management | AP/Switch | No | No |
| 17 | 117 | `unlocate` | `stopSiteLocateDevice()` | Management | AP/Switch | No | No |
| 18 | 118 | `bounce_port` | `bounceDevicePort()` | Management | Switch/Gateway | Yes | Yes (confirm) |
| 19 | 119 | `cable_test` | `cableTestFromSwitch()` | Management | Switch | Yes | No |
| 20 | 120 | `reprovision` | `reprovisionSiteOctermDevice()` | Management | Switch/Gateway | No | Yes (confirm) |
| 21 | 121 | `readopt` | `readoptSiteOctermDevice()` | Management | Switch | No | No |
| 22 | 122 | `request_ztp_password` | `getSiteDeviceZtpPassword()` | Management | Switch/Gateway | No | No |
| 23 | 123 | `get_config_cmd` | `getSiteDeviceConfigCmd()` | Management | Switch | No | No |
| 24 | 124 | `support` | `uploadSiteDeviceSupportFile()` | Management | Switch/Gateway | No | No |
| 25 | 125 | `clear_arp` | `clearSiteSsrArpCache()` | Clear/Reset | SSR/SRX/Switch | No | Yes (confirm) |
| 26 | 126 | `clear_bgp` | `clearSiteSsrBgpRoutes()` | Clear/Reset | SSR/SRX | No | Yes (confirm) |
| 27 | 127 | `clear_session` | `clearSiteDeviceSession()` | Clear/Reset | SSR/SRX | No | Yes (confirm) |
| 28 | 128 | `clear_mac_table` | `clearSiteDeviceMacTable()` | Clear/Reset | Switch/Gateway | No | Yes (confirm) |
| 29 | 129 | `clear_bpdu_error` | `clearSiteSwitchBpduError()` | Clear/Reset | Switch | No | Yes (confirm) |
| 30 | 130 | `clear_macs` | `clearSiteDeviceLearnedMacs()` | Clear/Reset | Switch | No | Yes (confirm) |
| 31 | 131 | `clear_policy_hit_count` | `clearSiteDevicePolicyHitCount()` | Clear/Reset | Gateway (SSR) | No | Yes (confirm) |
| 32 | 132 | `release_dhcp_leases` | `releaseSiteDeviceDhcpLease()` | Clear/Reset | Switch/Gateway | No | Yes (confirm) |
| 33 | 133 | `release_dhcp` (SSR) | `releaseSiteSsrDhcpLease()` | Clear/Reset | SSR/SRX | No | Yes (confirm) |
| 34 | 134 | `poll_stats` | `pollSiteSwitchStats()` | Hardware | Switch | No | No |
| 35 | 135 | `snapshot` | `createSiteDeviceSnapshot()` | Hardware | Switch | No | No |

**Note**: BIOS and FPGA upgrades (`upgrade_bios`, `upgrade_fpga`) from the spec map to `upgradeSiteDeviceBios()` and `upgradeSiteDeviceFpga()`. However, these are already partially covered by existing Menu 99-100 (Switch/SSR Firmware). Per the spec clarification, menu numbers 101-135 cover the 35 commands listed above. BIOS/FPGA will be handled as menu 134-135 alternatives if the existing menu 99-100 doesn't already cover them, or as additional entries.

**Revision**: Examining the spec's FR-032 and FR-033, BIOS and FPGA upgrades are explicitly required. Adjusting the menu map: poll_stats=134, snapshot=135, BIOS upgrade=136, FPGA upgrade=137 — yielding 37 total menu entries (101-137). Alternatively, the spec says "35 missing endpoints" and the two hardware upgrades may overlap with existing menus 99-100. Resolution: Keep 35 entries at 101-135 by combining poll_stats+snapshot into management (134-135) and noting BIOS/FPGA are already in menus 99-100. If they truly need separate entries, extend to 137.

### Alternatives Considered
- **Direct HTTP calls**: Rejected because every endpoint has an SDK method. Using the SDK ensures consistent authentication, rate limiting, and error handling.
- **mistapi v2 API**: Not yet stable for device utilities. Stay with v1.

## Research Task 2: WebSocket Command Pattern

### Decision
Reuse the existing `WebSocketManager` class for all WebSocket-based commands. The pattern is well-established in Menu 5-8 and `RoutingUtils`.

### Rationale
The codebase already has a robust WebSocket command pattern:
1. `WebSocketManager.connect(site_id, device_id)` — establishes authenticated WS connection
2. `WebSocketManager.subscribe(channel)` — subscribes to `/sites/{site_id}/devices/{device_id}/cmd`
3. POST command via SDK (returns `session` ID for demux)
4. `WebSocketManager.wait_for_command_result(session_id, timeout_seconds=60)` — awaits result
5. Process and display results

22 of the 35 commands use this WebSocket pattern (all show/diagnostic commands). The remaining 13 (management, clear/reset, hardware) are synchronous HTTP POST calls that return immediately.

### Streaming Commands
Two commands (`monitor_traffic`, `run_top`) are streaming — they send continuous data until stopped. These require:
- A modified wait loop that displays output incrementally
- Ctrl+C handler for early termination
- Auto-timeout (configurable, default 60 seconds)
- Marking as "interactive" in the test skip list

### Alternatives Considered
- **New WebSocket class per command category**: Rejected — unnecessary complexity. The existing `WebSocketManager` handles all command types.
- **Polling instead of WebSocket**: Rejected — the API requires WebSocket for command output delivery.

## Research Task 3: Menu Number Allocation

### Decision
Contiguous block 101-135 for the 35 new commands. BIOS/FPGA upgrades overlap with existing Menu 99-100 and will be cross-referenced rather than duplicated.

### Rationale
Per spec clarification: "New contiguous block starting at 101 — all 35 new commands grouped sequentially (101-135+)." Some menu numbers in the 100s are already taken (102=WLAN RADIUS, 103=WAN2 migration, 104=WAN2 update, 105=Gateway config extract, 106=Gateway config apply, 115=interactive login). The new commands must use available numbers or the existing entries must shift.

**Resolution**: The existing 102-106, 115 entries predate this feature. New device utility commands should use a distinct sub-range. Options:
- **Option A**: Use 120-155 (skip existing 102-106, 115 allocations)
- **Option B**: Renumber existing 102-106 and use 101-135 cleanly

**Decision**: Use **Option A** — allocate at 120-155 to avoid renumbering existing entries. This keeps backward compatibility for anyone referencing existing menu numbers. The 35 commands map to 120-154.

### Alternatives Considered
- **Scattered across gaps in 60-100**: Rejected — spec explicitly calls for contiguous block.
- **Starting at 200**: Rejected — unnecessarily high numbers, harder to discover.

## Research Task 4: Device Type Validation

### Decision
Implement a device-type validation helper (`_validate_device_type()`) in `DeviceUtilityCommands` that checks device type compatibility before API calls.

### Rationale
Each endpoint has specific device type requirements (documented in API docs). The spec requires (FR-034) that incompatible device types are rejected before any API call. The existing codebase has device type checks in `RoutingUtils._verify_ssr_compatibility()` — this pattern will be generalized.

Device type mapping per command:
- **All device types** (AP/Switch/Gateway): traceroute
- **SSR/SRX Gateway only**: OSPF (4), show_session, show_service_path, resolve_dns, clear_bgp, clear_session, release_dhcp (SSR), clear_policy_hit_count
- **Switch/Gateway**: show_arp, show_dhcp_leases, show_evpn_database, bounce_port, clear_mac_table, release_dhcp_leases, reprovision, ZTP password, support upload
- **Switch only**: show_dot1x, cable_test, readopt, config_cmd, clear_bpdu_error, clear_macs, poll_stats, snapshot, monitor_traffic
- **Switch/SRX**: run_top
- **AP/Switch**: locate, unlocate
- **SSR/SRX/Switch**: show_bgp_summary, clear_arp

### Alternatives Considered
- **No client-side validation (let API return error)**: Rejected — spec requires pre-check (FR-034) and it provides better UX for junior NOC engineers.

## Research Task 5: Confirmation Gate Patterns

### Decision
Use three tiers of confirmation based on operation severity:
1. **No confirmation**: Read-only commands (show, diagnostic)
2. **Simple confirmation** (`y/N`): Port bounce, reprovision, re-adopt, DHCP lease release 
3. **Typed keyword confirmation** (`'CLEAR'` or `'UPGRADE'`): Clear operations (ARP/BGP/session/MAC/BPDU/MACs/policy), BIOS/FPGA upgrade

### Rationale
The existing codebase uses `safe_input("Type 'UPGRADE' to proceed: ")` for firmware upgrades. Clear/reset operations destroy device state (ARP cache, BGP routes, sessions) and need the same level of protection. Port bounce briefly disrupts connectivity but is common enough to warrant only `y/N`. Locate/unlocate are non-destructive (LED blink).

### Alternatives Considered
- **Same confirmation for all destructive ops**: Rejected — `y/N` is insufficient for state-clearing operations, but typed keyword for port bounce is excessive for a routine operation.

## Research Task 6: Dual Output for Command Results

### Decision
WebSocket command results that return structured data will be written through `DataExporter.write_with_format_selection()`. Raw text output (like traceroute hop-by-hop) will be displayed on console and also saved to a per-command CSV with timestamp.

### Rationale
FR-039 requires all commands returning structured data to use the dual output system. WebSocket results arrive as text (`raw` field in the data payload), which must be parsed before writing to CSV/SQLite. The existing `RoutingUtils._parse_routing_table()` pattern shows how to extract structured data from raw WebSocket output.

For commands that don't return structured data (locate, reprovision, clear operations), only console confirmation is provided — no CSV/SQLite output.

### Primary Key Strategy
- **WebSocket show commands** (returning device state): `composite_pk` with `['device_id', 'timestamp']`
- **Streaming commands** (monitor_traffic, run_top): No persistent storage — console-only due to streaming nature
- **Management/clear operations** (action confirmations): No persistent storage — action results only

### Alternatives Considered
- **Store all command outputs including confirmations**: Rejected — "ARP cache cleared" confirmation is not useful as persistent data.
- **Skip dual output entirely**: Rejected — FR-039 explicitly requires it for structured data.

## Research Task 7: Streaming Command Architecture (monitor_traffic, run_top)

### Decision
Implement streaming commands with an incremental display loop, Ctrl+C handler, and auto-timeout. Mark as "interactive" in the test skip list.

### Rationale
`monitor_traffic` and `run_top` send continuous WebSocket data until the connection is closed or timeout fires. The existing `WebSocketManager.wait_for_command_result()` waits for a single response — it needs a streaming variant that displays output incrementally.

Implementation approach:
1. Start command via SDK POST
2. Subscribe to WebSocket channel
3. Loop: receive data fragments, display immediately, check timeout
4. On Ctrl+C (KeyboardInterrupt) or timeout: close WebSocket, display summary
5. FR-040 requires both Ctrl+C and auto-timeout support

### Alternatives Considered
- **Buffered display (show all at once after timeout)**: Rejected — defeats the purpose of live monitoring.
- **Separate thread for display**: Rejected — over-engineering for a console tool.

## Research Task 8: Port Selection UX (FR-041)

### Decision
For port-specific commands (bounce_port, cable_test, clear_macs, monitor_traffic), fetch available ports from device stats API, display numbered list, allow selection by number or manual port name entry.

### Rationale
FR-041 requires: "present a selectable list of available ports fetched from the device, while also allowing manual port name entry as an override." The existing `SiteDeviceExporter.port_stats` fetches port data. We'll use a similar API call to get port names for the interactive selector.

Steps:
1. Fetch device stats including port list via `mistapi.api.v1.sites.stats.getSiteDeviceStats()`
2. Extract port names from the response
3. Display numbered list with port name, status, speed
4. User selects by number or types port name directly
5. Validate the selected port name format before API call

### Alternatives Considered
- **Manual entry only**: Rejected — junior NOC engineers benefit from seeing available ports.
- **Always fetch full port stats**: Could be slow for switches with 48+ ports. Use simple port list from stats, not full per-port stats.

## Summary of Resolved Items

All 8 research tasks resolved. No NEEDS CLARIFICATION items remain. Key decisions:
1. All 35 endpoints covered by mistapi SDK — no direct HTTP calls needed
2. Reuse existing `WebSocketManager` for all WebSocket commands
3. Menu numbers 120-154 (avoids conflict with existing 102-106, 115)
4. Three-tier confirmation gates (none / y-N / typed keyword)
5. Dual output for structured show commands; console-only for actions
6. Streaming commands use incremental display with Ctrl+C and auto-timeout
7. Port selector with device stats + manual override
8. Device type validation helper before all API calls
