# Data Model: Menu 164 - WAN Hub-Spoke VPN Builder

## Entities

### VPN Definition (Created via API)

The primary output of this operation. Created via `createOrgVpn()`.

| Field | Type | Description |
| - | - | - |
| `name` | `str` | User-provided VPN name, unique within org |
| `type` | `str` | Always `"hub_spoke"` |
| `path_selection` | `dict` | `{"strategy": "simple"}` (fixed default) |
| `paths` | `dict[str, dict]` | Path key -> `{"pod": int}` mapping |

**API body example**:
```python
{
    "name": "OrgOverlay",
    "type": "hub_spoke",
    "path_selection": {"strategy": "simple"},
    "paths": {
        "VREPOL69-HE_WAN1": {"pod": 69},
        "VREPOL69-HE_WAN1-WAN1": {"pod": 69},
        "VREPOL69-HE_WAN1-WAN2": {"pod": 69},
        "SPOKE01-WAN1": {"pod": 1},
        "VREPOL69-LAN1": {"pod": 69}
    }
}
```

### Gateway Device Profile (Read/Update via API)

Existing org-level profile fetched via `listOrgDeviceProfiles(type="gateway")`.

| Field | Type | Description |
| - | - | - |
| `id` | `str` | Profile UUID (used for updates) |
| `name` | `str` | Profile name (used as path key prefix) |
| `port_config` | `dict` | Interface definitions with `usage` and `vpn_paths` |

### Profile Assignment (In-memory only)

Tracks user's role assignment for each profile during the build workflow.

| Field | Type | Description |
| - | - | - |
| `profile` | `dict` | Full API profile object |
| `role` | `str` | `"hub"`, `"spoke"`, or `"skip"` |
| `pod` | `int` | Pod number (1-128) |

### WAN/LAN Interface (Extracted from profile `port_config`)

| Field | Type | Description |
| - | - | - |
| `name` | `str` | Interface name (key in `port_config`, e.g., `HE_WAN1`) |
| `usage` | `str` | `"wan"` or `"lan"` (from `port_config[name]["usage"]`) |
| `suffix` | `str` | Extracted suffix for cross-connects (e.g., `WAN1`, `5G`) |

## Relationships

```
Gateway Profile  1---*  Interface (via port_config)
Gateway Profile  *---1  Profile Assignment (in-memory)
Profile Assignment  *---1  VPN Definition (via paths)
Interface  1---*  VPN Path (key generated from profile + interface)
VPN Path  1---1  vpn_paths Reference (in profile port_config)
```

## State Transitions

### Build Workflow State Machine

```
START
  |
  v
FETCH_PROFILES  ---[0 profiles]--> EXIT("No profiles found")
  |
  v
FETCH_VPNS  ---[fetch error]--> EXIT("API error")
  |
  v
SHOW_EXISTING_VPNS  ---[display only]
  |
  v
PROMPT_VPN_NAME  ---[duplicate]--> PROMPT_VPN_NAME (loop)
  |               ---[empty]-----> PROMPT_VPN_NAME (loop)
  |               ---['q']-------> EXIT("Cancelled")
  v
ASSIGN_ROLES  ---[all skip]--> PROMPT_AGAIN / EXIT
  |            ---[no hubs]---> WARN + CONTINUE (spoke-only VPN)
  v
ASSIGN_PODS  ---[invalid]--> RE-PROMPT
  |
  v
GENERATE_PATHS  (pure computation, no user input)
  |
  v
PREVIEW  ---[decline]--> EXIT("Cancelled, no API call")
  |
  v
CREATE_VPN  ---[API error]--> EXIT("Error, no profile updates")
  |
  v
PROMPT_UPDATE_PROFILES  ---[decline]--> EXIT("VPN created, profiles not updated")
  |
  v
UPDATE_PROFILES  ---[partial failure]--> REPORT_SUMMARY
  |
  v
DONE("Success summary")
```

## Validation Rules

| Field | Rule | Error Action |
| - | - | - |
| VPN name | Non-empty, unique in org (case-insensitive) | Re-prompt |
| Pod value | Integer, 1-128 | Re-prompt |
| Role | Must be `hub`, `spoke`, or `skip` | Re-prompt |
| Profile selection | At least 1 profile not `skip` | Warn, re-prompt or exit |
| Profile name | Used as-is (API accepts special chars) | No validation needed |

## Path Key Generation Rules

### Hub Profile

For each WAN interface:
- 1 direct path: `{PROFILE}-{IFACE}`
- N cross-connect paths: `{PROFILE}-{IFACE}-{SUFFIX}` for each suffix in the global WAN suffix set

For each LAN interface:
- 1 direct path: `{PROFILE}-{IFACE}`

### Spoke Profile

For each WAN interface:
- 1 direct path: `{PROFILE}-{IFACE}`

For each LAN interface:
- 1 direct path: `{PROFILE}-{IFACE}`

### Global WAN Suffix Set

Union of all WAN interface suffixes across all selected (non-skip) profiles:
```python
suffixes = set()
for assignment in assignments:
    for interface in assignment.wan_interfaces:
        suffixes.add(extract_wan_suffix(interface.name))
# Example result: {"WAN1", "WAN2", "5G"}
```

## vpn_paths Update Structure

When updating a profile's `port_config` to reference the new VPN:

```python
# For WAN port with hub role and cross-connects
port_config["HE_WAN1"]["vpn_paths"] = {
    "VREPOL69-HE_WAN1.OrgOverlay": {"key": 0, "role": "hub"},
    "VREPOL69-HE_WAN1-WAN1.OrgOverlay": {"key": 0, "role": "hub"},
    "VREPOL69-HE_WAN1-WAN2.OrgOverlay": {"key": 1, "role": "hub"},
    "VREPOL69-HE_WAN1-5G.OrgOverlay": {"key": 2, "role": "hub"}
}

# For LAN port with hub role (direct only)
port_config["LAN1"]["vpn_paths"] = {
    "VREPOL69-LAN1.OrgOverlay": {"key": 0, "role": "hub"}
}

# For spoke WAN port (direct only)
port_config["WAN1"]["vpn_paths"] = {
    "SPOKE01-WAN1.OrgOverlay": {"key": 0, "role": "spoke"}
}
```

**Key assignment**: Direct path gets `key: 0`. Cross-connect paths get sequential keys starting from `0` within the cross-connect group.
