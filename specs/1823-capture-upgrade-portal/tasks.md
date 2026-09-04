# Tasks - Issue #1823: Capture Portal Upgrade
**Status**: In Progress  
**Last Updated**: 2025-01-31  
**Total Tasks**: 20 (5 Phases)  

---

## Phase 1: Foundation & Authentication (T-001 through T-005)
Establish core infrastructure, authentication, and device/site selection framework.

### T-001: Fix DatabaseRouter Query Pattern
**Phase**: 1  
**Priority**: Critical  
**Effort**: 1 day  

**Description**:
Fix the DatabaseRouter query pattern to correctly handle multi-database routing. The current implementation has issues with how Query objects are inspected and routed. This is a blocking issue for all other database operations in the capture portal.

**Acceptance Criteria**:
- DatabaseRouter correctly identifies model type from Query objects
- Routing directs requests to correct database (mist_db, capture_db, etc.)
- No AttributeError when inspecting Query.model or model._meta
- Unit tests verify routing for each database type
- Integration tests confirm reads/writes reach correct database
- Performance impact < 5% vs. direct database access

**Verification Steps**:
1. Run DatabaseRouter unit tests
2. Execute integration test with multi-database setup
3. Check query logs to verify correct database selection
4. Load test with 100 concurrent requests
5. Verify no routing errors in application logs

**Affected Files**:
- src/infra/db/router.py
- src/infra/db/__init__.py
- tests/unit/test_router.py
- tests/integration/test_multi_db.py

**Implementation Notes**:
- Review Django documentation on custom database routers
- Test with both ORM queries and raw SQL
- Ensure compatibility with all database backends (PostgreSQL, MySQL, SQLite)

**Dependencies**: None (blocking task)

---

### T-002: Implement OAuth Integration
**Phase**: 1  
**Priority**: Critical  
**Effort**: 2 days  

**Description**:
Implement OAuth authentication flow with Juniper/HPE identity provider. This includes token exchange, refresh token handling, and user session management. Integration with existing authentication middleware.

**Acceptance Criteria**:
- OAuth token exchange works with HPE identity provider
- Refresh token automatically extends session without user action
- User session created after successful OAuth
- Scope-based permission assignment implemented
- Rate limiting on token refresh (max 10/minute per user)
- Failed authentication redirects to login page
- PKCE flow implemented for secure client-side auth

**Verification Steps**:
1. Test OAuth flow end-to-end with test identity provider
2. Verify token refresh within session lifetime
3. Confirm session timeout after token expiration
4. Test with invalid/expired credentials
5. Load test: 50 simultaneous logins
6. Verify PKCE challenge/verifier exchange

**Affected Files**:
- src/auth/oauth.py (new)
- src/auth/middleware.py (new)
- src/config/auth_config.py (new)
- src/api/routes/auth.py (new)
- tests/unit/test_oauth.py (new)
- tests/integration/test_oauth_flow.py (new)

**Implementation Notes**:
- Use authlib for OAuth handling
- Store tokens securely (encrypted DB or session store)
- Implement token rotation for security
- Add audit logging for auth events

**Dependencies**: T-001 (DatabaseRouter)

---

### T-003: Organization Validation & Setup
**Phase**: 1  
**Priority**: High  
**Effort**: 1 day  

**Description**:
Implement organization validation to ensure users only access organizations they're authorized for. Create organization context middleware and validation decorators.

**Acceptance Criteria**:
- Org validation middleware checks user has org access
- Org context available in request throughout lifecycle
- Org validation applied to all protected routes
- Cross-org data access prevented
- Multiple org support for multi-tenant users
- Org-specific audit logging implemented
- Org context passed to database router

**Verification Steps**:
1. Test org validation with authorized user
2. Confirm access denied for unauthorized org
3. Test multi-org user switching
4. Verify org context in logs
5. Load test: 100 concurrent users across 10 orgs
6. SQL injection test on org validation

**Affected Files**:
- src/auth/org_context.py (new)
- src/auth/middleware.py (update)
- src/decorators/org_required.py (new)
- tests/unit/test_org_validation.py (new)

