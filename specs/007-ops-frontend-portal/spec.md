# Feature Specification: Ops Frontend Portal

**Feature Branch**: `007-ops-frontend-portal`  
**Created**: 2026-03-06  
**Status**: Draft  
**Input**: User description: "Add the frontend web portal layer to the Mist Ops Platform. The platform was designed as a 3-layer architecture (frontend, application, backend) per FR-022/SC-008, but the implementation completed only the application and backend layers. The frontend portal must consume the existing REST API (~46 endpoints under /api/v1/) and provide an operator-facing web dashboard for all 6 user stories: time-travel investigation, config versioning/diff/rollback, scheduled deployments, audit trail, phased rollouts, and drift detection."

## Clarifications

### Session 2026-03-06

- Q: How should the frontend container serve the portal (static assets, SSR, or BFF pattern)? → A: Static asset server with reverse proxy — serve pre-built files, proxy /api/ requests to the application layer. No Node.js runtime needed in production.
- Q: What level of frontend observability should the portal provide? → A: Lightweight client-side telemetry (JS errors, API call failures, page load times) reported to existing backend metrics/logging. Future: upgrade to full observability stack (session replay, performance tracing) via dedicated frontend monitoring service.
- Q: Should the portal enforce strict Content Security Policy headers and sanitize all rendered configuration data? → A: Yes — strict CSP headers (no inline scripts/styles) plus sanitize all API-sourced data before rendering.
- Q: How should the portal display and handle timestamps? → A: Display in operator's local browser timezone by default, with a per-view toggle to switch to UTC or site timezone. Scheduled deployments require explicit timezone selection.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Operational Dashboard & Navigation (Priority: P1)

A NOC engineer logs into the Mist Ops Platform portal and lands on a dashboard that shows the health of all managed organizations at a glance. They see organization cards displaying sync status, device counts, active alerts (drift, deployment failures), and recent changes. The engineer clicks into an organization to see its sites, then drills into a specific site to see devices grouped by type (APs, switches, gateways) with connection status indicators. From any point in the navigation hierarchy, they can jump to time-travel, audit, deployment, or drift views scoped to the selected entity.

**Why this priority**: The dashboard is the primary entry point for every operator session. Without a navigable overview, operators cannot discover which organizations, sites, or devices need attention — making all other features unreachable. This is the shell that hosts every other user story.

**Independent Test**: Can be fully tested by logging in, verifying the dashboard renders organization summaries from the inventory API, drilling into an org/site/device, and confirming navigation links route to the correct views. Delivers immediate value as a real-time fleet health monitor.

**Acceptance Scenarios**:

1. **Given** the operator has valid credentials, **When** they log in, **Then** the portal displays a dashboard with cards for each managed organization showing name, site count, device count, sync state, and active alert count.
2. **Given** the dashboard is displayed, **When** the operator clicks an organization card, **Then** the portal navigates to a site list view filtered to that organization, showing each site's name, location, device count, and health indicators.
3. **Given** the operator is viewing a site, **When** they select a device, **Then** the portal displays the device detail view including model, serial, firmware version, connection status, uptime, and contextual links to time-travel, revisions, drift alerts, and audit records for that device.
4. **Given** the operator is anywhere in the application, **When** they use the global navigation, **Then** they can access Dashboard, Time-Travel, Config, Deployments, Audit, Drift, and Settings views without losing their current organization/site context.
5. **Given** the operator's session token expires or becomes invalid, **When** they perform any action, **Then** the portal redirects to the login page with a clear "session expired" message and preserves the URL so they return to the same view after re-authenticating.

---

### User Story 2 — Time-Travel Investigation (Priority: P1)

