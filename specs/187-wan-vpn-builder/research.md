# Research: Menu 164 - WAN Hub-Spoke VPN Builder

## R1: mistapi SDK Methods for VPN CRUD

**Decision**: Use `mistapi.api.v1.orgs.vpns` module with keyword arguments.

**Available methods**:
- `createOrgVpn(mist_session, org_id, body)` — Creates a VPN, returns `APIResponse`
- `listOrgVpns(mist_session, org_id, limit, page)` — Lists all VPNs
- `getOrgVpn(mist_session, org_id, vpn_id)` — Gets single VPN
- `updateOrgVpn(mist_session, org_id, vpn_id, body)` — Updates a VPN
- `deleteOrgVpn(mist_session, org_id, vpn_id)` — Deletes a VPN

**API body for `createOrgVpn`**:
```python
{
    "name": "MyVPN",
    "type": "hub_spoke",
    "path_selection": {"strategy": "simple"},
    "paths": {
        "PROFILE-WAN1": {"pod": 69},
        "PROFILE-WAN1-WAN2": {"pod": 69},
        "PROFILE-LAN1": {"pod": 69}
    }
}
```

**Pagination**: Use `mistapi.get_all(response=response, mist_session=apisession)` with keyword args (NOT positional).

**Rationale**: Matches the pattern established by Menu 163 (`wan_hub_group_manager.py`). All 5 methods confirmed via `dir()` and `inspect.signature()`.

**Alternatives considered**: Direct HTTP calls — rejected per constitution (mistapi methods exist).

---

## R2: VPN Path Key Generation Algorithm

**Decision**: Profile-name-prefixed keys with suffix-based cross-connects for hubs.

### Path Key Convention

Path keys follow the pattern `{PROFILE_NAME}-{INTERFACE_NAME}` with optional peer suffix for cross-connects:

| Path Type | Format | Example | Role |
| - | - | - | - |
| Hub WAN direct | `{PROFILE}-{IFACE}` | `VREPOL69-HE_WAN1` | Hub only |
| Hub WAN cross-connect | `{PROFILE}-{IFACE}-{PEER_SUFFIX}` | `VREPOL69-HE_WAN1-WAN2` | Hub only |
| Hub LAN direct | `{PROFILE}-{IFACE}` | `VREPOL69-LAN1` | Hub only |
| Spoke WAN direct | `{PROFILE}-{IFACE}` | `SPOKE01-WAN1` | Spoke only |
| Spoke LAN direct | `{PROFILE}-{IFACE}` | `SPOKE01-LAN1` | Spoke only |

### Cross-Connect Logic (Hub WAN Interfaces Only)

For each hub WAN interface, generate paths to every **other** WAN suffix across all selected profiles:

1. Collect all WAN interface suffixes from all selected profiles (strip profile-specific prefix)
2. For each hub WAN interface, the "peer suffix" is the suffix portion after stripping a common prefix pattern
3. Generate `{PROFILE}-{IFACE}-{PEER_SUFFIX}` for each peer suffix that differs from the interface's own suffix
4. Also generate the direct path `{PROFILE}-{IFACE}` (no peer suffix)

**Suffix extraction**: Given `HE_WAN1`, strip provider prefix (e.g., `HE_`) to get `WAN1`. Pattern: split on `_` and take the last segment, unless it's a known format like `5G`.

**Example** with profile `VREPOL69` having WAN interfaces `HE_WAN1`, `HE_WAN2`, `HE_5G`:
- `VREPOL69-HE_WAN1` (direct)
- `VREPOL69-HE_WAN1-WAN1` (cross-connect to WAN1)
- `VREPOL69-HE_WAN1-WAN2` (cross-connect to WAN2)
- `VREPOL69-HE_WAN1-5G` (cross-connect to 5G)
- `VREPOL69-HE_WAN2` (direct)
- `VREPOL69-HE_WAN2-WAN1` (cross-connect to WAN1)
- `VREPOL69-HE_WAN2-WAN2` (cross-connect to WAN2)
- `VREPOL69-HE_WAN2-5G` (cross-connect to 5G)
- `VREPOL69-HE_5G` (direct)
- `VREPOL69-HE_5G-WAN1` (cross-connect to WAN1)
- `VREPOL69-HE_5G-WAN2` (cross-connect to WAN2)
- `VREPOL69-HE_5G-5G` (cross-connect to 5G)

LAN interfaces (`LAN1`, `LAN2`) get direct paths only:
- `VREPOL69-LAN1` (direct)
- `VREPOL69-LAN2` (direct)

**Rationale**: Observed in production VPN "OrgOverlay" from Morrison House org. Cross-connects enable mesh routing between hub WAN interfaces. LAN interfaces are local and don't need cross-connects.

