# Implementation Plan: Pre-Upgrade/Post-Upgrade Capture Portal

**Issue**: #1823  
**Feature**: Pre-upgrade and post-upgrade capture portal with side-by-side comparison  
**Related Spec**: `spec.md`  
**Created**: 2026-09-04  
**Status**: In Planning

---

## 1. Architecture Overview

### 1.1 System Architecture

The capture portal follows a three-tier architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    Web UI (Gunicorn)                        │
│              Port 8056 (separate from 8055)                 │
│         Flask app with Jinja2 templates + T-Mobile theme   │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────┐
│              REST API Layer & Session Manager              │
│  • Authentication (Mist token / MSP email+password)        │
│  • Session locking (email + browser ID → 5min cooldown)   │
│  • Route handlers: capture, upgrade, settle, compare       │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────┐
│                 Business Logic Services                      │
│  • CaptureService (multi-threaded device/client fetch)     │
│  • UpgradeService (firmware execution, cascade)            │
│  • SettleGateService (event polling + stats stabilization) │
│  • ComparisonService (delta calculation, rendering)        │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────┐
│              Storage & Data Persistence                      │
│  • Primary: ArangoDB (captures, upgrades, comparisons)      │
│  • Cache: Redis (session state, site locks)                 │
│  • Fallback: CSV files in data/ directory                   │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Key Design Decisions