**Implementation Notes**:
- Use request.user.orgs for multi-org support
- Store org_id in session and request context
- Add org validation to API permission classes
- Implement org-scoped logging

**Dependencies**: T-002 (OAuth)

---

### T-004: Site & Device Selection API
**Phase**: 1  
**Priority**: High  
**Effort**: 2 days  

**Description**:
Build API endpoints for site and device selection. Endpoints must query Mist Cloud API to retrieve available sites and devices with filtering, pagination, and caching.

**Acceptance Criteria**:
- GET /api/v1/sites endpoint returns paginated site list
- GET /api/v1/devices endpoint returns device list with filters
- Filter by device type, model, status, firmware version
- Pagination with cursor or offset-based navigation
- 5-minute cache on site/device lists with manual refresh
- Results honor organization context
- API rate limiting: 100 requests/minute per user
- Device availability status updated in real-time

**Verification Steps**:
1. Test site list retrieval with 1000+ sites
2. Verify device filtering by all supported attributes
3. Test pagination with 10k devices
4. Verify cache hits/misses in metrics
5. Manual cache refresh endpoint
6. Load test: 50 concurrent users fetching device lists

**Affected Files**:
- src/api/routes/devices.py (new)
- src/api/routes/sites.py (new)
- src/services/device_service.py (new)
- src/services/site_service.py (new)
- src/cache/device_cache.py (new)
- tests/integration/test_device_selection.py (new)

**Implementation Notes**:
- Use Mist Cloud Python SDK for site/device retrieval
- Implement Redis caching for device lists
- Add metrics for cache hit/miss rates
- Design filter schema for extensibility

**Dependencies**: T-003 (Organization Validation)

---

### T-005: Portal Session Management
**Phase**: 1  
**Priority**: High  
**Effort**: 1 day  

**Description**:
Implement session management for the capture portal. Sessions track capture flow progress, state, and user context. Support for session timeout, resumption, and multi-device capture sessions.

**Acceptance Criteria**:
- Session created upon entering portal
- Session stores user, org, site, device context
- Session timeout after 30 minutes inactivity
- Session resumption within 24 hours
- Session locking prevents concurrent edits
- Maximum 5 active sessions per user
- Session state persisted in database
- Session cleanup for stale sessions (>7 days)

**Verification Steps**:
1. Create and retrieve session
2. Verify timeout after 30 min inactivity
3. Resume session within 24 hours
4. Verify session lock on concurrent access attempt
5. Test session cleanup cron job
6. Load test: 1000 concurrent sessions

**Affected Files**:
- src/models/portal_session.py (new)
- src/services/session_service.py (new)
- src/api/routes/sessions.py (new)
- tests/unit/test_session_service.py (new)

**Implementation Notes**:
- Use Django sessions for storage
- Implement optimistic locking for session updates
- Add session metrics tracking
- Design session context object

**Dependencies**: T-002 (OAuth), T-003 (Org Validation)

---

## Phase 2: Capture & Pre-Capture (T-006 through T-009)
Implement capture service, pre-capture UI/API, and upgrade service.

### T-006: CaptureService - Data Collection
**Phase**: 2  
**Priority**: Critical  
**Effort**: 2 days  

**Description**:
Build CaptureService to collect configuration and operational data from devices. Handles CLI commands, SSH connections, and data aggregation from multiple sources.

**Acceptance Criteria**:
- SSH connection to device with configurable timeout (30s default)
- Execute capture commands with error handling
- Collect syslog configuration from device
- Collect interface configuration and status
- Collect routing protocol state (BGP, OSPF)
- Aggregate data with metadata (timestamp, source)
- Retry on transient failures (3 attempts, exponential backoff)
- Store capture in database with version tracking
- Support parallel captures (10 devices concurrently)

**Verification Steps**:
1. Capture from test device (real or simulated)
2. Verify SSH connection and command execution
3. Validate collected data schema
4. Test retry behavior with connection failures
5. Measure capture time for various device sizes
6. Load test: 10 parallel device captures

**Affected Files**:
- src/services/capture_service.py (new)
- src/models/device_capture.py (new)
- src/utils/ssh_connection.py (new)
- src/commands/capture_commands.py (new)
- tests/unit/test_capture_service.py (new)

