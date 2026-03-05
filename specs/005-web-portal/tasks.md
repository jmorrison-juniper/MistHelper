# Tasks: Web Portal Interface

**Input**: Design documents from `/specs/005-web-portal/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/rest-api.md, contracts/sse-events.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1-US5)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create package structure, install dependencies, bundle vendor assets

- [X] T001 Create web_portal/ directory tree with __init__.py files per plan.md project structure
- [X] T002 Update requirements.txt (+gunicorn>=22.0.0, +Flask>=3.0.0, +flask-wtf>=1.2.0, -dash)
- [X] T003 [P] Bundle Bootstrap 5.3 CSS and JS into web_portal/static/vendor/bootstrap/
- [X] T004 [P] Bundle plotly.min.js into web_portal/static/vendor/plotly/
- [X] T005 [P] Create logo-default.svg placeholder in web_portal/static/img/logo-default.svg

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Implement PortalConfigLoader class (read ENV branding, theme, port, allowed IPs) in web_portal/services/security.py
- [X] T007 Implement SecurityMiddleware class (CSRF via flask-wtf, CSP headers, XSS escaping, IP allowlist) in web_portal/services/security.py
- [X] T008 [P] Implement ThemeManager class (enumerate theme CSS files, resolve ENV default) in web_portal/services/theme.py
- [X] T009 Implement WebPortalApp.create_app() app factory (register blueprints, inject apisession/menu_actions/org_id, apply security) in web_portal/app.py
- [X] T010 Create base.html master layout (navbar with logo/title, theme switcher dropdown, footer, CSS/JS includes, CSRF meta tag) in web_portal/templates/base.html
- [X] T011 [P] Create portal.css core layout styles (navbar, sidebar, content area, tables, responsive breakpoints) in web_portal/static/css/portal.css
- [X] T012 [P] Create portal.js (theme switcher with localStorage, sortable table utilities, SSE EventSource helper, CSRF token reader) in web_portal/static/js/portal.js

**Checkpoint**: Flask app starts with `python -c "from web_portal.app import WebPortalApp; app = WebPortalApp.create_app(None, {}, None); app.run(port=8055)"` and serves base.html at http://localhost:8055

---

## Phase 3: User Story 1 — View and Download Existing Data (Priority: P1) MVP

**Goal**: NOC engineers browse and download CSV/SQLite data from the portal without CLI access

**Independent Test**: Navigate to http://localhost:8055/data, verify file listing with sizes and dates, preview a CSV in a sortable table, download a file, preview a SQLite table

### Implementation for User Story 1

- [X] T013 [US1] Implement DataBrowserService class (list files via os.scandir, preview CSV with pagination, preview SQLite tables, path traversal guard) in web_portal/services/data_browser.py
- [X] T014 [US1] Implement data routes blueprint (GET /data, GET /api/data/files, GET /api/data/preview/{path}, GET /api/data/preview/{path}/{table}, GET /api/data/download/{path}) in web_portal/routes/data.py
- [X] T015 [US1] Create data_browser.html template (file list table with sort/filter, inline preview panel with pagination, download buttons, empty state message) in web_portal/templates/data_browser.html
- [X] T015b [P] [US1] Add CSV export/download button to data_browser.html and operations.html table views (FR-017: any table displayed in the portal can be exported as CSV) — client-side CSV generation via Blob + download link in portal.js
- [X] T016 [US1] Implement dashboard routes blueprint (GET / home page, GET /health JSON endpoint) in web_portal/routes/dashboard.py
- [X] T017 [US1] Create dashboard.html template (data directory summary card, recent files list, quick-link cards to data/operations/maps) in web_portal/templates/dashboard.html

**Checkpoint**: Browse http://localhost:8055/data — see file listing, preview a CSV with pagination, download a file, see SQLite table list. Dashboard at / shows summary.

---

## Phase 4: User Story 2 — Run Data Extraction Operations (Priority: P2)

**Goal**: NOC engineers execute Mist API operations from the portal with real-time SSE progress

**Independent Test**: Select operation 1 (List Org Sites), confirm it runs, see progress events via SSE, verify output appears in data browser

### Implementation for User Story 2

- [X] T018 [US2] Implement PortalEventBus class (publish-subscribe with per-subscriber bounded Queue, heartbeat timer, subscriber cleanup) in web_portal/services/event_bus.py
- [X] T019 [US2] Implement OperationExecutor class (background thread dispatch via ThreadPoolExecutor, OperationRun state tracking with Lock, category mapping from menu number ranges, log capture) in web_portal/services/operation.py
- [X] T020 [US2] Implement operations routes blueprint (GET /operations page, GET /api/operations/list, POST /api/operations/run with CSRF, GET /api/operations/status/{run_id}, GET /api/operations/active, GET /api/operations/stream SSE endpoint, GET /api/operations/parameters/{menu_number}) in web_portal/routes/operations.py
- [X] T021 [US2] Create operations.html template (categorized accordion menu, operation detail panel with parameter dropdowns, execution log viewer, progress bar area) in web_portal/templates/operations.html
- [X] T022 [US2] Create operations.js (operation form submission with CSRF, EventSource SSE client for progress/log/complete/error events, progress bar updates, log line appending, completion notification) in web_portal/static/js/operations.js
- [X] T023 [US2] Add --web-portal CLI flag and launch_web_portal() function in MistHelper.py (parse arg, create Flask app with apisession/menu_actions/org_id, run Flask dev server on Windows or Gunicorn programmatically in container)

**Checkpoint**: Start operation from portal, see SSE progress events in real time, verify output file appears in data browser after completion

---

## Phase 5: User Story 3 — Theme Customization (Priority: P3)

**Goal**: Users switch between dark/light/high-contrast themes with instant visual feedback and persistence

**Independent Test**: Open portal with dark default, click theme switcher, select light, verify instant UI change without reload, refresh page, confirm light theme persists via localStorage

### Implementation for User Story 3

- [X] T024 [P] [US3] Create dark.css NOC theme (charcoal background, green/cyan accents, light text, table striping, code block styling) in web_portal/static/css/themes/dark.css
- [X] T025 [P] [US3] Create light.css office theme (white background, blue accents, dark text, subtle shadows, card borders) in web_portal/static/css/themes/light.css
- [X] T026 [P] [US3] Create high-contrast.css accessibility theme (black background, yellow/white text, thick borders, no gradients, enlarged focus indicators) in web_portal/static/css/themes/high-contrast.css
- [X] T027 [US3] Implement settings routes blueprint (GET /api/themes listing available themes with default indicator) in web_portal/routes/settings.py

**Checkpoint**: Theme switcher in navbar works — switching themes applies instantly, selection persists across page loads via localStorage, matches ENV default on first visit

---

## Phase 6: User Story 4 — Portal Branding via ENV (Priority: P4)

**Goal**: Administrators customize portal title, logo, and accent color via ENV without code changes

**Independent Test**: Set PORTAL_TITLE=ACME, PORTAL_LOGO_URL=/custom/logo.png, PORTAL_ACCENT_COLOR=#FF6B35 in .env, restart portal, verify branding appears in header and throughout UI

### Implementation for User Story 4

- [X] T028 [US4] Add context_processor to inject PortalConfig branding (title, logo_url, accent_color) into all templates via web_portal/app.py
- [X] T029 [US4] Add accent color CSS custom property (--portal-accent) injection and logo src binding to base.html template

**Checkpoint**: Portal displays custom title in navbar and page title, custom logo in header, accent color on buttons/links/highlights — all from ENV values only

---

## Phase 7: User Story 5 — Container Integration (Priority: P2)

**Goal**: Container runs both SSH (port 2200) and web portal (port 8055) with health monitoring

**Independent Test**: Build container, run it, verify `ssh -p 2200 misthelper@localhost` works AND `curl http://localhost:8055/health` returns healthy

