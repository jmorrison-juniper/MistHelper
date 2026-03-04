# Implementation Plan: Web Portal Interface

**Branch**: `005-web-portal` | **Date**: 2026-03-04 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-web-portal/spec.md`

## Summary

Add a Flask + Gunicorn web portal to MistHelper that runs alongside the existing SSH service in the container on port 8055. The portal provides browser-based access to data browsing/download, non-destructive operation execution (menus 1-89) with SSE real-time progress, theming (dark/light/high-contrast), and ENV-driven branding. The existing Dash-based map viewer (`maps_manager.py` on port 8050) is absorbed into the Flask portal and the standalone Dash dependency is retired. See [research.md](research.md) for key technical decisions.

## Technical Context

**Language/Version**: Python 3.13+  
**Primary Dependencies**: Flask>=3.0.0 (direct), Gunicorn>=22.0.0 (new), flask-wtf>=1.2.0 (new, CSRF), Bootstrap 5 (new, bundled static), Plotly.js (bundled static), Jinja2 (transitive via Flask)  
**Storage**: SQLite (`data/mist_data.db`), CSV files in `data/`, browser localStorage (theme persistence)  
**Testing**: `python -m py_compile` (syntax), `python MistHelper.py --test` (integration), manual browser testing  
**Target Platform**: Linux container (Podman/Docker) serving desktop browsers (Chrome, Firefox, Edge at 1920x1080 and 1366x768)  
**Project Type**: Web service embedded within existing CLI/SSH container  
**Performance Goals**: 200ms theme switch, 3s CSV preview (50MB/1000 rows), 10s container dual-service startup, 5 concurrent sessions  
**Constraints**: 5-item rule (max 5 children per level, max 25 lines per function), class-based architecture, coexist with SSH on port 2200, non-destructive operations only (menus 1-89)  
**Scale/Scope**: ~5 pages (dashboard, data browser, operations, map viewer, health), 3 CSS themes, 5 SSE event types

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. 5-Item Rule

| Level | Planned | Compliant | Notes |
|-------|---------|-----------|-------|
| Top-level directories | `web_portal/` (1 new dir at repo root) | YES | Joins existing MistHelper.py, maps_manager.py, etc. |
| web_portal/ children | __init__.py, app.py, routes/, services/, templates/, static/ | YES | 6 items (5 + __init__.py) |
| templates/ children | base.html, dashboard.html, data_browser.html, operations.html, map_viewer.html | YES | 5 items; partials go in templates/partials/ |
| static/ children | css/, js/, img/ | YES | 3 items |
| css/ children | themes/ (dir), portal.css, bootstrap.min.css | YES | 3 items |
| themes/ children | dark.css, light.css, high-contrast.css | YES | 3 items |
| Class method counts | Each class max 5 public methods | VERIFY | Will enforce during Phase 1 design |
| Function params | Max 5 per function | VERIFY | Will enforce during implementation |
| Function length | Max 25 lines per function | VERIFY | Will enforce during implementation |

**Status**: PASS (verified post-Phase 1 design)

### II. Class-Based Architecture

All web portal functionality will be organized into semantic classes:
- `WebPortalApp` — Flask app factory and configuration
- `DataBrowserService` — file listing, CSV/SQLite preview, download serving
- `OperationExecutor` — background operation dispatch, status tracking, file locking
- `PortalEventBus` — SSE event publish-subscribe for real-time server-to-client communication
- `ThemeManager` — CSS theme enumeration and ENV default resolution
- `PortalConfigLoader` — ENV branding variable loading (title, logo, accent, allowed IPs)
- `SecurityMiddleware` — CSRF, CSP headers, IP allowlisting middleware

No standalone wrapper functions. Each class has single responsibility.

**Status**: PASS

### III. Safety-First Input Handling

- Web portal exposes only non-destructive operations (menus 1-89) — FR-015
- All form submissions include CSRF tokens — FR-018
- All output auto-escaped via Jinja2 — FR-019
- CSP headers on all responses — FR-020
- IP allowlisting guard — FR-021
- Operation parameters validated server-side before execution
- No `input()` calls in web context (all interaction via HTTP/WebSocket)

**Status**: PASS

### IV. Natural Business Keys

- Operation tracking uses menu number (natural key from existing system)
- Data files identified by filesystem path (natural key)
- No new database tables or surrogate keys needed
- SQLite tables preserve existing primary key strategies

**Status**: PASS

### V. Target Audience Clarity

- Bootstrap 5 provides accessible, familiar UI patterns for NOC engineers
- Clear operation descriptions from existing `menu_actions` descriptions
- Progress indicators via SSE (visible, no hidden background jobs)
- Destructive operations completely hidden (not greyed out — absent)

**Status**: PASS

### Gate Result: **ALL GATES PASS** — Proceeding to Phase 0

### Post-Phase 1 Re-Evaluation (2026-03-04)

Changes from research:
- **WebSocket → SSE**: Flask-SocketIO dropped due to eventlet/gevent Python 3.13 compatibility issues. SSE provides equivalent user experience with zero extra dependencies. See [research.md R1](research.md#r1-real-time-communication--websocket-vs-sse-vs-polling).
- **Flask-SocketIO → flask-wtf**: Dependency swap. flask-wtf provides CSRF protection; SSE is a Flask built-in pattern.
- **`WebSocketHandler` → `PortalEventBus`**: Class renamed to reflect SSE pub-sub pattern.
- **Dash removed**: `maps_manager.py` Flask viewer already proves Plotly.js works without Dash. Dash dependency removed; plotly.min.js bundled as static vendor file.
- **Single Gunicorn worker**: `-w 1 -k gthread --threads 4` to avoid `apisession` fork-safety issues.

All constitution gates still pass after these changes.

## Project Structure

### Documentation (this feature)

```text
specs/005-web-portal/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (REST + WebSocket)
│   ├── rest-api.md      # HTTP endpoint contracts
│   └── sse-events.md    # SSE event contracts
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
web_portal/
├── __init__.py          # Package init, Flask app factory
├── app.py               # WebPortalApp class, Gunicorn entry point
├── routes/              # Route blueprints (5-item rule: max 5 files)
│   ├── __init__.py
│   ├── dashboard.py     # Dashboard + health routes
│   ├── data.py          # Data browser + download routes
│   ├── operations.py    # Operation execution + status routes
│   ├── maps.py          # Map viewer routes (absorbed from maps_manager.py)
│   └── settings.py      # Theme + branding API routes
├── services/            # Business logic classes
│   ├── __init__.py
│   ├── data_browser.py  # DataBrowserService class
│   ├── operation.py     # OperationExecutor class
│   ├── security.py      # SecurityMiddleware + PortalConfigLoader
│   ├── theme.py         # ThemeManager class
│   └── event_bus.py     # PortalEventBus class (SSE pub-sub)
├── templates/           # Jinja2 HTML templates
│   ├── base.html        # Master layout (navbar, footer, theme JS)
│   ├── dashboard.html   # Home dashboard
│   ├── data_browser.html # File listing + preview tables
│   ├── operations.html  # Operation menu + execution UI
│   └── map_viewer.html  # Embedded map viewer (replaces Dash)
└── static/              # Static assets
    ├── css/
    │   ├── portal.css       # Core portal styles
    │   └── themes/
    │       ├── dark.css         # Dark NOC theme (default)
    │       ├── light.css        # Light office theme
    │       └── high-contrast.css # Accessibility theme
    ├── js/
    │   ├── portal.js        # Theme switcher, SSE client, table pagination
    │   └── operations.js    # Operation form handling, progress display
    └── img/
        └── logo-default.svg # Default MistHelper logo
```

### Modified Existing Files

```text
MistHelper.py            # Add web portal integration hooks (OperationExecutor calls menu_actions)
Containerfile            # Add EXPOSE 8055, install gunicorn, update CMD
compose.yml              # Add port 8055 mapping, remove 8050
container/scripts/start.sh  # Start Gunicorn + sshd (dual service)
requirements.txt         # Add gunicorn, Flask, flask-wtf; remove dash (keep plotly)
```

**Structure Decision**: Web application pattern (Option 2 simplified) — Flask backend with server-rendered templates. No separate frontend build step. All static assets served directly by Flask/Gunicorn. The `web_portal/` package is a peer to `MistHelper.py` at the repository root, keeping the 5-item rule compliant at the top level.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| `services/` has 5 files + `__init__.py` | 5 service classes mapped to distinct responsibilities | Merging security+theme into one file would mix concerns |
| `routes/` has 5 files + `__init__.py` | 5 route groups cover the full portal feature surface | Fewer routes would create oversized modules |
| `web_portal/` has 5 children (app.py, routes/, services/, templates/, static/) | Clean separation of concerns following Flask conventions | Fewer top-level items would require nesting presentation with logic |

No constitution violations — all items are at or below the 5-item limit. Listed here for transparency.