**Implementation Notes**:
- Use Paramiko for SSH connections
- Implement connection pooling for efficiency
- Add data validation for collected configs
- Design extensible command framework
- Add telemetry for capture success/failure rates

**Dependencies**: T-004 (Site & Device Selection)

---

### T-007: Pre-Capture UI & API
**Phase**: 2  
**Priority**: High  
**Effort**: 2 days  

**Description**:
Build frontend and API for pre-capture workflow. Includes device selection confirmation, capture settings, and capture initiation UI.

**Acceptance Criteria**:
- Display selected device details and current config
- Allow user to configure capture settings (SSH credentials, timeout)
- Trigger capture with validation
- Real-time capture progress indicator
- Capture status updates via WebSocket or polling (5s intervals)
- Cancel in-progress capture
- View capture summary after completion
- Download captured configuration as JSON/YAML

**Verification Steps**:
1. Render pre-capture UI with device details
2. Submit capture with valid settings
3. Monitor progress indicators update
4. Test cancel during capture
5. Verify download formats (JSON, YAML)
6. Load test: 50 concurrent captures

**Affected Files**:
- src/frontend/pages/PreCapturePage.tsx (new)
- src/frontend/components/DeviceSelector.tsx (new)
- src/frontend/components/CaptureProgress.tsx (new)
- src/api/routes/capture.py (new)
- src/websocket/handlers.py (new)
- tests/e2e/test_pre_capture.py (new)

**Implementation Notes**:
- Use React hooks for state management
- Implement real-time updates via WebSocket
- Fallback to polling for WebSocket unavailable
- Add error messages for capture failures
- Design responsive UI for mobile

**Dependencies**: T-005 (Portal Session Management), T-006 (CaptureService)

---

### T-008: UpgradeService - Orchestration
**Phase**: 2  
**Priority**: Critical  
**Effort**: 2 days  

**Description**:
Build UpgradeService to orchestrate device upgrade. Handles firmware staging, pre-upgrade validation, upgrade execution, and status tracking.

**Acceptance Criteria**:
- Retrieve available firmware versions from Mist Cloud
- Validate device compatibility with firmware
- Pre-upgrade checks (disk space, running processes)
- Stage firmware to device or upload to Mist
- Monitor upgrade progress (0-100%)
- Handle upgrade failures with rollback plan
- Track upgrade status in database
- Upgrade timeout handling (2 hour default)
- Support batch upgrades (5-10 devices)

**Verification Steps**:
1. Retrieve firmware list for device
2. Validate compatibility checks
3. Execute pre-upgrade validations
4. Stage firmware to device
5. Monitor upgrade progress
6. Verify post-upgrade state
7. Test failure handling and rollback
8. Load test: 5 concurrent device upgrades

**Affected Files**:
- src/services/upgrade_service.py (new)
- src/models/upgrade_job.py (new)
- src/utils/firmware_client.py (new)
- src/validators/upgrade_validators.py (new)
- tests/integration/test_upgrade_service.py (new)

**Implementation Notes**:
- Use Mist Cloud API for firmware operations
- Implement state machine for upgrade process
- Add detailed upgrade logging
- Design recovery mechanism for failed upgrades
- Support pause/resume for upgrades

**Dependencies**: T-006 (CaptureService)

---

### T-009: Status UI & Websocket Handler
**Phase**: 2  
**Priority**: High  
**Effort**: 1 day  

**Description**:
Build real-time status UI component for upgrade progress. Implement WebSocket handler for pushing status updates to clients.

**Acceptance Criteria**:
- Real-time upgrade progress display (0-100%)
- Status message updates every 5 seconds
- Connection handling for WebSocket disconnects
- Auto-reconnect on disconnection
- Display estimated time remaining
- Alert on upgrade completion/failure
- Accessible status history view
- Support multiple simultaneous upgrade tracking

**Verification Steps**:
1. Connect to WebSocket and receive updates
2. Verify updates frequency (every 5s)
3. Test reconnection after 30s disconnect
4. Load test: 100 concurrent WebSocket connections
5. Verify message delivery reliability
6. Test UI responsiveness with rapid updates