### Implementation for User Story 5

- [X] T030 [US5] Create dual-process startup script (background Gunicorn on WEB_PORT, background sshd, trap SIGTERM/SIGINT to kill both, wait for exit) in container/scripts/start.sh
- [X] T031 [US5] Update Containerfile (EXPOSE 8055, pip install web portal deps, COPY web_portal/, CMD container/scripts/start.sh)
- [X] T032 [US5] Update compose.yml (add port 8055:8055 mapping, remove port 8050:8050, add WEB_PORT env var)
- [X] T033 [US5] Add Gunicorn WSGI entry point module (bootstrap apisession and menu_actions for container startup) in web_portal/wsgi.py

**Checkpoint**: `podman build && podman run` — both SSH (port 2200) and web portal (port 8055) accessible; `curl :8055/health` returns `{"status": "healthy"}`

---

## Phase 8: Map Viewer Integration (FR-022)

**Goal**: Absorb maps_manager.py Dash viewer into Flask portal; retire standalone Dash dependency

- [X] T034 Implement map viewer routes blueprint (GET /maps page, GET /api/maps/sites, GET /api/maps/site/{id}/maps, GET /api/maps/site/{id}/map/{id}/data, GET /api/maps/image/{id}) in web_portal/routes/maps.py
- [X] T035 Create map_viewer.html template (site dropdown selector, floor plan dropdown, Plotly.js rendering area via Plotly.react(), device overlay markers) in web_portal/templates/map_viewer.html
- [X] T036 Refactor maps_manager.py (remove Dash app creation and standalone __main__ block, keep MapsManager class API methods as pure library, update MistHelper.py MapsManagerLauncher to use portal route)