A NOC engineer receives a complaint that a branch office experienced intermittent connectivity yesterday afternoon. They navigate to the affected device (from the dashboard or via search), open the time-travel view, and use a timeline scrubber or date/time picker to select the timestamp in question. The portal displays the device's configuration, port up/down states, connected client count, and health metrics as they were at that exact moment. The engineer clicks "Compare with Current" to see a side-by-side diff of what changed between then and now. They identify that a radio power setting was modified after the outage window, confirming a misconfiguration rather than hardware failure.

**Why this priority**: Time-travel investigation is the #1 feature gap identified in the competitive analysis and the primary reason the platform exists. The backend already provides the `/api/v1/config/time-travel` endpoint (SC-001: <5s response); the frontend must make this capability accessible and intuitive so that 90% of operators complete an investigation in under 5 minutes (SC-011).

**Independent Test**: Can be tested by navigating to any synced device, selecting a past timestamp, verifying the portal renders historical config/status/health data, then comparing that snapshot against the current state. Delivers immediate value as a standalone "network forensics" tool.

**Acceptance Scenarios**:

1. **Given** the operator has selected a device that has been synced for at least 24 hours, **When** they open the time-travel view and select a past timestamp, **Then** the portal displays the device's configuration, port states, connected client count, and health metrics as they were at that moment, with the queried timestamp and actual data timestamp both visible.
2. **Given** the time-travel view is showing a historical snapshot, **When** the operator clicks "Compare with Current," **Then** the portal displays a side-by-side field-level diff showing exactly which settings differ between the historical state and the current state.
3. **Given** the operator queries a timestamp older than the retention window, **When** the query returns no data, **Then** the portal displays a clear message stating the data has been aged out and shows the oldest available timestamp as a clickable link.
4. **Given** the operator is in the time-travel view, **When** they adjust the timeline scrubber forward or backward, **Then** the portal updates the displayed state to reflect the new timestamp without requiring a full page reload.

---

### User Story 3 — Configuration Versioning, Diff & Restore (Priority: P1)

A network administrator notices degraded Wi-Fi performance after a recent WLAN policy change. They navigate to the affected site's configuration revision history and see a chronological list of all captured config snapshots with timestamps, actors, and change summaries. They select the two most recent revisions and click "Compare." The portal renders a structured diff view showing old values and new values for each changed field, color-coded (removed in red, added in green, modified in amber). Confirming that the recent SSID rename caused the issue, the administrator clicks "Install from Revision" on the known-good revision, reviews the confirmation dialog (which shows how many devices will be affected and the risk assessment), types the confirmation keyword, and the portal queues the restore job — showing real-time progress as each device receives the restored configuration.

**Why this priority**: Config versioning and rollback are the second-most-cited missing capability. The backend provides revision listing, diff computation, and install-from-revision endpoints; the frontend must present these as a seamless, mistake-proof workflow with clear confirmation gates for the destructive restore operation.

**Independent Test**: Can be tested by viewing revision history for an entity with multiple revisions, computing a diff between two revisions, verifying the diff renders correctly, then initiating an install-from-revision and confirming the job is queued and trackable. Delivers immediate value as a visual "undo button."

**Acceptance Scenarios**:

1. **Given** the operator navigates to a device or site, **When** they open the revision history tab, **Then** the portal displays a paginated, chronological list of configuration revisions showing revision ID, timestamp, actor, and source (sync, manual push, restore).
2. **Given** revision history is displayed, **When** the operator selects two revisions and clicks "Compare," **Then** the portal renders a field-level diff with old/new values color-coded (red for removed, green for added, amber for changed), with a summary count of fields changed, added, and removed.
3. **Given** the operator clicks "Install from Revision" on a prior revision, **When** the confirmation dialog appears, **Then** it displays the number of target devices, the revision timestamp, a risk assessment (blast radius), and requires the operator to type a confirmation keyword before proceeding.
4. **Given** the install-from-revision job is submitted, **When** the job is running, **Then** the portal shows real-time status updates (pending, pushing to device 1 of N, completed/failed) without requiring manual page refresh.
5. **Given** the install-from-revision job fails for one or more devices, **When** the failure occurs, **Then** the portal displays which devices failed, the error reason, and offers a "Retry Failed" option.