**Affected Files**:
- src/frontend/components/UpgradeStatus.tsx (new)
- src/frontend/hooks/useUpgradeWebSocket.ts (new)
- src/websocket/handlers.py (update)
- src/websocket/broadcaster.py (new)
- tests/e2e/test_upgrade_status.py (new)

**Implementation Notes**:
- Use Django Channels for WebSocket support
- Implement message queue for status broadcasts
- Add reconnection with exponential backoff
- Design status message schema
- Add error handling and retry logic

**Dependencies**: T-008 (UpgradeService), T-007 (Pre-Capture UI)

---

## Phase 3: Settle & Comparison (T-010 through T-012)
Implement post-upgrade data collection and configuration comparison.

### T-010: SettleGateService - Post-Upgrade Collection
**Phase**: 3  
**Priority**: Critical  
**Effort**: 2 days  

**Description**:
Build SettleGateService to collect post-upgrade device state. Collects same data as pre-capture to enable comparison.

**Acceptance Criteria**:
- Delay data collection by 30 minutes post-upgrade (settle time)
- Collect same data types as CaptureService
- Validate post-upgrade config completeness
- Compare pre/post data to detect configuration drift
- Store settle capture with reference to upgrade job
- Handle collection failures with retry (up to 5 attempts)
- Collection timeout: 2 minutes per device
- Support manual trigger for post-capture collection

**Verification Steps**:
1. Wait 30 minutes and trigger settle collection
2. Verify data collected matches pre-capture schema
3. Validate completeness checks pass
4. Compare with pre-upgrade data
5. Test retry behavior on collection failure
6. Load test: 10 parallel settle collections

**Affected Files**:
- src/services/settle_gate_service.py (new)
- src/models/settle_capture.py (new)
- src/tasks/settle_gate_tasks.py (new)
- tests/integration/test_settle_gate.py (new)

**Implementation Notes**:
- Implement as async Celery task with delayed execution
- Design settle gate workflow state machine
- Add configurable settle delay
- Implement collection status tracking
- Design retry strategy with backoff

**Dependencies**: T-008 (UpgradeService), T-006 (CaptureService)

---

### T-011: ComparisonService - Configuration Diff
**Phase**: 3  
**Priority**: High  
**Effort**: 2 days  

**Description**:
Build ComparisonService to compare pre and post-upgrade configurations. Generates detailed diff report highlighting changes.

**Acceptance Criteria**:
- Parse pre/post configs into structured format
- Generate line-by-line diff for each config section
- Identify breaking changes (config removals, conflicts)
- Categorize changes (added, removed, modified)
- Generate human-readable summary report
- Highlight critical configuration changes
- Support multi-format comparisons (JSON, YAML, text)
- Performance: diff 10k-line configs in <2 seconds

**Verification Steps**:
1. Compare sample pre/post configs
2. Verify diff accuracy against manual review
3. Test with various config complexities
4. Measure performance on large configs
5. Test breaking change detection
6. Verify report formatting

**Affected Files**:
- src/services/comparison_service.py (new)
- src/utils/config_parser.py (new)
- src/utils/diff_generator.py (new)
- src/models/config_diff.py (new)
- tests/unit/test_comparison_service.py (new)

**Implementation Notes**:
- Use difflib for diff generation
- Implement config parsers for various formats
- Design change categorization logic
- Add critical change detection heuristics
- Support custom comparison rules

**Dependencies**: T-010 (SettleGateService)

---

### T-012: Post-Capture UI & Diff Viewer
**Phase**: 3  
**Priority**: High  
**Effort**: 1 day  

**Description**:
Build post-capture UI showing settlement status and configuration comparison results.

**Acceptance Criteria**:
- Display post-capture collection status
- Show diff viewer with side-by-side comparison
- Highlight additions/removals/modifications
- Provide filtering by section (interfaces, routing, etc.)
- Export diff report (PDF, HTML, JSON)
- User can approve or flag changes
- Show configuration change summary
- Display estimated impact assessment

