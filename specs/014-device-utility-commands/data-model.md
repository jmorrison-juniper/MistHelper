# Data Model: Device Utility Commands

**Feature**: 014-device-utility-commands | **Date**: 2026-03-20

## Entities

### 1. DeviceUtilityCommand

Represents a single utility command invocation against a Mist device.

| Field | Type | Description |
|-------|------|-------------|
| `site_id` | `str (UUID)` | Site containing the target device |
| `device_id` | `str (UUID)` | Target device ID |
| `device_type` | `str` | Device type: `ap`, `switch`, `gateway` |
| `command_name` | `str` | API endpoint name (e.g., `traceroute`, `show_ospf_neighbors`) |
| `category` | `str` | One of: `diagnostic`, `show`, `management`, `clear_reset`, `hardware` |
| `requires_websocket` | `bool` | Whether results arrive via WebSocket |
| `is_destructive` | `bool` | Whether confirmation is required |
| `confirmation_type` | `str` | `none`, `y_n`, `typed_keyword` |

This entity is not persisted — it's a runtime dispatch model for command routing.

### 2. CommandResult (Persisted for show/diagnostic commands)

Structured output from WebSocket-based show and diagnostic commands, written to dual output.

| Field | Type | Description |
|-------|------|-------------|
| `device_id` | `str (UUID)` | Device that produced the result |
| `site_id` | `str (UUID)` | Site of the device |
| `command` | `str` | Command name |
| `timestamp` | `str (ISO8601)` | When the command was executed |
| `raw_output` | `str` | Raw text output from WebSocket |
| `session_id` | `str (UUID)` | WebSocket session demux ID |

### 3. Device Type Compatibility Map

Static mapping of which device types are valid for each command.

| Command Group | Valid Device Types |
|---------------|-------------------|
| traceroute | ap, switch, gateway |
| OSPF (4 commands) | gateway (SSR/SRX only) |
| show_session, show_service_path | gateway (SSR/SRX only) |
| show_bgp_summary | switch, gateway (SSR/SRX) |
| show_arp, show_dhcp_leases | switch, gateway |
| show_dot1x | switch |
| show_evpn_database | switch, gateway |
| resolve_dns | gateway (SSR only) |
| monitor_traffic | switch, gateway (SRX) |
| run_top | switch, gateway (SRX) |
| locate, unlocate | ap, switch |
| bounce_port | switch, gateway |
| cable_test | switch |
| reprovision | switch, gateway |
| readopt | switch |
| ztp_password | switch, gateway |
| config_cmd | switch |
| support_upload | switch, gateway |
| clear_arp | switch, gateway (SSR/SRX) |
| clear_bgp | gateway (SSR/SRX) |
| clear_session | gateway (SSR/SRX) |
| clear_mac_table | switch, gateway |
| clear_bpdu_error | switch |
| clear_macs | switch |
| clear_policy_hit_count | gateway (SSR) |
| release_dhcp_leases | switch, gateway |
| release_dhcp (SSR) | gateway (SSR/SRX) |
| poll_stats | switch |
| snapshot | switch |

## Primary Key Strategies (ENDPOINT_PRIMARY_KEY_STRATEGIES)

### Show/Diagnostic Commands (WebSocket results with structured data)