---

### User Story 4 — Deployment Scheduling & Approval (Priority: P2)

A change manager needs to deploy a firewall policy update across 15 devices during a 2 AM maintenance window. During business hours, they navigate to the Deployments view, click "New Deployment," select the target devices (by searching or browsing the org/site/device hierarchy), paste or author the configuration change payload, set the scheduled date/time, configure pre-checks (device reachability) and post-checks (client count threshold), enable auto-rollback on failure, and submit the job. Before submission, they run a dry-run to see the risk assessment and blast radius. The portal identifies this as a high-impact change requiring maker-checker approval and routes it to a senior engineer, who sees the pending approval in their notification badge, reviews the dry-run results and change payload, and clicks "Approve." At 2 AM, the job executes automatically. The change manager checks the portal the next morning and sees the job completed successfully with all pre/post-checks passed.

**Why this priority**: Scheduled deployments with safety gates are a core operational workflow for regulated enterprises. This user story maps to the Deploy API (jobs, dry-run, approval) and is P2 because it depends on the dashboard navigation (P1) being in place to select target entities.

**Independent Test**: Can be tested by creating a scheduled job, running a dry-run, submitting for approval (if required), verifying the job appears in the pending jobs list, and monitoring execution status after the scheduled time. Delivers value as a self-service deployment scheduler with built-in safety.

**Acceptance Scenarios**:

1. **Given** the operator opens the "New Deployment" wizard, **When** they select target devices, enter a change payload, set a future schedule time, and configure pre/post-checks, **Then** the portal validates the input and enables the "Submit" button.
2. **Given** the operator clicks "Dry Run" before submitting, **When** the dry-run executes, **Then** the portal displays the risk score (low/medium/high), blast radius (devices, sites, estimated clients affected), warnings, and any policy violations — all within 10 seconds (SC-013).
3. **Given** the change requires maker-checker approval (different user must approve), **When** the job is submitted, **Then** the portal shows "Pending Approval" status and the approver sees a badge notification with the pending job details.
4. **Given** a pending job exists, **When** the approver reviews and approves it, **Then** the portal updates the job status to "Approved — Scheduled" and the author receives a notification.
5. **Given** a scheduled job is executing, **When** pre-checks fail, **Then** the portal shows the job as "Aborted — Pre-check Failed" with the specific failure reason visible.
6. **Given** a scheduled job deployed successfully but post-checks fail and auto-rollback is enabled, **When** the rollback executes, **Then** the portal shows "Rolled Back" status with a link to the rollback details.
7. **Given** the operator wants to cancel or reschedule a pending job, **When** they edit the job before its scheduled time, **Then** the portal updates the schedule or cancels the job and reflects the new status immediately.

---

### User Story 5 — Audit Trail & Compliance Reporting (Priority: P2)

An auditor requests evidence of all WLAN configuration changes made in Q1. The operator opens the Audit view, sets the entity type filter to "WLAN," selects the date range (January 1 to March 31), and optionally filters by actor. The portal displays a paginated table of change records, each row showing timestamp, actor, entity name, change type, and a summary of what changed. The operator clicks a record to see the full old-to-new field-level diff. They then click "Export" and select CSV format. The portal shows a progress indicator while the export generates, then offers a download link. For a SOX audit, the operator navigates to the Compliance Packs section, selects the SOX framework and date range, and generates a complete evidence package.

**Why this priority**: Change audit trails with field-level diffs are table-stakes for SOX/PCI/SOC2 compliance. This user story maps to the Audit API (records, export, compliance packs, correlations). P2 because it provides read-only historical analysis rather than active operational intervention.

**Independent Test**: Can be tested by querying audit records with various filter combinations, verifying records display correct old/new values, exporting to CSV, and generating a compliance pack. Delivers value as a standalone compliance evidence tool.