**Verification Steps**:
1. Display post-capture status
2. Render diff viewer with test data
3. Test filtering by config section
4. Export to multiple formats
5. Load test: 50 concurrent diff viewers
6. Test with large diffs (10k+ lines)

**Affected Files**:
- src/frontend/pages/PostCaptureComparisonPage.tsx (new)
- src/frontend/components/DiffViewer.tsx (new)
- src/frontend/components/ConfigSummary.tsx (new)
- src/api/routes/comparison.py (new)
- tests/e2e/test_comparison_ui.py (new)

**Implementation Notes**:
- Use diff-match-patch library for visualization
- Implement syntax highlighting for configs
- Design responsive layout for diff viewer
- Add export functionality
- Support large diff rendering performance

**Dependencies**: T-011 (ComparisonService), T-010 (SettleGateService)

---

## Phase 4: Validation & Testing (T-013 through T-016)
Implement session locking, timeout handling, E2E tests, and performance validation.

### T-013: Session Locking & Conflict Resolution
**Phase**: 4  
**Priority**: High  
**Effort**: 1 day  

**Description**:
Implement session locking mechanism to prevent concurrent user modifications. Add conflict detection and resolution strategies.

**Acceptance Criteria**:
- Lock session when upgrade starts
- Prevent concurrent operations on locked session
- Lock timeout after 4 hours
- Display lock status and locked-by information
- Support force unlock by admin
- Detect stale locks (server crash)
- Conflict detection on concurrent operations
- Conflict resolution strategy (last-write-wins)

**Verification Steps**:
1. Lock session during upgrade
2. Attempt concurrent modification (should fail)
3. Verify lock timeout after 4 hours
4. Test stale lock detection
5. Force unlock and verify
6. Load test: 50 concurrent users with conflicts

**Affected Files**:
- src/services/session_service.py (update)
- src/models/portal_session.py (update)
- src/api/routes/sessions.py (update)
- tests/unit/test_session_locking.py (new)

**Implementation Notes**:
- Implement pessimistic locking with timeout
- Design conflict detection algorithm
- Add audit logging for locks/unlocks
- Implement admin override mechanism
- Test distributed lock scenarios

**Dependencies**: T-005 (Portal Session Management)

---

### T-014: Timeout & Error Handling
**Phase**: 4  
**Priority**: High  
**Effort**: 1 day  

**Description**:
Implement comprehensive timeout and error handling for long-running operations.

**Acceptance Criteria**:
- Capture timeout: 5 minutes per device
- Upgrade timeout: 2 hours per device
- Settle collection timeout: 2 minutes
- Comparison timeout: 30 seconds
- Graceful degradation on partial failures
- User notification on timeout
- Automatic retry with exponential backoff
- Error categorization (transient vs. permanent)
- Max retry attempts: 3 for transient errors

**Verification Steps**:
1. Test capture timeout after 5 min
2. Test upgrade timeout after 2 hours
3. Verify retry behavior for transient errors
4. Test user notification on timeout
5. Load test: 100 concurrent timeouts
6. Verify error categorization

**Affected Files**:
- src/services/timeout_handler.py (new)
- src/services/error_handler.py (new)
- src/utils/retry_decorator.py (new)
- tests/unit/test_timeout_handling.py (new)

**Implementation Notes**:
- Use Celery timeouts for async operations
- Implement timeout context managers
- Design error classification logic
- Add configurable timeout values
- Implement user notification system

**Dependencies**: T-006 (CaptureService), T-008 (UpgradeService)

---

### T-015: End-to-End Test Suite
**Phase**: 4  
**Priority**: High  
**Effort**: 2 days  

**Description**:
Build comprehensive end-to-end test suite covering complete capture-upgrade-compare workflow.

**Acceptance Criteria**:
- E2E test for full workflow (capture → upgrade → settle → compare)
- Test with 5 different device types
- Test with various configuration complexities
- Test error scenarios (device offline, SSH failure, upgrade failure)
- Test timeout scenarios
- Test concurrent user sessions
- Minimum 80% workflow coverage
- All tests pass in <30 minutes
- Tests run in CI/CD pipeline

**Verification Steps**:
1. Run full E2E test suite
2. Verify all workflow paths covered
3. Test error scenarios
4. Measure test execution time
5. Verify CI/CD integration
6. Test with various data sizes