**Alternatives considered**: Generating cross-connects for LAN — rejected (matches Mist Dashboard behavior).

---

## R3: Device Profile Port Config Structure

**Decision**: Use `getOrgDeviceProfile` to fetch full profile, extract WAN/LAN from `port_config`, then `updateOrgDeviceProfile` with updated `vpn_paths`.

### Profile `port_config` Structure

```python
{
    "port_config": {
        "HE_WAN1": {
            "usage": "wan",
            "ip_config": {...},
            "vpn_paths": {
                "VREPOL69-HE_WAN1.OrgOverlay": {"key": 0, "role": "hub"},
                "VREPOL69-HE_WAN1-WAN1.OrgOverlay": {"key": 0, "role": "hub"},
                "VREPOL69-HE_WAN1-WAN2.OrgOverlay": {"key": 1, "role": "hub"},
                "VREPOL69-HE_WAN1-5G.OrgOverlay": {"key": 2, "role": "hub"}
            }
        },
        "LAN1": {
            "usage": "lan",
            "vpn_paths": {
                "VREPOL69-LAN1.OrgOverlay": {"key": 0, "role": "hub"}
            }
        }
    }
}
```

### vpn_paths Key Format

`{PathName}.{VPNName}` where:
- `PathName` = the VPN path key (e.g., `VREPOL69-HE_WAN1-WAN2`)
- `VPNName` = the VPN definition name (e.g., `OrgOverlay`)
- Separator is `.` (dot)

### vpn_paths Value Fields

- `key`: 0-based index within the port's vpn_paths. Direct path gets `key: 0`, cross-connects get sequential keys starting from 0.
- `role`: `"hub"` or `"spoke"` matching the profile's assigned role.

### Interface Classification

Determine WAN vs LAN from `port_config[interface_name]["usage"]`:
- `"wan"` — WAN interface (generates cross-connects for hub roles)
- `"lan"` — LAN interface (direct paths only)

**Rationale**: Verified against production data from Morrison House org.

**Alternatives considered**: Inferring WAN/LAN from interface name patterns — rejected (unreliable, `usage` field is authoritative).

---

## R4: Pod Number Auto-Suggestion Strategy

**Decision**: Extract trailing digits from profile name via regex; fall back to sequential assignment.

### Algorithm

1. Apply regex `r"(\d+)$"` to profile name to extract trailing number.
2. If found and within 1-128, suggest as pod value (e.g., `VREPOL69` -> pod 69).
3. If no match or out of range, assign sequentially starting from 1.
4. User can always override the suggestion.

**Example auto-suggestions**:
| Profile Name | Suggested Pod | Reason |
| - | - | - |
| `VREPOL69` | 69 | Trailing digits `69` |
| `VRECHR69` | 69 | Trailing digits `69` |
| `VREPOL61-69` | 69 | Trailing digits after last separator |
| `SPOKE01` | 1 | Trailing digits `01` |
| `MyGateway` | 1 (next sequential) | No trailing digits |

**Rationale**: Production profiles follow the pattern of embedding location/pod numbers in names. This matches what NOC engineers expect.

**Alternatives considered**: Always sequential assignment — rejected (less helpful); parsing arbitrary position numbers — rejected (too fragile).

---

## R5: Existing VPN Name Uniqueness Check

**Decision**: Fetch all org VPNs before creation and reject duplicate names.

### Algorithm

1. Call `listOrgVpns()` to get all VPNs.
2. Build a set of lowercase VPN names.
3. When user enters a new name, check `name.lower() in existing_names`.
4. If duplicate, display error and re-prompt.

**Rationale**: Mist API may or may not enforce name uniqueness server-side, but preventing duplicates client-side provides better UX and avoids confusion.

---

## R6: Cross-Connect Suffix Extraction

**Decision**: Suffix = the portion of the WAN interface name after the last `_` separator, or the full name if no `_`.

### Algorithm

```python
def extract_wan_suffix(interface_name: str) -> str:
    """Extract the WAN suffix used for cross-connect path naming.
    
    'HE_WAN1' -> 'WAN1'
    'HE_WAN2' -> 'WAN2'  
    'HE_5G'   -> '5G'
    'WAN1'    -> 'WAN1'
    """
    if "_" in interface_name:
        return interface_name.rsplit("_", 1)[1]
    return interface_name
```

**Rationale**: Production data shows provider prefixes like `HE_` (Hurricane Electric) on WAN interfaces. The suffix after the last `_` represents the logical interface identity used in cross-connects.

**Alternatives considered**: Splitting on first `_` — rejected (handles `HE_5G` correctly but fails on `PROVIDER_NET_WAN1`). Using last segment after `_` handles all observed cases.