**Checkpoint**: Navigate to http://localhost:8055/maps — select a site, see interactive floor plan map with device markers rendered via Plotly.js

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, validation, and deployment

- [X] T037 [P] Update README.md (add web portal section, ENV variable reference table, updated operation count, version changelog entry)
- [X] T038 Run py_compile syntax validation on all new Python files and MistHelper.py --test integration tests
- [X] T039 Execute full deployment pipeline (git add, commit with version timestamp, push, wait for container build, pull image, restart container, verify)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on T001 (directory structure) and T002 (dependencies installed)
- **US1 (Phase 3)**: Depends on Phase 2 completion (app factory, base template, security middleware)
- **US2 (Phase 4)**: Depends on Phase 2 completion; benefits from US1 for data browser integration but independently testable
- **US3 (Phase 5)**: Depends on Phase 2 (ThemeManager, base.html theme link); no dependency on US1 or US2
- **US4 (Phase 6)**: Depends on Phase 2 (PortalConfigLoader, base.html); no dependency on other stories
- **US5 (Phase 7)**: Depends on Phase 2; benefits from at least US1 complete for deployment validation
- **Maps (Phase 8)**: Depends on Phase 2; independent of all user stories
- **Polish (Phase 9)**: Depends on all desired phases being complete

### User Story Independence

- **US1**: Independently testable after Phase 2 — data browser works without operations, themes, or branding
- **US2**: Independently testable after Phase 2 — operations work with base theme only
- **US3**: Independently testable after Phase 2 — theme switching works on any page including base template
- **US4**: Independently testable after Phase 2 — branding visible on base template header/title
- **US5**: Requires at least Phase 2 for meaningful container testing

### Within Each User Story

- Service classes → route blueprints (routes import services)
- Route blueprints → templates (templates render route context)
- Python backend → JavaScript (JS enhances server-rendered HTML)

### Parallel Opportunities

Within Phase 1:
- T003, T004, T005 can all run in parallel (different static asset directories)

Within Phase 2:
- T008 (ThemeManager) can run in parallel with T006/T007 (different files)
- T011, T012 can run in parallel with each other and with T010 (css, js, html — different files)

Within Phase 5:
- T024, T025, T026 can all run in parallel (three independent CSS theme files)

Cross-story parallelism (after Phase 2):
- US1 and US3 can be implemented simultaneously (different routes, templates, services)
- US4 can run in parallel with US1/US2/US3 (modifies existing files only)
- Map Viewer (Phase 8) can run in parallel with US3/US4/US5

---

## Parallel Example: Phase 2

```text
# T006 runs first (PortalConfigLoader creates security.py):
Task T006: "PortalConfigLoader in services/security.py"

# After T006, these run simultaneously (different files):
Task T007: "SecurityMiddleware in services/security.py"  (extends T006's file)
Task T008: "ThemeManager in services/theme.py"           (new file, parallel)

# After T007+T008, T009 runs (imports both):
Task T009: "WebPortalApp.create_app() in app.py"

# After T009, these run simultaneously (different file types):
Task T010: "base.html template"
Task T011: "portal.css"
Task T012: "portal.js"
```

## Parallel Example: User Story 1

```text
# T013 runs first (service layer):
Task T013: "DataBrowserService in services/data_browser.py"

# After T013, routes can start (both independent, different files):
Task T014: "data routes in routes/data.py"
Task T016: "dashboard routes in routes/dashboard.py"

# Templates after their routes:
Task T015: "data_browser.html"   (after T014)
Task T017: "dashboard.html"      (after T016)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup → package structure and dependencies ready
2. Complete Phase 2: Foundational → Flask app serves base template
3. Complete Phase 3: User Story 1 → Data browser functional
4. **STOP and VALIDATE**: Browse files, preview CSVs, download data
5. This alone provides value: NOC engineers access data without SSH

### Incremental Delivery

1. Setup + Foundational → Flask shell running
2. \+ User Story 1 → Data browser MVP (deploy/demo)
3. \+ User Story 2 → Operations from browser (deploy/demo)
4. \+ User Story 3 → Theme switching (deploy/demo)
5. \+ User Story 4 → Custom branding (deploy/demo)
6. \+ User Story 5 → Container deployment (deploy/demo)
7. \+ Map Viewer → Full feature parity with standalone Dash viewer
8. Polish → Documentation + final deployment

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- Each checkpoint validates story independence before proceeding
- Commit after completing each phase
- Theme CSS files (T024-T026) are the easiest parallel batch
- Map viewer (Phase 8) can be deferred without affecting other stories
- US4 (Branding) is very thin — 2 tasks modifying existing files from Phase 2
- Gunicorn is Linux-only; local Windows development uses Flask dev server
- All service classes enforce max 5 public methods and max 25 lines per function (constitution)
