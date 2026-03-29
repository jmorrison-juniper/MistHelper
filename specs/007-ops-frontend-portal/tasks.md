# Tasks: Ops Frontend Portal

**Input**: Design documents from `/specs/007-ops-frontend-portal/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/api-client.md, contracts/routes-views.md, quickstart.md

**Tests**: Not explicitly requested in the feature specification. Unit and component test tasks are omitted. E2E test scaffolding is included in the Polish phase per research.md R-08.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

All paths are relative to the repository root. The frontend portal lives in `ops-portal/`:

- Source: `ops-portal/src/`
- API client & query factories: `ops-portal/src/api/` (5 files: client, config, deploy, audit, sync)
- Shared components: `ops-portal/src/components/` (DiffViewer, ConfirmationDialog, PaginatedTable, ProgressTracker)
- Feature modules: `ops-portal/src/features/` (5 dirs: dashboard, config, deploy, audit, drift)
- Shared hooks: `ops-portal/src/hooks/` (5 files: useNavigationContext, useSession, useSettings, useConnectivity, useTelemetry)
- Page components: `ops-portal/src/pages/` (shell/, dashboard/, config/, deploy/, audit/, drift/, settings/)
- Shell pages: `ops-portal/src/pages/shell/` (RootLayout.tsx, LoginPage.tsx)
- Deploy pages: `ops-portal/src/pages/deploy/` (jobs/, rollouts/, TemplatesPage.tsx, GoldenImagesPage.tsx)
- Deploy features: `ops-portal/src/features/deploy/` (jobs/, rollouts/)
- Container config: `ops-portal/nginx/`, `ops-portal/Containerfile`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, toolchain configuration, and container build setup

- [X] T001 Initialize ops-portal/ project with Vite 6 scaffolding, React 19, TypeScript 5.5, and all runtime dependencies (react-router, @tanstack/react-query, zustand, @headlessui/react, tailwindcss) in ops-portal/package.json
- [X] T002 [P] Configure TypeScript strict mode with ES2022 target, React JSX transform, and path aliases in ops-portal/tsconfig.json
- [X] T003 [P] Configure Vite dev server with /api/ proxy to localhost:8000, build output to dist/, and environment variable handling in ops-portal/vite.config.ts
- [X] T004 [P] Configure Tailwind CSS 4 with design tokens (spacing scale, color palette for diff highlighting and severity badges) in ops-portal/tailwind.config.ts and ops-portal/src/index.css
- [X] T005 [P] Configure ESLint with typescript-eslint, eslint-plugin-react, eslint-plugin-jsx-a11y, and Prettier integration in ops-portal/.eslintrc.cjs and ops-portal/.prettierrc
- [X] T006 [P] Create multi-stage Containerfile: Node.js 22 Alpine build stage (npm ci + npm run build) and Nginx 1.27 Alpine serve stage (copy dist/ to /usr/share/nginx/html/) in ops-portal/Containerfile
- [X] T007 [P] Create Nginx config with SPA try_files routing, /api/ reverse proxy to backend service, CSP/HSTS/X-Frame-Options/X-Content-Type-Options security headers, gzip compression, and cache-control (immutable for hashed assets, no-cache for index.html) in ops-portal/nginx/default.conf
- [X] T008 [P] Create environment template with VITE_API_BASE_URL, VITE_POLLING_ACTIVE_MS, VITE_POLLING_PASSIVE_MS variables in ops-portal/.env.example

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**Warning**: No user story work can begin until this phase is complete

### API Client

- [X] T009 Create ApiClient class with typed get/post/put/delete methods, /api/v1 base URL, Authorization header injection, response envelope unwrapping (extract data from {data, meta, errors}), error code mapping (401 redirect, 403 inline, 404 not found, 409 conflict, 429 rate limit, 5xx unavailable), and shared types (ApiResponse, PaginationMeta, ApiError, DiffChange, DiffSummary, NotificationItem, TimezonePreference) per FR-040 in ops-portal/src/api/client.ts

### State Management

- [X] T010 Create Zustand navigation store with NavigationContext type (mspId, orgId, orgName, siteId, siteName, deviceId), hierarchical validation (siteId requires orgId, deviceId requires siteId), clearing cascade on parent change, and localStorage persistence middleware in ops-portal/src/hooks/useNavigationContext.ts
- [X] T011 [P] Create Zustand session store with SessionState and OperatorIdentity types (isAuthenticated, sessionId, operator with email/name/role/orgs, expiresAt, returnUrl), login/logout actions, and session expiry detection per FR-005/FR-006/FR-007 in ops-portal/src/hooks/useSession.ts
- [X] T012 [P] Create Zustand settings store with PollingConfig (activeIntervalMs default 5000, passiveIntervalMs default 30000) and TimezonePreference (mode: local/utc/site) with localStorage persistence per FR-045 in ops-portal/src/hooks/useSettings.ts
- [X] T013 [P] Create connectivity detection hook with online/offline event listeners, reconnection polling, and "Connection Lost — Reconnecting" banner state per FR-041 in ops-portal/src/hooks/useConnectivity.ts

### Routing & App Shell

- [X] T014 Create React Router 7 route configuration with all 24 routes, auth guard wrapper (redirect to /login if unauthenticated with returnUrl preservation), and React.lazy loading for page components in ops-portal/src/router.tsx
- [X] T015 Create app entry point with StrictMode, QueryClientProvider (global error handler mapping 401/403/429/5xx to user-facing messages), RouterProvider, and index.css import in ops-portal/src/main.tsx and ops-portal/src/App.tsx

### Shared Components

- [X] T016 [P] Create DiffViewer component with side-by-side and stacked layout modes, color-coded field-level changes (red background for removed, green for added, amber for modified), DiffSummary counts header, accessibility icons (minus/plus/pencil) for colorblind support, and responsive layout switching per FR-015/R-04 in ops-portal/src/components/DiffViewer.tsx
- [X] T017 [P] Create ConfirmationDialog component using Headless UI Dialog with title, description, impact summary, optional keyword input field (typed confirmation like RESTORE/REMEDIATE/ROLLBACK), focus trap, Escape-to-close, and cancel/confirm buttons per FR-039 in ops-portal/src/components/ConfirmationDialog.tsx
- [X] T018 [P] Create PaginatedTable component with TanStack Query integration via queryKey prop, typed ColumnDef array, configurable FilterDef array, empty state message, optional row click handler, and pagination controls driven by PaginationMeta (page, perPage, total, totalPages) in ops-portal/src/components/PaginatedTable.tsx
- [X] T019 [P] Create ProgressTracker component with ordered Checkpoint list (label, status: pending/running/completed/failed, detail), progress bar (0-100 or null for indeterminate), elapsed time display, and configurable poll interval in ops-portal/src/components/ProgressTracker.tsx

### Layout & Authentication Pages

- [X] T020 Create RootLayout with TopBar (logo, search input placeholder, notification area placeholder, user identity display with role, logout button), NavBar (7 sections: Dashboard, Time-Travel, Config, Deploy, Audit, Drift, Settings with active-state highlighting), content area with React Router Outlet, and StatusBar (connectivity banner from useConnectivity, timezone mode toggle from useSettings) per FR-001/FR-004/FR-006 in ops-portal/src/pages/shell/RootLayout.tsx
- [X] T021 Create LoginPage with three authentication flows: API token text entry, email/password form with optional 2FA code field, and SSO redirect button, calling POST /auth/login via ApiClient and storing session in useSession store per FR-005 in ops-portal/src/pages/shell/LoginPage.tsx

**Checkpoint**: Foundation ready — user story implementation can now begin in priority order

---

## Phase 3: User Story 1 — Operational Dashboard & Navigation (Priority: P1) MVP

**Goal**: Operators land on a dashboard showing organization health at a glance, drill into the org/site/device hierarchy, search for entities, and see notifications — providing the shell that hosts every other feature.

**Independent Test**: Log in, verify dashboard renders organization cards with sync state and alert counts from inventory API, drill from org to site to device, confirm navigation context persists across views, verify global search returns results, and check notification badge displays unread count.

### Implementation for User Story 1

- [X] T022 [US1] Create sync query factory (syncQueries, systemQueries) with inventory queries (orgs, sites, devices), sync status query, drift alert count query, notification list query, and Domain 5 types (SyncStatus, EntitySyncCount, InventoryDevice, InventorySite, InventoryOrg, DriftAlert) in ops-portal/src/api/sync.ts
- [X] T023 [US1] Create DashboardPage with organization summary cards displaying org name, site count, device count, sync state badge (synced/stale/error), and active alert count (drift + deploy failures), with 30s passive polling via syncQueries per FR-008 in ops-portal/src/pages/dashboard/DashboardPage.tsx
- [X] T024 [P] [US1] Create OrgDetailPage with paginated site list filtered by orgId showing site name, location, device count, and health indicators, setting orgId/orgName in NavigationContext for hierarchical drill-down per FR-002 in ops-portal/src/pages/dashboard/OrgDetailPage.tsx
- [X] T025 [P] [US1] Create SiteDetailPage with device list grouped by type tabs (AP, switch, gateway) using PaginatedTable, showing connection status indicator, firmware version, and uptime, setting siteId/siteName in NavigationContext in ops-portal/src/pages/dashboard/SiteDetailPage.tsx
- [X] T026 [US1] Create DeviceDetailPage with device model, serial number, MAC address, firmware version, connection status, uptime, last seen timestamp, and contextual navigation links to time-travel (/time-travel), revision history (/config/revisions), drift alerts (/drift), and audit records (/audit) for that device per FR-009 in ops-portal/src/pages/dashboard/DeviceDetailPage.tsx
- [X] T027 [US1] Create GlobalSearch component with debounced input, search across orgs/sites/devices by name, serial, MAC, or IP via system query, grouped result dropdown with entity type labels, and direct navigation to matching entity detail page per FR-003 in ops-portal/src/features/dashboard/GlobalSearch.tsx
- [X] T028 [P] [US1] Create SyncStatusCard component displaying last sync time, next scheduled poll, and per-entity-type sync counts (total/synced/stale/error) with color-coded status indicators per FR-010 in ops-portal/src/features/dashboard/SyncStatusCard.tsx
- [X] T029 [US1] Create NotificationBadge component in TopBar with unread count badge, dropdown listing recent NotificationItems (approval_request, drift_alert, deploy_status, export_ready) with severity icons and clickable links to relevant views per FR-035 in ops-portal/src/features/dashboard/NotificationBadge.tsx

**Checkpoint**: Dashboard, navigation hierarchy, and inventory views fully functional. Operators can monitor fleet health and navigate to any entity.

---

## Phase 4: User Story 2 — Time-Travel Investigation (Priority: P1)

**Goal**: Operators select a device and past timestamp to view historical configuration, port states, client count, and health metrics, then compare the historical snapshot against the current live state using a field-level diff.

**Independent Test**: Navigate to a synced device, open time-travel view, select a past timestamp via date/time picker, verify historical config/ports/clients/health render from TimeTravelSnapshot, click "Compare with Current" and verify DiffViewer shows field-level changes, test retention window message for timestamps beyond data retention.

### Implementation for User Story 2

- [X] T030 [US2] Create config query factory (configQueries) with revision list query, diff mutation, time-travel query, baseline list query, and Domain 2 types (ConfigRevision, ConfigDiff, TimeTravelSnapshot, PortState, ConfigBaseline) in ops-portal/src/api/config.ts
- [X] T031 [US2] Create TimeTravelPage with device selector pre-populated from NavigationContext, date/time picker with calendar and clock inputs, timeline scrubber integration, and main panel displaying HistoricalStatePanel per FR-011 in ops-portal/src/pages/config/TimeTravelPage.tsx
- [X] T032 [P] [US2] Create TimelineScrubber component with interactive drag-to-select timestamp on a horizontal axis, smooth state updates via TanStack Query without full page reload, and dual display of queried timestamp vs actual data timestamp in ops-portal/src/features/config/TimelineScrubber.tsx
- [X] T033 [P] [US2] Create HistoricalStatePanel displaying device configuration as key-value tree, port states table (PortState[] with up/down/disabled indicators), connected client count, and health metrics gauges from TimeTravelSnapshot response in ops-portal/src/features/config/HistoricalStatePanel.tsx
- [X] T034 [US2] Implement "Compare with Current" action button that fetches current device config via configQueries and renders side-by-side field-level diff using DiffViewer component with "Historical" and "Current" labels per FR-012 in ops-portal/src/features/config/CompareWithCurrent.tsx
- [X] T035 [US2] Implement retention window handling: display clear "data has been aged out" message when query returns no data, show oldest available timestamp as clickable link that loads that snapshot, and graceful empty state per FR-013 in ops-portal/src/features/config/RetentionMessage.tsx

**Checkpoint**: Time-travel investigation fully functional. Operators can rewind device state to any timestamp and compare with current configuration.

---

## Phase 5: User Story 3 — Configuration Versioning, Diff & Restore (Priority: P1)

**Goal**: Operators view a chronological revision history for any entity, compare any two revisions with field-level diffs, and safely restore a known-good revision with confirmation gates and real-time progress tracking.

**Independent Test**: View revision history for an entity with multiple revisions, select two revisions and compute diff, verify DiffViewer renders color-coded changes with summary counts, initiate install-from-revision with RESTORE keyword confirmation, verify ProgressTracker shows per-device checkpoint status with 5s polling.

### Implementation for User Story 3

- [X] T036 [US3] Create deploy query factory (deployQueries) with job status query (for install progress tracking), install-from-revision mutation, and Domain 3 types (DeployJob, JobStatus, CheckConfig) in ops-portal/src/api/deploy.ts
- [X] T037 [US3] Create RevisionsPage with paginated revision history using PaginatedTable showing revision ID, captured timestamp (with timezone toggle), actor, source badge (sync/manual/restore), and content hash, scoped to entity from NavigationContext per FR-014 in ops-portal/src/pages/config/RevisionsPage.tsx
- [X] T038 [US3] Implement revision comparison: checkbox or click-select for two revisions, "Compare" button calling POST /config/diff, and field-level diff rendering using DiffViewer with change summary counts (added, removed, modified) per FR-015 in ops-portal/src/features/config/RevisionDiff.tsx
- [X] T039 [US3] Implement "Install from Revision" flow: button on revision row, ConfirmationDialog displaying target device count, revision timestamp, blast radius from dry-run, and RESTORE keyword requirement, calling POST /config/install-from-revision on confirmation per FR-016 in ops-portal/src/features/config/InstallFromRevision.tsx
- [X] T040 [US3] Implement real-time install-from-revision progress tracking using ProgressTracker with per-device checkpoints (pending, pushing, completed, failed), 5s active polling of GET /deploy/jobs/{id}, and "Retry Failed" action button per FR-017 in ops-portal/src/features/config/InstallProgress.tsx

**Checkpoint**: Config versioning and rollback fully functional. Operators can view history, compare revisions, and safely restore configurations with full progress visibility.

---

## Phase 6: User Story 4 — Deployment Scheduling & Approval (Priority: P2)

**Goal**: Operators create scheduled deployments with target selection, pre/post-checks, auto-rollback, run dry-runs to assess risk, submit for maker-checker approval, and monitor execution with real-time status updates.

**Independent Test**: Create a scheduled job with target devices, change payload, future schedule time with explicit timezone, and pre/post-checks. Run dry-run and verify risk score/blast radius display. Submit for approval, verify pending badge appears in notifications, approve the job, and monitor execution status transitions via ProgressTracker.

### Implementation for User Story 4

- [X] T041 [US4] Extend deploy query factory with dry-run mutation, job creation mutation, approval/reject mutations, cancel mutation, and additional Domain 3 types (DryRunResult, BlastRadius, ChangeTemplate, TemplateParam) in ops-portal/src/api/deploy.ts
- [X] T042 [US4] Create JobsListPage with filterable PaginatedTable (status filter: draft/pending_approval/approved/scheduled/running/completed/failed/cancelled/rolled_back, date range, creator), status badges with color coding, and row links to JobDetailPage per FR-021 in ops-portal/src/pages/deploy/jobs/JobsListPage.tsx
- [X] T043 [US4] Create JobDetailPage with job metadata (name, status, schedule, creator), target device list, change payload viewer, pre/post-check configuration and results, rollback status, approval state, and ProgressTracker for running jobs in ops-portal/src/pages/deploy/jobs/JobDetailPage.tsx
- [X] T044 [US4] Create NewJobPage with multi-step wizard: step 1 target selection via org/site/device browser or search, step 2 change payload entry (JSON editor or template selection), step 3 schedule date/time with explicit IANA timezone picker per FR-045, step 4 pre/post-check configuration and auto-rollback toggle, step 5 review and submit per FR-018 in ops-portal/src/pages/deploy/jobs/NewJobPage.tsx
- [X] T045 [P] [US4] Create DryRunPanel component displaying risk score gauge (low green/medium amber/high red), blast radius summary (device count, site count, estimated clients), warnings list with severity icons, and policy violations list per FR-019 in ops-portal/src/features/deploy/jobs/DryRunPanel.tsx
- [X] T046 [US4] Implement maker-checker approval flow: pending jobs appear as approval_request notifications in NotificationBadge, approval review page showing change payload and dry-run results side by side, approve/reject buttons with reason field per FR-020 in ops-portal/src/features/deploy/jobs/ApprovalFlow.tsx
- [X] T047 [US4] Implement deployment execution monitoring with ProgressTracker showing job status transitions (scheduled, running pre-checks, deploying device 1 of N, running post-checks, completed/failed/rolled_back), 5s active polling while job status is running in ops-portal/src/features/deploy/jobs/DeploymentProgress.tsx
- [X] T048 [US4] Implement job cancel and reschedule actions: cancel with ConfirmationDialog (click-only confirmation), reschedule with inline datetime/timezone editor, both updating job status immediately per US4-AS7 in ops-portal/src/features/deploy/jobs/JobActions.tsx

**Checkpoint**: Deployment scheduling with safety gates fully functional. Operators can schedule, dry-run, approve, monitor, and manage deployment jobs.

---

## Phase 7: User Story 5 — Audit Trail & Compliance Reporting (Priority: P2)

**Goal**: Operators search and filter audit records, view field-level change diffs, export filtered records to CSV/JSON, generate compliance evidence packs (SOX/PCI-DSS/SOC2), and explore incident-change correlations.

**Independent Test**: Query audit records with entity type, date range, and actor filters, verify results render within 5 seconds. Click a record to view full old-to-new diff via DiffViewer. Export filtered records as CSV and verify download link appears after progress completes. Generate a SOX compliance pack and verify progress tracking and download.

### Implementation for User Story 5

- [X] T049 [US5] Create audit query factory (auditQueries) with record list query, record detail query, export creation mutation, export status query, compliance pack mutation, pack status query, and correlation queries, plus Domain 4 types (AuditRecord, AuditExport, AuditFilters, IncidentCorrelation, CompliancePack) in ops-portal/src/api/audit.ts
- [X] T050 [US5] Create AuditListPage with filterable PaginatedTable (entity type, actor, date range, change type filters), columns for timestamp, actor, entity type, entity name, change type, and change summary, with row click navigating to AuditDetailPage per FR-022 in ops-portal/src/pages/audit/AuditListPage.tsx
- [X] T051 [US5] Create AuditDetailPage with full old-to-new field-level diff using DiffViewer (oldValues vs newValues), linked revision ID as clickable link to RevisionsPage, associated deployment job link to JobDetailPage, and audit metadata (timestamp, actor, entity) per FR-023 in ops-portal/src/pages/audit/AuditDetailPage.tsx
- [X] T052 [US5] Create AuditExportPage with current filter summary, format selector (CSV/JSON radio), "Export" button calling POST /audit/export, ProgressTracker showing generation progress with 5s polling, and download link on completion per FR-024 in ops-portal/src/pages/audit/AuditExportPage.tsx
- [X] T053 [US5] Create CompliancePage with framework selector (SOX, PCI-DSS, SOC2 dropdown), date range picker, "Generate Pack" button, ProgressTracker for generation progress, and download link for completed packs per FR-025 in ops-portal/src/pages/audit/CompliancePage.tsx
- [X] T054 [US5] Create CorrelationsPage with incident-change correlation list showing linked incident type badge (alarm/SLE degradation), correlated audit record summary, confidence score percentage, detection method, and clickable links to both the audit record detail and the incident source per FR-026 in ops-portal/src/pages/audit/CorrelationsPage.tsx
- [X] T055 [US5] Create AuditNav component with tab navigation connecting AuditListPage, AuditExportPage, CompliancePage, and CorrelationsPage with active tab state and route synchronization in ops-portal/src/features/audit/AuditNav.tsx

**Checkpoint**: Audit trail and compliance reporting fully functional. Operators can search, inspect, export, and generate compliance evidence.

---

## Phase 8: User Story 6 — Rollout Management (Priority: P3)

**Goal**: Operators create multi-wave rollout plans with golden image selection and health gate criteria, monitor wave-by-wave progress on a timeline visualization, and control promotion, pause, and rollback actions.

**Independent Test**: Create a multi-wave rollout with golden image, device assignment to 3 waves, and health gate criteria. Activate and verify timeline visualization shows per-wave progress bars with device counts. Simulate health gate failure to verify rollout pauses with alert banner. Test "Rollback Wave" action with ROLLBACK keyword confirmation.

### Implementation for User Story 6

- [X] T056 [US6] Extend deploy query factory with rollout list query, rollout detail query, rollout creation mutation, activate/pause/resume/rollback-wave mutations, golden image list query, and Domain 3 types (Rollout, RolloutStatus, RolloutWave, HealthGate, GoldenImage) in ops-portal/src/api/deploy.ts
- [X] T057 [US6] Create RolloutListPage with rollout plans list showing name, status badge (draft/active/paused/completed/cancelled), wave count, overall progress percentage, and creation date, with row links to RolloutDetailPage in ops-portal/src/pages/deploy/rollouts/RolloutListPage.tsx
- [X] T058 [US6] Create NewRolloutPage with wizard: name input, golden image selection from approved images list, device/site assignment to numbered waves via multi-select, health gate criteria (min client percentage, max alarm count, wait minutes between waves), and promotion mode toggle (automatic/manual) per FR-027 in ops-portal/src/pages/deploy/rollouts/NewRolloutPage.tsx
- [X] T059 [US6] Create RolloutDetailPage with timeline visualization showing each wave as a horizontal progress bar with completed/pending/failed device counts, health gate status badge (passed/pending/failed), elapsed time, health gate failure alert banner when rollout is paused due to failed health gate (per US6-AS5), auto-promotion event log, and 5s active polling while rollout is active per FR-028 in ops-portal/src/pages/deploy/rollouts/RolloutDetailPage.tsx
- [X] T060 [US6] Implement wave management controls: manual "Promote to Next Wave" button with ConfirmationDialog, visual health gate pass/fail indicators next to each wave bar, and auto-promotion mode status display per FR-029 in ops-portal/src/features/deploy/rollouts/WaveControls.tsx
- [X] T061 [US6] Implement rollout action buttons: "Activate" with ConfirmationDialog (click-only, transitions draft to active per US6-AS2), "Pause Rollout" and "Resume Rollout" with ConfirmationDialog (click-only), "Rollback Wave" with ConfirmationDialog requiring ROLLBACK keyword, and real-time rollback progress via ProgressTracker per FR-030 in ops-portal/src/features/deploy/rollouts/RolloutActions.tsx

**Checkpoint**: Rollout management with wave-by-wave control fully functional. Operators can orchestrate phased upgrades with health gates and safe rollback.

---

## Phase 9: User Story 7 — Drift Detection & Baseline Management (Priority: P3)

**Goal**: Operators view drift alerts with severity indicators, inspect field-level diffs between baselines and actual config, remediate unauthorized changes or accept intentional ones as new baselines, and manage golden configuration baselines.

**Independent Test**: View drift alerts list with severity badges. Click an alert to see baseline vs actual diff in DiffViewer. Remediate a drift with REMEDIATE keyword confirmation (verify remediation job is created). Accept a drift as new baseline (verify baseline updated and alert cleared). Create, edit, and delete a configuration baseline.

### Implementation for User Story 7

- [X] T062 [US7] Create DriftListPage with filterable PaginatedTable showing severity badge (low/medium/high/critical with color coding), entity name, drifted field count, detection timestamp, and acknowledgment status toggle, with row click navigating to DriftDetailPage per FR-031 in ops-portal/src/pages/drift/DriftListPage.tsx
- [X] T063 [US7] Create DriftDetailPage with side-by-side baseline vs actual configuration diff using DiffViewer ("Baseline" and "Current" labels), entity context (name, type, site), severity badge, detection timestamp, and action buttons (Remediate, Accept as New Baseline) per FR-032 in ops-portal/src/pages/drift/DriftDetailPage.tsx
- [X] T064 [US7] Implement "Remediate" action with ConfirmationDialog showing baseline configuration to be pushed, target device list, and REMEDIATE keyword requirement, calling POST /sync/drift/alerts/{id}/remediate and tracking remediation job progress via ProgressTracker per FR-033 in ops-portal/src/features/drift/DriftActions.tsx
- [X] T065 [US7] Implement "Accept as New Baseline" action with ConfirmationDialog explaining that the baseline will be updated to match current actual state, calling POST /sync/drift/alerts/{id}/accept, clearing the drift alert on success per FR-033 in ops-portal/src/features/drift/AcceptBaseline.tsx
- [X] T066 [US7] Create BaselinesPage with baseline list showing name, scope type (site/device group), scope name, created date, and last updated date, plus create (capture current live config), edit (rename, change scope), and delete (with ConfirmationDialog) actions per FR-034 in ops-portal/src/pages/config/BaselinesPage.tsx
- [X] T067 [US7] Implement drift alert acknowledgment toggle (acknowledge/unacknowledge) as inline action in DriftListPage rows, and add acknowledged/unacknowledged filter to DriftListPage filter bar in ops-portal/src/features/drift/AcknowledgeToggle.tsx

**Checkpoint**: Drift detection and baseline management fully functional. Operators can monitor, remediate, accept, and govern configuration drift.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Settings views, remaining management pages, accessibility hardening, client-side telemetry, responsive refinements, and container integration

- [X] T068 Create SettingsPage with notification channel management: list existing channels, create new channel (type, destination, alert subscriptions), edit channel, delete channel with ConfirmationDialog, and "Test" button to send test notification per FR-036 in ops-portal/src/pages/settings/SettingsPage.tsx
- [X] T069 [P] Create TemplatesPage with change template list showing name and description, create/edit forms with parameter definitions (name, label, type, required, options, default), and "Use Template" action that navigates to NewJobPage with pre-filled payload per FR-037 in ops-portal/src/pages/deploy/TemplatesPage.tsx
- [X] T070 [P] Create GoldenImagesPage with image repository list showing version, device type, compatible models, and status badge (pending/approved/retired), register new image form, and approve/retire lifecycle buttons per FR-038 in ops-portal/src/pages/deploy/GoldenImagesPage.tsx
- [X] T071 Implement client-side telemetry hook: capture unhandled JavaScript errors via window.onerror, failed API calls via ApiClient interceptor, and page load times via Performance API, reporting batched metrics to backend /api/v1/system/metrics endpoint per FR-043 in ops-portal/src/hooks/useTelemetry.ts
- [X] T072 [P] Add keyboard navigation and ARIA attributes across all shared components (DiffViewer, ConfirmationDialog, PaginatedTable, ProgressTracker), verify Tab ordering for all interactive elements, add aria-live regions for status updates, and enforce eslint-plugin-jsx-a11y rules per FR-042/SC-012 in ops-portal/src/components/
- [X] T073 Implement responsive layout adaptations: collapsed sidebar with icons only at 1024-1279px, hamburger menu at 768-1023px, DiffViewer auto-switch to stacked layout on narrow screens, PaginatedTable row-to-card conversion on tablet, and touch-friendly controls per FR-004 in ops-portal/src/pages/shell/RootLayout.tsx and ops-portal/src/components/DiffViewer.tsx
- [X] T074 [P] Verify CSP header enforcement end-to-end: confirm Nginx serves correct Content-Security-Policy header, validate production build contains no inline scripts or styles, audit all components for dangerouslySetInnerHTML usage (must be zero), and verify API-sourced string data uses text nodes only per FR-044 in ops-portal/nginx/default.conf
- [X] T075 Add portal service to compose.yml as ops-portal container alongside api, worker, db, redis, minio, vault services, with port 8080:80 mapping, depends_on api service, and network configuration for /api/ reverse proxy in compose.yml

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 Dashboard (Phase 3)**: Depends on Foundational — MVP, implement first
- **US2 Time-Travel (Phase 4)**: Depends on Foundational — can parallel with US1 (different pages/files)
- **US3 Config Versioning (Phase 5)**: Depends on configQueries from US2 (T030)
- **US4 Deploy Scheduling (Phase 6)**: Depends on deployQueries from US3 (T036)
- **US5 Audit Trail (Phase 7)**: Depends on Foundational only — can start after Phase 2, independent of other stories
- **US6 Rollouts (Phase 8)**: Depends on deploy.ts from US4 (T041) for extend pattern
- **US7 Drift Detection (Phase 9)**: Depends on sync.ts from US1 (T022) and config.ts from US2 (T030)
- **Polish (Phase 10)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Foundational only — start immediately after Phase 2
- **US2 (P1)**: Foundational only — can start parallel with US1 (both P1, different files)
- **US3 (P1)**: After US2 — needs configQueries (T030) for revision/diff queries
- **US4 (P2)**: After US3 — needs deploy.ts (T036) for job types and queries
- **US5 (P2)**: After Foundational — fully independent API group (audit), can parallel with any story
- **US6 (P3)**: After US4 — extends deploy.ts (T041) with rollout types
- **US7 (P3)**: After US1 + US2 — needs sync.ts (T022) for drift alerts and config.ts (T030) for baseline types

### Within Each User Story

- Query factory and types before page components
- Page components before feature components (pages compose features)
- List views before detail views
- Non-destructive views before destructive actions
- Core functionality before secondary features

### Parallel Opportunities

- **Phase 1**: All tasks T002-T008 marked [P] can run in parallel after T001
- **Phase 2**: All stores T011-T013 can run in parallel. All shared components T016-T019 can run in parallel. Layout T020-T021 can run in parallel after router T014-T015.
- **Phase 3 (US1)**: OrgDetailPage (T024) and SiteDetailPage (T025) can run in parallel. SyncStatusCard (T028) can run in parallel with page tasks.
- **Phase 4 (US2)**: TimelineScrubber (T032) and HistoricalStatePanel (T033) can run in parallel.
- **Phase 5 (US3)**: Entire phase is independent of US5 (audit) — can execute in parallel if staffed.
- **Phase 6 (US4)**: DryRunPanel (T045) can run in parallel with page implementations.
- **Phase 10**: TemplatesPage (T069), GoldenImagesPage (T070), accessibility audit (T072), and CSP verification (T074) can all run in parallel.

---

## Parallel Example: Phase 2 Foundational

```bash
# Step 1: Create ApiClient (blocking for all query usage)
Task T009: "Create ApiClient class in ops-portal/src/api/client.ts"

