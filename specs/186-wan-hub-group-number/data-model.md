# Data Model: WAN Hub Group Number Manager

**Feature**: 186-wan-hub-group-number | **Date**: 2025-07-17

## Entities

### GatewayDeviceProfile

**Source**: `mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles(apisession, org_id, type="gateway")`

| Field | Type | Description |
| - | - | - |
| `id` | str (UUID) | Unique profile identifier |
| `name` | str | Profile name (e.g., `VREIRV65`) — used as prefix for VPN path matching |
| `org_id` | str (UUID) | Organization identifier |

**Used for**: Listing and selecting hub profiles. The `name` field is the key for VPN path prefix matching.

### OrgVpn

**Source**: `mistapi.api.v1.orgs.vpns.listOrgVpns(apisession, org_id)`

| Field | Type | Description |
| - | - | - |
| `id` | str (UUID) | VPN definition identifier |
| `name` | str | VPN name (e.g., `OrgOverlay`) |
| `type` | str | VPN type — only `hub_spoke` is relevant |
| `paths` | dict[str, VpnPath] | Dictionary of VPN path entries keyed by path name |

**Filter**: Only VPNs where `type == "hub_spoke"` are processed. Mesh VPNs are ignored.

**Update API**: `mistapi.api.v1.orgs.vpns.updateOrgVpn(apisession, org_id, vpn_id, body=updated_vpn)`

### VpnPath

**Location**: Values in `OrgVpn.paths` dictionary

| Field | Type | Description |
| - | - | - |
| key | str | Path name following `{DeviceProfileName}-{PortName}[-Suffix]` pattern |
| `pod` | int | Group number, range 1-128, default 1 |

**Prefix matching rule**: A path belongs to profile `P` if `path_key.startswith(f"{P.name}-")`. The trailing hyphen prevents false matches (e.g., `DC1-` won't match `DC1-BACKUP-` paths intended for profile `DC1-BACKUP`).

## Relationships

```text
GatewayDeviceProfile 1──*  VpnPath  *──1 OrgVpn
       (by name prefix)         (in paths dict)
```

- One GatewayDeviceProfile maps to ~10 VpnPaths (across WAN/LAN port variants)
- VpnPaths live inside one or more OrgVpn objects (typically one per org)
- The relationship is by naming convention, not by foreign key

## State Transitions

### Pod Value Lifecycle

```text
┌─────────┐  set(n)   ┌──────────┐  set(m)   ┌──────────┐
│ Default  │ ───────── │ Pod = n  │ ───────── │ Pod = m  │
│ (pod=1)  │           │ (1-128)  │           │ (1-128)  │
└─────────┘           └──────────┘           └──────────┘
     ▲                      │                      │
     │      clear           │      clear           │
     └──────────────────────┘──────────────────────┘
```

All transitions are reversible. "Clear" always returns to pod=1.

## Validation Rules

| Field | Rule | Error Message |
| - | - | - |
| Profile index | Integer, 1 to len(profiles) | "Please enter a number between 1 and {n}." |
| Pod value | Integer, 1 to 128 | "Pod value must be between 1 and 128." |
| Profile name prefix | Must match at least one VPN path key | "No VPN paths found for profile '{name}'." |
