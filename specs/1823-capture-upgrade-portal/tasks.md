# Implementation Tasks: Capture Upgrade Portal (Issue #1823)

**Status**: Ready for Phase 1 after pre-implementation fixes.
**Last updated**: Task list initialized

---

## Overview

20 actionable tasks across 5 phases. Critical path: 18 days (T-001 → T-006 → T-011 → T-015 → T-020). All tasks carry inline comments explaining rationale, acceptance criteria, and verification steps.

---

## Pre-Implementation Phase (Blockers to Fix Before Phase 1)

### T-0.0: Fix DatabaseRouter container initialization bug
- **Description**: Address issue #2228 (container silent failures with "container name already in use"). Update `scripts/compose.ps1` to prevent ArangoDB and Redis recreations when upgrading only MistHelper app.
- **Acceptance criteria**:
  - Compose script requires `--no-deps` flag
  - Service name argument is mandatory
  - No ArangoDB or Redis pods destroyed during `misthelper-app` upgrade
  - Caution message added to MistHelper custom instructions
- **Verification**: Run `.\scripts\compose.ps1 up -d --no-deps misthelper` and confirm ArangoDB and Redis remain untouched
- **Dependency**: None (blocks all other tasks)
- **Effort**: 1 hour

### T-0.5: Implement audit logging framework
- **Description**: Build logging infrastructure to satisfy FR-019 (log all operations with timestamps) and SC-010 (queryable logs with zero secrets). Create ArangoDB collection `audit_logs`, query endpoint `GET /api/audit`, and secret masking filter.
- **Acceptance criteria**:
  - ArangoDB collection `audit_logs` exists with indexed `timestamp` and `operation`
  - All operations log before/after state with millisecond precision
  - Query endpoint `GET /api/audit?operation=X&start=Y&limit=Z` works
  - Secret masking filter redacts tokens/passwords in query output
  - Unit test coverage >= 80%
- **Verification**: Trigger a capture operation, then query `GET /api/audit?operation=capture_start` and confirm log entry exists with no secrets
- **Dependency**: T-0.0
- **Effort**: 8 hours

---

## Phase 1: Authentication & Site Selection (Days 1-3)

### T-001: Implement JWT-based session management
- **Description**: Build Flask-JWT extension for stateless sessions. Tokens expire after 5 minutes of inactivity (per SC-009). Return tokens with 30-second warning before expiry; support "continue" flow to refresh without re-authenticating.
- **Acceptance criteria**:
  - `POST /api/auth/login` accepts `(username, password)`, returns `{token, expires_at}`
  - Token payload includes `user_id`, `site_id`, `issued_at`, `expires_at`
  - Middleware validates token on all protected endpoints
  - Token refresh response arrives 30 seconds before expiry
  - "Continue" button extends session without re-login
  - Invalid token returns 401 Unauthorized
  - Unit tests: valid token, expired token, invalid signature, missing token
- **Verification**: Login, wait 4.5 minutes, confirm 30-second warning appears, click "Continue", confirm session extends
- **Dependency**: T-0.0, T-0.5
- **Effort**: 12 hours

### T-002: List sites and devices from Mist API
- **Description**: Query `mistapi.api.v1.orgs.listOrgSites(org_id)` and `mistapi.api.v1.sites.listSiteDevices(site_id, type="all")` to populate dropdown selectors. Cache results for 5 minutes (per FR-003).
- **Acceptance criteria**:
  - `GET /api/sites` returns [{"id", "name", "country_code"}, ...] sorted by name
  - `GET /api/sites/:site_id/devices` returns APs, switches, gateways (type="all")
  - Results cached for 5 minutes in Redis
  - Stale cache expires automatically
  - Mock test with 10 sites times 20 devices
- **Verification**: Call `GET /api/sites`, confirm 10 test sites appear, call same endpoint again within 5 minutes and confirm response time less than 50ms (cache hit)
- **Dependency**: T-001
- **Effort**: 6 hours