**Acceptance Scenarios**:

1. **Given** the operator opens the Audit view, **When** they apply filters (entity type, date range, actor), **Then** the portal displays a paginated table of matching audit records with timestamp, actor, entity name, change type, and change summary, returning results in under 5 seconds (SC-006).
2. **Given** the operator clicks an audit record row, **When** the detail view opens, **Then** the portal displays the full old-to-new field-level diff for that change, including the revision ID and any associated deployment job.
3. **Given** the operator clicks "Export," **When** they select a format (CSV) and the export begins, **Then** the portal shows a progress indicator and provides a download link when complete, finishing in under 30 seconds for 12 months of data (SC-012).
4. **Given** the operator views an incident-change correlation, **When** they click a correlated change, **Then** the portal navigates to the audit record detail showing the linked incident (alarm/SLE degradation) and confidence score.
5. **Given** the operator generates a compliance audit pack, **When** they select a framework (SOX, PCI-DSS, SOC2) and date range, **Then** the portal produces a downloadable evidence package and shows generation progress.

---

### User Story 6 — Rollout Management (Priority: P3)

A firmware upgrade needs to be deployed to 200 APs across 40 sites. The operator opens the Rollouts view, clicks "New Rollout," names the plan, selects the firmware version from the approved golden images list, and divides sites into three waves (pilot, regional, remaining) using drag-and-drop or multi-select assignment. They set health gate criteria (minimum client count percentage, maximum alarm count, wait time between waves) and choose automatic promotion mode. After reviewing and activating the plan, the portal shows a rollout timeline visualization with each wave as a horizontal bar showing progress percentage, device counts, and health gate status. Wave 1 completes and passes health gates — the portal auto-advances to Wave 2. If Wave 2 shows degraded health, the portal pauses with a clear alert and offers "Rollback Wave 2" and "Resume" options.

**Why this priority**: Phased rollouts limit blast radius for fleet-wide changes. P3 because it builds on top of the scheduling (P2) and versioning (P1) capabilities and is used less frequently than daily operations.

**Independent Test**: Can be tested by creating a multi-wave rollout plan, activating it, monitoring wave progression, simulating a health gate failure to verify pause behavior, and rolling back a wave. Delivers value as a visual firmware upgrade orchestrator.

**Acceptance Scenarios**:

1. **Given** the operator opens "New Rollout," **When** they assign devices/sites to waves, set health gate criteria, and select a golden image, **Then** the portal creates a rollout plan in "draft" status showing total targets per wave.
2. **Given** a rollout plan is in "draft," **When** the operator clicks "Activate," **Then** the portal prompts for confirmation and transitions the plan to "active," beginning Wave 1 execution.
3. **Given** a rollout is active, **When** the operator views the rollout detail, **Then** the portal displays a timeline visualization with each wave showing progress percentage, completed/pending/failed device counts, and health gate status (passed/pending/failed).
4. **Given** Wave 1 completes and health gates pass in auto-promotion mode, **When** the wait period expires, **Then** the portal automatically shows Wave 2 as "in progress" with an auto-promotion event in the activity log.
5. **Given** a wave fails health gate criteria, **When** the degradation is detected, **Then** the portal pauses the rollout, shows a prominent alert banner, and offers "Rollback Wave" and "Resume" action buttons.
6. **Given** the operator clicks "Rollback Wave," **When** the rollback executes, **Then** the portal displays confirmation dialog, rolls back devices in that wave, and shows rollback progress in real time.

---

### User Story 7 — Drift Detection & Baseline Management (Priority: P3)

A senior engineer defines a "golden" configuration baseline for all AP devices at a regional office. Days later, a field technician manually changes a radio power setting on one device via the Mist portal. Within two sync cycles (~10 minutes), the Mist Ops Platform detects the drift. The senior engineer opens the Drift view and sees a list of active drift alerts with severity badges. They click the alert to see the full field-level diff between the baseline and actual state. They decide this particular change was intentional and click "Accept as New Baseline" to update the golden config. For another drift alert where a VLAN was accidentally removed, they click "Remediate" — the portal confirms the action, pushes the intended configuration back, and clears the drift alert.

