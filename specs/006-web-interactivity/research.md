# Research: Web Portal Interactivity

**Feature**: 006-web-interactivity  
**Date**: 2026-03-04  
**Status**: Complete

## R1: Input Interception Mechanism

**Decision**: `builtins.input` monkeypatch with `threading.local()` per-thread queues

**Rationale**:
- Python resolves `input()` through `builtins` at **call time** (not import time). Replacing `builtins.input` transparently intercepts all callers — both raw `input()` calls (~153 sites) and `InputUtils.safe_input()` (~131 sites, which wraps `input()` on line 2113).
- `threading.local()` gives each thread an isolated namespace with zero locking overhead. Each operation thread gets its own `deque` of pre-filled answers.
- A context manager (`web_input_context`) sets the queue before the operation runs and clears it in `finally` — essential because `ThreadPoolExecutor` reuses threads.

**Alternatives considered**:
- `unittest.mock.patch`: Not designed for concurrent threading — patches globally and restores on `__exit__`, creating race conditions between concurrent operations.
- Custom `sys.stdin` per thread: `sys.stdin` is a single global object; wrapping it in a thread-dispatching proxy is fragile and breaks if anything else reads stdin.

**Key implementation detail**: When the queue is empty (more prompts than expected), `_patched_input()` raises `EOFError`. For calls through `safe_input()`, this is caught and returns `default_value` — graceful fallback. For raw `input()` calls, it propagates to `_execute_operation()` which catches `EOFError`.

---

## R2: Parameter Discovery Strategy

**Decision**: Static `PARAMETER_REGISTRY` dictionary mapping menu numbers to ordered parameter definitions

**Rationale**:
- Only ~35 operations require parameters; the mapping is a one-time manual effort.
- Runtime introspection (e.g., `inspect.signature()`) cannot discover input prompts — they are embedded in function bodies, not function signatures.
- A static registry enables the frontend to render the correct form controls before execution.

**Alternatives considered**:
- AST parsing of function bodies: Fragile, would break on refactors, cannot determine parameter semantics.
- Decorator-based annotation: Would require modifying MistHelper.py's 284 input call sites — violates the "minimal monolith changes" principle.

---

## R3: Parameter Type Taxonomy

**Decision**: Six parameter types cover all ~35 interactive operations

| Type | Control | Data Source | Operations |
|------|---------|-------------|------------|
| `site` | Dropdown | `/api/maps/sites` (existing) | 29-34, 49-53, 68-74, 84-86 |
| `device` | Dropdown (depends on site) | New `/api/operations/devices` | 33, 72-74, 79-81, 85, 87-89 |
| `client` | Dropdown (depends on site) | New `/api/operations/clients` | 69, 86 |
| `choice` | Dropdown (static options) | Registry `options` field | 9 (capture type), 62 (troubleshoot sub-menu) |
| `text` | Text input | User-entered | 87 (hostname), 89 (service name) |
| `number` | Number input | User-entered | 9-10 (duration, packet count) |

**Rationale**: These six types map directly to the input prompts observed across all interactive operations. No operation requires a type outside this set.

---

## R4: Operation Category Classification

**Decision**: Three operation categories for web portal behavior

| Category | Menu Numbers | Behavior |
|----------|-------------|----------|
| Non-interactive | 1-4, 11-28, 35-48, 54-67, 75-78, 82-83 | Run immediately (existing) |
| Interactive | 5-10, 29-34, 49-53, 68-74, 80-81, 84-89 | Show parameter form, then run |
| CLI-only | 62 (Troubleshoot), 79 (CLI Shell) | Show "Use SSH" message |
| Destructive | 90-100 | Blocked (existing DESTRUCTIVE_THRESHOLD) |

**Rationale**: Menu 62 has free-form multi-step interactions that cannot be pre-filled. Menu 79 is an interactive CLI shell requiring ongoing keyboard input. Both should direct users to SSH access (port 2200).

---

## R5: Site/Device Data Source

