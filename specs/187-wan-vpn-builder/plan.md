# Implementation Plan: Menu 164 - WAN Hub-Spoke VPN Builder

**Branch**: `187-wan-vpn-builder` | **Date**: 2025-04-22 | **Spec**: `specs/187-wan-vpn-builder/spec.md`
**Input**: Feature specification from `/specs/187-wan-vpn-builder/spec.md`

## Summary

Create a new Menu 164 operation that automates hub-spoke VPN overlay creation in Juniper Mist Cloud. The builder fetches gateway device profiles, lets users assign hub/spoke roles, auto-generates VPN path keys from WAN/LAN interfaces, assigns pod numbers, creates the VPN via API, and optionally updates device profile `vpn_paths` references.

Follows the same module pattern as Menu 163 (`src/wan_hub_group_manager.py`): a standalone class with `execute()` static entry point, dependency injection for `apisession`, `get_org_id_func`, and `safe_input_func`.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: `mistapi` 0.59+ (Mist API SDK)
**Storage**: N/A (API-only, no local persistence)
**Testing**: `pytest` with `unittest.mock`
**Target Platform**: Windows 11 (dev), Linux container (prod)
**Project Type**: CLI menu operation (module within monolith)
**Performance Goals**: N/A (interactive, single-user)
**Constraints**: Pod values 1-128; VPN name unique per org; rate limiting via existing adaptive delay
**Scale/Scope**: Typically 1-50 gateway profiles per org, each with 2-6 WAN/LAN interfaces

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| - | - | - |
| 5-Item Rule (max 5 children per level) | PASS | Single new module `src/wan_vpn_builder.py`, single class `WanVpnBuilder` |
| Max 25 lines per function | PASS | Will decompose into small focused methods |
| Max 5 parameters per function | PASS | Uses dependency injection via `execute()` with 3 params |
| Class-based design (no wrappers) | PASS | All logic in `WanVpnBuilder` class |
| Safety-first input handling | PASS | Uses `safe_input_func` injection, explicit confirmation for destructive create |
| Logging standards (ASCII only, no secrets) | PASS | Will follow existing patterns |
| Naming standards (no abbreviations) | PASS | Full descriptive names |
| File path management (os.path.join/Path) | N/A | No file I/O |
| Quality gates (py_compile, ruff, black) | PASS | Will run before commit |
| Security (OWASP, validate inputs) | PASS | Validates VPN name, pod values, profile selections |
| Menu Op Steps 2-4 (PK, flatten, export) | N/A | API-only operation — creates VPN data via API, no local data export |

**Post-Phase 1 Re-check**: All gates remain PASS. No architectural changes needed.

## Project Structure

### Documentation (this feature)

```text
specs/187-wan-vpn-builder/
├── plan.md              # This file
├── research.md          # Phase 0: API patterns, path generation rules
├── data-model.md        # Phase 1: Entities and relationships
├── quickstart.md        # Phase 1: Quick reference
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/
└── wan_vpn_builder.py          # NEW: WanVpnBuilder class

tests/
└── unit/
    └── test_wan_vpn_builder.py  # NEW: Unit tests

MistHelper.py                    # EDIT: Add menu 164 entry + import
README.md                        # EDIT: Update operation count
CHANGELOG.md                     # EDIT: Add version entry
documentation/                   # EDIT: Update wiki, diagrams
```

**Structure Decision**: Single module pattern matching `src/wan_hub_group_manager.py` (Menu 163). One class per file, unit tests in `tests/unit/`.