```python
# Traceroute
'tracerouteSiteDevice': {
    'type': 'composite_pk',
    'primary_key': ['device_id', 'timestamp'],
    'indexes': ['site_id', 'command']
}

# OSPF commands
'showSiteDeviceOspfNeighbors': {
    'type': 'composite_pk',
    'primary_key': ['device_id', 'timestamp'],
    'indexes': ['site_id']
}
'showSiteDeviceOspfInterfaces': {
    'type': 'composite_pk',
    'primary_key': ['device_id', 'timestamp'],
    'indexes': ['site_id']
}
'showSiteDeviceOspfDatabase': {
    'type': 'composite_pk',
    'primary_key': ['device_id', 'timestamp'],
    'indexes': ['site_id']
}
'showSiteDeviceOspfSummary': {
    'type': 'composite_pk',
    'primary_key': ['device_id', 'timestamp'],
    'indexes': ['site_id']
}

# Session/Service Path commands
'showSiteDeviceSessions': {
    'type': 'composite_pk',
    'primary_key': ['device_id', 'timestamp'],
    'indexes': ['site_id']
}
'showSiteDeviceServicePath': {
    'type': 'composite_pk',
    'primary_key': ['device_id', 'timestamp'],
    'indexes': ['site_id']
}

# Show commands
'showSiteDeviceBgpSummary': {
    'type': 'composite_pk',
    'primary_key': ['device_id', 'timestamp'],
    'indexes': ['site_id']
}
'showSiteDeviceArpTable': {
    'type': 'composite_pk',
    'primary_key': ['device_id', 'timestamp'],
    'indexes': ['site_id']
}
'showSiteDeviceDhcpLeases': {
    'type': 'composite_pk',
    'primary_key': ['device_id', 'timestamp'],
    'indexes': ['site_id']
}
'showSiteSwitchDot1x': {
    'type': 'composite_pk',
    'primary_key': ['device_id', 'timestamp'],
    'indexes': ['site_id']
}
'showSiteDeviceEvpnDatabase': {
    'type': 'composite_pk',
    'primary_key': ['device_id', 'timestamp'],
    'indexes': ['site_id']
}

# DNS resolution
'resolveSiteDeviceDns': {
    'type': 'composite_pk',
    'primary_key': ['device_id', 'timestamp'],
    'indexes': ['site_id']
}

# Cable test (returns structured pair data)
'cableTestFromSwitch': {
    'type': 'composite_pk',
    'primary_key': ['device_id', 'timestamp'],
    'indexes': ['site_id', 'port']
}
```

### Management/Clear Commands (No persistent storage)

Commands that perform actions (locate, bounce_port, reprovision, clear_*, etc.) produce confirmation messages only. These do NOT need primary key strategies and should NOT be written to SQLite/CSV.

### Streaming Commands (No persistent storage)

`monitor_traffic` and `run_top` produce continuous streaming output that is displayed in real-time on console only. Not viable for CSV/SQLite persistence.

## Validation Rules

### Device Type Validation
- Checked BEFORE any API call
- Uses static mapping (Device Type Compatibility Map above)
- On mismatch: display clear message and return without calling API
- Example: "OSPF commands are only available on SSR/SRX gateway devices. The selected device is an AP."

### Input Validation for Command Parameters
- **host** (traceroute): Non-empty, valid hostname or IP address format
- **port_id** (OSPF interfaces, bounce_port, cable_test, clear_macs, monitor_traffic): Valid interface name format (e.g., `ge-0/0/0`, `xe-0/0/1`)
- **vrf** (multiple commands): Non-empty string if provided
- **node** (HA commands): Must be `node0` or `node1` if provided
- **service_name** (show_session, show_service_path): Non-empty string if provided
- **neighbor** (OSPF neighbors, clear_bgp): Valid IP address format if provided

### Confirmation Gates
- **No confirmation**: All 22 read-only commands
- **Simple y/N**: bounce_port, reprovision, readopt, release_dhcp_leases, release_dhcp
- **Typed keyword 'CLEAR'**: clear_arp, clear_bgp, clear_session, clear_mac_table, clear_bpdu_error, clear_macs, clear_policy_hit_count
- **Typed keyword 'UPGRADE'**: BIOS upgrade, FPGA upgrade (if added as separate menu items)

## State Transitions

Commands are stateless from MistHelper's perspective. Each command is a single request-response cycle (or request-subscribe-receive for WebSocket). No state machine is needed.

The only state consideration is the WebSocket connection lifecycle:
1. **Disconnected** -> connect() -> **Connected**
2. **Connected** -> subscribe() -> **Subscribed**
3. **Subscribed** -> POST command -> **Awaiting Result**
4. **Awaiting Result** -> receive data -> **Complete** (disconnect)
5. **Awaiting Result** -> timeout -> **Timed Out** (disconnect)
6. **Any state** -> error/KeyboardInterrupt -> **Disconnected** (cleanup)
