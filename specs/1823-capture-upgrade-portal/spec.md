# Feature Specification: Pre-Upgrade/Post-Upgrade Capture Portal

**Feature Branch**: `feat/1823-capture-upgrade-portal`

**Created**: 2026-09-04

**Status**: Specified

**Input**: Customer needs a pre-check and post-check tool before/after code upgrade with side-by-side comparison of captures.

## User Scenarios & Testing

### User Story 1 - Authenticate and Select Organization (Priority: P1)

Network administrator accesses the capture portal web interface. The system prompts for credentials (either Mist API token via environment, or MSP email/password login). For MSP users, the system presents a searchable organization list; for single-token users, the organization is auto-selected.

**Why this priority**: This is the foundational entry point. No further action is possible without authentication and org selection. Users cannot proceed to capture without this working.

**Independent Test**: Can be tested by launching the web server and verifying the login flow works independently of the upgrade process.

**Acceptance Scenarios**:

1. **Given** user is unauthenticated, **When** they navigate to the portal, **Then** they see the credential prompt (token input or email/password fields)
2. **Given** user provides a valid Mist API token, **When** they submit credentials, **Then** the system authenticates and displays the portal with auto-selected organization
3. **Given** user is MSP admin with email/password, **When** they submit credentials, **Then** the system displays a searchable organization selection list
4. **Given** user selects an organization, **When** they confirm, **Then** the portal loads showing site selection screen

---

### User Story 2 - Select Site and Device Types (Priority: P1)

Administrator selects a target site from a searchable list. The system displays available device types (AP, gateway, switch) as radio button options. User selects which device type(s) to capture in the pre-upgrade snapshot.

**Why this priority**: Site and device type selection directly determines the scope of the capture. Without this, the capture cannot be properly bounded and cannot meet customer needs.

**Independent Test**: Can be tested by mocking organization/site data and verifying UI selection and filtering logic works independently of actual API calls.

**Acceptance Scenarios**:

1. **Given** user is authenticated in an organization, **When** they view the site selection screen, **Then** they see a searchable list of sites with organization context
2. **Given** user searches for a site by name, **When** they type a partial name, **Then** the list filters in real-time to matching sites
3. **Given** user selects a site, **When** they confirm, **Then** the portal displays device type selection (checkboxes for AP, Gateway, Switch)
4. **Given** user selects device types (e.g., "AP" and "Gateway"), **When** they confirm, **Then** the selection is captured for the pre-upgrade capture step

---

### User Story 3 - Configure Bulk Upgrade Options (Priority: P1)

Administrator selects bulk firmware upgrade strategy via radio buttons: (1) standard upgrade, (2) staged upgrade, or (3) skip capture and use previous results. The choice determines upgrade behavior after pre-capture.

**Why this priority**: Upgrade strategy directly impacts the upgrade execution flow and risk profile. This is essential configuration before the upgrade runs.

**Independent Test**: Can be tested by verifying the UI accepts radio button selections and passes them through to the upgrade execution path.

**Acceptance Scenarios**:

1. **Given** user has selected a site and device types, **When** they view the upgrade options screen, **Then** they see three radio button options: (a) standard, (b) staged, (c) reuse
2. **Given** user selects "standard upgrade", **When** they confirm, **Then** the system plans to execute standard bulk firmware upgrade
3. **Given** user selects "staged upgrade", **When** they confirm, **Then** the system plans to execute staged upgrade with device grouping
4. **Given** user selects "reuse previous captures", **When** they confirm, **Then** the system skips the upgrade and uses cached capture data for comparison

---

### User Story 4 - Pre-Upgrade Capture with Data Persistence (Priority: P1)

System captures network state before upgrade: code versions, device status (connected/disconnected/upgrading), firmware versions, client counts per device, switch port statistics. Data is displayed in interactive tables with sorting and pagination. User can download as CSV. Data is persisted to ArangoDB (primary), Redis (alongside), and CSV (backup). User must confirm data looks correct before proceeding.

**Why this priority**: Pre-upgrade capture is the baseline measurement. Without accurate, persisted data, comparison and troubleshooting are impossible. This is the core value proposition of the feature.