# Step 2: Launch all stores and connectivity hook in parallel
Task T010: "Create navigation store in ops-portal/src/hooks/useNavigationContext.ts"
Task T011: "Create session store in ops-portal/src/hooks/useSession.ts"
Task T012: "Create settings store in ops-portal/src/hooks/useSettings.ts"
Task T013: "Create connectivity hook in ops-portal/src/hooks/useConnectivity.ts"

# Step 3: Launch all shared components in parallel
Task T016: "Create DiffViewer in ops-portal/src/components/DiffViewer.tsx"
Task T017: "Create ConfirmationDialog in ops-portal/src/components/ConfirmationDialog.tsx"
Task T018: "Create PaginatedTable in ops-portal/src/components/PaginatedTable.tsx"
Task T019: "Create ProgressTracker in ops-portal/src/components/ProgressTracker.tsx"

# Step 4: Router and entry (after stores are ready)
Task T014: "Create router configuration in ops-portal/src/router.tsx"
Task T015: "Create app entry in ops-portal/src/main.tsx"

# Step 5: Layout and auth (after router + components)
Task T020: "Create RootLayout in ops-portal/src/pages/shell/RootLayout.tsx"
Task T021: "Create LoginPage in ops-portal/src/pages/shell/LoginPage.tsx"
```

---

## Parallel Example: User Story 1

```bash
# Step 1: Create query factory (blocking for all dashboard data)
Task T022: "Create syncQueries factory in ops-portal/src/api/sync.ts"