**Why this priority**: Drift detection closes the configuration governance loop. P3 because it depends on the config versioning infrastructure (P1) and the remediation push mechanisms (P2).

**Independent Test**: Can be tested by creating a baseline, viewing drift alerts, inspecting a full diff, remediating a drift (verifying the push job is created), and accepting a drift as the new baseline. Delivers value as a continuous compliance monitor.

**Acceptance Scenarios**:

1. **Given** the operator opens the Drift view, **When** drift alerts exist, **Then** the portal displays a list of active alerts with severity badge (low/medium/high/critical), entity name, drift summary (number of changed fields), and detection timestamp.
2. **Given** the operator clicks a drift alert, **When** the detail view opens, **Then** the portal shows the baseline configuration alongside the actual configuration in a side-by-side diff with changed fields highlighted.
3. **Given** the operator clicks "Remediate," **When** the confirmation dialog appears, **Then** it shows the baseline that will be pushed, the target device(s), and requires confirmation before creating a remediation job.
4. **Given** the operator clicks "Accept as New Baseline," **When** confirmed, **Then** the portal updates the baseline to match the current actual state and clears the drift alert.
5. **Given** the operator navigates to Baseline Management, **When** they create or edit a baseline, **Then** the portal allows selecting an entity scope (site, device group), capturing the current live config as the baseline content, and saving it.

---

### Edge Cases

- What happens when the operator's network connection drops while viewing real-time deployment progress? The portal detects the disconnection, displays a "Connection Lost — Reconnecting" banner, and resumes polling or re-establishes the real-time connection when the network recovers. No data is lost; the view refreshes to current state on reconnection.
- What happens when two operators simultaneously approve and cancel the same pending job? The portal uses optimistic concurrency — the first action succeeds, and the second operator receives a "Job status already changed" error with the new status displayed.
- What happens when the operator navigates to a device that was deleted from Mist between page loads? The portal shows a "Device Not Found" state with the last known details (name, serial) and a timestamp indicating when it was last seen.
- What happens when an audit export or compliance pack takes longer than expected? The portal shows a progress indicator with elapsed time and allows the operator to navigate away — the export continues in the background and a notification appears when the download is ready.
- What happens when the API returns paginated results exceeding display limits? The portal uses progressive loading with pagination controls and never attempts to load all pages at once, preventing browser memory exhaustion.
- What happens when the portal is accessed on a small screen (tablet or narrow window)? The layout adapts responsively — navigation collapses to a sidebar menu, tables switch to card views, and diff views stack vertically instead of side-by-side.

## Requirements *(mandatory)*

### Functional Requirements

#### Navigation & Layout

- **FR-001**: Portal MUST provide a persistent navigation structure with access to all primary views (Dashboard, Time-Travel, Config, Deployments, Audit, Drift, Settings) from any page, preserving the operator's current organization and site context during navigation.
- **FR-002**: Portal MUST implement a hierarchical drill-down from MSP level to Organization to Site to Device, reflecting the Mist management hierarchy.
- **FR-003**: Portal MUST provide a global search that finds organizations, sites, and devices by name, serial number, MAC address, or IP address, with results linking directly to the matching entity's detail view.
- **FR-004**: Portal MUST adapt its layout for screens from 1024px width (standard laptop) to 2560px (ultra-wide monitor), with table views, diff views, and navigation adjusting to the available space.

#### Authentication & Session Management

