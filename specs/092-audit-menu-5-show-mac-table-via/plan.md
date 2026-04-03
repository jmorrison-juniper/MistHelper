# Implementation Plan: Audit Menu #5 — Show MAC Table via WebSocket

**Branch**: `092-audit-menu-5-show-mac-table-via` | **Date**: 2025-07-01 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/092-audit-menu-5-show-mac-table-via/spec.md`

## Summary

Audit and harden the existing `WebSocketCommands.show_mac_table` static method
(MistHelper.py, lines 15817–16043) and its `WebSocketManager` infrastructure
(lines 3961–4800). The spec identified eight audit findings (AF-01 through
AF-08): zero test coverage, fragile `locals().get()` cleanup, unconfirmed
subscription race condition, hardcoded 1-second sleep, direct `requests.post`
bypassing the API session, fragile completion detection heuristics, ambiguous
empty-table messaging, and inline `import traceback`. The plan addresses all
eight findings through targeted refactoring and comprehensive test coverage.
No new features are added — this is a quality and reliability audit.

## Technical Context

**Language/Version**: Python 3.13+ (per constitution constraint)
**Primary Dependencies**: websocket-client (`WebSocketApp`), requests (HTTP for REST POST — to be replaced with apisession), mistapi 0.59+ (Mist API SDK)
**Storage**: N/A (no data persistence in this feature — console output only)
**Testing**: pytest with `tests/conftest.py` fixtures (`tmp_data_dir`, `isolate_working_directory`); unit tests in `tests/unit/`
**Target Platform**: Windows 11 (local dev), Linux container (production), SSH sessions (remote access)
**Project Type**: CLI tool (single-file monolith `MistHelper.py`, ~16,000+ lines)
**Performance Goals**: MAC table results within 90 seconds end-to-end (SC-001); idle-timeout heuristic must tolerate pauses of ≥5 seconds between chunks (FR-008, SC-005)
**Constraints**: All `input()` calls via `safe_input()`; ASCII-only logging; max 25 lines per function (Principle I); no wrapper functions (Principle II)
**Scale/Scope**: 1 static method (~227 lines), 1 supporting class (~839 lines), 8 audit findings, target ≥80% line coverage (SC-004)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I — Five-Item Rule: PASS

The `show_mac_table` method is currently 227 lines — a clear violation of the
25-line limit. The audit refactoring will extract helper functions for:
(1) site/device selection, (2) WebSocket setup (connect + subscribe),
(3) REST command trigger, (4) result display, (5) cleanup. Each helper
will stay within the 25-line / 5-parameter limit. The `wait_for_command_result`
method (493 lines) is shared infrastructure used by many commands and is
out of scope for this audit — it will be tracked separately.

### Principle II — Class-Based Architecture: PASS

All code lives within `WebSocketCommands` (static methods) and
`WebSocketManager` (instance methods). No standalone wrapper functions are
introduced. Variable names use full words (`websocket_manager`, not `ws_mgr`).

### Principle III — Safety-First: PASS

- Device selection already uses `PromptUtils.select_device_id_from_inventory`
  which calls `safe_input()` internally.
- No destructive operations — `show_mac_table` is read-only.
- API token is already redacted in debug output (line 15926:
  `'Authorization': 'Token [REDACTED]'`).
- AF-05 fix will route the POST through `apisession`, which handles
  credential management at the session boundary.

### Principle IV — Full Deployment Pipeline: PASS

After audit fixes: `py_compile` → commit with `version YY.MM.DD.HH.MM` →
push → CI → pull image → restart container → verify.

### Principle V — Observability & Logging: PASS

- All logging uses ASCII-only output.
- Log levels follow the standard: debug (API payloads, WebSocket state),
  info (user progress), error (exception context).
- AF-08 fix moves `import traceback` to top-of-file, conforming to
  project convention.

### Pre-Phase 0 Gate: ALL PASS — proceed to Phase 0

## Project Structure

### Documentation (this feature)

```text
specs/092-audit-menu-5-show-mac-table-via/
├── plan.md              # This file
├── research.md          # Phase 0 — research on subscription confirmation,
│                        #   apisession usage, completion detection strategies
├── data-model.md        # Phase 1 — entity/state model for WebSocket lifecycle
├── quickstart.md        # Phase 1 — dev setup & test execution guide
├── contracts/           # Phase 1 — N/A (no external API contracts exposed;
│                        #   this feature consumes Mist API, does not expose one)
└── tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py                              # WebSocketCommands.show_mac_table (lines 15817-16043)
                                           # WebSocketManager class (lines 3961-4800)
tests/
├── conftest.py                            # Shared fixtures (tmp_data_dir, isolate_working_directory)
└── unit/
    ├── test_show_mac_table.py             # NEW — unit tests for show_mac_table (AF-01)
    └── test_websocket_manager.py          # NEW — unit tests for WebSocketManager methods
```

**Structure Decision**: Single-file monolith — consistent with existing codebase.
All production code changes in `MistHelper.py`. New test files in `tests/unit/`
following the existing pattern (class-based tests, mocked dependencies, no
network calls, `isolate_working_directory` fixture).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| `wait_for_command_result` exceeds 25 lines (493 lines) | Shared infrastructure used by all WebSocket commands (ping, MAC table, routing, etc.) — refactoring it is a cross-cutting concern beyond this audit's scope | Refactoring it within this audit would risk regressions in 10+ other menu commands that depend on its current behavior. Tracked for a dedicated refactoring spec. |
| `show_mac_table` currently exceeds 25 lines (227 lines) | Will be refactored as part of this audit to comply | N/A — this IS the fix |

## Post-Design Constitution Re-evaluation

Re-evaluated after Phase 1 artifacts (data-model.md, quickstart.md) were complete.

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Five-Item Rule | PASS (with documented exception) | `show_mac_table` refactored into ≤5 helper methods each under 25 lines. `wait_for_command_result` exception documented in Complexity Tracking — out of scope for this audit. |
| II. Class-Based | PASS | All code in `WebSocketCommands` and `WebSocketManager`. No wrappers. Full variable names. |
| III. Safety-First | PASS | Read-only operation. `safe_input()` used via `PromptUtils`. Token redacted. AF-05 routes POST through `apisession`. |
| IV. Deployment Pipeline | PASS | Standard pipeline applies. |
| V. Observability | PASS | ASCII-only. `import traceback` moved to top-of-file (AF-08). Structured log levels. |

**Gate Result: ALL PASS — no violations introduced during design**