**Decision**: Reuse existing `/api/maps/sites` endpoint for site list; add new device/client endpoints

**Rationale**:
- `/api/maps/sites` already fetches organization sites via `mistapi.api.v1.orgs.sites.listOrgSites()`. No duplication needed.
- Device and client lists are site-specific and need new endpoints: `/api/operations/sites/<site_id>/devices` and `/api/operations/sites/<site_id>/clients`.
- Device endpoint must accept a `type` query parameter (ap/switch/gateway/all) to match how operations filter devices.

**Alternatives considered**:
- Fetching devices client-side via direct API calls: Would require exposing Mist API credentials to the browser — security violation.

---

## R6: Modal Preview Component

**Decision**: Bootstrap 5 modal using existing vendor bundle, with the same preview API backend

**Rationale**:
- Bootstrap 5 is already bundled at `web_portal/static/vendor/bootstrap/`. The modal component requires zero additional dependencies.
- The existing `/api/data/preview/<filepath>` endpoint with pagination, search, and sort support provides all the data the modal needs.
- The modal replaces the inline `<div id="previewPanel">` which currently pushes page content around.

**Alternatives considered**:
- Custom overlay without Bootstrap: Would duplicate modal behavior (backdrop, keyboard dismiss, focus trap) already provided by Bootstrap.
- Separate preview page: Would lose page context — the user story explicitly requires no navigation.

---

## R7: 5-Item Rule Compliance for services/

**Decision**: Merge `theme.py` into `security.py` (renamed to `config.py`), add `input_hook.py`

**Rationale**:
- Current `services/` has 5 files: `data_browser.py`, `event_bus.py`, `operation.py`, `security.py`, `theme.py`.
- Adding `input_hook.py` would make 6 — violating the 5-item rule.
- `ThemeManager` (50 lines) and `PortalConfigLoader`/`SecurityMiddleware` (130 lines) both handle portal configuration. Merging them into `config.py` is semantically coherent and keeps class count at 3 (within the 5-class-per-module limit).
- The parameter registry will be added to `operation.py` as a `PARAMETER_REGISTRY` constant + expanding `get_operation_parameters()` — this is the natural home since the executor already has the method stub.

**Result**:
```
services/
├── config.py          # Was security.py, gains ThemeManager from theme.py
├── data_browser.py    # Unchanged
├── event_bus.py       # Unchanged
├── input_hook.py      # NEW: InputInterceptor class
├── operation.py       # Gains PARAMETER_REGISTRY dict
```
5 files — compliant.

---

## R8: Frontend Architecture for Parameter Forms

**Decision**: Extend `operations.js` with parameter rendering logic; add `data_preview.js` for modal

**Rationale**:
- `operations.js` already has `loadParameters()`, `renderParameterFields()` stubs. The parameter form rendering naturally extends this file.
- The modal preview component is used on both Data Browser and Operations pages — it must be a separate JS file (`data_preview.js`) included on both templates.
- `static/js/` currently has 2 files. Adding 1 makes 3 — well within the 5-item limit.

---

## R9: Packet Capture Parameter Complexity

**Decision**: Multi-section form with conditional fields driven by capture type

**Rationale**:
- Menu 9 (Site Packet Capture) has 6 sub-types, each with different parameter sets (3-8 fields per type).
- A "capture type" dropdown (choice parameter) shows/hides relevant fields dynamically.
- All fields are pre-fillable (dropdowns, numbers, checkboxes) — no free-form interaction needed.
- The parameter registry uses a `depends_on` field to express conditional visibility.

---

## R10: WebSocket Command Parameters (Menus 5-8, 87-89)

**Decision**: Support with site + device + optional text/number parameters

**Rationale**:
- WebSocket commands follow a consistent pattern: select site → select device → optional parameters (IP prefix, VRF, protocol, etc.).
- Optional text parameters can have sensible defaults (empty string = "show all").
- The WebSocket connection and command execution happen server-side; the web form only collects parameters.