- **FR-005**: Portal MUST support the three authentication methods already defined by the application layer: API token entry, interactive login (email/password with optional 2FA code), and Mist SSO redirect.
- **FR-006**: Portal MUST display the authenticated operator's identity, role scope (MSP/org-level), and managed organizations after login, restricting all views to resources within the operator's Mist-assigned permissions.
- **FR-007**: Portal MUST detect expired or invalid sessions and redirect the operator to the login page with a clear "session expired" message, preserving the current URL for post-login redirect.

#### Dashboard & Inventory

- **FR-008**: Portal MUST display organization summary cards on the main dashboard showing name, site count, device count, sync state (synced/stale/error), and active alert count, sourced from the inventory and drift alert endpoints.
- **FR-009**: Portal MUST provide device inventory views filterable by organization, site, device type (AP/switch/gateway), model, firmware version, and connection status with paginated results.
- **FR-010**: Portal MUST show sync status for each organization including last sync time, next scheduled poll, and per-entity-type sync counts (total, synced, stale, error).

#### Time-Travel

- **FR-011**: Portal MUST render a time-travel investigation view where the operator selects a device and a past timestamp (via date/time picker or timeline scrubber) and the view displays the device's historical configuration, port states, client count, and health metrics at that moment.
- **FR-012**: Portal MUST provide a "Compare with Current" action from the time-travel view that generates a side-by-side diff between the historical snapshot and the current live state.
- **FR-013**: Portal MUST display a clear, actionable message when queried data falls outside the retention window, including the oldest available timestamp as a clickable shortcut.

#### Configuration Versioning & Diff

- **FR-014**: Portal MUST display a paginated revision history for any entity (device, site, WLAN, policy) showing revision ID, captured timestamp, actor, source, and content hash.
- **FR-015**: Portal MUST render field-level configuration diffs between any two selected revisions with color-coded indicators (red for removed fields, green for added fields, amber for changed values) and a change summary (fields changed, added, removed).
- **FR-016**: Portal MUST provide an "Install from Revision" action that shows a confirmation dialog displaying the target device count, risk assessment (from dry-run), and revision details, and requires the operator to type a confirmation keyword before execution.
- **FR-017**: Portal MUST display real-time progress for install-from-revision jobs showing per-device checkpoint status (pending, pushing, completed, failed) without requiring manual page refresh.

#### Deployment & Scheduling

- **FR-018**: Portal MUST provide a deployment creation workflow that walks the operator through: selecting target entities, entering/uploading a change payload, setting the schedule time, configuring pre/post-checks, and enabling auto-rollback.
- **FR-019**: Portal MUST provide a dry-run action before deployment submission that displays the risk score, risk level, blast radius, warnings, and policy violations within the view.
- **FR-020**: Portal MUST display pending jobs that require maker-checker approval with a visual badge in the operator's notification area, linking to the job detail where the approver can review and approve/reject.
- **FR-021**: Portal MUST display a deployment jobs list filterable by status (pending, running, completed, failed, cancelled), date range, and creator, with each job row linking to a detail view showing checkpoints, pre/post-check results, and rollback status.

#### Audit & Compliance

- **FR-022**: Portal MUST display audit trail records in a filterable, paginated table with columns for timestamp, actor, entity type, entity name, change type, and change summary.
- **FR-023**: Portal MUST provide audit record detail views showing the full old-to-new field-level diff, linked revision ID, and associated deployment job (if any).
- **FR-024**: Portal MUST provide an audit export workflow where the operator selects filters and output format, initiates the export, sees generation progress, and downloads the resulting file.
- **FR-025**: Portal MUST provide a compliance pack generation workflow where the operator selects a compliance framework (SOX, PCI-DSS, SOC2), date range, and format, then monitors generation and downloads the package.
- **FR-026**: Portal MUST display incident-change correlations showing the linked incident (alarm or SLE degradation), the correlated configuration change, confidence score, and detection method, with clickable links to both the incident and the audit record.

#### Rollouts

