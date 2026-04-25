# Quickstart: WAN Hub Group Number Manager

**Feature**: 186-wan-hub-group-number | **Date**: 2025-07-17

## What This Feature Does

Menu operation `163` that lets NOC engineers manage the `pod` (group number) field on VPN paths associated with WAN Hub Profiles (gateway device profiles). Users pick a profile from an alphabetized list, then set or clear the pod value across all matching VPN paths.

## Key Files

| File | Action | Purpose |
| - | - | - |
| `src/wan_hub_group_manager.py` | CREATE | `WanHubGroupNumberManager` class — all feature logic |
| `MistHelper.py` | MODIFY (+3 lines) | Import, menu_actions entry, test classification |
| `README.md` | MODIFY | Operation count bump, menu table entry |
| `CHANGELOG.md` | MODIFY | Version entry |
| `tests/unit/test_wan_hub_group_manager.py` | CREATE | Unit tests with mocked API calls |

## How to Develop

```powershell
# Activate venv
.venv\Scripts\Activate.ps1

# After making changes, validate
python -m py_compile MistHelper.py
python -m py_compile src/wan_hub_group_manager.py
python -m ruff check MistHelper.py src/wan_hub_group_manager.py
python -m black MistHelper.py src/wan_hub_group_manager.py

# Run interactively to test
python MistHelper.py --menu 163
```

## API Calls Used

1. `mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles(apisession, org_id, type="gateway")`
2. `mistapi.api.v1.orgs.vpns.listOrgVpns(apisession, org_id)`
3. `mistapi.api.v1.orgs.vpns.updateOrgVpn(apisession, org_id, vpn_id, body=updated_vpn)`

## Architecture Pattern

This is the first menu operation in an external module. The pattern:

```python
# src/wan_hub_group_manager.py
class WanHubGroupNumberManager:
    def __init__(self, apisession, org_id: str):
        self.apisession = apisession
        self.org_id = org_id

    @staticmethod
    def execute(apisession):
        """Static entry point called by menu_actions."""
        org_id = ConfigUtils.get_cached_or_prompted_org_id(apisession)
        manager = WanHubGroupNumberManager(apisession, org_id)
        manager.run()

# MistHelper.py (2 lines added)
from src.wan_hub_group_manager import WanHubGroupNumberManager
# ...
"163": (WanHubGroupNumberManager.execute, "WAN Hub Group Number Manager"),
```

## Key Design Decisions

- **Batch update**: All VPN paths per profile updated together (they share the same pod)
- **Prefix matching**: Path keys start with `{ProfileName}-` (trailing hyphen prevents false matches)
- **No CSV/SQLite output**: Interactive-only operation (no PK strategy needed)
- **y/N confirmation**: Pod changes are trivially reversible, no typed-keyword confirmation needed
- **Full VPN object update**: Send entire VPN object to `updateOrgVpn` (not partial patch)
