# Quickstart: Menu 164 - WAN Hub-Spoke VPN Builder

## What It Does

Creates a hub-spoke VPN overlay definition in Mist Cloud from gateway device profiles. Optionally updates profiles to reference the new VPN.

## How to Run

```powershell
# Interactive
python MistHelper.py --menu 164

# Will prompt for: VPN name, profile role assignments, pod numbers, confirmation
```

## Key Decisions

| Decision | Choice | Reference |
| - | - | - |
| Module location | `src/wan_vpn_builder.py` | Follows Menu 163 pattern |
| Class name | `WanVpnBuilder` | Constitution: class-based |
| Entry point | `execute(apisession, get_org_id_func, safe_input_func)` | Dependency injection |
| Path key format | `{PROFILE}-{IFACE}[-{SUFFIX}]` | Production data verified |
| Pod auto-suggest | Trailing digits from profile name | Regex `r"(\d+)$"` |
| VPN type | Always `hub_spoke` | Spec scope |
| Path selection | Always `{"strategy": "simple"}` | Spec assumption |

## API Methods Used

| Method | Purpose |
| - | - |
| `listOrgDeviceProfiles(type="gateway")` | Fetch gateway profiles |
| `listOrgVpns()` | Check existing VPNs for name uniqueness |
| `createOrgVpn(body=...)` | Create the VPN definition |
| `getOrgDeviceProfile(deviceprofile_id=...)` | Get fresh profile before update |
| `updateOrgDeviceProfile(deviceprofile_id=..., body=...)` | Add vpn_paths to port_config |

## Class Structure

```python
class WanVpnBuilder:
    """Build hub-spoke VPN overlays from gateway device profiles."""

    POD_MIN = 1
    POD_MAX = 128
    POD_DEFAULT = 1

    @staticmethod
    def execute(apisession, get_org_id_func, safe_input_func): ...

    def run(self): ...  # Main workflow

    # API helpers
    def _fetch_profiles(self): ...
    def _fetch_existing_vpns(self): ...
    def _create_vpn(self, vpn_body): ...
    def _update_profile_vpn_paths(self, profile_id, vpn_name, paths, role): ...

    # Path generation (pure functions)
    @staticmethod
    def _extract_wan_suffix(interface_name): ...
    def _collect_wan_suffixes(self, assignments): ...
    def _generate_hub_paths(self, profile_name, interfaces, suffixes, pod): ...
    def _generate_spoke_paths(self, profile_name, interfaces, pod): ...
    def _build_vpn_body(self, vpn_name, assignments): ...

    # Interface extraction
    @staticmethod
    def _classify_interfaces(port_config): ...

    # User interaction
    def _prompt_vpn_name(self, existing_names): ...
    def _prompt_role_assignments(self, profiles): ...
    def _prompt_pod_values(self, assignments): ...
    def _display_preview(self, vpn_name, vpn_body): ...
    def _prompt_profile_updates(self, vpn_id, vpn_name, assignments): ...
```

## Test File

`tests/unit/test_wan_vpn_builder.py` — covers path generation, suffix extraction, interface classification, pod auto-suggestion, name validation, and display formatting.
