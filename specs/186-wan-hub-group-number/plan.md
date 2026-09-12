# Implementation Plan: WAN Hub Group Number Manager

**Branch**: `186-wan-hub-group-number` | **Date**: 2025-07-17 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/186-wan-hub-group-number/spec.md`

## Summary

Add a new menu operation (`"163"`) that lets NOC engineers view WAN Hub Profiles (gateway device profiles), see their current pod values (cross-referenced from Org VPNs), and set or clear the pod (group number) on all matching VPN paths. The implementation lives in a new external module `src/wan_hub_group_manager.py`, establishing the pattern for future menu operations outside MistHelper.py. MistHelper.py changes are limited to one import line and one `menu_actions` entry.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: mistapi 0.59+ (`orgs.deviceprofiles`, `orgs.vpns`)
**Storage**: N/A (no CSV/SQLite output — interactive display + API write only)
**Testing**: `python MistHelper.py --test` (menu 163 added to test harness)
**Target Platform**: Windows 11 (dev), Linux container (prod), SSH sessions
**Project Type**: CLI menu operation (external module)
**Performance Goals**: Profile listing within 5 seconds (SC-001); 3-step interaction (SC-002)
**Constraints**: EOF-safe input, ASCII-only logging, container-compatible
**Scale/Scope**: ~50 gateway device profiles, ~10 VPN paths per profile, 1-2 hub_spoke VPNs per org

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
| - | - | - |
| I. Five-Item Rule | PASS | New module has 1 class with ~4 public methods. Functions stay under 25 lines by extracting helpers. Max 5 params per method. |
| II. Class-Based Architecture | PASS | All logic in `WanHubGroupNumberManager` class. No standalone wrapper functions. `execute()` static entry point matches existing pattern (e.g., `SSIDTemplateConsolidationManager.execute`). |
| III. Safety-First | PASS | Uses `safe_input()` for all user input. Pod value validated (int 1-128) before API call. Confirmation prompt before destructive update. EOF handled via existing `safe_input` pattern. |
| IV. Full Deployment Pipeline | PASS | Will follow standard pipeline: py_compile, ruff, black, commit, push, CI, pull, restart. |
| V. Observability & Logging | PASS | ASCII-only logging. Debug for API responses, Info for user progress, Error for exceptions with traceback. No secrets logged. |
| Technology Constraints | PASS | Uses mistapi SDK (no direct HTTP). File paths via `os.path.join`. No new dependencies. Python 3.13+. |
| Menu Operation Workflow | PARTIAL | No primary key strategy needed (no CSV/SQLite output — this is an interactive-only operation). README and CHANGELOG updates required. |

**Gate Result**: PASS — no violations. The "PARTIAL" on Menu Operation Workflow is justified: this operation modifies API state interactively and does not export data, so steps 2-4 (PK strategy, flatten, dual output) are N/A.

## Project Structure

### Documentation (this feature)

```text
specs/186-wan-hub-group-number/
├── plan.md              # This file
├── research.md          # Phase 0: Technology decisions
├── data-model.md        # Phase 1: Entity definitions
├── quickstart.md        # Phase 1: Developer guide
└── tasks.md             # Phase 2 output (speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── __init__.py                    # Existing
├── wan_hub_group_manager.py       # NEW: WanHubGroupNumberManager class
├── constants.py                   # Existing
├── db/                            # Existing
├── ...                            # Other existing modules

MistHelper.py                      # MODIFY: +1 import, +1 menu_actions entry
README.md                          # MODIFY: operation count, menu table
CHANGELOG.md                       # MODIFY: version entry

tests/
└── unit/
    └── test_wan_hub_group_manager.py  # NEW: unit tests
```

**Structure Decision**: Single new module under existing `src/` directory. This follows the established pattern (MistHelper.py already imports from `src.db`). The module is self-contained with one class. No new subdirectories needed.

## Implementation Design

### Class: `WanHubGroupNumberManager`

**Location**: `src/wan_hub_group_manager.py`

**Constructor**: `__init__(self, apisession, org_id: str)`
- Stores mistapi session and org_id
- No API calls in constructor (lazy loading)

**Public Methods** (4 — within 5-Item Rule):

1. `execute()` — Static entry point. Resolves org_id via `ConfigUtils`, instantiates class, calls `run()`.
2. `run()` — Main workflow: fetch profiles + VPNs, display list, handle selection, dispatch action.
3. `set_pod(profile, vpn_data, new_pod: int)` — Batch-update all matching paths to `new_pod`.
4. `clear_pod(profile, vpn_data)` — Reset all matching paths to pod=1 (delegates to `set_pod`).

**Private Helpers** (extracted to stay under 25-line limit):

- `_fetch_profiles()` — API call + sort alphabetically
- `_fetch_hub_spoke_vpns()` — API call + filter to `hub_spoke` type
- `_find_matching_paths(profile_name, vpns)` — Prefix matching, returns list of `(vpn_id, vpn_name, path_key, current_pod)`
- `_display_profile_list(profiles, vpn_data)` — Format and print alphabetized list with pod values
- `_prompt_action()` — Show set/clear/cancel menu, validate selection

### MistHelper.py Integration

**Changes** (3 lines):

1. **Import** (near line 75, after existing `src.db` imports):
   ```python
   from src.wan_hub_group_manager import WanHubGroupNumberManager
   ```

2. **Menu registration** (after line 58131, menu `"162"`):
   ```python
   "163": (WanHubGroupNumberManager.execute, "WAN Hub Group Number Manager"),
   ```

3. **Test classification** (near line 58869, after `"162"`):
   ```python
   "163": {"category": "interactive_safe"},
   ```

### Interaction Flow

```text
User selects Menu 163
    │
    ▼