- **FR-027**: Portal MUST provide a rollout creation workflow where the operator names the plan, selects a golden image or change payload, assigns devices/sites to numbered waves, sets health gate criteria, and chooses promotion mode (automatic or manual).
- **FR-028**: Portal MUST render a rollout timeline visualization showing each wave as a progress bar with device counts (completed, pending, failed), health gate status, and elapsed time.
- **FR-029**: Portal MUST support manual wave promotion (with confirmation dialog) and automatic promotion (with visual indicators of health gate pass/fail).
- **FR-030**: Portal MUST provide "Pause Rollout," "Resume Rollout," and "Rollback Wave" actions with appropriate confirmation dialogs for destructive operations.

#### Drift Detection & Baselines

- **FR-031**: Portal MUST display drift alerts in a filterable list showing severity badge, entity name, drift field count, detection timestamp, and acknowledgment status.
- **FR-032**: Portal MUST render drift alert details as a side-by-side diff between the baseline (intended) configuration and the actual (current) configuration.
- **FR-033**: Portal MUST provide "Remediate" and "Accept as New Baseline" actions on drift alerts, each with a confirmation dialog explaining the consequences.
- **FR-034**: Portal MUST provide a baseline management view where operators can create, view, edit, and delete configuration baselines scoped to sites or device groups.

#### Notifications & Settings

- **FR-035**: Portal MUST display a notification indicator (badge with count) in the global navigation showing unread notifications (pending approvals, drift alerts, deployment failures, export completions), with a dropdown listing recent notifications linking to the relevant view.
- **FR-036**: Portal MUST provide a settings view for managing notification channels (create, edit, delete, test) with fields for channel type, destination, and alert type subscriptions.
- **FR-037**: Portal MUST provide a change templates management view where operators can browse, create, edit, and instantiate reusable change templates.
- **FR-038**: Portal MUST provide a golden images management view where operators can view the image repository, register new images, and initiate the approval/retirement lifecycle.

#### Cross-Cutting Concerns

- **FR-039**: Portal MUST handle all destructive operations (install-from-revision, remediation push, rollback, firmware upgrade) with explicit confirmation dialogs that describe the action's impact and require deliberate user action before proceeding.
- **FR-040**: Portal MUST display meaningful error messages when API calls fail, including the error code, a human-readable message, and suggested next actions — never exposing raw stack traces or internal error details.
- **FR-041**: Portal MUST detect loss of connectivity to the application layer and display a non-blocking "Connection Lost — Reconnecting" banner, automatically resuming when connectivity is restored.
- **FR-042**: Portal MUST support keyboard navigation and meet WCAG 2.1 Level AA accessibility standards for all interactive elements.
- **FR-043**: Portal MUST capture client-side errors (JavaScript exceptions, failed API calls) and core performance metrics (page load times, API response times) and report them to the application layer's existing logging and metrics infrastructure. Full observability (session replay, performance tracing via dedicated monitoring service) is deferred to a future iteration.
- **FR-044**: Portal MUST enforce strict Content Security Policy headers (no inline scripts, no inline styles) and sanitize all data received from the API before rendering, preventing cross-site scripting via injected configuration values (SSIDs, hostnames, descriptions).
- **FR-045**: Portal MUST display all timestamps in the operator's local browser timezone by default, with a per-view toggle to switch between local, UTC, and site-configured timezone. The deployment scheduling workflow MUST require the operator to explicitly select the timezone for the scheduled execution time.

### Key Entities

