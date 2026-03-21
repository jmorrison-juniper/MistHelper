# Contracts: Show Commands

**Feature**: 014-device-utility-commands | **Date**: 2026-03-20

## 1. Show Session — `showSiteDeviceSessions()`

**Menu**: 125 | **Endpoint**: `POST .../show_session`
**Device Types**: SSR/SRX Gateway | **WebSocket**: Yes | **Destructive**: No

### Request Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `service_name` | string | No | Filter by service name |
| `session_id` | string | No | Show specific session details |
| `node` | string | No | HA: `node0` / `node1` |

### MistHelper Behavior (FR-042)
1. Select site -> select gateway device
2. Validate device is SSR/SRX
3. Prompt for optional filters (each with Enter-to-skip):
   - Service name (Enter to skip)
   - Session ID (Enter to skip)
   - Node for HA (Enter to skip)
4. Empty filters = show all sessions
5. POST command, await WebSocket results
6. Display session table (Session ID, Direction, Service, Tenant, Protocol, Src/Dst IP:Port, NAT, State, Uptime)
7. Write to CSV/SQLite

---

## 2. Show Service Path — `showSiteDeviceServicePath()`

**Menu**: 126 | **Endpoint**: `POST .../show_service_path`
**Device Types**: SSR Gateway | **WebSocket**: Yes | **Destructive**: No

### Request Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `service_name` | string | No | Filter by service name |
| `node` | string | No | HA: `node0` / `node1` |

### MistHelper Behavior
1. Select site -> select gateway device
2. Validate device is SSR
3. Prompt for optional service name and node
4. POST command, await WebSocket results
5. Display path table (Service, Route, Type, Destination, Next-Hop, Interface, Vector, Cost, Rate, Capacity, State)
6. Write to CSV/SQLite

---

## 3. Show BGP Summary — `showSiteDeviceBgpSummary()`

**Menu**: 127 | **Endpoint**: `POST .../show_bgp_summary`
**Device Types**: SSR/SRX/Switch | **WebSocket**: Yes | **Destructive**: No

### Request Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `node` | string | No | HA: `node0` / `node1` |

### MistHelper Behavior
1. Select site -> select device (switch or gateway)
2. Validate device type is SSR/SRX or switch
3. Prompt for optional node (HA only)
4. POST command, await WebSocket results
5. Display BGP summary table (Neighbor, AS, State, Prefix Count)
6. Write to CSV/SQLite

---

## 4. Show ARP Table — `showSiteDeviceArpTable()`

**Menu**: 128 | **Endpoint**: `POST .../show_arp`
**Device Types**: Switch, Gateway | **WebSocket**: Yes | **Destructive**: No

### Request Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `node` | string | No | HA: `node0` / `node1` |

### MistHelper Behavior
1. Select site -> select device (switch or gateway)
2. POST command, await WebSocket results
3. Display ARP table (IP, MAC, Interface, VLAN)
4. Write to CSV/SQLite

---

## 5. Show DHCP Leases — `showSiteDeviceDhcpLeases()`

**Menu**: 129 | **Endpoint**: `POST .../show_dhcp_leases`
**Device Types**: Switch, Gateway | **WebSocket**: Yes | **Destructive**: No

### Request Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `node` | string | No | HA: `node0` / `node1` |

### MistHelper Behavior
1. Select site -> select device (switch or gateway)
2. POST command, await WebSocket results
3. Display DHCP lease table
4. Write to CSV/SQLite

---

## 6. Show 802.1X Table — `showSiteSwitchDot1x()`

**Menu**: 130 | **Endpoint**: `POST .../show_dot1x`
**Device Types**: Switch | **WebSocket**: Yes | **Destructive**: No

### Request Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `node` | string | No | HA: `node0` / `node1` |

### MistHelper Behavior
1. Select site -> select switch device
2. Validate device is switch
3. POST command, await WebSocket results
4. Display 802.1X table (Port, MAC, Auth Status, VLAN)
5. Write to CSV/SQLite

---

## 7. Show EVPN Database — `showSiteDeviceEvpnDatabase()`

**Menu**: 131 | **Endpoint**: `POST .../show_evpn_database`
**Device Types**: Switch, Gateway | **WebSocket**: Yes | **Destructive**: No

### Request Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `node` | string | No | HA: `node0` / `node1` |

### MistHelper Behavior
1. Select site -> select device (switch or gateway)
2. POST command, await WebSocket results
3. Display EVPN database entries
4. Write to CSV/SQLite