Fetch gateway profiles + hub_spoke VPNs (2 parallel-ish API calls)
    │
    ▼
Display alphabetized list with current pod values:
  ┌──────────────────────────────────────────────────┐
  │  WAN Hub Profiles:                               │
  │   1. VRECHR69          Pod: 89                   │
  │   2. VREIRV65          Pod: 65                   │
  │   3. VREORL72          Pod: 72                   │
  │                                                  │
  │  Select profile (1-3) or 'q' to cancel:          │
  └──────────────────────────────────────────────────┘
    │
    ▼
User selects profile → confirm selection
    │
    ▼
Display current pod + path count:
  ┌──────────────────────────────────────────────────┐
  │  Profile: VREIRV65                               │
  │  Current Pod: 65  (10 VPN paths)                 │
  │                                                  │
  │  Actions:                                        │
  │   1. Set new pod value                           │
  │   2. Clear pod (reset to default 1)              │
  │   3. Cancel                                      │
  │                                                  │
  │  Select action (1-3):                            │
  └──────────────────────────────────────────────────┘
    │
    ├── Set → prompt for value (1-128) → confirm → API update
    ├── Clear → confirm reset to 1 → API update
    └── Cancel → return to menu
```

### API Call Sequence

```text
1. listOrgDeviceProfiles(apisession, org_id, type="gateway")
   └── Returns: list of gateway profiles with id, name
2. listOrgVpns(apisession, org_id)
   └── Returns: list of VPN objects (filter to hub_spoke)
3. [On update] updateOrgVpn(apisession, org_id, vpn_id, body=modified_vpn)
   └── Body: full VPN object with updated pod values on matching paths
```

### Error Handling Matrix

| Error | Detection | User Message | Recovery |
| - | - | - | - |
| No gateway profiles | Empty list from API | "No WAN Hub Profiles found in this organization." | Return to menu |
| No hub_spoke VPNs | Empty filtered list | "No hub-spoke VPN definitions found." | Return to menu |
| No matching paths | Empty prefix match | "No VPN paths found for profile '{name}'." | Return to profile list |
| Inconsistent pods | Multiple distinct pod values in matched paths | "Warning: Mixed pod values detected ({values}). All will be updated." | Proceed with update |
| API auth error (401) | Exception from mistapi | "API session may have expired. Please restart MistHelper." | Return to menu |
| Permission denied (403) | Exception from mistapi | "Insufficient permissions to modify VPN objects." | Return to menu |
| Network error | ConnectionError/Timeout | "Network error. Please check connectivity." | Return to menu |
| Rate limit (429) | Handled by mistapi SDK | N/A (SDK retries automatically) | Transparent |

### Update Payload Strategy

The `updateOrgVpn` API expects the full VPN object body. Strategy:

1. Fetch VPN object via `listOrgVpns` (already cached from listing step)
2. Deep-copy the `paths` dictionary
3. For each matching path key: update `{"pod": new_value}`
4. Send full VPN object with modified paths to `updateOrgVpn`

This avoids partial updates and race conditions. The full-object update is idempotent.

## Post-Design Constitution Re-Check

| Principle | Status | Evidence |
| - | - | - |
| I. Five-Item Rule | PASS | 4 public methods, 5 private helpers. No function exceeds 25 lines. Max 4 params on any method. |
| II. Class-Based | PASS | Single `WanHubGroupNumberManager` class. No wrappers. Static `execute()` entry point. |
| III. Safety-First | PASS | `safe_input()` for all prompts. y/N confirmation before updates. Pod range validated. EOF handled. |
| IV. Pipeline | PASS | Standard py_compile → ruff → black → commit → push → CI → container flow. |
| V. Observability | PASS | ASCII logging at Debug/Info/Error levels. No secrets. Structured messages. |

**Gate Result**: PASS — design is constitution-compliant.

## Complexity Tracking

No constitution violations to justify. Single new file + 2-line MistHelper.py change.