- **View / Page**: A distinct screen in the portal mapped to a primary capability. Key attributes: route path, required permission scope, parent view (for breadcrumbs), data source endpoints. Examples: Dashboard, Time-Travel, Revision History, Deployment Detail, Audit Table, Drift Alerts, Rollout Timeline.
- **Navigation Context**: The currently selected scope that persists across view transitions. Key attributes: selected MSP, selected organization, selected site, selected device. Determines which API calls are made and what data is displayed.
- **Diff Visualization**: A rendered comparison between two configuration states. Key attributes: left revision (old), right revision (new), change list (path, old value, new value, change type), summary counts. Used in time-travel compare, revision diff, drift detail, and audit record detail.
- **Confirmation Dialog**: A safety gate presented before any destructive operation. Key attributes: action description, impact summary (device count, blast radius), confirmation keyword requirement, cancel option. Enforces explicit operator intent before irreversible actions.
- **Notification Item**: An in-portal alert for operator attention. Key attributes: notification type (approval request, drift alert, deployment status, export ready), severity, timestamp, read/unread status, link to relevant view.
- **Dashboard Widget**: A summary card or indicator on the main dashboard. Key attributes: data source endpoint, refresh interval, entity scope (org/site), metric type (count, status, alert count).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 90% of operators complete a "rewind and inspect" time-travel investigation in under 5 minutes on their first attempt using the portal (aligns with backend SC-011).
- **SC-002**: The portal loads and renders the main dashboard within 3 seconds on a standard broadband connection (10 Mbps+) for an operator managing up to 100 organizations.
- **SC-003**: Configuration diff views render in under 3 seconds for configurations up to 50 KB, matching the backend diff computation performance (aligns with backend SC-003).
- **SC-004**: The deployment creation workflow (target selection, payload entry, schedule, pre/post-checks, submission) can be completed in 10 or fewer user interactions.
- **SC-005**: Audit trail search results appear within 5 seconds of applying filters, consistent with the backend query performance (aligns with backend SC-006).
- **SC-006**: Change templates can be instantiated and applied to a target site in under 3 user actions (select template, fill parameters, confirm) — matching backend SC-014.
- **SC-007**: Deployment dry-run results (risk score, blast radius, warnings) display within 10 seconds of clicking "Dry Run," matching backend SC-013.
- **SC-008**: The portal functions correctly on the two most recent stable versions of major desktop browsers without requiring plugins or extensions.
- **SC-009**: All destructive operations require a minimum of 2 deliberate user actions (click button + confirm dialog) before execution, with zero "one-click destructive" paths.
- **SC-010**: The portal scales to support at least 50 concurrent operator sessions without performance degradation, independently of the application layer's scaling (aligns with backend FR-022 / SC-008 on independent layer scaling).
- **SC-011**: Portal navigation between any two primary views completes in under 1 second (client-side routing, no full page reloads).
- **SC-012**: The portal meets WCAG 2.1 Level AA compliance for all primary workflows (dashboard, time-travel, config diff, deployment creation, audit search).

## Assumptions

- The application layer's REST API (~46 endpoints under `/api/v1/`) is fully implemented and stable. The portal consumes these endpoints as documented in the API contracts and does not require any new backend endpoints.
- Authentication and authorization are handled by the application layer. The portal delegates login to the `/api/v1/auth/login` endpoint and uses the returned session/token for subsequent requests. The portal does not maintain its own user database.
- The portal is deployed as a separate container (the "frontend layer" from FR-022) that serves pre-built static assets via a lightweight web server, with API requests reverse-proxied to the application layer. No server-side rendering runtime is required in production. This separation enables independent scaling per SC-008.
- Real-time updates (deployment progress, drift alerts, sync status) use periodic polling against the existing REST API rather than requiring new WebSocket or server-sent event infrastructure. Polling intervals are configurable (default: 5 seconds for active operations, 30 seconds for passive monitoring).
- The portal targets desktop browser usage by NOC engineers on standard workstations. Tablet support is a secondary consideration; mobile phone support is not required.
- Operators are NOC engineers with network operations experience. The portal prioritizes operational clarity and safety (confirmation dialogs, risk assessments, color-coded diffs) over minimizing click counts.
- The existing MistHelper Flask-based web portal (`--web-portal` on port 8055) provides design precedent for the project's web UI patterns. The new portal is a separate application purpose-built for the Mist Ops Platform, not an extension of the MistHelper portal.
