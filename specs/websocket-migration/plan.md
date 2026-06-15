# Implementation Plan: WebSocket Migration to mistapi.websockets

**Branch**: `websocket-migration` | **Date**: 2026-06-11 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/websocket-migration/spec.md`

## Summary

Migrate MistHelper's ~3,008 lines of custom WebSocket code (`src/websocket/`) to the official `mistapi.websockets.sites.DeviceCmdEvents` SDK class (v0.61.0+). An adapter class translates between the SDK's generator-based `receive()` API and the current `WebSocketManager` interface, enabling incremental per-operation migration across all 22 menu operations (102-123). Operations covered by `device-utils-adoption` spec are excluded — those will use `mistapi.device_utils` instead of direct WebSocket access.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: `mistapi >= 0.61.0` (`mistapi.websockets.sites.DeviceCmdEvents`), removing `websocket-client` after migration
**Storage**: N/A (output goes through existing `DataExporter`)
**Testing**: pytest, baseline output diff comparison
**Target Platform**: Linux container (Podman), Windows local dev
**Project Type**: CLI tool (menu-driven)
**Performance Goals**: Connection recovery time equal to or faster than current custom implementation
**Constraints**: Identical user-facing output (prompts, tables, error messages). SSH/container EOF handling unaffected.
**Scale/Scope**: 22 menu operations, 13 custom WS files (3,008 lines) → adapter (~200-400 lines) + deletion

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| - | - | - |
| I. Five-Item Rule | PASS | Adapter class is one new file in `src/websocket/`. No new hierarchy levels. |
| II. Class-Based Architecture | PASS | Adapter is a proper class (`MistWebSocketAdapter`), not a wrapper function. |
| III. Safety-First | PASS | No new `input()` calls. Existing `safe_input()` in menu ops unaffected. |
| IV. Full Deployment Pipeline | PASS | Standard commit/push/build/deploy cycle applies. |
| V. Observability & Logging | PASS | Adapter includes structured logging. ASCII only. |
| VI. Inline Comments | PASS | All new code will have inline comments per constitution. |
| VII. Action Logging | PASS | `logging.info()` before, `logging.debug()` after every WS operation. |

## Project Structure

### Documentation (this feature)

```text
specs/websocket-migration/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0: SDK API research, overlap analysis
├── data-model.md        # Phase 1: Adapter interface, message flow
├── quickstart.md        # Phase 1: Migration how-to for each operation
└── contracts/           # Phase 1: Adapter interface contract
    └── adapter-interface.md
```

### Source Code (repository root)

```text
src/websocket/
├── adapter.py           # NEW: MistWebSocketAdapter wrapping DeviceCmdEvents
├── manager.py           # EXISTING: Kept during migration, removed in cleanup phase
├── commands.py          # EXISTING: Show command impls (migrated one-by-one)
├── context.py           # EXISTING: WebSocketCmdDeps (unchanged)
├── diagnostics/         # EXISTING: Ping/ARP executors (migrated one-by-one)
├── polling/             # EXISTING: Custom polling (removed after full migration)
├── service_ping_*.py    # EXISTING: Service ping (migrated or excluded per device-utils)
└── __init__.py          # UPDATED: Exports adapter alongside existing classes

tests/
├── unit/
│   └── test_ws_adapter.py    # NEW: Adapter unit tests (mocked DeviceCmdEvents)
└── integration/
    └── test_ws_migration.py  # NEW: Baseline output diff tests
```

**Structure Decision**: Single new file (`adapter.py`) inside existing `src/websocket/` package. No new packages or directories needed. Cleanup phase deletes everything except `adapter.py` and `context.py`, then eventually moves adapter into MistHelper.py's `WebSocketManager` location.

## Complexity Tracking

No constitution violations to justify.

---

## Phase 0: Research

See [research.md](research.md) for full findings.

---

## Phase 1: Design & Contracts

See [data-model.md](data-model.md), [contracts/adapter-interface.md](contracts/adapter-interface.md), and [quickstart.md](quickstart.md).
