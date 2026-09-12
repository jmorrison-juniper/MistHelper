# Implementation Plan: Web Portal Interactivity

**Branch**: `006-web-interactivity` | **Date**: 2026-03-04 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/006-web-interactivity/spec.md`

## Summary

Enable ~35 interactive operations (site/device selection, packet captures, WebSocket commands) to run from the web portal by intercepting `input()` calls via `builtins.input` monkeypatch with per-thread queues. Replace the inline preview panel with a Bootstrap 5 modal overlay for file preview on both Data Browser and Operations pages.

**Technical approach**: A static `PARAMETER_REGISTRY` maps each interactive operation to its required parameters (site, device, client, choice, text, number). The frontend renders appropriate form controls (dropdowns populated via API, text fields, number inputs). On Run, the selected values are serialized as an ordered `input_answers` list. Server-side, a `threading.local()` deque feeds these answers to `input()` calls transparently — no changes to MistHelper.py's 54K-line monolith.

## Technical Context

**Language/Version**: Python 3.13+ (per pyproject.toml)  
**Primary Dependencies**: Flask (web framework), Bootstrap 5 (frontend, already bundled), mistapi >= 0.59.0 (Mist API SDK)  
**Storage**: CSV files in `data/`, SQLite (`data/mist_data.db`), browser localStorage (theme)  
**Testing**: `python MistHelper.py --test` (existing test harness)  
**Target Platform**: Linux container (Podman) + Windows 11 local dev  
**Project Type**: Web service (Flask portal) + CLI tool (MistHelper monolith)  
**Performance Goals**: Parameter form render < 500ms, site dropdown population < 2s, modal preview open < 2s for files up to 10MB  
**Constraints**: 5-item rule enforcement, no new Python dependencies, no MistHelper.py structural changes  
**Scale/Scope**: ~35 interactive operations to support, 6 parameter types, 1 modal component shared across 2 pages

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Gate (Phase 0 entry)

| Rule | Status | Notes |
|------|--------|-------|
| **5-Item Rule** | PASS | services/ currently at 5 files; plan merges theme.py into security.py (→ config.py) to make room for input_hook.py; stays at 5 |
| **Class-Based Architecture** | PASS | New code: `InputInterceptor` class (input_hook.py), parameter registry as class constant in `OperationExecutor` |
| **Safety-First Input** | PASS | `web_input_context` clears thread-local queue in `finally` block; empty queue raises `EOFError` caught by `safe_input` |
| **Natural Business Keys** | N/A | No new database entities |
| **Target Audience** | PASS | Dropdown labels use site names (not UUIDs); CLI-only ops show friendly message directing to SSH |
| **Naming Conventions** | PASS | No abbreviations; descriptive variable names throughout |
| **Deployment Pipeline** | PASS | Will execute full pipeline after implementation |

### Post-Design Gate (Phase 1 re-check)

| Rule | Status | Notes |
|------|--------|-------|
| **5-Item Rule: services/** | PASS | 5 files: config.py, data_browser.py, event_bus.py, input_hook.py, operation.py |
| **5-Item Rule: routes/** | PASS | 5 files (unchanged): dashboard.py, data.py, maps.py, operations.py, settings.py |
| **5-Item Rule: templates/** | PASS | 5 files (unchanged): base.html, dashboard.html, data_browser.html, map_viewer.html, operations.html |
| **5-Item Rule: static/js/** | PASS | 3 files: portal.js, operations.js, data_preview.js (new) |
| **Max 25 lines/function** | PASS | All new functions designed within limit; complex logic split across helper methods |
| **Max 5 params/function** | PASS | Largest new function has 4 params (web_input_context has 1) |
| **Class-Based Architecture** | PASS | `InputInterceptor` class, parameter registry in `OperationExecutor`; no wrappers |

## Project Structure

### Documentation (this feature)

```text
specs/006-web-interactivity/
├── plan.md              # This file
├── research.md          # Phase 0: input interception, parameter taxonomy, 5-item compliance
├── data-model.md        # Phase 1: ParameterDefinition, OperationParameterSet, PreviewState
├── quickstart.md        # Phase 1: developer setup and architecture overview
├── contracts/           # Phase 1: API endpoint contracts
│   └── api.md           # New/modified REST endpoints
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
web_portal/
├── app.py               # MODIFY: import config.py (was security.py+theme.py), install input hook
├── menu_registry.py     # UNCHANGED
├── routes/
│   ├── dashboard.py     # UNCHANGED
│   ├── data.py          # UNCHANGED
│   ├── maps.py          # UNCHANGED
│   ├── operations.py    # MODIFY: add sites/devices/clients endpoints
│   └── settings.py      # UNCHANGED
├── services/
│   ├── config.py        # RENAME+MERGE: security.py + theme.py → config.py
│   ├── data_browser.py  # UNCHANGED
│   ├── event_bus.py     # UNCHANGED
│   ├── input_hook.py    # NEW: InputInterceptor class
│   └── operation.py     # MODIFY: add PARAMETER_REGISTRY, expand get_operation_parameters()
├── templates/
│   ├── base.html        # MODIFY: add data_preview.js script tag
│   ├── dashboard.html   # UNCHANGED
│   ├── data_browser.html # MODIFY: replace inline preview with modal trigger
│   ├── map_viewer.html  # UNCHANGED
│   └── operations.html  # MODIFY: enhance parameter form area, add modal
└── static/
    ├── css/
    │   └── portal.css   # MODIFY: add modal styles
    └── js/
        ├── portal.js        # UNCHANGED
        ├── operations.js    # MODIFY: extend parameter rendering (dropdowns, deps)
        └── data_preview.js  # NEW: modal preview component (shared)
```

**Structure Decision**: Extends the existing `web_portal/` monorepo structure established in feature 005. No new top-level packages. The `services/` directory stays at 5 items by merging `security.py` + `theme.py` → `config.py`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | — | — |

No constitution violations. All rules satisfied by design.
