# Tasks: Web Portal Interactivity

**Input**: Design documents from `/specs/006-web-interactivity/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.md, quickstart.md

**Tests**: Not requested in spec — test tasks omitted. Manual testing per quickstart.md in Polish phase.

**Organization**: Tasks grouped by user story. US1 and US2 are both P1 but independent — US2 (modal) is simpler and can run in parallel with US1. US3 (P2) depends on US2 completion.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Merge config files to maintain 5-item rule compliance in services/, preparing room for new input_hook.py

- [X] T001 Merge SecurityMiddleware and PortalConfigLoader from security.py with ThemeManager from theme.py into web_portal/services/config.py, then delete security.py and theme.py
- [X] T002 Update all imports in web_portal/app.py from security and theme modules to config module

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Input interception infrastructure and parameter registry that ALL interactive operations depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 [P] Create InputInterceptor class in web_portal/services/input_hook.py with install() classmethod that replaces builtins.input, _patched_input() that reads from threading.local() deque, and web_input_context() context manager that sets/clears the per-thread queue
- [X] T004 [P] Add PARAMETER_REGISTRY dict to web_portal/services/operation.py with entries for simple site-only operations (menus 29, 30, 31, 32, 34, 49, 50, 51, 52, 53, 68, 70, 71, 84) using ParameterDefinition format from data-model.md
- [X] T005 Call InputInterceptor.install() in web_portal/app.py startup, and add category field to each operation in GET /api/operations/list response in web_portal/routes/operations.py by calling get_operation_parameters()

**Checkpoint**: Input interception active, parameter registry queryable — user story implementation can begin

---

## Phase 3: User Story 1 — Run Interactive Operations from the Browser (Priority: P1) MVP

**Goal**: Enable ~35 interactive operations to execute from the web portal by presenting parameter forms (site/device/client dropdowns, text/number inputs) and injecting answers into the input() call chain

**Independent Test**: Navigate to Operations, select Menu 31, see site dropdown, select a site, click Run, see device list in Execution Log

### Implementation for User Story 1

- [X] T006 [US1] Add GET /api/operations/sites endpoint returning org sites list in web_portal/routes/operations.py (reuse mistapi listOrgSites from app.config apisession)
- [X] T007 [P] [US1] Add GET /api/operations/sites/{site_id}/devices endpoint with type query param in web_portal/routes/operations.py (call mistapi listSiteDevices with type filter)
- [X] T008 [P] [US1] Add GET /api/operations/sites/{site_id}/clients endpoint in web_portal/routes/operations.py (call mistapi searchSiteWirelessClients + searchSiteWiredClients, merge results)
- [X] T009 [US1] Modify POST /api/operations/run to extract input_answers from parameters and pass to executor in web_portal/routes/operations.py
- [X] T010 [US1] Wrap func() call in _execute_operation() with web_input_context(input_answers) in web_portal/services/operation.py so input() calls are fed from the answer queue
- [X] T011 [US1] Extend loadParameters() in web_portal/static/js/operations.js to fetch GET /api/operations/parameters/{menu} and call renderParameterFields() with the returned parameter definitions
- [X] T012 [US1] Implement renderParameterFields() in web_portal/static/js/operations.js to render site dropdown (populated via GET /api/operations/sites), with loading spinner and empty-state message
- [X] T013 [US1] Add dependency chain handling in web_portal/static/js/operations.js — when site dropdown changes, fetch devices via GET /api/operations/sites/{id}/devices and populate device dropdown; same for client dropdown
- [X] T014 [US1] Add choice (static options dropdown), text (input field), and number (input with min/max) parameter controls in renderParameterFields() in web_portal/static/js/operations.js
- [X] T015 [US1] Update runSelectedOperation() in web_portal/static/js/operations.js to collect all parameter values in order and send as input_answers array in POST body
- [X] T016 [US1] Add form validation in web_portal/static/js/operations.js — disable Run button until all required parameter fields are populated, show red border on unfilled required fields
- [X] T017 [US1] Add CLI-only operation handling in web_portal/static/js/operations.js — when category is cli_only, show cli_only_message with SSH port 2200 info instead of parameter form
- [X] T018 [P] [US1] Update parameter form area in web_portal/templates/operations.html — add container div for dynamic parameter controls, loading indicator, and error/retry display
- [X] T019 [US1] Add PARAMETER_REGISTRY entries for site+device operations (menus 33, 72, 73, 74, 80, 81, 85, 87, 88, 89) with depends_on and device_filter fields in web_portal/services/operation.py
- [X] T020 [US1] Add PARAMETER_REGISTRY entries for complex operations: packet captures (menus 9, 10) with capture_type choice and conditional fields, WebSocket commands (menus 5, 6, 7, 8) with site+device+text params, and client operations (menus 69, 86) in web_portal/services/operation.py
- [X] T021 [US1] Add PARAMETER_REGISTRY entries for CLI-only operations (menus 62, 79) with category cli_only and cli_only_message in web_portal/services/operation.py
- [X] T022 [US1] Add parameter fetch error handling with Retry button in web_portal/static/js/operations.js — show error message if sites/devices/clients API calls fail, with retry capability

**Checkpoint**: All ~35 interactive operations can be executed from the web portal with parameter forms

---

## Phase 4: User Story 2 — Modal Data Preview (Priority: P1)

**Goal**: Replace inline preview panel in Data Browser with a full-viewport Bootstrap 5 modal overlay supporting CSV (sortable, searchable, paginated), SQLite (table list + content), JSON, and LOG files

**Independent Test**: Go to Data Browser, click Preview on a CSV file, see full-screen modal with sortable table, search within it, close it, confirm page state unchanged

### Implementation for User Story 2

- [X] T023 [P] [US2] Create web_portal/static/js/data_preview.js with DataPreviewModal class — Bootstrap 5 modal initialization, openPreview(filepath) entry point, state management (currentPath, currentPage, searchQuery, sortColumn)
- [X] T024 [P] [US2] Add modal overlay CSS styles in web_portal/static/css/portal.css — full-viewport modal dimensions, table styling, search bar, pagination controls, loading spinner
- [X] T025 [US2] Add data_preview.js script tag to web_portal/templates/base.html after portal.js
- [X] T026 [US2] Add Bootstrap 5 modal markup to web_portal/templates/data_browser.html — modal container with header (filename + close button), search input, table area, pagination, export button
- [X] T027 [US2] Replace inline previewFile()/loadPreview()/closePreview() functions in web_portal/templates/data_browser.html to call DataPreviewModal.openPreview() instead, and remove old #previewPanel div
- [X] T028 [US2] Implement CSV rendering in web_portal/static/js/data_preview.js — fetch from GET /api/data/preview/{path}, render sortable table headers (click to sort asc/desc), paginated rows, search filter input with real-time filtering
- [X] T029 [US2] Implement SQLite rendering in web_portal/static/js/data_preview.js — fetch table list from preview endpoint, show table names with row counts, click table name to load contents in same modal
- [X] T030 [US2] Implement JSON and LOG rendering in web_portal/static/js/data_preview.js — formatted JSON with syntax highlighting, LOG as scrollable pre-formatted text
- [X] T031 [US2] Add CSV export button in web_portal/static/js/data_preview.js — export current view (respecting search filter) as downloadable CSV file
- [X] T032 [US2] Add keyboard dismiss (Escape key) and backdrop click handlers in web_portal/static/js/data_preview.js — verify page scroll position and state preserved on close

**Checkpoint**: Data Browser preview uses modal — sortable, searchable, paginated, exportable for all file types

---

## Phase 5: User Story 3 — Operation Results Preview in Modal (Priority: P2)

**Goal**: After an operation completes, allow previewing output files directly from the Operations page using the same modal component from US2

**Independent Test**: Run operation 11, wait for completion, click Preview on output CSV in results area, see modal with site data

### Implementation for User Story 3

- [X] T033 [US3] Add Bootstrap 5 modal markup to web_portal/templates/operations.html (same structure as data_browser.html modal from US2)
- [X] T034 [US3] Add Preview button next to each output file in showOutputFiles() in web_portal/static/js/operations.js — alongside existing Download button
- [X] T035 [US3] Wire Preview button click to DataPreviewModal.openPreview(filepath) in web_portal/static/js/operations.js, reusing the shared data_preview.js component

**Checkpoint**: All three user stories functional — interactive ops, modal preview on Data Browser, modal preview on Operations results

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validation, testing, and deployment

- [X] T036 Validate Python syntax with python -m py_compile MistHelper.py and verify no import errors in web_portal modules
- [ ] T037 Run manual test scenarios from specs/006-web-interactivity/quickstart.md — interactive operation (Menu 31), modal preview (CSV), operation results preview
- [X] T038 Commit all changes to 006-web-interactivity branch with message "006-web-interactivity: implement interactive operations, modal preview, results preview"
- [ ] T039 Push to origin, wait for container build, pull new image, restart container, verify with podman ps

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS US1 (input hook + registry needed)
- **US1 (Phase 3)**: Depends on Foundational — needs InputInterceptor and PARAMETER_REGISTRY
- **US2 (Phase 4)**: Depends on Setup only — can run in PARALLEL with Foundational + US1 (uses existing preview API, no input hook needed)
- **US3 (Phase 5)**: Depends on US2 completion (reuses modal component)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Depends on Phase 2 (Foundational) — InputInterceptor and PARAMETER_REGISTRY required
- **US2 (P1)**: Independent of US1 — only needs Phase 1 (Setup) complete. Can run in parallel with US1
- **US3 (P2)**: Depends on US2 — reuses DataPreviewModal component from data_preview.js

### Within Each User Story

- Backend routes before frontend JS (frontend calls the API)
- Service layer changes before route changes (routes call services)
- Core form rendering before advanced controls (dropdowns before validation)
- Simple registry entries before complex ones (site-only before packet captures)

### Parallel Opportunities

**Phase 2 (Foundational)**:
- T003 (input_hook.py) and T004 (PARAMETER_REGISTRY) can run in parallel — different files

**Phase 3 (US1)**:
- T007 (devices endpoint) and T008 (clients endpoint) can run in parallel — independent endpoints in same file but non-overlapping
- T018 (operations.html) can run in parallel with T011-T017 (operations.js) — different files

**Phase 4 (US2)**:
- T023 (data_preview.js) and T024 (portal.css) can run in parallel — different files

**Cross-story parallelism**:
- US2 (Phase 4) can be implemented entirely in parallel with Foundational (Phase 2) and US1 (Phase 3) since it only touches data_preview.js, portal.css, data_browser.html, and base.html — none of which overlap with US1 files

---

## Parallel Example: US1 Backend + US2 Frontend

```
# These can run simultaneously since they touch different files:

# Stream A: US1 Backend (Phase 2 + Phase 3 backend)
T003: Create input_hook.py
T004: Add PARAMETER_REGISTRY to operation.py
T005: Install hook in app.py + category in routes
T006-T010: Backend endpoints and executor changes

# Stream B: US2 Modal (Phase 4)
T023: Create data_preview.js
T024: Add modal CSS to portal.css
T025: Add script tag to base.html
T026-T032: Modal rendering and features in data_browser.html + data_preview.js
```

---

## Implementation Strategy

### MVP First (US1 Only — Interactive Operations)

1. Complete Phase 1: Setup (merge config files)
2. Complete Phase 2: Foundational (input hook + registry)
3. Complete Phase 3: US1 (interactive operations)
4. **STOP and VALIDATE**: Select Menu 31, verify site dropdown, run operation
5. Deploy if ready — the ~35 interactive operations now work from the browser

### Incremental Delivery

1. Setup + Foundational → Infrastructure ready
2. US1 → Interactive operations working → Deploy (MVP!)
3. US2 → Modal preview on Data Browser → Deploy
4. US3 → Preview on Operations results → Deploy (Full feature)
5. Each story adds value without breaking previous stories

### Recommended Parallel Strategy

Since US2 is independent of US1:
1. Complete Phase 1 (Setup) first — 2 tasks
2. Start US1 (Phases 2-3) and US2 (Phase 4) in parallel
3. Once US2 completes, US3 can begin immediately
4. Polish after all stories complete

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- No new Python dependencies required — Bootstrap 5 already bundled as vendor asset
- PARAMETER_REGISTRY is split across T004 (simple ops), T019 (site+device), T020 (complex), T021 (cli-only) to keep each task manageable
- All operations.js changes are sequential within US1 (same file, building on each other)
- The 5-item rule is maintained: services/ stays at 5 files after config.py merge + input_hook.py addition