**Affected Files**:
- tests/e2e/test_full_workflow.py (new)
- tests/e2e/fixtures/device_simulator.py (new)
- tests/e2e/fixtures/upgrade_simulator.py (new)
- tests/conftest.py (update)

**Implementation Notes**:
- Use Pytest for test framework
- Implement device/upgrade simulators
- Design test data fixtures
- Add test reporting and metrics
- Support parallel test execution

**Dependencies**: T-012 (Post-Capture UI), T-008 (UpgradeService)

---

### T-016: Performance & Load Testing
**Phase**: 4  
**Priority**: Medium  
**Effort**: 1 day  

**Description**:
Execute performance and load testing to validate scalability requirements.

**Acceptance Criteria**:
- Support 100 concurrent users
- Support 50 concurrent device captures
- Capture latency: <5 min per device
- API response time: <200ms for 95th percentile
- Comparison generation: <2 sec for 10k-line config
- Database query latency: <100ms
- Memory usage stable over 1 hour load test
- No memory leaks detected
- WebSocket message delivery: <100ms

**Verification Steps**:
1. Load test: 100 concurrent users
2. Load test: 50 parallel captures
3. Measure API response times
4. Measure database query performance
5. Memory leak detection (1 hour test)
6. WebSocket performance test
7. Generate performance report

**Affected Files**:
- tests/performance/test_load.py (new)
- tests/performance/fixtures/locustfile.py (new)
- scripts/performance_test.sh (new)

**Implementation Notes**:
- Use Locust for load testing
- Implement performance benchmarks
- Add metrics collection and reporting
- Design load test profiles
- Identify and document bottlenecks

**Dependencies**: T-015 (End-to-End Test Suite)

---

## Phase 5: Production Readiness (T-017 through T-020)
Documentation, security audit, and production deployment preparation.

### T-017: Security Audit & Hardening
**Phase**: 5  
**Priority**: Critical  
**Effort**: 2 days  

**Description**:
Execute comprehensive security audit and implement hardening measures.

**Acceptance Criteria**:
- OWASP Top 10 vulnerability scan
- Credential handling audit (no hardcoded secrets)
- SSH key management secure
- OAuth token security validation
- SQL injection prevention verified
- XSS vulnerability scan
- CSRF protection on state-changing operations
- Rate limiting implemented on all APIs
- Input validation on all endpoints
- Secrets management via environment variables/vaults

**Verification Steps**:
1. Run OWASP security scan
2. Credential audit: grep for hardcoded secrets
3. Verify OAuth token handling
4. SQL injection test on all endpoints
5. XSS injection test
6. CSRF token validation
7. Rate limiting test

**Affected Files**:
- src/security/validators.py (new)
- src/security/rate_limiter.py (update)
- src/config/secrets.py (new)
- .env.example (new)
- SECURITY.md (update)

**Implementation Notes**:
- Use Bandit for security scanning
- Implement secret scanning in CI/CD
- Add security headers middleware
- Document security practices
- Create incident response plan

**Dependencies**: All previous phases

---

### T-018: Comprehensive Documentation
**Phase**: 5  
**Priority**: High  
**Effort**: 1 day  

**Description**:
Create complete documentation for capture portal including user guide, API docs, and architecture guide.

**Acceptance Criteria**:
- User guide with screenshots (10+ pages)
- API documentation with examples (all endpoints)
- Architecture guide with diagrams
- Database schema documentation
- Configuration guide for deployment
- Troubleshooting guide with common issues
- Security best practices guide
- Developer setup guide
- Deployment runbook

**Verification Steps**:
1. Review user guide completeness
2. Verify all API endpoints documented
3. Check documentation accuracy with code
4. Test deployment runbook
5. Review for technical accuracy
6. Spellcheck and grammar check

**Affected Files**:
- documentation/user_guide.md (new)
- documentation/api_guide.md (new)
- documentation/architecture.md (new)
- documentation/deployment.md (new)
- documentation/troubleshooting.md (new)

