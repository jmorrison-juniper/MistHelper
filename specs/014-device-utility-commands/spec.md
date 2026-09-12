# Feature Specification: Device Utility Commands — Complete Mist API Coverage

**Feature Branch**: `014-device-utility-commands`
**Created**: 2026-03-20
**Status**: Draft
**Input**: User description: "Add complete coverage of all 35 missing Mist API device utility command endpoints as new menu options in MistHelper, covering diagnostics, OSPF, clear/reset, device management, and switch hardware operations."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Run Traceroute from a Device (Priority: P1)

A NOC engineer investigating a connectivity issue between a branch site and a cloud service needs to run a traceroute from the device itself (not from their laptop) to see the actual path the device's traffic takes. They select a site, pick the target device (AP, switch, or gateway), enter a destination, and see hop-by-hop results in real time.

**Why this priority**: Traceroute is the single most-requested missing diagnostic. It applies to all three device types (AP, switch, gateway) and is used daily in NOC troubleshooting workflows.

**Independent Test**: Can be tested by selecting any device, entering a known destination (e.g., 8.8.8.8), and confirming hop-by-hop output appears with RTT values.

**Acceptance Scenarios**:

1. **Given** authenticated session and a connected device, **When** user selects traceroute and enters a valid destination, **Then** hop-by-hop results display with IP addresses and round-trip times
2. **Given** an unreachable destination, **When** user runs traceroute, **Then** output shows asterisks (*) for non-responding hops and does not hang indefinitely
3. **Given** user enters an invalid destination (empty, malformed), **When** traceroute is requested, **Then** input is rejected with a clear message before any API call is made

---

### User Story 2 — OSPF Troubleshooting on SSR/SRX Gateways (Priority: P1)

A network engineer troubleshooting WAN routing on an SSR or SRX gateway needs to inspect OSPF state — neighbors, interfaces, database, and summary. Currently they must SSH into devices directly. With dedicated menu options for each OSPF view, they can inspect OSPF state through MistHelper's standard workflow: pick a site, pick a gateway, see results.

**Why this priority**: OSPF is the dominant routing protocol in enterprise WAN. Having zero OSPF visibility while BGP routing (Menu 8) is already supported creates a major troubleshooting gap for gateway-heavy deployments.

**Independent Test**: Can be tested by selecting any SSR/SRX gateway running OSPF, running each of the four OSPF commands, and confirming structured output matches device state.

**Acceptance Scenarios**:

1. **Given** an SSR/SRX gateway with OSPF configured, **When** user selects "show OSPF neighbors", **Then** output displays neighbor router IDs, states, uptimes, and interface associations
2. **Given** an SSR/SRX gateway with OSPF configured, **When** user selects "show OSPF interfaces", **Then** output displays interface names, area IDs, types, and IP addresses
3. **Given** an SSR/SRX gateway with OSPF configured, **When** user selects "show OSPF database", **Then** output displays the link-state database entries
4. **Given** an SSR/SRX gateway with OSPF configured, **When** user selects "show OSPF summary", **Then** output displays router ID, ABR type, and area summary
5. **Given** a device that is not an SSR/SRX or has no OSPF configured, **When** user attempts any OSPF command, **Then** a clear message indicates the command is not applicable

---

### User Story 3 — SSR Session and Service Path Inspection (Priority: P1)

A network engineer diagnosing traffic flow issues on an SSR gateway needs to view active sessions and service paths. These are core SSR troubleshooting tools — sessions show what traffic is flowing and service paths show how it's being routed through the SSR fabric.

**Why this priority**: `show_session` and `show_service_path` are the two most fundamental SSR-specific diagnostic commands. Without them, engineers cannot effectively troubleshoot SSR traffic forwarding.

**Independent Test**: Can be tested by selecting an SSR gateway with active traffic, running each command, and confirming session/path data appears.

**Acceptance Scenarios**:

1. **Given** an SSR gateway with active sessions, **When** user selects "show sessions", **Then** output displays active session details including service name, source, destination, and state
2. **Given** an SSR gateway with active sessions, **When** user selects "show sessions" and enters optional filters (service name, session ID, node), **Then** only matching sessions are displayed
3. **Given** an SSR gateway with active sessions, **When** user selects "show sessions" and presses Enter through all filter prompts, **Then** all sessions are displayed unfiltered
4. **Given** an SSR gateway, **When** user selects "show service path", **Then** output displays service path information including service names, next hops, and path metrics
5. **Given** an SSR gateway with no active sessions, **When** user runs show sessions, **Then** output clearly indicates no sessions are active (not an error)

