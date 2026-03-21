# Contracts: Clear/Reset Commands

**Feature**: 014-device-utility-commands | **Date**: 2026-03-20

All clear/reset operations are **destructive** — they remove cached or learned state from devices. Every command requires explicit confirmation before execution.

## Common Pattern

All clear/reset commands follow this pattern:
1. Select site -> select device (validated for compatibility)
2. Prompt for optional parameters (port, IP, neighbor, etc.)
3. **Confirmation gate**: `safe_input("Type 'CLEAR' to proceed: ", context="clear_{operation}")`
4. If confirmation != 'CLEAR': cancel with message, return
5. POST command via SDK
6. Display confirmation message
7. No CSV/SQLite output (action result only)

---

## 1. Clear ARP Cache — `clearSiteSsrArpCache()`

**Menu**: 144 | **Endpoint**: `POST .../clear_arp`
**Device Types**: SSR/SRX, Switch | **Confirmation**: Type 'CLEAR'

### Request Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ip` | string | No | Specific IP to clear (requires port_id) |
| `port_id` | string | No | Interface to clear |
| `vlan` | int | No | VLAN to clear (requires port_id) |
| `node` | string | No | HA: `node0` / `node1` |

---

## 2. Clear BGP Routes — `clearSiteSsrBgpRoutes()`

**Menu**: 145 | **Endpoint**: `POST .../clear_bgp`
**Device Types**: SSR/SRX | **Confirmation**: Type 'CLEAR'

### Request Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `neighbor` | string | Yes | BGP neighbor IP address |
| `type` | string | No | `in` or `out` (default: both) |
| `vrf` | string | No | VRF name |
| `node` | string | No | HA: `node0` / `node1` |

---

## 3. Clear Session — `clearSiteDeviceSession()`

**Menu**: 146 | **Endpoint**: `POST .../clear_session`
**Device Types**: SSR/SRX | **Confirmation**: Type 'CLEAR'

### Request Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session_id` | string | No | Specific session to clear |
| `node` | string | No | HA: `node0` / `node1` |

---

## 4. Clear MAC Table — `clearSiteDeviceMacTable()`

**Menu**: 147 | **Endpoint**: `POST .../clear_mac_table`
**Device Types**: Switch, Gateway | **Confirmation**: Type 'CLEAR'

### Request Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `node` | string | No | HA: `node0` / `node1` |

---

## 5. Clear BPDU Errors — `clearSiteSwitchBpduError()`

**Menu**: 148 | **Endpoint**: `POST .../clear_bpdu_error`
**Device Types**: Switch | **Confirmation**: Type 'CLEAR'

### Request Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `port_id` | string | No | Specific port to clear BPDU errors |

---

## 6. Clear Learned MACs — `clearSiteDeviceLearnedMacs()`

**Menu**: 149 | **Endpoint**: `POST .../clear_macs`
**Device Types**: Switch | **Confirmation**: Type 'CLEAR'

### Request Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `port_id` | string | Yes | Port from which to clear learned MACs |

### MistHelper Behavior (extension of common pattern)
- Fetch and display available ports (FR-041) before prompting for port selection

---

## 7. Clear Policy Hit Count — `clearSiteDevicePolicyHitCount()`

**Menu**: 150 | **Endpoint**: `POST .../clear_policy_hit_count`
**Device Types**: Gateway (SSR) | **Confirmation**: Type 'CLEAR'

### Request Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `node` | string | No | HA: `node0` / `node1` |

---

## 8. Release DHCP Lease — `releaseSiteDeviceDhcpLease()`

**Menu**: 151 | **Endpoint**: `POST .../release_dhcp_leases`
**Device Types**: Switch, Gateway | **Confirmation**: y/N

### Request Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `port_id` | string | Yes | Interface with the DHCP lease |
| `node` | string | No | HA: `node0` / `node1` |

---

## 9. Release DHCP Lease (SSR) — `releaseSiteSsrDhcpLease()`

**Menu**: 152 | **Endpoint**: `POST .../release_dhcp`
**Device Types**: SSR/SRX | **Confirmation**: y/N

### Request Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `port_id` | string | Yes | SSR network interface |
| `node` | string | No | HA: `node0` / `node1` |
