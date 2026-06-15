# Data Model: device_utils Adoption

**Date**: 2026-06-11 | **Plan**: [plan.md](plan.md)

## Entities

### DeviceUtilsAdapter

Central class that routes device commands through `mistapi.device_utils` or falls back to raw API.

| Field | Type | Description |
| - | - | - |
| `mist_session` | `mistapi.APISession` | Authenticated API session (injected) |
| `_utils_available` | `bool` | Whether device_utils module is importable |
| `_command_map` | `dict[str, dict[str, Callable]]` | Maps `(device_type, command)` → device_utils function |

**Methods**:
- `execute(command, device_type, site_id, device_id, **params) -> list[dict]` — Main entry point. Dispatches to device_utils or falls back to raw API. Returns flattened dicts matching current output format.
- `_normalize_response(util_response) -> list[dict]` — Extracts `.data` from `UtilResponse`, flattens nested JSON using existing `flatten_dict()`.
- `_fallback_raw_api(command, site_id, device_id, **params) -> list[dict]` — Calls existing WebSocket-based implementation when device_utils unavailable.
- `is_available(command, device_type) -> bool` — Checks if device_utils covers this command + device type combo.

### CommandResult (output contract)

Not a new class — reuses existing flat dict format. Key fields preserved:

| Field | Type | Source (current) | Source (device_utils) |
| - | - | - | - |
| `mac_address` | `str` | WebSocket message `.data.mac_address` | `UtilResponse.data.mac_address` |
| `port` | `str` | WebSocket message `.data.port` | `UtilResponse.data.port` |
| `vlan` | `int` | WebSocket message `.data.vlan` | `UtilResponse.data.vlan` |
| *(varies by command)* | varies | WebSocket message `.data.*` | `UtilResponse.data.*` |

### DeviceType Routing

| device_type string | device_utils submodule | Commands covered |
| - | - | - |
| `"switch"` / `"ex"` | `device_utils.ex` | show_arp, show_mac_table, show_dhcp_leases, show_route_summary, show_dot1x_clients, show_evpn_database, ping, traceroute, bounce_port, cable_test, clear_arp, clear_mac_table, clear_bgp |
| `"gateway"` / `"ssr"` | `device_utils.ssr` | show_route, show_sessions, show_service_path, show_ospf_neighbors, show_ospf_interfaces, ping, traceroute |
| `"gateway"` / `"srx"` | `device_utils.srx` | show_route, show_ospf_neighbors, show_security_flow_session, ping, traceroute |
| `"ap"` | `device_utils.ap` | ping, traceroute, dns_resolution |

## State Transitions

No state transitions — device commands are request/response, not stateful workflows.

## Validation Rules

- `site_id` must be valid UUID format
- `device_id` must be valid UUID format
- `device_type` must be one of: `"switch"`, `"gateway"`, `"ap"`
- `command` must be a known command string (validated against `_command_map`)
- For management commands (Phase 4): confirmation string must be validated before calling adapter
