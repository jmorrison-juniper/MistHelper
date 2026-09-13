# Implementation Plan: Device Utility Commands — Complete Mist API Coverage

**Branch**: `014-device-utility-commands` | **Date**: 2026-03-20 | **Spec**: [spec.md](specs/014-device-utility-commands/spec.md)
**Input**: Feature specification from `/specs/014-device-utility-commands/spec.md`

## Summary

Add 35 missing Mist API device utility endpoints as menu options 120-154 in MistHelper. Commands span five categories: diagnostics (traceroute, OSPF, BGP, ARP, DHCP, sessions, DNS, traffic monitoring), device management (locate/unlocate, port bounce, cable test, reprovision, re-adopt, ZTP password, config CLI, support upload), clear/reset operations (ARP, BGP, session, MAC table, BPDU, policy hit count, DHCP lease), switch hardware (poll stats, snapshot, BIOS/FPGA upgrade), and show commands (BGP summary, ARP table, DHCP leases, 802.1X, EVPN database). All WebSocket-based commands follow the existing pattern (POST endpoint -> session ID -> subscribe to WebSocket -> receive results) established by `WebSocketCommands` and `RoutingUtils`.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: mistapi 0.59+ (Mist API SDK), websocket-client (WebSocket connections), requests (HTTP fallback for non-SDK endpoints)
**Storage**: SQLite (`data/mist_data.db`) + CSV dual output via `DataExporter.write_with_format_selection()`
**Testing**: `python MistHelper.py --test` with skip list for interactive/destructive operations; pytest for unit tests
**Target Platform**: Windows 11 (local dev), Linux container (production), SSH sessions (remote access)
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines)
**Performance Goals**: Command results within 30 seconds of menu selection (SC-002); WebSocket timeout at 120 seconds max (SC-005)
**Constraints**: All commands must handle EOF in SSH/container contexts; destructive operations require explicit confirmation; ASCII-only logging
**Scale/Scope**: 35 new menu options (120-154), one new class (`DeviceUtilityCommands`), primary key strategies for all endpoints producing data output

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** — The new `DeviceUtilityCommands` class organizes 35 commands into 5 logical method groups (diagnostics, show commands, device management, clear/reset, hardware ops). Each method stays under 25 lines by delegating to shared helpers for WebSocket setup, device selection, confirmation gates, and result processing.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** — All 35 commands implemented as static methods within `DeviceUtilityCommands`. No standalone wrapper functions. Shared infrastructure reuses existing `WebSocketManager`, `PromptUtils`, and `safe_input()`.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** — All `input()` calls use `safe_input()` with context. All destructive operations (12 total: 8 clear/reset, port bounce, reprovision, BIOS, FPGA) require explicit typed confirmation. Device type validation before API calls (FR-034). Offline device detection with graceful messaging (FR-035). WebSocket timeout at 120s (FR-038).

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** — After implementation: `py_compile` -> commit with `version YY.MM.DD.HH.MM` -> push -> CI -> pull image -> restart container -> verify.

### Principle V: Observability & Logging

- **STATUS: PASS** — All commands log at appropriate levels (debug: API payloads; info: user progress; error: exceptions with traceback). ASCII-only. No secrets logged.

### Pre-Phase 0 Gate: PASS

### Post-Phase 1 Re-Check

All five principles re-evaluated after design phase:

- **Principle I (Five-Item Rule)**: EXCEPTION — `DeviceUtilityCommands` class has 35+ static methods, exceeding the 5-children rule at the method level. Justified: splitting into 5+ sub-classes within a single-file monolith adds navigation overhead without structural benefit. Methods are organized into 5 logical groups (diagnostic, show, management, clear/reset, hardware) and each stays under 25 lines. Menu 120-154 is a contiguous block (avoids conflict with existing 102-106, 115).
- **Principle II (Class-Based)**: PASS — Single new class, no wrappers. Reuses existing `WebSocketManager`, `PromptUtils`, `DataExporter`.
- **Principle III (Safety-First)**: PASS — Three-tier confirmation gates defined. Device type validation before all API calls. `safe_input()` for all input. EOF handling in SSH/container contexts.
- **Principle IV (Pipeline)**: PASS — No changes to pipeline needed.
- **Principle V (Observability)**: PASS — ASCII-only, appropriate log levels, no secrets logged.

### Post-Phase 1 Gate: PASS

## Project Structure

### Documentation (this feature)

```text
specs/014-device-utility-commands/
├── plan.md              # This file
├── research.md          # Phase 0 - API endpoint inventory & SDK analysis
├── data-model.md        # Phase 1 - entity definitions & PK strategies
├── quickstart.md        # Phase 1 - dev setup & testing guide
├── contracts/           # Phase 1 - API endpoint contracts
│   ├── diagnostics.md
│   ├── show-commands.md
│   ├── management.md
│   ├── clear-reset.md
│   └── hardware.md
└── tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # DeviceUtilityCommands class + menu entries 101-135 + PK strategies
README.md                # Updated operation count + menu table
```

**Structure Decision**: Single-file monolith — consistent with existing codebase. All new code in `MistHelper.py` as `DeviceUtilityCommands` class following `WebSocketCommands` / `RoutingUtils` pattern.

## Complexity Tracking

| Principle | Status | Justification |
|-----------|--------|---------------|
| I. Five-Item Rule | **EXCEPTION** | `DeviceUtilityCommands` has 35+ static methods (exceeds 5-children at method level). Splitting into 5 sub-classes within a single-file monolith adds navigation overhead without structural benefit. Methods are logically grouped into 5 categories (diagnostic, show, management, clear/reset, hardware) and each stays under 25 lines. |