# Step 2: Launch dashboard page
Task T023: "Create DashboardPage in ops-portal/src/pages/dashboard/DashboardPage.tsx"

# Step 3: Launch detail pages in parallel
Task T024: "Create OrgDetailPage in ops-portal/src/pages/dashboard/OrgDetailPage.tsx"
Task T025: "Create SiteDetailPage in ops-portal/src/pages/dashboard/SiteDetailPage.tsx"

# Step 4: Device detail and feature components
Task T026: "Create DeviceDetailPage in ops-portal/src/pages/dashboard/DeviceDetailPage.tsx"
Task T027: "Create GlobalSearch in ops-portal/src/features/dashboard/GlobalSearch.tsx"
Task T028: "Create SyncStatusCard in ops-portal/src/features/dashboard/SyncStatusCard.tsx"
Task T029: "Create NotificationBadge in ops-portal/src/features/dashboard/NotificationBadge.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (project scaffold, tooling, container config)
2. Complete Phase 2: Foundational (API client, stores, router, shared components, layout, auth)
3. Complete Phase 3: User Story 1 (dashboard, navigation hierarchy, inventory, search, notifications)
4. **STOP and VALIDATE**: Log in, verify dashboard renders org data, drill down to device, test global search
5. Build and deploy container: `cd ops-portal && npm run build && podman build -t ops-portal .`

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 (Dashboard) → Test independently → Deploy (MVP: fleet health monitor!)
3. Add US2 (Time-Travel) → Test independently → Deploy (adds investigation capability)
4. Add US3 (Config Versioning) → Test independently → Deploy (adds configuration rollback)
5. Add US4 (Deploy Scheduling) → Test independently → Deploy (adds change management)
6. Add US5 (Audit Trail) → Test independently → Deploy (adds compliance evidence)
7. Add US6 (Rollouts) → Test independently → Deploy (adds phased upgrades)
8. Add US7 (Drift Detection) → Test independently → Deploy (adds configuration governance)
9. Polish → Accessibility, telemetry, responsive refinements → Final release

### Parallel Strategy

With multiple developers or agents:

1. Complete Setup + Foundational together
2. Once Foundational is done:
   - Agent A: US1 (Dashboard) → US3 (Config) → US6 (Rollouts)
   - Agent B: US2 (Time-Travel) → US4 (Deploy) → US7 (Drift)
   - Agent C: US5 (Audit) → Polish
3. Each track delivers independently testable increments

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable at its checkpoint
- Commit after each task or logical group of tasks
- Stop at any checkpoint to validate the story independently
- Five-Item Rule enforced: src/ has 5 children (api, components, features, hooks, pages), api/ has 5 files, hooks/ has 5 files, features/ has 5 subdirs
- All 45 FRs from spec.md are covered across the 75 tasks
- No test tasks generated (not requested); E2E scaffolding deferred to future iteration