---

### User Story 4 — Structured Show Commands (BGP Summary, ARP Table, DHCP Leases, 802.1X, EVPN) (Priority: P2)

A NOC engineer needs quick access to common device state tables — BGP summary, ARP table, DHCP leases, 802.1X authentication status, and EVPN database — without opening a shell session. Each command targets specific device types and returns structured, readable output.

**Why this priority**: These are frequently needed during troubleshooting but currently require an interactive shell (Menu 79). Dedicated menu options are faster and produce cleaner output.

**Independent Test**: Each command can be tested independently on the appropriate device type (BGP on SSR/SRX/switch, ARP on switch/gateway, DHCP on switch/gateway, 802.1X on switch, EVPN on switch/gateway).

**Acceptance Scenarios**:

1. **Given** an SSR/SRX/switch with BGP configured, **When** user selects "show BGP summary", **Then** output displays neighbor addresses, AS numbers, state, and prefix counts
2. **Given** a switch or gateway, **When** user selects "show ARP table", **Then** output displays IP-to-MAC mappings with interface and VLAN information
3. **Given** a switch or gateway, **When** user selects "show DHCP leases", **Then** output displays active lease assignments
4. **Given** a switch with 802.1X enabled, **When** user selects "show 802.1X table", **Then** output displays authenticated clients with port, MAC, and authentication status
5. **Given** a switch or gateway with EVPN configured, **When** user selects "show EVPN database", **Then** output displays EVPN route entries

---

### User Story 5 — DNS Resolution Test and Device Monitoring (Priority: P2)

A network engineer needs to verify that an SSR gateway can resolve DNS names, or needs to monitor live traffic on a switch/SRX port, or check resource utilization via the top command.

**Why this priority**: DNS resolution failures cause widespread service outages that are hard to debug without testing from the device itself. Traffic monitoring and resource inspection are essential advanced diagnostics.

**Independent Test**: DNS can be tested by resolving a known hostname from an SSR. Monitor traffic can be tested on any switch with active ports. Top can be tested on any switch/SRX.

**Acceptance Scenarios**:

1. **Given** an SSR gateway, **When** user selects "resolve DNS" and enters a hostname, **Then** output shows resolution status, resolved addresses, and timing
2. **Given** a switch or SRX with active ports, **When** user selects "monitor traffic" and specifies a port, **Then** live traffic data streams until user presses Ctrl+C or the auto-timeout fires (whichever comes first)
3. **Given** a switch or SRX, **When** user selects "run top", **Then** output displays resource utilization (CPU, memory, processes) and streams until Ctrl+C or auto-timeout

---

### User Story 6 — Locate and Unlocate Devices (Priority: P2)

A field technician at a site with dozens of APs or switches in a wiring closet needs to physically identify a specific device. They use "locate" to blink the device LED and "unlocate" to stop it when they've found it.

**Why this priority**: Extremely useful for field operations. Simple to implement and directly solves a common physical-access problem.

**Independent Test**: Can be tested by selecting any AP or switch and confirming the API call succeeds (LED blink is physical verification).

**Acceptance Scenarios**:

1. **Given** an AP or switch, **When** user selects "locate device", **Then** the device LED begins blinking and a confirmation message displays
2. **Given** a device currently being located (LED blinking), **When** user selects "unlocate device", **Then** the LED stops blinking and a confirmation displays
3. **Given** a gateway device, **When** user attempts locate, **Then** a clear message indicates locate is only supported on APs and switches

---

### User Story 7 — Port Bounce and Cable Test (Priority: P2)

A NOC engineer troubleshooting a switch port issue needs to bounce (reset) a port to clear a connectivity problem, or run a cable test to diagnose physical layer issues.

**Why this priority**: Port bounce is one of the most common switch operations in NOC workflows. Cable test provides unique physical-layer diagnostics not available any other way through the API.

**Independent Test**: Port bounce can be tested on any switch port. Cable test can be tested on any switch port with a cable connected.

**Acceptance Scenarios**:

1. **Given** a switch device, **When** user selects "bounce port" and specifies a port, **Then** the port is reset and confirmation displays
2. **Given** a switch device, **When** user selects "cable test" and specifies a port, **Then** cable diagnostic results display (pair status, length, fault distance)
3. **Given** a destructive port bounce, **When** user confirms the operation, **Then** explicit confirmation is required before execution