**Independent Test**: Can be tested independently by capturing against a test site and verifying table display, CSV export, and multi-backend persistence work without needing the upgrade to complete.

**Acceptance Scenarios**:

1. **Given** user has configured upgrade options, **When** they click "Begin Capture", **Then** the system fetches device list, client counts, and firmware data for the selected site/device types
2. **Given** capture data is retrieved, **When** it is displayed, **Then** tables show: device name, model, firmware version, status, client count, uptime, and carrier/SSR-specific fields
3. **Given** user reviews the table, **When** they sort by any column (e.g., client count), **Then** the table re-sorts and reflects the selected column order
4. **Given** tables are populated, **When** user clicks "Download CSV", **Then** the browser downloads a CSV file with all captured data
5. **Given** user has reviewed and confirmed the pre-capture data, **When** they click "I Confirm - Proceed to Upgrade", **Then** the system saves data to ArangoDB and Redis, and logs the capture timestamp
6. **Given** data is saved, **When** the system writes CSV as backup, **Then** the CSV file is created in the data directory with timestamp and site name

---

### User Story 5 - Execute Upgrade with Status Monitoring (Priority: P1)

System initiates upgrade according to selected strategy. Portal displays real-time upgrade progress with device-by-device status updates. System polls device events every 20 seconds to detect connection changes and firmware version changes. Status screen updates every 30 seconds. User sees: device name, current status (connected/disconnected/upgrading/rebooting), estimated time remaining.

**Why this priority**: Visibility into upgrade progress is critical for operations. Without real-time feedback, administrator cannot detect stuck devices or failed upgrades.

**Independent Test**: Can be tested with mock device status transitions to verify polling interval (20s), display refresh interval (30s), and status parsing work correctly.

**Acceptance Scenarios**:

1. **Given** user confirms pre-capture and clicks "Begin Upgrade", **When** the upgrade is initiated, **Then** the portal displays a status monitor with a table of devices
2. **Given** upgrade is in progress, **When** the portal polls every 30 seconds, **Then** the device status table updates to reflect current state (connected/disconnected/upgrading/rebooting)
3. **Given** a device is upgrading, **When** the system polls device events every 20 seconds, **Then** it detects firmware version changes and connection state changes
4. **Given** a device reboots during upgrade, **When** it reconnects, **Then** the status changes from "disconnected" to "connected" and eventual "completed"
5. **Given** all devices have completed upgrade, **When** the system detects all statuses as "connected" OR "completed", **Then** the portal signals "Upgrade Complete" and automatically transitions to post-capture

---

### User Story 6 - Settle Gate (Post-Upgrade Stabilization) (Priority: P2)

After all devices report connected, system enters "settle gate": polls device stats every 20 seconds for up to 300 seconds, waiting for uptime counter to reset (indicating successful reboot) AND firmware version to change (indicating successful upgrade). Once both conditions met, waits additional 60 seconds for clients to re-associate. Then takes post-capture automatically.

**Why this priority**: Post-upgrade "settle" time ensures devices have truly completed upgrade and clients have stabilized. This prevents comparison against incomplete/mid-reboot state, which would produce false negatives.

**Independent Test**: Can be tested with mock device uptime/firmware data to verify settle gate logic (reset detection, 60s delay, timeout handling).

**Acceptance Scenarios**:

1. **Given** upgrade completes and all devices are connected, **When** the settle gate begins, **Then** the system polls device stats every 20 seconds looking for uptime reset and firmware version change
2. **Given** a device shows uptime counter reset AND firmware version changed, **When** the condition is met, **Then** the system records this device as "settled"
3. **Given** all devices have settled or timeout expires (300s), **When** 60 additional seconds elapse, **Then** the system automatically initiates post-capture
4. **Given** post-capture begins, **When** the user sees the status screen, **Then** it displays "Taking post-upgrade capture..." with a progress indicator

---

### User Story 7 - Post-Upgrade Capture and Comparison (Priority: P1)