**Implementation Notes**:
- Use Markdown for documentation
- Include architecture diagrams (Mermaid)
- Add code examples
- Create troubleshooting decision tree
- Design for non-technical users

**Dependencies**: All implementation phases

---

### T-019: Documentation & Runbook Review
**Phase**: 5  
**Priority**: High  
**Effort**: 1 day  

**Description**:
Review and validate all documentation, deployment runbooks, and operational procedures.

**Acceptance Criteria**:
- Documentation review by 2+ team members
- All procedures tested and verified
- Runbook successfully executed in test environment
- Knowledge transfer session completed
- Deployment checklist finalized
- Emergency procedures documented
- Escalation procedures clear
- Support team trained

**Verification Steps**:
1. Documentation peer review
2. Procedure testing and sign-off
3. Runbook execution in test environment
4. Team knowledge transfer session
5. Support team verification
6. Final approval

**Affected Files**:
- documentation/ (all files)
- deploy/runbook.md (new)
- deploy/emergency_procedures.md (new)
- deploy/checklist.md (new)

**Implementation Notes**:
- Conduct knowledge transfer meeting
- Create runbook checklist
- Document lessons learned
- Create change log
- Prepare rollback procedures

**Dependencies**: T-018 (Comprehensive Documentation)

---

### T-020: Production Deployment & Monitoring Setup
**Phase**: 5  
**Priority**: Critical  
**Effort**: 1 day  

**Description**:
Deploy capture portal to production environment with comprehensive monitoring, logging, and alerting.

**Acceptance Criteria**:
- Application deployed to production
- All monitoring dashboards active
- Logging centralized and indexed
- Alerting configured for critical events
- Health checks passing
- Database backups automated
- Rollback procedure tested
- Incident response team briefed
- Day-1 support procedures ready

**Verification Steps**:
1. Deploy to production environment
2. Verify all services healthy
3. Check monitoring dashboard
4. Test alert notifications
5. Verify logging and centralization
6. Test rollback procedure
7. Conduct production readiness review

**Affected Files**:
- deploy/production.yml (new)
- deploy/monitoring.yml (new)
- deploy/logging.yml (new)
- deploy/alerting.yml (new)

**Implementation Notes**:
- Use Prometheus for metrics
- Use ELK/CloudWatch for logging
- Implement uptime monitoring
- Configure incident alerting
- Set up automated backups
- Design monitoring dashboards

**Dependencies**: T-019 (Documentation & Runbook Review), T-017 (Security Audit)

---

## Task Dependencies Graph

\\\
T-001 (DatabaseRouter)
  ├─→ T-002 (OAuth)
      ├─→ T-003 (Org Validation)
          ├─→ T-004 (Site & Device Selection)
          │   └─→ T-006 (CaptureService)
          │       ├─→ T-007 (Pre-Capture UI)
          │       ├─→ T-008 (UpgradeService)
          │       │   ├─→ T-009 (Status UI)
          │       │   └─→ T-010 (SettleGateService)
          │       │       └─→ T-011 (ComparisonService)
          │       │           └─→ T-012 (Post-Capture UI)
          │       │               └─→ T-015 (E2E Tests)
          │       │                   └─→ T-016 (Performance Tests)
          │       └─→ T-014 (Timeout Handling)
          │
          ├─→ T-005 (Portal Session Management)
              └─→ T-013 (Session Locking)
\\\

**Security & Production**:
- T-017 (Security Audit) - Depends on all implementation phases
- T-018 (Documentation) - Depends on all implementation phases
- T-019 (Review & Runbook) - Depends on T-018
- T-020 (Production Deployment) - Depends on T-017, T-019

---

## Summary by Phase

| Phase | Tasks | Duration | Focus |
|-------|-------|----------|-------|
| 1 | T-001 to T-005 | ~7 days | Foundation & Auth |
| 2 | T-006 to T-009 | ~7 days | Capture & Upgrade |
| 3 | T-010 to T-012 | ~5 days | Settle & Compare |
| 4 | T-013 to T-016 | ~5 days | Testing & Validation |
| 5 | T-017 to T-020 | ~5 days | Security & Deployment |
| **Total** | **20 tasks** | **~29 days** | **Full Implementation** |