### T-003: Build site/device selection UI (HTML/Jinja2)
- **Description**: Create selection page at `/upgrade/select` with dropdown for site, multi-select for devices, and "Next" button (validates >= 1 device selected). Display device model, serial, firmware version (running version from `RunningFirmwareVersionResolver`).
- **Acceptance criteria**:
  - Site dropdown loads from `GET /api/sites`
  - Device list updates when site changes
  - Device table shows: model, serial, running firmware (not configured version per issue #2006)
  - Multi-select supports Ctrl+A, Ctrl+Click
  - "Next" button disabled until >= 1 device selected
  - Form validation on client and server
- **Verification**: Load page, select site, confirm devices populate, select 3 devices, click "Next", confirm POST to `/upgrade/configure` with device IDs
- **Dependency**: T-002
- **Effort**: 8 hours

### T-004: Persist selection state to ArangoDB
- **Description**: Store site_id, device_ids, user_id, selected_at, session_token in `upgrade_runs` collection (natural PK: run_id). Create `/api/runs/:run_id` read endpoint and `PATCH /api/runs/:run_id` update endpoint.
- **Acceptance criteria**:
  - POST handler at selection saves to `upgrade_runs`
  - `run_id` is UUID, never changes during session
  - Collection has indexes on: org_id, site_id, user_id, created_at
  - Read endpoint returns full run state
  - Update only allows field changes that preserve immutable fields (site_id, device_ids, created_at)
- **Verification**: Navigate to selection, select devices, confirm ArangoDB doc exists, query `GET /api/runs/:run_id` and confirm device list matches
- **Dependency**: T-003
- **Effort**: 6 hours

### T-005: Add input validation and error handling
- **Description**: Validate all inputs (site_id format, device_id format, min/max array lengths). Return 400 Bad Request with clear error messages. Log all validation failures (audit log).
- **Acceptance criteria**:
  - Missing site_id arrow 400 "site_id required"
  - Invalid site_id format arrow 400 "invalid site_id format"
  - Empty device_ids arrow 400 "select at least 1 device"
  - Duplicate device_ids arrow deduplicated silently
  - All validation failures logged to audit log
  - Unit tests cover 10 edge cases
- **Verification**: POST with missing site_id, confirm 400 response with correct message, check audit log shows validation error
- **Dependency**: T-004
- **Effort**: 4 hours

---

## Phase 2: Pre-Capture and Upgrade Service (Days 4-6)

### T-006: Implement CaptureService (pre-upgrade snapshot)
- **Description**: Build service that calls `getOrgInventory(org_id)`, `listSiteDevicesStats(site_id)`, and `listSiteNetworkPolicies(site_id)` to capture pre-upgrade state. Store snapshot in ArangoDB `upgrade_captures` collection with composite PK (run_id, capture_type="pre", timestamp). Include device config, radio settings, security policies.
- **Acceptance criteria**:
  - Service fetches device inventory via Mist API
  - Snapshot includes: firmware versions (running), radio config, policy bindings, LLDP neighbors
  - ArangoDB doc created with composite key
  - Timestamp recorded in UTC
  - No secrets stored (tokens, passwords redacted)
  - Retries up to 3 times on API timeout
  - Logs before/after capture
- **Verification**: Trigger pre-capture, confirm ArangoDB doc exists with all expected fields, check audit log shows capture_start and capture_complete
- **Dependency**: T-005
- **Effort**: 12 hours

### T-007: Build pre-upgrade configuration page UI
- **Description**: Create `/upgrade/configure` page that displays selected devices, reads from T-006 capture endpoint, shows options for: upgrade strategy (serial/parallel), rollback enable, pre-flight checks. "Start capture" button initiates T-006.
- **Acceptance criteria**:
  - Page loads device list from `GET /api/runs/:run_id`
  - Displays pre-capture summary (device count, current firmware versions)
  - Upgrade strategy selector (serial: one device at a time; parallel: all devices together)
  - Rollback checkbox (enable/disable automatic rollback on failure)
  - "Start Capture" button disabled until device list loads
  - Click "Start Capture" arrow POST to `/api/runs/:run_id/capture/start` (invokes T-006)
- **Verification**: Load page, select serial strategy, enable rollback, click "Start Capture", confirm page transitions to status page and T-006 runs in background
- **Dependency**: T-006
- **Effort**: 8 hours

### T-008: Implement UpgradeService (firmware upgrade orchestration)
- **Description**: Build service that orchestrates the firmware upgrade workflow. Calls `getOrgDeviceFirmwareVersions()` to check available versions, then calls device-specific upgrade endpoints (`upgradeOrgDevice()` per mistapi). Respects serial vs. parallel strategy from T-007. Reports progress every 10 seconds. Handles retries, rollback on failure (per SC-005).
- **Acceptance criteria**:
  - Service accepts: run_id, device_ids, firmware_version, strategy (serial/parallel), rollback_enabled
  - Validates firmware version is available
  - Serial: upgrades one device, waits for completion, upgrades next
  - Parallel: upgrades all devices concurrently
  - Polls device status every 10 seconds (progress callback)
  - On upgrade failure: if rollback_enabled, calls rollback endpoint; otherwise marks device as failed
  - Stores upgrade_run record in ArangoDB with status (pending/in_progress/completed/failed)
  - Retries up to 3 times per device on transient errors
  - Logs every state transition (audit log)
- **Verification**: Trigger upgrade on 3 devices (serial), confirm devices upgrade one at a time, check `GET /api/runs/:run_id` shows progress callback every 10s, confirm rollback log entry if one device fails
- **Dependency**: T-007
- **Effort**: 16 hours

### T-009: Build upgrade status page UI
- **Description**: Create real-time status dashboard at `/upgrade/status` that polls `GET /api/runs/:run_id/status` every 1 second. Display: device name, current status (pending/upgrading/completed/failed), progress percent, firmware version (before/after), time elapsed, ETA.
- **Acceptance criteria**:
  - Page polls status endpoint every 1 second
  - Device rows update in real-time
  - Color-coded status: pending (grey), upgrading (blue), completed (green), failed (red)
  - Progress bar shows percent complete
  - Shows before/after firmware versions
  - Displays time elapsed and ETA based on average device upgrade time
  - "Cancel upgrade" button available (triggers rollback if enabled)
  - Page auto-advances to post-capture page when all devices complete
- **Verification**: Trigger upgrade, open status page, confirm real-time updates every approximately 1s, check color-coding and progress bar, wait for completion and confirm auto-advance
- **Dependency**: T-008
- **Effort**: 10 hours

---

## Phase 3: Post-Upgrade and Settle Gate (Days 7-9)

### T-010: Implement SettleGateService (post-upgrade validation)
- **Description**: Build service that runs post-upgrade checks to ensure network stability before declaring success. Checks: device reachability (ICMP ping), API responsiveness (mistapi call), correct firmware version running, LLDP neighbor presence. Waits up to 5 minutes for all checks to pass (per SC-006). Stores settle_gate_run in ArangoDB with results.
- **Acceptance criteria**:
  - Service accepts run_id, device_ids
  - Checks run in parallel: ping, API query, firmware version read, LLDP neighbor query
  - Each check has timeout: ping 5s, API 10s, firmware read 10s, neighbor query 10s
  - Retries failed check every 10 seconds for up to 5 minutes
  - If all checks pass before timeout: returns success
  - If timeout expires and checks still failing: returns failure with reason
  - Stores settle_gate_run doc in ArangoDB with composite key (run_id, timestamp)
  - Logs all check results (audit log)
- **Verification**: Simulate device reachability by pinging MistHelper test servers, trigger settle gate, confirm all checks pass within 5 min, query `GET /api/runs/:run_id/settle-gate` and confirm results
- **Dependency**: T-009
- **Effort**: 12 hours

### T-011: Capture post-upgrade state
- **Description**: After settle gate succeeds, call CaptureService again (same as T-006) to capture post-upgrade snapshot. Store in `upgrade_captures` with composite key (run_id, capture_type="post", timestamp).
- **Acceptance criteria**:
  - Service method identical to T-006, but capture_type="post"
  - Snapshot captures same fields as pre-capture (firmware versions, radio config, policies)
  - ArangoDB doc created
  - Stores reference to settle_gate_run (edge document in `captures_for_run`)
- **Verification**: Query ArangoDB for both `capture_type="pre"` and `capture_type="post"` docs for same run_id, confirm both exist
- **Dependency**: T-010
- **Effort**: 4 hours

### T-012: Enforce settle gate cascade (no comparison until post-capture complete)
- **Description**: Add validation to comparison service (T-013): check that settle_gate_run exists and succeeded before allowing comparison. Return 400 "Settle gate not complete" if not. Prevent user from advancing to comparison page until post-capture is done.
- **Acceptance criteria**:
  - Comparison endpoint checks: settle_gate_run.status equals "success"
  - Returns 400 if check fails
  - UI "View Comparison" button disabled until settle gate completes
  - Status page shows "Settle gate in progress..." until T-010 finishes
- **Verification**: Attempt to fetch comparison before settle gate completes, confirm 400 response, wait for settle gate, confirm comparison endpoint works
- **Dependency**: T-011
- **Effort**: 3 hours

---

## Phase 4: Comparison and Session Locking (Days 10-14)

### T-013: Implement ComparisonService (delta calculation)
- **Description**: Build service that compares pre- and post-upgrade ArangoDB snapshots. Calculates deltas for each device: firmware version change, radio config change, policy binding change, new/missing neighbors. Stores comparison_report in ArangoDB with composite key (run_id, device_id, timestamp).
- **Acceptance criteria**:
  - Service accepts run_id
  - Loads pre-capture and post-capture docs from ArangoDB
  - Calculates deltas for each device field
  - Marks fields as: unchanged, changed (old arrow new), new, missing
  - Flags unexpected changes (for example, radio config changed when it should not)
  - Stores comparison_report doc with all deltas
  - Returns human-readable delta summary
- **Verification**: Trigger comparison, query `GET /api/runs/:run_id/comparison`, confirm deltas show correct before/after values
- **Dependency**: T-012
- **Effort**: 10 hours

### T-014: Build comparison UI page
- **Description**: Create `/upgrade/comparison` page that displays pre/post comparison side-by-side. Table: Device | Field | Before | After | Status (✓ expected, ⚠ unexpected). "Accept comparison" button marks run as complete (stores run.status="completed", run.completed_at). "Flag for review" button marks concerning deltas.
- **Acceptance criteria**:
  - Loads comparison from `GET /api/runs/:run_id/comparison`
  - Displays side-by-side table with before/after for each device field
  - Shows status icon: ✓ for expected, ⚠ for unexpected
  - "Flag for review" button marks rows as requiring manual approval
  - "Accept comparison" button enabled when all flagged items reviewed
  - Stores decision in audit log
- **Verification**: Load comparison page, check side-by-side display, flag one delta, confirm "Accept" button still disabled, unflag, click "Accept", confirm run.status updates to "completed"
- **Dependency**: T-013
- **Effort**: 8 hours

### T-015: Implement session locking (Redis-based)
- **Description**: Use Redis to lock upgrade_run during execution. Only one active session per user per site. If user tries to start a new upgrade while one is in progress, return 409 Conflict with message "Upgrade already in progress for this site". Lock expires after 30 minutes or when run completes (whichever is first).
- **Acceptance criteria**:
  - Redis key format: `upgrade_lock:{user_id}:{site_id}`
  - Lock value: run_id (allows checking which run is locked)
  - Lock acquired at T-006 (capture start), released at T-014 (comparison complete)
  - Lock TTL 30 minutes (per SC-009 session timeout)
  - Attempt to start upgrade while locked arrow 409 response
  - POST `/api/runs` checks lock before creating new run
- **Verification**: Start upgrade, attempt to start second upgrade for same site, confirm 409 response with correct message, wait for first upgrade to complete, confirm lock released and second upgrade can start
- **Dependency**: T-014
- **Effort**: 6 hours

### T-016: Implement session timeout and continuation (per SC-009)
- **Description**: Monitor JWT token expiry. When token has less than or equal to 30 seconds remaining, send warning response header `X-Token-Expires-In: 30`. If token expires mid-upgrade, pause upgrade, return 401, and require "Continue" to refresh token and resume. Store pause state in ArangoDB (upgrade_runs.paused_at, paused_reason).
- **Acceptance criteria**:
  - Middleware checks token expiry, sends warning header when less than or equal to 30s remaining
  - Client receives header, displays "Session expiring in 30 seconds" warning
  - "Continue" button calls `POST /api/auth/continue` to refresh token
  - If token expires during upgrade (for example, no continue click): upgrade pauses
  - Resume endpoint `POST /api/runs/:run_id/resume` resumes from paused state
  - Pause events logged to audit log
- **Verification**: Login, trigger upgrade, wait 4.5 minutes without action, confirm warning appears, click "Continue", confirm token refreshed and upgrade resumes
- **Dependency**: T-015
- **Effort**: 8 hours

---

## Phase 5: Testing and Documentation (Days 15-29)

### T-017: Write end-to-end tests (Playwright)
- **Description**: Build E2E test suite covering full upgrade workflow: login arrow select devices arrow configure arrow start capture arrow monitor upgrade arrow view settle gate arrow review comparison arrow accept. Tests run against containerized MistHelper with mock Mist API. Include happy path (all devices upgrade successfully) and sad paths (device failure, network timeout, token expiry).
- **Acceptance criteria**:
  - Happy path test: login arrow select 3 devices arrow serial upgrade arrow all complete arrow accept comparison
  - Sad path 1: device failure mid-upgrade, rollback triggered
  - Sad path 2: network timeout during capture, retry succeeds
  - Sad path 3: token expires, "Continue" refreshes and resumes
  - Tests use mock Mist API (no real cloud calls)
  - Tests run in Docker container
  - Coverage: 90 percent or more of UI flows
- **Verification**: Run `pytest tests/e2e/test_upgrade_portal.py`, confirm all tests pass
- **Dependency**: T-016
- **Effort**: 16 hours

### T-018: Write performance tests (concurrent upgrades)
- **Description**: Load test with concurrent upgrade requests: 10 users, 3 concurrent upgrades per user, 5 devices per upgrade. Measure: response time (p50, p99), upgrade completion time, API error rate, Redis/ArangoDB throughput.
- **Acceptance criteria**:
  - Can handle 30 concurrent upgrades without degradation
  - Response time p99 less than 2 seconds
  - Upgrade completion time stable (no queueing delays)
  - API error rate equals 0 percent
  - Redis CPU less than 30 percent, ArangoDB CPU less than 50 percent
  - Logs show no errors or warnings
- **Verification**: Run `pytest tests/perf/test_concurrent_upgrades.py`, confirm all thresholds met
- **Dependency**: T-017
- **Effort**: 10 hours

### T-019: Write data migration and rollback procedures
- **Description**: Document data migration plan for future schema changes (for example, adding fields to capture schema). Document rollback procedure if upgrade fails beyond recovery point. Store procedures in `specs/1823-capture-upgrade-portal/contracts/schema-versioning.md`.
- **Acceptance criteria**:
  - Schema versioning strategy defined (current version field in all collections)
  - Migration playbook: how to add/remove fields, backfill data
  - Rollback procedure: restore from pre-upgrade snapshot
  - Tested: perform dummy migration, verify no data loss
- **Verification**: Read procedure doc, follow steps, confirm data remains consistent after migration
- **Dependency**: T-018
- **Effort**: 6 hours

### T-020: Final documentation, cleanup, and acceptance
- **Description**: Complete documentation (data-model.md, contracts/, API guide). Update README with portal URL and quick start. Run all quality gates (ruff, black, mypy, pytest, coverage greater than or equal to 80 percent). Tag version. Acceptance: all FRs (26) and SCs (10) verified passing.
- **Acceptance criteria**:
  - data-model.md complete: all collections, fields, indexes
  - contracts/storage.md: ArangoDB behavior, Redis TTLs
  - contracts/settle-gate.md: timing, algorithm, retry policy
  - contracts/comparison.md: delta rules
  - contracts/schema-versioning.md: migration and rollback
  - API documentation: all endpoints, request/response examples
  - README updated: portal description, installation, quick start
  - All quality gates pass (ruff, black, mypy, pytest)
  - Coverage greater than or equal to 80 percent
  - All 26 FRs covered by tests
  - All 10 SCs have acceptance criteria and pass
  - Version tagged and released
- **Verification**: Run `ruff check . && black --check . && mypy ... && pytest --cov`, confirm all pass; verify 26 FRs in test output; verify 10 SCs in acceptance test output
- **Dependency**: T-019
- **Effort**: 12 hours

---

## Task Dependencies

Critical path: T-0.0 arrow T-0.5 arrow T-001 arrow T-002 arrow T-003 arrow T-004 arrow T-005 arrow T-006 arrow T-007 arrow T-008 arrow T-009 arrow T-010 arrow T-011 arrow T-012 arrow T-013 arrow T-014 arrow T-015 arrow T-016

After T-016 complete, Phase 5 tasks run in sequence: T-017 arrow T-018 arrow T-019 arrow T-020

Total effort: approximately 245 hours

Estimated calendar time: 18 days critical path plus 7 days (Phase 5 in parallel) equals approximately 25 days with 1 full-time engineer

---

## Notes for Implementation

1. Secrets management: All Mist API tokens, database credentials stored in `.env`, never in code
2. Retries: All external API calls (Mist API, device connectivity checks) retry 3 times with exponential backoff
3. Observability: Every operation logged to `audit_logs` collection with before/after state
4. Testing: Mock Mist API for unit tests; use containerized MistHelper for E2E tests
5. Session timeout: 5 minutes inactivity (per SC-009), 30-second warning, "Continue" to extend