System captures network state after upgrade using identical data schema as pre-capture. Post-capture data is persisted to ArangoDB, Redis, and CSV. Portal displays side-by-side comparison table showing: device name, pre-upgrade firmware, post-upgrade firmware, pre-upgrade client count, post-upgrade client count, connection status change, and calculated delta (e.g., "Upgraded: 5.1 → 5.2, Clients: 120 → 125 (+5)"). User can download pre-capture, post-capture, and delta-report CSVs.

**Why this priority**: Side-by-side comparison is the core deliverable. Users need to verify the upgrade succeeded, identify any regressions, and troubleshoot issues.

**Independent Test**: Can be tested with pre-loaded capture data by calling comparison logic independently and verifying delta calculations.

**Acceptance Scenarios**:

1. **Given** post-capture completes, **When** the portal displays comparison view, **Then** it shows pre-capture and post-capture data in side-by-side tables
2. **Given** comparison view is rendered, **When** user reviews a device row, **Then** they see: pre-firmware, post-firmware, pre-client-count, post-client-count, status-change, delta summary
3. **Given** delta calculations are performed, **When** firmware versions differ, **Then** delta shows "Upgraded: X.Y → X.Z"
4. **Given** client counts differ, **When** delta is calculated, **Then** delta shows "Clients: N → M (+/-K)" with direction
5. **Given** comparison view is complete, **When** user clicks "Download Pre-Capture CSV", **Then** browser downloads pre-capture data
6. **Given** user clicks "Download Post-Capture CSV", **Then** browser downloads post-capture data
7. **Given** user clicks "Download Delta Report CSV", **Then** browser downloads delta-report with device-level changes

---

### User Story 8 - Session Locking and Data Retention (Priority: P2)

System prompts for work email on portal entry. Email is combined with browser identity (session cookie). Portal enforces 5-minute cooldown on abandoned sessions. User must click "CONFIRM" button to erase session data or "Continue" to resume interrupted session. Captured data is retained in ArangoDB for later retrieval.

**Why this priority**: Multi-user safety and audit trail. Prevents accidental data erasure and tracks who initiated captures. 5-minute cooldown prevents unattended portals from being accessed by others.

**Independent Test**: Can be tested by mocking session timeout and verifying prompt behavior, email logging, and resume logic work independently.

**Acceptance Scenarios**:

1. **Given** user enters the portal, **When** they are prompted for work email, **Then** they enter their email and it is stored with the session
2. **Given** user starts a capture but leaves the browser idle, **When** 5 minutes elapse without activity, **Then** the session is marked as abandoned
3. **Given** session is abandoned and another user accesses the portal, **When** they see the resume prompt, **Then** they can click "Continue" to resume or "CONFIRM" to erase
4. **Given** user clicks "CONFIRM", **When** the session is erased, **Then** data is removed from active session but remains in ArangoDB for audit
5. **Given** data is captured, **When** it is persisted to ArangoDB, **Then** it is tagged with session ID, user email, timestamp, and site for later retrieval

---

### Edge Cases

- **What happens if a device becomes disconnected during upgrade?** The system logs the event, continues polling, and waits for reconnection. If reconnection does not occur within timeout (300s settle gate), the device is marked as "failed" in the comparison report.
- **What happens if ArangoDB/Redis is unavailable?** DatabaseRouter silently falls back to CSV persistence. Pre-capture proceeds; user is notified that cloud backends are down but CSV backup is active.
- **What happens if upgrade is aborted mid-way?** System logs abort timestamp. Comparison view marks incomplete devices as "upgrade-cancelled". User can either rerun full upgrade or save current state for analysis.
- **What happens if user navigates away during capture?** Session timeout and locking logic kicks in. Browser stores capture state in session cookie for resume.
- **What happens if two admins start upgrades on the same site simultaneously?** The second admin's request is rejected with "Site locked by [email] until [timestamp]" message. Locking is per-site.

## Requirements

### Functional Requirements