---

### User Story 8 — Clear/Reset Operations (Priority: P3)

A network engineer needs to clear stale state from devices — ARP cache, BGP routes, sessions, MAC tables, BPDU errors, or policy hit counts. These are recovery operations used when devices have incorrect cached state causing traffic issues.

**Why this priority**: Clear operations are less frequently needed than show commands but are critical for recovery scenarios. They are destructive (clear cached state) and require confirmation gates.

**Independent Test**: Each clear operation can be tested independently. ARP/BGP/session clear on SSR/SRX. MAC table/BPDU/MAC clear on switches. Policy hit count clear on gateways.

**Acceptance Scenarios**:

1. **Given** an SSR/SRX/switch, **When** user selects "clear ARP cache", **Then** explicit confirmation is required and ARP cache is cleared upon confirmation
2. **Given** an SSR/SRX, **When** user selects "clear BGP routes" and specifies neighbor, **Then** explicit confirmation is required and BGP routes are cleared
3. **Given** an SSR/SRX, **When** user selects "clear session", **Then** explicit confirmation is required and sessions are cleared
4. **Given** a switch or gateway, **When** user selects "clear MAC table", **Then** explicit confirmation is required and MAC table is cleared
5. **Given** a switch, **When** user selects "clear BPDU errors", **Then** error state on specified ports is cleared
6. **Given** a switch, **When** user selects "clear learned MACs from port", **Then** learned MACs on the specified port are cleared
7. **Given** a gateway (SSR), **When** user selects "clear policy hit count", **Then** application policy counters are reset
8. **Given** any clear operation, **When** user does not confirm, **Then** operation is cancelled with no side effects

---

### User Story 9 — DHCP Lease Release (Priority: P3)

A network engineer needs to release an active DHCP lease on a device to force a renewal — either on a switch/gateway (general DHCP) or on an SSR/SRX (SSR-specific DHCP).

**Why this priority**: Used in IP addressing troubleshooting. Less frequent than show commands but important for resolving addressing conflicts.

**Independent Test**: Can be tested by releasing a lease on a device and confirming the lease is released.

**Acceptance Scenarios**:

1. **Given** a switch or gateway with active DHCP leases, **When** user selects "release DHCP lease" and specifies the lease, **Then** explicit confirmation is required and the lease is released
2. **Given** an SSR/SRX, **When** user selects "release DHCP lease (SSR)", **Then** explicit confirmation is required and the SSR-specific lease is released

---

### User Story 10 — Device Management Operations (Priority: P3)

A network engineer needs to perform device management tasks: reprovision a device to push fresh config, re-adopt a device with incorrect ID, retrieve ZTP password for initial setup, get config CLI commands for brown-field adoption, or upload support files for TAC cases.

**Why this priority**: These are administrative operations used during initial deployment, device recovery, and support case escalation. Important but less frequent than daily troubleshooting.

**Independent Test**: Each operation can be tested independently on the appropriate device type.

**Acceptance Scenarios**:

1. **Given** a switch or gateway, **When** user selects "reprovision device", **Then** explicit confirmation is required and the device begins reprovisioning
2. **Given** a switch with incorrect device ID, **When** user selects "re-adopt device", **Then** the device is re-adopted with the correct ID
3. **Given** a switch or gateway, **When** user selects "get ZTP password", **Then** the temporary root password is displayed
4. **Given** a switch, **When** user selects "get config commands", **Then** the CLI commands needed for brown-field adoption are displayed
5. **Given** a switch or gateway, **When** user selects "upload support file", **Then** the device uploads support files for TAC analysis

---

### User Story 11 — Switch Hardware Operations (Priority: P3)

A network engineer needs to poll fresh statistics from a switch, create a device snapshot, or upgrade switch BIOS/FPGA firmware.

**Why this priority**: Hardware operations are infrequent but essential for maintenance windows. BIOS/FPGA upgrades are destructive and require the strongest confirmation gates.

**Independent Test**: Poll stats can be tested on any switch. Snapshot creation can be tested on any switch. BIOS/FPGA upgrades require a switch with available firmware.

**Acceptance Scenarios**:

1. **Given** a switch, **When** user selects "poll stats", **Then** fresh statistics are polled from the device
2. **Given** a switch, **When** user selects "create snapshot", **Then** a device snapshot is created
*(BIOS and FPGA upgrade scenarios removed — these operations are already covered by existing Menu 99-100 Switch/SSR Firmware)*