- **Port**: Dedicated port 8056 to avoid conflict with existing 8055 portal.
- **Storage Hierarchy**: ArangoDB as primary (matches issue #1823 requirement); Redis for locks; CSV fallback.
- **Concurrency Model**: Threading for capture operations; async polling for upgrade status.
- **Session Isolation**: Email + browser session token prevents cross-user contamination.
- **Cascade Dependencies**: Gateways → Switches → APs → Wireless clients (enforced at settle gate).

---

## 2. Database Schema

### 2.1 ArangoDB Collections

#### Collection: `capture_snapshots`

Stores pre-upgrade and post-upgrade capture data.

```json
{
  "_key": "capture_<site_id>_<timestamp>",
  "site_id": "abc123def456",
  "site_name": "New York HQ",
  "organization_id": "org_xyz789",
  "capture_type": "pre_upgrade|post_upgrade",
  "timestamp": "2026-09-04T12:30:45Z",
  "schema_version": "1.0",
  "capture_tier": 2,
  "device_types_selected": ["gateway", "switch", "ap"],
  "devices": [
    {
      "device_id": "dev_001",
      "name": "SRX345-01",
      "model": "SRX345",
      "device_type": "gateway",
      "mac": "00:1a:2b:3c:4d:5e",
      "firmware_version": "21.4R1",
      "status": "connected",
      "uptime_seconds": 864000,
      "wired_clients": 42,
      "wireless_clients": 128,
      "tunnel_count": 5,
      "bgp_peers": 3
    }
  ],
  "statistics_summary": {
    "total_devices": 15,
    "connected": 14,
    "disconnected": 1,
    "total_wired_clients": 156,
    "total_wireless_clients": 342
  }
}
```

#### Collection: `upgrade_runs`

Tracks firmware upgrade execution.

```json
{
  "_key": "upgrade_run_<site_id>_<timestamp>",
  "site_id": "abc123def456",
  "organization_id": "org_xyz789",
  "user_email": "admin@customer.com",
  "upgrade_id": "upgrade_abc123",
  "status": "pending|running|succeeded|failed",
  "upgrade_strategy": "standard|staged",
  "started_at": "2026-09-04T12:35:00Z",
  "completed_at": "2026-09-04T13:15:30Z",
  "device_count": 15,
  "devices_upgraded": 14,
  "devices_failed": 1,
  "target_firmware": "22.1R1",
  "pre_capture_key": "capture_<site_id>_<timestamp>",
  "post_capture_key": "capture_<site_id>_<timestamp>",
  "error_message": null
}
```

#### Collection: `comparison_reports`

Stores side-by-side comparison results.

```json
{
  "_key": "comparison_<site_id>_<run_timestamp>",
  "site_id": "abc123def456",
  "upgrade_run_key": "upgrade_run_<site_id>_<timestamp>",
  "pre_capture_key": "capture_<site_id>_<pre_timestamp>",
  "post_capture_key": "capture_<site_id>_<post_timestamp>",
  "generated_at": "2026-09-04T13:16:00Z",
  "summary": {
    "total_devices": 15,
    "upgraded_successfully": 14,
    "upgrade_failed": 1,
    "firmware_version_changes": 14,
    "client_count_delta": { "wired": -2, "wireless": +5 }
  },
  "device_deltas": [
    {
      "device_id": "dev_001",
      "name": "SRX345-01",
      "pre_firmware": "21.4R1",
      "post_firmware": "22.1R1",
      "uptime_change": -864000,
      "client_delta": { "wired": 0, "wireless": 3 }
    }
  ]
}
```

#### Collection: `session_locks`

Manages multi-user session safety.

```json
{
  "_key": "lock_<site_id>",
  "site_id": "abc123def456",
  "organization_id": "org_xyz789",
  "owner_email": "admin@customer.com",
  "browser_session_token": "sess_abc123xyz",
  "locked_at": "2026-09-04T12:30:00Z",
  "expires_at": "2026-09-04T12:35:00Z",
  "status": "active|expired|released",
  "current_upgrade_run": "upgrade_run_<site_id>_<timestamp>|null"
}
```

### 2.2 Redis Keys

- `site_lock:<site_id>` → JSON of active session lock (TTL: 5 min)
- `session_state:<session_token>` → User state (TTL: 24h)
- `capture_inprogress:<site_id>:<timestamp>` → Capture progress (TTL: 2h)

### 2.3 CSV Fallback Format

Files stored in `data/<YYYYMMDD>_<site_name>_<capture_type>.csv`:

```
device_id,device_name,device_type,model,mac,firmware_version,status,uptime_seconds,wired_clients,wireless_clients
dev_001,SRX345-01,gateway,SRX345,00:1a:2b:3c:4d:5e,21.4R1,connected,864000,42,128
```

---

## 3. API Layer Design

### 3.1 Endpoints

#### Authentication

- **POST** `/auth/login` — Authenticate with Mist token or MSP email/password
  - Response: Session token, authenticated organization ID

#### Site & Device Selection

- **GET** `/api/organizations` — List orgs (MSP mode only)
- **GET** `/api/organizations/<org_id>/sites` — List sites with search
- **GET** `/api/organizations/<org_id>/sites/<site_id>/devices` — List devices by type

#### Capture & Upgrade

- **POST** `/api/sites/<site_id>/capture` — Initiate pre-capture
  - Payload: `{device_types: [...], tier: 2|3}`
  - Response: `{capture_id, started_at}`

- **POST** `/api/sites/<site_id>/upgrade` — Begin firmware upgrade
  - Payload: `{pre_capture_id, upgrade_strategy, target_firmware}`
  - Response: `{upgrade_run_id, status}`

- **GET** `/api/upgrade/<upgrade_run_id>/status` — Poll upgrade progress
  - Response: `{status, progress_percent, devices_upgraded, current_device, eta_seconds}`

- **POST** `/api/sites/<site_id>/capture-post` — Initiate post-capture
  - Payload: `{upgrade_run_id, tier: 2|3}`
  - Response: `{capture_id, started_at}`

#### Comparison

- **GET** `/api/comparison/<comparison_report_id>` — Fetch comparison report
  - Response: Full comparison JSON with deltas

- **GET** `/api/comparison/<comparison_report_id>/csv` — Export comparison as CSV

### 3.2 Authentication

- Accept Mist API token from environment variable or user login
- MSP login via email + password (delegated to `mistapi` library)
- Session token stored in Flask session; validate on each request
- Site lock: combine user email + browser session token to prevent concurrent edits

---

## 4. Backend Services

### 4.1 CaptureService

**Responsibility**: Fetch device state, client lists, statistics before and after upgrade.

```python
class CaptureService:
    def capture_site(self, site_id, device_types, tier=2):
        """
        Multi-threaded capture of all device state for a site.
        
        Returns:
            capture_document: {devices, statistics_summary, timestamp, ...}
        """
        # 1. Fetch device list for site (filtered by device_types)
        # 2. For each device type, spawn worker threads:
        #    - Fetch device metadata (model, firmware, status)
        #    - Fetch client lists (wired / wireless)
        #    - Fetch statistics (uptime, tunnel count, BGP peers if tier 3)
        # 3. Aggregate results
        # 4. Build capture document with schema_version
        # 5. Return document (does not persist — caller does that)
```

### 4.2 UpgradeService

**Responsibility**: Execute firmware upgrade across devices with cascade dependency enforcement.

```python
class UpgradeService:
    def execute_upgrade(self, site_id, device_list, upgrade_strategy, target_firmware):
        """
        Execute upgrade via Mist API with cascade logic.
        
        Cascade order:
        1. Gateways (if SRX: via upgradeSiteDevices; if SSR: via upgradeOrgSsrs)
        2. Switches (via upgradeSiteDevices)
        3. APs (via upgradeSiteDevices)
        4. Wireless clients follow APs automatically
        
        Returns:
            upgrade_run_document with status, devices_upgraded, errors
        """
        # 1. Detect gateway family (SRX vs SSR) per device
        # 2. Partition device list by type and family
        # 3. Execute upgrade in cascade order
        # 4. Poll status every 30 seconds
        # 5. Return upgrade run record with final counts
```

### 4.3 SettleGateService

**Responsibility**: Wait for devices to stabilize after upgrade (uptime reset, firmware confirmed).

```python
class SettleGateService:
    def wait_for_settle(self, site_id, devices, max_wait_seconds=600):
        """
        Gate that holds capture until devices are stable.
        
        Process:
        1. Poll device events API every 20s for <device_type>_CONNECTED events
        2. For each device:
           a. Wait for connected event (firmware write phase complete)
           b. Poll device stats every 20s until:
              - uptime_seconds < previous uptime (device rebooted)
              - firmware_version == target_firmware (confirmed)
           c. Wait additional 60s for stats to stabilize
           d. Consider device settled
        3. Return list of settled devices (timeout if any device exceeds max_wait)
        
        Cascade enforcement:
            - Gateways must settle before switches are declared ready
            - Switches must settle before APs are declared ready
            - APs must settle before wireless clients are considered ready
        
        Returns:
            {settled_devices: [...], timeout_devices: [...], took_seconds: N}
        """
```

### 4.4 ComparisonService

**Responsibility**: Compute deltas between pre and post captures.

```python
class ComparisonService:
    def compare_captures(self, pre_capture, post_capture):
        """
        Generate side-by-side comparison with delta calculations.
        
        Returns:
            comparison_document with:
            - device-by-device firmware version changes
            - client count deltas (wired + wireless)
            - device status changes
            - summary statistics
        """
        # 1. Match devices between pre and post by MAC/ID
        # 2. For each device, compute deltas:
        #    - firmware_version: pre vs post
        #    - uptime_seconds: should have reset
        #    - client counts: should be stabilized
        # 3. Aggregate summary
        # 4. Build comparison document
        # 5. Store in ArangoDB via DatabaseRouter
```

---

## 5. UI/Portal Design

### 5.1 Page Flow

```
Login Page
    ↓
Organization Selection (MSP only)
    ↓
Site Selection (searchable)
    ↓
Device Type Selection (AP, Gateway, Switch)
    ↓
Upgrade Options (Standard / Staged / Reuse)
    ↓
Pre-Capture Display (tables, sorting, CSV download)
    ↓
Confirm & Proceed (requires "CONFIRM" text input)
    ↓
Upgrade Status (real-time polling every 30s)
    ↓
Post-Capture Display (tables, sorting, CSV download)
    ↓
Comparison View (side-by-side, deltas, CSV export)
```

### 5.2 UI Implementation

- **Framework**: Flask + Jinja2 templates
- **Styling**: T-Mobile color scheme (magenta, white, dark gray)
- **Interactivity**: Client-side sorting (JavaScript), real-time status refresh (fetch every 30s)
- **Tables**: Sortable columns, pagination for large device lists
- **CSV Export**: Server-side generation, browser download

### 5.3 Session Timeout & Locking

- User enters work email on login
- Combine email + browser session token to create lock
- Display: "Session held by: admin@customer.com"
- On 5-minute idle: show warning "Session expiring in 30s"
- On timeout: lock released, data erased, new user must confirm
- On page refresh: "Resume session?" → type "continue" to restore state

---

## 6. Deployment & Integration

### 6.1 New Files & Directories

```
src/upgrade_portal/
├── app.py                      # Gunicorn entry point (port 8056)
├── auth.py                     # Authentication layer
├── session_manager.py          # Session locking + timeout
├── routes.py                   # API endpoints
├── capture.py                  # CaptureService
├── upgrade.py                  # UpgradeService (reuses existing src/firmware/)
├── settle_gate.py              # SettleGateService
├── comparison.py               # ComparisonService
├── storage.py                  # DatabaseRouter integration
└── templates/
    ├── base.html
    ├── login.html
    ├── organization_select.html
    ├── site_select.html
    ├── device_type_select.html
    ├── upgrade_options.html
    ├── pre_capture.html
    ├── upgrade_status.html
    ├── post_capture.html
    └── comparison.html

specs/1823-capture-upgrade-portal/
├── spec.md
├── plan.md
├── data-model.md
├── contracts/
│   ├── storage.md              # ArangoDB/Redis/CSV behavior
│   ├── settle-gate.md          # Event polling + stats stabilization
│   └── comparison.md           # Delta calculation
└── quickstart.md               # Manual testing guide
```

### 6.2 Container Integration

- Add `src/upgrade_portal/` to the `Containerfile` build
- Keep ArangoDB and Redis in the `misthelper` compose project
- Export port 8056 in `docker-compose.yml` / `compose.yml`
- Symlink data directory: `/app/data` (shared with main portal)

### 6.3 MistHelper.py Integration

- Add menu option 239: "Launch Capture Upgrade Portal"
- Command: `python MistHelper.py --capture-portal`
- Behavior: Start Gunicorn on port 8056, print clickable link

---

## 7. Testing Strategy

### 7.1 Unit Tests

- **CaptureService**: Mock device API calls, verify multi-threaded aggregation
- **UpgradeService**: Mock firmware endpoints, verify cascade order
- **SettleGateService**: Mock events API, verify reconnect detection and stats polling
- **ComparisonService**: Compare known pre/post snapshots, verify deltas

### 7.2 Integration Tests

- Mock Mist API cloud, execute full flow: capture → upgrade → settle → compare
- Verify ArangoDB writes with DatabaseRouter
- Verify CSV fallback when ArangoDB unavailable
- Verify session locking with concurrent browser sessions

### 7.3 E2E / Contract Tests

- Browser automation (Playwright) for login → capture → upgrade → compare flow
- Verify UI renders correctly (tables, sorting, CSV download)
- Verify session timeout after 5 minutes
- Verify timeout recovery ("continue" to resume)

### 7.4 Performance Tests

- Capture 10,000 devices in <60s (threaded)
- Comparison rendering <2s latency
- Upgrade status polling every 30s (no missed updates)

---

## 8. Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| DatabaseRouter bug: ArangoDB/Redis silently skip writes outside container | High | Critical | Fix #1823 prerequisite before implementation. Add explicit error logging. |
| Gateway model detection fails (SRX vs SSR mismatch) | Medium | High | Read `device.model` field, validate against known SRX/SSR prefixes. Add unit tests with all known models. |
| Cascade dependency broken: switch upgrade before gateway settled | Medium | High | Enforce cascade via settle gate. Fail fast if upstream device not settled. |
| Mist API rate limits block rapid polling | Medium | Medium | Implement exponential backoff. Cache recent responses. Respect `Retry-After` header. |
| Session lock expires mid-upgrade | Low | High | Extend lock TTL automatically during active upgrade. Warn user 30s before expiry. |
| Comparison report too large for browser (100k devices) | Low | Low | Paginate report. Lazy-load device deltas. Export to CSV for bulk inspection. |
| Port 8056 already in use | Low | Medium | Fall back to 8057, 8058. Log the actual port. |

---

## 9. Implementation Phases

### Phase 1: Foundation (Weeks 1-2)
- [x] Create spec.md and plan.md
- [ ] Fix DatabaseRouter bug (#1823 prerequisite)
- [ ] Implement authentication (login page, session token)
- [ ] Implement site/device selection pages
- [ ] Unit tests for routing

### Phase 2: Capture & Upgrade (Weeks 3-4)
- [ ] Implement CaptureService (multi-threaded device fetch)
- [ ] Implement pre-capture page (tables, CSV export)
- [ ] Integrate UpgradeService (reuse src/firmware/)
- [ ] Implement upgrade status page (real-time polling)
- [ ] Unit + integration tests

### Phase 3: Settle Gate & Post-Capture (Weeks 5-6)
- [ ] Implement SettleGateService (event polling + stats)
- [ ] Implement post-capture page
- [ ] Cascade dependency enforcement
- [ ] Contract tests for settle gate behavior

### Phase 4: Comparison & UI Polish (Weeks 7-8)
- [ ] Implement ComparisonService (delta calculation)
- [ ] Implement comparison view (side-by-side tables)
- [ ] Session locking (email + browser ID)
- [ ] Timeout handling (5-min cooldown, "continue" recovery)
- [ ] T-Mobile styling

### Phase 5: Testing & Documentation (Weeks 9-10)
- [ ] E2E browser tests (Playwright)
- [ ] Performance testing (10k devices in <60s)
- [ ] Documentation: quickstart.md, contracts
- [ ] Pre-merge quality gates (ruff, black, mypy, pytest)

---

## 10. Success Criteria (from spec.md)

All success criteria from the specification must be met:

- **SC-001**: Pre-capture completes in <60s (threaded)
- **SC-002**: Status updates every 30s with zero data loss
- **SC-003**: Post-capture completes in <60s
- **SC-004**: Settle gate identifies readiness within 300s timeout
- **SC-005**: Comparison renders with <2s latency on 10k devices
- **SC-006**: CSV export includes all data with no truncation
- **SC-007**: Portal loads in <5s on dedicated port
- **SC-008**: Concurrent users on different sites have no cross-contamination
- **SC-009**: Idle timeout triggers at 5-minute mark (±10s)
- **SC-010**: All operations logged with timestamps; queryable, no secrets

---

## Next Steps

1. **Review & Clarification**: ✅ Specification complete. Plan ready for feedback.
2. **Task Breakdown**: Run `speckit.tasks` to generate actionable tasks from this plan.
3. **Contract Development**: Define explicit API contracts and storage behavior.
4. **Implementation**: Follow phases 1-5 sequentially with periodic quality gates.

---

**Prepared by**: Copilot (Haiku)  
**Date**: 2026-09-04  
**Status**: Ready for task generation & implementation