- **FR-001**: System MUST authenticate users via Mist API token (environment variable) or MSP email/password login and validate credentials against Mist Cloud
- **FR-002**: System MUST display searchable site list for multi-site organizations; auto-select site for single-site users
- **FR-003**: System MUST allow users to select device type(s) (AP, Gateway, Switch) for pre-upgrade capture
- **FR-004**: System MUST fetch and display pre-upgrade network state: device firmware versions, uptime, client counts, port statistics, connection status
- **FR-005**: System MUST persist pre-upgrade capture to ArangoDB (primary), Redis (parallel), and CSV (backup)
- **FR-006**: System MUST render pre-capture data in interactive tables with sorting, pagination, and column filtering
- **FR-007**: System MUST provide CSV download for pre-capture data
- **FR-008**: System MUST require explicit "I Confirm" click before unlocking upgrade begin button (safety gate)
- **FR-009**: System MUST execute bulk firmware upgrade according to selected strategy (standard/staged/none)
- **FR-010**: System MUST poll device events every 20 seconds during upgrade to detect connection and firmware changes
- **FR-011**: System MUST display real-time upgrade status (device name, status: connected/disconnected/upgrading/rebooting/completed) with 30-second refresh interval
- **FR-012**: System MUST implement settle gate: after all devices connected, poll device stats every 20 seconds for uptime reset + firmware change, then wait 60 seconds before post-capture
- **FR-013**: System MUST fetch and display post-upgrade network state using identical data schema as pre-capture
- **FR-014**: System MUST persist post-upgrade capture to ArangoDB, Redis, and CSV
- **FR-015**: System MUST calculate and display side-by-side comparison: device name, pre-firmware, post-firmware, pre-client-count, post-client-count, status delta
- **FR-016**: System MUST provide CSV downloads for pre-capture, post-capture, and delta-report
- **FR-017**: System MUST prompt for work email on portal entry and combine with browser session identity for audit trail
- **FR-018**: System MUST enforce 5-minute idle timeout on sessions and display abandon/resume/erase prompt
- **FR-019**: System MUST log every operation (capture start, capture complete, upgrade start, upgrade complete, data save, session timeout) with timestamps before and after execution
- **FR-020**: System MUST run on a dedicated port (not 8055)
- **FR-021**: System MUST support multiple concurrent users on different sites without data cross-contamination (per-site locking)
- **FR-022**: System MUST use threading to parallelize capture API calls and shorten total run time
- **FR-023**: System MUST detect gateway hardware model (SRX vs SSR) per site and call appropriate upgrade endpoint (upgradeSiteDevices for SRX, upgradeOrgSsrs/upgradeSsr for SSR)
- **FR-024**: System MUST support capture tier selection (tier 2 default, tier 3 optional via per-run toggle)
- **FR-025**: System MUST tag captured data with schema_version field for forward compatibility
- **FR-026**: System MUST implement cascade dependencies: gateways release switches, switches release APs/clients, APs release wireless clients (for upgrade ordering)

### Key Entities

- **Capture**: Pre-upgrade or post-upgrade snapshot containing device list, firmware versions, client counts, port stats. Attributes: capture_id, timestamp, site_id, org_id, capture_tier (2 or 3), schema_version, device_list, client_metrics, uptime_baseline (pre-only), session_id, user_email
- **Device**: Network device (AP, Gateway, Switch). Attributes: device_id, device_name, model, firmware_version, uptime, status (connected/disconnected/upgrading), client_count, site_id, device_type
- **Session**: Portal session with email and timeout tracking. Attributes: session_id, user_email, created_at, last_activity, status (active/abandoned), site_id, org_id
- **ComparisonReport**: Calculated delta between pre and post captures. Attributes: report_id, site_id, pre_capture_id, post_capture_id, device_deltas (firmware_change, client_delta, status_change), total_devices_upgraded, total_devices_failed, timestamp

## Success Criteria

### Measurable Outcomes

- **SC-001**: Pre-upgrade capture completes in under 60 seconds (threaded API calls)
- **SC-002**: Upgrade status updates every 30 seconds with zero data loss or out-of-order events
- **SC-003**: Post-upgrade capture completes in under 60 seconds
- **SC-004**: Settle gate logic correctly identifies device readiness within 300 seconds (or timeout)
- **SC-005**: Side-by-side comparison renders with zero latency on data sets up to 10,000 devices
- **SC-006**: CSV export includes all pre-capture and post-capture data with no truncation or formatting errors
- **SC-007**: Portal loads on dedicated port within 5 seconds of startup
- **SC-008**: Concurrent users on different sites do not see data cross-contamination or locking conflicts
- **SC-009**: Idle session timeout triggers exactly at 5-minute mark (±10 seconds)
- **SC-010**: All operations are logged with before/after timestamps; logs are queryable and contain no secrets