---

### Edge Cases

- What happens when the selected device is offline or unreachable? Commands must fail gracefully with a clear message, not hang.
- What happens when a command targets the wrong device type (e.g., OSPF on an AP)? Input validation must reject the request before making API calls.
- What happens when the API returns an empty result set (e.g., no OSPF neighbors)? Display a clear "no results" message, not an error.
- What happens when the WebSocket connection drops mid-command? A timeout must fire and inform the user of the incomplete result.
- What happens when multiple commands are issued concurrently against the same device? Session-based demultiplexing must prevent output from mixing.
- What happens when a clear/reset operation is run on a production device without confirmation? Destructive operations must require explicit confirmation and never auto-execute.

## Requirements *(mandatory)*

### Functional Requirements

**Diagnostic Commands (Read-Only)**:

- **FR-001**: System MUST provide a traceroute command targeting AP, switch, and gateway devices, with user-specified destination and real-time hop display
- **FR-002**: System MUST provide four OSPF inspection commands (database, interfaces, neighbors, summary) targeting SSR/SRX gateways
- **FR-003**: System MUST provide SSR session inspection (`show_session`) targeting SSR/SRX gateways
- **FR-004**: System MUST provide SSR service path inspection (`show_service_path`) targeting SSR gateways
- **FR-005**: System MUST provide BGP summary (`show_bgp_summary`) targeting SSR/SRX/switch devices
- **FR-006**: System MUST provide structured ARP table display (`show_arp`) targeting switch/gateway devices
- **FR-007**: System MUST provide DHCP lease display (`show_dhcp_leases`) targeting switch/gateway devices
- **FR-008**: System MUST provide 802.1X authentication table display (`show_dot1x`) targeting switch devices
- **FR-009**: System MUST provide EVPN database display (`show_evpn_database`) targeting switch/gateway devices
- **FR-010**: System MUST provide DNS resolution testing (`resolve_dns`) targeting SSR gateways
- **FR-011**: System MUST provide traffic monitoring (`monitor_traffic`) targeting switch/SRX devices
- **FR-012**: System MUST provide resource utilization display (`run_top`) targeting switch/SRX devices

**Device Management (Mixed Read/Write)**:

- **FR-013**: System MUST provide device locate/unlocate (LED blink) for AP and switch devices
- **FR-014**: System MUST provide port bounce for switch and gateway devices, with confirmation before execution
- **FR-015**: System MUST provide cable test for switch devices
- **FR-016**: System MUST provide device reprovisioning for switch and gateway devices, with confirmation
- **FR-017**: System MUST provide device re-adoption for switch devices
- **FR-018**: System MUST provide ZTP password retrieval for switch and gateway devices
- **FR-019**: System MUST provide config CLI command retrieval for switch brown-field adoption
- **FR-020**: System MUST provide support file upload for switch and gateway devices
- **FR-021**: System MUST provide switch statistics polling
- **FR-022**: System MUST provide switch snapshot creation

**Clear/Reset Operations (Destructive)**:

- **FR-023**: System MUST provide ARP cache clear for SSR/SRX/switch devices, requiring explicit confirmation
- **FR-024**: System MUST provide BGP route clear for SSR/SRX devices, requiring explicit confirmation
- **FR-025**: System MUST provide session clear for SSR/SRX devices, requiring explicit confirmation
- **FR-026**: System MUST provide MAC table clear for switch/gateway devices, requiring explicit confirmation
- **FR-027**: System MUST provide policy hit count clear for gateway (SSR) devices, requiring explicit confirmation
- **FR-028**: System MUST provide BPDU error clear for switch devices
- **FR-029**: System MUST provide learned MAC clear from specific port for switch devices
- **FR-030**: System MUST provide DHCP lease release for switch/gateway devices, requiring confirmation
- **FR-031**: System MUST provide SSR-specific DHCP lease release for SSR/SRX devices, requiring confirmation

**Hardware Operations**:

- ~~**FR-032**~~: *(Removed — BIOS upgrade is already covered by existing Menu 99-100 Switch/SSR Firmware operations)*
- ~~**FR-033**~~: *(Removed — FPGA upgrade is already covered by existing Menu 99-100 Switch/SSR Firmware operations)*

**Cross-Cutting Requirements**:

- **FR-034**: All commands MUST validate device type compatibility before making API calls (e.g., reject OSPF commands on APs)
- **FR-035**: All commands MUST handle device-offline scenarios gracefully with clear error messages and no hanging
- **FR-036**: All destructive operations (clear/reset, port bounce, reprovision, BIOS/FPGA upgrade) MUST require explicit user confirmation before execution
- **FR-037**: All commands MUST support the existing `--debug` flag for verbose diagnostic output
- **FR-038**: All commands that return results via WebSocket MUST implement a 120-second timeout (hardcoded, matching SC-005) with clear timeout messaging
- **FR-039**: All commands that return structured data MUST write results through the dual output system (CSV/SQLite via `DataExporter.write_with_format_selection()`), with appropriate primary key strategies defined in `ENDPOINT_PRIMARY_KEY_STRATEGIES`
- **FR-040**: Streaming commands (`monitor_traffic`, `run_top`) MUST support both Ctrl+C (early exit) and auto-timeout (configurable duration), and MUST be marked as "interactive" in the automated test skip list so `--test` mode skips them
- **FR-041**: Port-specific commands (`bounce_port`, `cable_test`, `clear_macs`, `monitor_traffic`) MUST present a selectable list of available ports fetched from the device, while also allowing manual port name entry as an override
- **FR-042**: The `show_session` command MUST prompt for optional filter fields (service name, session ID, node) where pressing Enter skips each filter, and empty filters result in showing all sessions

### Key Entities

- **Device**: A Mist-managed network device (AP, switch, or gateway/SSR/SRX), identified by site_id and device_id
- **Command**: A utility operation sent to a device via the Mist API, which may return results synchronously or via WebSocket stream
- **Session**: A WebSocket demultiplexing identifier that correlates command requests with their asynchronous results
- **Confirmation Gate**: A user interaction barrier required before destructive operations execute (ranges from simple y/N to typing a specific keyword like 'UPGRADE')

## Clarifications

### Session 2026-03-20

- Q: Should command output be console-only or also written to the dual output system (CSV/SQLite)? → A: Dual output — results written to both console display and CSV/SQLite via `DataExporter.write_with_format_selection()`, consistent with existing data extraction operations.
- Q: How should the 35 new menu options be organized in the menu number space? → A: New contiguous block at 120-154 — all 35 new commands grouped sequentially, avoiding conflict with existing menu entries 102-106 and 115. Destructive operations within the block still require confirmation gates regardless of menu number.
- Q: How should streaming/long-running commands (monitor_traffic, run_top) be terminated? → A: Both auto-timeout and Ctrl+C — commands auto-stop after a configurable duration with Ctrl+C as early exit, whichever comes first. These commands must be marked as "interactive" in the automated test skip list so `--test` mode skips them.
- Q: For port-specific commands (bounce_port, cable_test, clear_macs, monitor_traffic), how should users specify ports? → A: List with manual override — fetch and display available ports from the device for selection, but also allow the user to type a custom port name directly. This prevents errors for junior engineers while preserving flexibility for advanced users.
- Q: For show_session on SSR/SRX, should the command prompt for filters or show all sessions unfiltered? → A: Optional filters — prompt for filter fields (service name, session ID, node) where pressing Enter skips each filter. Empty filters = show all sessions. This keeps the happy-path fast while allowing targeted filtering when needed.

## Assumptions

- The Mist API `mistapi` Python SDK (v0.59+) already wraps all 35 missing endpoints as callable functions. If any are missing from the SDK, they will need direct REST calls.
- WebSocket-based commands follow the documented pattern: POST the command, receive a session ID, subscribe to `/sites/{site_id}/devices/{device_id}/cmd`, and receive results keyed by session ID.
- All 35 new menu options will occupy a contiguous block at menu numbers 120-154, avoiding conflict with existing entries 102-106 and 115. Destructive operations within this block still require confirmation gates.
- Each command endpoint has device type restrictions documented in the OpenAPI spec. These restrictions must be enforced client-side before making API calls.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 35 previously missing device utility endpoints are accessible through MistHelper menu options
- **SC-002**: NOC engineers can run any diagnostic command (traceroute, OSPF, BGP, ARP, DHCP, sessions) in under 30 seconds from menu selection to first output
- **SC-003**: Zero destructive operations can execute without explicit user confirmation
- **SC-004**: Commands targeting incompatible device types are rejected before any API call, 100% of the time
- **SC-005**: All WebSocket-based commands complete or timeout within 120 seconds — no hanging commands
- **SC-006**: Each new menu option works correctly via both interactive menu selection and direct invocation (`--menu N`)
