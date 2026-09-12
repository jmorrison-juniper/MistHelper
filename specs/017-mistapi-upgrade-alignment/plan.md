# Implementation Plan: Systematic mistapi Upgrade Alignment

**Branch**: `017-mistapi-upgrade-alignment` | **Date**: 2026-03-29 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/017-mistapi-upgrade-alignment/spec.md`

## Summary

Systematically update all MistHelper menu options (1-158) to align with mistapi v0.59.1-v0.61.3 changes. This covers: (1) fixing breaking parameter changes in Insights API functions, (2) migrating deprecated SLE functions to new trend endpoints, (3) adopting the new `device_utils` module for Menu 123-157, (4) migrating WebSocket code to use `mistapi.websockets` module, (5) leveraging new search parameters (`search_after`, alarm filters), and (6) handling exception-based auth errors replacing `sys.exit()`. Each menu option is updated and validated individually.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: mistapi >= 0.61.3 (Juniper Mist API SDK), websocket-client >= 1.8.0, sshkeyboard >= 2.3.1
**Storage**: SQLite (`data/mist_data.db`) + CSV dual output via `DataExporter`
**Testing**: `python MistHelper.py --test` (systematic test harness) + `python -m py_compile` syntax check
**Target Platform**: Windows 11 (local dev), Linux containers (Podman), SSH sessions
**Project Type**: CLI tool (single-file ~28K lines)
**Performance Goals**: Menu operations complete within same or better timeframes; WebSocket streams bounded
**Constraints**: Single-file architecture (MistHelper.py), ASCII-only logging, non-root container execution
**Scale/Scope**: 158 menu options, ~250 mistapi API call sites, 35 device utility commands

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| - | - | - |
| I. Five-Item Rule | PASS | Changes are within existing classes/methods, not adding new hierarchy levels. Any new helpers will respect 5-item/25-line limits. |
| II. Class-Based Architecture | PASS | Migrating `DeviceUtilityCommands` internals to use `device_utils` module — stays within the existing class. `WebSocketManager` refactoring stays class-based. No new wrappers. |
| III. Safety-First | PASS | No changes to destructive operation confirmations. All `safe_input()` patterns preserved. Exception handling additions improve safety (catching `ConnectionError`/`ValueError` instead of `sys.exit()`). |
| IV. Full Deployment Pipeline | PASS | Each menu option update will be committed with `py_compile` validation. Full pipeline at end. |
| V. Observability & Logging | PASS | New WebSocket auto-reconnect and bounded queue events will be logged at Info/Debug levels with ASCII-only output. |
| Technology Constraints | PASS | mistapi is the sole Mist API interface. UV/pip compatibility maintained. `requirements.txt` updated. |

## Project Structure

### Documentation (this feature)

```text
specs/017-mistapi-upgrade-alignment/
├── plan.md              # This file
├── research.md          # Phase 0: API signature research
├── data-model.md        # Phase 1: Menu-to-API mapping model
├── quickstart.md        # Phase 1: Implementation guide per menu group
├── contracts/           # Phase 1: API call contracts
└── tasks.md             # Phase 2: Ordered task list
```

### Source Code (repository root)

```text
MistHelper.py            # Primary file - all changes here
requirements.txt         # Update mistapi version pin
README.md               # Update changelog
```

**Structure Decision**: Single-file project. All changes are within `MistHelper.py` modifying existing classes: `WebSocketManager`, `DeviceUtilityCommands`, `WebSocketCommands`, `PacketCaptureManager`, and the various exporter classes. No new files needed.

## Post-Design Constitution Re-Check

| Principle | Status | Post-Design Notes |
| - | - | - |
| I. Five-Item Rule | PASS | `contracts/` has 3 files (< 5). `data-model.md` has 6 entities but these are documentation sections, not code hierarchy. All implementation stays within existing class methods respecting 25-line limits — device_utils calls are simpler (fewer lines) than current raw API + manual WebSocket polling. |
| II. Class-Based Architecture | PASS | `DeviceUtilityCommands` class stays class-based — internal methods call `device_utils.*` instead of raw API. `WebSocketManager` refactored to use `mistapi.websockets.*` channel classes. No standalone wrappers introduced. `DEVICE_UTILS_DISPATCH` dict pattern mirrors existing `DEVICE_TYPE_COMPATIBILITY_MAP`. |
| III. Safety-First | PASS | Session exception handling contract (contracts/session-exceptions.md) adds `ConnectionError` and `ValueError` catching — improves safety. Device utility commands keep existing `safe_input()` confirmations for destructive operations. |
| IV. Full Deployment Pipeline | PASS | `quickstart.md` mandates `python -m py_compile` after each menu change. Tasks will enforce syntax validation between groups. |
| V. Observability & Logging | PASS | Contracts specify `logging.error()` and `logging.warning()` for new exception paths. ASCII-only throughout. |
| Technology Constraints | PASS | `requirements.txt` pin updated to `mistapi>=0.61.3`. No direct HTTP calls — all through mistapi SDK. |

**Gate Result**: ALL PASS — proceed to task generation.

## Complexity Tracking

No constitution violations. All changes fit within existing class hierarchies.