## Assumptions

- **Authentication**: Mist API token is provided via environment variable (preferred) or MSP email/password login is available. Either method is assumed to work; the portal does not provision new users.
- **Network State**: Pre-upgrade baseline captures device uptime; post-upgrade compares against uptime reset as upgrade success indicator. This assumes devices reboot during firmware upgrade (true for APs and switches; may vary for gateways).
- **Gateway Hardware**: SRX and SSR are the only gateway models; other models are not in scope for this feature. Detection per site is assumed to be accurate based on API model field.
- **Capture Data Schema**: Pre-capture and post-capture use identical schema (same fields, same order). Schema version field enables backward compatibility if schema changes in future releases.
- **Client Association Timing**: Wireless clients re-associate within 60 seconds after upgrade completion. This 60-second settle delay is assumed sufficient.
- **ArangoDB Availability**: ArangoDB is running when container is deployed. If not available, DatabaseRouter falls back to Redis then CSV. Reads from ArangoDB are assumed to be consistent (no replication lag).
- **Single-Site Scope**: Feature targets one site at a time. Multi-site batch jobs are out of scope; data layer is designed to support this later (captured via site_id and org_id fields).
- **Thread Pool**: Threaded capture is assumed to complete within 60 seconds. Thread pool size is assumed to be between 4-8 threads (OS dependent).
- **CSV Backup Location**: CSV files are written to `data/` directory. This directory is assumed to exist and be writable (enforced at runtime).
- **Browser Session Persistence**: Session cookies are assumed to be stored in browser memory and survive page refresh but not browser close.
- **Mist API Rate Limits**: Polling every 20 seconds (device events) and 30 seconds (UI refresh) is assumed to stay within Mist API rate limits (1000 req/min default). If exceeded, the system is assumed to back off gracefully.

## Out of Scope

- Multi-site batch jobs (data layer must support this later via site_id, org_id fields)
- Changes to existing CLI upgrade menus (e.g., menu option 88, 89, etc.)
- Pre-upgrade validation (e.g., checking for unsupported device models or firmware versions before upgrade starts)
- Auto-recovery from failed devices (system reports failure; operator must remediate manually)
- Custom upgrade ordering beyond cascade dependencies (e.g., rolling upgrade per building)
- Real-time device metric streaming (polling model only)
- Mobile-responsive UI (desktop/tablet browsers only)

## Known Prerequisites & Breaking Assumptions

- **DatabaseRouter Bug**: DatabaseRouter currently skips ArangoDB and Redis writes when running outside container (silent failure with CSV fallback). This MUST be fixed before this feature can work properly. The feature relies on ArangoDB as primary data store and Redis for caching. Fix priority: BLOCKER. Without this fix, all captures are CSV-only, limiting data retrieval and audit trail.

## Technical Constraints (Locked Decisions from Issue)

- **Port**: Dedicated port (not 8055); exact port TBD during planning/implementation
- **Terminology**: Use "capture" not "snapshot" throughout UI and logs
- **Settle Gate**: Poll device events every 20s, wait for connected event + firmware version change + 60s delay
- **Cascade**: Gateways release switches, switches release APs/clients, APs release wireless clients
- **Storage**: ArangoDB primary, Redis alongside, CSV backup
- **Locking**: Prompt for work email, combine with browser identity, 5-min cooldown, "CONFIRM" to erase, "continue" to resume
- **Scope**: One site at a time; data layer supports multi-site for later
- **Gateway Modes**: Mixed fleet; detect SRX vs SSR per site; call upgradeSiteDevices for SRX, upgradeOrgSsrs/upgradeSsr for SSR
- **Capture Tier**: Tier 2 default, per-run toggle for tier 3, schema_version field included
- **Multi-User**: Support multiple users on different sites; prevent cross-contamination
- **Threading**: Use threads to shorten run time
- **Logging**: Log before and after every operation
