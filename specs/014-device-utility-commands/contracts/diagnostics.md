# Contracts: Diagnostic Commands

**Feature**: 014-device-utility-commands | **Date**: 2026-03-20

## 1. Traceroute — `tracerouteSiteDevice()`

**Menu**: 120 | **Endpoint**: `POST /api/v1/sites/{site_id}/devices/{device_id}/traceroute`
**Device Types**: AP, Switch, Gateway | **WebSocket**: Yes | **Destructive**: No

### Request Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `host` | string | Yes | Destination hostname or IP address |
| `protocol` | string | No | `udp` (default) or `icmp` (AP/MxEdge only) |
| `port` | int | No | UDP port (default 33434, not supported on SSR) |
| `timeout` | int | No | Max wait seconds (default 60, not supported on SSR) |
| `network` | string | No | SSR: source network (default 'internal') |
| `vrf` | string | No | SRX: source VRF (default master VRF) |
| `node` | string | No | HA: `node0` or `node1` |

### Response
```json
{"session": "session_id"}
```

### WebSocket Output (via `/sites/{site_id}/devices/{device_id}/cmd`)
Hop-by-hop text output with IP addresses and RTT values. Arrives as `raw` field in data payload.

### MistHelper Behavior
1. Select site -> select device (any type)
2. Prompt for destination host (required, validated)
3. Prompt for protocol (optional, default udp)
4. Establish WebSocket, POST command, await results
5. Display hop-by-hop output on console
6. Write results to CSV/SQLite via `DataExporter`

---

## 2-5. OSPF Commands (4 endpoints)

### 2. Show OSPF Neighbors — `showSiteDeviceOspfNeighbors()`

**Menu**: 121 | **Endpoint**: `POST .../show_ospf_neighbors`
**Device Types**: SSR/SRX Gateway | **WebSocket**: Yes

#### Request Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `neighbor` | string | No | Filter by neighbor IP |
| `port_id` | string | No | Filter by interface |
| `vrf` | string | No | VRF name |
| `node` | string | No | HA: `node0` / `node1` |

### 3. Show OSPF Interfaces — `showSiteDeviceOspfInterfaces()`

**Menu**: 122 | **Endpoint**: `POST .../show_ospf_interfaces`
**Device Types**: SSR/SRX Gateway | **WebSocket**: Yes

#### Request Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `port_id` | string | No | Filter by interface |
| `vrf` | string | No | VRF name |
| `node` | string | No | HA: `node0` / `node1` |

### 4. Show OSPF Database — `showSiteDeviceOspfDatabase()`

**Menu**: 123 | **Endpoint**: `POST .../show_ospf_database`
**Device Types**: SSR/SRX Gateway | **WebSocket**: Yes

#### Request Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `self_originate` | boolean | No | Show self-originated (default false) |
| `vrf` | string | No | VRF name |
| `node` | string | No | HA: `node0` / `node1` |

### 5. Show OSPF Summary — `showSiteDeviceOspfSummary()`

**Menu**: 124 | **Endpoint**: `POST .../show_ospf_summary`
**Device Types**: SSR/SRX Gateway | **WebSocket**: Yes

#### Request Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `vrf` | string | No | VRF name |
| `node` | string | No | HA: `node0` / `node1` |

### Common OSPF MistHelper Behavior
1. Select site -> select gateway device
2. Validate device is SSR/SRX (reject others with message)
3. Prompt for optional VRF, node, and command-specific filters
4. Establish WebSocket, POST command, await results
5. Display structured table output on console
6. Write results to CSV/SQLite

---

## 6. Resolve DNS — `resolveSiteDeviceDns()`

**Menu**: 132 | **Endpoint**: `POST .../resolve_dns`
**Device Types**: SSR Gateway | **WebSocket**: Yes | **Destructive**: No

### Request Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `hostname` | string | Yes | Hostname to resolve |

### MistHelper Behavior
1. Select site -> select gateway device
2. Validate device is SSR
3. Prompt for hostname (required, validated non-empty)
4. POST command, await WebSocket results
5. Display resolution results (addresses, timing)

---

## 7. Monitor Traffic — `startSiteDeviceMonitorTraffic()`

**Menu**: 133 | **Endpoint**: `POST .../monitor_traffic`
**Device Types**: Switch, SRX | **WebSocket**: Yes (streaming) | **Destructive**: No

### Request Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `port_id` | string | Yes | Port to monitor |
| `duration` | int | No | Monitoring duration in seconds |

### MistHelper Behavior (Streaming)
1. Select site -> select switch/SRX device
2. Validate device type
3. Show port list, prompt for port selection (FR-041)
4. POST command, subscribe to WebSocket
5. **Streaming loop**: display output fragments as they arrive
6. Stop on Ctrl+C (KeyboardInterrupt) or auto-timeout
7. Console-only output (no CSV/SQLite for streaming data)
8. **Test skip**: Marked as interactive in test skip list (FR-040)

---

## 8. Run Top — `runSiteDeviceTopCommand()`

**Menu**: 134 | **Endpoint**: `POST .../run_top`
**Device Types**: Switch, SRX | **WebSocket**: Yes (streaming) | **Destructive**: No

### MistHelper Behavior (Streaming)
Same streaming pattern as monitor_traffic. No port selection needed.
1. Select site -> select switch/SRX device
2. POST command, stream results until Ctrl+C or timeout
3. Console-only output
4. **Test skip**: Marked as interactive in test skip list (FR-040)
